# Chuẩn bị và chạy thực nghiệm

Chỉ dùng train/dev/dev_eval khi benchmark v2 còn draft. Ma trận nghiên cứu gồm
`b3`/`b3l` × seed 42/43/44; hiện mới `b3/42` train hoàn tất. Quyết định hiện tại
là [chưa mở rộng](diagnosis/scaling-decision.json); không tự submit thêm job.

## Chuẩn bị

Giữ cùng encoder/dictionary/schema giữa các split. `b3-base` và `b3l-base` dùng
messages/prompt hash giống `b3` và `b3l`, chỉ khác việc có adapter.
[Kiểm prompt parity](prompt-parity.json) lưu phép kiểm trên 100 câu dev_eval.

```bash
for split in train dev dev_eval; do
  uv run --locked eth-nl2sql link --split "$split"
done
for config in b3 b3l; do
  uv run --locked eth-nl2sql prompts --config "$config" --training
done
for config in b3 b3l b3-base b3l-base; do
  uv run --locked eth-nl2sql prompts --config "$config" --split dev_eval
done
```

Chỉ dựng lại input cho lượt mới; không ghi đè prompt/SFT đang ràng buộc hash với
kết quả được giữ. Khi đổi input/protocol, dùng thư mục làm việc riêng. Chỉ đưa
kết quả mới vào tập hiện hành sau khi kiểm tra và chọn kết quả còn có giá trị.

## Provenance của adapter đang giữ

Adapter `b3/42` khớp hash đã ghi. `code_sha256` trong manifest train là
`df9d81eeb86785d4495ac08c5d2238183625e1af10c5b7088348193a0995e824`, khác source
training ở HEAD ngay trước khi dọn (`51b98447b1cbe3bf1a438f18cb96fa45eb6419b8f62c43000affd9ef5f7967f3`).
Đây là khác biệt có sẵn, không do dọn artifact. `train --resume`/`generate b3`
bằng source hiện tại sẽ bị chặn provenance; cần dùng đúng source đã train hoặc
lượt mới. Không sửa manifest cũ để vượt kiểm tra. Những lệnh dưới đây mô tả
quy trình cho lượt có source/input đúng provenance.

## Train và sinh SQL

Trên GPU host có extra `gpu`, model pin trong `experiment.toml` và runtime khóa
ở `configs/t11b-gpu-requirements.txt`:

```bash
eth-nl2sql preflight --config b3 --training --seed 42
eth-nl2sql train --config b3 --seed 42 --resume
eth-nl2sql generate --config b3 --seed 42 --limit 10
eth-nl2sql smoke --predictions runs/b3/seed-42/predictions-dev_eval.jsonl   --out .cache/smoke.json
# Chỉ tiếp tục khi smoke đạt và lượt chạy được phép tiếp tục:
eth-nl2sql generate --config b3 --seed 42
```

Preflight giữ/bỏ nguyên dòng, không truncate SQL/EOT. Generation kiểm hash
prompt/model/settings/adapter kể cả khi không còn câu cần sinh. Seed generation
và bootstrap 42 độc lập với seed training. Resume training đang dang dở cần
checkpoint có state/optimizer/RNG; lượt hoàn tất dùng adapter và summary đã
kiểm hash, không cần giữ checkpoint optimizer.

`scripts/t11a.py` ghi hai base control vào `base-controls/`. `scripts/t11b.py`
và controller `scripts/t11b_continue.py` dùng thư mục thực nghiệm này cùng
`runs/<config>/seed-<seed>/`. Script notebook dùng ZIP tạm trong `.cache/` để
truyền GPU. Collector giữ file giải nén và manifest, không chép ZIP vào báo cáo.
Xóa bundle tạm sau khi thu nhận và kiểm hash thành công.

## Chấm và báo cáo

```bash
uv run --locked eth-nl2sql evaluate --config b3 --seed 42
uv run --locked eth-nl2sql report
```

Evaluator chuẩn yêu cầu đủ split. Pilot 10 câu và chẩn đoán chấm riêng, không
nâng thành accuracy 100 câu. Báo cáo chuẩn kiểm manifest/hash và giữ từng seed;
mean/SD mẫu (ddof=1) chỉ trên cùng dữ liệu/prompt/protocol, không gộp thành 3N.
Thiếu seed được báo rõ, SD một seed là null.

Chẩn đoán dùng `scripts/t11b_diagnose.py` và `scripts/t11b_diagnosis_report.py`;
raw prediction, prompt, kế hoạch gốc, loss và đối chứng giữ dưới `diagnosis/`.
Không trộn can thiệp prompt vào run gốc.

```bash
uv run --locked pytest -q
uv run --locked ruff check src tests scripts
uv run --locked eth-nl2sql check-sql
```

Log/JUnit của kiểm tra lưu tạm ngoài `reports/`. Chỉ giữ báo cáo hiện hành,
manifest, kết quả và adapter còn dùng; không tạo archive.

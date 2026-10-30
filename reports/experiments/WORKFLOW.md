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

## Kernel và version Kaggle

Mọi tên mặc định đi qua `load_settings()` và `configs/kaggle.toml`; có thể đổi
owner, cache hoặc kernel suy luận bằng các biến `ETH_NL2SQL_KAGGLE_*` tương ứng.
Không dùng `run_tag` hoặc ngày để tạo thêm kernel.

| Loại job | Kernel |
|---|---|
| Tạo adapter | Riêng từng config/seed: `OWNER/eth-nl2sql-b3l-seed-42`, v.v. |
| Pilot, base control, chẩn đoán, chỉ sinh SQL | Dùng chung `OWNER/eth-nl2sql-inference`, mỗi lượt là một version |
| Model cache | `OWNER/<environment_cache>` |

`training_kernels` ghi identity cho adapter đã công bố. Kernel `b3/42` đã đổi tên
thành `eth-nl2sql-fine-tune`; cache là `eth-nl2sql-model-cache`, giữ nguyên ID,
version và output. Các ref trong bằng chứng cũ vẫn mô tả tên tại thời điểm chạy.
Không xóa hoặc push đè output đang làm nguồn. Các job train mới có tên ổn định
không kèm ngày. Client từ chối
push lên producer đã tồn tại; thay protocol/input cần một identity mới được
cấu hình rõ ràng, không tự cập nhật output đang được mount.

`NotebookSpec.extra_kernel_sources` thêm producer vào notebook chẩn đoán.
`prepare` ghi `adapter_kernel` vào kế hoạch và pin hash config; builder đọc đúng
nguồn trong kế hoạch, GPU dùng cùng nguồn đó và kiểm hash adapter. Bundle cũ
không có trường này phải được dựng lại trong thư mục làm việc của lượt mới;
không sửa kế hoạch hoặc kết quả đã lưu của lượt gốc.

Hai controller dùng `KaggleClient` cho lock kernel, push, polling và tải output.
Push xác nhận số version và lưu `submission.json`; state training lưu
`kernel_ref=OWNER/SLUG/VERSION`. Status và output đều dùng ref đó. Không tự
retry push khi mất phản hồi; receipt trạng thái chưa rõ yêu cầu xem log trước
khi tiếp tục. ZIP được tải vào thư mục tạm mới và chỉ nhận sau khi kiểm đủ
manifest/hash; thu nhận xong thì bỏ bản ZIP tạm.

Controller training dừng ngay nếu quyết định vẫn là
`hold_for_further_development`. Collector chẩn đoán chỉ submit khi người chạy
truyền `--notebook`; chế độ chỉ thu nhận cần version cụ thể hoặc receipt đã lưu:

```bash
# Chỉ thu nhận một version đã submit:
uv run --locked python scripts/t11b_diagnosis_continue.py \
  --kernel OWNER/eth-nl2sql-inference/VERSION
# Submit notebook đã dựng rồi thu nhận; chỉ dùng khi lượt chạy được cho phép:
uv run --locked python scripts/t11b_diagnosis_continue.py \
  --notebook .cache/t11b-diagnosis-notebook
```

Thông tin `kernel_sources` nhận owner/slug theo
[Kaggle metadata](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels_metadata.md).
Quy tắc giữ producer riêng bảo vệ nguồn mount khỏi các version của job khác;
version ref bảo vệ việc polling/download, không biến nguồn mount thành version pin.
Xem thêm [Kaggle CLI](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md).
Notebook chạy tay cũ đã bỏ; hai notebook hiện hành được sinh bằng workflow bên dưới.

## Đồng bộ notebook local và Kaggle

Chỉ sửa source local, rồi chạy:

```bash
uv run --locked eth-nl2sql kaggle build --job b3-seed-42
uv run --locked eth-nl2sql kaggle status --offline
uv run --locked eth-nl2sql kaggle status
```

`notebooks/fine_tune.ipynb` và `notebooks/model_cache.ipynb` là bản dễ đọc, giống
byte với bản dựng trong `.cache/kaggle/<workflow>/`. Header ghi commit và cờ source
chưa commit, fingerprint code/dữ liệu, job/config/seed và SHA256 của input.
Nếu source, dữ liệu hoặc notebook local đổi sau build, `status` báo `needs_build`.
Phần Kaggle báo `in_sync`/`different` và Input có sẵn hay không; không lưu version
hay chạy GPU. Commit Git không tự cập nhật Kaggle.

Bundle vẫn dùng `package_inputs`: chỉ ID/câu hỏi của dev_eval được gửi lên GPU,
gold và chấm EX ở local. Bản dựng không ghi đè manifest hoặc hash nghiên cứu đã lưu.
ZIP mang đuôi `.bundle` trong Input để giữ nguyên byte. Tên file chứa SHA256;
notebook từ chối bundle thiếu, sai hash hoặc có đường dẫn không hợp lệ trước khi
cài thư viện/chạy workflow. Một dataset private `inputs_dataset` trong config
được dùng chung cho hai notebook; version mới có thể thay bundle, khi đó notebook
cũ sẽ dừng thay vì âm thầm dùng input khác.

Chỉ khi cần xuất bản input cho lượt chạy đã được duyệt:

```bash
# Lần đầu tạo dataset private; chưa chạy hoặc lưu notebook:
uv run --locked eth-nl2sql kaggle publish-inputs --create
# Các lần sau tạo version dataset mới, giữ version cũ:
uv run --locked eth-nl2sql kaggle publish-inputs
# Kiểm Input đã xử lý xong và đối chiếu lại notebook:
uv run --locked eth-nl2sql kaggle status
# Submit riêng khi kernel là producer mới chưa có output cần bảo vệ:
uv run --locked eth-nl2sql kaggle run --workflow fine-tune
```

`run` từ chối ghi đè hai producer hiện có; không dùng Quick Save để "đồng bộ"
vì latest output có thể trở thành rỗng. Để cập nhật notebook trên hai kernel này,
trước hết cần quyết định cách giữ nguồn output và lượt chạy thay thế. Không tự
submit lại train/cache chỉ vì local khác cloud.

Builder chẩn đoán hoặc controller cũ cũng tạo Input đính kèm. Có thể xuất bản
đúng gói nó đã dựng bằng `kaggle publish-inputs --deployment <thư-mục-notebook>`
(thêm `--create` chỉ lần đầu). `KaggleClient.push` kiểm Input tồn tại trước submit.
Lỗi/timeout khi xuất bản không được tự retry vì server có thể đã nhận version.

Cache dùng `scripts/model_cache.py` và runtime CPU khóa ở
`configs/model-cache-requirements.txt`, không còn phụ thuộc repo `LuanVan`.
Thêm secret `HF_TOKEN` trong Kaggle Add-ons > Secrets khi cần tải lại cache;
token chỉ truyền qua stdin và không ghi vào notebook/provenance. Hàm kiểm hash
cache được dùng chung với workflow train, không tải model vào RAM/GPU.

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

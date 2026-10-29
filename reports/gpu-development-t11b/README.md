# T11B — smoke compile, full-catalog pilot và QLoRA theo thứ tự

Ngày bắt đầu: **28/10/2026**, Asia/Saigon. Trạng thái thực thi cập nhật tại
[`continuation.json`](continuation.json); log điều phối ở
[`continuation.log`](continuation.log). Chưa coi việc submit notebook là train hoàn tất.

Smoke T11A chỉ kiểm allowlist. Tái hiện tối thiểu: SQL `t35-001` gọi
`labeled_transactions` như bảng, dùng `start_date`/`end_date` trong `WHERE`.
Validator cũ chấp nhận nhưng compiler báo `requires date arguments`.
Smoke mới dùng cùng executor production trên schema rỗng với tám managed relation:
kiểm TVF, số/kiểu đối số ngày, cửa sổ snapshot và bind cột qua DuckDB.
Không cần gold hay dữ liệu snapshot; không suy diễn EX từ kết quả schema rỗng.
T11A runner ghi báo cáo lỗi và dừng trước resume khi smoke thất bại.

Lệnh kiểm độc lập (exit 1 nếu có lỗi):

```bash
eth-nl2sql smoke \
  --predictions reports/gpu-development-t11a/b3-base-smoke-10.jsonl \
  --out .cache/recheck-smoke.json
```

Hai smoke T11A đều bị kiểm tra mới từ chối với **10/10 compile error**;
xem [b3-base](recheck-b3-base.json) và [b3l-base](recheck-b3l-base.json).
Bộ test cuối: **335 passed**, gồm 19 test smoke và kiểm gate runner;
xem [log](tests.log) và [JUnit](tests.xml).
Ruff pass trên `src tests scripts`. Ruff toàn repo còn bảy lỗi định dạng đã có
trong hai notebook mẫu; không sửa notebook ngoài phạm vi này.

## Trình tự phát triển

1. **B1 seed 42**: catalog đầy đủ, 10 câu đầu `dev_eval`, greedy tối đa 512 token,
   model và revision giữ nguyên T11A. Chấm local đúng 10 câu đã sinh; prediction
   manifest giữ trạng thái partial của split 100 câu. Không báo thành accuracy 100 câu.
2. **b3 seed 42**: 4.872 train / 516 dev, QLoRA đã chốt trong `experiment.toml`.
   Chọn checkpoint theo dev loss, sinh 10 câu, kiểm smoke mới. Chỉ resume đủ 100
   nếu cả 10 câu qua smoke; nếu không, tải nguyên artifact để chấm và chẩn đoán.
3. Xem dev loss, valid SQL, EX, runtime, phần cứng và peak PyTorch trên từng GPU.
   Không mở rộng nếu dev loss không hữu hạn, thiếu số đo GPU, valid SQL bằng 0
   hoặc EX bằng 0. Đây là điều kiện tránh nhân rộng một lượt hỏng trên dữ liệu
   phát triển, không phải tiêu chí chấp nhận benchmark.
4. Nếu lượt đầu chạy được, tiếp tục **b3l/42, b3/43, b3l/43, b3/44, b3l/44**,
   lần lượt từng notebook và ghi review sau mỗi lượt.

## B1 catalog đầy đủ — kết quả thật

Kaggle [pilot phiên bản 1](https://www.kaggle.com/code/aohkvd/eth-nl2sql-t11b-pilot-20261028)
đã COMPLETE. Đủ 10 ID đúng thứ tự, provenance/hash download đã kiểm.
**Valid SQL 0/10; EX 0/10** trên DuckDB sample local. Cả mười câu lỗi compile:
TVF bị dùng như bảng hoặc tham chiếu relation/cột mà không JOIN.
Không chỉnh sửa prediction SQL. Prompt có tối đa 1.549 token, cộng 512 token output
vẫn trong context 8.192; không truncate. Catalog đầy đủ chưa giải quyết được lỗi
ở lượt zero-shot này; vẫn cần đo khả năng học cách gọi TVF của QLoRA.

Tài nguyên đo thật: 2×Tesla T4, Python 3.11.15, torch 2.5.1+cu124;
runtime load + generate **114,310 giây**, 1.127 output token;
peak allocated GPU0/GPU1 **2,108 / 3,870 GiB**,
max reserved trên một GPU **4,018 GiB**.
Xem [evaluation](pilot/eval.json), [smoke](pilot/smoke.json),
[case](pilot/cases.jsonl), [download](pilot/download.json),
[manifest generation](../../runs/b1/seed-42/predictions-dev_eval.manifest.json).

`b3` seed 42 đã submit tại
[notebook riêng](https://www.kaggle.com/code/aohkvd/eth-nl2sql-t11b-b3-seed-42-20261028).
Loss và EX của job được ghi vào `b3-seed-42/review.json` sau khi artifact trả về
và chấm local. Trạng thái hiện tại lấy từ `continuation.json`.

Phiên bản 1 của `b3` seed 42 đã load model rồi lỗi trước optimizer step:
`TrainingArguments(data_seed=42)` yêu cầu Accelerate >=1.1.0, trong khi runtime
T11A khóa 0.34.2. Đây là yêu cầu trong
[source Transformers 4.49.0](https://github.com/huggingface/transformers/blob/v4.49.0/src/transformers/training_args.py#L2117).
Đã tái hiện cùng lỗi trên CPU, đổi riêng Accelerate thành 1.4.0 và kiểm args pass.
Một lượt tích hợp CPU với Llama ngẫu nhiên rất nhỏ + LoRA + SQL-only labels đã chạy
hai optimizer step và trả eval loss hữu hạn; đây là kiểm dependency,
**không phải loss hay chất lượng của b3**.
Xem [bằng chứng kiểm runtime](runtime-compatibility.json),
[attempt v1 nguyên vẹn](attempts/b3-seed-42-v1-accelerate/status.json)
và [manifest lỗi thật](attempts/b3-seed-42-v1-accelerate/training-manifest.json).

Lock training mới ở `configs/t11b-gpu-requirements.txt`; lower bound của extra
`gpu` đã nâng lên 1.1. Không đổi seed, model, batch hay hyperparameter.
Notebook v2 đã submit sau khi nén thêm bundle để dưới giới hạn source 1 MB của
Kaggle; kiểm checksum và giải nén đầy đủ đã pass, không bỏ dữ liệu khỏi bundle.

Pilot dùng runtime đã khóa của T11A. Training dùng lock T11B, giữ nguyên mọi pin
ngoại trừ Accelerate **0.34.2 → 1.4.0** để hỗ trợ `data_seed`.
Python 3.11.15, cache model riêng tư được kiểm hash trước load và Kaggle T4.
Quota được đọc trước/sau từng job;
không suy ra chi phí tiền. Peak allocated là peak riêng trên từng GPU,
không cộng các peak khác thời điểm thành peak tổng. Chỉ dùng train/dev/dev_eval;
test v2 giữ nguyên và không vào bundle GPU.

## Artifact và thực hiện lại

Mỗi job có thư mục `pilot/`, `b3-seed-42/`, … chứa input manifest, hash bundle,
trạng thái Kaggle, ZIP nguyên vẹn, hash download, smoke, evaluation, case và review.
Training summary, adapter, checkpoint và provenance ở `runs/<config>/seed-<seed>/`.
Input manifest ghi commit gốc, diff working tree và hash từng file, bao gồm file mới;
không cần commit tự động để nhận diện đúng source đã chạy.

```bash
eth-nl2sql prompts --config b1
python scripts/t11b.py package
python scripts/t11b_notebook.py --output .cache/t11b-pilot \
  --kernel aohkvd/eth-nl2sql-t11b-pilot-20261028 --job pilot
kaggle kernels push -p .cache/t11b-pilot --accelerator NvidiaTeslaT4 --timeout 1800
python -u scripts/t11b_continue.py > reports/gpu-development-t11b/continuation.log 2>&1
```

Controller lưu trạng thái để tiếp tục job đã submit mà không submit trùng. Nếu có
lỗi hoặc review yêu cầu chẩn đoán, nó dừng và lưu nguyên nhân; không tự đổi batch,
seed, model, target hay sửa prediction SQL. File lock chặn hai controller chạy cùng lúc.
Trước lượt kế tiếp, controller ước lượng quota cần từ runtime đã đo, cộng dự phòng
cho bootstrap/generation. Nếu chưa đủ, giữ trạng thái `waiting_for_quota` và kiểm lại
đến khi quota làm mới; không khởi chạy một lượt dài chỉ với quota còn lại rất ít.
Các lượt đủ 100 câu dùng CLI evaluate/report production và cập nhật `RESULTS.md`;
pilot/diagnostic 10 câu chỉ ghi trong thư mục báo cáo này.

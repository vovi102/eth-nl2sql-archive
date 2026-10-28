# T11A — GPU pipeline trên dữ liệu phát triển

Ngày thực hiện: **28/10/2026** (Asia/Saigon). **T11A hoàn tất về hạ tầng**:
[Kaggle phiên bản 1](https://www.kaggle.com/code/aohkvd/eth-nl2sql-t11a-20261028) báo COMPLETE,
hai bộ prediction đủ 100 câu đã tải nguyên vẹn, kiểm resume/provenance và chấm local.
Đầu vào đã chốt tại `9ec8d87`. EX của hai đối chứng đều **0/100**; không dùng accuracy
làm tiêu chí xác nhận hạ tầng. Chất lượng SQL của model chưa đạt.

T07–T10 được commit tại `2d80243` trước khi chuyển dữ liệu sang Kaggle. Các sửa T11A
đọc context thật từ `config.json` ở đúng model revision (8.192 token thay cho sentinel
khoảng 10³⁰ của tokenizer), ghi tỷ lệ bỏ dòng SFT và từ chối chấm prediction chưa đủ split.
Bộ hồi quy: **316 test pass**; Ruff và 1.547 gold SQL pass. Xem [tests.xml](tests.xml)
và [check-sql.json](check-sql.json).

## Kết quả phát triển trên DuckDB sample

| Config, seed 42 | N | EX | Compile error | Không qua validator | Chạm 512 token | Gen p50 / p95 (s) |
|---|---:|---:|---:|---:|---:|---:|
| b3-base | 100 | 0/100 | 84 | 16 | 0 | 13,269 / 19,783 |
| b3l-base | 100 | 0/100 | 89 | 11 | 1 | 16,177 / 24,868 |

Lỗi chính: model gọi các TVF như bảng thường, thiếu đối số ngày (`requires date arguments`);
một số câu dùng tên relation không qualified nên bị validator từ chối. Mọi SQL model đều
dừng ở validator/compiler; evaluator vẫn chạy gold thật trên DuckDB sample để chấm đủ
100 case/config. Không có prediction thực thi thành công nên execution latency của
prediction không có mẫu hợp lệ. Không sửa SQL prediction để tăng điểm.

Hai lượt smoke 10 câu đều qua kiểm tra SQL tĩnh, nhưng kiểm tra đó chưa kiểm chữ ký TVF.
Không tính EX ở lượt smoke. Mỗi cấu hình có hai session thật **10 + 90**; chạy lại limit 10
không sinh thêm dòng, và 10 dòng đầu sau resume giữ nguyên **từng byte**. Mọi manifest
generation đều `complete`, `adapter_sha256=null`, đủ 100 ID duy nhất.

Phần cứng thực: **2×Tesla T4**, Python 3.11.15, torch 2.5.1+cu124. Memory là peak PyTorch
trên từng GPU, không cộng các peak khác thời điểm thành peak tổng:

| Config | Peak allocated GPU0 / GPU1 (GiB) | Max reserved trên một GPU (GiB) | Runtime 10+90, gồm load (phút) | Output token |
|---|---:|---:|---:|---:|
| b3-base | 1,968 / 3,661 | 3,742 | 23,129 | 20.641 |
| b3l-base | 1,998 / 3,707 | 3,871 | 27,378 | 24.215 |

Ca chạm token limit là `t35-091` của b3l-base. Runtime từng process/CLI nằm trong
[stages.json](stages.json); runtime/model/hardware/token/memory từng session nằm trong
manifest prediction. Quota GPU tài khoản tăng 55 phút 10,162 giây giữa hai lần đọc,
không còn quota reserved sau khi kết thúc; không quy đổi thành chi phí tiền.

Bằng chứng: [summary.json](summary.json), [trạng thái hoàn tất](status.json),
[b3-base evaluation](../../runs/b3-base/seed-42/eval-dev_eval.json),
[b3l-base evaluation](../../runs/b3l-base/seed-42/eval-dev_eval.json),
[resume b3-base](b3-base-resume.json), [resume b3l-base](b3l-base-resume.json),
[ZIP gốc tải về](artifacts.zip), [hash download](download-manifest.json),
[manifest đầu vào](inputs-manifest.json), [metadata notebook/source](kaggle-kernel.json),
[log worker](bootstrap/gpu-pipeline.log), [chi tiết lỗi SQL](sql-errors.json),
[kiểm tra toàn vẹn cuối](final-integrity.json), [bảng kết quả](../../RESULTS.md).

## Đầu vào và phạm vi

- Generator: `meta-llama/Meta-Llama-3-8B-Instruct` tại
  `8afb486c1db24fe5011ec46dfbe5b5dccdb575c2`; NF4 4-bit, greedy, seed generation 42,
  tối đa 512 token đầu ra. Hai config `b3-base` và `b3l-base` đều không adapter.
- Encoder: `sentence-transformers/all-MiniLM-L6-v2` tại
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Cả 11 file local đã kiểm hash, gồm trọng số;
  xem [encoder-files.json](encoder-files.json). Dựng toàn bộ train/dev/dev_eval cùng
  encoder, dictionary, schema, runtime và thiết bị. Không dùng cache lexical/fuzzy của T08
  để thay thế encoder trong lượt T11A.
- Train/dev/dev_eval lần lượt 4.872/516/100 câu. Prompt compact của mỗi base control phải
  trùng messages và prompt hash với cấu hình QLoRA tương ứng. Chỉ chạy preflight SFT;
  T11A không huấn luyện adapter.
- Test v2 giữ draft và không thay đổi. Không đưa câu hỏi, gold hay annotation test v2 vào
  bundle GPU. Bundle chỉ có projection ID/question của dev_eval; gold dev_eval nằm local.
- Dùng cache model riêng tư `aohkvd/nl2sql-environment-cache`, phiên bản đã kiểm 5.
  HF token local không truy cập được revision; dùng cache của tài khoản hiện có, không
  đổi model và không ghi token vào source/artifact. Kiểm lại toàn bộ 13 file generator
  trong chính phiên GPU trước khi load model.

## Preflight thật và lỗi đã xử lý

Model context là **8.192 token**; SFT dùng **1.024 token**, gồm toàn bộ SQL và EOT,
không truncate. Kết quả cuối sau khi sửa renderer:

| Config | Split | Đầu vào | Giữ lại | Bỏ | Tỷ lệ bỏ | Dài nhất |
|---|---|---:|---:|---:|---:|---:|
| b3 | train | 4.872 | 4.872 | 0 | 0% | 649 |
| b3 | dev | 516 | 516 | 0 | 0% | 649 |
| b3l | train | 4.872 | 4.872 | 0 | 0% | 786 |
| b3l | dev | 516 | 516 | 0 | 0% | 757 |

Preflight đầu tiên phát hiện 3 prompt inference có hơn 53.000 token: renderer liệt kê
5.055 owner của lớp TokenContract cho mỗi mention. Hint được sửa thành predicate lớp
và số owner đã gán nhãn. Giữ nguyên full membership trong JSON linking và SQL target;
không xóa dòng, không cắt chuỗi theo số token. `b3l-base` cuối có input tối đa **550 token**,
cả 100 câu đều nằm trong context kể cả 512 token generation. Trước sửa, SFT b3l bỏ
219/4.872 train (4,495%) và 7/516 dev (1,357%); đây là diagnostic cũ, không phải bộ input
đưa lên Kaggle. Xem [chẩn đoán](large-class-diagnosis.json),
[bằng chứng linking giữ nguyên](linking-preserved-after-render-fix.json) và
[context/tokenizer](tokenizer-context.json).

## Thực hiện lại

Chuẩn bị linking bằng môi trường Python 3.11 có extra `embed`. Lượt này dùng torch 2.5.1
CUDA 12.4, sentence-transformers 3.4.1, transformers 4.49.0, NumPy 2.4.6, rapidfuzz 3.14.5
trên GTX 1650; thiết bị CUDA chỉ dành cho encoder. Một lượt CPU ban đầu bị dừng trước khi
lưu split; cả ba split cuối được dựng lại cùng nhau. Xem
[local-environment.json](local-environment.json), [linking-runtime.json](linking-runtime.json)
và [log chuẩn bị](linking-preparation.log).

```bash
uv venv --python 3.11.15 .cache/t11a-linking
uv pip install --python .cache/t11a-linking/bin/python -e '.[embed]' \
  -c configs/t11-gpu-constraints.txt \
  sentence-transformers==3.4.1 numpy==2.4.6 rapidfuzz==3.14.5
.cache/t11a-linking/bin/python scripts/t11a_prepare.py --device cuda
# Nếu chỉ có CPU, dựng lại cả ba split với --device cpu và tạo run mới.
eth-nl2sql preflight --config b3 --training
eth-nl2sql preflight --config b3l --training
# Commit code/config/inputs trước khi đóng gói.
python scripts/t11a.py package
python scripts/t11a_notebook.py
kaggle kernels push -p .cache/t11a-kaggle --accelerator NvidiaTeslaT4 --timeout 7200
```

Notebook tạo Python 3.11.15 và cài dependency có hash từ
[`t11-gpu-requirements.txt`](../../configs/t11-gpu-requirements.txt), ngoài môi trường global
Kaggle. Lock mặc định hiện dùng CUDA 13; lock T11 dùng torch 2.5.1/CUDA 12.4 cho T4.
Model/encoder revision và tham số thực nghiệm vẫn lấy từ `experiment.toml`. Cache model
được mount đọc, không copy 16 GB trọng số vào working output; không cần truy cập HF bằng
secret trong saved notebook API.

GPU runner gọi CLI production bằng process riêng: preflight b3/b3l và hai base control;
sinh 10 câu/config; kiểm ID, content/provenance hash, output không rỗng và SQL tĩnh; lưu
snapshot lượt 10 câu; chạy lại `--limit 10` để kiểm không sinh trùng; tiếp tục 90 câu còn
lại. Kiểm đủ 100 ID duy nhất, manifest complete và 10 dòng đầu giữ nguyên từng trường.
Lượt 10 câu chỉ kiểm output/provenance/resume, không tính hoặc suy diễn EX trên 100 câu.

Tải nguyên ZIP và chấm trên DuckDB sample local:

```bash
kaggle kernels output aohkvd/eth-nl2sql-t11a-20261028 \
  -p .cache/t11a-download --file-pattern '^t11a-artifacts[.]zip$' --page-size 200
python scripts/t11a.py collect --archive .cache/t11a-download/t11a-artifacts.zip
for config in b3-base b3l-base; do
  eth-nl2sql evaluate --config "$config" --split dev_eval --seed 42
done
python scripts/t11a.py summarize
eth-nl2sql report
```

`collect` kiểm hash mọi file trong ZIP trước khi ghi, giữ nguyên SFT/prompt đã chuẩn bị,
kiểm lại prediction/provenance và đủ 100 câu cho cả hai config trước khi EX. Summary chỉ
được đánh dấu complete khi có EX đủ 100 câu, bằng chứng resume và GPU measurements thật.
`summary.json` ghi EX/CI, lỗi SQL theo loại, số lần chạm trần token, latency p50/p95,
runtime từng session và peak allocated/reserved GPU memory. Peak là số đo của PyTorch;
latency generation không bao gồm thời gian load model, thời gian load nằm trong session runtime.

Để chạy một lượt mới, dùng kernel/run directory mới thay vì ghi đè artifact đã dẫn ở đây.
Nếu sửa riêng renderer, xuất lại cả prompt/SFT và chạy preflight; không cần thay dữ liệu
membership linking. Chẩn đoán và lượt CPU bị dừng được giữ riêng, không đưa vào kết quả GPU.

Đây luôn là **development evaluation trên DuckDB sample** (`complete_snapshot=false`),
không phải test v2, parity BigQuery hay kết quả benchmark cuối. T11A không đặt ngưỡng EX.

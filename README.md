# eth-nl2sql

Hệ thống cho phép người dùng hỏi bằng tiếng Anh và nhận kết quả từ dữ liệu Ethereum mà không
cần tự viết SQL. Đối tượng sử dụng là người phân tích an ninh, AML và nghiên cứu blockchain.
LLM sinh GoogleSQL với hỗ trợ schema/entity linking, sau đó SQL được kiểm tra và thực thi
trên DuckDB dựng từ dữ liệu BigQuery public Ethereum.

Phạm vi nghiên cứu là Ethereum mainnet, một schema phân tích cố định và các thực thể đã có
trong dictionary. Các truy vấn cung cấp dữ liệu phục vụ phân tích; chưa đánh giá khả năng
kết luận hành vi rửa tiền hoặc hỗ trợ điều tra hoàn chỉnh. Xem
[METHODOLOGY.md](METHODOLOGY.md) cho phương pháp, thiết kế thí nghiệm và giới hạn.

## Ba đóng góp dự kiến

Ba đóng góp có vai trò ngang nhau; hiệu quả nghiên cứu còn cần được thực nghiệm xác nhận.

| Đóng góp | Mục tiêu và bằng chứng cần thu thập |
|---|---|
| Dataset Ethereum NL–SQL | Câu hỏi tiếng Anh và SQL chuẩn; công bố độ phủ tác vụ, số SQL/template/paraphrase, kiểm gold, leakage và human review |
| Schema/entity linking | Xử lý nhiều địa chỉ, alias, câu hỏi theo lớp và property; đo linking trực tiếp, EX theo hiện tượng, baseline và ablation |
| Phân tích fine-tuning | So zero-shot, five-shot và QLoRA có/không linking; đo accuracy, biến thiên huấn luyện, latency, chi phí và điều kiện triển khai/privacy |

Blockchain đã xuất hiện trong benchmark tổng quát như [BIRD, mục 3.2](https://arxiv.org/html/2305.03111v3).
Khoảng trống về benchmark chuyên Ethereum có nhãn cho cả bốn hiện tượng linking cần được
khảo sát xác nhận; project chưa tuyên bố là dataset blockchain NL–SQL đầu tiên.

## Kiến trúc và nguồn dữ liệu

Có ba loại dữ liệu: blockchain lấy từ `bigquery-public-data.crypto_ethereum`, dictionary
nhãn owner/alias/lớp và dataset câu hỏi–SQL do project xây dựng dựa trên schema đó.

```text
Luồng chuẩn bị dữ liệu:
BigQuery public Ethereum → trích xuất/bổ sung dữ liệu → Parquet → DuckDB + managed layer
                                                              ↑
                                                   dictionary nhãn thực thể

Luồng trả lời câu hỏi:
Câu hỏi tiếng Anh → Schema linker + Entity linker → Resolver → Linking hints
  → Prompt → LLM (± QLoRA) → Trích SQL → Validator → SQLGlot → DuckDB → Kết quả
```

Model sinh GoogleSQL; SQLGlot chuyển SQL sang DuckDB khi thực thi. Managed layer có tám
relation được phép truy vấn. Cửa sổ dữ liệu là UTC `[2026-05-31, 2026-07-01)`.

**Hiện trạng:** DuckDB dùng dữ liệu giao dịch đã lọc/lấy mẫu từ bộ CSV kế thừa, có bổ sung
thuộc tính từ BigQuery. Snapshot đầy đủ và parity BigQuery **chưa hoàn tất**. EX trên store
này là kết quả phát triển trong phạm vi sample. `parity` yêu cầu snapshot đầy đủ và dictionary
v1 để đối chiếu fixture cũ; chạy `echo-gold` không chứng minh tương đương BigQuery.

## Dataset và giao thức nghiên cứu

Dataset hiện tại có **4.872 câu train / 516 dev / 100 dev_eval**, tương ứng **1.218 / 129 / 100
SQL phân biệt**. Train/dev có 25 template chung và 10 template thực thể, mỗi SQL có bốn cách
diễn đạt. Bộ 100 câu hiện tại gồm 50 câu chung và 50 câu thực thể; đã review bằng agent,
**human review còn chờ**. Bộ này đã được xem trong quá trình thiết kế và được xem là bộ
đánh giá phát triển. T07 đã chuyển nguyên vẹn sang `data/dev_eval.jsonl` và split `dev_eval`;
mặc định CLI dùng split này. Review cũ ở `data/dev_eval-review.json`. Annotation mới có review riêng và đều pending.

**T09A đã soạn test v2, vẫn là draft:** `data/benchmark/v2/` có 100 câu mới cùng gold SQL,
annotation trực tiếp và hồ sơ human review pending. Phân bố gồm
20 câu chung và 20 câu chính cho mỗi hiện tượng `multi_address`, `alias`, `class_level`, `ambiguous_property`;
cho phép nhãn phụ chồng lấn. Dùng holdout train/dev/test và ba seed QLoRA, không yêu cầu
cross-validation. Train/dev giữ nguyên; kiểm hash/leakage với train/dev/dev_eval và thực thi
gold trên sample được ghi trong [báo cáo T09A](reports/benchmark-t09a/README.md).
T09B chờ T06 để kiểm lại gold/witness/ca rỗng trên snapshot đầy đủ và hoàn tất human review
trước khi đóng băng; sample không đáp ứng gate phát hành.

Truy vấn theo lớp chỉ bao phủ các thực thể đã gán nhãn, ví dụ “any DEX”; benchmark v2 bỏ từ
“major”. Resolver đã có ba property: gửi/nhận/cả hai, transaction/token event/join và
token contract/endpoint; thiếu bằng chứng thì giữ `null` khi xuất JSON. Baseline, bốn
ablation và bộ chấm linking trực tiếp đã có; kết quả lexical/fuzzy dùng annotation nháp
chỉ là [đánh giá phát triển](reports/linking-development/README.md). T10 đã bổ sung đối chứng
prompt compact và hạ tầng ba seed. T11A đã chạy thật hai đối chứng compact trên Kaggle,
resume 10 → 100 câu/config và chấm local: EX đều 0/100 do SQL không qua validator/compiler.
Đây là kiểm chứng hạ tầng trên dữ liệu phát triển, không dùng ngưỡng accuracy để xác nhận.
Xem [báo cáo T11A và tài nguyên](reports/gpu-development-t11a/README.md),
[hướng dẫn T10](reports/experiments-t10/README.md)
và [thiết kế phương pháp](METHODOLOGY.md).

## Cài đặt

```bash
uv sync --locked                  # lõi: validator, DuckDB store, đánh giá
uv sync --locked --extra embed    # linking và retrieval (MiniLM, kéo theo torch)
uv sync --locked --extra bq       # trích/bổ sung dữ liệu từ BigQuery
uv run --locked pytest -q
uv run --locked ruff check src tests
uv run --locked eth-nl2sql check-sql
```

Extra `gpu` dùng trên Kaggle qua [notebook dự đoán](notebooks/kaggle_predict.ipynb) và
[notebook huấn luyện](notebooks/kaggle_train.ipynb). Kaggle là môi trường cloud; prompt được
chuyển lên đó khi sinh SQL. Chạy model trên Kaggle không đồng nghĩa với inference cục bộ.

## Quy trình hiện có

Các lệnh dưới đây dùng artifact phát triển; test v2 hiện có 100 câu draft. `--split test` yêu cầu
benchmark đã đóng băng, hash hợp lệ và human review đầy đủ.
Sau cài đặt, chạy lệnh CLI bằng `uv run --locked eth-nl2sql ...`.

| Bước | Lệnh CLI / notebook | Ghi chú |
|---|---|---|
| Kiểm SQL của dataset | `eth-nl2sql check-sql` | offline, không cần store |
| Sinh train/dev thực thể | `eth-nl2sql build-entity-data` | 10 template; giữ dữ liệu chung, không tạo test v2 |
| Kiểm dataset và gold | `eth-nl2sql check-dataset` | train/dev/dev_eval trên DuckDB; ghi báo cáo |
| Kiểm annotation | `eth-nl2sql check-annotations` | schema, mention, owner/address/class, ba property, hash review; `--require-human` kiểm human review |
| Kiểm benchmark v2 | `eth-nl2sql check-benchmark` | cấu trúc/hash/leakage và gold; `--skip-execution` để kiểm offline; `--require-release` kiểm điều kiện phát hành |
| Đóng băng benchmark | `eth-nl2sql freeze-benchmark` | chỉ khi đủ 100 câu, cân bằng 20×5, human review và full snapshot; từ chối ghi đè bản frozen |
| Kiểm CSV đã nhập | `eth-nl2sql check-data` | cần bộ CSV local; ghi báo cáo chất lượng |
| Kiểm join của CSV | `eth-nl2sql local-plan` | ghi mapping và tỷ lệ join |
| Ước lượng phần bổ sung | `eth-nl2sql supplement-plan --project P` | dry-run BigQuery; cần ADC |
| Tải phần bổ sung | `eth-nl2sql supplement-run --project P` | sử dụng quota BigQuery; ghi provenance/checksum |
| Chuyển CSV đã bổ sung | `eth-nl2sql prepare-local` | xuất Parquet, giữ nhãn dữ liệu lấy mẫu |
| Ước lượng snapshot | `eth-nl2sql snapshot-plan --project P` | dry-run BigQuery; cần ADC |
| Trích snapshot | `eth-nl2sql snapshot-run --project P` | sử dụng quota BigQuery; ghi dữ liệu |
| Dựng store | `eth-nl2sql build-store` | mặc định dictionary v2; `--labels data/entities/v1` cho parity kế thừa |
| Kiểm dictionary | `eth-nl2sql check-dictionary` | địa chỉ, owner, alias, nhóm, nguồn, ngày và checksum |
| Đo hiện diện dictionary | `eth-nl2sql dictionary-coverage` | đo trên raw tables local; không đại diện toàn mạng |
| Kiểm parity | `eth-nl2sql parity` | cần snapshot đầy đủ + v1; 88 gold BigQuery và 206 witness |
| Linking | `eth-nl2sql link --split dev_eval` | hỗ trợ cả `train`, `dev`; CPU |
| Linking sáu biến thể | `eth-nl2sql link --split dev_eval --variant all --no-encoder` | full, baseline và bốn ablation; lexical/fuzzy, giữ cùng schema linker |
| Chấm linking trực tiếp | `eth-nl2sql evaluate-linking --variant full` | schema recall, entity/address-set, class/membership và từng property; audit annotation/review trước khi chấm |
| Dựng bộ prompt đối chứng | `eth-nl2sql link-experiments --split dev_eval` | `b2`, `b2l`, `b2l-baseline`, `b2l-no-multi-address`, `b2l-no-alias`, `b2l-no-class`, `b2l-no-property`; retrieval dùng chung |
| Dựng prompt | `eth-nl2sql prompts --config b2l` | thêm `b3-base`/`b3l-base` có prompt giống hệt QLoRA; `--training` dành cho `b3`/`b3l` |
| Preflight | `eth-nl2sql preflight --config b3 --training --seed all` | kiểm input/token, giữ/bỏ dòng; chỉ tải tokenizer, không tải model |
| Kiểm chứng GPU phát triển T11A | `scripts/t11a_prepare.py`, `scripts/t11a.py`, `scripts/t11a_notebook.py` | quy trình đã chạy thật, input/ZIP có hash; [lệnh và kết quả T11A](reports/gpu-development-t11a/README.md) |
| Train ba seed | `eth-nl2sql train --config all --seed all` | sáu lượt `b3`/`b3l` × 42/43/44; `--resume` kiểm provenance |
| Sinh SQL / train | `notebooks/kaggle_predict.ipynb`, `notebooks/kaggle_train.ipynb` | GPU Kaggle T4 |
| Đánh giá | `eth-nl2sql evaluate --config b3l --seed all` | artifact riêng `runs/<config>/seed-<seed>/`; thực thi trên DuckDB local |
| Báo cáo | `eth-nl2sql report` | từng seed, mean/SD mẫu (ddof=1), N câu dùng chung; thêm `runs/seed-summary-dev_eval.json` |

`eth-nl2sql echo-gold` rồi `eth-nl2sql evaluate --config gold-echo` dùng gold làm dự đoán;
EX phải bằng 100%. Đây là kiểm tra đường ống, không phải accuracy của model.

Chi tiết chuẩn bị input, lệnh chạy hai đối chứng và ma trận sáu lượt, layout artifact,
resume và báo cáo tài nguyên nằm trong [báo cáo T10](reports/experiments-t10/README.md).
Seed generation/bootstrap vẫn là 42, độc lập với seed huấn luyện. File prediction cũ không
có manifest sẽ không được tự động tái sử dụng. `--split test` vẫn bị chặn khi benchmark draft.

## Cấu trúc repo

```text
configs/   catalog.json · experiment.toml · schema_synonyms.json
data/      train/dev/dev_eval.jsonl · dev_eval-annotations/reviews · benchmark/v2/
           entities/ · templates/ · raw/luanvan/ · store/
src/eth_nl2sql/
  store/       snapshot · build · execute · parity
  linking/     dictionary · entity · schema · resolver · context · variants · evaluate
  generation/  prompt · retrieval · runs · extract · backend
  data/        splits · annotations · benchmark · dataset_audit · entities
  validation.py · results.py · evaluate.py · report.py · experiments.py · train_qlora.py · cli.py
notebooks/ kaggle_predict.ipynb · kaggle_train.ipynb
reports/   data-quality/ · local-store/ · dictionary-v2/ · entity-dataset/ · benchmark-t07/ · benchmark-t09a/
           linking-development/ · experiments-t10/ · gpu-development-t11a/
```

## Trạng thái và bằng chứng

Đối chiếu tài liệu/artifact ngày **28/10/2026**; các báo cáo T02–T06 ghi ngày
26/10/2026; T07 ghi ngày 27/10/2026. Chi tiết nguồn và quan hệ với `luanvan` nằm trong phần provenance của
[METHODOLOGY.md](METHODOLOGY.md).

| Hạng mục | Hiện trạng | Bằng chứng / việc còn thiếu |
|---|---|---|
| Pipeline lõi | Đã có validator, store, linking, prompt và bộ đánh giá | [Kiểm tra lõi](VALIDATION.md) |
| Dữ liệu blockchain local | CSV đã kiểm chất lượng; Parquet/DuckDB phát triển đã dựng, vẫn là sample | [Chất lượng CSV](reports/data-quality/luanvan.md), [store local](reports/local-store/README.md) |
| Snapshot và parity | T06: chuẩn bị/dry-run xong; kiểm nghiệm hoãn theo yêu cầu | [Ghi chú T06 và cách thực hiện sau](reports/snapshot-t06/README.md) |
| Dictionary v2 | Đã có nhiều địa chỉ, alias, lớp và báo cáo hiện diện | [Dictionary](data/entities/v2/README.md), [kiểm chứng](reports/dictionary-v2/README.md) |
| Dataset hiện tại | Đã kiểm gold và review agent; human review còn chờ | [Dataset và hồ sơ kiểm](reports/entity-dataset/README.md) |
| Benchmark v2 | T09A: 100 câu/SQL, annotation và hồ sơ review; draft, chờ full snapshot và human review ở T09B | [Báo cáo T09A](reports/benchmark-t09a/README.md), [giao thức annotation](data/benchmark/README.md) |
| Linking và ablation | Resolver ba property, baseline, bốn ablation, runner dùng chung retrieval và bộ chấm trực tiếp đã có | [Đánh giá phát triển với annotation nháp](reports/linking-development/README.md) |
| Kiểm chứng GPU | T11A hoàn tất: hai base control không adapter, 100 câu/config, resume thật, provenance và tài nguyên; EX phát triển đều 0/100, mọi SQL dừng ở validator/compiler | [Báo cáo T11A](reports/gpu-development-t11a/README.md), [kết quả](RESULTS.md) |
| Thực nghiệm nghiên cứu | Runner ba seed và ablation đã có; chưa huấn luyện QLoRA hoặc chạy ma trận test frozen | [Hướng dẫn T10](reports/experiments-t10/README.md), [phương pháp](METHODOLOGY.md) |

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

Dataset hiện tại có **4.872 câu train / 516 dev / 100 test**, tương ứng **1.218 / 129 / 100
SQL phân biệt**. Train/dev có 25 template chung và 10 template thực thể, mỗi SQL có bốn cách
diễn đạt. Bộ 100 câu hiện tại gồm 50 câu chung và 50 câu thực thể; đã review bằng agent,
**human review còn chờ**. Bộ này đã được xem trong quá trình thiết kế và được xem là bộ
đánh giá phát triển. File `data/test.jsonl` và các lệnh hiện tại vẫn dùng tên split `test`.

**Thiết kế đích, chưa triển khai:** tạo test v2 gồm 100 câu mới, với 20 câu chung và 20 câu
chính cho mỗi hiện tượng `multi_address`, `alias`, `class_level`, `ambiguous_property`;
cho phép nhãn phụ chồng lấn. Dùng holdout train/dev/test và ba seed QLoRA, không yêu cầu
cross-validation. Giữ quy mô train/dev hiện tại làm nền, bổ sung kiểm leakage với test v2.

Truy vấn theo lớp chỉ bao phủ các thực thể đã gán nhãn, ví dụ “any DEX”; benchmark v2 bỏ từ
“major”. Property gồm gửi/nhận, transaction/token event và token contract/endpoint; resolver
hiện chủ yếu hỗ trợ chiều gửi/nhận. Đối chứng prompt compact, baseline linking thông thường,
bốn ablation và chỉ số linking trực tiếp đều là phần cần triển khai theo
[thiết kế phương pháp](METHODOLOGY.md).

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

Các lệnh dưới đây dùng artifact hiện tại; chưa tạo test v2, đối chứng mới hoặc các ablation.
Sau cài đặt, chạy lệnh CLI bằng `uv run --locked eth-nl2sql ...`.

| Bước | Lệnh CLI / notebook | Ghi chú |
|---|---|---|
| Kiểm SQL của dataset | `eth-nl2sql check-sql` | offline, không cần store |
| Sinh train/dev thực thể | `eth-nl2sql build-entity-data` | 10 template; giữ dữ liệu chung, không tạo test v2 |
| Kiểm dataset và gold | `eth-nl2sql check-dataset` | chạy gold trên DuckDB; ghi báo cáo, có thay đổi artifact báo cáo |
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
| Linking | `eth-nl2sql link --split test` | hỗ trợ cả `train`, `dev`; CPU |
| Dựng prompt | `eth-nl2sql prompts --config b2l` | sáu cấu hình `b1 b1l b2 b2l b3 b3l`; `--training` dành cho QLoRA |
| Sinh SQL / train | `notebooks/kaggle_predict.ipynb`, `notebooks/kaggle_train.ipynb` | GPU Kaggle T4 |
| Đánh giá | `eth-nl2sql evaluate --config b2l` | thực thi trên DuckDB local |
| Báo cáo | `eth-nl2sql report` | ghi đè `RESULTS.md` từ các lượt đã đánh giá |

`eth-nl2sql echo-gold` rồi `eth-nl2sql evaluate --config gold-echo` dùng gold làm dự đoán;
EX phải bằng 100%. Đây là kiểm tra đường ống, không phải accuracy của model.

## Cấu trúc repo

```text
configs/   catalog.json · experiment.toml · schema_synonyms.json
data/      train/dev/test.jsonl · entities/ · templates/ · raw/luanvan/ · store/
src/eth_nl2sql/
  store/       snapshot · build · execute · parity
  linking/     dictionary · entity · schema · resolver · context
  generation/  prompt · retrieval · runs · extract · backend
  validation.py · results.py · evaluate.py · report.py · train_qlora.py · cli.py
notebooks/ kaggle_predict.ipynb · kaggle_train.ipynb
reports/   data-quality/ · local-store/ · dictionary-v2/ · entity-dataset/
```

## Trạng thái và bằng chứng

Đối chiếu tài liệu/artifact ngày **27/10/2026**; các báo cáo triển khai bên dưới ghi ngày
26/10/2026. Chi tiết nguồn và quan hệ với `luanvan` nằm trong phần provenance của
[METHODOLOGY.md](METHODOLOGY.md).

| Hạng mục | Hiện trạng | Bằng chứng / việc còn thiếu |
|---|---|---|
| Pipeline lõi | Đã có validator, store, linking, prompt và bộ đánh giá | [Kiểm tra lõi](VALIDATION.md) |
| Dữ liệu blockchain local | CSV đã kiểm chất lượng; Parquet/DuckDB phát triển đã dựng, vẫn là sample | [Chất lượng CSV](reports/data-quality/luanvan.md), [store local](reports/local-store/README.md) |
| Snapshot và parity | Chưa hoàn tất snapshot đầy đủ và đối chiếu BigQuery | [Phạm vi và cách chạy parity](reports/local-store/README.md) |
| Dictionary v2 | Đã có nhiều địa chỉ, alias, lớp và báo cáo hiện diện | [Dictionary](data/entities/v2/README.md), [kiểm chứng](reports/dictionary-v2/README.md) |
| Dataset hiện tại | Đã kiểm gold và review agent; human review còn chờ | [Dataset và hồ sơ kiểm](reports/entity-dataset/README.md) |
| Benchmark v2 | Mới là thiết kế; chưa tạo 100 câu test mới hoặc chuyển đổi artifact cũ | [Phương pháp](METHODOLOGY.md) |
| Thực nghiệm nghiên cứu | Chưa có lượt LLM được báo cáo; thiếu đối chứng, ablation, chỉ số linking và tổng hợp ba seed | [Trạng thái kết quả](RESULTS.md) |

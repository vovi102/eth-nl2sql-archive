# T03 — Từ CSV lịch sử đến store phát triển

Luồng này dùng bộ CSV trong `data/raw/luanvan/`, giữ nguyên dữ liệu nguồn và phạm vi lấy mẫu.
Các cột thiếu phải có nguồn thực tế; không suy đoán transaction index, gas thực dùng hoặc
metadata token. Đây là store phát triển, chưa phải snapshot đầy đủ để so parity BigQuery.

## Mapping đã đo trên dữ liệu thực

| Join | Dòng đầu vào | Khớp | Không khớp | Lệch timestamp |
|---|---:|---:|---:|---:|
| Giao dịch → block theo block number | 4.431.329 | 4.431.329 | 0 | 0 |
| Token transfer → giao dịch theo hash | 4.001.230 | 4.001.230 | 0 | 0 |
| Contract → block local theo timestamp | 3.513 | 10 | 3.503 | 0 |

Quan sát được **15.276 token address** trong token transfer. Xem [plan.json](plan.json).

- `transactions.block_hash`: từ block đã join.
- `token_transfers.block_number/block_hash`: từ giao dịch và block đã join.
- Transaction index, receipt gas used và receipt contract address: bổ sung từ BigQuery.
- Base fee của block: bổ sung từ BigQuery.
- Block number/hash của contract lịch sử và metadata các token contract quan sát được: BigQuery.
- Symbol/name/decimals: bảng BigQuery `amended_tokens`.

## Kết quả thực thi ngày 26/10/2026

Đã dựng `data/store/eth.duckdb` từ năm bảng Parquet có đầy đủ cột cho managed layer:

| Bảng | Số dòng |
|---|---:|
| transactions | 4.431.329 |
| blocks | 221.548 |
| token_transfers | 4.001.230 |
| contracts | 16.386 |
| amended_tokens | 2.489.651 |
| entity_labels_snapshot (dictionary v1) | 5.135 |

Năm phép đếm qua các hàm facts/labeled đều khớp số giao dịch/block/transfer gốc; join metadata
và nhãn không nhân dòng. Tổng `value_wei` khớp chính xác với CSV bằng DECIMAL, không qua float.
Không thiếu transaction index, receipt gas used hoặc block hash sau bổ sung. Có 701 receipt
tạo contract, phù hợp 701 `to_address` trống trong CSV.

**122 test pass**, lint sạch; gold-echo **50/50**, EX và valid SQL đều 100% trên store này.
Đây là kiểm tra đường ống, chưa phải kết quả model. `parity` được xác nhận trả skipped/exit 1
do scope lấy mẫu. Chi tiết tại [validation.json](validation.json).

Có **2.110 contract lịch sử** khác cờ ERC so với dữ liệu BigQuery đọc lại; store giữ cờ CSV
để bảo toàn ngữ nghĩa nguồn và ghi số khác biệt trong manifest. Chỉ 1.290.700 transfer có
`normalized_amount`; không suy đoán metadata hoặc chuẩn hóa những dòng không đạt điều kiện ERC.
Các giới hạn này phải được giữ khi diễn giải kết quả phát triển.

## API và đăng nhập

[BigQuery API](https://docs.cloud.google.com/bigquery/docs/reference/rest) thực thi SQL trên
`bigquery-public-data.crypto_ethereum`; [BigQuery Storage Read API](https://docs.cloud.google.com/bigquery/docs/reference/storage)
đọc kết quả theo luồng Arrow. Xem/bật dịch vụ trong Google Cloud Console → APIs & Services →
Library của project chạy query, hiện dùng `nl2sparql-thesis`.

Python dùng thư viện trong extra `bq` và [Application Default Credentials (ADC)](https://docs.cloud.google.com/docs/authentication/application-default-credentials).
Máy hiện tại đã có ADC của gcloud tại `~/.config/gcloud/application_default_credentials.json`.
Khi thiết lập máy khác, chạy `gcloud auth application-default login` rồi chọn project qua
`--project`. Credential chỉ lưu local, không đưa vào manifest hoặc Git.

## Chạy lại

```bash
uv sync --locked --extra bq
uv run --locked eth-nl2sql local-plan
uv run --locked eth-nl2sql supplement-plan --project nl2sparql-thesis
uv run --locked eth-nl2sql supplement-run --project nl2sparql-thesis
uv run --locked eth-nl2sql prepare-local
uv run --locked eth-nl2sql build-store --labels data/entities/v1
uv run --locked eth-nl2sql echo-gold
uv run --locked eth-nl2sql evaluate --config gold-echo
```

BigQuery dùng ADC của người chạy. Dry-run ban đầu ước tính tổng **30,454 GiB** cho bốn truy vấn;
mỗi query thật có `maximum_bytes_billed=50 GiB`. Ước lượng không chứng minh chi phí bằng không;
xem cơ chế [kiểm soát chi phí BigQuery](https://docs.cloud.google.com/bigquery/docs/best-practices-costs).
Tổng query bytes billed thực tế là **28,270 GiB**; con số này không bao gồm lượng đọc Storage API
và không phải số tiền thanh toán. Job ID và lượng billed từng query nằm trong [supplements.json](supplements.json).

`supplement-run` chỉ dùng lại file khi query/input binding và SHA-256 còn khớp. `prepare-local`
kiểm lại CSV, kiểm checksum/schema/khóa của phần bổ sung và từ chối nếu join bỏ sót hoặc đổi số dòng.
Mặc định tải qua Storage API; dùng `--rest` nếu cần tải qua REST. Job đã hoàn tất được ghi vào
manifest để tải lại kết quả khi gián đoạn mà không chạy lại SQL.
Nếu thư mục Parquet đã tồn tại, chọn thư mục khác bằng `--parquet`; lệnh không ghi đè bản cũ.
Các bước bổ sung/chuẩn bị còn có cờ `--directory`, `--supplements` để chọn đầu vào.

## Artifact

| Vị trí | Nội dung |
|---|---|
| `data/store/supplements/` | Metadata bổ sung, query/input hash, checksum và job ID |
| `data/store/parquet/` | Năm bảng có đầy đủ cột cho managed layer và manifest |
| `data/store/eth.duckdb` | Store có tám managed object, dictionary v1 và metadata scope |
| `reports/local-store/plan.json` | Mapping và join đo trên dữ liệu thực |
| `reports/local-store/supplement-plan.json` | Dry-run của bốn truy vấn bổ sung |
| `reports/local-store/supplements.json` | Bản lưu provenance/checksum của phần bổ sung thực tế |
| `reports/local-store/parquet-manifest.json` | Bản lưu manifest Parquet đã dùng để dựng store |
| `reports/local-store/validation.json` | Phép đếm, kiểm giá trị, metadata coverage và gold-echo |

CSV, Parquet và DuckDB lớn chỉ lưu local. Manifest và báo cáo có thể lưu trong Git.

## Phạm vi kiểm chứng

`build-store` kiểm manifest, checksum, số dòng và cột của mọi file Parquet, từ chối file thiếu/thừa.
Snapshot khai báo đầy đủ phải có đủ 95 file dự kiến cho cửa sổ 31 ngày. Database được dựng ở
vị trí tạm và chỉ thay bản cũ khi thành công; lỗi dữ liệu/nhãn không làm mất store trước đó.

`evaluate` ghi scope cùng hash dữ liệu/nhãn trong kết quả. `gold-echo` là kiểm tra đường ống;
EX 100% ở bước này không phải accuracy của model hoặc bằng chứng snapshot đầy đủ. Chưa có
kết quả thực nghiệm LLM ở T03.

`parity` trên store này trả trạng thái skipped và exit code 1. Để kiểm parity chính thức,
cần dự toán rồi trích snapshot đầy đủ vào thư mục riêng:

```bash
eth-nl2sql snapshot-plan --project P
eth-nl2sql snapshot-run --project P --parquet data/store/full-parquet
eth-nl2sql build-store --parquet data/store/full-parquet --store data/store/full.duckdb --labels data/entities/v1
eth-nl2sql parity --store data/store/full.duckdb
```

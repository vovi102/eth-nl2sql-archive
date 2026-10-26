# Dữ liệu Ethereum nhập từ LuanVan

Ngày nhập: **26/10/2026**. Nguồn: `LuanVan/data/raw/full/`, thư mục cùng cấp với project này.
Các file được sao chép độc lập; dữ liệu nguồn được giữ nguyên. Tổng dung lượng sáu file nguồn:
**1.992.246.050 byte** (khoảng 1,86 GiB).

## Các file

| File | Nội dung | Số dòng theo manifest nguồn |
|---|---|---:|
| `transactions.csv` | Giao dịch đã chọn, có cột `tier` | 4.431.329 |
| `token_transfers.csv` | Token transfer thuộc các giao dịch đã chọn | 4.001.230 |
| `blocks.csv` | Block chứa các giao dịch đã chọn | 221.548 |
| `contracts.csv` | Contract thuộc tập địa chỉ có nhãn | 3.513 |
| `entities.csv` | Nhãn và alias của địa chỉ trong bản xuất cũ | Không ghi (T02 đếm được 4.520) |
| `manifest.json` | Bản sao nguyên vẹn manifest trích xuất nguồn | — |

[import-manifest.json](import-manifest.json) ghi đường dẫn nguồn, dung lượng và SHA-256
của từng file. Toàn bộ sáu bản sao đã có checksum khớp nguồn. Manifest nhập ghi lại trạng thái
tại thời điểm sao chép; kết quả kiểm tra độc lập sau đó được lưu riêng trong báo cáo T02.
Các file CSV lớn được bỏ qua trong `.gitignore`; manifest và tài liệu có thể được lưu trong Git.

## Kiểm tra T02

Ngày 26/10/2026, `eth-nl2sql check-data` đã kiểm lại dung lượng, SHA-256, header và quét
toàn bộ **8.662.140 dòng CSV** bằng DuckDB. Số dòng của bốn bảng có số liệu nguồn đều khớp;
không có dòng trùng toàn bộ hoặc trùng khóa đã kiểm tra. Giao dịch, token transfer và block
có timestamp hợp lệ trong đủ 31 ngày của kỳ. Contract lịch sử được phép có ngày tạo trước kỳ.

Có **701 ô `transactions.to_address` trống**; các cột khác không có NULL/blank. Khóa định danh,
timestamp và địa chỉ không rỗng đều đạt các kiểm tra. Bộ dữ liệu còn thiếu cột/bảng cho store
hiện tại và phạm vi lấy mẫu được giữ nguyên, nên kết quả T02 không chứng minh snapshot đầy đủ.

Chạy lại từ thư mục gốc project:

```bash
uv run --locked eth-nl2sql check-data
```

Lệnh kiểm tra không sửa CSV hoặc manifest. JSON và Markdown mặc định được ghi vào
`reports/data-quality/luanvan.json` và `reports/data-quality/luanvan.md`. Có thể chọn đường dẫn
bằng `--directory`, `--out` và `--report`. Lệnh trả exit code 1 nếu manifest/file không khớp,
CSV không đọc được, số dòng lệch nguồn, khóa thiếu/trùng, địa chỉ sai hoặc timestamp sai kỳ.
Thiếu cột/bảng cho store và phạm vi lấy mẫu là cảnh báo riêng; chúng không bị hiểu là lỗi sao chép.

Xem [báo cáo](../../../reports/data-quality/luanvan.md) và
[chi tiết theo từng cột/ngày](../../../reports/data-quality/luanvan.json).

## Phạm vi

Manifest nguồn ghi thời gian **31/05–30/06/2026**, trích xuất từ BigQuery ngày **02/07/2026**.
Theo mã trích xuất `LuanVan/src/nl2sparql/kg/extraction/full_extract.py`, dữ liệu gồm giao dịch
liên quan đến các địa chỉ trong dictionary và mẫu khoảng 1% các giao dịch còn lại. Block và
token transfer được chọn theo tập giao dịch này; contract được giới hạn theo dictionary.

Bộ này phù hợp để phát triển và chạy thử offline với phạm vi dữ liệu được ghi rõ. Nó chưa
thay thế snapshot đầy đủ hoặc chứng minh parity với kết quả gold BigQuery hiện có.

## Tương thích với store hiện tại

Đối chiếu header CSV với `RAW_SCHEMAS` trong `src/eth_nl2sql/store/build.py`:

| Bảng | Cột hoặc file còn thiếu |
|---|---|
| `transactions` | `transaction_index`, `receipt_gas_used`, `receipt_contract_address`, `block_hash` |
| `blocks` | `base_fee_per_gas` |
| `token_transfers` | `block_number`, `block_hash` |
| `contracts` | `block_number`, `block_hash` |
| `amended_tokens` | Toàn bộ file |

CSV tại đây giữ nguyên bản nhập. T03 đã xử lý các khác biệt trên bằng join đã kiểm tra và
thuộc tính bổ sung từ BigQuery, xuất Parquet ở `data/store/parquet/` rồi dựng
`data/store/eth.duckdb`. Số giao dịch, block và transfer giữ nguyên; contract được bổ sung cho
các token address quan sát được. `entities.csv` được giữ làm dữ liệu nguồn, dictionary dùng
trong store là `data/entities/v1/`. Xem [kết quả và giới hạn T03](../../../reports/local-store/README.md).

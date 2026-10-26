# T02 — Kiểm tra dữ liệu CSV nhập từ LuanVan

Thư mục: `/home/khoavd/WORKSPACE/thesis/eth-nl2sql/data/raw/luanvan`.

- File khớp manifest: **True**.
- Chất lượng dữ liệu đạt các kiểm tra: **True**.
- Đủ schema cho store hiện tại: **False**.
- Snapshot đầy đủ đã được chứng minh: **False**.

Null/blank là ô NULL, rỗng hoặc chỉ có khoảng trắng; không phải mọi ô trống đều là lỗi.
Khóa thiếu hoặc trùng, địa chỉ sai định dạng, số dòng lệch và timestamp sai là lỗi.
Thiếu cột/bảng cho store, ngày vắng trong dữ liệu lấy mẫu là cảnh báo.

## Số dòng và trùng lặp

| Bảng | Dòng thực tế | Dòng theo nguồn | Khóa | Dòng trùng khóa dư | Dòng trùng toàn bộ dư |
|---|---:|---:|---|---:|---:|
| blocks | 221,548 | 221548 | number | 0 | 0 |
| contracts | 3,513 | 3513 | address, block_timestamp | 0 | 0 |
| entities | 4,520 | — | address | 0 | 0 |
| token_transfers | 4,001,230 | 4001230 | transaction_hash, log_index | 0 | 0 |
| transactions | 4,431,329 | 4431329 | hash | 0 | 0 |

## Timestamp (UTC)

| Bảng | Nhỏ nhất | Lớn nhất | Sai/thiếu | Ngoài kỳ | Ngày vắng |
|---|---|---|---:|---:|---|
| blocks | 2026-05-31T00:00:11+00:00 | 2026-06-30T23:59:59+00:00 | 0 | 0 | — |
| contracts | 2016-06-24T21:38:09+00:00 | 2026-06-25T12:21:11+00:00 | 0 | 0 | — |
| token_transfers | 2026-05-31T00:00:11+00:00 | 2026-06-30T23:59:59+00:00 | 0 | 0 | — |
| transactions | 2026-05-31T00:00:11+00:00 | 2026-06-30T23:59:59+00:00 | 0 | 0 | — |

Contract cũ được phép nằm trước kỳ; mọi timestamp phải trước ngày kết thúc + 1 (UTC).
Khoảng ngày trong manifest được hiểu là bao gồm cả ngày đầu và ngày cuối.
Số dòng theo từng ngày được ghi trong báo cáo JSON.

## Null/blank

| Bảng | Cột | Số ô |
|---|---|---:|
| blocks | Không có | 0 |
| contracts | Không có | 0 |
| entities | Không có | 0 |
| token_transfers | Không có | 0 |
| transactions | to_address | 701 |

## Vấn đề và giới hạn

- **warning / missing_store_columns** (blocks.csv): base_fee_per_gas
- **warning / missing_store_columns** (contracts.csv): block_hash, block_number
- **warning / missing_store_columns** (token_transfers.csv): block_hash, block_number
- **warning / missing_store_columns** (transactions.csv): block_hash, receipt_contract_address, receipt_gas_used, transaction_index
- **warning / missing_store_tables**: amended_tokens
- **warning / full_snapshot_not_verified**: The imported data is a declared subset; date coverage does not prove full-chain coverage.

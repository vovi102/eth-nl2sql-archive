# T06 — Dry-run BigQuery

Thời điểm UTC: 2026-10-27T13:48:46.441288+00:00. Project: `nl2sparql-thesis`; location `US`.

| Bảng | Query | Scan ước lượng (GiB) |
|---|---:|---:|
| amended_tokens | 1 | 0.175 |
| blocks | 31 | 112.351 |
| contracts | 1 | 33.035 |
| token_transfers | 31 | 46.000 |
| transactions | 31 | 22.878 |

Tổng scan: **230,252,981,386 bytes (214.44 GiB)**.
Ước lượng sau làm tròn billing: 230,310,281,216 bytes (214.493 GiB).
Query lớn nhất: 33.04 GiB. Trần mỗi query: 50 GiB.

Dry-run không gửi query tính phí. Trần 1 TiB dùng ở bước dự toán là giới hạn tháng của sandbox,
không phải xác nhận allowance còn lại. Kiểm tháng hiện tại cho allowance bảo thủ là 0;
lệnh thực thi đã dừng trước khi gửi query trích dữ liệu. Xem [trạng thái sandbox](sandbox-status.json).

[JSON đầy đủ SQL, hash và bytes từng partition](dry-run.json).

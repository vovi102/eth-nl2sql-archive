# T05 — Kiểm dataset trên DuckDB

Kết quả: **PASS**. Thời điểm UTC: 2026-10-26T15:28:22.386191+00:00.

Scope: `labeled_address_transactions_plus_approximately_one_percent_of_other_transactions`; complete_snapshot: `False`.

| Split | Câu | SQL phân biệt | Lỗi | Rỗng | Aggregate 0/NULL |
|---|---:|---:|---:|---:|---:|
| train | 4872 | 1218 | 0 | 428 | 92 |
| dev | 516 | 129 | 0 | 72 | 0 |
| test | 100 | 100 | 0 | 2 | 0 |

Test: {'generic': 50, 'entity': 50}. Nhãn có thể chồng lấn: {'multi_address': 34, 'ambiguous_property': 23, 'alias': 18, 'class_level': 6}.
Multi-address: 34 owner; mỗi ca được kiểm trực tiếp trên raw fact theo đúng chiều và cửa sổ.

## Leakage

No exact question/SQL/family overlaps; no 12-token overlaps with test. Train/dev share template boilerplate, reported separately.

| Cặp split | Trùng câu | Trùng SQL | Trùng family | Câu chung 12-gram |
|---|---:|---:|---:|---:|
| train/dev | 0 | 0 | 0 | 3078 |
| train/test | 0 | 0 | 0 | 0 |
| dev/test | 0 | 0 | 0 | 0 |

Train/dev dùng chung template nên có đoạn văn mẫu trùng; đây là cảnh báo được giữ trong báo cáo, không phải kiểm tra 12-gram đã sạch.

## Kết quả rỗng của test

- `t05-e044`: No direct outer transaction from an exchange-labeled sender to a DEX-labeled recipient is observed in this local sample. Both classes are individually active; this does not imply absence of exchange/DEX activity or token-transfer paths.
- `t05-e050`: No token-transfer endpoints labeled Tornado Cash occur in the local sample; observed service activity is router transactions only.

Kết quả đếm 0 vẫn trả một dòng; danh sách zero_aggregate_ids ghi riêng trong JSON.

## Review ngữ nghĩa

Reviewer: Codex (agent semantic review). Human review: pending; no human sign-off claimed.
Mỗi câu test có ghi chú và hash câu hỏi/SQL trong `data/test-review.json`. Đổi câu hoặc SQL làm review hết hiệu lực.

Đây là kiểm tra trên dữ liệu local lấy mẫu, chưa phải parity với BigQuery.

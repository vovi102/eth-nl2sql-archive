# Kiểm chứng hiện hành

Ngày kiểm: **30/10/2026**, Asia/Saigon. Kiểm tra local sau khi dọn `reports/` và
`runs/`, cập nhật đường dẫn và bỏ phụ thuộc vào ZIP/báo cáo lịch sử.

| Kiểm tra | Kết quả |
|---|---|
| `uv run --locked pytest -q` | 360 passed, 146,27 giây |
| Ba case regression bổ sung | 3 passed: giữ manifest không chép ZIP; tách chẩn đoán khỏi seed aggregate; từ chối evaluation sai hash |
| `uv run --locked ruff check src tests scripts` | All checks passed |
| `uv run --locked eth-nl2sql check-sql` | 1.547 SQL, không lỗi |
| `uv run --locked eth-nl2sql report` | Tạo RESULTS thành công, chẩn đoán prompt có mục riêng |
| `git diff --check` | Không lỗi whitespace |
| Liên kết Markdown local | Đều trỏ tới file hiện có |

Các case mới chạy riêng sau suite đầy đủ; không diễn giải bảng trên thành một
lần chạy đầy đủ 363 case. Kiểm SQL trên schema rỗng không thay kiểm gold trên dữ liệu.

## Toàn vẹn và giữ artifact

Đối chiếu SHA-256 trước/sau xác nhận **130 artifact dữ liệu được giữ nguyên**,
kể cả prediction, evaluation, prompt/SFT và metadata train. File benchmark v2
không đổi. Manifest của raw diagnostic output và evaluation đều khớp. Adapter
cuối `b3/42` khớp digest đã ghi:

`4881dd2caa1014ea214e3a68c33cf4224a40b87dd1182c7d0658f58b54f1aed7`.

Toàn bộ 40 output gốc được kiểm trước khi xóa ZIP/checkpoint. Manifest hiện tại
chỉ liệt kê 17 file gốc còn giữ; không tuyên bố checkpoint đã xóa vẫn tồn tại.
`reports/` và `runs/` còn khoảng **103,43 MiB**, giảm **658,27 MiB**; không còn
ZIP, log, JUnit, notebook sinh tự động hoặc checkpoint optimizer cũ.

Giới hạn provenance có sẵn: hash source training trong manifest `b3/42` khác
HEAD trước khi dọn. Adapter vẫn nguyên vẹn; không sửa manifest để vượt kiểm
resume. Chi tiết ở [hướng dẫn thực nghiệm](reports/experiments/WORKFLOW.md).

## Phạm vi

Kiểm tra này không chạy GPU hoặc query BigQuery mới. Các số đo thực nghiệm
được giữ nguyên từ lần chạy gốc. Snapshot đầy đủ, parity và human review vẫn
chưa hoàn tất; xem [báo cáo hiện hành](reports/README.md).

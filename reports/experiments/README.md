# Thực nghiệm phát triển hiện hành

Kết quả dùng DuckDB sample và `dev_eval`; test v2 vẫn draft và không được dùng.
**Chưa mở rộng `b3l/42` hoặc các seed còn lại**; quyết định hiện tại là
[hold_for_further_development](diagnosis/scaling-decision.json).

| Điều kiện | N | Compile | EX | Bằng chứng |
|---|---:|---:|---:|---|
| `b3-base`, compact prompt gốc | 100 | 0 | 0 | [Evaluation](../../runs/b3-base/seed-42/eval-dev_eval.json) |
| `b3l-base`, compact prompt + linking gốc | 100 | 0 | 0 | [Evaluation](../../runs/b3l-base/seed-42/eval-dev_eval.json) |
| B1 catalog đầy đủ, pilot | 10 | 0 | 0 | [Evaluation](pilot/eval.json) |
| `b3/42`, adapter và prompt gốc | 10 | 7 | 0 | [Evaluation](b3-seed-42/eval.json) |
| Adapter đóng băng, thêm quy tắc ngày và cột | 100 | 85 | 19 | [Evaluation](diagnosis/evaluation/dates-columns.json) |
| Base nhận cùng prompt bổ sung | 100 | 0 | 0 | [Evaluation](diagnosis/evaluation/base-dates-columns.json) |

`b3/42` train hoàn tất **608 step**, chọn theo minimum dev loss **0,0000535721**.
[Review](b3-seed-42/review.json) và
[training summary](../../runs/b3/seed-42/training-summary.json) giữ loss/tài nguyên.
Adapter cuối ở `runs/b3/seed-42/adapter/` local; optimizer checkpoint đã xóa sau
khi kiểm toàn vẹn. Manifest, prediction và số đo gốc giữ nguyên nội dung.

Can thiệp ngày/cột là chẩn đoán lúc suy luận trên adapter đóng băng, không phải
lượt QLoRA mới hoặc bản thay thế prompt chính. EX 19% có CI bootstrap 95%
[12%, 27%]; generic 3/50, entity 16/50. Còn 14 lỗi compile, một lỗi validator và
66 câu compile được nhưng sai kết quả. [Báo cáo chẩn đoán](diagnosis/README.md)
giữ so sánh 2×2, kiểm loss và giới hạn ORDER BY hòa trước LIMIT.

Hai base control gốc đã chạy 10 → 100 câu, kiểm resume giữ prediction từng byte.
[Tổng hợp](base-controls/summary.json), [b3-base resume](base-controls/b3-base-resume.json)
và [b3l-base resume](base-controls/b3l-base-resume.json) giữ bằng chứng hạ tầng;
EX=0 vẫn là đối chứng có giá trị. Không dùng chúng thay đối chứng cùng prompt
của nhánh chẩn đoán.

Nguồn gốc đầu vào ở `inputs-manifest.json` của từng job ghi source/hash tại lần
chạy gốc. [Manifest output được giữ](b3-seed-42/outputs-manifest.json) kiểm những
file gốc còn sử dụng, thay phụ thuộc ZIP. Xác nhận toàn vẹn có ngày cũ mô tả
phép kiểm đã thực hiện trước khi bỏ checkpoint/log, không xác nhận chúng còn tồn tại.

Xem [quy trình chạy](WORKFLOW.md), [bảng kết quả](../../RESULTS.md) và
[quy tắc giữ artifact](../README.md). Không giữ ZIP, attempts, log và notebook
sinh tự động trong báo cáo hiện hành.

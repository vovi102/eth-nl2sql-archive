# T11B — giao thức chẩn đoán phát triển

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-29 (Asia/Saigon)
- Verification Status: VERIFIED (v2 đã hoàn tất, thu nhận và chấm đủ 100 câu)
- Version Label: t11b_diagnosis_protocol_v2

Adapter b3/42 và prediction gốc được giữ nguyên. Đây là can thiệp prompt lúc suy
luận trên adapter đã train; chưa phải lượt QLoRA mới. Bốn prompt và tám cặp dev
được lập trước khi submit; v1/v2 có cùng hash hai file đầu vào này. V2 đổi cách
chuẩn bị runtime: đọc trực tiếp adapter và kiểm hash cache model bằng hàm T11B đã
dùng, kèm log giai đoạn. Chưa xác định nguyên nhân v1 kẹt nạp checkpoint.

| Giả thuyết | Phép kiểm đã định trước |
|---|---|
| Khác cách viết ngày làm model sai khoảng | Tám câu dev ISO và tám bản viết ngày bằng chữ, cùng target; so loss và greedy output |
| Compact prompt thiếu cột dẫn đến đoán cột | Thêm riêng danh sách cột từ catalog; đo compile trên cùng 10 câu |
| Sai masking/dịch nhãn làm loss thấp giả | Tokenizer thật, collator thật, model loss so với CE dịch một token chỉ trên SQL+EOT; kiểm mask padding và target đầy đủ |
| Dev tổng hợp chưa phản ánh tổng quát hóa | Đối chiếu template, ngày và pattern SQL; so loss với sinh tự do, không suy từ loss sang EX |

Thiết kế prompt 2×2: `original`, `dates`, `columns`, `dates-columns`. Quy tắc ngày
dùng ví dụ chung ba ngày đầu tháng, không đưa gold dev_eval vào prompt. Danh sách
cột lấy từ catalog. Nhánh `b3-base/dates-columns` nhận byte-identical messages với
nhánh adapter; chỉ tắt adapter trên cùng model nền NF4. Không sửa SQL sau sinh.

Nhánh kết hợp phải qua smoke 10/10 bằng validator/compiler production trên schema
rỗng rồi mới sinh tiếp đủ 100 câu dev_eval. Sau đó chấm local và đối chiếu với
`b3-base` cùng prompt. Nếu smoke thất bại, giữ output 10 câu để chẩn đoán tiếp;
không nới gate hoặc biến 10 câu thành kết quả 100 câu.

EX dùng DuckDB sample. Với cặp dev, đọc cả `exact_match` và literal ngày vì kết quả
thực thi có thể trùng tình cờ trên truy vấn rỗng. Số đếm 10 câu chỉ là chẩn đoán,
không phải suy luận thống kê cho test. Chưa mở rộng b3l/42 hoặc các seed khác.

Test v2 chỉ được kiểm checksum ở ledger local, không đọc nội dung và không nằm
trong bundle GPU. Prompt dev_eval chỉ có ID/messages/hash; gold nằm ở máy local
để chấm sau khi thu nhận output. Tám cặp dev có target riêng phục vụ kiểm loss;
backend sinh tự do chỉ nhận messages.

Nguồn đầu vào và thiết kế trước khi chạy nằm trong [plan.json](plan.json),
[prompt](prompts.jsonl) và [dev probes](dev-probes.jsonl). Checksum raw output
ở [manifest](output/manifest.json). ZIP truyền dữ liệu và attempt bị dừng đã xóa;
không có loss hoặc prediction chẩn đoán từ attempt bị dừng được dùng làm kết quả.

V2 đã qua smoke 10/10 và sinh đủ 100 câu cho adapter cùng đối chứng. Kết quả là
85/100 compile, EX 19/100 cho adapter; đối chứng 0/100 ở cả hai số đo. Kiểm loss
GPU khớp CE thủ công; replay prompt gốc giữ nguyên SQL. Review chất lượng quyết
định **hold_for_further_development**, chưa chạy b3l/42 hoặc seed khác.
Xem [báo cáo kết quả và giới hạn](README.md), [quyết định](scaling-decision.json).

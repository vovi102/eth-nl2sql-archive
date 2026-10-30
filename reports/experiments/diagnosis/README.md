# T11B — chẩn đoán trên adapter đóng băng

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-29 (Asia/Saigon)
- Verification Status: VERIFIED (hash và chấm local; không phải kết quả test)
- Version Label: t11b_diagnosis_v1

**Quyết định sau khi chấm đủ 100 câu: giữ chưa chạy `b3l/42` và các seed còn lại.**
Can thiệp prompt qua smoke nhưng EX mới đạt 19/100; generic chỉ đúng 3/50.
Xem [quyết định mở rộng](scaling-decision.json).

Giữ nguyên adapter và dự đoán T11B. Các can thiệp chỉ đổi prompt lúc suy luận; không có lượt QLoRA mới. Mỗi nhánh dùng cùng 10 câu đầu dev_eval, seed greedy 42, model/revision và runtime đã khóa. Thiết kế 2×2 được ghi trước khi submit.

| Prompt, cùng 10 câu | Compile | EX | Literal ngày khớp gold |
|---|---:|---:|---:|
| original | 7/10 | 0/10 | 0/10 |
| dates | 7/10 | 4/10 | 7/10 |
| columns | 10/10 | 0/10 | 0/10 |
| dates-columns | 10/10 | 3/10 | 4/10 |
| base-dates-columns | 0/10 | 0/10 | 0/10 |

| Cặp dev (8 ý định, chỉ đổi cách viết ngày) | EX | Loss teacher forcing trung bình |
|---|---:|---:|
| dev-iso | 8/8 | 3.2283607e-05 |
| dev-natural-date | 7/8 | 8.5698708e-05 |

Hai cách diễn đạt đều có **SQL khớp chính xác gold 8/8**, gồm cả literal ngày.
EX thô 7/8 của nhánh natural có một ca bất định: `syn-v2-000051__en__formal`
sắp xếp theo timestamp rồi `LIMIT 2`, trong khi năm giao dịch hòa timestamp cao
nhất. SQL gold và prediction giống từng byte; chạy lại nguyên SQL 24 lần cho 10
kết quả có thứ tự khác nhau. Giữ nguyên điểm EX đã chấm và ghi
[bằng chứng riêng](probe-tie-audit.json); không quy ca này thành lỗi diễn đạt ngày.
Trong hai nhánh đủ 100 câu không có ca exact match nhưng EX sai; điều đó không
chứng minh mọi truy vấn đều có thứ tự ổn định.

Model loss = 2.00428967e-05; cross-entropy dịch một token, chỉ SQL+EOT = 2.00428967e-05; sai khác tuyệt đối 0. Target đầy đủ: True; padding được mask: True. Runtime thực tế: Transformers 4.49.0, torch 2.5.1+cu124.

Replay prompt gốc sinh SQL giống từng byte: True.

Nhánh kết hợp qua smoke 10/10 trước khi sinh tiếp. Kết quả đủ 100 câu:

| Nhánh | Compile | EX |
|---|---:|---:|
| dates-columns | 85/100 | 19/100 |
| base-dates-columns | 0/100 | 0/100 |

Gate kỹ thuật trả **ready_for_review_before_scaling**: đủ output, loss hữu hạn,
có tài nguyên GPU và EX lớn hơn 0. Sau khi xem chất lượng, quyết định là
**hold_for_further_development**. Gate kỹ thuật không tự khởi chạy seed.

Trong 100 câu của nhánh kết hợp, 14 câu lỗi compile, một câu bị validator từ chối
vì comment; 66 câu compile được nhưng trả kết quả sai. Generic đạt 3/50, entity
đạt 16/50. EX 19% có khoảng bootstrap 95% [12%, 27%] trên sample này.
Literal ngày khớp gold 53/100 là phép so sánh chuỗi literal, không đủ để kết luận
47 câu còn lại đều sai ngữ nghĩa ngày. Xem [từng câu](evaluation/dates-columns-cases.jsonl).

Đối chứng chỉ thêm cột sửa được cả ba lỗi bind ở mười câu gốc (7→10 compile),
nhưng không sửa ngày và EX vẫn 0/10. Chỉ thêm quy tắc ngày nâng số câu khớp literal
ngày từ 0 lên 7/10 và EX từ 0 lên 4/10; ba lỗi cột vẫn còn. Khi kết hợp, compile
đạt 10/10 nhưng literal ngày chỉ còn 4/10 và EX 3/10. Hai bổ sung tương tác với
nhau; chưa thể coi prompt kết hợp là bản sửa ổn định hoặc đưa vào cấu hình chính.

Audit dữ liệu xác nhận mọi câu train/dev có ngày đều dùng ISO, còn 50/100 câu
dev_eval dùng cách viết khác. Tuy nhiên, tám cặp dev ở trên đều sinh đúng gold,
nên chưa có bằng chứng rằng mọi ngày viết bằng chữ đều gây lỗi. Bằng chứng trực
tiếp hiện tập trung vào cách hiểu ngày cuối có tính bao gồm ở dev_eval và việc
thiếu tên cột trong compact prompt. Masking/loss không có lỗi trong các phép kiểm
đã chạy; không thay hàm loss. Chi tiết ở [LOSS.md](LOSS.md).

Bước phát triển kế tiếp cần kiểm riêng cách diễn đạt khoảng ngày và khả năng
gắn cột với đúng relation trên train/dev, rồi thử nhỏ trước khi mở rộng. Nếu đổi
prompt huấn luyện, dựng cùng prompt cho inference và đối chứng `b3-base`, giữ
thí nghiệm adapter đóng băng này thành kết quả chẩn đoán riêng. Chưa submit lượt
huấn luyện mới.

Mọi EX ở đây dùng DuckDB sample phát triển. Mười câu đầu và tám cặp dev là phép chẩn đoán nhỏ, không chứng minh tổng quát hóa cho test. Test v2 không được dùng. Khác biệt literal ngày chỉ là số đo chẩn đoán, không thay EX.

ResourceMonitor đo từ sau bước kiểm cache, gồm load model, kiểm loss và sinh:
2543,530 giây; 2×Tesla T4; peak allocated riêng GPU0/GPU1 là 2,587 / 4,335 GiB,
max reserved trên một GPU 4,621 GiB. Đồng hồ bao gồm chuẩn bị adapter và kiểm
cache là 2640,665 giây, không gồm bootstrap cài dependency của notebook.
Không phân bổ các số đo chung này thành runtime riêng cho từng nhánh.

Raw output hiện giữ đủ 19 file và [manifest checksum](output/manifest.json).
Phép kiểm toàn vẹn ngày 29/10/2026 đã xác nhận adapter, 40 output gốc và checksum
test v2 nguyên vẹn; [integrity](final-integrity.json) mô tả thời điểm đó. Sau khi
dọn, checkpoint/log/ZIP đã xóa; [manifest hiện giữ](../b3-seed-42/outputs-manifest.json)
chỉ liệt kê file còn dùng. Adapter, prediction, prompt và các số đo không đổi.

Xem [review đầy đủ](review.json), [kế hoạch trước khi chạy](plan.json),
[checksum evaluation](evaluation/manifest.json), [bằng chứng gốc](evidence.json)
và [giao thức](PROTOCOL.md).

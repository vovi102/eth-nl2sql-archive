# T11B — kiểm masking và cách tính loss

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-29 (Asia/Saigon)
- Verification Status: VERIFIED (audit toàn bộ span local và đối chiếu loss trên GPU)
- Version Label: t11b_loss_v1

Encoder thực tế nối prompt đã áp chat template với SQL và EOT; labels của prompt
là -100, labels của SQL/EOT là token đích. Collator đặt attention của padding bằng
0 và label bằng -100. Dòng quá dài bị loại cả dòng, không cắt SQL.

[Audit toàn bộ 5.388 dòng SFT gốc](masking-all-rows.json) xác nhận không có span
nhãn sai hoặc target bị cắt. Tổng token được giám sát là 490.812 ở train và 47.772
ở dev; các token prompt tương ứng 1.357.819 và 143.601 đều được mask. Bản local dùng
Transformers 4.57.6/tokenizers 0.22.2; không coi đây là phép đo loss của runtime GPU.

Đối chiếu [causal loss của Transformers 4.49.0](https://github.com/huggingface/transformers/blob/v4.49.0/src/transformers/loss/loss_utils.py#L21):
logits được chuyển sang float32, nhãn dịch một vị trí, -100 bị bỏ qua. Khi không
có `num_items_in_batch`, cross-entropy lấy trung bình trên token còn được giám sát;
khi có, tổng loss được chia cho số token truyền vào.

[Trainer 4.49.0](https://github.com/huggingface/transformers/blob/v4.49.0/src/transformers/trainer.py#L4122)
gọi `compute_loss(..., return_outputs=True)` trong bước eval, không truyền số token
của gradient accumulation. Backend của repo dùng Trainer mặc định, không có loss
tùy biến hoặc label smoothing. Vì vậy không có căn cứ từ code để chia dev loss cho
toàn bộ prompt/padding hoặc đổ lỗi cho gradient accumulation ở bước eval.

Phép kiểm GPU trên adapter thật dùng hai dòng có độ dài khác nhau, so model loss
với cross-entropy trực tiếp của logits ở t-1 và labels ở t, bỏ qua -100. Nó còn
kiểm target đầy đủ và mask padding. Giá trị và phiên bản thực thi được xuất tại
[output/loss-audit.json](output/loss-audit.json). Trên runtime thật Transformers
4.49.0 / torch 2.5.1+cu124, model loss và CE thủ công đều bằng
0,000020042896721861325; sai khác bằng 0, trên 88 token SQL+EOT được giám sát.
Target đầy đủ và toàn bộ label padding bằng -100. Không có bằng chứng loss thấp
do chia cho prompt hoặc padding trong phép kiểm này.

Tám cặp dev có loss teacher forcing trung bình 0,0000322836 (ISO) và 0,0000856987
(ngày bằng chữ); cả hai nhánh sinh SQL khớp chính xác gold 8/8. EX thô lần lượt
8/8 và 7/8 có một ca ORDER BY hòa timestamp trước LIMIT: gold và prediction giống
từng byte nhưng kết quả thực thi không ổn định. Xem [audit ca hòa](probe-tie-audit.json).
Không dùng chênh lệch EX này để kết luận model kém hơn với ngày bằng chữ.

Train/dev tổng hợp dùng chung 33 template dev với train, và mọi câu có ngày đều
viết ISO. Loss thấp là bằng chứng dự đoán token tốt trong phân bố đã đo; chưa đại
diện khả năng giải khoảng ngày có ngày cuối bao gồm hoặc câu hỏi dev_eval mới.
Không suy từ loss thấp sang EX cao.

Chưa thay loss/masking của pipeline. Mọi can thiệp chất lượng hiện chỉ đổi prompt
trong thử nghiệm có đối chứng, giữ adapter gốc và test v2 nguyên vẹn.

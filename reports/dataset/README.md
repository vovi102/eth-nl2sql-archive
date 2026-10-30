# Dataset và annotation hiện hành

Dataset có **4.872 train / 516 dev / 100 dev_eval**, tương ứng **1.218 / 129 / 100
SQL phân biệt**. `dev_eval` gồm 50 câu chung và 50 câu thực thể, đã được xem trong
quá trình thiết kế. Test cuối có [hồ sơ riêng](../benchmark/README.md).

[Kiểm dataset](validation.md) và [JSON từng query](validation.json) ghi nhận
1.447 SQL phân biệt thực thi không lỗi trên DuckDB sample. Không trùng ID, câu
chuẩn hóa, SQL canonical hoặc family giữa các split. Train/dev dùng chung
template; không tuyên bố template/owner holdout.

[Kiểm annotation](annotations.json) xác nhận đủ 100 annotation phát triển hợp lệ
về cấu trúc, mention, schema, owner/address, class/membership và ba property.
[Review câu hỏi–SQL](../../data/dev_eval-review.json) và các hồ sơ review annotation
trong `data/` chưa có human sign-off. Đổi nội dung làm review gắn hash hết hiệu lực.

Hai ca `t05-e044` và `t05-e050` trả rỗng có lý do trong báo cáo; không suy từ sample
ra sự vắng mặt toàn mạng. Store có `complete_snapshot=false`; gold-echo 100% chỉ
kiểm đường ống.

```bash
uv run --locked eth-nl2sql check-sql
uv run --locked eth-nl2sql check-annotations
uv run --locked eth-nl2sql check-dataset
```

CLI mặc định ghi vào thư mục này. `--require-human` tiếp tục bị chặn khi review
pending; agent không xác nhận thay người review.

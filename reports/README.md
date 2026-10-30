# Báo cáo hiện hành

Chỉ giữ kết quả còn sử dụng, bằng chứng cho kết luận hiện tại và hồ sơ phục vụ
công việc đang chờ. Tổ chức theo nội dung, không theo mốc Txx.

| Chủ đề | Báo cáo |
|---|---|
| CSV nguồn | [Chất lượng dữ liệu](data-quality/luanvan.md) |
| Store và snapshot còn chờ | [Store local](local-store/README.md) |
| Dictionary đang dùng | [Dictionary v2](dictionary-v2/README.md) |
| Train/dev/dev_eval và annotation | [Dataset](dataset/README.md) |
| Test v2 draft và human review | [Benchmark](benchmark/README.md) |
| Linking, baseline và ablation | [Linking phát triển](linking/README.md) |
| Đối chứng, QLoRA và chẩn đoán | [Thực nghiệm](experiments/README.md) |

`runs/<config>/seed-<seed>/` giữ prediction, case, evaluation, manifest và metadata
huấn luyện. Giữ prompt/SFT còn ràng buộc với run hoặc đối chứng. Adapter cuối
`b3/42` còn phục vụ phát triển được giữ local.

Không giữ archive, ZIP, attempts thất bại, notebook sinh tự động, log hay JUnit
trong tập báo cáo được duy trì. ZIP chỉ dùng tạm để truyền GPU; sau khi kiểm hash,
giữ file đã giải nén và manifest. Xóa checkpoint optimizer sau khi train hoàn tất
và adapter cuối đã được kiểm toàn vẹn; giữ checkpoint của lượt còn cần resume.

Chỉ thay báo cáo hiện hành sau khi kết quả mới được kiểm tra. Các đối chứng và
nhánh chẩn đoán còn cần được giữ riêng theo điều kiện thí nghiệm; không sửa
prediction hoặc số đo gốc. Hash và đường dẫn trong provenance mô tả lần chạy gốc,
không phải bản sao source hiện tại. Không giữ hai báo cáo chỉ lặp lại cùng nội dung.

Mọi kết quả hiện có dùng dữ liệu phát triển/sample. Snapshot đầy đủ, parity
BigQuery và human review test v2 vẫn chưa hoàn tất.

# Benchmark v2 và annotation — T07 / T09A

`train` và `dev` giữ nguyên. Bộ 100 câu đã xem trong phát triển chuyển nguyên byte từ
`data/test.jsonl` sang `data/dev_eval.jsonl`; review câu hỏi–SQL cũ chuyển sang
`data/dev_eval-review.json`. Artifact gold-echo chuyển sang hậu tố `dev_eval` và được chạy lại
trên đủ 100 câu. CLI và notebook mặc định dùng `dev_eval`; retrieval chỉ đọc `train`.

`test` trỏ riêng tới `data/benchmark/v2/test.jsonl`. T09A đã soạn 100 câu/100 SQL phân biệt,
100 annotation và 100 review pending; manifest vẫn `draft`. Gold và annotation được khai báo
trực tiếp trong [nguồn soạn](v2/authoring.py), độc lập với prediction T08/renderer train.
Script này chỉ đóng gói các bản ghi soạn sẵn, mở rộng tập địa chỉ/lớp từ dictionary và tính hash;
không gọi model/linker hoặc đọc câu hỏi/SQL train/dev/dev_eval; manifest chỉ pin hash các split.
Schema target được khai báo riêng rồi
validator đối chiếu với SQL, không lấy SQL/prediction để bootstrap nhãn semantic.

[Báo cáo T09A](../../reports/benchmark/README.md) ghi phạm vi sample, hash/leakage và các
ca còn chờ. [Hồ sơ human review](../../reports/benchmark/human-review.md) chứa từng cặp
câu hỏi–SQL–annotation, preview sample, lý do tác giả, đối chứng và hash cần người xác nhận.
T09B chờ T06 để chạy lại trên snapshot đầy đủ, kiểm witness/ca rỗng và hoàn tất human review
trước khi đóng băng. Không chạy generator hoặc chỉnh linker từ test v2.

## Định dạng

Nguồn quy định là [JSON Schema](../../configs/benchmark.schema.json) và kiểm tra ngữ nghĩa
trong `src/eth_nl2sql/data/annotations.py`. Mỗi dòng JSONL là một object; mỗi ID có đúng một
case, annotation và review, không thiếu, trùng hoặc dư.

| Artifact | Nội dung |
|---|---|
| `test.jsonl` | ID, question, SQL, family, primary_group, specifics, subset, difficulty, categories, provenance, property_focus, window, empty_reason |
| `annotations.jsonl` | schema_version=2, ID, hash question/SQL, schema targets, entities, classes, properties |
| `reviews.jsonl` | ID, hash case/question/SQL/annotation, status, reviewer, reviewer_kind, reviewed_at, note |
| `manifest.json` | phiên bản, trạng thái, quota, hash ba file và phụ thuộc; profile store và thời điểm khi frozen |
| `authoring.py`, `author-notes.jsonl` | bản ghi soạn sẵn, annotation khai báo độc lập và lý do ngữ nghĩa của tác giả |
| `property-contrasts.jsonl` | 20 truy vấn cố ý sai để kiểm khả năng phân biệt ba property; không phải prediction |

Case có `primary_group` là một trong `generic`, `multi_address`, `alias`, `class_level`,
`ambiguous_property`, mỗi nhóm 20 câu. `specifics` ghi mọi hiện tượng áp dụng, kể cả nhãn
chính khi không phải generic. `property_focus` chỉ dùng cho nhóm chính property, với
`direction`=7, `fact`=7, `address_role`=6. `provenance` ghi `author`, `author_type`
(`human`/`agent`), `method=independent_authoring`. Không dùng renderer train để soạn test.
`window` ghi `start_date`, `end_date` theo UTC half-open trong cửa sổ catalog.

Annotation dùng các trường sau:

- `schema.relations`: tên ngắn của relation trong catalog. `schema.columns`: các cặp
  `{relation, column}` tham chiếu trong gold SQL. Resolver SQLGlot phân giải alias, CTE và
  table-valued function để kiểm tập cột. `COUNT(*)` không tạo target cột `*`.
- `entities`: mỗi mention có `{text,start,end}` với offset ký tự Unicode kiểu Python,
  `owner`, `addresses` viết thường và `address_scope`. `known_owner_addresses` yêu cầu tập
  đầy đủ theo dictionary, không chỉ địa chỉ có hoạt động. `explicit_address` yêu cầu đúng
  một địa chỉ literal trong câu hỏi; owner có thể null nếu chưa gán nhãn.
- `classes`: mention, `category`, `concept_class`, và tập `owners` đầy đủ theo dictionary.
  Phạm vi là các owner đã có nhãn; không tuyên bố bao phủ mọi DEX/owner trên Ethereum.
  Test v2 loại cách diễn đạt “major” chưa có tiêu chí.
- `properties.direction`: danh sách `{target,value}` với target `entity:0`, `class:0`, ...;
  value `from`, `to` hoặc `either`. Cặp sender/recipient có hai target riêng.
- `properties.fact`: `transaction`, `token_transfer`, `transaction_token_transfer_join`,
  hoặc null khi không áp dụng. Transaction là outer transaction; token transfer là log event.
- `properties.address_role`: danh sách `{target,value}` với value `token_contract` hoặc
  `endpoint`. Token contract chỉ danh tính token tại `token_address`; endpoint chỉ địa chỉ
  tham gia gửi/nhận. Địa chỉ contract cũng có thể đóng vai endpoint tùy câu hỏi.

Thuộc tính không áp dụng dùng danh sách rỗng hoặc fact null. Không dùng `unspecified` làm gold
cho câu hỏi thiếu thông tin; cần làm rõ câu trước khi đưa vào benchmark SQL chính.

Các file `data/dev_eval-annotations.jsonl` và `data/dev_eval-annotation-reviews.jsonl` dùng
cùng định dạng annotation/review. Chúng được bootstrap tất định từ SQL và expectation cũ
bằng `draft_development_annotations`; toàn bộ review là `pending`. Đây là nhãn nháp phục vụ
kiểm hạ tầng, cần đối chiếu ngữ nghĩa độc lập trước khi dùng làm gold linking cuối.

## Review, hash và kiểm tra

Hash question/SQL là SHA-256 của chuỗi UTF-8 nguyên văn. Hash toàn case (`case_sha256`) và annotation dùng JSON UTF-8
`sort_keys=True, ensure_ascii=False, separators=(',', ':')`; thứ tự key/whitespace không
làm mất review, nhưng thay nội dung, kể cả tập target, nhãn nhóm hay provenance của case,
làm review hết hiệu lực.

Status gồm `pending`, `agent_reviewed`, `human_reviewed`, `rejected`. Review đã thực hiện
cần tên reviewer, `reviewer_kind`, timestamp ISO 8601 có timezone và note. Human reviewer
phải khác tác giả. Agent review không đáp ứng gate human review. `--require-human` trả mã 1
khi còn thiếu; kiểm cấu trúc bình thường vẫn báo riêng `human_review_complete=false`.

```bash
uv run --locked eth-nl2sql check-annotations
uv run --locked eth-nl2sql check-annotations --require-human
uv run --locked eth-nl2sql check-benchmark --skip-execution
uv run --locked eth-nl2sql check-benchmark
uv run --locked eth-nl2sql check-benchmark --require-release
```

`passed` là kết quả kiểm artifact hiện có; draft rỗng có thể PASS cấu trúc/hash.
`release_ready` yêu cầu thêm 100 câu/100 SQL phân biệt, quota, đủ review human và full snapshot.
Các báo cáo luôn ghi riêng hai trạng thái. Gold rỗng hoặc aggregate 0/NULL cần giải thích.
Multi-address cần raw-table witness với ít nhất hai địa chỉ hoạt động và union khác mọi
địa chỉ riêng theo fact/direction/window.

T09A kiểm trên `data/store/t09-sample-v2.duckdb`, dựng riêng từ Parquet sample và dictionary v2;
không ghi đè store kế thừa. Chạy báo cáo chi tiết và tạo lại hồ sơ review bằng:

```bash
uv run --locked eth-nl2sql build-store --parquet data/store/parquet \
  --labels data/entities/v2 --store data/store/t09-sample-v2.duckdb
uv run --locked python scripts/audit_t09a.py
```

Script audit chỉ đọc benchmark/store và ghi báo cáo; không sửa gold, review hoặc trạng thái.
Nó chặn dùng full snapshot trong giai đoạn T09A. Script đóng gói `authoring.py` chỉ dùng khi
chỉnh bản draft; từ chối chạy nếu benchmark frozen hoặc đã bắt đầu review. Các hash bổ sung
của nguồn soạn, ghi chú và đối chứng nằm trong `sample.json`; manifest chuẩn giữ hợp đồng T07.

Leakage kiểm mọi cặp train/dev/dev_eval/test: ID, câu chuẩn hóa, SQL canonical và family.
Kiểm 12-token n-gram giữa train/dev và từng bộ đánh giá; văn mẫu train/dev và n-gram giữa
hai bộ đánh giá được báo riêng. Shared template/owner không tự gây fail và không chứng minh
template/owner holdout. Không thay train/dev để né kiểm leakage sau khi xem kết quả test.

## Đóng băng

Trong giai đoạn soạn, cập nhật hash manifest bằng `draft_manifest(directory, data_dir,
dictionary)` sau khi chỉnh ba file JSONL; chỉ áp dụng khi status còn draft. Manifest pin
catalog, JSON Schema, ba split phát triển, dictionary manifest/entities/aliases/concepts.
Dictionary loader còn kiểm hash evidence của dictionary. Lệnh đóng băng kiểm đầy đủ trước
khi ghi `status=frozen`, timestamp và profile store với hash manifest Parquet/dictionary:

```bash
uv run --locked eth-nl2sql freeze-benchmark
```

Store sample không đáp ứng gate đóng băng. Lệnh từ chối ghi đè benchmark đã frozen; thay đổi
sau khi xem kết quả cần phiên bản mới. Các lệnh link/prompts/generate/echo-gold/evaluate/report
với `--split test` kiểm trạng thái frozen, hash và readiness trước khi dùng. Evaluate còn
đối chiếu store hiện tại với profile đã đóng băng và ghi hash manifest benchmark trong kết quả.

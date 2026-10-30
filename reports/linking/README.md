# Linking, baseline và bốn ablation — đánh giá phát triển

Ngày kiểm: **27/10/2026**. Đây là **development evaluation trên annotation nháp** của
100 câu `dev_eval`; 0/100 annotation có human review. Không phải kết quả test cuối hoặc
accuracy của LLM. Các lượt lưu ở đây dùng **lexical/fuzzy, không encoder**; retrieval và
generator không được chạy trên corpus trong lượt kiểm này. Store không bị thay đổi.

## Phạm vi triển khai

- Output v2 theo cấu trúc T07: `schema`, `entities`, `classes`, `properties`, mention có
  text và offset Unicode Python. Prediction không có gold SQL/hash SQL. Metadata của
  prediction bổ sung variant, trạng thái, ứng viên và phạm vi địa chỉ đại diện.
- `LinkingPipeline.link` chỉ nhận câu hỏi; `link_rows` chỉ đọc ID/câu hỏi. Scoring đọc
  annotation sau khi prediction đã được lưu. Kiểm thử chặn truy cập các trường gold.
- Resolver phân biệt `from/to/either`, `transaction/token_transfer/transaction_token_transfer_join`
  và `token_contract/endpoint`; thiếu cue giữ `null`. Không lấy thứ hạng schema làm bằng
  chứng property. Địa chỉ explicit giữ literal, không mở rộng sang toàn bộ owner.
- Alias nhập nhằng giữ danh sách ứng viên. Class có category, concept class và tập owner
  thuộc lớp trong dictionary. Chưa có cơ chế hỏi lại; cue có thể sai hoặc chưa phân giải.

| Variant | Config five-shot | Can thiệp |
|---|---|---|
| `full` | `b2l` | Schema + entity cascade + owner union + class + ba property |
| `baseline` | `b2l-baseline` | Exact tên/alias và địa chỉ, một địa chỉ đại diện; không class/property |
| `no_multi_address` | `b2l-no-multi-address` | Một địa chỉ theo thứ tự từ điển; hints dùng địa chỉ, không predicate owner mở rộng toàn bộ |
| `no_alias` | `b2l-no-alias` | Giữ canonical name/raw address/class; bỏ alias exact/fuzzy và owner paraphrase qua embedding |
| `no_class` | `b2l-no-class` | Bỏ hints lớp và tập thành viên |
| `no_property` | `b2l-no-property` | Bỏ ba property khỏi hints; schema ranking vẫn giữ nguyên |

Mỗi ablation giữ các tùy chọn khác của `full`; các hiện tượng kết hợp có thể tương tác.
`no_alias` vẫn fuzzy trên tên chuẩn để nhận lỗi chính tả; không dùng alias đã biết làm
đường vòng qua fuzzy/embedding. Địa chỉ được viết trực tiếp giữ nguyên ở mọi variant.

## Kết quả linking trực tiếp

| Variant | Relation@3 | Column@6 | Entity | Address-set | Multi-address set | Class | Membership | Direction | Fact | Address role |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| [full](full-dev_eval.json) | 96/110 | 44/168 | 45/47 | 45/47 | 43/45 | 7/7 | 7/7 | 28/52 | 76/92 | 30/54 |
| [baseline](baseline-dev_eval.json) | 96/110 | 44/168 | 45/47 | 2/47 | 0/45 | 0/7 | 0/7 | 0/52 | 0/92 | 0/54 |
| [no_multi_address](no_multi_address-dev_eval.json) | 96/110 | 44/168 | 45/47 | 2/47 | 0/45 | 7/7 | 7/7 | 28/52 | 76/92 | 30/54 |
| [no_alias](no_alias-dev_eval.json) | 96/110 | 44/168 | 27/47 | 27/47 | 27/45 | 7/7 | 7/7 | 19/52 | 78/92 | 19/54 |
| [no_class](no_class-dev_eval.json) | 96/110 | 44/168 | 45/47 | 45/47 | 43/45 | 0/7 | 0/7 | 26/52 | 76/92 | 28/54 |
| [no_property](no_property-dev_eval.json) | 96/110 | 44/168 | 45/47 | 45/47 | 43/45 | 7/7 | 7/7 | 0/52 | 0/92 | 0/54 |

Recall schema là micro recall relation@3 và column@6. Entity chấm owner hoặc địa chỉ explicit;
address-set so đúng tập giá trị. `multi_address_set` chỉ chấm mention owner có hơn một địa chỉ
gold. Class và membership chấm riêng. Property được ghép bằng mention, không dựa vào thứ tự
index trong prediction. Miss/chưa phân giải vẫn nằm trong mẫu số; N=0 trả `null`.
Prediction dư được ghi riêng theo case. Không dùng SQL do model sinh để chấm linking.

JSON từng variant chứa số đúng/tổng, kết quả từng case, annotation audit, hash nguồn và
metadata dự đoán. Schema recall thấp ở một số mục và các lỗi property vẫn là giới hạn của
bản cue-based lexical/fuzzy; các số này không chứng minh hiệu quả SQL hoặc parity store.

## Kiểm chứng và tái lập

- Kiểm thử tại lần đánh giá: **279 test PASS**, Ruff sạch; kiểm sender/recipient, transaction/event/join, token/endpoint,
  thiếu thông tin, địa chỉ explicit/nhiều địa chỉ, alias nhập nhằng và fallback khi bỏ alias.
- [Reproducibility](reproducibility.json): hai lượt dự đoán trên đủ sáu variant cho output và
  manifest giống từng byte; hai lượt chấm cũng giống từng byte. Manifest của prediction
  lưu code lúc dự đoán; `scorer_sha256` ghi riêng phiên bản bộ chấm.
- [Gate T07](gates.json): chín lệnh trên test draft bị từ chối trước model/prediction loading,
  gồm runner mới và bộ chấm mới. Artifact benchmark/test/review không bị sửa.
- Test runner offline dùng fixture kiểm các prompt có cùng system/schema, câu hỏi, năm ID
  retrieval và nội dung ví dụ; retrieve đúng một lần/câu. Kiểm thử chạy lại toàn bộ CLI
  preparation với cùng cache và so byte. Chưa có lượt MiniLM/retrieval thực tế hoặc LLM ở đây.

Chạy lại linking và scoring mà không cần extra `embed`:

```bash
uv run --locked eth-nl2sql link --split dev_eval --variant all --no-encoder
for variant in full baseline no_multi_address no_alias no_class no_property; do
  uv run --locked eth-nl2sql evaluate-linking --split dev_eval --variant "$variant" \
    --out "reports/linking/$variant-dev_eval.json"
done
uv run --locked pytest -q
uv run --locked ruff check src tests
```

Dựng prompt nghiên cứu với encoder pin và năm ví dụ dùng chung:

```bash
uv sync --locked --extra embed
uv run --locked eth-nl2sql link-experiments --split dev_eval
# Dùng lại đúng năm ID retrieval đã lưu:
uv run --locked eth-nl2sql link-experiments --split dev_eval \
  --examples runs/linking-examples-dev_eval.jsonl
```

Runner ghi prompt cho `b2`, `b2l` và năm config mới trong `runs/<config>/`, cache ID train và
`runs/linking-experiments-dev_eval.json`. Manifest ghi hash schema/dictionary, code, prompt,
train/cache và config generator/decoding. Cache bị từ chối nếu thiếu/trùng/không thuộc train,
trùng câu hỏi hoặc family. Dùng các lệnh `generate --config ...`, `evaluate --config ...` và
`report` hiện có cho từng config; generator, validator và store dùng cùng luồng hiện tại.

Chỉ dùng `--split test` sau khi benchmark đủ câu, quota, human review, hash/leakage và full snapshot
để đóng băng. Lượt này chưa chạy generator, EX, BigQuery parity hoặc benchmark cuối.

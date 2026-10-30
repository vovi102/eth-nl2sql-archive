## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run (local dataset validation)
- Origin Date: 2026-10-27T22:53:51+07:00
- Verification Status: UNVERIFIED (chưa có human review/full-snapshot verification)
- Version Label: t09a-draft-v2
- Repro Lock: null; pin dữ liệu/phụ thuộc trong manifest và báo cáo bên dưới

# T09A — 100 câu mới, gold SQL và annotation; vẫn draft

Đã soạn **100 câu tiếng Anh / 100 gold SQL phân biệt**, với annotation schema/entity/class/
property và hồ sơ review gắn hash. Tác giả là `codex-t09a` (agent). Không dùng prediction T08,
renderer train hoặc nhãn bootstrap từ SQL cũ làm gold. Không chạy generator, không chấm/tinh
chỉnh linker từ test v2, không đóng băng benchmark. **Human review: 0/100, tất cả pending.**

| Nhóm chính | Số câu |
|---|---:|
| `generic` | 20 |
| `multi_address` | 20 |
| `alias` | 20 |
| `class_level` | 20 |
| `ambiguous_property` | 20: direction 7 / fact 7 / address-role 6 |

Nhãn chồng lấn: multi-address 49, alias 23, class-level 20, property 20. Độ khó do tác giả
gán: easy 2, medium 84, hard 14; không phải độ khó đã đo trên model. Các câu phủ receipt
status, gas, metadata, block, bội số log/transaction, join/anti-join, cửa sổ tổng hợp,
union endpoint, owner-pair và class-pair. Không tuyên bố template/owner holdout hoặc đại diện
phân bố câu hỏi thực tế.

## Kiểm chứng T09A

| Kiểm tra | Kết quả và phạm vi |
|---|---|
| Cấu trúc, quota, annotation, hash | 100 case/annotation/review hợp lệ; manifest và phụ thuộc khớp |
| Leakage train/dev/dev_eval | Không trùng ID, câu chuẩn hóa, SQL canonical, family hoặc n-gram 12 token với test, kiểm n-gram cả hai chiều |
| Chỉ thay tên/ngày | Không trùng SQL với tập cũ sau che literal và alias; đây là phép sàng lọc cú pháp, chưa thay thế human review ngữ nghĩa |
| Gold SQL trên sample | 100/100 thực thi thành công; không phải accuracy của generator |
| Ca rỗng | 7 ca, đều có lý do riêng; không có aggregate toàn 0/NULL chưa giải thích |
| Multi-address chính | 20/20 có ít nhất hai địa chỉ raw hoạt động; đáp án gold union khác mọi địa chỉ riêng trên sample |
| Property | 20 đối chứng cố ý sai, 18/20 khác đáp án gold trên sample; `p04`, `p13` còn thiếu witness phân biệt |
| Human review | 0/100; agent không tự xác nhận thay người |
| Regression / lint | 282 test PASS; Ruff sạch trên src/tests/scripts/nguồn soạn |
| Phát hành | `status=draft`, `release_ready=false`; T09B còn chờ T06/full snapshot |

Các file chính:

- [Test mới](../../data/benchmark/v2/test.jsonl), [annotation](../../data/benchmark/v2/annotations.jsonl),
  [review pending](../../data/benchmark/v2/reviews.jsonl), [manifest](../../data/benchmark/v2/manifest.json).
- [Nguồn soạn](../../data/benchmark/v2/authoring.py) khai báo câu hỏi, SQL và target ngữ nghĩa
  riêng; chỉ tính span/hash và mở rộng owner/class từ dictionary. Schema target được khai
  báo riêng rồi đối chiếu bằng validator. Đọc các split cũ chỉ phục vụ hash/leakage/sàng lọc.
- [Lý do của tác giả](../../data/benchmark/v2/author-notes.jsonl) và
  [20 SQL đối chứng property](../../data/benchmark/v2/property-contrasts.jsonl); đối chứng không phải prediction.
- [Cấu trúc/hash/leakage](structure.json); [kết quả sample, digest và witness](sample.json).
- [Kiểm benchmark chuẩn trên sample](benchmark-sample.json): `passed=false` do **10 ca nhãn
  multi-address phụ chưa đạt witness**; danh sách và giới hạn helper ở bảng dưới. Không sửa
  nhãn để né gate; cần kiểm lại ở T09B. Sau retry tài nguyên, không còn lỗi thực thi SQL.
- [Hồ sơ human review đủ 100 câu](human-review.md): câu hỏi, SQL, annotation, preview có type,
  lý do tác giả, ca rỗng, đối chứng và hash. Người review điền danh tính/thời điểm/nhận xét/
  quyết định; hash nội dung phải còn hiệu lực khi ghi `human_reviewed`.
- [Tổng hợp human/release gate chặn đúng kỳ vọng](gates.json).
- [Trạng thái và handoff máy đọc được](status.json).

`structure.json.passed` kiểm artifact; `sample.json.execution_passed` kiểm thực thi SQL.
`sample.json.t09a_checks_passed` chỉ chứng nhận các kiểm tự động T09A, bao gồm 20 witness
multi-address chính, hồ sơ được tạo và ca rỗng có giải thích; không phải human approval,
không vượt qua mọi diagnostic/release gate của `benchmark-sample.json`.

| Diagnostic còn thiếu trong auditor chuẩn | Ca |
|---|---|
| Chưa có hai endpoint raw hoạt động phân biệt được trên sample | `a03`, `a04`, `a08`, `a17`, `a18`, `a20` |
| Helper raw witness hiện chưa xử lý fact join cho nhãn multi-address phụ | `p08`, `p09`, `p12`, `p13` |

Auditor chuẩn dùng 2 thread, memory limit 768 MB; `g16` gặp giới hạn bộ nhớ. Chỉ query đó
được chạy lại với 1 thread/1.536 MB và đã trả 20 hàng như lượt sample chính. Báo cáo giữ cả
lỗi tài nguyên ban đầu và retry thành công trong `resource_retries`; không thay gold SQL.
Giới hạn ban đầu và retry nằm trong JSON kết quả; đây không phải release PASS.

## Phạm vi dữ liệu và witness

Store riêng: `data/store/t09-sample-v2.duckdb`, nhãn v2 **6.647 địa chỉ**, dựng từ Parquet
sample đã có; store kế thừa không bị ghi đè. Profile:

- Scope: `labeled_address_transactions_plus_approximately_one_percent_of_other_transactions`.
- `complete_snapshot=false`; nguồn gồm 4.431.329 transaction, 4.001.230 token event,
  221.548 block, 16.386 contract và 2.489.651 dòng token metadata.
- Cửa sổ store `[2026-05-31, 2026-07-01)` UTC; 100 câu mới dùng tháng 6
  `[2026-06-01, 2026-07-01)` UTC. Metadata relation là snapshot, không có lịch sử theo ngày.
- Hash nhãn, manifest Parquet, benchmark và nguồn soạn nằm trong `sample.json`/manifest.
- Dictionary chưa có khoảng valid-from/valid-to; ngày xác minh nhãn sau tháng 6 không tự
  chứng minh quyền sở hữu trong tháng 6. Snapshot đầy đủ cũng không tự xác nhận lịch sử nhãn.

Với 20 ca multi-address chính, xác định tập địa chỉ hoạt động trực tiếp từ raw table theo
fact/chiều/window. Mỗi địa chỉ hoạt động được chạy lại **chính gold query** với mọi predicate
owner thay bằng một endpoint, giữ phép tổng hợp/filter/order/limit. Các địa chỉ không hoạt
động đều chọn tập raw rỗng; chạy một đại diện để kiểm kết quả tương đương. Điều này mạnh
hơn chỉ so tổng event của owner với từng wallet nhưng vẫn chỉ chứng minh trên sample.
Đối chiếu dùng typed row hash, float 12 chữ số có nghĩa, tôn trọng ORDER BY hoặc multiset;
giá trị preview giữ type và giới hạn 5 hàng. SUM normalized dùng DOUBLE cục bộ; raw numeric
cast dùng HUGEINT, nên không tuyên bố tương đương BigQuery BIGNUMERIC/NUMERIC hay accounting.

| Ca rỗng | Lý do cần giữ và kiểm lại |
|---|---|
| `a17`, `a20`, `c13` | Không có token event tương ứng với tập endpoint/class mixer đã pin trong sample; hoạt động router v1 không chứng minh coverage pool v2 |
| `c14` | Không có event thỏa cặp sender lending / recipient exchange trong sample |
| `p04` | Cặp outer sender Binance / recipient OKX rỗng; cặp đảo chiều cũng rỗng, chưa kiểm được chiều |
| `p13` | Join outer sender Binance / event recipient OKX rỗng; đối chứng event sender cũng rỗng, chưa kiểm được fact |
| `p14` | Negative control: token log trong outer transaction status 0 rỗng; đối chứng status 1 có hàng |

Giữ các ca rỗng có nghĩa; không đổi câu/owner để tạo kết quả đẹp. Chúng không chứng minh
absence trên toàn mạng hoặc correctness của resolver. Đối chứng chỉ so sánh với một SQL
sai được khai báo trước cho mỗi ca; chưa bao phủ mọi cách hiểu sai.

## Chạy lại và handoff T09B

```bash
uv run --locked eth-nl2sql build-store --parquet data/store/parquet \
  --labels data/entities/v2 --store data/store/t09-sample-v2.duckdb
uv run --locked python scripts/audit_t09a.py
uv run --locked eth-nl2sql check-benchmark --skip-execution \
  --out reports/benchmark/structure.json
uv run --locked eth-nl2sql check-benchmark --store data/store/t09-sample-v2.duckdb \
  --out reports/benchmark/benchmark-sample.json
uv run --locked pytest -q
uv run --locked ruff check src tests scripts data/benchmark/v2/authoring.py
```

Lệnh kiểm benchmark có thực thi hiện trả mã 1 do witness còn thiếu. Không dùng kết
quả sample để gỡ gate, chạy generator hay chọn cấu hình linker. `--require-human` trên ba
artifact v2 phải trả mã 1. Không gọi lệnh freeze trong T09A.

T09B chờ T06 cung cấp snapshot đầy đủ và các gate provenance/parity liên quan. Sau đó:

1. Dựng store full với dictionary v2, ghi scope/hash; chạy lại đủ 100 gold và kiểm join/NULL/
   zero/ca rỗng, đặc biệt `g15` có thể rỗng khi transaction coverage đầy đủ.
2. Kiểm witness raw và chính gold-query cho multi-address, kể cả nhãn phụ và các join;
   kiểm đủ 20 property, giải quyết `p04`/`p13` hoặc ghi rõ không đủ witness.
3. Người độc lập hoàn tất review câu hỏi–SQL–annotation và binding hash cho đủ 100 ca;
   sửa draft thì review lại phần bị thay đổi, không tự đánh dấu bằng agent.
4. Kiểm lại cấu trúc/quota/hash/leakage/gold/witness/human/full-snapshot và tất cả gate.
   Chỉ sau đó mới cân nhắc đóng băng theo giao thức T07.

T10 về compact và runner seed 42/43/44 có thể tiếp tục trên train/dev/dev_eval khi chờ;
T09A không triển khai hoặc chạy generator cho T10 trong phiên này.

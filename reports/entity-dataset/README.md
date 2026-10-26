# T05 — Dataset thực thể

Ngày thực hiện: **26/10/2026**. Bộ test gồm **100 câu: 50 chung + 50 thực thể**.
Review ngữ nghĩa bằng agent đã có cho toàn bộ 100 cặp; xác nhận của người review còn chờ.

## Kết quả xác nhận

| Kiểm tra | Kết quả |
|---|---|
| Chạy gold trên DuckDB local | 1.447 SQL phân biệt, không lỗi |
| Test có kết quả rỗng | `t05-e044` (outer exchange → DEX), `t05-e050` (token events từ TC); có giải thích |
| Test có aggregate 0/NULL | 0 |
| Multi-address | Đủ 34 owner; gold lớn hơn count của từng địa chỉ đơn lẻ |
| Nhãn test, có thể chồng lấn | 34 multi_address, 18 alias, 6 class_level, 23 ambiguous_property |
| Leakage với test | 0 câu chuẩn hoá, 0 SQL chuẩn hoá, 0 family và 0 n-gram 12 token |
| Train/dev | 0 câu/SQL/family trùng; 3.078 câu train chung n-gram văn mẫu với dev, được báo riêng |
| Kiểm thử | 165 test pass; Ruff sạch; `check-sql` kiểm đủ 1.447 SQL |
| Sinh lại | Renderer tái tạo đúng từng dòng thực thể; hash dataset/manifest/review khớp báo cáo |

Hai ca `t05-e045`/`t05-e046` cố ý dùng cùng cặp Binance → SwissBorg: outer transaction count là
**3**, còn token-transfer events nhận ở SwissBorg trong transaction do Binance gửi là **97**.
Cả hai khớp oracle độc lập, nên nhầm hai loại property sẽ tạo đáp án khác nhau trên sample này.

## Train/dev

| Dữ liệu | Train | Dev |
|---|---:|---:|
| Chung, kế thừa Stage A | 3.604 câu / 901 SQL | 396 câu / 99 SQL |
| Thực thể T05 | 1.268 câu / 317 SQL | 120 câu / 30 SQL |
| Tổng | 4.872 câu / 1.218 SQL | 516 câu / 129 SQL |

[Mười template](../../data/templates/entity_templates.json) gồm transaction theo owner gửi/nhận,
transaction có owner ở một trong hai đầu, owner pair có hướng, token events theo owner gửi/nhận,
lớp gửi/nhận, cặp lớp có hướng, địa chỉ owner hoạt động kèm số transaction. Chúng sinh từ 47 owner
ngoài token và sáu category có nhãn; không loại owner ít hoạt động hay ca rỗng để làm đẹp dữ liệu.

Mỗi SQL đã điền tham số có bốn cách diễn đạt, hai cách có thể chèn alias không nhập nhằng.
Family được hash từ SQL chuẩn hoá, seed 42, khoảng 10% dev; tối thiểu một family dev cho mỗi
template. Mọi alias/cách diễn đạt của cùng SQL nằm trọn trong một split. Các split không nhằm
đánh giá owner hoặc template chưa từng xuất hiện. Cửa sổ train/dev là các khoảng UTC nửa mở
1–4 ngày trong tháng 6, khác cửa sổ 31 ngày của test thực thể.

`build-entity-data` giữ các dòng nhập từ Stage A, thay đúng các dòng mang source
`t05:entity-templates-v1`, và ghi [manifest](../../data/entity-manifest.json). Nó không sinh lại
test hay tự ký lại hồ sơ review. Nếu cách diễn đạt/SQL trùng test thì loại cả family.

## Test và ngữ nghĩa

50 câu thực thể được soạn riêng trong [test.jsonl](../../data/test.jsonl), không render bằng
template train. Trường `primary_specific` chia 50 câu thành 34 multi-address, 4 alias, 6 class-level
và 6 ambiguous-property; `specifics` cho phép gắn nhiều nhãn. Số nhãn thực tế và kết quả từng
câu nằm trong [validation.md](validation.md) và [validation.json](validation.json).

- **Multi-address:** mỗi owner trong đủ 34 owner có nhiều địa chỉ hoạt động nhận một ca. Oracle
  join trực tiếp raw facts theo đúng from/to/either và cửa sổ UTC của câu, lưu count từng địa chỉ,
  count hợp nhất và count lớn nhất của một địa chỉ. Cả 34 ca phải có ít nhất hai địa chỉ khớp và
  gold lớn hơn mọi count chỉ dùng một địa chỉ. Internal transaction được tính một lần ở cấp owner.
- **Alias:** dùng mapping không nhập nhằng của v2, gồm Crypto.com, Curve Finance, Huobi Global,
  OKEx, Uni V2/V3/V4, OP Bridge, TC, TORN, USDT. Tránh bare `Huobi`/`Uniswap` vì dictionary giữ
  nhiều ứng viên. TC là owner dịch vụ; TORN là owner token riêng.
- **Class-level:** exchange, DEX, mixer, bridge, lending và exchange → DEX; bao gồm mọi owner
  và vai trò địa chỉ thuộc category, không ngầm giới hạn vào treasury hoặc một owner đại diện.
- **Ambiguous-property:** phân biệt outer transaction với token log, token contract với endpoint,
  chiều gửi/nhận, either endpoint và cặp owner hai hướng. Truy vấn ghép transaction/log dùng
  transaction hash, block number và block hash để tránh ghép nhầm hoặc tăng số dòng.

Test thực thể dùng UTC **[2026-05-31, 2026-07-01)**, tất cả receipt status trừ khi câu nói rõ
successful. Transaction value là trường wei ghi trong giao dịch, không phải thay đổi số dư đã
quyết toán. Token-event count đếm log; một transaction có nhiều log được đếm nhiều event.

SQL của 50 câu chung được giữ nguyên và vẫn phủ 29 intent. Review sửa ba câu:
`t35-051`/`t35-096` nói rõ mọi địa chỉ recipient có nhãn; `t35-100` nói rõ ưu tiên số token event,
sau đó native wei rồi hash. Các phép tổng hợp token symbol cố ý nhóm theo symbol và đơn vị
normalized; không diễn giải chúng thành giá trị tiền hoặc định danh token duy nhất.

[test-review.json](../../data/test-review.json) lưu ghi chú, người review là agent, trạng thái
human review và hash câu hỏi/SQL của từng câu. Thay câu/SQL làm review hết hiệu lực.
Bản đọc dành cho người review, có đủ câu hỏi, SQL và ghi chú cho từng ID, nằm trong
[test-review.md](test-review.md); header ghi hash của bản dataset được review.

## Kiểm gold và leakage

```bash
uv run --locked eth-nl2sql build-entity-data
uv run --locked eth-nl2sql check-dataset
uv run --locked eth-nl2sql check-sql
uv run --locked pytest -q
uv run --locked ruff check src tests
```

`check-dataset` mở DuckDB read-only, thực thi mọi SQL phân biệt của train/dev/test (1.447 SQL),
ghi số dòng/digest/columns và lỗi theo từng ID. Các count test thực thể có oracle raw-table độc
lập; kiểm các cặp/lớp và phép join riêng, không chỉ kiểm câu SQL có chạy được hay không.
`empty_result_ids` chỉ kết quả không có dòng; `zero_aggregate_ids` ghi riêng một dòng tổng hợp
toàn 0/NULL. Các ca rỗng có giải thích trong dataset và báo cáo, được giữ trong test.

Chạy dữ liệu thật đã phát hiện 86 SQL cũ (344 cách diễn đạt) lỗi tại literal một ETH:
SQLGlot chuyển `NUMERIC` không tham số thành DuckDB `DECIMAL(18,3)`. Backend nay chuyển thành
`DECIMAL(38,9)` đúng với schema NUMERIC, giữ precision/scale khi SQL chỉ định rõ. Regression test
kiểm ngưỡng wei trên dữ liệu có dòng và chín chữ số thập phân; schema rỗng không phát hiện lỗi này.

Kiểm leakage gồm ID, câu chuẩn hoá, SQL chuẩn hoá và family cho ba cặp split; train/dev không
được trùng n-gram 12 token với test. Những n-gram văn mẫu chung giữa train/dev được ghi riêng,
không bị báo là sạch: dữ liệu chung ban đầu đã có 2.475 câu train trùng n-gram với dev. Đây là
split theo family SQL và không giữ template độc quyền cho một split.

## Giới hạn

Store T03 là dữ liệu lấy mẫu, không phải snapshot đầy đủ hoặc parity BigQuery. Manifest data,
dictionary và scope được giữ trong báo cáo. Source xác minh sau cửa sổ tháng 6 không chứng minh
lịch sử sở hữu. Số 0/rỗng chỉ mô tả sample local.

Tornado Cash chỉ có router hoạt động local; không dùng owner này làm chứng cứ nhiều pool hoặc
multi-address. Các phép kiểm lớp mixer vẫn bao gồm pool/router có nhãn, dù pool không có hoạt
động quan sát được. Hoàn tất yêu cầu có người review của đề cương cần human sign-off cho hồ sơ
100 câu; task này không tự nhận đã có xác nhận đó.

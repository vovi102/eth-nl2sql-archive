# Phương pháp nghiên cứu

Tài liệu này là nguồn mô tả phương pháp chính của project; [README](README.md) dành cho
người mới tìm hiểu và chạy hệ thống. **Hiện trạng** mô tả code/artifact đã có; **thiết kế
đích** là yêu cầu nghiên cứu đã chốt nhưng chưa hoàn tất; **việc còn thiếu** được tổng hợp
ở mục 6. Cập nhật tài liệu ngày **27/10/2026** không tạo dữ liệu hoặc kết quả thực nghiệm mới.

## 1. Mục tiêu nghiên cứu và đóng góp

Dữ liệu Ethereum công khai hỗ trợ phân tích an ninh, AML và nghiên cứu, nhưng truy vấn đòi
hỏi hiểu schema và SQL. Hệ thống nhận câu hỏi tiếng Anh, liên kết schema/thực thể, sinh
GoogleSQL bằng LLM, kiểm tra rồi thực thi để trả kết quả.

Ba đóng góp dự kiến có vai trò ngang nhau. Việc có code hoặc gold SQL chạy được chưa xác
nhận hiệu quả nghiên cứu.

| Đóng góp | Mục tiêu / câu hỏi cần trả lời | Bằng chứng cần thu thập |
|---|---|---|
| Dataset Ethereum NL–SQL | Bộ dữ liệu phủ những tác vụ, cấu trúc SQL và cách diễn đạt nào; gold có đủ tin cậy để đánh giá không? | Số câu/SQL/template, phân bố tác vụ và độ khó, kiểm thực thi và ngữ nghĩa, leakage, human review |
| Schema/entity linking | Linking đặc thù cải thiện độ đúng bao nhiêu, và cơ chế nào giúp từng hiện tượng? | Schema recall, độ đúng entity/class/property, EX theo nhóm, baseline và bốn ablation |
| Phân tích fine-tuning | Zero-shot, five-shot và QLoRA có/không linking khác nhau thế nào về accuracy, latency, chi phí và điều kiện triển khai? | Đối chứng prompt, ba seed QLoRA, kết quả từng seed và tổng hợp, đo tài nguyên và mô tả luồng dữ liệu/privacy |

**Tính mới cần khảo sát:** [BIRD (2023), mục 3.2](https://arxiv.org/html/2305.03111v3) đã liệt
kê blockchain trong các miền của benchmark tổng quát. Vì vậy chưa tuyên bố đây là dataset
blockchain NL–SQL công khai đầu tiên. Khoảng trống dự kiến là benchmark chuyên Ethereum có
nhãn và đánh giá riêng cho nhiều địa chỉ, alias, lớp thực thể và property; cần khảo sát
thêm để xác nhận. Tương tự, chưa khẳng định mọi phương pháp NL2SPARQL truyền thống đều không
xử lý được bốn hiện tượng này khi chưa có đối chiếu cụ thể.

## 2. Định nghĩa bài toán, phạm vi và kiến trúc

### 2.1. Đầu vào, đầu ra và phạm vi

- **Đầu vào:** câu hỏi tiếng Anh, catalog schema cố định và dictionary Ethereum mainnet
  có phiên bản. Gold SQL chỉ được dùng trong train/dev và đánh giá, không đưa vào prompt
  cho câu hỏi đang được đánh giá.
- **Đầu ra:** một câu GoogleSQL read-only và kết quả thực thi, hoặc trạng thái lỗi nếu không
  qua kiểm tra/thực thi. Hệ thống hiện chưa có luồng hỏi lại để giải quyết nhập nhằng.
- **Phạm vi chính:** một schema và các owner/lớp đã biết trong dictionary. Kết quả chưa chứng
  minh tổng quát hóa sang schema, owner hoặc template chưa gặp. Chỉ hỗ trợ các tác vụ có
  trong catalog; không đánh giá khả năng kết luận AML hoặc điều tra hoàn chỉnh.
- **Thời gian:** UTC, cửa sổ dữ liệu `[2026-05-31, 2026-07-01)`. Tham số ngày là DATE,
  start < end, tối đa 31 ngày. Ngoài snapshot phải báo `window_outside_snapshot`.

### 2.2. Hai luồng hệ thống

```text
Chuẩn bị dữ liệu:
BigQuery public Ethereum → trích xuất/bổ sung → Parquet → DuckDB + managed layer
                                                          ↑
                                               dictionary nhãn thực thể

Trả lời câu hỏi:
Câu hỏi → Schema linker + Entity linker → Resolver → Linking hints → Prompt
  → LLM (± QLoRA) → Trích GoogleSQL → Validator → SQLGlot → DuckDB → Kết quả
```

DuckDB là backend thực thi đã chọn. SQL được viết lại tên relation rồi chuyển từ GoogleSQL
bằng SQLGlot; tham số ngày của table function được tính trước khi chạy. Mọi cấu hình dùng
cùng store, dictionary và quy tắc validator. Tắt linking chỉ bỏ hints, không xóa nhãn khỏi
managed layer; chênh lệch EX vì vậy đo giá trị hỗ trợ của linker trên cùng tài nguyên dữ liệu.

## 3. Dữ liệu blockchain và xây dựng dataset NL–SQL

### 3.1. Ba lớp dữ liệu

| Lớp | Nguồn và vai trò |
|---|---|
| Blockchain | `bigquery-public-data.crypto_ethereum`; cung cấp dữ liệu để thực thi SQL |
| Dictionary nhãn | Ánh xạ địa chỉ → owner, alias và lớp, kèm nguồn/phiên bản; dùng chung cho linker và managed layer |
| Dataset NL–SQL | Các cặp câu hỏi tiếng Anh–SQL chuẩn do project xây dựng/kế thừa trên schema đó; phục vụ train/dev/đánh giá |

Dữ liệu blockchain kế thừa từ BigQuery là nền thực thi; đóng góp dataset nằm ở bộ cặp NL–SQL,
annotation và quy trình kiểm chứng.

### 3.2. Store hiện tại và snapshot đích

**Hiện trạng:** store phát triển dùng bộ CSV đã lọc/lấy mẫu từ `luanvan`, khôi phục block
hash/number bằng join đã kiểm tra và bổ sung thuộc tính thiếu từ BigQuery. Contract bổ sung
bao gồm token address quan sát trong token transfer; cờ ERC lịch sử trong CSV được giữ
nguyên. `prepare-local` không tạo giá trị giả cho cột thiếu. Manifest Parquet ghi checksum,
số dòng, mapping và provenance job bổ sung; DuckDB lưu scope và hash manifest/dictionary.
Đủ ngày/cột không có nghĩa là đủ giao dịch toàn mạng. Xem [báo cáo store local](reports/local-store/README.md).

**Snapshot đầy đủ, chưa hoàn tất:** lấy `transactions` (bỏ `input`), `blocks`,
`token_transfers` trong cửa sổ trên; `contracts` lấy các địa chỉ xuất hiện trong cửa sổ;
`amended_tokens` lấy toàn bộ. Việc trích dữ liệu dùng quota BigQuery; thực thi trên bản sao
local giúp giảm truy vấn BigQuery lặp lại trong ma trận thí nghiệm.

T06 đã chuẩn bị streaming/resume theo job ID, provenance và cap bytes tích lũy. Lần kiểm tra
27/10/2026 dùng chính sách chỉ miễn phí, không gắn billing: dry-run đủ 95 partition nhưng
preflight chặn thực thi do allowance miễn phí không còn. Chưa có kết quả parity đầy đủ hoặc
gold/coverage v2 trên full snapshot. Xem [báo cáo T06](reports/local-store/README.md).

Theo yêu cầu ngày 27/10/2026, phần kiểm nghiệm T06 trên snapshot đầy đủ được ghi lại và hoãn
để thực hiện sau. Parity, kiểm chứng manifest/resume thực tế và gold/coverage v2 vẫn chưa đạt
kiểm chứng; không tự chạy lại khi quota được cấp lại.

**Managed layer hiện có:** hai view `entity_labels_v1`, `token_dimension` và sáu table function
`transaction_facts`, `block_facts`, `contract_dimension`, `token_transfer_facts`,
`labeled_transactions`, `labeled_token_transfers`. DuckDB biểu diễn bằng view/table macro
có cùng cột và tham số. Tên `entity_labels_v1` là giao diện SQL, không phải phiên bản nhãn;
`build-store` và `link` mặc định dùng dictionary v2.

**Parity, chưa hoàn tất:** lệnh `parity` yêu cầu snapshot đầy đủ và store nhãn v1, đối chiếu
row digest với 88 gold BigQuery thật của campaign c03 và số dòng của 206 witness Stage A.
Ngưỡng gate hiện có là ≥95% gold khớp; phải báo cáo và giải thích từng sai khác. Fixture v1
không kiểm chứng nhãn v2 hoặc gold test v2. Gate này không chứng minh mọi truy vấn tương
đương BigQuery; đánh giá chính luôn so prediction và gold trên cùng DuckDB đã đóng băng.

### 3.3. Dataset hiện tại: nền phát triển

| Phần | Câu train / dev | SQL phân biệt train / dev | Template và cách diễn đạt |
|---|---|---|---|
| Chung, Stage A v2 | 3.604 / 396 | 901 / 99 | 25 template; mỗi SQL có bốn cách diễn đạt |
| Thực thể, T05 | 1.268 / 120 | 317 / 30 | 10 template; mỗi SQL có bốn cách diễn đạt, có alias |
| **Tổng** | **4.872 / 516** | **1.218 / 129** | **35 template; 1.347 SQL train/dev, 5.388 câu** |

Bốn cách diễn đạt do renderer tất định sinh là formal, conversational, abbreviated và
alternative. Paraphrase không phải bốn SQL hoặc bốn tác vụ độc lập. Phần thực thể có 347
family; seed split 42 và tối thiểu một family dev cho mỗi template. Đây là split theo SQL
đã điền tham số, không giữ template hoặc owner riêng cho một split; hai template chung
chưa có family trong dev hiện tại.

Bộ `data/dev_eval.jsonl` (trước T07 là `data/test.jsonl`) hiện có **100 câu / 100 SQL**, gồm
50 câu chung phủ 29 intent và 50 câu thực thể soạn riêng. Nhãn chính của phần thực thể là 34 multi-address, 4 alias, 6 class-level
và 6 property; khi tính cả nhãn phụ là 34/18/6/23. Các nhóm nhãn phụ có thể chồng lấn.
Bộ này đã được xem và dùng trong quá trình thiết kế, nên được xem là **bộ đánh giá phát triển**.
T07 đã chuyển nguyên vẹn sang file và split `dev_eval`; CLI và notebook mặc định dùng
bộ này. Tên `test` dành riêng cho `data/benchmark/v2/test.jsonl`, có 100 câu draft T09A
và bị chặn trước khi đóng băng.

**Kiểm chứng đã có:** 1.447 SQL phân biệt của cả ba split đã chạy trên DuckDB sample không
lỗi. Các count thực thể có raw-table oracle; 34 ca multi-address cho kết quả hợp nhất lớn
hơn mọi count của từng địa chỉ riêng theo đúng fact, chiều và cửa sổ. Ca rỗng hợp lệ và
aggregate 0/NULL được báo riêng, không loại để tăng EX. Tornado Cash hiện chỉ chứng minh
router/service alias hoặc token TORN, chưa chứng minh nhiều pool cùng hoạt động.

Kiểm leakage hiện có không thấy trùng câu chuẩn hóa, SQL chuẩn hóa hoặc family giữa các
split, và không chung n-gram 12 token giữa train/dev với test hiện tại. N-gram văn mẫu chung
train/dev vẫn tồn tại và được báo cáo riêng; không suy ra khả năng tổng quát hóa từ vựng
hoặc cấu trúc. Review agent có hash cho đủ 100 cặp, nhưng **human review còn chờ**. Xem
[báo cáo và hồ sơ review](reports/dataset/README.md).

### 3.4. Thiết kế test v2 và quy trình chất lượng — T09A draft, T09B chờ T06

Giữ quy mô train/dev hiện tại làm nền, không ép giảm xuống đúng 1.000 cặp. Test v2 gồm
**100 câu mới / 100 gold SQL phân biệt**, phân bố theo nhãn chính:

| Nhãn chính | Số câu | Nội dung |
|---|---:|---|
| Chung | 20 | Tác vụ trong catalog, đa dạng fact, phép tổng hợp, join và độ khó |
| `multi_address` | 20 | Hợp nhất các địa chỉ đã biết của một owner |
| `alias` | 20 | Tên gọi khác về đúng thực thể, không ngầm chọn một ứng viên nhập nhằng |
| `class_level` | 20 | Lớp owner đã gán nhãn, gồm DEX và các lớp hỗ trợ khác |
| `ambiguous_property` | 20 | 7 câu gửi/nhận, 7 câu transaction/token event, 6 câu token contract/endpoint |

Nhãn chính tạo năm nhóm rời nhau; nhãn phụ được phép chồng lấn và phải báo số câu thực tế.
Đây là benchmark chẩn đoán cân bằng, không đại diện phân bố câu hỏi của người dùng thực tế.

Quy trình đích:

1. Cố định catalog, phạm vi snapshot và dictionary có nguồn; soạn câu hỏi độc lập với renderer
   train, không chỉ đổi tên/ngày của câu test cũ. Kiểm số câu, SQL, template/intent, độ khó và
   mức đa dạng ngôn ngữ riêng; ghi rõ nguồn câu hỏi do người/agent soạn.
2. Viết gold SQL và annotation schema/entity/class/property; có người review độc lập đối chiếu
   câu hỏi–SQL–nhãn. Review agent chỉ hỗ trợ; lưu người xác nhận, ghi chú và hash nội dung.
3. Chạy gold trên store thực tế, đối chiếu raw-table oracle hoặc witness độc lập cho các ca
   chẩn đoán. Với multi-address phải có ít nhất hai địa chỉ quan sát được và witness phân biệt
   hợp nhất với một địa chỉ. Giữ ca rỗng hợp lệ kèm giải thích; không dùng EX rỗng làm bằng chứng
   duy nhất rằng cơ chế linking đúng.
4. Kiểm leakage với train/dev và bộ đánh giá phát triển cũ: câu chuẩn hóa, SQL chuẩn hóa và
   family không trùng; kiểm n-gram 12 token với train/dev. Mọi paraphrase cùng SQL phải ở cùng
   split. Báo cáo việc dùng chung template/owner; không tuyên bố split cấu trúc hoặc owner mới.
5. Đóng băng test, annotation, review, dictionary và manifest store bằng hash trước thí nghiệm
   cuối. Chỉ chỉnh prompt, ngưỡng, siêu tham số và checkpoint trên dev; retrieval chỉ lấy train.
   Thay test sau khi đã xem kết quả phải tạo phiên bản mới, không ghi đè benchmark đã công bố.

Mỗi câu test SQL chính phải có cách hiểu đủ rõ để xác định gold. Câu thực sự thiếu thông tin
không được ép một SQL tùy ý; cần cơ chế hỏi lại ngoài phạm vi pipeline hiện tại.

**T07 đã triển khai hạ tầng:** JSON Schema cho case, annotation, review và manifest; annotation
relation/cột, mention–owner/address, class/membership và ba property `direction`, `fact`,
`address_role`. Review gắn hash câu hỏi, SQL và annotation; human review cần người xác nhận
độc lập, timestamp và ghi chú. Có kiểm mọi cặp split, hash các phụ thuộc, gold trên DuckDB,
quota 20×5 và property 7/7/6, cùng gate đóng băng yêu cầu full snapshot.
100 annotation phát triển được bootstrap từ SQL/expectation cũ, đều là draft pending human review.
T09A đã soạn 100 câu/100 SQL cùng annotation khai báo trực tiếp từ ý hỏi và catalog/dictionary,
không dùng prediction T08 hoặc bootstrap annotation phát triển. Tác giả là agent; toàn bộ
review vẫn pending. Kiểm cấu trúc/hash/leakage và thực thi gold, đối chứng property, ablation
địa chỉ trên sample có [hồ sơ T09A](reports/benchmark/README.md).
Benchmark vẫn draft. T09B chờ T06: kiểm lại gold, witness multi-address/property và ca rỗng
trên snapshot đầy đủ, hoàn tất human review và mọi gate trước khi đóng băng. Không chạy
generator hoặc chỉnh linker từ test v2 trong T09A. Xem [giao thức](data/benchmark/README.md)
và [kiểm chứng hạ tầng T07](reports/dataset/README.md).

## 4. Schema/entity linking

### 4.1. Phương pháp hiện có

Ba thành phần kế thừa từ `luanvan`, hiện giữ thuật toán và ngưỡng:

- **Schema linker:** điểm = 0,65 × cosine MiniLM `all-MiniLM-L6-v2` + 0,35 × độ trùng từ,
  mở rộng bằng synonym; trả 3 relation và 6 cột đứng đầu. Revision encoder pin trong config.
- **Entity linker:** address regex → alias chính xác → fuzzy ≥0,85 → embedding ≥0,75;
  biên nhập nhằng 0,03. Khớp xấp xỉ tên token chỉ nhận cụm có chữ hoa, tránh “ten token”
  thành “WEN Token”. Output giữ ứng viên khi alias trùng.
- **Resolver:** owner mang tập địa chỉ đã gán nhãn; hints hướng lọc `entity_labels_v1.owner`.
  Concept giải về `concept_class`. Chiều gửi/nhận lấy từ cue trong 40 ký tự trước mention,
  rồi từ schema linker, cuối cùng là `unspecified`.

### 4.2. Bốn hiện tượng trong thiết kế đích

Ví dụ dưới đây minh họa tác vụ; câu trong benchmark phải có cửa sổ UTC rõ ràng.

| Hiện tượng | Ví dụ tiếng Anh | Đầu ra mong đợi và cách đo | Giới hạn |
|---|---|---|---|
| Multi-address | “Count transactions sent by Binance.” | Owner chuẩn và hợp của các địa chỉ đã biết; đo target/tập địa chỉ đúng, EX và witness so một địa chỉ | Danh sách tuyển chọn, không phải mọi địa chỉ Binance thực tế |
| Alias | “Count transactions sent to TC.” | Alias TC → owner dịch vụ Tornado Cash; đo owner đúng và EX; giữ tập ứng viên nếu chưa phân giải được | Alias dịch vụ và token TORN phải tách; nhập nhằng không được coi là đã resolve |
| Class-level | “Count transactions sent to any DEX.” | Lớp `DEXProtocol` và phạm vi owner thuộc lớp trong dictionary; đo lớp đúng và EX | Chỉ các DEX đã gán nhãn; không có xếp hạng “major” hoặc bao phủ mọi DEX |
| Property | “Count token-transfer events received by Binance.” | Xác định recipient, fact token event và vai trò endpoint; đo riêng từng loại property và EX | Resolver dựa trên cue trong câu; thiếu thông tin giữ chưa phân giải, chưa có hỏi lại |

Property được chia thành ba loại: **gửi/nhận**, **outer transaction/token-transfer event** và
**token contract/địa chỉ endpoint**. Token-event count đếm log; một transaction có thể chứa
nhiều event. Các join transaction/log phải kiểm khóa và tránh nhân bản dòng. Giao dịch gửi
tới địa chỉ DEX không mặc nhiên là swap. Giá trị wei ghi trong transaction, gồm cả giao dịch
thất bại nếu câu không lọc successful, không được diễn giải thành thay đổi số dư đã quyết toán.

“Any/all DEX” là truy vấn lớp đã biết. Từ “major” bị loại khỏi thiết kế benchmark v2 vì chưa
có tiêu chí xếp hạng. Code/dictionary hiện vẫn có thể khớp cụm này; tài liệu không xem đó là
khả năng xác định DEX lớn. Trường hợp chưa xác định được owner hoặc property cần cơ chế làm
rõ; trạng thái chưa phân giải không phải bằng chứng hệ thống đã giải quyết nhập nhằng.
Output v2 dùng `mention={text,start,end}` theo offset Unicode của Python, tách `entities`
(owner, addresses, address_scope), `classes` (category, concept_class, owners) và `properties`
theo T07. `either` có nghĩa là cả hai endpoint; property chưa xác định là `null`, không suy
từ thứ hạng schema. Địa chỉ viết trực tiếp chỉ giữ địa chỉ đó, kể cả khi biết owner.
Alias nhập nhằng giữ danh sách ứng viên, không chọn tùy ý. Pipeline chỉ nhận chuỗi câu hỏi;
boundary xuất dự đoán chỉ đọc `id` và `question`, không đọc gold SQL hoặc annotation.

### 4.3. Dictionary và phạm vi nhãn

Dictionary v1 có 5.135 địa chỉ, trong đó 5.078 là token; 57 owner còn lại mỗi owner chỉ có
một địa chỉ. V2 giữ địa chỉ v1 và có 6.647 địa chỉ, 47 owner ngoài token, 40 owner nhiều địa
chỉ. TORN được tách khỏi owner Tornado Cash gồm 19 pool và một router. Alias `Uniswap` giữ
các ứng viên V2/V3/V4 thay vì ghi đè thành một owner.

Loader kiểm địa chỉ, chain, nguồn/ngày, owner–alias–lớp và checksum. Nguồn có URL, revision,
locator và thời điểm xác minh; API Binance/Bitstamp có snapshot và SHA-256. Coverage join
raw tables local theo vai trò from/to/token, giữ địa chỉ có count 0 và tách metadata presence
khỏi hoạt động. Một dòng chỉ đếm một lần cho mỗi owner/lớp. Nguồn xác minh sau cửa sổ dữ liệu
không chứng minh khoảng sở hữu lịch sử; danh sách tuyển chọn không chứng minh độ phủ toàn mạng.
Xem [quy tắc dictionary](data/entities/v2/README.md) và [coverage](reports/dictionary-v2/coverage.md).

## 5. Thiết kế thực nghiệm và đánh giá

### 5.1. Holdout và model

**Thiết kế đích:** holdout train/dev/test, không yêu cầu cross-validation. Test cuối là v2;
bộ test hiện tại chỉ phục vụ phát triển. Dùng ba seed QLoRA **42, 43, 44** trên cùng split;
không đổi split theo seed huấn luyện. Mỗi seed chọn checkpoint theo dev loss. Báo cáo từng
seed, trung bình và độ lệch chuẩn; không chọn seed tốt nhất trên test. Greedy decoding không
loại bỏ biến thiên từ huấn luyện. T10 đã có runner/tổng hợp ba seed, kiểm thử bằng fixture
và backend giả. T11A đã chạy hai compact base control trên `dev_eval`; ở lượt T11A chưa
huấn luyện QLoRA.

**Cập nhật phát triển T11B, 29/10/2026:** `b3/42` đã train 608 step trên 4.872 train /
516 dev, checkpoint-608 có dev loss thấp nhất 0,0000535721. Smoke dừng ở 7/10 compile,
EX 0/10 trên DuckDB sample; không gộp lượt 10 câu này vào bảng kết quả 100 câu. Adapter,
checkpoint và dự đoán được giữ nguyên để chẩn đoán lệch cách diễn đạt ngày, khả năng học
cột từ compact prompt và masking/loss. Chưa mở rộng seed và chưa dùng test v2.
Xem [bằng chứng T11B](reports/experiments/README.md).

Chẩn đoán tiếp theo giữ adapter đóng băng, can thiệp prompt theo thiết kế 2×2
ngày/cột. Nhánh kết hợp qua smoke 10/10 rồi sinh đủ 100 câu phát triển, đạt
85/100 compile và EX 19/100; `b3-base` cùng messages đạt 0/100. Đây là can thiệp
inference khác prompt train gốc, được báo cáo riêng; chưa cập nhật cấu hình chính
hoặc train adapter mới. Masking/loss đã kiểm trên toàn bộ span local và đối chiếu
CE trực tiếp trên runtime GPU. Prompt kết hợp còn tương tác bất lợi về ngày;
quyết định chưa mở rộng seed. Xem [báo cáo chẩn đoán](reports/experiments/README.md).

**Cấu hình hiện có làm nền:** `meta-llama/Meta-Llama-3-8B-Instruct` và encoder pin revision
trong `configs/experiment.toml`; generator NF4 4-bit, compute float16 trên T4, greedy, tối đa
512 token, dừng ở `<|eot_id|>`. QLoRA r=16, α=32, dropout 0,05, module q/k/v/o, lr 2e-4 cosine,
batch hiệu dụng 16, tối đa 2 epoch, early stopping theo dev loss. Loss chỉ trên token SQL
và token EOT kết thúc lượt; prompt và padding được mask bằng -100;
dòng dài hơn 1.024 token bị bỏ và có đếm. Config huấn luyện có ba seed 42/43/44; seed
generation và bootstrap vẫn là 42. Preflight ghi
ID/số dòng giữ/bỏ và token; dừng nếu train hoặc dev rỗng sau lọc. Không cắt target SQL.
T11A đã báo cáo hai base control, mỗi cấu hình 100 câu phát triển: EX đều 0/100 do SQL
không qua validator/compiler. Kết quả này xác nhận đường ống GPU/resume/evaluator hoạt động,
không xác nhận chất lượng SQL hoặc hiệu quả fine-tuning. Xem [T11A](reports/experiments/README.md).

### 5.2. Các cấu hình và đối chứng compact

| Config đã có | Prompt | Chế độ |
|---|---|---|
| `b1` / `b1l` | Catalog đầy đủ, cú pháp gọi và quy tắc [+ linking] | Zero-shot |
| `b2` / `b2l` | Như B1 + 5 ví dụ retrieval từ train [+ linking] | Five-shot |
| `b3-base` / `b3l-base` | Chính xác prompt của `b3` / `b3l` | Base model không adapter |
| `b3` / `b3l` | Chữ ký 8 relation (compact) [+ linking] | QLoRA, ba seed |

Retrieval cosine MiniLM hiện lấy train, loại câu trùng và cùng family khi có ID family;
ID ví dụ được lưu. Ma trận chính giữ ba chế độ × có/không linking. Train và inference của
mỗi adapter phải dùng cùng kiểu prompt, có/không hints theo cấu hình tương ứng.

**Đối chứng compact đã triển khai (T10):** `b3-base` và `b3l-base` dùng chính messages/hash
prompt của `b3` và `b3l`, tương ứng không/có linking, cùng giới hạn sinh và validator.
`prompt_style` được chọn độc lập với cờ `fine_tuned`. So với QLoRA cùng prompt để đo tác động thích nghi trọng số. So QLoRA với B1/B2 có prompt khác
chỉ phản ánh khác biệt giữa các cấu hình triển khai, không quy toàn bộ chênh lệch cho
fine-tuning. T11A đã chạy cả hai đối chứng không adapter, seed generation 42, đủ 100 câu
`dev_eval` mỗi cấu hình; không suy diễn lượt smoke 10 câu thành accuracy trên 100 câu.

### 5.3. Baseline linking và ablation

Thực hiện trên generator **five-shot không fine-tune**, cùng catalog đầy đủ, store,
dictionary, câu hỏi, năm ví dụ retrieval, decoding và validator. `b2` là mốc không hints;
`b2l` là mốc đầy đủ với resolver ba property.

| Thí nghiệm đích | Can thiệp so với linking đầy đủ |
|---|---|
| Baseline linking thông thường | Giữ schema linker; exact-match tên chuẩn/alias và địa chỉ thô; mỗi owner chỉ gợi ý một địa chỉ đại diện theo thứ tự từ điển của địa chỉ; không mở rộng lớp hoặc property |
| Bỏ multi-address | Chỉ gợi ý một địa chỉ đại diện như trên thay vì hợp địa chỉ/lọc owner |
| Bỏ alias | Không dùng các tên gọi khác để resolve owner; giữ hỗ trợ tên chuẩn/địa chỉ |
| Bỏ class-level | Không đưa hints lớp và mở rộng thành viên lớp |
| Bỏ property | Không đưa gợi ý chiều gửi/nhận, loại fact và vai trò token/endpoint |

Mỗi ablation chỉ thay cơ chế tương ứng, không xóa dữ liệu/nhãn trong store hoặc thay generator.
Báo cáo EX tổng và từng nhóm với số câu; các ca kết hợp nhiều hiện tượng có thể chịu tương
tác giữa cơ chế. Config tương ứng là `b2l-baseline`, `b2l-no-multi-address`,
`b2l-no-alias`, `b2l-no-class`, `b2l-no-property`. Nhánh bỏ alias giữ tên chuẩn/địa chỉ,
fuzzy trên tên chuẩn và linking lớp; loại alias trong exact/fuzzy và owner paraphrase
trong embedding để fallback không khôi phục cơ chế đã bỏ.

`link-experiments` lấy năm ví dụ từ train một lần cho mỗi câu rồi dựng cả bảy bộ prompt.
Có thể dùng lại `--examples runs/linking-examples-dev_eval.jsonl`; cache chỉ chứa ID train,
được kiểm số lượng, trùng ID, câu giống hệt và family leakage. Manifest ghi hash prompt,
cache, dictionary, catalog, code và config generator/decoding. Store không bị sửa.
Các lệnh `generate`, `evaluate`, `report` dùng được cho từng config five-shot mới;
chưa chạy LLM cho baseline/ablation five-shot.

### 5.4. Đánh giá SQL hiện có

- **Trích SQL:** lấy fence đầu tiên hoặc dòng đầu bắt đầu SELECT/WITH, bỏ dấu `;` và prose
  cuối theo bộ trích hiện có. `format_ok` ghi riêng việc output có đúng một câu SQL.
- **Thứ tự kiểm:** một câu read-only, không comment/`;`, không `SELECT *`, chỉ tám relation
  trong allowlist → cửa sổ ngày → chuyển/biên dịch/thực thi DuckDB; timeout 120 giây.
- **EX, chỉ số chính:** so kết quả gold và prediction trên cùng store. Chuẩn hóa số theo
  giá trị, float 12 chữ số có nghĩa, timestamp UTC; so dãy nếu gold có ORDER BY ngoài cùng,
  ngược lại so multiset, không so tên cột. Mọi lỗi prediction giữ trong mẫu số; gold lỗi
  phải sửa và kiểm lại dataset trước đánh giá.
- **Chỉ số phụ đã có:** tỷ lệ SQL thực thi hợp lệ qua validator, format, EM/structural match
  canonical SQLGlot, answer F1 và EX theo subset, nhãn hiện tượng, độ khó, kèm số câu.
- **Thống kê hiện có:** bootstrap CI 95% cho EX tổng, 10.000 mẫu, seed bootstrap 42;
  McNemar exact ghép cặp theo câu hỏi. Seed bootstrap tách khỏi ba seed huấn luyện.
- **Scope:** mỗi lượt `evaluate` ghi scope, hash manifest Parquet và dictionary. EX trên
  store sample là EX phát triển; `echo-gold` 100% chỉ kiểm tra đường ống.

### 5.5. Chỉ số linking trực tiếp

Test v2 cần gold annotation relation/cột, target owner/address/class và ba loại property.
Dùng cùng dictionary đóng băng để chấm; không lấy SQL model sinh làm gold linking.
`evaluate-linking` chấm file dự đoán đã lưu sau khi audit annotation/review. Ghép mention
bằng text và offset, ghép property qua mention thay vì số thứ tự target. Miss và chưa phân
giải giữ trong mẫu số; mẫu số 0 trả `null`. Schema dùng recall vi mô relation@3 và column@6.
Class và tập thành viên chấm riêng; địa chỉ explicit phải khớp literal. Address-set so tập
giá trị, đồng thời có `multi_address_set` chỉ trên mention owner có hơn một địa chỉ gold;
owner một địa chỉ không bị tính sai chỉ vì baseline gọi nó là địa chỉ đại diện. Dự đoán dư được
ghi riêng trong từng case. Annotation pending hoặc split phát triển luôn được ghi là
development evaluation, không phải kết quả benchmark cuối.

| Chỉ số đích | Cách báo cáo |
|---|---|
| Schema recall | Recall relation@3 và cột@6 so với tập cần cho gold SQL; báo số mục được chấm |
| Entity resolution | Tỷ lệ mention được resolve đúng owner/address, và khớp tập địa chỉ đã biết cho multi-address; giữ lỗi/miss trong mẫu số |
| Class resolution | Tỷ lệ đúng lớp và phạm vi thành viên theo dictionary |
| Property resolution | Độ đúng riêng từng loại: gửi/nhận/cả hai, transaction/event/join, contract/endpoint; kèm số ca áp dụng |
| EX theo nhóm | Năm nhóm nhãn chính, các nhãn phụ và độ khó; kèm N và CI 95% cho từng nhóm |
| Biến thiên QLoRA | Từng seed và trung bình/độ lệch chuẩn trên cùng test; không gộp ba seed thành 300 câu độc lập |

Lưu annotation/review có hash và bổ sung bộ chấm trước thí nghiệm cuối. So sánh ghép cặp
trên cùng ID câu hỏi; báo chênh lệch EX và McNemar cho từng seed QLoRA, không chọn seed có
p nhỏ nhất. Các đối chứng/ablation nhiều phép so sánh phải công bố đầy đủ, hiệu chỉnh Holm
trong nhóm phép so sánh đã định trước. CI theo câu hỏi và biến thiên giữa seed là hai nguồn
bất định khác nhau. Nhóm 20 câu chỉ cho kết luận có độ phân giải hạn chế; ca cùng ý định
không được diễn giải thành tác vụ độc lập mới.

### 5.6. Latency, chi phí và privacy

**Hiện trạng:** evaluator có thời gian generation và execution, p50/p95 khi có dữ liệu;
linking mặc định chạy CPU; lượt T11A dựng cả ba split bằng encoder pin trên GPU local.
T10 ghi runtime từng phiên train/generate, số dòng giữ/bỏ, token và peak
GPU memory theo seed, gồm tải model, reset peak giữa các lượt và lưu phần cứng. Chưa có
báo cáo chi phí hay latency đầu cuối hoàn chỉnh cho thí nghiệm nghiên cứu. T11A đã ghi
latency generation, runtime phiên và allocated/reserved memory thật trên 2×T4; SQL model
đều dừng trước execution nên không có mẫu execution latency hợp lệ của prediction.

**Thiết kế đích, cần bổ sung đo/tổng hợp:**

- **Latency:** tách linking, retrieval/dựng prompt, generation, validator/chuyển SQL và
  execution; đo cả đầu cuối. Ghi phần cứng, batch, số token input/output, warm-up, số lần
  đo và việc dùng cache; báo p50/p95 và số mẫu đo. Latency DuckDB không đại diện BigQuery.
- **Chi phí:** tách train theo seed với inference theo câu; ghi GPU-giờ, CPU/thời gian query,
  peak memory, token và chi phí BigQuery trích/bổ sung dữ liệu riêng. Nếu có quy đổi tiền,
  ghi đơn giá/nguồn/ngày; quota miễn phí không làm lượng tài nguyên tiêu thụ bằng 0.
- **Privacy:** mô tả câu hỏi, schema, ví dụ retrieval, hints và dữ liệu kết quả đi qua đâu.
  Luồng Kaggle hiện có nhận prompt và sinh SQL trên cloud, còn thực thi kết quả ở DuckDB
  local. Không gọi luồng này là inference cục bộ hoặc khẳng định không gửi câu hỏi ra ngoài.
  Self-hosted/on-prem là khả năng triển khai cần kiểm chứng riêng; chưa có thí nghiệm đo
  rò rỉ riêng tư. Không có đối chứng API bên ngoài trong ma trận bắt buộc.

## 6. Khả năng tái lập, giới hạn và khoảng cách triển khai

### 6.1. Provenance và tái lập

Repo là bản tinh gọn của [luanvan](https://github.com/vovi102/luanvan), nhập từ commit
`0ed5cd1`; nguồn và SHA-256 nằm trong [manifest nhập](data/import-manifest.json). Kế thừa
Stage A v2, Test-100, catalog, managed layer và thuật toán linking. Khi nhập, catalog bỏ
`input` và bổ sung mô tả hai relation labeled đã có trong allowlist. Phần test chung giữ
SQL của 50 câu, phủ 29 intent; diễn đạt `t35-051`, `t35-096`, `t35-100` đã được sửa cho khớp SQL.

Lịch sử pivot SPARQL/Fuseki sang SQL được giữ là bối cảnh, không phải đóng góp hoặc đối chứng
của nghiên cứu mới. B0, nhánh tiếng Việt, campaign runner và các approval gate cũ không nằm
trong repo tinh gọn. Kết quả không so trực tiếp với campaign c03 vì test, trích SQL và backend
đã đổi. Bộ CSV local có [manifest riêng](data/raw/luanvan/import-manifest.json) và
[báo cáo chất lượng](reports/data-quality/luanvan.md).

Mỗi lượt nghiên cứu cần lưu phiên bản code/model/config, seed, hash dataset/review/dictionary/
store, prompt và ID ví dụ retrieval, checkpoint, output thô và lỗi. Hiện đã có pin model,
hash prompt/config/store và artifact kiểm dữ liệu; test v2 và annotation trực tiếp ở trạng thái
draft T09A. T10 đã có đối chứng compact và tổng hợp đa seed; T11A đã chạy hai compact base
control trên dữ liệu phát triển. Ma trận QLoRA/five-shot/ablation vẫn chưa chạy LLM.
Báo cáo hiện hành giữ bằng chứng còn sử dụng theo [quy tắc artifact](reports/README.md);
thời điểm/hash của lần chạy gốc không tự xác nhận source hiện tại.

T10 lưu artifact trong `runs/<config>/seed-<seed>/`, dùng chung SFT/prompt ở thư mục config.
Resume train/generate kiểm hash prompt/model/adapter, config, siêu tham số và seed; checkpoint
được kiểm cả state/optimizer/RNG. Generation kiểm provenance ngay cả khi không còn câu cần
sinh. Báo cáo giữ kết quả từng seed, mean/SD mẫu (ddof=1), số seed còn thiếu và N câu dùng
chung; không gộp prediction thành 3N câu độc lập. Chi tiết lệnh, artifact và giới hạn đo
tài nguyên khi phiên bị ngắt ở [T10](reports/experiments/WORKFLOW.md). Gate test draft giữ nguyên.

Hai base control giữ prediction/evaluation/manifest và [bằng chứng resume](reports/experiments/base-controls/summary.json)
giữ nguyên từng byte của 10 dòng đầu. ZIP và bản sao trung gian đã xóa sau kiểm hash.
Preflight thật dùng context 8.192 token từ model config; hint lớp dùng predicate và số owner,
không liệt kê hàng nghìn tên. Full membership linking và SQL target giữ nguyên. Sau sửa,
cả b3/b3l giữ đủ 4.872 train và 516 dev ở giới hạn 1.024 token. Test v2 không thay đổi.

### 6.2. Giới hạn cần giữ khi diễn giải

- **Sample và parity:** store hiện tại không đại diện toàn mạng; snapshot đầy đủ và parity
  chưa hoàn tất. Fixture v1 không xác nhận dictionary/test v2; hợp đồng ngoài cửa sổ có thể
  khác BigQuery. Phạm vi dữ liệu và nhãn phải đi cùng mọi kết quả.
- **Kiểu số:** `BIGNUMERIC` chưa có kiểu tương đương chính xác trong bản sao; `value_bignumeric`
  dùng HUGEINT, `normalized_amount` dùng DOUBLE, tổng có thể lệch chữ số cuối. Chứng minh
  parity từng truy vấn không loại bỏ mọi sai khác dialect/kiểu số.
- **Nhãn:** dictionary là tập tuyển chọn, chưa có khoảng valid_from/valid_to; xác minh sau
  tháng 6 không chứng minh sở hữu tháng 6. Báo cáo phát triển v1 quan sát router Tornado Cash;
  các ca token-event trên endpoint/class mixer v2 của T09A còn rỗng trên sample, chưa xác
  nhận coverage hoặc nhiều pool cùng hoạt động trên snapshot đầy đủ.
- **Benchmark:** train/dev chủ yếu là câu renderer; dùng chung template/owner giữa các split.
  Test hiện tại đã được xem, human review chưa hoàn tất. Test v2 cân bằng là chẩn đoán trên
  schema/dictionary đã biết, không đại diện phân bố câu hỏi thực tế hoặc toàn bộ nghiệp vụ AML.
- **Ngữ nghĩa:** resolver ba property dùng cue, có thể sai hoặc chưa phân giải; chưa có hỏi lại. Không
  diễn giải token-event count thành transaction count, dòng tiền ghi trong transaction
  thành thay đổi số dư hoặc số token normalized thành giá trị tiền.
- **Thực nghiệm:** T11A chỉ kiểm chứng hạ tầng trên 100 câu phát triển/config; hai base
  control đều EX=0 do lỗi validator/compiler. T11B đã train b3/42; smoke gốc 7/10 compile,
  EX 0/10. Can thiệp prompt trên adapter đóng băng đạt EX 19/100 phát triển nhưng
  chưa ổn định, nên vẫn dừng mở rộng. Chưa có QLoRA ba seed hoặc kết quả test frozen.
  Accuracy, tốc độ, chi phí hay privacy tốt hơn vẫn là câu hỏi cần kiểm chứng.

### 6.3. Khoảng cách triển khai

| Hạng mục | Hiện trạng có bằng chứng | Việc cần làm cho thiết kế đích |
|---|---|---|
| Blockchain và DuckDB | [Store sample đã dựng](reports/local-store/README.md) | Hoàn tất snapshot/parity; đóng băng scope và kiểm gold v2 trên store nghiên cứu |
| Dictionary | [V2 và coverage đã có](reports/dictionary-v2/README.md) | Đóng băng phiên bản cho benchmark, giữ giới hạn lịch sử/độ phủ |
| Dataset | [Train/dev và 100 câu phát triển đã kiểm](reports/dataset/README.md); [100 câu v2 draft T09A](reports/benchmark/README.md) | T09B: kiểm gold/witness/ca rỗng trên full snapshot sau T06, hoàn tất human review và gate đóng băng |
| Linking | Resolver ba property, output T07 và bộ chấm trực tiếp đã có; [đánh giá nháp](reports/linking/README.md) | Human review, kiểm trên test frozen và cơ chế làm rõ ngoài test SQL chính |
| Cấu hình thí nghiệm | T11A đã chạy hai compact base control; T11B đã train b3/42 và chẩn đoán prompt trên adapter đóng băng đủ 100 câu; runner ba seed và baseline/bốn ablation đã có | Tiếp tục sửa lỗi trên phát triển trước khi mở rộng; thí nghiệm test sau đóng băng |
| Báo cáo | [Evaluator](src/eth_nl2sql/evaluate.py), [RESULTS phát triển](RESULTS.md), [artifact/tài nguyên T11A](reports/experiments/README.md) | Chạy ma trận sau đóng băng; CI theo nhóm, latency đầu cuối và chi phí/privacy; tổng hợp seed đã có ở T10 |

T11A đã có hai compact base control; T11B có pilot B1, lượt train b3/42 với output
smoke gốc 10 câu và chẩn đoán prompt riêng đủ 100 câu. Các lượt còn lại và ma trận
test frozen chưa thực hiện. README mặc định
vận hành trên `dev_eval`;
T07 đã có lệnh kiểm/đóng băng; T09A đã soạn nội dung test v2 draft. Linking baseline
và ablation đã được chấm phát triển ở chế độ lexical/fuzzy; chưa chạy generator five-shot
cho các baseline/ablation đó.

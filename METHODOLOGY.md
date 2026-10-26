# Phương pháp

Tài liệu này mô tả cách dữ liệu được tạo, linking, các cấu hình model và cách đánh giá. Chi tiết
nào chưa thực hiện đều được ghi rõ là chưa thực hiện.

## 1. Dữ liệu nguồn và bản sao cục bộ

- **Nguồn:** `bigquery-public-data.crypto_ethereum`. Lấy các bảng `transactions` (bỏ cột `input`),
  `blocks`, `token_transfers` trong cửa sổ [2026-05-31, 2026-07-01); `contracts` chỉ lấy các địa chỉ
  xuất hiện trong cửa sổ; `amended_tokens` lấy toàn bộ.
- **Store phát triển từ CSV cũ (T03):** giữ bộ giao dịch đã lọc/lấy mẫu của LuanVan, khôi phục
  block hash/number bằng join đã kiểm tra, lấy các thuộc tính còn thiếu từ BigQuery. Contract
  bổ sung bao gồm các token address quan sát được trong token transfer; cờ ERC của contract
  lịch sử trong CSV được giữ nguyên. `prepare-local` không tạo giá trị giả cho cột thiếu.
  Manifest Parquet ghi checksum, số dòng, mapping và provenance job bổ sung; DuckDB lưu scope
  cùng hash manifest/dictionary. Store này dùng cho phát triển; đủ ngày/cột không có nghĩa là
  đủ giao dịch toàn mạng. `parity` yêu cầu manifest của snapshot đầy đủ, nên chưa áp dụng cho
  store lấy mẫu. Chi tiết tại `reports/local-store/README.md`.
- **Managed layer:** 8 object kế thừa từ luanvan (`sql/label_layer.py`): view `entity_labels_v1`,
  `token_dimension` và các table function `transaction_facts`, `block_facts`, `contract_dimension`,
  `token_transfer_facts`, `labeled_transactions`, `labeled_token_transfers`. Bản sao DuckDB định
  nghĩa lại chúng bằng view và table macro có cùng cột và cùng tham số
  (`src/eth_nl2sql/store/build.py`).
- **Thực thi:** SQL do model sinh ra (GoogleSQL) được viết lại tên relation rồi chuyển sang DuckDB
  bằng SQLGlot. Tham số ngày của table function được tính trước khi chạy, áp đúng luật của
  BigQuery: start < end, tối đa 31 ngày, kiểu DATE. Cửa sổ nằm ngoài snapshot bị gắn nhãn
  `window_outside_snapshot`, không âm thầm trả về rỗng. Session dùng múi giờ UTC.
- **Vì sao không chạy BigQuery mỗi lần:** ở luanvan, 88 câu gold đã quét khoảng 420 GiB. Một ma trận
  6 cấu hình × 100 câu sẽ vượt free tier 1 TiB/tháng nhiều lần.
- **Parity:** `eth-nl2sql parity` (store dựng với dictionary v1) so row digest của từng câu gold với
  88 kết quả BigQuery thật trong campaign c03 của luanvan. Hàm digest khớp từng byte với luanvan;
  test vector nằm trong `tests/test_results.py`. Lệnh này cũng so số dòng của 206 truy vấn witness
  Stage A. Ngưỡng chấp nhận: ≥95% gold khớp, mọi chỗ lệch phải được giải thích. *Chưa chạy.*
- **Giới hạn đã biết:**
  - BigQuery `BIGNUMERIC` không có kiểu tương đương chính xác: `value_bignumeric` dùng HUGEINT,
    `normalized_amount` dùng DOUBLE, nên tổng normalized amount có thể lệch ở chữ số cuối.
  - Truy vấn hỏi hợp đồng không xuất hiện trong cửa sổ sẽ khác BigQuery.

## 2. Dataset

| Phần | Nguồn | Số lượng |
|---|---|---|
| Train/dev chung | Stage A v2 của luanvan (1.000 SQL đã kiểm bằng BigQuery), mỗi SQL có 4 câu tiếng Anh do renderer tất định sinh (formal, conversational, abbreviated, alternative) | 3.604 / 396 câu (901 / 99 SQL), split theo family |
| Test chung | Test-100 của luanvan, giữ đủ 29 intent; thêm một tuần thứ hai cho 21 intent lặp nhiều nhất | 50 |
| Train/dev thực thể (T05) | 10 template owner/owner-pair/token/class/address; 347 family SQL × 4 cách diễn đạt, có alias; hash seed 42, tối thiểu một family dev mỗi template | 1.268 / 120 câu (317 / 30 SQL) |
| Test thực thể (T05) | 50 câu soạn riêng, gắn nhiều nhãn `multi_address`, `alias`, `class_level`, `ambiguous_property`; đã review bằng agent, chờ người review xác nhận | 50 |

- Test-100 của luanvan không có câu nào nhắc tên thực thể, nên không đo được đóng góp 2. Đó là lý do
  phải thêm phần test thực thể.
- Tổng train/dev hiện tại là **4.872 / 516** câu; test **100 = 50 chung + 50 thực thể**.
  Dữ liệu chung được giữ nguyên, trừ cách diễn đạt của `t35-051`, `t35-096`, `t35-100` được sửa
  để khớp SQL; SQL của 50 câu chung không đổi, vẫn đủ 29 intent.
- **Leakage** (`data/leakage.py`, `data/entities.py`): không trùng câu chuẩn hoá, SQL chuẩn hoá
  hoặc family giữa các split; train/dev không chung n-gram 12 token với test. Generator loại
  cả family nếu một cách diễn đạt trùng test. Các đoạn văn mẫu 12 token chung giữa train/dev
  vẫn được báo cáo riêng; đây là split theo family SQL, không phải split theo từ vựng/template
  hoặc owner chưa từng thấy. Không tuyên bố train/dev sạch mọi n-gram.
- **Kiểm chéo gold T05:** `check-dataset` chạy mọi SQL phân biệt của cả ba split trên DuckDB
  thực tế, ghi số dòng, digest, lỗi, kết quả rỗng và aggregate 0/NULL riêng. Kết quả rỗng hợp lệ
  được giữ cùng giải thích, không bị loại để tăng EX. Các count của test thực thể được đối
  chiếu bằng raw-table oracle; 34 ca nhiều địa chỉ kiểm đúng fact, chiều và cửa sổ, chứng minh
  một địa chỉ đơn lẻ cho count nhỏ hơn gold. Tornado Cash chỉ kiểm router/service alias hoặc
  token TORN; không được tính là chứng cứ nhiều pool hoạt động.
- **Review ngữ nghĩa:** `data/test-review.json` có ghi chú cho đủ 100 cặp câu hỏi–SQL cùng hash
  câu/SQL, nên chỉnh sửa làm review hết hiệu lực. Agent đã review ngày 26/10/2026; xác nhận
  của người review còn chờ. Đây chưa phải hoàn tất yêu cầu có người review của đề cương.
  Artifact, cách sinh lại và giới hạn local nằm trong `reports/entity-dataset/README.md`.

## 3. Linking

Ba thành phần, port từ luanvan, giữ nguyên thuật toán và ngưỡng:

- **Schema linker:** điểm = 0,65 × cosine (MiniLM `all-MiniLM-L6-v2`, revision pin trong
  `configs/experiment.toml`) + 0,35 × độ trùng từ, có mở rộng bằng synonym. Trả về 3 relation và
  6 cột đứng đầu.
- **Entity linker:** chuỗi bước address regex → alias khớp chính xác → khớp mờ (≥0,85) →
  embedding (≥0,75). Biên nhập nhằng 0,03. Tên token là danh từ riêng: khớp xấp xỉ chỉ chấp nhận
  khi cụm từ có chữ hoa, tránh "ten token" thành "WEN Token".
- **Resolver**, xử lý bốn đặc thù:
  - *Nhiều địa chỉ:* target owner gom mọi địa chỉ của thực thể. Prompt hướng model lọc
    `entity_labels_v1.owner`, không liệt kê từng địa chỉ.
  - *Alias:* bước khớp ánh xạ alias về owner chuẩn.
  - *Theo lớp:* "any/all/every/major X" hoặc dạng số nhiều được giải về `concept_class`.
  - *Property nhập nhằng:* chiều from/to lấy từ từ chỉ chiều trong 40 ký tự trước mention, nếu
    không có thì lấy từ schema linker, cuối cùng để là "unspecified".
- **Dictionary v1** (luanvan) có 5.135 entry, nhưng 5.078 là token. 57 thực thể còn lại mỗi thực thể
  chỉ có đúng 1 địa chỉ; Tornado Cash chỉ là token TORN.
- **Dictionary v2 (T04):** 6.647 địa chỉ, giữ mọi địa chỉ v1; 47 owner ngoài token, trong đó
  40 owner có nhiều địa chỉ. Nguồn ghi URL, revision và vị trí trong tài liệu; nguồn vừa đối
  chiếu ghi ngày 26/10/2026, nhãn kế thừa giữ ngày xác minh cũ. Hai API công bố ví Binance/
  Bitstamp có snapshot JSON và SHA-256. Manifest ghi hash các file và các thay đổi phân loại.
  TORN và token quản trị được tách khỏi owner hoạt động; Tornado Cash có 19 pool và một router,
  thuộc `MixerAccount`. Alias trùng có danh sách owner, ví dụ `uniswap` nhập nhằng giữa V2/V3/V4.
  Validator kiểm địa chỉ duy nhất, chain, nguồn/ngày, graph owner–alias–nhóm và checksum trước
  khi tải. `build-store` và `link` mặc định dùng v2; parity vẫn yêu cầu v1.
- **Hiện diện dictionary:** `dictionary-coverage` join v2 trực tiếp với raw tables local,
  đếm theo địa chỉ/owner/nhóm và vai trò from/to/token, giữ cả địa chỉ có số đếm 0. Một dòng
  chỉ được đếm một lần cho mỗi owner/nhóm dù có nhiều địa chỉ khớp. Metadata presence được
  ghi riêng với hoạt động. Cửa sổ là [2026-05-31, 2026-07-01); store T03 lấy mẫu nên số đếm
  không đại diện toàn mạng. Nguồn xác minh sau cửa sổ dữ liệu không chứng minh khoảng sở hữu
  lịch sử. Xem `reports/dictionary-v2/coverage.md` và tài liệu dictionary để biết giới hạn.

## 4. Cấu hình model

Tất cả dùng `meta-llama/Meta-Llama-3-8B-Instruct` (revision pin), NF4 4-bit, compute float16 (vì T4
không hỗ trợ bf16), decoding greedy, tối đa 512 token, dừng ở `<|eot_id|>`.

| Config | Ngữ cảnh trong prompt | Ghi chú |
|---|---|---|
| `b1` / `b1l` | catalog đầy đủ (tên relation đầy đủ + cú pháp gọi) [+ linking] | zero-shot |
| `b2` / `b2l` | + 5 ví dụ retrieval từ train (cosine MiniLM, loại cùng family) [+ linking] | five-shot |
| `b3` / `b3l` | chỉ chữ ký 8 relation [+ linking] | QLoRA |

- QLoRA: r=16, α=32, dropout 0,05, các module q/k/v/o, lr 2e-4 cosine, batch hiệu dụng 16, tối đa
  2 epoch, early stopping theo dev loss. Loss chỉ tính trên token SQL; dòng dài hơn 1.024 token bị
  bỏ và có đếm số dòng bị bỏ.
- Mỗi cấu hình chạy một lượt, vì greedy là tất định (luanvan đo 3 lượt, giống hệt 100/100).
- Thiết kế prompt chỉ được chỉnh trên dev, không nhìn test.

## 5. Đánh giá

- **Trích SQL** (lenient): lấy khối fence đầu tiên hoặc dòng đầu bắt đầu bằng SELECT/WITH; bỏ dấu
  `;` và prose ở cuối. `format_ok` ghi lại output có đúng chỉ một câu SQL hay không; chỉ số này được
  báo cáo riêng.
- **Thứ tự kiểm:** an toàn (một câu read-only, không comment/`;`, không `SELECT *`, chỉ 8 relation
  trong allowlist) → cửa sổ ngày → biên dịch/thực thi DuckDB (timeout 120 s).
- **EX (chỉ số chính):** so dòng kết quả đã chuẩn hoá theo kiểu. Số so theo giá trị (float làm tròn
  12 chữ số có nghĩa), timestamp quy về UTC. So như dãy nếu gold có `ORDER BY` ở cấp ngoài cùng,
  ngược lại so như multiset; không so tên cột. Mọi lỗi đều giữ trong mẫu số.
- Mỗi kết quả `evaluate` kèm scope, hash manifest Parquet và hash dictionary của store. Kết quả
  trên store lấy mẫu là kết quả phát triển, chưa tương đương đánh giá trên snapshot đầy đủ.
- **Chỉ số phụ:** tỷ lệ SQL hợp lệ, EM và structural match (canonical SQLGlot), answer F1, EX tách
  theo nhóm chung/thực thể, theo từng đặc thù và theo độ khó.
- **Thống kê:** bootstrap 95% CI (10.000 mẫu, seed 42); McNemar exact cho các cặp có/không linking
  và cho fine-tune so với prompting.
- **Latency:** sinh SQL (đo trên T4, từng câu), linking (CPU) và thực thi (DuckDB cục bộ, không phải
  latency của BigQuery).
- **Cost:** số GPU-giờ Kaggle.
- **Privacy:** inference chạy cục bộ, không gửi câu hỏi ra ngoài. So sánh với LLM lớn qua API là tuỳ
  chọn và chỉ chạy khi được đồng ý.

## 6. Quan hệ với luanvan

- **Giữ:** pivot sang SQL (Plan A SPARQL/Fuseki mất 34–38 s/query, là negative result), Stage A v2,
  test-100, catalog, managed layer, thuật toán linking.
- **Nhập từ commit `0ed5cd1`** (nguồn và SHA-256 trong `data/import-manifest.json`):
  - catalog: bỏ cột `input`; bổ sung mô tả `labeled_transactions`, `labeled_token_transfers`, hai
    relation có trong allowlist nhưng thiếu trong catalog gốc;
  - train/dev và test chung: lấy như mô tả ở mục 2;
  - fixture parity: lấy từ `evidence.json` của campaign c03 và Stage A v2.
- **Bỏ:** B0, nhánh tiếng Việt, Kaggle bundle/campaign runner, journal và các approval gate.
- **Khác:** kết quả không so trực tiếp với campaign c03 của luanvan, vì test set, bước trích SQL và
  backend thực thi đều đã đổi.

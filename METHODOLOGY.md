# Phương pháp

Tài liệu này mô tả cách dữ liệu được tạo, linking, các cấu hình model và cách đánh giá. Chi tiết
nào chưa thực hiện đều được ghi rõ là chưa thực hiện.

## 1. Dữ liệu nguồn và bản sao cục bộ

- **Nguồn:** `bigquery-public-data.crypto_ethereum`. Lấy các bảng `transactions` (bỏ cột `input`),
  `blocks`, `token_transfers` trong cửa sổ [2026-05-31, 2026-07-01); `contracts` chỉ lấy các địa chỉ
  xuất hiện trong cửa sổ; `amended_tokens` lấy toàn bộ.
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
| Train thực thể | ~10 template mới (dòng tiền theo owner, giữa hai owner, theo lớp…), alias được chèn vào câu | *chưa tạo* |
| Test thực thể | 50 câu viết tay, gắn nhãn `multi_address`, `alias`, `class_level`, `ambiguous_property`; gold phải chạy được trên store; có người review | *chưa tạo* |

- Test-100 của luanvan không có câu nào nhắc tên thực thể, nên không đo được đóng góp 2. Đó là lý do
  phải thêm phần test thực thể.
- **Leakage** (`data/leakage.py`): câu train bị loại nếu trùng câu test sau khi chuẩn hoá, hoặc
  chung một n-gram 12 token với câu test. Kiểm trong `tests/test_data.py`.
- **"Cross-validation" trong đề cương** được hiểu là kiểm chéo gold: chạy được trên store, kết quả
  khác rỗng, và có người review.

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
- **Dictionary v2** dự kiến khoảng 40–60 thực thể có nhiều địa chỉ, ghi nguồn cho từng địa chỉ.
  *Chưa tạo.*

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

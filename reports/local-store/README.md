# Store phát triển và snapshot còn chờ

Store hiện tại `data/store/eth.duckdb` dùng **dictionary v2, 6.647 địa chỉ**,
được dựng từ CSV kế thừa và dữ liệu bổ sung BigQuery. Kiểm local ngày 30/10/2026
xác nhận store có `complete_snapshot=false`, scope
`labeled_address_transactions_plus_approximately_one_percent_of_other_transactions`.
Cửa sổ UTC là `[2026-05-31, 2026-07-01)`.

| Bảng | Số dòng nguồn Parquet |
|---|---:|
| transactions | 4.431.329 |
| blocks | 221.548 |
| token_transfers | 4.001.230 |
| contracts | 16.386 |
| amended_tokens | 2.489.651 |

[Manifest Parquet](parquet-manifest.json) giữ nguồn, scope và checksum của năm
bảng. [Provenance bổ sung](supplements.json) giữ query/input hash, checksum và
job ID. Các cột transaction index, receipt gas used, contract receipt, block
base fee và metadata token được bổ sung từ nguồn thật, không suy đoán.

Nguồn giữ 2.110 khác biệt cờ ERC của contract lịch sử; 1.290.700 token transfer
có normalized_amount. Không suy đoán metadata cho phần còn thiếu. Coverage
sample không đại diện toàn mạng. [Kiểm store/dictionary v2](../dictionary-v2/validation.json)
và [kiểm gold hiện hành](../dataset/validation.md) thay báo cáo store v1 cũ.
[Gold-echo](../../runs/gold-echo/eval-dev_eval.json) đạt 100/100 chỉ kiểm đường ống,
không chứng minh accuracy model hay parity BigQuery.

## Chuẩn bị dữ liệu local

```bash
uv run --locked eth-nl2sql check-data
uv run --locked eth-nl2sql local-plan
uv run --locked eth-nl2sql prepare-local --parquet data/store/new-parquet
uv run --locked eth-nl2sql build-store --parquet data/store/new-parquet   --labels data/entities/v2 --store data/store/new.duckdb
```

`supplement-plan` và `supplement-run` dùng extra `bq` cùng ADC local khi cần tải
phần bổ sung. Manifest hiện có cho phép dùng lại dữ liệu đúng query/input hash.
Không ghi credential vào repo. Không dựng đè store đang dùng cho kết quả đã chấm.

## Snapshot đầy đủ và parity — chưa hoàn tất

Theo yêu cầu hoãn ngày 27/10/2026, chưa chạy extraction snapshot đầy đủ hoặc
kiểm parity thật; không tự chạy khi quota được cấp lại. Yêu cầu dùng miễn phí,
không gắn billing vẫn áp dụng. Những số quota và dry-run cũ đã bỏ vì không mô tả
trạng thái hiện tại; khi tiếp tục phải kiểm lại quota và dry-run.

Khi được phép tiếp tục:

1. Kiểm trạng thái billing/quota và dry-run đủ 95 partition cho cửa sổ UTC.
2. Trích dữ liệu với cap bytes, provenance/checksum và resume theo job ID; kiểm
   manifest/resume trên dữ liệu thật, không suy từ fixture offline thành đạt.
3. Dựng full store nhãn v1 để parity 88 gold BigQuery và 206 witness kế thừa.
4. Dựng full store nhãn v2; kiểm gold, coverage và witness của benchmark draft,
   kể cả ca rỗng/join/property. Hoàn tất human review và gate trước đóng băng.

```bash
eth-nl2sql snapshot-plan --project P
eth-nl2sql snapshot-run --project P --parquet data/store/full-parquet
eth-nl2sql build-store --parquet data/store/full-parquet   --store data/store/full-v1.duckdb --labels data/entities/v1
eth-nl2sql parity --store data/store/full-v1.duckdb
```

Các lệnh snapshot mặc định ghi kết quả mới vào `reports/local-store/snapshot/`.
Không giữ bản archive của lần trước. Sample hiện tại không đáp ứng gate phát hành.

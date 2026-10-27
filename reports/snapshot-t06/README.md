# T06 — Snapshot Ethereum và parity BigQuery

Ngày kiểm tra: **27/10/2026**. **Mốc chuẩn bị đã hoàn tất; kiểm nghiệm trên snapshot đầy đủ được hoãn theo yêu cầu người dùng. T06 chưa hoàn tất.**

## Ghi chú hoãn kiểm nghiệm — 27/10/2026

Người dùng yêu cầu ghi lại phần kiểm nghiệm để thực hiện sau. Các việc còn chờ gồm kiểm chứng
manifest/resume trên dữ liệu thật, parity BigQuery với dictionary v1 và kiểm gold/coverage của
store v2 trên snapshot đầy đủ. Mốc chuẩn bị và báo cáo dry-run được giữ nguyên; các kiểm nghiệm
trên dữ liệu thật vẫn chưa được thực hiện, chưa được tính là đạt.

Chưa đặt lịch chạy lại. Khi quay lại T06, kiểm tra quota miễn phí, trích đủ dữ liệu rồi thực hiện
các bước bên dưới. Quota được cấp lại không tự kích hoạt trích dữ liệu hoặc kiểm nghiệm.

Người dùng yêu cầu dùng miễn phí, không gắn billing. Project `nl2sparql-thesis` hiện có
`billingEnabled=false` và không có billing account. T06 chỉ đọc trạng thái billing, lịch sử
job và dry-run; **chưa gửi query trích dữ liệu, bytes billed phát sinh cho T06 = 0**.

## Dry-run và điểm chặn

[Dry-run JSON](dry-run.json) ghi đủ SQL, SHA-256 và ước lượng của **95 partition**:
31 ngày × transactions/blocks/token_transfers, contracts/referenced và amended_tokens/all.
Cửa sổ UTC là `[2026-05-31, 2026-07-01)`. Tổng scan ước lượng **214,44 GiB**;
query lớn nhất **33,04 GiB**, dưới trần **50 GiB/query**. Xem bảng tại [dry-run.md](dry-run.md).
Ước lượng có thể đổi theo dữ liệu nguồn; `snapshot-run` luôn dry-run lại trước khi gửi SQL.
`passed=true` của dry-run chỉ xác nhận kế hoạch SQL dưới trần bytes đã cung cấp, không xác
nhận còn quota miễn phí hoặc dữ liệu đã được tải.

[Kiểm tra sandbox](sandbox-status.json) đọc lịch sử job của mọi user trong project từ đầu
tháng UTC: tổng `total_bytes_billed` là **1.807,831 GiB**. Đây là số byte theo metadata job,
không phải số tiền đã thanh toán hoặc số dư quota chính thức. Bộ kiểm dùng tổng này làm
ước lượng bảo thủ và tính allowance còn lại là **0** so với giới hạn miễn phí **1 TiB/tháng**.
Lịch sử còn có lỗi thực tế ngày 24/10/2026, job
`nl2sql_eval_56580e5a63addf43cecb6df6fcbacd67dd24c262`, reason `quotaExceeded`, location
`unbilled.analysis`: “Your project exceeded quota for free query bytes scanned.”

Lệnh chạy thật dừng ở preflight, exit 1; [extraction.json](extraction.json) lưu nguyên nhân.
Chưa có manifest snapshot đầy đủ hoặc hai store đích. Không lấy kết quả sample của T03–T05
làm kết quả T06. Các gate manifest, parity, gold v2 và coverage v2 đang chờ dữ liệu.
Trạng thái máy đọc được nằm trong [status.json](status.json).

Nguồn chính thức: [BigQuery sandbox và giới hạn miễn phí](https://cloud.google.com/bigquery/docs/sandbox),
[dry-run và maximum bytes billed](https://cloud.google.com/bigquery/docs/best-practices-costs),
[Arrow iterator](https://cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.table.RowIterator).

## Phần chuẩn bị đã triển khai

- Tải theo Arrow record batch, ghi Parquet Zstandard theo luồng. REST mặc định với page size
  50.000; tùy chọn Storage API giới hạn hai stream và hai batch trong queue. Đóng writer/client
  kể cả khi lỗi; chỉ công bố file sau khi số dòng khớp `total_rows` của BigQuery.
- Journal lưu job ID do client cấp **trước RPC submit**, SQL/hash, project/location, cap,
  bytes processed/billed và số dòng nguồn. Poll/tải bị gián đoạn thì lấy lại cùng job, tắt
  cơ chế tự tạo job thay thế của SDK. Journal và manifest ghi atomically với fsync.
- Resume kiểm checksum, số dòng, schema và binding mọi file trước khi liên lạc BigQuery.
  Đủ 95 file hợp lệ thì resume hoàn toàn offline. Có khóa thư mục chống hai extractor cùng ghi.
  Gián đoạn giữa rename file và commit manifest được phục hồi từ record tải đã ghi trước đó.
- Không tự tăng ngân sách khi resume. Mỗi query mới có server cap không quá 50 GiB, ngân sách
  snapshot còn lại và allowance miễn phí còn lại. Preflight từ chối billing đang gắn, trạng
  thái billing không xác minh được, quota thiếu hoặc query quá trần. ADC thiếu quyền đọc
  Cloud Billing có thể dùng đăng nhập gcloud hiện có để đọc trạng thái cùng project.
- Job đã ghi nhận mà server không còn giữ, hoặc reservation chưa submit quá một ngày nhưng
  không tìm thấy trên server, bị từ chối tự chạy lại. Job lỗi/expired cần xử lý minh bạch;
  extractor không tự thay bằng query mới và che chi phí của lần trước.
- `snapshot-validate` kiểm đủ 95 partition, provenance, checksum, số dòng, kiểu dữ liệu, ngày
  UTC, khóa, join transaction–block/transfer–transaction và transaction count từng block.
- Parity yêu cầu dictionary v1 đúng SHA-256. Gate yêu cầu ≥95% gold exact **và tất cả sai khác
  gold/witness có giải thích**, gắn với hash quan sát. Fixture hash và profile store có trong báo cáo.
- Coverage v2 có gate so với baseline T04: đúng dictionary/cửa sổ, store đầy đủ, labels khớp;
  không mất số hoạt động ở từng địa chỉ, owner và category. Không ép owner vốn không hoạt động
  phải có hoạt động và không tuyên bố coverage ownership toàn mạng.

**203 test pass, Ruff sạch.** Kết quả ghi tại [checks.json](checks.json);
[tests.xml](tests.xml) là kết quả pytest.
Các phép thử tải/resume dùng BigQuery giả lập; dry-run và kiểm billing/quota dùng dịch vụ thật.

## Hướng dẫn thực hiện sau khi quay lại T06

Chạy từ thư mục gốc repo. `snapshot-run` đọc lại billing và lịch sử tháng hiện tại, rồi tự
chọn trần tổng không vượt allowance miễn phí được kiểm. Nếu chưa đủ quota, lệnh tiếp tục
dừng trước khi gửi SQL. Chỉ dùng hướng dẫn này khi quay lại công việc đã hoãn và có đủ quota;
không cần gắn billing.

```bash
uv sync --locked --extra bq
uv run --locked eth-nl2sql snapshot-plan --project nl2sparql-thesis --budget-bytes 1099511627776
uv run --locked eth-nl2sql snapshot-run --project nl2sparql-thesis
uv run --locked eth-nl2sql snapshot-validate
uv run --locked eth-nl2sql build-store --parquet data/store/full-parquet --store data/store/full-v1.duckdb --labels data/entities/v1
uv run --locked eth-nl2sql build-store --parquet data/store/full-parquet --store data/store/full-v2.duckdb --labels data/entities/v2
uv run --locked eth-nl2sql parity --store data/store/full-v1.duckdb --out reports/snapshot-t06/parity.json
uv run --locked eth-nl2sql check-dataset --store data/store/full-v2.duckdb --out reports/snapshot-t06/gold-v2.json --report reports/snapshot-t06/gold-v2.md
uv run --locked eth-nl2sql dictionary-coverage --store data/store/full-v2.duckdb --baseline reports/dictionary-v2/coverage.json --out reports/snapshot-t06/coverage-v2.json --report reports/snapshot-t06/coverage-v2.md
```

Chỉ tiếp tục bước sau khi bước trước thành công. Parity đối chiếu **88 gold** và **206 witness**
đã ghi nhận từ BigQuery; không gửi thêm query BigQuery. Hai store dùng cùng manifest raw,
khác SHA-256 dictionary. Store v2 phải vượt `check-dataset` trên toàn bộ train/dev/test,
bao gồm oracle raw-table cho test thực thể; coverage phải có `coverage_gate.passed=true`.

Nếu parity có sai khác, điều tra từng SQL rồi tạo file JSON có key `gold:<sql_sha256>` hoặc
`witness:<id>`. Mỗi entry cần `reason`, `evidence` và `observed_sha256` đúng giá trị được xuất
trong báo cáo parity. Chạy lại với `--explanations PATH`; không sửa fixture để làm gate đạt.
Sai khác số học hoặc nguồn dữ liệu chỉ là giả thuyết cho tới khi có bằng chứng cụ thể.

Không đổi dataset/test review để che lỗi khi chuyển từ sample sang full. Các kết quả rỗng,
support multi-address và property witnesses phải được kiểm lại trên dữ liệu thật.

## Tiêu chí đóng T06

| Gate | Trạng thái hiện tại |
|---|---|
| Streaming, resume, provenance, ngân sách và test | Đã chuẩn bị và kiểm thử |
| Báo cáo dry-run 95 partition | Đã xuất |
| Trích đủ 95 partition trong ngân sách miễn phí | Chưa thực hiện; quota chặn |
| Manifest/resume được kiểm chứng trên dữ liệu thật | Hoãn theo yêu cầu; chưa có snapshot đầy đủ |
| Parity ≥95%, giải thích mọi sai khác | Hoãn theo yêu cầu; chưa chạy trên store đầy đủ |
| Store v2 vượt gold và coverage | Kiểm nghiệm hoãn theo yêu cầu; chưa dựng từ snapshot đầy đủ |

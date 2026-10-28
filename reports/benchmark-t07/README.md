# T07 — Hạ tầng benchmark v2 và annotation

Ngày kiểm: **27/10/2026**. T07 đã tách bộ đánh giá phát triển khỏi test cuối và thêm schema,
annotation, kiểm hash/leakage/review cùng quy trình đóng băng. Nội dung 100 câu test v2 và
human review vẫn chưa hoàn thành; snapshot đầy đủ ở T06 tiếp tục chờ.

## Chuyển đổi artifact

- `data/test.jsonl` → `data/dev_eval.jsonl`, giữ nguyên 100 dòng và SHA-256
  `2e2f63071718e045d4ca24cea8aecbdaf37c7749d4f33ce3e2d687cd1173c8ee`.
- Review câu hỏi–SQL cũ chuyển sang `data/dev_eval-review.json`, không nâng trạng thái human.
- Gold-echo đổi hậu tố `test` → `dev_eval`, chạy lại đủ 100 câu hiện tại (artifact cũ chỉ có
  50 câu chung). CLI/notebook mặc định `dev_eval`; train/dev và retrieval train giữ phạm vi cũ.
- `test` dành riêng cho `data/benchmark/v2/test.jsonl`, hiện **0 câu, status=draft**.

## Kiểm chứng

| Kiểm tra | Kết quả / phạm vi |
|---|---|
| Annotation trên bộ phát triển | 100/100 hợp lệ cấu trúc, schema SQL, mention, owner/address, class/membership, ba property và hash |
| Human review annotation | 0/100; cả 100 là pending, `--require-human` trả mã 1 |
| Gold SQL | 1.447 SQL phân biệt / 5.488 câu train/dev/dev_eval, không lỗi thực thi trên DuckDB sample |
| Leakage phát triển | Không trùng ID, câu chuẩn hóa, SQL canonical hoặc family; không trùng 12-gram với dev_eval; văn mẫu train/dev được báo riêng |
| Multi-address | 34 ca phát triển có raw-table witness phân biệt union với từng địa chỉ riêng |
| Kiểm thử tự động | 245 test PASS; Ruff sạch; `check-sql` đạt 1.447 SQL |
| Gold-echo dev_eval | 100/100, EX=100%, valid SQL=100%; chỉ kiểm tra đường ống |
| Benchmark draft | PASS kiểm artifact hiện có; `release_ready=false`; thiếu câu, quota, human review và full snapshot |
| Gate test cuối | Link/prompts/generate/echo-gold/evaluate/report từ chối dùng draft với `--split test` |

Store có scope `labeled_address_transactions_plus_approximately_one_percent_of_other_transactions`,
`complete_snapshot=false`. Hash dictionary và manifest Parquet được ghi trong báo cáo;
kết quả sample không xác nhận parity BigQuery hoặc accuracy LLM.

Artifact chi tiết:

- [Kiểm annotation](annotations.json).
- [Kiểm train/dev/dev_eval trên DuckDB](development.json), [bản đọc](development.md).
- [Kiểm benchmark draft với store sample](benchmark.json).
- [Test suite](tests.xml), [ba gate từ chối phát hành/đóng băng đúng kỳ vọng](gates.json).
- [Gold-echo dev_eval](../../runs/gold-echo/eval-dev_eval.json).
- [Định dạng và cách vận hành](../../data/benchmark/README.md).

## Chạy lại

```bash
uv run --locked pytest -q --junitxml=reports/benchmark-t07/tests.xml
uv run --locked ruff check src tests
uv run --locked eth-nl2sql check-sql
uv run --locked eth-nl2sql check-annotations
uv run --locked eth-nl2sql check-dataset \
  --out reports/benchmark-t07/development.json --report reports/benchmark-t07/development.md
uv run --locked eth-nl2sql check-benchmark
uv run --locked eth-nl2sql echo-gold --split dev_eval
uv run --locked eth-nl2sql evaluate --config gold-echo --split dev_eval
```

Các lệnh `check-annotations --require-human`, `check-benchmark --require-release` và
`freeze-benchmark` hiện phải trả mã 1. Không dùng agent để xác nhận thay human reviewer.
Đóng băng chỉ được phép khi đủ 100 câu/100 SQL, 20 câu mỗi nhóm chính, property 7/7/6,
hash đúng (kể cả metadata case), không leakage, human review độc lập đầy đủ và gold đạt trên full snapshot.
Thay nội dung annotation làm review hết hiệu lực; thay file/phụ thuộc làm checksum fail.
Bản frozen không được ghi đè bằng lệnh freeze hoặc hàm tạo draft.

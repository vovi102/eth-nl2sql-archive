# T01 — Xác nhận pipeline hiện tại

Ngày kiểm tra: **26/10/2026** (Asia/Saigon). Trạng thái: **hoàn thành**.

## Môi trường

- Linux x86_64, CPython 3.11.15, uv 0.11.14.
- Môi trường `.venv/` được tạo bằng `uv sync --locked`, gồm dependency lõi và nhóm `dev`.
- Giữ nguyên `pyproject.toml`, `.python-version` và `uv.lock`.
- SHA-256 của `uv.lock`:
  `2e20ab85c09f1b1d4c6294abbe18184549d519b721bdac168ecf5fa7dda5a4ca`.

| Package | Phiên bản |
|---|---|
| eth-nl2sql | 0.1.0 |
| duckdb | 1.5.6 |
| numpy | 2.4.6 |
| pyarrow | 21.0.0 |
| pytest | 8.4.2 |
| pytz | 2026.5 |
| rapidfuzz | 3.14.6 |
| ruff | 0.17.2 |
| sqlglot | 30.24.0 |

## Kết quả

| Kiểm tra | Kết quả | Exit code |
|---|---|---|
| `uv sync --locked` | Cài đặt thành công theo lockfile | 0 |
| `uv run --locked pytest -q` | `75 passed in 11.99s` | 0 |
| `uv run --locked ruff check src tests` | `All checks passed!` | 0 |
| `uv run --locked eth-nl2sql check-sql` | `{"checked": 1050, "failures": []}` | 0 |

`check-sql` kiểm SQL phân biệt trong từng split: 901 train, 99 dev và 50 test.
Các kiểm tra đã pass; không cần sửa mã nguồn hoặc dữ liệu để hoàn tất T01.

## Chạy lại

Từ thư mục gốc của repo:

```bash
uv sync --locked
uv run --locked pytest -q
uv run --locked ruff check src tests
uv run --locked eth-nl2sql check-sql
```

Trong phiên kiểm tra này, mỗi lệnh trên dùng thêm biến môi trường
`UV_CACHE_DIR=/tmp/eth-nl2sql-uv` vì thư mục cache mặc định chỉ đọc.
Lần cài đầu cần tải package; các kiểm tra sau khi cài không cần BigQuery hoặc GPU.

## Phạm vi xác nhận

T01 xác nhận test của pipeline lõi trên CPU với fixture cục bộ, lint và khả năng chạy SQL
dataset trên schema DuckDB rỗng. Kết quả này chưa xác nhận tính đúng của gold trên dữ liệu
Ethereum thật, parity BigQuery–DuckDB, embedding MiniLM hoặc training/inference trên GPU.
Các phần đó thuộc các task tiếp theo.

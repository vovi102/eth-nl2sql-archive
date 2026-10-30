# AGENTS.md

Repo luận văn NL→SQL trên Ethereum. Prediction, số đo và manifest là bằng chứng nghiên cứu;
các quy ước dưới đây giữ chúng truy vết được và giữ mỗi workflow ở một chỗ.

## Gate hoàn tất

Một thay đổi chỉ xong khi cả ba lệnh xanh trên working tree cuối cùng:

```bash
uv run --locked ruff check src tests scripts
uv run --locked pytest -q
uv run --locked eth-nl2sql check-sql
```

Tin nhắn cuối ghi kết quả thật của gate; khi đỏ, dán output lỗi.
`tests/test_repo_conventions.py` kiểm máy các quy ước bên dưới; khi nó đỏ, làm theo câu
hướng dẫn in trong lỗi.

## Mở rộng module chung

Logic nằm trong `src/eth_nl2sql/` và có test; `scripts/` chỉ parse argument rồi gọi vào `src`.
Workflow GPU/Kaggle dùng chung `gpu_workflow.py` (package, verify, stage, collect),
`gpu_notebook.py` (`NotebookSpec`), `kaggle.py` (tên kernel, Kaggle CLI) và
`generation/runs.py` (`Job`). Loại job mới = thêm field/tham số vào các module này cộng
một entry point mỏng. Trước khi viết hàm package/poll/download/collect/verify, tìm hàm
sẵn có và tái sử dụng. Cần hành vi khác ở một module: sửa chính module đó.

## Đặt tên theo vai trò

File, thư mục, config và kernel mang tên việc chúng làm (`gpu_notebook.py`,
`reports/experiments/`). Mã mốc (T11B, …) chỉ nằm trong commit message và phần tường thuật
của `reports/<chủ đề>/README.md`.

## Kaggle

- Tên kernel lấy từ `eth_nl2sql.kaggle.load_settings()`; owner và tag chỉ có trong
  `configs/kaggle.toml`.
- Chạy lại một job = push version mới lên slug sẵn có.
- `kernel_sources` chỉ ghi slug, không pin version. Trước khi push version mới lên một
  kernel, kiểm tra kernel nào đang mount output của nó.

## Bằng chứng

Đọc [reports/README.md](reports/README.md) trước khi thêm, xóa hoặc di chuyển file trong
`reports/` hoặc `runs/`; danh sách file được commit nằm trong `.gitignore`. Khi di chuyển
hay xóa file, `git grep` đường dẫn cũ và cập nhật mọi chỗ tham chiếu.

## Hỏi trước

Các việc sau cần người dùng duyệt trong lượt hiện tại:

- push/submit job Kaggle, tạo kernel slug mới, hoặc chạy lệnh dùng quota BigQuery
  (`supplement-run`, `snapshot-run`);
- sửa `data/benchmark/v2/` hoặc chạy với `--split test`;
- sửa manifest, hash hoặc prediction đã ghi;
- thêm entry vào `LEGACY` trong `tests/test_repo_conventions.py`.

`LEGACY` ghi vi phạm có trước quy tắc và chỉ co lại: khi sửa một file có trong đó, đưa
file về quy ước rồi xóa entry.

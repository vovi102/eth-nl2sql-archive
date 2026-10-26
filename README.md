# eth-nl2sql

Hệ thống hỏi đáp dữ liệu Ethereum bằng tiếng Anh. Câu hỏi được chuyển thành GoogleSQL bởi một LLM
nhỏ, có bước linking đặc thù blockchain, rồi chạy trên dữ liệu lấy từ BigQuery public dataset.
Repo này là bản tinh gọn của [luanvan](https://github.com/vovi102/luanvan), dựng lại từ commit
`0ed5cd1`; xem `data/import-manifest.json`.

## Ba đóng góp

1. **Dataset NL–SQL cho blockchain:** khoảng 1.000 SQL train, mỗi SQL có 4 cách diễn đạt, cùng
   100 câu test được kiểm bằng thực thi và review.
2. **Schema/entity linking đặc thù blockchain**, xử lý bốn trường hợp:
   - một thực thể có nhiều địa chỉ;
   - alias ("Tornado Cash" / "the mixer" / "TC");
   - câu hỏi theo lớp ("any major DEX");
   - property nhập nhằng (gửi hay nhận).
3. **Thực nghiệm LLM nhỏ** (Llama-3-8B-Instruct 4-bit): zero-shot, five-shot và QLoRA, mỗi cấu hình
   có và không có linking. Đo accuracy, latency, cost và privacy.

## Kiến trúc

```
câu hỏi ─┬─ schema linker ──┐
         ├─ entity linker ──┼─→ linking hints ─→ prompt ─→ LLM (± LoRA) ─→ trích SQL
         └─ resolver ───────┘                                               │
                     validator (read-only, allowlist, cửa sổ ngày) ←────────┘
                                         │
                       DuckDB: bản sao managed layer dựng từ BigQuery ─→ kết quả
```

Model sinh GoogleSQL. Khi chạy, SQLGlot chuyển câu SQL sang DuckDB, thực thi trên bản sao cục bộ
của cửa sổ 2026-05-31 → 2026-07-01. Nhờ vậy việc đánh giá miễn phí và lặp lại được; độ trung thực
của bản sao được kiểm bằng kết quả BigQuery thật (`eth-nl2sql parity`).

## Cài đặt

```bash
uv sync --locked                  # lõi: validator, DuckDB store, đánh giá
uv sync --locked --extra embed    # thêm linking và retrieval (MiniLM, kéo theo torch)
uv sync --locked --extra bq       # thêm trích snapshot từ BigQuery (chạy một lần)
uv run --locked pytest -q
uv run --locked ruff check src tests
uv run --locked eth-nl2sql check-sql
```

Extra `gpu` dùng trên Kaggle (xem `notebooks/`).

## Quy trình

| Bước | Lệnh | Ghi chú |
|---|---|---|
| Kiểm SQL của dataset | `eth-nl2sql check-sql` | offline, không cần dữ liệu |
| Sinh train/dev thực thể | `eth-nl2sql build-entity-data` | 10 template; split theo family, giữ dữ liệu chung |
| Kiểm dataset và gold | `eth-nl2sql check-dataset` | chạy gold trên DuckDB, ghi rỗng/0, leakage và review vào `reports/entity-dataset/` |
| Kiểm CSV đã nhập | `eth-nl2sql check-data` | offline; cần `data/raw/luanvan/`; xuất JSON + Markdown vào `reports/data-quality/` |
| Kiểm join của CSV | `eth-nl2sql local-plan` | báo cáo mapping và tỷ lệ join trong `reports/local-store/plan.json` |
| Ước lượng phần bổ sung | `eth-nl2sql supplement-plan --project P` | dry-run metadata còn thiếu của bộ CSV |
| Tải phần bổ sung | `eth-nl2sql supplement-run --project P` | có sử dụng quota BigQuery; tối đa 50 GiB/truy vấn; có provenance/checksum |
| Chuyển CSV đã bổ sung | `eth-nl2sql prepare-local` | xuất Parquet đầy đủ schema, giữ nhãn dữ liệu lấy mẫu |
| Ước lượng snapshot | `eth-nl2sql snapshot-plan --project P` | dry-run miễn phí; cần ADC (`gcloud auth application-default login`) |
| Trích snapshot | `eth-nl2sql snapshot-run --project P` | ⚠ tốn free quota BigQuery; chạy lại được, tự bỏ qua file đã có |
| Dựng store | `eth-nl2sql build-store` | `--labels data/entities/v1` cho parity |
| Kiểm dictionary | `eth-nl2sql check-dictionary` | mặc định v2; kiểm địa chỉ, owner, alias, nhóm, nguồn, ngày và checksum |
| Đo hiện diện dictionary | `eth-nl2sql dictionary-coverage` | đo trên raw tables của DuckDB local; JSON + Markdown tại `reports/dictionary-v2/` |
| Kiểm parity | `eth-nl2sql parity` | so với 88 kết quả gold BigQuery thật + 206 witness |
| Linking | `eth-nl2sql link --split test` (cả `train`, `dev`) | CPU, khoảng 0,15 s/câu |
| Dựng prompt | `eth-nl2sql prompts --config b2l` | cấu hình `b1 b1l b2 b2l b3 b3l`; `--training` cho SFT |
| Sinh SQL / train | `notebooks/kaggle_predict.ipynb`, `kaggle_train.ipynb` | ⚠ GPU Kaggle T4 |
| Đánh giá | `eth-nl2sql evaluate --config b2l` | local, miễn phí |
| Báo cáo | `eth-nl2sql report` | ghi `RESULTS.md` |

`eth-nl2sql echo-gold` + `evaluate --config gold-echo` dùng gold làm dự đoán; EX phải bằng 100%.
Đây là cách kiểm đường ống.

## Cấu trúc

```
configs/   catalog.json (managed layer) · experiment.toml (model, sinh SQL, QLoRA) · schema_synonyms.json
data/      train/dev/test.jsonl · entities/ (dictionary) · templates/ · raw/luanvan/ · store/
src/eth_nl2sql/
  store/       snapshot (BigQuery→Parquet) · build (DuckDB + macros) · execute · parity
  linking/     dictionary · entity · schema · resolver · context
  generation/  prompt · retrieval · runs · extract · backend (GPU)
  validation.py · results.py · evaluate.py · report.py · train_qlora.py · cli.py
notebooks/ kaggle_predict · kaggle_train
reports/   data-quality/ (kiểm CSV) · local-store/ (mapping, provenance và kiểm chứng T03)
           dictionary-v2/ (kiểm chứng dictionary và mức hiện diện local T04)
```

`data/raw/luanvan/` chứa bản sao bộ CSV Ethereum cũ (khoảng 1,86 GiB), đã đối chiếu SHA-256
với nguồn. Luồng `local-plan` → `supplement-run` → `prepare-local` → `build-store` bổ sung cột
có nguồn thực tế và dựng store phục vụ phát triển. Dữ liệu giao dịch vẫn là tập lấy mẫu;
`parity` từ chối so nó với gold của snapshot đầy đủ. Xem [hướng dẫn T03](reports/local-store/README.md),
[phạm vi dữ liệu](data/raw/luanvan/README.md) và
[manifest nhập dữ liệu](data/raw/luanvan/import-manifest.json).

## Trạng thái

Xem `METHODOLOGY.md` cho phương pháp và giới hạn. Tiến độ:

- [x] Nhập dữ liệu từ luanvan; validator, store, đánh giá, linking và prompt đã có test.
- [x] T01: xác nhận pipeline lõi trên Python 3.11; 75 test pass, lint sạch, 1.050 SQL không lỗi
  (26/10/2026; xem [biên bản kiểm tra](VALIDATION.md)).
- [x] Sao chép bộ CSV Ethereum cũ từ LuanVan; xác nhận checksum của 6 file nguồn (26/10/2026).
- [x] T02: kiểm manifest/checksum và quét 8.662.140 dòng CSV; số dòng khớp nguồn, không trùng khóa,
  có dữ liệu giao dịch/block/token transfer trong đủ 31 ngày
  (26/10/2026; xem [báo cáo chất lượng](reports/data-quality/luanvan.md)).
- [x] T03: bổ sung thuộc tính từ BigQuery, chuyển CSV sang Parquet và dựng DuckDB phát triển;
  122 test pass, năm phép đếm qua managed layer khớp nguồn, gold-echo 50/50
  (26/10/2026; xem [kết quả T03](reports/local-store/README.md)).
- [ ] Trích snapshot BigQuery đầy đủ + parity (ADC đã dùng được; cần dự toán quota cho snapshot).
- [x] T04: dictionary v2 có 47 owner ngoài token, 40 owner nhiều địa chỉ; alias và nhóm
  DEX/exchange/mixer, nguồn kèm ngày xác minh, kiểm nhất quán và báo cáo hiện diện local
  (26/10/2026; xem [dictionary v2](data/entities/v2/README.md) và
  [kết quả T04](reports/dictionary-v2/README.md)). `build-store` và `link` mặc định dùng v2.
- [x] T05: 10 template, thêm 1.268/120 câu train/dev và 50 câu test thực thể; bộ test 100 câu,
  có ca nhiều địa chỉ cho đủ 34 owner hoạt động. Kiểm gold, leakage và review ngữ nghĩa bằng
  agent; xác nhận của người review còn chờ. Xem [kết quả T05](reports/entity-dataset/README.md).
- [ ] Chạy B1/B2 (có và không có linking) và B3 trên Kaggle; `RESULTS.md`.

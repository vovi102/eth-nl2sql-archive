# Dictionary v2 hiện hành

Hoàn tất ngày 26/10/2026. Dictionary tải qua linker và managed SQL layer; store local đã dựng
lại với v2 và `build-store`/`link` mặc định chọn v2.

## Kết quả

| Tiêu chí | Kết quả |
|---|---|
| Địa chỉ | 6.647 địa chỉ duy nhất trên Ethereum mainnet; giữ toàn bộ 5.135 địa chỉ v1 |
| Owner hoạt động | 47 owner ngoài token; 40 owner có nhiều địa chỉ |
| Nhóm chính | 30 sàn tập trung, 5 DEX, Tornado Cash mixer; thêm bridge/lending/staking |
| Alias | Chuẩn hoá, đồng nhất giữa label rows và linker; giữ danh sách khi nhập nhằng |
| Nguồn | Mỗi địa chỉ có URL, revision, locator, ngày lấy nguồn và ngày xác minh; manifest/checksum và snapshot API |
| Hiện diện local | 4.139/6.647 địa chỉ có hoạt động; 45/47 owner ngoài token có hoạt động |
| Nhiều địa chỉ hoạt động | 34 owner ngoài token có từ hai địa chỉ hoạt động trở lên |
| Kiểm thử | 156 test pass; Ruff sạch; 1.050 SQL dataset biên dịch thành công |

`TC`/`the mixer`/`Tornado Cash` giải về 19 pool và một router; `TORN` giải về token riêng.
Token quản trị CoinEx/SwissBorg và token giao thức được tách khỏi owner hoạt động. 19 token
đổi owner đã đối chiếu tên/symbol với metadata local và giữ bằng chứng. `Uniswap` giữ ba ứng
viên V2/V3/V4. Tên view `entity_labels_v1` giữ nguyên để tương thích managed SQL API.

Loader và store kiểm địa chỉ trùng/sai, chain, nguồn/ngày, graph owner–alias–nhóm và checksum.
Nhãn v1 vẫn giữ nguyên để tái tạo parity. Store hiện tại dùng v2 như metadata trong `validation.json`.

## Chạy lại

```bash
eth-nl2sql check-dictionary
eth-nl2sql build-store
eth-nl2sql dictionary-coverage
uv run --locked pytest -q
uv run --locked ruff check src tests
eth-nl2sql check-sql
```

`dictionary-coverage` đọc store, join dictionary được chọn với bảng raw và không đổi nhãn trong
database. Có thể dùng `--dictionary`, `--store`, `--out`, `--report` để chọn artifact khác.
Không cần encoder, GPU hoặc BigQuery cho phép đo này.

## Artifact và giới hạn

- [Dictionary và quy tắc nguồn](../../data/entities/v2/README.md).
- [Manifest dictionary](../../data/entities/v2/manifest.json): lineage v1, hash ba file, nguồn
  revision/checksum và thay đổi phân loại; `evidence/` giữ snapshot API và token metadata.
- [Coverage Markdown](coverage.md): theo nhóm và từng owner ngoài token.
- [Coverage JSON](coverage.json): từng địa chỉ/owner/nhóm, gồm số 0, vai trò from/to/token,
  first/last seen, metadata presence, tỷ lệ khớp trên số dòng local và scope/hash dữ liệu.
- [Validation JSON](validation.json): checksum dictionary/store, kiểm v1 không đổi, số dòng qua
  managed layer, alias SQL và đối chiếu số đếm owner với báo cáo coverage.

Cửa sổ đo UTC là [2026-05-31, 2026-07-01). Dữ liệu T03 gồm giao dịch đã lọc/lấy mẫu; tỷ lệ
hiện diện chỉ mô tả dữ liệu local, không đại diện toàn mạng. Concrete và Merlins Seal chưa có
hoạt động local trong cửa sổ. Tornado Cash chỉ quan sát thấy hoạt động của router; các pool có
số đếm 0. Vì thế dữ liệu hiện tại chưa đủ chứng minh trường hợp nhiều pool mixer cùng hoạt động.

Nguồn xác minh vào tháng 8/tháng 10 không chứng minh khoảng sở hữu lịch sử trong tháng 6;
dictionary chưa có valid_from/valid_to. Nhãn kế thừa giữ nguồn/ngày cũ trừ các token đã được
đối chiếu metadata; nhãn mới ghi ngày 2026-10-26. Snapshot Bitstamp là trang mặc định và danh
sách địa chỉ của mọi owner là tập tuyển chọn. Chưa tạo template hoặc 50 câu test thực thể ở T04.

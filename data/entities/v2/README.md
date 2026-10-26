# Dictionary v2 — T04

Dictionary Ethereum mainnet (`chain_id=1`) cho entity linking và managed SQL layer. Có 6.647
địa chỉ, 5.102 owner; 47 owner ngoài token, trong đó 40 owner có nhiều địa chỉ. Mọi địa chỉ v1
đều được giữ. Danh sách là tập địa chỉ được tuyển chọn, không phải toàn bộ địa chỉ của từng owner.

## Tải và kiểm tra

```python
from eth_nl2sql.config import DICTIONARY_DIR
from eth_nl2sql.linking.dictionary import load_dictionary

dictionary = load_dictionary(DICTIONARY_DIR)
binance = dictionary.by_id["owner:Binance"]  # 50 địa chỉ
mixers = dictionary.owners_of_class("MixerAccount")
```

```bash
eth-nl2sql check-dictionary
eth-nl2sql build-store                         # mặc định nhãn v2
eth-nl2sql link --split test --no-encoder       # lexical/fuzzy, offline
eth-nl2sql dictionary-coverage                 # JSON + Markdown, read-only trên store
```

`--dictionary PATH` chọn dictionary khác cho `check-dictionary`, `link`, `dictionary-coverage`.
`build-store --labels PATH` chọn nhãn khác; parity với gold BigQuery kế thừa phải dùng v1.
Tên view `entity_labels_v1` là giao diện managed layer, không phải phiên bản dictionary đang nạp.

## Hợp đồng dữ liệu

| File | Nội dung |
|---|---|
| `entities.json` | Một dòng/địa chỉ, owner chuẩn, primary_label, category, concept_class, address_role, aliases, confidence, verified_date, sources |
| `aliases.json` | Phrase chuẩn hoá NFKC/casefold/whitespace → một owner hoặc danh sách owner khi nhập nhằng |
| `concepts.json` | Nhóm, ontology class, alias nhóm và danh sách owner thành viên |
| `manifest.json` | Phiên bản 2, lineage/hash v1, hash ba file, revision/checksum nguồn và các thay đổi phân loại |
| `evidence/` | Snapshot API Binance/Bitstamp và trích token metadata local, kiểm checksum khi tải |

Một owner có nhiều dòng địa chỉ và dùng cùng category/concept_class. Mỗi địa chỉ có đúng một
owner, được so sánh không phân biệt hoa/thường. Alias của owner có mặt trên mọi dòng địa chỉ
của owner để SQL và linker có cùng ánh xạ. Nhóm chứa đúng các owner có category/class tương ứng.
Loader từ chối địa chỉ trùng/sai, chain khác 1, owner/alias/nhóm không khớp, nguồn rỗng, ngày sai
hoặc checksum khác manifest. V1 và fixture cũ vẫn tải được với các kiểm tra cơ bản.

| Ví dụ | Kết quả |
|---|---|
| `Binance`, `binance exchange`, `bnb exchange` | owner Binance, 50 địa chỉ |
| `Tornado Cash`, `tornado`, `TC`, `the mixer` | owner Tornado Cash, 19 pool + một router |
| `TORN` | owner Tornado Cash Token, riêng token quản trị |
| `any major DEX`, `exchanges`, `mixers` | class DEXProtocol, ExchangeAccount, MixerAccount |
| `Uniswap` | nhập nhằng giữa Uniswap V2, V3, V4; cần câu hỏi cụ thể hơn |

Tên token trùng nhau vẫn có thể nhập nhằng. V2 giữ mọi ứng viên đã khai báo thay vì ghi đè
alias bằng một owner cuối cùng. CoinEx/SwissBorg token được tách khỏi ví sàn; UNI/CRV và các
token chỉ có bằng chứng token được phân loại TokenContract. Gauntlet/Sentora là các vault
lending được quản lý, theo nội dung adapter; Concrete/Veda/Hastra giữ loại hoạt động vault/staking.

## Nguồn và thời điểm

- Ví sàn: phần Ethereum của [DefiLlama adapters](https://github.com/DefiLlama/DefiLlama-Adapters/tree/bbd74a89801e9729ea1a5076d80bc7d636520f4b/projects),
  pin commit `bbd74a89801e9729ea1a5076d80bc7d636520f4b`; Binance/Bitstamp bổ sung ví tự công bố từ API.
  Chỉ lấy `ethereum.owners`, hoặc withdrawalAddresses được dùng cho staking Ethereum;
  không quét mọi địa chỉ EVM trong file đa chain. Snapshot Binance chỉ lấy network ETH và loại
  mục ghi custodian bên thứ ba. Snapshot Bitstamp chỉ lấy network ethereum ở trang mặc định;
  đây là danh sách tuyển chọn, không phải kết quả phân trang đầy đủ.
- Uniswap: tài liệu deployment chính thức [V2](https://developers.uniswap.org/docs/protocols/v2/deployments),
  [V3](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-ethereum-deployments),
  [V4](https://developers.uniswap.org/docs/protocols/v4/deployments); các dòng nhãn pin commit
  trong repo Uniswap/docs. Chỉ lấy Ethereum mainnet; Universal Router và Permit2 dùng chung
  nhiều phiên bản được bỏ khỏi owner theo phiên bản để tránh gán độc quyền sai.
- Curve: phần ALIASES_ETHEREUM trong [SDK chính thức](https://github.com/curvefi/curve-js),
  router và factory; Optimism: các proxy L1 trong [superchain registry](https://github.com/ethereum-optimism/superchain-registry).
- Tornado Cash: `netId1.tokens.*.instanceAddress` và router trong
  [networkConfig.js chính thức](https://github.com/tornadocash/tornado-classic-ui/blob/a83fae0772c8da084c0e76b3a756b456f5b9f5bb/networkConfig.js).
  Không lấy địa chỉ token nền của các pool hoặc địa chỉ pool chain khác.

Mỗi dòng ghi URL, revision, locator, retrieved_date và verified_date. Các nguồn đối chiếu trong
T04 ghi ngày 2026-10-26; dữ liệu kế thừa giữ ngày 2026-08-09. Manifest ghi checksum tài liệu đã
đọc; API thay đổi theo thời gian có snapshot giữ trong `evidence/`. Alias như `TC` và `the mixer`
là quy ước ngôn ngữ của dictionary, không phải bằng chứng sở hữu địa chỉ.

19 token được đổi owner đã đối chiếu tên/symbol với `amended_tokens` local. Bằng chứng trích
trong `evidence/token-metadata.json` kèm hash manifest Parquet T03; các dòng này có thêm nguồn
metadata và ngày xác minh 2026-10-26. Ví dụ nhãn giao thức SolvBTC/Avalon USDa/M0/Kelp cũ thực
tế trỏ tới token SOLV/AVL/POWER/KERNEL. Không dùng các tên giao thức đó làm alias token.

Ngày xác minh mô tả lần kiểm nguồn, không phải ngày bắt đầu/kết thúc quyền sở hữu. Các nhãn
không có valid_from/valid_to và không khẳng định attribution lịch sử trong tháng 6/2026. Địa chỉ
không quan sát thấy ở local vẫn được giữ; không chọn nhãn theo việc nó có xuất hiện ở test hay không.

Khi sửa dictionary, kiểm tra source/locator và cập nhật manifest SHA-256 của ba file tương ứng;
`check-dictionary` kiểm lại graph sau khi kiểm hash. Không sửa v1 để giữ khả năng tái tạo parity.

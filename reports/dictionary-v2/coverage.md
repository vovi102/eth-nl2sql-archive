# T04 — Dictionary v2: hiện diện trong dữ liệu local

Đo lúc: 2026-10-26T14:50:30.577448+00:00. Cửa sổ UTC: [2026-05-31, 2026-07-01).
Scope store: `labeled_address_transactions_plus_approximately_one_percent_of_other_transactions`; complete_snapshot: `False`.

Dictionary: 6,647 địa chỉ, 47 owner ngoài token; 40 owner nhiều địa chỉ.
Có hoạt động: 4,139 địa chỉ, 45 owner ngoài token; 34 owner có từ hai địa chỉ hoạt động trở lên.

`any` đếm một dòng nguồn đúng một lần ở mỗi cấp địa chỉ/owner/nhóm, kể cả khi cả hai phía cùng khớp. Token transfer tính thêm vai trò token contract. Các vai trò from/to/token được đếm riêng và có thể chồng lấn.
Hiện diện trong contracts/token metadata/block miner được ghi riêng trong JSON; không thay thế hoạt động giao dịch. Số 0 chỉ có nghĩa không quan sát thấy trong dữ liệu local; đây không phải coverage toàn mạng hay bằng chứng lịch sử về quyền sở hữu.

Nhãn đang nạp trong store khớp dictionary được đo: `True`.
Báo cáo join dictionary trực tiếp với bảng raw, không phụ thuộc nhãn đang nạp.

| Nhóm | Địa chỉ | Hoạt động | Giao dịch any | Token transfer any |
|---|---:|---:|---:|---:|
| bridge | 8 | 5 | 14,206 | 11,628 |
| dex | 21 | 11 | 8,838 | 57,743 |
| exchange | 1,496 | 305 | 1,677,394 | 1,566,315 |
| lending | 10 | 7 | 1,197 | 641 |
| mixer | 20 | 1 | 83 | 0 |
| staking | 1 | 1 | 1,021 | 1,133 |
| token_contract | 5,091 | 3,809 | 3,297,165 | 3,517,753 |

| Owner ngoài token | Địa chỉ | Hoạt động | Giao dịch any | Token transfer any |
|---|---:|---:|---:|---:|
| Aster Bridge | 1 | 1 | 8,229 | 6,088 |
| Binance | 50 | 23 | 285,290 | 433,135 |
| Bitfinex | 4 | 3 | 8,137 | 5,345 |
| Bitget | 57 | 15 | 213,570 | 123,189 |
| Bitkub | 255 | 14 | 6,517 | 6,686 |
| Bitmex | 2 | 2 | 995 | 759 |
| Bitrue | 2 | 1 | 2,361 | 2,318 |
| Bitstamp | 14 | 7 | 5,827 | 5,933 |
| Bitunix | 2 | 1 | 13,775 | 9,633 |
| Bitvavo | 4 | 4 | 526 | 318 |
| Bybit | 119 | 44 | 335,848 | 284,946 |
| CCIP | 1 | 1 | 28 | 0 |
| CoinEx | 14 | 4 | 3,910 | 3,145 |
| Concrete | 1 | 0 | 0 | 0 |
| Crypto-com | 6 | 4 | 148,725 | 81,084 |
| Curve DEX | 6 | 2 | 201 | 663 |
| Deribit | 26 | 9 | 58,202 | 2,538 |
| Gate.io | 45 | 10 | 148,239 | 137,185 |
| Gauntlet | 3 | 2 | 426 | 25 |
| Gemini | 5 | 2 | 14,666 | 5 |
| HTX | 36 | 5 | 4,395 | 2,691 |
| HashKey Exchange | 5 | 4 | 12,215 | 2,354 |
| Hastra | 1 | 1 | 1,021 | 1,133 |
| Indodax | 10 | 6 | 20,059 | 20,798 |
| Korbit | 8 | 4 | 1,327 | 996 |
| KuCoin | 61 | 31 | 127,064 | 102,748 |
| Lista Lending | 1 | 1 | 498 | 351 |
| MEXC | 21 | 17 | 151,025 | 216,831 |
| Merlins Seal | 3 | 0 | 0 | 0 |
| Nexo | 16 | 9 | 14,832 | 1,918 |
| OKX | 226 | 35 | 63,357 | 95,510 |
| OSL HK | 444 | 26 | 3,397 | 299 |
| Optimism Bridge | 2 | 2 | 613 | 220 |
| PancakeSwap AMM | 2 | 1 | 4 | 0 |
| Phemex | 5 | 4 | 4,134 | 2,950 |
| Poloniex | 3 | 3 | 8,974 | 7,500 |
| Robinhood | 2 | 1 | 1 | 0 |
| Sentora | 4 | 3 | 272 | 265 |
| SwissBorg | 30 | 10 | 7,078 | 4,630 |
| Tornado Cash | 20 | 1 | 83 | 0 |
| USDT0 | 1 | 1 | 5,336 | 5,320 |
| Uniswap V2 | 2 | 2 | 4,835 | 4,585 |
| Uniswap V3 | 7 | 4 | 2,513 | 1,729 |
| Uniswap V4 | 4 | 2 | 1,285 | 50,766 |
| VALR | 4 | 3 | 12,918 | 11,066 |
| Veda | 1 | 1 | 1 | 0 |
| WEEX | 20 | 4 | 55 | 50 |

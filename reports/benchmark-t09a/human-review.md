# T09A — hồ sơ human review (DRAFT)

Tác giả: `codex-t09a` (agent). **0/100 human review**; mọi trạng thái là `pending`.
Người review đối chiếu câu hỏi, SQL và annotation; ghi reviewer, timestamp có timezone,
ghi chú, status và bốn hash trong `reviews.jsonl`. Agent không điền xác nhận thay người.
Sửa bất kỳ nội dung case/annotation nào phải cập nhật hash và review lại.

Kiểm: ý hỏi, UTC/cutoff, fact/đơn vị đếm, chiều, token/endpoint, tập owner/class,
join/fanout, NULL/zero, sắp xếp/tie/limit, witness và giải thích ca rỗng.
Kết quả dưới đây chỉ là sample; T09B phải chạy lại toàn bộ trên full snapshot sau T06.
Sample report SHA-256: `28c54703f845765a62a71a715e5e5ba3e354026030a6aacf75118aad0c8c772f`.

## v2-g01 — generic

For each date, report failed and successful outer transaction counts and the failed fraction among transactions whose receipt status is 0 or 1; order by date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "daily_known_status_failure_share"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:daily_known_status_failure_share",
  "id": "v2-g01",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `daily_known_status_failure_share`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNTIF(receipt_status = 0) AS failed,
    COUNTIF(receipt_status = 1) AS succeeded,
    SAFE_DIVIDE(COUNTIF(receipt_status = 0), COUNT(*)) AS failure_fraction
    FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01') WHERE receipt_status IN (0, 1) GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g01",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": "transaction"
  },
  "question_sha256": "7df3b12bfe456f7087acf48f8d5e3b1b4672b57fb573f522295da0796eb32e33",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "transaction_facts"
      },
      {
        "column": "receipt_status",
        "relation": "transaction_facts"
      }
    ],
    "relations": [
      "transaction_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "7408949b8c94453ca3797f9a7d50734084c1186270e9b13d0aafd2b6a151d0e5"
}
```

Lý do tác giả: Denominator excludes unknown receipt status; failed outer transactions remain included.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "693"
    ],
    [
      "number",
      "142168"
    ],
    [
      "number",
      "0.004850869026536283"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "728"
    ],
    [
      "number",
      "149583"
    ],
    [
      "number",
      "0.004843291575466866"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "778"
    ],
    [
      "number",
      "152574"
    ],
    [
      "number",
      "0.005073295424904794"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "792"
    ],
    [
      "number",
      "156697"
    ],
    [
      "number",
      "0.005028922654915582"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "817"
    ],
    [
      "number",
      "166079"
    ],
    [
      "number",
      "0.004895264116575592"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "8b5e2f82d8c722acbcf8422f9ff49165237b656e5941617133731d69c98315b5",
  "case_sha256": "f306bd8a55e965a4adabdbd1627dd1d6347cf500741262a5107634e43c289262",
  "id": "v2-g01",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "7df3b12bfe456f7087acf48f8d5e3b1b4672b57fb573f522295da0796eb32e33",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "7408949b8c94453ca3797f9a7d50734084c1186270e9b13d0aafd2b6a151d0e5",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g02 — generic

Group failed outer transactions by transaction type and return their count and total gas expenditure in wei, calculated as receipt gas used times gas price; sort by expenditure descending, then type. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "failed_gas_expenditure_by_type"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:failed_gas_expenditure_by_type",
  "id": "v2-g02",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `failed_gas_expenditure_by_type`. Property focus: `None`.

```sql
SELECT transaction_type, COUNT(*) AS failed, SUM(CAST(receipt_gas_used AS NUMERIC) * gas_price_wei) AS spent_wei
    FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01') WHERE receipt_status = 0 GROUP BY transaction_type
    ORDER BY spent_wei DESC, transaction_type
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g02",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": "transaction"
  },
  "question_sha256": "116caf9c57727ac62661949f85e85375c826e32f0d7451d50bbc6cfc63157245",
  "schema": {
    "columns": [
      {
        "column": "gas_price_wei",
        "relation": "transaction_facts"
      },
      {
        "column": "receipt_gas_used",
        "relation": "transaction_facts"
      },
      {
        "column": "receipt_status",
        "relation": "transaction_facts"
      },
      {
        "column": "transaction_type",
        "relation": "transaction_facts"
      }
    ],
    "relations": [
      "transaction_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "484a5a5e98f4e15cee2341cefa4b0e3ac34798776811d7659980b4056a0edec0"
}
```

Lý do tác giả: Uses actual receipt gas, not the gas limit; no ETH/token conflation.

Sample: 4 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "2"
    ],
    [
      "number",
      "20276"
    ],
    [
      "number",
      "1779459759390877123"
    ]
  ],
  [
    [
      "number",
      "0"
    ],
    [
      "number",
      "3900"
    ],
    [
      "number",
      "200575829977317887"
    ]
  ],
  [
    [
      "number",
      "4"
    ],
    [
      "number",
      "228"
    ],
    [
      "number",
      "30598000180622267"
    ]
  ],
  [
    [
      "number",
      "1"
    ],
    [
      "number",
      "23"
    ],
    [
      "number",
      "201288419947193"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "7d2f2bc3de68889fa83bf657a2acc57879c42c378f1c966ec68bf3ea873a419b",
  "case_sha256": "ded042eed4a412c3e3958c223ae65d87b930fc092342909adcd3b5310d23eafd",
  "id": "v2-g02",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "116caf9c57727ac62661949f85e85375c826e32f0d7451d50bbc6cfc63157245",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "484a5a5e98f4e15cee2341cefa4b0e3ac34798776811d7659980b4056a0edec0",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g03 — generic

Using the transaction counts recorded in blocks, give each day's minimum, maximum and range of transactions per block, in date order. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "block_daily_transaction_spread"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:block_daily_transaction_spread",
  "id": "v2-g03",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `block_daily_transaction_spread`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, MIN(transaction_count) AS minimum,
    MAX(transaction_count) AS maximum, MAX(transaction_count)-MIN(transaction_count) AS spread
    FROM `nl2sparql-thesis.nl2sparql_analytics.block_facts`(DATE '2026-06-01', DATE '2026-07-01') GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g03",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": null
  },
  "question_sha256": "11711b309b6c28ce5bae478dd0e0aa12589a85ca13cbfc0b410a51306856a048",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "block_facts"
      },
      {
        "column": "transaction_count",
        "relation": "block_facts"
      }
    ],
    "relations": [
      "block_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "02dc023f97ae8062468e531e6ff93f0b6336bdf8a6fbef00c03a88f2c5bf3da2"
}
```

Lý do tác giả: Uses block metadata rather than counting sampled outer transactions.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "15"
    ],
    [
      "number",
      "2227"
    ],
    [
      "number",
      "2212"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "4"
    ],
    [
      "number",
      "2042"
    ],
    [
      "number",
      "2038"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "3"
    ],
    [
      "number",
      "2052"
    ],
    [
      "number",
      "2049"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "918"
    ],
    [
      "number",
      "916"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "4"
    ],
    [
      "number",
      "1097"
    ],
    [
      "number",
      "1093"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "e7eff6dc4feb366ff894e37db55c532b401d7686dac7b48917cd28c6dff25429",
  "case_sha256": "467114cecf33f6d938139487438c864ad4540107054a06c09a971caaf4258b1e",
  "id": "v2-g03",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "11711b309b6c28ce5bae478dd0e0aa12589a85ca13cbfc0b410a51306856a048",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "02dc023f97ae8062468e531e6ff93f0b6336bdf8a6fbef00c03a88f2c5bf3da2",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g04 — generic

Return the ten fee recipient addresses credited with the most blocks, including their block count and average block gas used; break count ties by address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "beneficiary_block_gas_summary"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:beneficiary_block_gas_summary",
  "id": "v2-g04",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `beneficiary_block_gas_summary`. Property focus: `None`.

```sql
SELECT beneficiary_address, COUNT(*) AS blocks, AVG(gas_used) AS average_gas
    FROM `nl2sparql-thesis.nl2sparql_analytics.block_facts`(DATE '2026-06-01', DATE '2026-07-01') GROUP BY beneficiary_address ORDER BY blocks DESC, beneficiary_address LIMIT 10
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g04",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": null
  },
  "question_sha256": "4eb0a47acd09e976ef3dce6344496275931b46493aff95ca3f90c7bb69268103",
  "schema": {
    "columns": [
      {
        "column": "beneficiary_address",
        "relation": "block_facts"
      },
      {
        "column": "gas_used",
        "relation": "block_facts"
      }
    ],
    "relations": [
      "block_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "e1bcb772504e842d1bf620068f094d2d4e6b95fd008260c4e32f1688282e357d"
}
```

Lý do tác giả: Beneficiary is the fee recipient, not an asserted validator identity.

Sample: 10 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97"
    ],
    [
      "number",
      "105044"
    ],
    [
      "number",
      "32563099.09479837"
    ]
  ],
  [
    [
      "string",
      "0x396343362be2a4da1ce0c1c210945346fb82aa49"
    ],
    [
      "number",
      "42974"
    ],
    [
      "number",
      "31710322.095406525"
    ]
  ],
  [
    [
      "string",
      "0xdadb0d80178819f2319190d340ce9a924f783711"
    ],
    [
      "number",
      "25609"
    ],
    [
      "number",
      "30420485.50556445"
    ]
  ],
  [
    [
      "string",
      "0xfb74767c1ce1aada0a0e114441173b57f8c1571b"
    ],
    [
      "number",
      "15004"
    ],
    [
      "number",
      "30962535.457677953"
    ]
  ],
  [
    [
      "string",
      "0x95222290dd7278aa3ddd389cc1e1d165cc4bafe5"
    ],
    [
      "number",
      "3470"
    ],
    [
      "number",
      "29224675.86282421"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "7f47ceff773472f14ccc15d2baacb7807813f4709f61076073dd0d2319c3571f",
  "case_sha256": "22a6aa9475c5baaae5a8811e5f9a32cd2a020230c815a41381bc94828f8f769c",
  "id": "v2-g04",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "4eb0a47acd09e976ef3dce6344496275931b46493aff95ca3f90c7bb69268103",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "e1bcb772504e842d1bf620068f094d2d4e6b95fd008260c4e32f1688282e357d",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g05 — generic

Which five UTC hours of day contain the most outer transaction rows? Return hour and count, resolving count ties with the earlier hour. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "busiest_utc_hours"
  ],
  "difficulty": "easy",
  "empty_reason": null,
  "family_id": "t09a:busiest_utc_hours",
  "id": "v2-g05",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `busiest_utc_hours`. Property focus: `None`.

```sql
SELECT EXTRACT(HOUR FROM block_timestamp AT TIME ZONE 'UTC') AS utc_hour, COUNT(*) AS n
    FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01') GROUP BY utc_hour ORDER BY n DESC, utc_hour LIMIT 5
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g05",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": "transaction"
  },
  "question_sha256": "eda929d189fc163d7928bf58e742ef090f4d4357ba8f89c39ddc9e4ce4b0d19f",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "transaction_facts"
      }
    ],
    "relations": [
      "transaction_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "ef9706c3a5a31d4e3a99b6965a31afd8232edee51383db63e2b6d862e9251706"
}
```

Lý do tác giả: Explicit UTC hour extraction; all stored outer rows are counted.

Sample: 5 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "15"
    ],
    [
      "number",
      "224138"
    ]
  ],
  [
    [
      "number",
      "14"
    ],
    [
      "number",
      "224039"
    ]
  ],
  [
    [
      "number",
      "16"
    ],
    [
      "number",
      "216578"
    ]
  ],
  [
    [
      "number",
      "13"
    ],
    [
      "number",
      "205955"
    ]
  ],
  [
    [
      "number",
      "12"
    ],
    [
      "number",
      "202918"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "a6e409598bcd467d4a4541e26e599204634629e593fb50d644383addcb2f3fd1",
  "case_sha256": "a1f7f4b417bf2330c267a79f7a5af3cee1787d4180e6b7e1d64f3efb71d6bdcd",
  "id": "v2-g05",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "eda929d189fc163d7928bf58e742ef090f4d4357ba8f89c39ddc9e4ce4b0d19f",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "ef9706c3a5a31d4e3a99b6965a31afd8232edee51383db63e2b6d862e9251706",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g06 — generic

For each date with successful contract creations, count distinct non-null contract addresses recorded in transaction receipts; return dates chronologically. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "creation_receipt_daily_addresses"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:creation_receipt_daily_addresses",
  "id": "v2-g06",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `creation_receipt_daily_addresses`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(DISTINCT receipt_contract_address) AS contracts
    FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01') WHERE receipt_status = 1 AND receipt_contract_address IS NOT NULL
    GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g06",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": "transaction"
  },
  "question_sha256": "c58736753655330606a4c0706db64fdb03e313ad59b26242d4b7eda2ddd75c39",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "transaction_facts"
      },
      {
        "column": "receipt_contract_address",
        "relation": "transaction_facts"
      },
      {
        "column": "receipt_status",
        "relation": "transaction_facts"
      }
    ],
    "relations": [
      "transaction_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "3f1a38098b096181ad24d9c724fbb547e8c83655c22611f2a443cd1166944b0b"
}
```

Lý do tác giả: Receipt contract address identifies creation, not the transaction recipient.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "15"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "17"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "19"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "8"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "8"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "fed31c834794fb161b4bc948242ac0e5cc1af3e9af3a68ce3a87996ec2cc8f14",
  "case_sha256": "275ea636b13974378e1c294919fa760f78588e361d8b3d7854e35088906e2667",
  "id": "v2-g06",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "c58736753655330606a4c0706db64fdb03e313ad59b26242d4b7eda2ddd75c39",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "3f1a38098b096181ad24d9c724fbb547e8c83655c22611f2a443cd1166944b0b",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g07 — generic

Find sender-recipient pairs with both a failed and a successful outer transaction. Return each pair and the two counts, keeping the twenty pairs with the most combined rows; break ties by sender then recipient. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "mixed_outcome_endpoint_pairs"
  ],
  "difficulty": "hard",
  "empty_reason": null,
  "family_id": "t09a:mixed_outcome_endpoint_pairs",
  "id": "v2-g07",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `mixed_outcome_endpoint_pairs`. Property focus: `None`.

```sql
SELECT from_address, to_address, COUNTIF(receipt_status = 0) AS failed,
    COUNTIF(receipt_status = 1) AS succeeded FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01') WHERE receipt_status IN (0, 1)
    GROUP BY from_address, to_address HAVING failed > 0 AND succeeded > 0
    ORDER BY failed+succeeded DESC, from_address, to_address LIMIT 20
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g07",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": "transaction"
  },
  "question_sha256": "f57e1bf4a33f9271c5d804b8b813549d3939dedad2e38484f301be2f41d5ff70",
  "schema": {
    "columns": [
      {
        "column": "from_address",
        "relation": "transaction_facts"
      },
      {
        "column": "receipt_status",
        "relation": "transaction_facts"
      },
      {
        "column": "to_address",
        "relation": "transaction_facts"
      }
    ],
    "relations": [
      "transaction_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "fbe25b02bd41c33eef3a6f8921987df73a22bb4da99dac355b25a6035ae3fe79"
}
```

Lý do tác giả: HAVING requires both outcomes for the same ordered endpoint pair.

Sample: 20 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x260b364fe0d3d37e6fd3cda0fa50926a06c54cea"
    ],
    [
      "string",
      "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    ],
    [
      "number",
      "8"
    ],
    [
      "number",
      "24020"
    ]
  ],
  [
    [
      "string",
      "0xf89d7b9c864f589bbf53a82105107622b35eaa40"
    ],
    [
      "string",
      "0xdac17f958d2ee523a2206206994597c13d831ec7"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "11342"
    ]
  ],
  [
    [
      "string",
      "0xf89d7b9c864f589bbf53a82105107622b35eaa40"
    ],
    [
      "string",
      "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "8739"
    ]
  ],
  [
    [
      "string",
      "0x6fe39f2831caf58529779efdb73341aa64df50ab"
    ],
    [
      "string",
      "0xdac17f958d2ee523a2206206994597c13d831ec7"
    ],
    [
      "number",
      "3"
    ],
    [
      "number",
      "6262"
    ]
  ],
  [
    [
      "string",
      "0x05cdb1526f6e224e02919a4c018d9784ea25eb3d"
    ],
    [
      "string",
      "0xdac17f958d2ee523a2206206994597c13d831ec7"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "6119"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "c9fe6fa17fe2227fad11c63cd254792648404164b9f603119091c65e8982bbaa",
  "case_sha256": "f1df0b1e38d27ba5c3028c638b9c4e209c03484c69696dc179b9931616526972",
  "id": "v2-g07",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "f57e1bf4a33f9271c5d804b8b813549d3939dedad2e38484f301be2f41d5ff70",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "fbe25b02bd41c33eef3a6f8921987df73a22bb4da99dac355b25a6035ae3fe79",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g08 — generic

On dates with outer transactions whose sender equals recipient, report their row count and sum of declared value in wei; order by date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "self_transaction_daily_value"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:self_transaction_daily_value",
  "id": "v2-g08",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `self_transaction_daily_value`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS n, SUM(value_wei) AS declared_wei
    FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_address = to_address GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g08",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": "transaction"
  },
  "question_sha256": "e749c60ecb95cef0e17018e25afd91e8f8bea9192b49459bc5f3bf10f778bfb7",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "transaction_facts"
      },
      {
        "column": "from_address",
        "relation": "transaction_facts"
      },
      {
        "column": "to_address",
        "relation": "transaction_facts"
      },
      {
        "column": "value_wei",
        "relation": "transaction_facts"
      }
    ],
    "relations": [
      "transaction_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "2c709a7eef91ed5dea46eea320280bb4b9155a0de87a7b0ed5e3f6737e11cce4"
}
```

Lý do tác giả: Declared outer value is not a net balance change; self-address equality is deliberate.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "120"
    ],
    [
      "number",
      "2057912467453821312"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "121"
    ],
    [
      "number",
      "70103571341402342189"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "119"
    ],
    [
      "number",
      "2740904858436306851"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "154"
    ],
    [
      "number",
      "739697560338074972"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "165"
    ],
    [
      "number",
      "1299947483807732880"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "010d911f845936dfd89acf03988b813f810ed44bfc9440da5f478843e9b768b9",
  "case_sha256": "50ca9a97207bf07dad0ee294dc24336409fb025948d561196d917cf0ebb57401",
  "id": "v2-g08",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "e749c60ecb95cef0e17018e25afd91e8f8bea9192b49459bc5f3bf10f778bfb7",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "2c709a7eef91ed5dea46eea320280bb4b9155a0de87a7b0ed5e3f6737e11cce4",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g09 — generic

Bucket outer transactions with positive gas limits and known receipt gas into utilization below 25%, 25% to below 75%, and at least 75%; return bucket and count ordered by bucket label. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "receipt_gas_utilization_buckets"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:receipt_gas_utilization_buckets",
  "id": "v2-g09",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `receipt_gas_utilization_buckets`. Property focus: `None`.

```sql
SELECT CASE WHEN SAFE_DIVIDE(receipt_gas_used, gas_limit) < 0.25 THEN 'a_below_25'
    WHEN SAFE_DIVIDE(receipt_gas_used, gas_limit) < 0.75 THEN 'b_25_to_75'
    ELSE 'c_at_least_75' END AS bucket, COUNT(*) AS n
    FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01') WHERE gas_limit > 0 AND receipt_gas_used IS NOT NULL
    GROUP BY bucket ORDER BY bucket
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g09",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": "transaction"
  },
  "question_sha256": "68290d363a63f9d2fc4039b9d64662d76da7e48a1073ff16f9f557e96e6ae09d",
  "schema": {
    "columns": [
      {
        "column": "gas_limit",
        "relation": "transaction_facts"
      },
      {
        "column": "receipt_gas_used",
        "relation": "transaction_facts"
      }
    ],
    "relations": [
      "transaction_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "422ce2ad78de56a0841f1c97b84a7e5b0aa6e5a87d78164f7640406ce01e93dc"
}
```

Lý do tác giả: Boundary values 25% and 75% enter the next bucket; missing gas is excluded.

Sample: 3 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "a_below_25"
    ],
    [
      "number",
      "861685"
    ]
  ],
  [
    [
      "string",
      "b_25_to_75"
    ],
    [
      "number",
      "2178428"
    ]
  ],
  [
    [
      "string",
      "c_at_least_75"
    ],
    [
      "number",
      "1269193"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "cab0f68398a77bcb0aca1a73ec5e8f3c0cea257eaf3f8409fec6a3976b7d85c0",
  "case_sha256": "004cfe44ce686171210b5c48c9f80a5f1fdd590cd6833832b536c27ea7f37fc8",
  "id": "v2-g09",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "68290d363a63f9d2fc4039b9d64662d76da7e48a1073ff16f9f557e96e6ae09d",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "422ce2ad78de56a0841f1c97b84a7e5b0aa6e5a87d78164f7640406ce01e93dc",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g10 — generic

For each token contract with transfer logs, show event count, distinct outer transaction count, and events per distinct transaction; return the fifteen highest event counts, breaking ties by token address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "token_event_transaction_multiplicity"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:token_event_transaction_multiplicity",
  "id": "v2-g10",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `token_event_transaction_multiplicity`. Property focus: `None`.

```sql
SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT transaction_hash) AS transactions,
    SAFE_DIVIDE(COUNT(*), COUNT(DISTINCT transaction_hash)) AS events_per_transaction
    FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-07-01') GROUP BY token_address ORDER BY events DESC, token_address LIMIT 15
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g10",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": "token_transfer"
  },
  "question_sha256": "9fdcb675c222c4e8b8def324334494157a0003fc2e03db588797be2f1c7d8fcf",
  "schema": {
    "columns": [
      {
        "column": "token_address",
        "relation": "token_transfer_facts"
      },
      {
        "column": "transaction_hash",
        "relation": "token_transfer_facts"
      }
    ],
    "relations": [
      "token_transfer_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "ea6fb69d6fd31daf022f41412313b4cbedbe75b2396a01fa69a38e8e638fdbe8"
}
```

Lý do tác giả: A transfer row is a log event; no join multiplies event rows.

Sample: 15 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0xdac17f958d2ee523a2206206994597c13d831ec7"
    ],
    [
      "number",
      "674947"
    ],
    [
      "number",
      "438344"
    ],
    [
      "number",
      "1.5397655722446297"
    ]
  ],
  [
    [
      "string",
      "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    ],
    [
      "number",
      "353165"
    ],
    [
      "number",
      "198917"
    ],
    [
      "number",
      "1.7754390021968962"
    ]
  ],
  [
    [
      "string",
      "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    ],
    [
      "number",
      "105518"
    ],
    [
      "number",
      "69912"
    ],
    [
      "number",
      "1.5092974024487928"
    ]
  ],
  [
    [
      "string",
      "0x6c3ea9036406852006290770bedfcaba0e23a0e8"
    ],
    [
      "number",
      "80839"
    ],
    [
      "number",
      "80503"
    ],
    [
      "number",
      "1.0041737574997205"
    ]
  ],
  [
    [
      "string",
      "0xfaba6f8e4a5e8ab82f62fe7c39859fa577269be3"
    ],
    [
      "number",
      "75214"
    ],
    [
      "number",
      "74774"
    ],
    [
      "number",
      "1.0058843983202717"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "72e570f839d23835204cd06a30643ea635eb29e3823573ec9c9aab3ea8d9fa58",
  "case_sha256": "e4835746633af43f38fd9c537144c2398b6c54d6cd731f801e2f6f53b819981b",
  "id": "v2-g10",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "9fdcb675c222c4e8b8def324334494157a0003fc2e03db588797be2f1c7d8fcf",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "ea6fb69d6fd31daf022f41412313b4cbedbe75b2396a01fa69a38e8e638fdbe8",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g11 — generic

List the twenty transaction-hash and token-contract combinations with the most transfer logs, requiring at least three logs; return both keys and log count, breaking ties by the two keys. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "repeated_token_in_one_transaction"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:repeated_token_in_one_transaction",
  "id": "v2-g11",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `repeated_token_in_one_transaction`. Property focus: `None`.

```sql
SELECT transaction_hash, token_address, COUNT(*) AS logs FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-07-01')
    GROUP BY transaction_hash, token_address HAVING logs >= 3
    ORDER BY logs DESC, transaction_hash, token_address LIMIT 20
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g11",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": "token_transfer"
  },
  "question_sha256": "9bf01ca18d5a9e41074e7d8f43dad7263a1c6ff285d8a9875447a8a973b7c606",
  "schema": {
    "columns": [
      {
        "column": "token_address",
        "relation": "token_transfer_facts"
      },
      {
        "column": "transaction_hash",
        "relation": "token_transfer_facts"
      }
    ],
    "relations": [
      "token_transfer_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "2569f9d83c9b2fa04fd83e8bfb16776b1a80cce10d4cce084e285aee2c9f2a09"
}
```

Lý do tác giả: Multiplicity is measured per transaction and token, not per endpoint.

Sample: 20 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0xf2e8255d68ed4ba750489301bb74d771fddd548c8ef33a28dad9da886a6a3536"
    ],
    [
      "string",
      "0xda47c9f2f7eef01865a9203b0198516db52878ed"
    ],
    [
      "number",
      "1503"
    ]
  ],
  [
    [
      "string",
      "0x8c1e7b2e3d0c2ea043204b96da106a7b8a58ddd037af2a1860203b9aa1a0e861"
    ],
    [
      "string",
      "0x272710035c77b978060106ac50b35143754681a8"
    ],
    [
      "number",
      "1002"
    ]
  ],
  [
    [
      "string",
      "0x15870e74d15e776d804954fd592c3f5069a3f41b386c0099cbf7b473622286bf"
    ],
    [
      "string",
      "0x66a3c2fa3e467aa586e90912f977e648589cabaf"
    ],
    [
      "number",
      "1000"
    ]
  ],
  [
    [
      "string",
      "0x9bd0e115a08b76cac522de973cef50788a7c86397b35b9d3e691287858b8d2a0"
    ],
    [
      "string",
      "0x53fdca91fd33b9131b5ceade42a3edbd9b38edff"
    ],
    [
      "number",
      "869"
    ]
  ],
  [
    [
      "string",
      "0x9aa99ef51f961a46a2bd178583dd1d5689a8bf9edb8a944c5d393e5aa0cf02eb"
    ],
    [
      "string",
      "0x007edb4e4ebff5ab3c61cecd2525e717365da092"
    ],
    [
      "number",
      "838"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "78fb191ac92d03d1adea44a04186e5960764301a93aa7435288a6d9de3163804",
  "case_sha256": "2c5fb9a32db8820016569d10138866ba3849c1211a222087f03fc0fff7719ac3",
  "id": "v2-g11",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "9bf01ca18d5a9e41074e7d8f43dad7263a1c6ff285d8a9875447a8a973b7c606",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "2569f9d83c9b2fa04fd83e8bfb16776b1a80cce10d4cce084e285aee2c9f2a09",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g12 — generic

Among transfer events positively classified as ERC20 and not as ERC721, report token addresses with missing normalized amounts, their total event counts and missing-amount counts; show the twenty largest gaps and break ties by token address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "normalization_gap_by_token"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:normalization_gap_by_token",
  "id": "v2-g12",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `normalization_gap_by_token`. Property focus: `None`.

```sql
SELECT token_address, COUNT(*) AS events, COUNTIF(normalized_amount IS NULL) AS missing
    FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-07-01') WHERE is_erc20 IS TRUE AND COALESCE(is_erc721, FALSE) IS FALSE
    GROUP BY token_address HAVING missing > 0 ORDER BY missing DESC, token_address LIMIT 20
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g12",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": "token_transfer"
  },
  "question_sha256": "86cb9ab058d5f64a24f26c6f2e2b602b721900dc3e9aaaf32e6362afd162e75d",
  "schema": {
    "columns": [
      {
        "column": "is_erc20",
        "relation": "token_transfer_facts"
      },
      {
        "column": "is_erc721",
        "relation": "token_transfer_facts"
      },
      {
        "column": "normalized_amount",
        "relation": "token_transfer_facts"
      },
      {
        "column": "token_address",
        "relation": "token_transfer_facts"
      }
    ],
    "relations": [
      "token_transfer_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "cadc1baecfced6b0e2fe62155466d8d4123d75562a2611da79d0c40e48af3591"
}
```

Lý do tác giả: Missing decimals/cast metadata can make normalization NULL; no amount is fabricated.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0xe0b7927c4af23765cb51314a0e0521a9645f0e2a"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "f11293eb0666ef00905809943ac8e6de22b7a5e8d94e8ea0058bea00fb6f8974",
  "case_sha256": "233ee063290dfff38fa3f8b7b3850a679080cc6de6b64688a5ae488e35da729f",
  "id": "v2-g12",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "86cb9ab058d5f64a24f26c6f2e2b602b721900dc3e9aaaf32e6362afd162e75d",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "cadc1baecfced6b0e2fe62155466d8d4123d75562a2611da79d0c40e48af3591",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g13 — generic

In the token metadata, find nonempty symbols assigned to more than one distinct contract address. Return symbol and address count, ordered by count descending and then symbol, limited to twenty rows. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "duplicate_token_symbols"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:duplicate_token_symbols",
  "id": "v2-g13",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `duplicate_token_symbols`. Property focus: `None`.

```sql
SELECT symbol, COUNT(DISTINCT address) AS addresses FROM `nl2sparql-thesis.nl2sparql_analytics.token_dimension`
    WHERE symbol IS NOT NULL AND symbol <> '' GROUP BY symbol HAVING addresses > 1
    ORDER BY addresses DESC, symbol LIMIT 20
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g13",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": null
  },
  "question_sha256": "efbbc8d6c04c723d9b1fa4d78e6dc7de9c99817988fd430c6991da75a80d0d5e",
  "schema": {
    "columns": [
      {
        "column": "address",
        "relation": "token_dimension"
      },
      {
        "column": "symbol",
        "relation": "token_dimension"
      }
    ],
    "relations": [
      "token_dimension"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "ca0f0f9f290153bd697a01ba3916cd8c73e1a9179e5b25421e13644f8eb917a1"
}
```

Lý do tác giả: Metadata-only query; symbol is not assumed to uniquely identify a token.

Sample: 20 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "UNI-V2"
    ],
    [
      "number",
      "526790"
    ]
  ],
  [
    [
      "string",
      "USDT"
    ],
    [
      "number",
      "21638"
    ]
  ],
  [
    [
      "string",
      "ETH"
    ],
    [
      "number",
      "15002"
    ]
  ],
  [
    [
      "string",
      "USDC"
    ],
    [
      "number",
      "11687"
    ]
  ],
  [
    [
      "string",
      "DAI"
    ],
    [
      "number",
      "10144"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "7ef94b3b72b7731801af4e62464de5cd9c923458ca0ba4c7a31511fff8d359a2",
  "case_sha256": "e2246b9c559aad884c4867868c1cdca8075fc5eb98a2b8e663a7d969b677c9bd",
  "id": "v2-g13",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "efbbc8d6c04c723d9b1fa4d78e6dc7de9c99817988fd430c6991da75a80d0d5e",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "ca0f0f9f290153bd697a01ba3916cd8c73e1a9179e5b25421e13644f8eb917a1",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g14 — generic

From the latest available contract metadata before the cutoff, list up to twenty addresses marked as both ERC20 and ERC721, ordered by address; also return their recorded creation time. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "dual_standard_contract_flags"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:dual_standard_contract_flags",
  "id": "v2-g14",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `dual_standard_contract_flags`. Property focus: `None`.

```sql
SELECT address, created_at FROM `nl2sparql-thesis.nl2sparql_analytics.contract_dimension`(DATE '2026-07-01') WHERE is_erc20 IS TRUE AND is_erc721 IS TRUE
    ORDER BY address LIMIT 20
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g14",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": null
  },
  "question_sha256": "eecc7740fd75f291ec70dc952f80023239799bc43125b7f99c3625f58807655f",
  "schema": {
    "columns": [
      {
        "column": "address",
        "relation": "contract_dimension"
      },
      {
        "column": "created_at",
        "relation": "contract_dimension"
      },
      {
        "column": "is_erc20",
        "relation": "contract_dimension"
      },
      {
        "column": "is_erc721",
        "relation": "contract_dimension"
      }
    ],
    "relations": [
      "contract_dimension"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "a5826318d13a84ceb584dd79a83b550eaff7675c80a3b0d8db31c576437884ed"
}
```

Lý do tác giả: Latest-per-address dimension metadata; an empty list is a valid coverage observation.

Sample: 20 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x00000000bc7441ee230d9d7e3b9a6abb83940849"
    ],
    [
      "timestamp",
      "2026-06-23T12:11:11Z"
    ]
  ],
  [
    [
      "string",
      "0x000caba1002917b27300d7b67be2d1c51b93bf00"
    ],
    [
      "timestamp",
      "2026-04-29T14:34:23Z"
    ]
  ],
  [
    [
      "string",
      "0x00d5bbd0fe275efee371a2b34d0a4b95b0c8aaaa"
    ],
    [
      "timestamp",
      "2026-02-05T11:53:35Z"
    ]
  ],
  [
    [
      "string",
      "0x026ad2fae8706f3d11139be460a93377ae3f7772"
    ],
    [
      "timestamp",
      "2024-02-13T22:37:23Z"
    ]
  ],
  [
    [
      "string",
      "0x02d3a27ac3f55d5d91fb0f52759842696a864217"
    ],
    [
      "timestamp",
      "2021-05-30T02:38:52Z"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "589402be5a7fc3a6ff13178707569a691144f2692448c03cd8965b69e2796114",
  "case_sha256": "2c3afceb14c7b101c05b3c0bb6ea143d23827fa126c996b1c7a9808bb419d2e9",
  "id": "v2-g14",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "eecc7740fd75f291ec70dc952f80023239799bc43125b7f99c3625f58807655f",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "a5826318d13a84ceb584dd79a83b550eaff7675c80a3b0d8db31c576437884ed",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g15 — generic

For blocks with at least one observed outer transaction but fewer observed rows than the block's declared transaction count, return block number, both counts and their difference. Show the twenty largest differences, breaking ties by block number. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "observed_vs_declared_block_rows"
  ],
  "difficulty": "hard",
  "empty_reason": null,
  "family_id": "t09a:observed_vs_declared_block_rows",
  "id": "v2-g15",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `observed_vs_declared_block_rows`. Property focus: `None`.

```sql
SELECT b.block_number, b.transaction_count AS declared, COUNT(t.transaction_hash) AS observed,
    b.transaction_count-COUNT(t.transaction_hash) AS gap FROM `nl2sparql-thesis.nl2sparql_analytics.block_facts`(DATE '2026-06-01', DATE '2026-07-01') b JOIN `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01') t
    ON t.block_number=b.block_number AND t.block_hash=b.block_hash
    GROUP BY b.block_number, b.transaction_count HAVING observed < b.transaction_count
    ORDER BY gap DESC, b.block_number LIMIT 20
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g15",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": "transaction"
  },
  "question_sha256": "f05116d92750e54619ca6b4ad0b0a16774d0c4c7bbff3b3ffdc3d73963369f05",
  "schema": {
    "columns": [
      {
        "column": "block_hash",
        "relation": "block_facts"
      },
      {
        "column": "block_number",
        "relation": "block_facts"
      },
      {
        "column": "transaction_count",
        "relation": "block_facts"
      },
      {
        "column": "block_hash",
        "relation": "transaction_facts"
      },
      {
        "column": "block_number",
        "relation": "transaction_facts"
      },
      {
        "column": "transaction_hash",
        "relation": "transaction_facts"
      }
    ],
    "relations": [
      "block_facts",
      "transaction_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "13f7447cafc5d323b3819d3dbdbb0ae5a8c294a6a464d26729eade9986ee2c90"
}
```

Lý do tác giả: A sample-coverage diagnostic, expected to be empty on complete transaction coverage.

Sample: 20 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "25306208"
    ],
    [
      "number",
      "2722"
    ],
    [
      "number",
      "29"
    ],
    [
      "number",
      "2693"
    ]
  ],
  [
    [
      "number",
      "25271916"
    ],
    [
      "number",
      "2658"
    ],
    [
      "number",
      "31"
    ],
    [
      "number",
      "2627"
    ]
  ],
  [
    [
      "number",
      "25306168"
    ],
    [
      "number",
      "2623"
    ],
    [
      "number",
      "39"
    ],
    [
      "number",
      "2584"
    ]
  ],
  [
    [
      "number",
      "25306710"
    ],
    [
      "number",
      "2591"
    ],
    [
      "number",
      "38"
    ],
    [
      "number",
      "2553"
    ]
  ],
  [
    [
      "number",
      "25305492"
    ],
    [
      "number",
      "2560"
    ],
    [
      "number",
      "49"
    ],
    [
      "number",
      "2511"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "f4566373045783cf0fbc3783d5547ab041820cc3a6e904cf289e67bc32a46ed8",
  "case_sha256": "bdd750f650d001f4365ae30c933adbcd5dbeaabce55cb48317aab20c26811f59",
  "id": "v2-g15",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "f05116d92750e54619ca6b4ad0b0a16774d0c4c7bbff3b3ffdc3d73963369f05",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "13f7447cafc5d323b3819d3dbdbb0ae5a8c294a6a464d26729eade9986ee2c90",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g16 — generic

For successful outer transactions with transfer events, return hash, declared wei value, event count and distinct token count. Keep the twenty transactions with the most events, resolving ties by hash. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "outer_transaction_log_summary"
  ],
  "difficulty": "hard",
  "empty_reason": null,
  "family_id": "t09a:outer_transaction_log_summary",
  "id": "v2-g16",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `outer_transaction_log_summary`. Property focus: `None`.

```sql
SELECT t.transaction_hash, t.value_wei, COUNT(*) AS events,
    COUNT(DISTINCT e.token_address) AS tokens FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01') t JOIN `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-07-01') e
    ON t.transaction_hash=e.transaction_hash AND t.block_number=e.block_number
    AND t.block_hash=e.block_hash WHERE t.receipt_status=1
    GROUP BY t.transaction_hash, t.value_wei ORDER BY events DESC, t.transaction_hash LIMIT 20
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g16",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": "transaction_token_transfer_join"
  },
  "question_sha256": "6c43857d3ce90160564de31ab1fe88eff9f200ccd7d36918ad044b6600f18543",
  "schema": {
    "columns": [
      {
        "column": "block_hash",
        "relation": "token_transfer_facts"
      },
      {
        "column": "block_number",
        "relation": "token_transfer_facts"
      },
      {
        "column": "token_address",
        "relation": "token_transfer_facts"
      },
      {
        "column": "transaction_hash",
        "relation": "token_transfer_facts"
      },
      {
        "column": "block_hash",
        "relation": "transaction_facts"
      },
      {
        "column": "block_number",
        "relation": "transaction_facts"
      },
      {
        "column": "receipt_status",
        "relation": "transaction_facts"
      },
      {
        "column": "transaction_hash",
        "relation": "transaction_facts"
      },
      {
        "column": "value_wei",
        "relation": "transaction_facts"
      }
    ],
    "relations": [
      "token_transfer_facts",
      "transaction_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "6eed790db9085cbec5e1bf4368221cb12b283909aab5f2195caf7f5d417196d1"
}
```

Lý do tác giả: Join uses hash plus block identity; transaction value is grouped, never summed across logs.

Sample: 20 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0xf2e8255d68ed4ba750489301bb74d771fddd548c8ef33a28dad9da886a6a3536"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "1503"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "0x9aa99ef51f961a46a2bd178583dd1d5689a8bf9edb8a944c5d393e5aa0cf02eb"
    ],
    [
      "number",
      "100000000000000000"
    ],
    [
      "number",
      "1275"
    ],
    [
      "number",
      "4"
    ]
  ],
  [
    [
      "string",
      "0x2e287a58aa1504d04a5f8e4ebc7288a217fe2dba2971dabbdb3498d50ed21ab7"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "1193"
    ],
    [
      "number",
      "3"
    ]
  ],
  [
    [
      "string",
      "0x8dd96a6d9eb10211efba15b48bf5f065a8511ce317d6f0dc08f25200190f5114"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "1098"
    ],
    [
      "number",
      "5"
    ]
  ],
  [
    [
      "string",
      "0x8c1e7b2e3d0c2ea043204b96da106a7b8a58ddd037af2a1860203b9aa1a0e861"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "1002"
    ],
    [
      "number",
      "1"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "ab0a22eba0f5d7bdb4f5e7c1e9f266e659934dbb704e1f73dbcbdd2da71865c7",
  "case_sha256": "71d2cb5e5c2ebc1563818654e666df53d084323d6ab2b23d24dd512baccc774a",
  "id": "v2-g16",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "6c43857d3ce90160564de31ab1fe88eff9f200ccd7d36918ad044b6600f18543",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "6eed790db9085cbec5e1bf4368221cb12b283909aab5f2195caf7f5d417196d1",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g17 — generic

Count successful outer transactions with no matching token-transfer event, grouped by transaction type and ordered by type. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "successful_transactions_without_transfer_logs"
  ],
  "difficulty": "hard",
  "empty_reason": null,
  "family_id": "t09a:successful_transactions_without_transfer_logs",
  "id": "v2-g17",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `successful_transactions_without_transfer_logs`. Property focus: `None`.

```sql
SELECT t.transaction_type, COUNT(*) AS transactions FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01') t
    WHERE t.receipt_status=1 AND NOT EXISTS (SELECT 1 FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-07-01') e
    WHERE e.transaction_hash=t.transaction_hash AND e.block_number=t.block_number
    AND e.block_hash=t.block_hash) GROUP BY t.transaction_type ORDER BY t.transaction_type
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g17",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": "transaction_token_transfer_join"
  },
  "question_sha256": "f8a1c34a3a0e57035fda128c63eed2d0a40a548d316e3f87fe7484e849604209",
  "schema": {
    "columns": [
      {
        "column": "block_hash",
        "relation": "token_transfer_facts"
      },
      {
        "column": "block_number",
        "relation": "token_transfer_facts"
      },
      {
        "column": "transaction_hash",
        "relation": "token_transfer_facts"
      },
      {
        "column": "block_hash",
        "relation": "transaction_facts"
      },
      {
        "column": "block_number",
        "relation": "transaction_facts"
      },
      {
        "column": "receipt_status",
        "relation": "transaction_facts"
      },
      {
        "column": "transaction_hash",
        "relation": "transaction_facts"
      },
      {
        "column": "transaction_type",
        "relation": "transaction_facts"
      }
    ],
    "relations": [
      "token_transfer_facts",
      "transaction_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "5b2eb9d4a5858b626eec49fb9abaabdff93ce69299498e96e51033a5573bfec4"
}
```

Lý do tác giả: NOT EXISTS avoids fanout and keeps transactions without transfer events.

Sample: 5 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "0"
    ],
    [
      "number",
      "217796"
    ]
  ],
  [
    [
      "number",
      "1"
    ],
    [
      "number",
      "251"
    ]
  ],
  [
    [
      "number",
      "2"
    ],
    [
      "number",
      "1290960"
    ]
  ],
  [
    [
      "number",
      "3"
    ],
    [
      "number",
      "3175"
    ]
  ],
  [
    [
      "number",
      "4"
    ],
    [
      "number",
      "1090"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "7f08955821c776accc7f25832fbd51d3be0fe1568ef27ce43433df46300c9998",
  "case_sha256": "007c4ab52d28303d42328df10934c15934600365f470023fe472a7904f78566a",
  "id": "v2-g17",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "f8a1c34a3a0e57035fda128c63eed2d0a40a548d316e3f87fe7484e849604209",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "5b2eb9d4a5858b626eec49fb9abaabdff93ce69299498e96e51033a5573bfec4",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g18 — generic

Compute total block gas used for each date and its trailing mean over that date and the preceding two observed dates; return dates in order, using the available dates at the start. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "three_day_block_gas_mean"
  ],
  "difficulty": "hard",
  "empty_reason": null,
  "family_id": "t09a:three_day_block_gas_mean",
  "id": "v2-g18",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `three_day_block_gas_mean`. Property focus: `None`.

```sql
WITH daily AS (SELECT DATE(block_timestamp) AS day, SUM(gas_used) AS gas
    FROM `nl2sparql-thesis.nl2sparql_analytics.block_facts`(DATE '2026-06-01', DATE '2026-07-01') GROUP BY day) SELECT day, gas,
    AVG(gas) OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS trailing_mean
    FROM daily ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g18",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": null
  },
  "question_sha256": "3d7ca76a4ee249feaa2513a7438ea9fdf87d5b96d802de4fbc1571450bc34e0a",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "block_facts"
      },
      {
        "column": "gas_used",
        "relation": "block_facts"
      }
    ],
    "relations": [
      "block_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "2856f59bc61beb3c9835634afc5a386cb8d2fe277109e1038099dafc6bda9fdf"
}
```

Lý do tác giả: Question specifies observed-date rows, including partial windows at the start.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "217607317588"
    ],
    [
      "number",
      "217607317588"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "217156169303"
    ],
    [
      "number",
      "217381743445.5"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "216546390137"
    ],
    [
      "number",
      "217103292342.66666"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "215955292490"
    ],
    [
      "number",
      "216552617310"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "215934020537"
    ],
    [
      "number",
      "216145234388"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "d9852ab46784f9fbe04a80ba4ff50fcf24d804fd493ad7f2532e2ef4af558e98",
  "case_sha256": "ec6773e198bcf924a5614d5550321a58ef26279496968d8e6f0e019ce664b65e",
  "id": "v2-g18",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "3d7ca76a4ee249feaa2513a7438ea9fdf87d5b96d802de4fbc1571450bc34e0a",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "2856f59bc61beb3c9835634afc5a386cb8d2fe277109e1038099dafc6bda9fdf",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g19 — generic

Using token metadata, return each known decimals value from 0 through 38 with its number of distinct token addresses, ordered by decimals. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "token_decimal_metadata_histogram"
  ],
  "difficulty": "easy",
  "empty_reason": null,
  "family_id": "t09a:token_decimal_metadata_histogram",
  "id": "v2-g19",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `token_decimal_metadata_histogram`. Property focus: `None`.

```sql
SELECT decimals, COUNT(DISTINCT address) AS tokens FROM `nl2sparql-thesis.nl2sparql_analytics.token_dimension`
    WHERE decimals BETWEEN 0 AND 38 GROUP BY decimals ORDER BY decimals
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g19",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": null
  },
  "question_sha256": "1d287c8d70412fb8407104bda7bb67d5da965b8fd233786c19763f987773c3ee",
  "schema": {
    "columns": [
      {
        "column": "address",
        "relation": "token_dimension"
      },
      {
        "column": "decimals",
        "relation": "token_dimension"
      }
    ],
    "relations": [
      "token_dimension"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "5f4322bd1ec9b74887be18066a65550021895c0276c3aba1d68437baa3637cde"
}
```

Lý do tác giả: Metadata snapshot is not a time series; UTC window supplies the benchmark cutoff context.

Sample: 38 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "0"
    ],
    [
      "number",
      "48572"
    ]
  ],
  [
    [
      "number",
      "1"
    ],
    [
      "number",
      "2564"
    ]
  ],
  [
    [
      "number",
      "2"
    ],
    [
      "number",
      "13130"
    ]
  ],
  [
    [
      "number",
      "3"
    ],
    [
      "number",
      "3504"
    ]
  ],
  [
    [
      "number",
      "4"
    ],
    [
      "number",
      "10565"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "163e5abe11645f6f0177fd6da60abcdb530c6d6b8de7da82d9423e48dcb499d6",
  "case_sha256": "b37a5181fe8a55e14e8f7af0042a2abb34f438a4c3ac0b5034be0f3f3f1b4894",
  "id": "v2-g19",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "1d287c8d70412fb8407104bda7bb67d5da965b8fd233786c19763f987773c3ee",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "5f4322bd1ec9b74887be18066a65550021895c0276c3aba1d68437baa3637cde",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-g20 — generic

For each date, count distinct non-null addresses appearing as either sender or recipient of an outer transaction, counting an address only once that day even if it has both roles; order by date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "daily_union_of_transaction_endpoints"
  ],
  "difficulty": "hard",
  "empty_reason": null,
  "family_id": "t09a:daily_union_of_transaction_endpoints",
  "id": "v2-g20",
  "primary_group": "generic",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [],
  "subset": "generic",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `daily_union_of_transaction_endpoints`. Property focus: `None`.

```sql
WITH endpoints AS (SELECT DATE(block_timestamp) AS day, from_address AS address
    FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01') UNION ALL SELECT DATE(block_timestamp) AS day, to_address AS address FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01'))
    SELECT day, COUNT(DISTINCT address) AS active_addresses FROM endpoints
    WHERE address IS NOT NULL GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [],
  "id": "v2-g20",
  "properties": {
    "address_role": [],
    "direction": [],
    "fact": "transaction"
  },
  "question_sha256": "3c9d036ee5dcb12bbe2e403f7f2ede51cc9a9b0031f4fa7224a3d575be58daca",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "transaction_facts"
      },
      {
        "column": "from_address",
        "relation": "transaction_facts"
      },
      {
        "column": "to_address",
        "relation": "transaction_facts"
      }
    ],
    "relations": [
      "transaction_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "8ab774aff90a5f9e246f76ae68781a2fdbf203b69303e719252267d844bd5d02"
}
```

Lý do tác giả: UNION ALL followed by distinct address count avoids double counting roles.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "59103"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "61010"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "58379"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "56351"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "62063"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "9f6ab2df6e3c9c40d4ad725957edf9f74639230fa828da50a08e7c5bced2ed4f",
  "case_sha256": "7fe19b1179359545958a8c21281f809c8cadb4b02bda1a8e43318f8f75672881",
  "id": "v2-g20",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "3c9d036ee5dcb12bbe2e403f7f2ede51cc9a9b0031f4fa7224a3d575be58daca",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "8ab774aff90a5f9e246f76ae68781a2fdbf203b69303e719252267d844bd5d02",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m01 — multi_address

Across all known Binance addresses, tabulate incoming outer transactions by date with separate total, successful and failed counts; order by date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "binance_inbound_daily_outcomes"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:binance_inbound_daily_outcomes",
  "id": "v2-m01",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `binance_inbound_daily_outcomes`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS total,
    COUNTIF(receipt_status=1) AS succeeded, COUNTIF(receipt_status=0) AS failed
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Binance' GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x030e37ddd7df1b43db172b23916d523f1599c6cb",
        "0x110daa3f3fac2a54bb508ac94f31f9df77057b29",
        "0x150aace136535a374f05b5ee209b6a61396db1c0",
        "0x18e226459ccf0eec276514a4fd3b226d8961e4d1",
        "0x1b46970cfe6a271e884f636663c257a5a571fb2c",
        "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        "0x22132139bf7f3921b1cadeab931f4fbf7bf2bc9e",
        "0x26bff98f6f37c8d560684eaf2afd1149bf76633e",
        "0x28c6c06298d514db089934071355e5743bf21d60",
        "0x308a2a0712570daeea77c8ba9c27a32cdc4000d4",
        "0x32e11a20337ebc79abd0eeab2d91bafbd9591149",
        "0x38aaef3782910bdd9ea3566c839788af6ff9b200",
        "0x42a93a9f5cfda54716c414b6eaf07cf512f46ead",
        "0x43684d03d81d3a4c70da68febdd61029d426f042",
        "0x4976a4a02f38326660d17bf34b431dc6e2eb2327",
        "0x4aec0e98fc1fb55b9cc2faaa7a81acca42cb4e96",
        "0x4ed6cf63bd9c009d247ee51224fc1c7041f517f1",
        "0x4fdfe365436b5273a42f135c6a6244a20404271e",
        "0x56eddb7aa87536c09ccc2793473599fd21a8b17f",
        "0x5a1e5b56aa33c056ed7bb93b88b1774a456f6694",
        "0x5a52e96bacdabb82fd05763e25335261b270efcb",
        "0x6357e4bdaff733dfe8f50d12d07c03b3bed0884b",
        "0x6454ac71ca260f99cca99a3f4241dfda20cfa965",
        "0x756b86fd69914db92229c07c7393d7d9948fed33",
        "0x835678a611b28684005a5e2233695fb6cbbb0007",
        "0x8498fc7280668874a5da79e87ca0896f4f0d1196",
        "0x86523c87c8ec98c7539e2c58cd813ee9d1a08d96",
        "0x87433fec6f8d9df13d1e17c4b11364ecd2e93a51",
        "0x8a6f8404c9ea4c33502a3f6a4bf8e41ef5ca10ea",
        "0x8e609ac80f4324e499a6efd24f221a2caa868224",
        "0x9696f59e4d72e237be84ffd425dcad154bf96976",
        "0x98adef6f2ac8572ec48965509d69a8dd5e8bba9d",
        "0xa345dcb63f984ed1c6d1a8901e0cdbd13b2b4d19",
        "0xa64b436964e7415c0e70b9989a53e1fb9a90e726",
        "0xa7c0d36c4698981fab42a7d8c783674c6fe2592d",
        "0xa9fc92f6faf9f103fc81d17de3e8daadc888afff",
        "0xad354cfbaa4a8572dd6df021514a3931a8329ef5",
        "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",
        "0xc47b3342df38d747033b6041f54e4e5e300c8d18",
        "0xc8daf809c7d7c27dd62d006196d8901ba57e5eae",
        "0xd27b39cb25fed854f9fce3a4e451f96e62089e48",
        "0xdbeb6c856ef5a167f5e1acb9dff65adb33207d8b",
        "0xdbf28a152d79b2b98eecd229b412ee98d21ec3bc",
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
        "0xe1940f578743367f38d3f25c2d2d32d6636929b6",
        "0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055",
        "0xf16924b866e58ac916ba933d1f1034bcbbb1958c",
        "0xf1f8cb7633d3ca3fd06c084d18ca5491a85ae9b4",
        "0xf977814e90da44bfa03b6295a0616a897441acec",
        "0xfc8059c2fb22005ede8a86d388e3d0f536a4dd44"
      ],
      "mention": {
        "end": 24,
        "start": 17,
        "text": "Binance"
      },
      "owner": "Binance"
    }
  ],
  "id": "v2-m01",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "3175df2da69b13159b015290efacb6487e83f0ee57cd010b28160bb2a1d618ae",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "receipt_status",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "4c78d653e2d3133c9fbd17233d2e75cad4169313b8d0331ba32f5ad863f69814"
}
```

Lý do tác giả: All known recipient addresses participate; unknown status is included only in total.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "65"
    ],
    [
      "number",
      "65"
    ],
    [
      "number",
      "0"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "84"
    ],
    [
      "number",
      "84"
    ],
    [
      "number",
      "0"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "81"
    ],
    [
      "number",
      "81"
    ],
    [
      "number",
      "0"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "71"
    ],
    [
      "number",
      "71"
    ],
    [
      "number",
      "0"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "87"
    ],
    [
      "number",
      "87"
    ],
    [
      "number",
      "0"
    ]
  ]
]
```

Multi-address: 8/50 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "e4343d9c56bec42d9b6fa085870574913c83aae833dd54e20a044dd6ddddbb5a",
  "case_sha256": "9c4a5155e7f352f290ce335801bffcd66b0d083d4dc48ffb9baf9872f97ca01e",
  "id": "v2-m01",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "3175df2da69b13159b015290efacb6487e83f0ee57cd010b28160bb2a1d618ae",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "4c78d653e2d3133c9fbd17233d2e75cad4169313b8d0331ba32f5ad863f69814",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m02 — multi_address

Combine the known OKX recipient addresses and summarize incoming outer transactions by type, returning row count and sum of receipt gas used; sort by type. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "okx_inbound_type_gas"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:okx_inbound_type_gas",
  "id": "v2-m02",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `okx_inbound_type_gas`. Property focus: `None`.

```sql
SELECT transaction_type, COUNT(*) AS n, SUM(receipt_gas_used) AS gas
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='OKX' GROUP BY transaction_type ORDER BY transaction_type
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0003b5aa5e30e97fcc596bb5d0f3a75255e08d4e",
        "0x01c2a9e7eeaee29b03708692ba5e1515036451e8",
        "0x01f66697aec1e7de7773115243247952245fd3a4",
        "0x01f7cea182239f9e9caf0f1ce0744bcb23c20585",
        "0x03ae1a796dfe0400439211133d065bda774b9d3e",
        "0x03d0aad7c6a0b36f47d852a28ff0fb7bc9ae46b6",
        "0x0475dd0e4194422a8cac486dc69173f535d0baf4",
        "0x0607c628054a7db3d36eed7c4a408eda8260de09",
        "0x06324bad3913cb69cb5e748a3ed72f9d692324bb",
        "0x06959153b974d0d5fdfd87d561db6d8d4fa0bb0b",
        "0x06d3a30cbb00660b85a30988d197b1c282c6dcb6",
        "0x073f564419b625a45d8aea3bb0de4d5647113ad7",
        "0x0750b999e493112c88cb226a13a2a67419f06ad6",
        "0x0799ddbf6f14db566ca4df4ff0575c4cc1e7749c",
        "0x08af9c4767236221c55069dd523e2f7a0013e898",
        "0x08f619716db7c6245401b543e59acac1d25cb483",
        "0x0938c63109801ee4243a487ab84dffa2bba4589e",
        "0x0a133528245eaf5bab72dc05a9dd8e0ea4b982f9",
        "0x0c48511102453352fe570370672cd556bf0e63f9",
        "0x0ff9491b236a36cc183823e39d7532194143fdb1",
        "0x11b113383ce08e84001dc614f141ae4c27221e31",
        "0x1278678b5b17eba14b313d287659ae9f3aa7c087",
        "0x12a8bdc0470ab29a229d828526641b7d1f170fcf",
        "0x16b5016803bcb4915701efc0a3b471bd4c168d93",
        "0x173810f8ca9c4c631aeb1d6c36d007f054fee980",
        "0x17e91b98988937cb59dc163b0b11781f9785591a",
        "0x1811068091a2459ee38a8dde52cce5b2acfc1b61",
        "0x19abcd6b8516d2b4d9aa3bbf700b38a30dc154fc",
        "0x1a557020c52f9d2495b2c12eb137ee7b5d467a4f",
        "0x1c628a9c66ff63454a4526a4f2b8af250da8d086",
        "0x1dfc6bec8499fcb5e3151c7c6d27feb9d7eae1d4",
        "0x1e43e7a911b1b0229ea7d64e11ae260c482a0870",
        "0x221ac9e1920932e95adf0c941f3524157f4bda4f",
        "0x25236e080106b5387df201fbbd9a6b870917676d",
        "0x26704ccfcd45b5780dcd58d38b12f5e0cdb481a0",
        "0x267b51c97632225da2b2e49aebe59eef1af32653",
        "0x276cdba3a39abf9cedba0f1948312c0681e6d5fd",
        "0x297611b7accb7f24032c27b3a496465624c7ef50",
        "0x2c8fbb630289363ac80705a1a61273f76fd5a161",
        "0x30c1dcde81e5dbf3121d0408abc7908980e83ae2",
        "0x313eb1c5e1970eb5ceef6aebad66b07c7338d369",
        "0x32dc16f4631a27b042a974d05c1ccf8a303e8199",
        "0x3425519651e4c42833633fe5c0e24ed89c1023a3",
        "0x3b9694465483cbb677b700a91c26f487193a6e03",
        "0x3b98b9e9cb75c1cb1729aab8f09ced2936505e4f",
        "0x3bb00393bfa5e76b7f31e93948f7d3cef12942ad",
        "0x3c5883c650d600bd543a9b5c8d9a3a6f5d16b8f4",
        "0x3d2335cac7b31411467ef03168c5869452fb7e86",
        "0x3d55ccb2a943d88d39dd2e62daf767c69fd0179f",
        "0x3e7d48c8ae2e50c2b9adedc8e276d3cc92b39458",
        "0x3f482c72a2b3e777746f5755cc0ff1323ea2ad16",
        "0x400d8280acf364f683e989462879fd8dd358067d",
        "0x4106a4be14867c70e52c51b9805514ae2e16de64",
        "0x42436286a9c8d63aafc2eebbca193064d68068f2",
        "0x42797deffe266a55fdc4c98d7d3885d7058cb3e5",
        "0x42cf18596ee08e877d532df1b7cf763059a7ea57",
        "0x445f16314284b43dfa1fd3cd77b9dea4a1bebd97",
        "0x45d9c02baed2d1670f7bad40fb5f657a05068d52",
        "0x45f329ff834a84fccea2319f91e1993540b22a2a",
        "0x461249076b88189f8ac9418de28b365859e46bfd",
        "0x47eb32dea1ab1436187939fa72d6d5ff884a87da",
        "0x48480aad203e8b030f82754b3c75869c9895c6bf",
        "0x48c4c83be7e3884ee5043a3abe5115eb020b5f4a",
        "0x4a11078a99b118bbfee78a5c187d98d264360433",
        "0x4bcbaf34862e6480329477917cf5cd7b9537a98d",
        "0x4d19c0a5357bc48be0017095d3c871d9afc3f21d",
        "0x4d619eb6db0b9b6184d9881c4828c0effff84eda",
        "0x4e2757e46103556f98d4d036d8efe18389b89f51",
        "0x5041ed759dd4afc3a72b8192c143f72f4724081a",
        "0x52738a51882f35d6b25a3fd0c86089ddbd206821",
        "0x52b311c52436789f3754bd199bf3886b8ccbab4c",
        "0x539c92186f7c6cc4cbf443f26ef84c595babbca1",
        "0x559432e18b281731c054cd703d4b49872be4ed53",
        "0x56fd42ecd77c88bdd959be54af10d1759b473dff",
        "0x593878f92dde464fc4e3b17cd7cc87117dca753c",
        "0x5a150733cb59bbdd5c7398a8fe7da7f97c8a213a",
        "0x5b27e98516fd2bd5001d4dfe3f5a2263f702f634",
        "0x5b873ffcad5dccdc61c1a53c391fb76cb316a841",
        "0x5c52cc7c96bde8594e5b77d5b76d042cb5fae5f2",
        "0x5ca38fb7cf2b587026a1650f0d2b0a13c41f5d0f",
        "0x5f5105b9a19e301208844263806df9b7212e655d",
        "0x5f8215ee653cb7225c741c7aa8591468d1f158b8",
        "0x608c27519c5e65a61cfc1d2c9e658e5c57a2e3d7",
        "0x611f7bf868a6212f871e89f7e44684045ddfb09d",
        "0x65a0947ba5175359bb457d3b34491edf4cbf7997",
        "0x65e891ec42fcaa19459fe6221163e1a3f8cf7ea6",
        "0x6667a4b7eff4a0b86781fb3b187622cd3c257f09",
        "0x66e6bdac6fae819f944901e3b6ecc9bfff61a706",
        "0x6709383e211ab08a6e3270532e756220400424a6",
        "0x68841a1806ff291314946eebd0cda8b348e73d6d",
        "0x68b5e9e083bfc28c33cfbf3f19d33e629015e907",
        "0x68e2ea1622aa67fb3a01a66d132daed8a48d1662",
        "0x69a722f0b5da3af02b4a205d6f0c285f4ed8f396",
        "0x6a4561ef7874a76b4bf0d3edca31dfcd51603414",
        "0x6b7ba57e1d43c2c975ba25139a04d193e64a11d0",
        "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
        "0x6d29fc1267b1691c0cd43a8d35b27135957ffea9",
        "0x6d8c32fcf2d95ff410ba492f6694f18cbee55ce1",
        "0x6dc1a070425f437ac08bb108f7093b177d7af3a6",
        "0x6ededbad1e864105fa2538ddfbf4e7214b9e6529",
        "0x6fb624b48d9299674022a23d92515e76ba880113",
        "0x6fd41d4a272247fd1104c710909a4af8bd38f522",
        "0x728d92a8023bfbe0d4f3fdd549ed3b4996a0eba9",
        "0x730df969955c0a2fa9e8f2484e9741a363afdbb3",
        "0x739768219c831ec1f747bf904f0e25c2d99c7dc1",
        "0x767a905b77b0a40801488c6af8b8b5992b43511c",
        "0x778e456fbfd14075f5ddbccf9be2d6a48e3b1ecb",
        "0x7926c83479e2708edfd83a39d62084693e192298",
        "0x793aa889e19a130ee4cb8b63c79aa3bdccc663cb",
        "0x7a91e803db0e58b6fecc4e42c86b366778475e3c",
        "0x7a93539c1bf9a96f87044925deb7a0849266213e",
        "0x7c7061221666e41b87ca5817cfa2fcac09b3d943",
        "0x7cfe28094f4531809992ed89060a61413116365d",
        "0x7d4a2c448fe5b07c62228140417b3565bbe1b86b",
        "0x7eb6c83ab7d8d9b8618c0ed973cbef71d1921ef2",
        "0x7f61dc44c15ca818f96c6fc40739e5aa732e240c",
        "0x7fe830ec109e112f549d6ee9d3e9540e7785997b",
        "0x7fea5b4568751533039179116e372e26b6b41b13",
        "0x80335e658ee73756bb8220bdb77f99e98322035f",
        "0x8167a1ebf00ff5886d1b5908419bb1159d8cf6a4",
        "0x83a32a54d31ee4f1f9dffad2a63a6d214e469ec3",
        "0x85dcd76d4fbd3aa0c85c27b9441222c19a14134b",
        "0x868dab0b8e21ec0a48b726a1ccf25826c78c6d7f",
        "0x86aee064cc073d0dc95ba86633067b2c615040bb",
        "0x8734bca44102bf8a663e1ba112308504606e1b08",
        "0x87d0d6c8cdd71a658ecf1566f13e4cbc562beaf9",
        "0x88c94d8e7d4203b185b3beb0a7b15a6b4f36b2a2",
        "0x89b2f6dafc9d46ce0ed7d7e45a4972d14f037a19",
        "0x8ad740adce08f2f3579884eac0a12e581304ac3b",
        "0x8c3cb9665833fd9f79eb14cba16d82bbab6f22d8",
        "0x8f1aae22d0b4335945950d0bbd0f3743d3fc6f22",
        "0x91d40e4818f4d4c57b4578d9eca6afc92ac8debe",
        "0x92ea7496eba5f001d620005f88f3e8e686e3d4ea",
        "0x932d7d2cbc06234919f34802a22a914282a00f87",
        "0x96fdc631f02207b72e5804428dee274cf2ac0bcd",
        "0x9723b6d608d4841eb4ab131687a5d4764eb30138",
        "0x98ec059dc3adfbdd63429454aeb0c990fba4a128",
        "0x9938ee74ba7a5c1abcd157272a18fcfc9ec9e8d5",
        "0x994d24172fcfafbb5fce0ac5392078fa1c025448",
        "0x9b645675e8d64759e5c36e30dcb766d8cec3d34f",
        "0x9ce5a8098270f07a0a56398febda76a8ee2858c4",
        "0x9d65bf1bce7a10814228f4d81d8cf99a6b0f44aa",
        "0x9db8b860692c41e709d48d089de64cf01e6e317e",
        "0x9e13bae2256f968d02fe0129a0f51788f4e2472f",
        "0x9e3bb2cd5a89fcc4b826230b144c4917881bea85",
        "0xa01533d5c66a4886d3bb39b156507d9de65653e6",
        "0xa2684f75740cfff46c29bae79a4ecc43043c003d",
        "0xa27cef8af2b6575903b676e5644657fae96f491f",
        "0xa68cfe488a785c8b38ce2db6c45cfe07cb620c2d",
        "0xa7efae728d2936e78bda97dc267687568dd593f3",
        "0xa9ac43f5b5e38155a288d1a01d2cbc4478e14573",
        "0xacf961ae22191f0d080497a3a3b427180f18ed67",
        "0xae0cbaba071d58efc278a815b2cb652286e192ff",
        "0xb072b7dc9521d97a3f12b04beb1e497f8875ec52",
        "0xb0a27099582833c0cb8c7a0565759ff145113d64",
        "0xb47a0ac7798d8308467b2b96ac632ed43c9cb6d7",
        "0xb4ec508adeb174610b4295e233a458b3475964f7",
        "0xb640e1e5a5f726a054cd518c968dfdac8c421ee5",
        "0xb8ede418d8116113efb7644a792e5d97aade6138",
        "0xb99cc7e10fe0acc68c50c7829f473d81e23249cc",
        "0xba0a39d37151fa4f938bec51cdae4675105760f4",
        "0xba7fd71d309bc0e96b64022fd8fea7299b256159",
        "0xba96a3f3d5e9f13a5f93c37001f946d42eb2e165",
        "0xbda23b750dd04f792ad365b5f2a6f1d8593796f2",
        "0xbe2ec156292587338d4e9f80f5439e6152d56fc5",
        "0xbf94f0ac752c739f623c463b5210a7fb2cbb420b",
        "0xbfbbfaccd1126a11b8f84c60b09859f80f3bd10f",
        "0xbfef5c888bb7a0a6b14b4c3ccc4364ea81aa573f",
        "0xc0d01a27fd89e6bbc68f43e94ade3dfca2c27674",
        "0xc18475f347cc757b3cc49025820248a5f27d97ce",
        "0xc275bf069df3e63184a1222359114b805b6cd2f5",
        "0xc5267f13b9b4ba7bb73bdd53a2a3c944733a2961",
        "0xc5451b523d5fffe1351337a221688a62806ad91a",
        "0xc5a93444cc4da6efb9e6fc6e5d3cb55a53b52396",
        "0xc6724cf116573eab588fb0d73dcdc16929493cea",
        "0xc68c17e6eec0fde3605c595c9b98de5c1a4cc3e4",
        "0xc708a1c712ba26dc618f972ad7a187f76c8596fd",
        "0xcab0c0a224bad992085430f87dc1855342763a88",
        "0xcb0963264231bb08b2f680ab3ed89a49c9641bb3",
        "0xcba38020cd7b6f51df6afaf507685add148f6ab6",
        "0xcbc767b519394a9e4682cc9a15dcd18c46a6045b",
        "0xcc5d36fb0126515cb7988bbeee8445f03c304b2a",
        "0xcd5bd47d3d1d8412b241ce9015c5032142948c12",
        "0xce9abe75d561f065f1c4adb188b260df9de32ca7",
        "0xd03e6a53a3298ba1cd9b0dbf525ad728f4f8ad6e",
        "0xd049e4ddf1133af3a7a27390b4c9018141df1a49",
        "0xd19d3341227967610b94e7aebe8c971d2d48f419",
        "0xd266529641eeffaa2b2a0bc99daa5b32ef241078",
        "0xd576392cb12b7749ba33f8d223f64e65ee32f03f",
        "0xd5f8c864f21824daf3a4b22d9c33693642ed7634",
        "0xd7764b4305bcca935e38a450e7956822113374b6",
        "0xd7f4a5613b38cb8c09229b7aed99803242fdf0a0",
        "0xd99d81949146b4c13a4a42c9a6addbbd2db932ad",
        "0xd9a3c9ba5aa4415a53b9190bcb00f14472790a70",
        "0xdad24044e36587d975d7b5bceb6467fac21e0c81",
        "0xdb0ed345cb52c2f2457918afa3eb4b682e264ad0",
        "0xdc3ce895714844b4775b6d06f0dae513542cee10",
        "0xdce83237fbf279c4522e7cac4b10428e2b8694da",
        "0xddf81e81ab956695600d8639356c045e5c8a8c94",
        "0xde01974fb4a98bafd7cbf8a06ecf6dcc94d7283f",
        "0xdeb6ad2a7820839464da79bac953ae6189215443",
        "0xe2effe5bd0617a5a2dc1ee579565911cef3a223b",
        "0xe3bb282457ce7b3be31f0441f3fc051b9fc6a9c3",
        "0xe404fe9b7b0d0e88e77731517202fb392f67cd74",
        "0xe6eea9812ccc5981ccf0ab333610c42c2d92d146",
        "0xe7b29ff45392876143c7b863d57fb2326afe0ff1",
        "0xe7c8fdd899ab06ac1023e8a3e867c5fa7e751450",
        "0xe9172daf64b05b26eb18f07ac8d6d723acb48f99",
        "0xe983845a04c681a295dd9ce1fa8c2c8505932da3",
        "0xea3b7dac6b96502a04c701d5e71b51912f70143f",
        "0xeaed6576334b003d1c5c4797d9c7bb025a20c038",
        "0xeb196a61f9a1e35bf5053b65aaa57c5541dcba86",
        "0xedc0a430dd32eb8cfcc3a344979f0e21bc48bf0d",
        "0xee1c6537e589a15a15f80961f5594c57bed936fb",
        "0xf02e3c0095f6de36c76364d4cc53eb06d1288fc1",
        "0xf418263a6468c80d3bcb71033c56aacf81b241ba",
        "0xf59869753f41db720127ceb8dbb8afaf89030de4",
        "0xf683b33e21e85ee6c0e25af2fff5b2b115f32617",
        "0xf7858da8a6617f7c6d0ff2bcafdb6d2eedf64840",
        "0xf7b17e0b2478ad21ac594e4b0954ece63d059064",
        "0xf7c63e75b90c60d7b343106a39658f8b3ca6e4d2",
        "0xf8b4256122369c48eb8c3d901875d62458a675e8",
        "0xfa13971666d0e6f2715d68eb44bb7964fc22b14b",
        "0xfad70cb84e104817a7e9345d25ed0d3048af2d2d",
        "0xfcb21730ac0cd487d8701dfed1170e023b57cf7a",
        "0xfe908731af54c56dfd63948f18ce5878a3b8a1ad"
      ],
      "mention": {
        "end": 21,
        "start": 18,
        "text": "OKX"
      },
      "owner": "OKX"
    }
  ],
  "id": "v2-m02",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "597513c24cce1dad039950ccc824be6f5bb28bf0d4ca1da712bfda26ad12e29c",
  "schema": {
    "columns": [
      {
        "column": "receipt_gas_used",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "transaction_type",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "a7fa4cade7cdbc688ac73c5625d79f1f7e054b28671e84ff826082b3c04a45f4"
}
```

Lý do tác giả: Receipt gas summarizes outer calls to the full owner address set.

Sample: 2 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "0"
    ],
    [
      "number",
      "5"
    ],
    [
      "number",
      "105000"
    ]
  ],
  [
    [
      "number",
      "2"
    ],
    [
      "number",
      "2742"
    ],
    [
      "number",
      "68061682"
    ]
  ]
]
```

Multi-address: 20/226 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "d8d5dc0eafa245b4044d07f89650404e2d66c9d49a61b5fdf1decdf2be5d638b",
  "case_sha256": "abf65f92b4129cc1b04242c08c5b206d0159eee59d628608b0397b9d9cf1ff2e",
  "id": "v2-m02",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "597513c24cce1dad039950ccc824be6f5bb28bf0d4ca1da712bfda26ad12e29c",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "a7fa4cade7cdbc688ac73c5625d79f1f7e054b28671e84ff826082b3c04a45f4",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m03 — multi_address

Pool the known Bitfinex sender addresses and give each active date's outgoing outer transaction count and sum of declared wei value, ordered by date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "bitfinex_outbound_daily_declared_value"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:bitfinex_outbound_daily_declared_value",
  "id": "v2-m03",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `bitfinex_outbound_daily_declared_value`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS n, SUM(value_wei) AS declared_wei
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_owner='Bitfinex' GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x742d35cc6634c0532925a3b844bc454e4438f44e",
        "0x77134cbc06cb00b66f4c7e623d5fdbf6777635ec",
        "0x876eabf441b2ee5b5b0554fd502a8e0600950cfa",
        "0xc61b9bb3a7a0767e3179713f3a5c7a9aedce193c"
      ],
      "mention": {
        "end": 23,
        "start": 15,
        "text": "Bitfinex"
      },
      "owner": "Bitfinex"
    }
  ],
  "id": "v2-m03",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "fb6ecb363ab95e86711fd92d79bdbc61657ad30a6e6c84fdfd6eed5af32cfd26",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "value_wei",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "af723a9624175a639bf7fae503652db057ae9aa869dccaa71036486ce3a63eff"
}
```

Lý do tác giả: All outcomes retained; declared value is not claimed to be realized ETH flow.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "298"
    ],
    [
      "number",
      "11410392730600000000000"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "413"
    ],
    [
      "number",
      "313029585165720000000000"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "433"
    ],
    [
      "number",
      "99529690528300000000000"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "420"
    ],
    [
      "number",
      "164096712978670000000000"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "421"
    ],
    [
      "number",
      "59468840689110000000000"
    ]
  ]
]
```

Multi-address: 2/4 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "90aa31e045caf2af5fc450a27416553e111962ec13deb243a454d2dfbed9487b",
  "case_sha256": "26f7137658803f75d3b488bf87119cc8964f1189931872e308f28d50a3cffb95",
  "id": "v2-m03",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "fb6ecb363ab95e86711fd92d79bdbc61657ad30a6e6c84fdfd6eed5af32cfd26",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "af723a9624175a639bf7fae503652db057ae9aa869dccaa71036486ce3a63eff",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m04 — multi_address

Treat every known KuCoin recipient address as one group. Return incoming outer transaction count and the number of distinct senders across that group. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "kucoin_inbound_sender_reach"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:kucoin_inbound_sender_reach",
  "id": "v2-m04",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `kucoin_inbound_sender_reach`. Property focus: `None`.

```sql
SELECT COUNT(*) AS incoming, COUNT(DISTINCT from_address) AS senders
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='KuCoin'
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x04f2abb57b53122eb0306418f2220746d06af9fc",
        "0x061f7937b7b2bc7596539959804f86538b6368dc",
        "0x06679e7b7f91487cc9d59779501c414a1b3eb89d",
        "0x0669bcdc8ede4a973ed9b3480aff984de15d2d65",
        "0x0c32131b67a9306a42e5b66f869bc213d40e43f0",
        "0x0f1836312d18524368d05d537c0fabaff6ca6ccc",
        "0x0f75e66731ca8ab3471503562ff964cd40741f41",
        "0x10affefb7ce337348e0b258fffc6a1d5745c2be9",
        "0x10c3d6ef33446e51b6d5c70970f7ad71cc1f42be",
        "0x1136a49f3a1e3a3b6b2b6de30f8244d16f18509a",
        "0x1692e170361cefd1eb7240ec13d048fd9af6d667",
        "0x175ce6204bfda2a509c7e9c786b74407f569c9cc",
        "0x189b24f3eb15dc71b4fc57c5914e7e9b3246e449",
        "0x1b14376ee2d46ae5c27a43d902d96d4f3f264b83",
        "0x2677c4c8757da1857cc7cc4071e0e0dd32ccb975",
        "0x2933782b5a8d72f2754103d1489614f29bfa4625",
        "0x2c73858225cfbf15fd1b71ff27d006cb96c57e27",
        "0x37e4d1cd3fe31edf473ebcf3b6a75f419c8839d1",
        "0x3b6d76719a4ea8c53a7a26b50175b8de23c8e956",
        "0x41e29c02713929f800419abe5770faa8a5b4dadc",
        "0x4316e553902c3eab807663001d089fd6554a4566",
        "0x441454b3d857fe365b7defe8cb3e4f498ec91eac",
        "0x446b86a33e2a438f569b15855189e3da28d027ba",
        "0x44f1b02d78ed39962600df6440cf8eed3e02a96b",
        "0x45300136662dd4e58fc0df61e6290dffd992b785",
        "0x4a1dffc4e4168fd436dd9d9fb8edb223fa259a68",
        "0x58edf78281334335effa23101bbe3371b6a36a51",
        "0x5b234aaab0f61d346a3ef8faca474c1c19f80c1f",
        "0x651f1d419c548125d7e5456fb61f3df47c29600d",
        "0x69be413d648ae00f0fbd9856f1355e22b36ee5e0",
        "0x6d6cc65e2060d0a280fcd47b6c22ec5636797fec",
        "0x738cf6903e6c4e699d1c2dd9ab8b67fcdb3121ea",
        "0x7491f26a0fcb459111b3a1db2fbfc4035d096933",
        "0x77f59b595cac829575e262b4c8bbcb17abadb33a",
        "0x7b915c27a0ed48e2ce726ee40f20b2bf8a88a1b3",
        "0x7ebfa8b1161e66fffec05d7edbb55e1a2c2aebd6",
        "0x83c41363cbee0081dab75cb841fa24f3db46627e",
        "0x85cef5c097a4df05d27c9fa1a1c1fe16fe691e60",
        "0x88bd4d3e2997371bceefe8d9386c6b5b4de60346",
        "0x8dac80ce96f69f9762bc450faa4d7fbd5891ae18",
        "0x9f4cf329f4cf376b7aded854d6054859dd102a2a",
        "0xa152f8bb749c55e9943a3a0a3111d18ee2b3f94e",
        "0xa2d69adf0b62fa32825d73f086cd4689743543db",
        "0xa649ffc455ac7c5acc1bc35726fce54e25eb59f9",
        "0xaa10db8804d076601999c7cd769e02e44a99d5b2",
        "0xaa99fc695eb1bbfb359fbad718c7c6dafc03a839",
        "0xb514c67824443868d3a70352398f524ef6af6207",
        "0xb8e6d31e7b212b2b7250ee9c26c56cebbfbe6b23",
        "0xbee64116bd2b1b6373273d01664fbc5532dad06d",
        "0xcad621da75a66c7a8f4ff86d30a2bf981bfc8fdd",
        "0xce0d2213a0eaff4176d90b39879b7b4f870fa428",
        "0xd6216fc19db775df9774a6e33526131da7d19a2c",
        "0xd89350284c7732163765b23338f2ff27449e0bf5",
        "0xd91efec7e42f80156d1d9f660a69847188950747",
        "0xdd276dc5223d0120f9bf1776f38957cc8da23cb0",
        "0xe4507d13b059eaf66f7b509b6929f7295690d7cc",
        "0xe8c15aad9d4cd3f59c9dfa18828b91a8b2c49596",
        "0xec30d02f10353f8efc9601371f56e808751f396f",
        "0xf16e9b0d03470827a95cdfd0cb8a8a3b46969b91",
        "0xf8da05c625a6e601281110cba52b156e714e1dc2",
        "0xf97deb1c0bb4536ff16617d29e5f4b340fe231df"
      ],
      "mention": {
        "end": 24,
        "start": 18,
        "text": "KuCoin"
      },
      "owner": "KuCoin"
    }
  ],
  "id": "v2-m04",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "e0c9617c142d68e89de47f375be47be638b92412117586ecb562685559266787",
  "schema": {
    "columns": [
      {
        "column": "from_address",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "1f8769bce09547e22158ec841c43af2e630831063c05b388596e7c82cbe97803"
}
```

Lý do tác giả: Distinct sender count is computed after owner union, not summed across wallets.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "19366"
    ],
    [
      "number",
      "5090"
    ]
  ]
]
```

Multi-address: 18/61 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "5d2edb0a043fbed45fa2c6d9c9173e9e8c9f2e0da75414a26b1831ef06cdc087",
  "case_sha256": "174888a9ef91e5864c3ba7587bf1b2633f447082cefcbe8922831ba3eb88d492",
  "id": "v2-m04",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "e0c9617c142d68e89de47f375be47be638b92412117586ecb562685559266787",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "1f8769bce09547e22158ec841c43af2e630831063c05b388596e7c82cbe97803",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m05 — multi_address

For the union of known Binance sender addresses, report outgoing outer transaction count, distinct non-null recipients and the largest declared wei value. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "binance_outbound_recipient_reach"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:binance_outbound_recipient_reach",
  "id": "v2-m05",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `binance_outbound_recipient_reach`. Property focus: `None`.

```sql
SELECT COUNT(*) AS outgoing, COUNT(DISTINCT to_address) AS recipients,
    MAX(value_wei) AS largest_wei FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_owner='Binance'
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x030e37ddd7df1b43db172b23916d523f1599c6cb",
        "0x110daa3f3fac2a54bb508ac94f31f9df77057b29",
        "0x150aace136535a374f05b5ee209b6a61396db1c0",
        "0x18e226459ccf0eec276514a4fd3b226d8961e4d1",
        "0x1b46970cfe6a271e884f636663c257a5a571fb2c",
        "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        "0x22132139bf7f3921b1cadeab931f4fbf7bf2bc9e",
        "0x26bff98f6f37c8d560684eaf2afd1149bf76633e",
        "0x28c6c06298d514db089934071355e5743bf21d60",
        "0x308a2a0712570daeea77c8ba9c27a32cdc4000d4",
        "0x32e11a20337ebc79abd0eeab2d91bafbd9591149",
        "0x38aaef3782910bdd9ea3566c839788af6ff9b200",
        "0x42a93a9f5cfda54716c414b6eaf07cf512f46ead",
        "0x43684d03d81d3a4c70da68febdd61029d426f042",
        "0x4976a4a02f38326660d17bf34b431dc6e2eb2327",
        "0x4aec0e98fc1fb55b9cc2faaa7a81acca42cb4e96",
        "0x4ed6cf63bd9c009d247ee51224fc1c7041f517f1",
        "0x4fdfe365436b5273a42f135c6a6244a20404271e",
        "0x56eddb7aa87536c09ccc2793473599fd21a8b17f",
        "0x5a1e5b56aa33c056ed7bb93b88b1774a456f6694",
        "0x5a52e96bacdabb82fd05763e25335261b270efcb",
        "0x6357e4bdaff733dfe8f50d12d07c03b3bed0884b",
        "0x6454ac71ca260f99cca99a3f4241dfda20cfa965",
        "0x756b86fd69914db92229c07c7393d7d9948fed33",
        "0x835678a611b28684005a5e2233695fb6cbbb0007",
        "0x8498fc7280668874a5da79e87ca0896f4f0d1196",
        "0x86523c87c8ec98c7539e2c58cd813ee9d1a08d96",
        "0x87433fec6f8d9df13d1e17c4b11364ecd2e93a51",
        "0x8a6f8404c9ea4c33502a3f6a4bf8e41ef5ca10ea",
        "0x8e609ac80f4324e499a6efd24f221a2caa868224",
        "0x9696f59e4d72e237be84ffd425dcad154bf96976",
        "0x98adef6f2ac8572ec48965509d69a8dd5e8bba9d",
        "0xa345dcb63f984ed1c6d1a8901e0cdbd13b2b4d19",
        "0xa64b436964e7415c0e70b9989a53e1fb9a90e726",
        "0xa7c0d36c4698981fab42a7d8c783674c6fe2592d",
        "0xa9fc92f6faf9f103fc81d17de3e8daadc888afff",
        "0xad354cfbaa4a8572dd6df021514a3931a8329ef5",
        "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",
        "0xc47b3342df38d747033b6041f54e4e5e300c8d18",
        "0xc8daf809c7d7c27dd62d006196d8901ba57e5eae",
        "0xd27b39cb25fed854f9fce3a4e451f96e62089e48",
        "0xdbeb6c856ef5a167f5e1acb9dff65adb33207d8b",
        "0xdbf28a152d79b2b98eecd229b412ee98d21ec3bc",
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
        "0xe1940f578743367f38d3f25c2d2d32d6636929b6",
        "0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055",
        "0xf16924b866e58ac916ba933d1f1034bcbbb1958c",
        "0xf1f8cb7633d3ca3fd06c084d18ca5491a85ae9b4",
        "0xf977814e90da44bfa03b6295a0616a897441acec",
        "0xfc8059c2fb22005ede8a86d388e3d0f536a4dd44"
      ],
      "mention": {
        "end": 30,
        "start": 23,
        "text": "Binance"
      },
      "owner": "Binance"
    }
  ],
  "id": "v2-m05",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "562d9f09859b776b617427f1bb0c63648837ed170e76af316285abc9619defb9",
  "schema": {
    "columns": [
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_address",
        "relation": "labeled_transactions"
      },
      {
        "column": "value_wei",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "4f12f0cbfc73fb8f4b32284bd4dffc258ff5c27f92447565caf01f6b00c1518f"
}
```

Lý do tác giả: Includes creation transactions in count; their NULL recipient is excluded by DISTINCT.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "275879"
    ],
    [
      "number",
      "3746"
    ],
    [
      "number",
      "14862393669420000000000"
    ]
  ]
]
```

Multi-address: 16/50 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "f8ba3e589a6e3e6181e0a57d0a2217d45be06d568f0aeacbc6421576f32cec7f",
  "case_sha256": "42cde1247badd2c447fbcd687f6c029c3163835f90fa67e3bc800f961519b900",
  "id": "v2-m05",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "562d9f09859b776b617427f1bb0c63648837ed170e76af316285abc9619defb9",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "4f12f0cbfc73fb8f4b32284bd4dffc258ff5c27f92447565caf01f6b00c1518f",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m06 — multi_address

Using all known Bybit recipient addresses, split incoming outer transaction rows into zero and nonzero declared wei values, and return the total alongside those counts. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "bybit_inbound_zero_value_split"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:bybit_inbound_zero_value_split",
  "id": "v2-m06",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `bybit_inbound_zero_value_split`. Property focus: `None`.

```sql
SELECT COUNT(*) AS total, COUNTIF(value_wei=0) AS zero_value,
    COUNTIF(value_wei<>0) AS nonzero_value FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Bybit'
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x01e2fb8f565d5e3cb9e0e8f0b607a96169b94393",
        "0x076d55c8998da29531ef7fcac2a01fa21582eed2",
        "0x0ac92eb5716516a08e7760d314d42e1d5d3c03ae",
        "0x13f52026493dccf09065952d44101c3e42b41dda",
        "0x180a1b935d28494f9ff4233985562b18b3dcfa74",
        "0x18673311fec54ac2244a602e6d91845553d24e62",
        "0x187c9fbf5bd0f266883c03f320260c407c7b4100",
        "0x18e296053cbdf986196903e889b7dca7a73882f6",
        "0x1c3944173abee256456b1498299fc501ad5bbd6f",
        "0x1db92e2eebc8e0c075a02bea49a2935bcd2dfcf4",
        "0x223fea5291d43a2fb372c5f332e9ade371ded0b5",
        "0x25c76fa90e90f5a5a6914da07baed9a9647c3dfd",
        "0x25c7d768a7d53e6ebe5590c621437126c766e1ea",
        "0x260b364fe0d3d37e6fd3cda0fa50926a06c54cea",
        "0x2ebf891f4718eb8367013d8d975a1e5afcae277f",
        "0x30ba21597f22aafa4b0e86c250c8a6eebaf0da54",
        "0x33ae83071432116ae892693b45466949a38ac74c",
        "0x35696b0847ed8428a098cba726b6514582aa5fc7",
        "0x35bf33df55472938ad314678962b7c69204f0a8a",
        "0x36cf90ac2d130b987aff0bded378525be36d9686",
        "0x371c31f9221459e10565cfe78937cbda5db1791c",
        "0x3bd0e57e2917d3d9a93f479b3a23b28c3f31a789",
        "0x3cef1f90be0f15f1573bda7a3e045cca9cff1d15",
        "0x3db4cb6d753d9e0ba7cc84e576d17dcd01b6b67d",
        "0x3ef28b7e18c510b8fa031d7f8a1bb24a83ccceb0",
        "0x412dd3f282b1fa20d3232d86ae060dec644249f6",
        "0x41be1bae9815d86820bcfd94a5161000fab448a6",
        "0x429b41e5eb73e2266affbc2d7a41553bd8f1ede1",
        "0x448c642074d7be4c5fc25929bb5536f772cd9d5c",
        "0x4865d4bcf4ab92e1c9ba5011560e7d4c36f54106",
        "0x495c70e181c45f80806dcbd733140361a0f75cc2",
        "0x495eb9345788ee6be50c9c36ed67ffa2beb3699f",
        "0x4be65e82a07b05686b092aa7d4426ce8ecd70ddc",
        "0x4ce053dfe58541e08f149c1050eb3df09d7a40bc",
        "0x4e19698c366f7dcd1cfad4d7f621b4d275bb1a6c",
        "0x4e5e17e8ef17c9a7ef9798ddf78f3a2c38367d16",
        "0x554e61af48afb53bd28670c3a2aa14ce858e63dd",
        "0x5a076b2d0941f2bc9b49d05d3a1ff9c7acdc5e78",
        "0x5c4e79cc7d5b66effcbb19e22cae0c92bff7276d",
        "0x61b2aa17c1c1114e7583bb31f777ff4bdc7ab717",
        "0x6206ae3781f9f1b6fbcf44c7240b1be14f3169ef",
        "0x62425cd6bdcb6bfe51558ea465b063486b70dc9f",
        "0x63bee4a7e4aa5d76dc6ab9b9d1852aabb9a40936",
        "0x651641299c7ec0aa44ad7ed9b7e12702fed2022f",
        "0x6522b7f9d481eceb96557f44753a4b893f837e90",
        "0x695f7dea85bf8c0aaafef0a9484e74834e28ce8b",
        "0x6b9b774502e6afaafcac84f840ac8a0844a1abe3",
        "0x6bd869be16359f9e26f0608a50497f6ef122ee3e",
        "0x6f4565c9d673dbdd379aba0b13f8088d1af3bb0c",
        "0x70167b76543c4a12b49b2f2b70cbf04d99345786",
        "0x70f58622158d7e609ae5839c4ad0d477f468863f",
        "0x72187db55473b693ded367983212fe2db3768829",
        "0x77439637cac35bedd63fc9e769d7819ca1d24a48",
        "0x79ae8c1b31b1e61c4b9d1040217a051f954d4433",
        "0x7a84c1f1aa344d466b0f161f57b0321b98faf6ee",
        "0x7c41c7d883dbbe1edfcefca9d7a7592dd30c8b51",
        "0x7e8c73462aaa9d61c801bd9f5682db014387621a",
        "0x801bfd99636ec8961f7e2d2dd0a296d726f5f1ae",
        "0x80a9b4aab0ad3c73cce1c9223236b722db5d6628",
        "0x80d45515a84e762c6497a089913f26b41235bf65",
        "0x855e9a74196764ab41adb3e3b76eaf9e3d6d6d48",
        "0x869bcee3a0bad2211a65c63ec47dbd3d85a84d68",
        "0x86dbaa55f0e65857b58109c3cb725deff4da3851",
        "0x8859eb340330492cb66f3b193e22696de8251e66",
        "0x88a1493366d48225fc3cefbdae9ebb23e323ade3",
        "0x89688768bf9e2e809ca3ac7e22fe5d2f849ef822",
        "0x8a2458f32e5ec9935f20e7c2e06e8d4820f726e5",
        "0x8c28e696c89200d423f9a5eea7347747e78ed25f",
        "0x8d6d3479c94bb95e737b72186192ff5e7fedf3a2",
        "0x8ed5b6bc3d85be31209fac182466e0bcc30ba3eb",
        "0x8fa129f87b8a11ee1ca35abd46674f8b66984d4a",
        "0x922fa922da1b0b28d0af5aa274d7326eaa108c3d",
        "0x93228d328c9c74c2bfe9f97638bbb5ef322f2bd5",
        "0x933646d78ede6f1ef5cf4a0a03e3a819c8057922",
        "0x9814ba501c7ad64bed5ac731d0a4f9a506e18f8a",
        "0x9cdb59516b37f5c1bd166bc41c5b9f68a57225bd",
        "0xa1abfa21f80ecf401bd41365adbb6fef6fefdf09",
        "0xa2e5e8a607562b7bda05d5820e569c290b43be6d",
        "0xa31231e727ca53ff95f0d00a06c645110c4ab647",
        "0xa4287bc8a021025974a642806cf2ab717b857380",
        "0xa4b9569bf942c3aad23c0c2d322fe4aff8e1bf30",
        "0xa7a93fd0a276fc1c0197a5b5623ed117786eed06",
        "0xa9acc15d8b74a01e5605eb0f1e815ba98e3a16af",
        "0xa9cf4aa55c675badb68519e3cfa8f4be942e6d11",
        "0xab97925eb84fe0260779f58b7cb08d77dcb1ee2b",
        "0xad85405cbb1476825b78a021fa9e543bf7937549",
        "0xb24692d17babefd97ea2b4ca604a481a7cc2c8ea",
        "0xb5873e333161e5b45adac57379ec2b15d861178d",
        "0xb829e684df8e31b402a4d4aedf3bbc18a52e7589",
        "0xbaed383ede0e5d9d72430661f3285daa77e9439f",
        "0xbce9aecd3985d4cbb9d273453159a26301fa02ef",
        "0xc22166664e820cda6bf4cedbdbb4fa1e6a84c440",
        "0xc273a2e3fc4c8f8610ebe51123dc32d233913da7",
        "0xc63fe58d36bef77a9a98df32a547537f45aac71d",
        "0xc6c6a48ee8e9f593724161c72414d76e94cda93f",
        "0xc93e48d89f2d6dbc1672908aa68ce7c24d0413b4",
        "0xcab3f132a11e5b723fc20ddab8bb1b858d00a8e8",
        "0xcacc7e55d0a4b10daaed40b3db7bfe11d23b6f94",
        "0xcf4b3a3be828b111eee75a0534a988c8d9284aae",
        "0xd07e6ab4b75b3da5a96b5e81064a65fc04f98814",
        "0xd4d2e6ebca6c94dd28a0935ae468012fdda5d35a",
        "0xd7c4d4b3f076bf9fe391190c42676b4dc269ee02",
        "0xd860962a96cd471bbe60a83c33e65011d40eb65f",
        "0xdae4fdcb7fc93738ec6d5b1ea92b7c7f75e4f2f6",
        "0xdba34cfc849738b2075fd28446902d3f1689c09d",
        "0xe1ab8c08294f8ee707d4efa458eab8bbeeb09215",
        "0xe46620553d6b28e5d2520b366942990d8654f243",
        "0xe5791f93b997c7fc90753a1f2711e479773a2a87",
        "0xec949f12a3acab835f3eed8b54b7361a8fbb3ee0",
        "0xee5b5b923ffce93a870b3104b7ca09c3db80047a",
        "0xee6281d94fed46a90379f2033b6bbdcda4ef462e",
        "0xefef30bd1cca520619306c95091ab18473febc5c",
        "0xf2f40c3bb444288f6f64d8336dcc14dbd929fd94",
        "0xf358d867bf928cb06408ff2b7564fce336e24de8",
        "0xf42aac93ab142090db9fdc0bc86aab73cb36f173",
        "0xf440139a62b2b939699c5b3e09f88e40464ab9bc",
        "0xf833685f98eba1b99947d418c9512d27c8193b1a",
        "0xf89d7b9c864f589bbf53a82105107622b35eaa40",
        "0xf8f061cfc030928a4acb8c4980911b4f5afc4002"
      ],
      "mention": {
        "end": 21,
        "start": 16,
        "text": "Bybit"
      },
      "owner": "Bybit"
    }
  ],
  "id": "v2-m06",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "2b1f2c2106daaaa57ccf30ac645fedc6f7810916bd3ece30ceff5c458f247c37",
  "schema": {
    "columns": [
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "value_wei",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "fa512c67e0ab9225cbddc54619bf326ff633cf5679b06da071f235dfd508bb2f"
}
```

Lý do tác giả: Owner address union is essential even for zero-value outer calls.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "26151"
    ],
    [
      "number",
      "25"
    ],
    [
      "number",
      "26126"
    ]
  ]
]
```

Multi-address: 22/119 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "309e932a2fbbc64b4879e25e0bf8058e0cd62f6514cd33eab9abfaac55eaa68b",
  "case_sha256": "3a9823bc3a2589007e3ec042ce5447c74cbf0f2bddc67526308a0bbf3224632b",
  "id": "v2-m06",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "2b1f2c2106daaaa57ccf30ac645fedc6f7810916bd3ece30ceff5c458f247c37",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "fa512c67e0ab9225cbddc54619bf326ff633cf5679b06da071f235dfd508bb2f",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m07 — multi_address

Combine known Gate.io senders and rank non-null recipient addresses by outgoing outer transaction count. Return twenty recipients with count and average receipt gas, breaking count ties by address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "gate_outbound_counterparty_ranking"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:gate_outbound_counterparty_ranking",
  "id": "v2-m07",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `gate_outbound_counterparty_ranking`. Property focus: `None`.

```sql
SELECT to_address, COUNT(*) AS n, AVG(receipt_gas_used) AS average_gas
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_owner='Gate.io' AND to_address IS NOT NULL
    GROUP BY to_address ORDER BY n DESC, to_address LIMIT 20
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0d0707963952f2fba59dd06f2b425ace40b492fe",
        "0x0fc73ffb9a0ded685234428e103d26b3762df460",
        "0x1c4b70a3968436b9a0a9cf5205c787eb81bb558c",
        "0x1f92332145465f3e536b7be301dde8d420478387",
        "0x234ee9e35f8e9749a002fc42970d570db716453b",
        "0x246a2ecd9626f9eda55fffbff5216ed417a904f5",
        "0x287a66c7d9cba7504e90fa638911d74c4dc6a147",
        "0x2bea9375c50f41f828c4e8eb0da3194449b5f062",
        "0x2cc81b80a293408a89084c77a0983de0730f731a",
        "0x354e0184a6a6e634ccb07388e2617e05e427563c",
        "0x356b9e62b20f4666e914fb99a9f651e5574f2bf7",
        "0x35b31ae2604dd81d9456205025ea02418dba8242",
        "0x37e1bf9ab62e523f358dafaca86151519f0a2f8d",
        "0x444c55075086f531a1c02730f41c46b9bbb00a39",
        "0x4bbe1961bd0a6cd1fe3cd8947be15bd8ae2ee562",
        "0x54c82d26624e85000d1387ee7c9580c3c6d7b5b7",
        "0x60618b3c6e3164c4a72d352bde263a5d15f9f7ee",
        "0x6596da8b65995d5feacff8c2936f0b7a2051b0d0",
        "0x66bbafc7269f1a9e5b454445585275f2b4ead28e",
        "0x68cdf5d77e75515edf7aa564d36fe3cbe751226e",
        "0x76bbb8d5dbedde9cb34882c9588dfa9def00b8bc",
        "0x7750fe679d47a9e00575ad46043297a234e83fa2",
        "0x7793cd85c11a924478d358d49b05b37e91b5810f",
        "0x7a3f9b7120386249528c93e5eb373b78e54d5ba9",
        "0x840760aed6bbd878c46c5850d3af0a61afcd09c8",
        "0x85faa6c1f2450b9caea300838981c2e6e120c35c",
        "0x8cd6437feaeb1a3a0cd65a16de2ad26bff1f5e43",
        "0x9bbe47fe66b3580551aac3124cf9fc6560252b19",
        "0x9f1daa35a4ef099c03744dfe3e67a39c4697ebe5",
        "0xa10eca918c71806ac55083d8ac942d4674b0f9ef",
        "0xa2df23519a6059dbc6f027f6cf8e59bdaecaf56f",
        "0xa2f10222b338c9ff3c953b129d1a49258f83f6c7",
        "0xa4992ccf2a74132936b87cbf28b5d52304ba3be7",
        "0xaaac1183d07c69f5befd22a06211690e953dca17",
        "0xb11c93f04bb7cc8d2d4aba47fcf73170bcea940d",
        "0xbcf03ce48091e6b820a7c33e166e5d0109d8e712",
        "0xc882b111a75c0c657fc507c04fbfcd2cc984f071",
        "0xccc5eeebe15291620be733997af60735618548d7",
        "0xcf6f5ec73942314c3ec864202b40dcbb1f9477a0",
        "0xd6a8047940a1f71df5f809919c10d9ba0a88786e",
        "0xd793281182a0e3e023116004778f45c29fc14f19",
        "0xd87c8e083aecc5405b0107c90d8e0c7f70996b84",
        "0xe39ba3f5bcbf0ef7ed31a07e799b8d2010c885cf",
        "0xf379a3d1ab6625eef34347d054cfaeafdf8f24a7",
        "0xffeb0f61871acdb4838dfc6d5082f063e738e421"
      ],
      "mention": {
        "end": 21,
        "start": 14,
        "text": "Gate.io"
      },
      "owner": "Gate.io"
    }
  ],
  "id": "v2-m07",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "71e31256926b8a784cc72fd8ffaca75e0601af3d1728b873fc203bd38e7edd1d",
  "schema": {
    "columns": [
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "receipt_gas_used",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_address",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "e8d2e80284e17808e6f1448ce94a3d1293a975c3d6730ce0f793af58298a9828"
}
```

Lý do tác giả: Counterparty ranking aggregates all owner sender addresses before limiting.

Sample: 20 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0xdac17f958d2ee523a2206206994597c13d831ec7"
    ],
    [
      "number",
      "24660"
    ],
    [
      "number",
      "55080.460340632606"
    ]
  ],
  [
    [
      "string",
      "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    ],
    [
      "number",
      "4336"
    ],
    [
      "number",
      "53985.362084870845"
    ]
  ],
  [
    [
      "string",
      "0xcf5104d094e3864cfcbda43b82e1cefd26a016eb"
    ],
    [
      "number",
      "3183"
    ],
    [
      "number",
      "47787.23845428841"
    ]
  ],
  [
    [
      "string",
      "0xaf5191b0de278c7286d6c7cc6ab6bb8a73ba2cd6"
    ],
    [
      "number",
      "1942"
    ],
    [
      "number",
      "43679.06282183316"
    ]
  ],
  [
    [
      "string",
      "0x232ce3bd40fcd6f80f3d55a522d03f25df784ee2"
    ],
    [
      "number",
      "1763"
    ],
    [
      "number",
      "42339.47589336358"
    ]
  ]
]
```

Multi-address: 7/45 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "5bc5e03282a15a8fb2d58a938e52f4e43f708cbfa03a2083f64d0d7e29f2b0b9",
  "case_sha256": "41f6a1be11b5a26f806d1b8406f98cb7f2b78bed1319cf909e229a3aada886bc",
  "id": "v2-m07",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "71e31256926b8a784cc72fd8ffaca75e0601af3d1728b873fc203bd38e7edd1d",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "e8d2e80284e17808e6f1448ce94a3d1293a975c3d6730ce0f793af58298a9828",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m08 — multi_address

Merge known Bitget recipient addresses and count incoming outer transactions by UTC hour of day, returning hours in order. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "bitget_inbound_hour_histogram"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:bitget_inbound_hour_histogram",
  "id": "v2-m08",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `bitget_inbound_hour_histogram`. Property focus: `None`.

```sql
SELECT EXTRACT(HOUR FROM block_timestamp AT TIME ZONE 'UTC') AS hour, COUNT(*) AS incoming
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Bitget' GROUP BY hour ORDER BY hour
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0635ac6675e05c7f58383493bb7d1a513cd65688",
        "0x0639556f03714a74a5feeaf5736a4a64ff70d206",
        "0x0edd5b0de0fe748be331186bf0aa878f47f601db",
        "0x14b5f559c27bc00c39f668a88471498d68d18768",
        "0x1a96e5da1315efcf9b75100f5757d5e8b76abb0c",
        "0x1ab4973a48dc892cd9971ece8e01dcc7688f8f23",
        "0x1ae3739e17d8500f2b2d80086ed092596a116e0b",
        "0x1d5ba5414f2983212e03bf7725add9eb4cdb00dc",
        "0x1d774ed0a7b897aaae3526f07e487c5f9540f55d",
        "0x255e91ab794da40d39a5aceff20d98841df873af",
        "0x26209d9f0dc3ac0129c3fb1badabfeb9ee728c66",
        "0x2bf7494111a59bd51f731dcd4873d7d71f8feeec",
        "0x2dd64ee5ea8706097a5674154288989e3dbe3a05",
        "0x31a36512d4903635b7dd6828a934c3915a5809be",
        "0x3c2a309d9005433c1bc2c92ef1be06489e5bf258",
        "0x4121217c238db06e942f3d87371106d30d0f8c84",
        "0x461f6dcdd5be42d41fe71611154279d87c06b406",
        "0x4c1d7de286d7c20df5f2ba44b3bc706c1e03bf13",
        "0x4d216d2682f3997f6c19420beee4530d08d0ea5f",
        "0x4dfc15890972ecea7a213bda2b478dabc382e7a1",
        "0x5051e9860c1889eb1bfa394365364b3dd61787f1",
        "0x51971c86b04516062c1e708cdc048cb04fbe959f",
        "0x54a679e853281a440911f72eae0e24107e9413dc",
        "0x58751ce78f174b58b8f5e345244984a78524a899",
        "0x59708733fbbf64378d9293ec56b977c011a08fd2",
        "0x5bdf85216ec1e38d6458c870992a69e38e03f7ef",
        "0x70213959a644baa94840bbfb4129550bceceb3c2",
        "0x731309e453972598ea05d706c6ee6c3c21ab4d2a",
        "0x80097a87a7dcde470e34c10b5cceb85abf83b531",
        "0x8028270e06fca18e212306a7c93bfee52b440fc5",
        "0x842ea89f73add9e4fe963ae7929fdc1e80acdb52",
        "0x95ccca6d1859ae5670c2213940c96dcb2e177fcb",
        "0x9756b4eedc434ca23dffd209c8ea01d4c95ff881",
        "0x97b9d2102a9a65a26e1ee82d59e42d1b73b68689",
        "0x9a449ef3665f60af503ea5b8ef5191aeb315b809",
        "0x9c9c8f4f33679ce7f2c46cbf8ab4feb4cf45fe46",
        "0x9e00816f61a709fa124d36664cd7b6f14c13ee05",
        "0x9f199b93ae33c330880bdb31422fca37c6d3fb14",
        "0xa700c091687afbfada6b84b5e02a5e672ee35597",
        "0xaab0039de2a8dba8696ee4d42c0d1aa30d7e1059",
        "0xac65bdf867103ae2c3a75cdd4b68f9d7178c604f",
        "0xadfffc33cdc9970349cbcea3d73ec343d6ed116d",
        "0xbff5092f83bd810e0926068b89633bf66eaa037b",
        "0xd509ff5d6e530401b53cc7d3b80607824d85ff60",
        "0xdbe46a02322e636b92296954637e1d7db9d5ed26",
        "0xdfe4b89cf009bffa33d9bca1f19694fc2d4d943d",
        "0xe2b406ec9227143a8830229eeb3eb6e24b5c60be",
        "0xe368759445438b8ec4e50bf4094e939341174e62",
        "0xe4786cfe980ef5a6428a2fffafabf24f1fc79b64",
        "0xe6a421f24d330967a3af2f4cdb5c34067e7e4d75",
        "0xe7b3b0a59b026ec1fef16561daf93672a61bafec",
        "0xe80623a9d41f2f05780d9cd9cea0f797fd53062a",
        "0xec96bbbe895301710a89a06546264ebb4f0cc546",
        "0xed470553f61f23cd30ccf51ab066dc1598ed0c4f",
        "0xf207b2f9f9417fc73cad069f7aa5ae1c6a5b428d",
        "0xf646d9b7d20babe204a89235774248ba18086dae",
        "0xffa8db7b38579e6a2d14f9b347a9ace4d044cd54"
      ],
      "mention": {
        "end": 18,
        "start": 12,
        "text": "Bitget"
      },
      "owner": "Bitget"
    }
  ],
  "id": "v2-m08",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "b783ea6523405504e04b50f53d28094431110afcfb95e6b0f0e4532c99dd4472",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "e3786f3d492df8f44f1d065665abbce22b8ef14ce059396c76d6c023c5ba714f"
}
```

Lý do tác giả: UTC hour grouping follows union of all dictionary-known recipients.

Sample: 24 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "0"
    ],
    [
      "number",
      "942"
    ]
  ],
  [
    [
      "number",
      "1"
    ],
    [
      "number",
      "1019"
    ]
  ],
  [
    [
      "number",
      "2"
    ],
    [
      "number",
      "1025"
    ]
  ],
  [
    [
      "number",
      "3"
    ],
    [
      "number",
      "1007"
    ]
  ],
  [
    [
      "number",
      "4"
    ],
    [
      "number",
      "1498"
    ]
  ]
]
```

Multi-address: 9/57 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "636d5b623dd5ccc241ff788e6277006c54bc58a35ba29d8694b0820fcf09622d",
  "case_sha256": "10bf1c2c6eee1166ff5c7f657884e040161b0ef9b7ac0573ea361b0c34330c5c",
  "id": "v2-m08",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "b783ea6523405504e04b50f53d28094431110afcfb95e6b0f0e4532c99dd4472",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "e3786f3d492df8f44f1d065665abbce22b8ef14ce059396c76d6c023c5ba714f",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m09 — multi_address

Across known Deribit senders, report dates with positive-value outgoing outer transactions, their counts and minimum positive wei value; order by date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "deribit_positive_outbound_daily"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:deribit_positive_outbound_daily",
  "id": "v2-m09",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `deribit_positive_outbound_daily`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS n, MIN(value_wei) AS minimum_wei
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_owner='Deribit' AND value_wei>0 GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x062448f804191128d71fc72e10a1d13bd7308e7e",
        "0x1b995f9d96951f4a04c30d2e114819949e971bc8",
        "0x1bae874af9f81b8f93315b27f080260da4702d3a",
        "0x245772af12d1c31e2b7d6ea810a91c1f3db4eb94",
        "0x2563328d58ac7ee9e930e89c29ce96046a291207",
        "0x282f9830e74d887da489c030cb1ef1d328eac0a9",
        "0x2eed6a08fb89a5cd111efa33f8dca46cfbeb370f",
        "0x369f8406a13729c168526018697f0da667656cde",
        "0x3d09d2354530466d32ed37c6ad19ea58504a0c37",
        "0x4e67722883ad992182e83b79bf06a93972963cac",
        "0x58f56615180a8eea4c462235d9e215f72484b4a3",
        "0x5f397b62502e255f68382791947d54c4b2d37f09",
        "0x63f41034871535cee49996cc47719891fe03dff9",
        "0x6b378be3c9642ccf25b1a27facb8ace24ac34a12",
        "0x77021d475e36b3ab1921a0e3a8380f069d3263de",
        "0x866c9a77d8ab71d2874703e80cb7ad809b301e8e",
        "0x8f5f8ada4d19bf4ffbe580e4ce92af424e60c720",
        "0x904cc2b2694ffa78f04708d6f7de205108213126",
        "0x98f980a6f4800b53db7df568b5e1f6f230d661e5",
        "0xa0f6121319a34f24653fb82addc8dd268af5b9e1",
        "0xa7e15ef7c01b58ebe5ef74aa73625ae4b11fe754",
        "0xacd41f0da1a84f5543c84a33864e025ce30c099d",
        "0xb61a16bda6d61d9b8ad493bf05962c5b98d1712f",
        "0xc7125da07a7110049ecc68f43bf10de4d45ca84e",
        "0xcf2027aab22980820f0767d9f214cdbd2aa2428d",
        "0xcfee6efec3471874022e205f4894733c42cbbf64"
      ],
      "mention": {
        "end": 20,
        "start": 13,
        "text": "Deribit"
      },
      "owner": "Deribit"
    }
  ],
  "id": "v2-m09",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "63244eaaa01e7ba93d211bd21e751ce5c82e2ee535c7bdc6b72c035e45ae4502",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "value_wei",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "617bd425b013f7eeb28c68105f0460e0ac646e0f0a080280d632695ac249e244"
}
```

Lý do tác giả: Positive declared value predicate belongs to both union and single-address checks.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "1433"
    ],
    [
      "number",
      "29000000000000"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "1597"
    ],
    [
      "number",
      "30000000000000"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "1837"
    ],
    [
      "number",
      "33000000000000"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "2204"
    ],
    [
      "number",
      "39000000000000"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "1383"
    ],
    [
      "number",
      "41000000000000"
    ]
  ]
]
```

Multi-address: 7/26 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "a0ba546019320d1c8523f518a96ade89f1ca78eead2725ae16b63fdf7d379ac8",
  "case_sha256": "8e0f7b946bcc0d90a84fed817840293d3bcbe55d58b87d01a4eb0018c127d33e",
  "id": "v2-m09",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "63244eaaa01e7ba93d211bd21e751ce5c82e2ee535c7bdc6b72c035e45ae4502",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "617bd425b013f7eeb28c68105f0460e0ac646e0f0a080280d632695ac249e244",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m10 — multi_address

For the complete known MEXC address group, return counts of outer transactions sent, received, and involving the group in either role. An internal transaction contributes once to the either-role count and once to each directional count. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "mexc_outer_both_role_counts"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:mexc_outer_both_role_counts",
  "id": "v2-m10",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `mexc_outer_both_role_counts`. Property focus: `None`.

```sql
SELECT COUNTIF(from_owner='MEXC') AS sent, COUNTIF(to_owner='MEXC') AS received,
    COUNT(*) AS involved FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_owner='MEXC' OR to_owner='MEXC'
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0162cd2ba40e23378bf0fd41f919e1be075f025f",
        "0x12c5e4eeeaa20e25847b5453d23246983c512db7",
        "0x1ed0be7d0a9580e202f6b98c29725d5c11d10b71",
        "0x1f7370792a057227024e7a8cc15b40e3ed171ffc",
        "0x2ff5fc5b63f2bfce5d6bb9ea4d170cf1aa40693c",
        "0x3cc936b795a188f0e246cbb2d74c5bd190aecf18",
        "0x469afe803c54a36674c55231489cf4b61da8c1bc",
        "0x4ac71ec43df19581d95eab5596c6fadc89170989",
        "0x6e5a3b0021949452d31a43be17d808de54752a44",
        "0x75e89d5979e4f6fba9f97c104c2f0afb3f1dcb88",
        "0x76bf215ade956642b056b9043e014988941bbddd",
        "0x9642b23ed1e01df1092b92641051881a322f5d4e",
        "0xb5a6fd438017dbb0a2e5fcdcca715da227582ce4",
        "0xbcb302a64adb7f2c8697e17c1e948f5b058f0e49",
        "0xc411ab12837f63935b71b6c6643d0f7000e55e4b",
        "0xc906895c8833481571118f0c59877bff6be38ac1",
        "0xd67f25ef2399a0c769b1a35634c5ce77166714db",
        "0xe4e3eca65460c14a5245b09fee15a92ba09458b6",
        "0xee136c0389733849dd710ac7104e92c6bf497574",
        "0xf016e1d45ef23bdd414e7a2e4d46e1b34577b508",
        "0xf95334a86d09a6eec74d69da344efaca424b13a9"
      ],
      "mention": {
        "end": 27,
        "start": 23,
        "text": "MEXC"
      },
      "owner": "MEXC"
    }
  ],
  "id": "v2-m10",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "either"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "376d5c566d6f65a7d9e680d607f9fda1c48f5b66521034a51b547a5f5face36c",
  "schema": {
    "columns": [
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "ae460c544195701479cf9763cfdaad1fb72e2afb26ab13d04d7dd0b6e0aae3ba"
}
```

Lý do tác giả: OR selects each outer row once; directional counts intentionally overlap.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "137660"
    ],
    [
      "number",
      "9704"
    ],
    [
      "number",
      "147350"
    ]
  ]
]
```

Multi-address: 16/21 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "a601b5d62d6ebb5fbe0b7ce68b4025f2a3ac93e403c15db9895fbadbe929c850",
  "case_sha256": "2397dd39ee43c18a25ec5273c6e57f5f9c0db69859555c729e204f99779b8201",
  "id": "v2-m10",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "376d5c566d6f65a7d9e680d607f9fda1c48f5b66521034a51b547a5f5face36c",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "ae460c544195701479cf9763cfdaad1fb72e2afb26ab13d04d7dd0b6e0aae3ba",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m11 — multi_address

Combine every known Binance recipient address and report incoming token events by token contract, including event count and distinct sender count; show the twenty most frequent tokens, breaking ties by token address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "binance_inbound_token_mix"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:binance_inbound_token_mix",
  "id": "v2-m11",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `binance_inbound_token_mix`. Property focus: `None`.

```sql
SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT from_address) AS senders
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Binance' GROUP BY token_address
    ORDER BY events DESC, token_address LIMIT 20
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x030e37ddd7df1b43db172b23916d523f1599c6cb",
        "0x110daa3f3fac2a54bb508ac94f31f9df77057b29",
        "0x150aace136535a374f05b5ee209b6a61396db1c0",
        "0x18e226459ccf0eec276514a4fd3b226d8961e4d1",
        "0x1b46970cfe6a271e884f636663c257a5a571fb2c",
        "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        "0x22132139bf7f3921b1cadeab931f4fbf7bf2bc9e",
        "0x26bff98f6f37c8d560684eaf2afd1149bf76633e",
        "0x28c6c06298d514db089934071355e5743bf21d60",
        "0x308a2a0712570daeea77c8ba9c27a32cdc4000d4",
        "0x32e11a20337ebc79abd0eeab2d91bafbd9591149",
        "0x38aaef3782910bdd9ea3566c839788af6ff9b200",
        "0x42a93a9f5cfda54716c414b6eaf07cf512f46ead",
        "0x43684d03d81d3a4c70da68febdd61029d426f042",
        "0x4976a4a02f38326660d17bf34b431dc6e2eb2327",
        "0x4aec0e98fc1fb55b9cc2faaa7a81acca42cb4e96",
        "0x4ed6cf63bd9c009d247ee51224fc1c7041f517f1",
        "0x4fdfe365436b5273a42f135c6a6244a20404271e",
        "0x56eddb7aa87536c09ccc2793473599fd21a8b17f",
        "0x5a1e5b56aa33c056ed7bb93b88b1774a456f6694",
        "0x5a52e96bacdabb82fd05763e25335261b270efcb",
        "0x6357e4bdaff733dfe8f50d12d07c03b3bed0884b",
        "0x6454ac71ca260f99cca99a3f4241dfda20cfa965",
        "0x756b86fd69914db92229c07c7393d7d9948fed33",
        "0x835678a611b28684005a5e2233695fb6cbbb0007",
        "0x8498fc7280668874a5da79e87ca0896f4f0d1196",
        "0x86523c87c8ec98c7539e2c58cd813ee9d1a08d96",
        "0x87433fec6f8d9df13d1e17c4b11364ecd2e93a51",
        "0x8a6f8404c9ea4c33502a3f6a4bf8e41ef5ca10ea",
        "0x8e609ac80f4324e499a6efd24f221a2caa868224",
        "0x9696f59e4d72e237be84ffd425dcad154bf96976",
        "0x98adef6f2ac8572ec48965509d69a8dd5e8bba9d",
        "0xa345dcb63f984ed1c6d1a8901e0cdbd13b2b4d19",
        "0xa64b436964e7415c0e70b9989a53e1fb9a90e726",
        "0xa7c0d36c4698981fab42a7d8c783674c6fe2592d",
        "0xa9fc92f6faf9f103fc81d17de3e8daadc888afff",
        "0xad354cfbaa4a8572dd6df021514a3931a8329ef5",
        "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",
        "0xc47b3342df38d747033b6041f54e4e5e300c8d18",
        "0xc8daf809c7d7c27dd62d006196d8901ba57e5eae",
        "0xd27b39cb25fed854f9fce3a4e451f96e62089e48",
        "0xdbeb6c856ef5a167f5e1acb9dff65adb33207d8b",
        "0xdbf28a152d79b2b98eecd229b412ee98d21ec3bc",
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
        "0xe1940f578743367f38d3f25c2d2d32d6636929b6",
        "0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055",
        "0xf16924b866e58ac916ba933d1f1034bcbbb1958c",
        "0xf1f8cb7633d3ca3fd06c084d18ca5491a85ae9b4",
        "0xf977814e90da44bfa03b6295a0616a897441acec",
        "0xfc8059c2fb22005ede8a86d388e3d0f536a4dd44"
      ],
      "mention": {
        "end": 27,
        "start": 20,
        "text": "Binance"
      },
      "owner": "Binance"
    }
  ],
  "id": "v2-m11",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "ff7bc22ad029240a9afba5d8314fdc484e16a8c8fe1cf12910e6ec41aecaaedc",
  "schema": {
    "columns": [
      {
        "column": "from_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "b5e1649f4fc5f5ce492149d65f6d47aec0576375429753ce6dfcc6a62925cece"
}
```

Lý do tác giả: Event counts, not normalized amounts across heterogeneous tokens.

Sample: 20 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x419d0d8bdd9af5e606ae2232ed285aff190e711b"
    ],
    [
      "number",
      "19771"
    ],
    [
      "number",
      "19771"
    ]
  ],
  [
    [
      "string",
      "0x163f8c2467924be0ae7b5347228cabf260318753"
    ],
    [
      "number",
      "6329"
    ],
    [
      "number",
      "668"
    ]
  ],
  [
    [
      "string",
      "0x57e114b691db790c35207b2e685d4a43181e6061"
    ],
    [
      "number",
      "5094"
    ],
    [
      "number",
      "910"
    ]
  ],
  [
    [
      "string",
      "0xfaba6f8e4a5e8ab82f62fe7c39859fa577269be3"
    ],
    [
      "number",
      "4767"
    ],
    [
      "number",
      "1071"
    ]
  ],
  [
    [
      "string",
      "0x4575f41308ec1483f3d399aa9a2826d74da13deb"
    ],
    [
      "number",
      "4506"
    ],
    [
      "number",
      "4506"
    ]
  ]
]
```

Multi-address: 20/50 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "be4b5f1df06dd8788b70236b8931d03cf3e28198d671e96e5e014304510d8439",
  "case_sha256": "8be2004be93a0ede9fe0182b194e98d46d889c7e233e3213587eb569272d9662",
  "id": "v2-m11",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "ff7bc22ad029240a9afba5d8314fdc484e16a8c8fe1cf12910e6ec41aecaaedc",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "b5e1649f4fc5f5ce492149d65f6d47aec0576375429753ce6dfcc6a62925cece",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m12 — multi_address

Across known OKX token-event senders, return the twenty most frequent token-contract and recipient pairs with their event counts; resolve ties by token address then recipient. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "okx_outbound_token_counterparties"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:okx_outbound_token_counterparties",
  "id": "v2-m12",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `okx_outbound_token_counterparties`. Property focus: `None`.

```sql
SELECT token_address, to_address, COUNT(*) AS events FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE from_owner='OKX' GROUP BY token_address, to_address
    ORDER BY events DESC, token_address, to_address LIMIT 20
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0003b5aa5e30e97fcc596bb5d0f3a75255e08d4e",
        "0x01c2a9e7eeaee29b03708692ba5e1515036451e8",
        "0x01f66697aec1e7de7773115243247952245fd3a4",
        "0x01f7cea182239f9e9caf0f1ce0744bcb23c20585",
        "0x03ae1a796dfe0400439211133d065bda774b9d3e",
        "0x03d0aad7c6a0b36f47d852a28ff0fb7bc9ae46b6",
        "0x0475dd0e4194422a8cac486dc69173f535d0baf4",
        "0x0607c628054a7db3d36eed7c4a408eda8260de09",
        "0x06324bad3913cb69cb5e748a3ed72f9d692324bb",
        "0x06959153b974d0d5fdfd87d561db6d8d4fa0bb0b",
        "0x06d3a30cbb00660b85a30988d197b1c282c6dcb6",
        "0x073f564419b625a45d8aea3bb0de4d5647113ad7",
        "0x0750b999e493112c88cb226a13a2a67419f06ad6",
        "0x0799ddbf6f14db566ca4df4ff0575c4cc1e7749c",
        "0x08af9c4767236221c55069dd523e2f7a0013e898",
        "0x08f619716db7c6245401b543e59acac1d25cb483",
        "0x0938c63109801ee4243a487ab84dffa2bba4589e",
        "0x0a133528245eaf5bab72dc05a9dd8e0ea4b982f9",
        "0x0c48511102453352fe570370672cd556bf0e63f9",
        "0x0ff9491b236a36cc183823e39d7532194143fdb1",
        "0x11b113383ce08e84001dc614f141ae4c27221e31",
        "0x1278678b5b17eba14b313d287659ae9f3aa7c087",
        "0x12a8bdc0470ab29a229d828526641b7d1f170fcf",
        "0x16b5016803bcb4915701efc0a3b471bd4c168d93",
        "0x173810f8ca9c4c631aeb1d6c36d007f054fee980",
        "0x17e91b98988937cb59dc163b0b11781f9785591a",
        "0x1811068091a2459ee38a8dde52cce5b2acfc1b61",
        "0x19abcd6b8516d2b4d9aa3bbf700b38a30dc154fc",
        "0x1a557020c52f9d2495b2c12eb137ee7b5d467a4f",
        "0x1c628a9c66ff63454a4526a4f2b8af250da8d086",
        "0x1dfc6bec8499fcb5e3151c7c6d27feb9d7eae1d4",
        "0x1e43e7a911b1b0229ea7d64e11ae260c482a0870",
        "0x221ac9e1920932e95adf0c941f3524157f4bda4f",
        "0x25236e080106b5387df201fbbd9a6b870917676d",
        "0x26704ccfcd45b5780dcd58d38b12f5e0cdb481a0",
        "0x267b51c97632225da2b2e49aebe59eef1af32653",
        "0x276cdba3a39abf9cedba0f1948312c0681e6d5fd",
        "0x297611b7accb7f24032c27b3a496465624c7ef50",
        "0x2c8fbb630289363ac80705a1a61273f76fd5a161",
        "0x30c1dcde81e5dbf3121d0408abc7908980e83ae2",
        "0x313eb1c5e1970eb5ceef6aebad66b07c7338d369",
        "0x32dc16f4631a27b042a974d05c1ccf8a303e8199",
        "0x3425519651e4c42833633fe5c0e24ed89c1023a3",
        "0x3b9694465483cbb677b700a91c26f487193a6e03",
        "0x3b98b9e9cb75c1cb1729aab8f09ced2936505e4f",
        "0x3bb00393bfa5e76b7f31e93948f7d3cef12942ad",
        "0x3c5883c650d600bd543a9b5c8d9a3a6f5d16b8f4",
        "0x3d2335cac7b31411467ef03168c5869452fb7e86",
        "0x3d55ccb2a943d88d39dd2e62daf767c69fd0179f",
        "0x3e7d48c8ae2e50c2b9adedc8e276d3cc92b39458",
        "0x3f482c72a2b3e777746f5755cc0ff1323ea2ad16",
        "0x400d8280acf364f683e989462879fd8dd358067d",
        "0x4106a4be14867c70e52c51b9805514ae2e16de64",
        "0x42436286a9c8d63aafc2eebbca193064d68068f2",
        "0x42797deffe266a55fdc4c98d7d3885d7058cb3e5",
        "0x42cf18596ee08e877d532df1b7cf763059a7ea57",
        "0x445f16314284b43dfa1fd3cd77b9dea4a1bebd97",
        "0x45d9c02baed2d1670f7bad40fb5f657a05068d52",
        "0x45f329ff834a84fccea2319f91e1993540b22a2a",
        "0x461249076b88189f8ac9418de28b365859e46bfd",
        "0x47eb32dea1ab1436187939fa72d6d5ff884a87da",
        "0x48480aad203e8b030f82754b3c75869c9895c6bf",
        "0x48c4c83be7e3884ee5043a3abe5115eb020b5f4a",
        "0x4a11078a99b118bbfee78a5c187d98d264360433",
        "0x4bcbaf34862e6480329477917cf5cd7b9537a98d",
        "0x4d19c0a5357bc48be0017095d3c871d9afc3f21d",
        "0x4d619eb6db0b9b6184d9881c4828c0effff84eda",
        "0x4e2757e46103556f98d4d036d8efe18389b89f51",
        "0x5041ed759dd4afc3a72b8192c143f72f4724081a",
        "0x52738a51882f35d6b25a3fd0c86089ddbd206821",
        "0x52b311c52436789f3754bd199bf3886b8ccbab4c",
        "0x539c92186f7c6cc4cbf443f26ef84c595babbca1",
        "0x559432e18b281731c054cd703d4b49872be4ed53",
        "0x56fd42ecd77c88bdd959be54af10d1759b473dff",
        "0x593878f92dde464fc4e3b17cd7cc87117dca753c",
        "0x5a150733cb59bbdd5c7398a8fe7da7f97c8a213a",
        "0x5b27e98516fd2bd5001d4dfe3f5a2263f702f634",
        "0x5b873ffcad5dccdc61c1a53c391fb76cb316a841",
        "0x5c52cc7c96bde8594e5b77d5b76d042cb5fae5f2",
        "0x5ca38fb7cf2b587026a1650f0d2b0a13c41f5d0f",
        "0x5f5105b9a19e301208844263806df9b7212e655d",
        "0x5f8215ee653cb7225c741c7aa8591468d1f158b8",
        "0x608c27519c5e65a61cfc1d2c9e658e5c57a2e3d7",
        "0x611f7bf868a6212f871e89f7e44684045ddfb09d",
        "0x65a0947ba5175359bb457d3b34491edf4cbf7997",
        "0x65e891ec42fcaa19459fe6221163e1a3f8cf7ea6",
        "0x6667a4b7eff4a0b86781fb3b187622cd3c257f09",
        "0x66e6bdac6fae819f944901e3b6ecc9bfff61a706",
        "0x6709383e211ab08a6e3270532e756220400424a6",
        "0x68841a1806ff291314946eebd0cda8b348e73d6d",
        "0x68b5e9e083bfc28c33cfbf3f19d33e629015e907",
        "0x68e2ea1622aa67fb3a01a66d132daed8a48d1662",
        "0x69a722f0b5da3af02b4a205d6f0c285f4ed8f396",
        "0x6a4561ef7874a76b4bf0d3edca31dfcd51603414",
        "0x6b7ba57e1d43c2c975ba25139a04d193e64a11d0",
        "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
        "0x6d29fc1267b1691c0cd43a8d35b27135957ffea9",
        "0x6d8c32fcf2d95ff410ba492f6694f18cbee55ce1",
        "0x6dc1a070425f437ac08bb108f7093b177d7af3a6",
        "0x6ededbad1e864105fa2538ddfbf4e7214b9e6529",
        "0x6fb624b48d9299674022a23d92515e76ba880113",
        "0x6fd41d4a272247fd1104c710909a4af8bd38f522",
        "0x728d92a8023bfbe0d4f3fdd549ed3b4996a0eba9",
        "0x730df969955c0a2fa9e8f2484e9741a363afdbb3",
        "0x739768219c831ec1f747bf904f0e25c2d99c7dc1",
        "0x767a905b77b0a40801488c6af8b8b5992b43511c",
        "0x778e456fbfd14075f5ddbccf9be2d6a48e3b1ecb",
        "0x7926c83479e2708edfd83a39d62084693e192298",
        "0x793aa889e19a130ee4cb8b63c79aa3bdccc663cb",
        "0x7a91e803db0e58b6fecc4e42c86b366778475e3c",
        "0x7a93539c1bf9a96f87044925deb7a0849266213e",
        "0x7c7061221666e41b87ca5817cfa2fcac09b3d943",
        "0x7cfe28094f4531809992ed89060a61413116365d",
        "0x7d4a2c448fe5b07c62228140417b3565bbe1b86b",
        "0x7eb6c83ab7d8d9b8618c0ed973cbef71d1921ef2",
        "0x7f61dc44c15ca818f96c6fc40739e5aa732e240c",
        "0x7fe830ec109e112f549d6ee9d3e9540e7785997b",
        "0x7fea5b4568751533039179116e372e26b6b41b13",
        "0x80335e658ee73756bb8220bdb77f99e98322035f",
        "0x8167a1ebf00ff5886d1b5908419bb1159d8cf6a4",
        "0x83a32a54d31ee4f1f9dffad2a63a6d214e469ec3",
        "0x85dcd76d4fbd3aa0c85c27b9441222c19a14134b",
        "0x868dab0b8e21ec0a48b726a1ccf25826c78c6d7f",
        "0x86aee064cc073d0dc95ba86633067b2c615040bb",
        "0x8734bca44102bf8a663e1ba112308504606e1b08",
        "0x87d0d6c8cdd71a658ecf1566f13e4cbc562beaf9",
        "0x88c94d8e7d4203b185b3beb0a7b15a6b4f36b2a2",
        "0x89b2f6dafc9d46ce0ed7d7e45a4972d14f037a19",
        "0x8ad740adce08f2f3579884eac0a12e581304ac3b",
        "0x8c3cb9665833fd9f79eb14cba16d82bbab6f22d8",
        "0x8f1aae22d0b4335945950d0bbd0f3743d3fc6f22",
        "0x91d40e4818f4d4c57b4578d9eca6afc92ac8debe",
        "0x92ea7496eba5f001d620005f88f3e8e686e3d4ea",
        "0x932d7d2cbc06234919f34802a22a914282a00f87",
        "0x96fdc631f02207b72e5804428dee274cf2ac0bcd",
        "0x9723b6d608d4841eb4ab131687a5d4764eb30138",
        "0x98ec059dc3adfbdd63429454aeb0c990fba4a128",
        "0x9938ee74ba7a5c1abcd157272a18fcfc9ec9e8d5",
        "0x994d24172fcfafbb5fce0ac5392078fa1c025448",
        "0x9b645675e8d64759e5c36e30dcb766d8cec3d34f",
        "0x9ce5a8098270f07a0a56398febda76a8ee2858c4",
        "0x9d65bf1bce7a10814228f4d81d8cf99a6b0f44aa",
        "0x9db8b860692c41e709d48d089de64cf01e6e317e",
        "0x9e13bae2256f968d02fe0129a0f51788f4e2472f",
        "0x9e3bb2cd5a89fcc4b826230b144c4917881bea85",
        "0xa01533d5c66a4886d3bb39b156507d9de65653e6",
        "0xa2684f75740cfff46c29bae79a4ecc43043c003d",
        "0xa27cef8af2b6575903b676e5644657fae96f491f",
        "0xa68cfe488a785c8b38ce2db6c45cfe07cb620c2d",
        "0xa7efae728d2936e78bda97dc267687568dd593f3",
        "0xa9ac43f5b5e38155a288d1a01d2cbc4478e14573",
        "0xacf961ae22191f0d080497a3a3b427180f18ed67",
        "0xae0cbaba071d58efc278a815b2cb652286e192ff",
        "0xb072b7dc9521d97a3f12b04beb1e497f8875ec52",
        "0xb0a27099582833c0cb8c7a0565759ff145113d64",
        "0xb47a0ac7798d8308467b2b96ac632ed43c9cb6d7",
        "0xb4ec508adeb174610b4295e233a458b3475964f7",
        "0xb640e1e5a5f726a054cd518c968dfdac8c421ee5",
        "0xb8ede418d8116113efb7644a792e5d97aade6138",
        "0xb99cc7e10fe0acc68c50c7829f473d81e23249cc",
        "0xba0a39d37151fa4f938bec51cdae4675105760f4",
        "0xba7fd71d309bc0e96b64022fd8fea7299b256159",
        "0xba96a3f3d5e9f13a5f93c37001f946d42eb2e165",
        "0xbda23b750dd04f792ad365b5f2a6f1d8593796f2",
        "0xbe2ec156292587338d4e9f80f5439e6152d56fc5",
        "0xbf94f0ac752c739f623c463b5210a7fb2cbb420b",
        "0xbfbbfaccd1126a11b8f84c60b09859f80f3bd10f",
        "0xbfef5c888bb7a0a6b14b4c3ccc4364ea81aa573f",
        "0xc0d01a27fd89e6bbc68f43e94ade3dfca2c27674",
        "0xc18475f347cc757b3cc49025820248a5f27d97ce",
        "0xc275bf069df3e63184a1222359114b805b6cd2f5",
        "0xc5267f13b9b4ba7bb73bdd53a2a3c944733a2961",
        "0xc5451b523d5fffe1351337a221688a62806ad91a",
        "0xc5a93444cc4da6efb9e6fc6e5d3cb55a53b52396",
        "0xc6724cf116573eab588fb0d73dcdc16929493cea",
        "0xc68c17e6eec0fde3605c595c9b98de5c1a4cc3e4",
        "0xc708a1c712ba26dc618f972ad7a187f76c8596fd",
        "0xcab0c0a224bad992085430f87dc1855342763a88",
        "0xcb0963264231bb08b2f680ab3ed89a49c9641bb3",
        "0xcba38020cd7b6f51df6afaf507685add148f6ab6",
        "0xcbc767b519394a9e4682cc9a15dcd18c46a6045b",
        "0xcc5d36fb0126515cb7988bbeee8445f03c304b2a",
        "0xcd5bd47d3d1d8412b241ce9015c5032142948c12",
        "0xce9abe75d561f065f1c4adb188b260df9de32ca7",
        "0xd03e6a53a3298ba1cd9b0dbf525ad728f4f8ad6e",
        "0xd049e4ddf1133af3a7a27390b4c9018141df1a49",
        "0xd19d3341227967610b94e7aebe8c971d2d48f419",
        "0xd266529641eeffaa2b2a0bc99daa5b32ef241078",
        "0xd576392cb12b7749ba33f8d223f64e65ee32f03f",
        "0xd5f8c864f21824daf3a4b22d9c33693642ed7634",
        "0xd7764b4305bcca935e38a450e7956822113374b6",
        "0xd7f4a5613b38cb8c09229b7aed99803242fdf0a0",
        "0xd99d81949146b4c13a4a42c9a6addbbd2db932ad",
        "0xd9a3c9ba5aa4415a53b9190bcb00f14472790a70",
        "0xdad24044e36587d975d7b5bceb6467fac21e0c81",
        "0xdb0ed345cb52c2f2457918afa3eb4b682e264ad0",
        "0xdc3ce895714844b4775b6d06f0dae513542cee10",
        "0xdce83237fbf279c4522e7cac4b10428e2b8694da",
        "0xddf81e81ab956695600d8639356c045e5c8a8c94",
        "0xde01974fb4a98bafd7cbf8a06ecf6dcc94d7283f",
        "0xdeb6ad2a7820839464da79bac953ae6189215443",
        "0xe2effe5bd0617a5a2dc1ee579565911cef3a223b",
        "0xe3bb282457ce7b3be31f0441f3fc051b9fc6a9c3",
        "0xe404fe9b7b0d0e88e77731517202fb392f67cd74",
        "0xe6eea9812ccc5981ccf0ab333610c42c2d92d146",
        "0xe7b29ff45392876143c7b863d57fb2326afe0ff1",
        "0xe7c8fdd899ab06ac1023e8a3e867c5fa7e751450",
        "0xe9172daf64b05b26eb18f07ac8d6d723acb48f99",
        "0xe983845a04c681a295dd9ce1fa8c2c8505932da3",
        "0xea3b7dac6b96502a04c701d5e71b51912f70143f",
        "0xeaed6576334b003d1c5c4797d9c7bb025a20c038",
        "0xeb196a61f9a1e35bf5053b65aaa57c5541dcba86",
        "0xedc0a430dd32eb8cfcc3a344979f0e21bc48bf0d",
        "0xee1c6537e589a15a15f80961f5594c57bed936fb",
        "0xf02e3c0095f6de36c76364d4cc53eb06d1288fc1",
        "0xf418263a6468c80d3bcb71033c56aacf81b241ba",
        "0xf59869753f41db720127ceb8dbb8afaf89030de4",
        "0xf683b33e21e85ee6c0e25af2fff5b2b115f32617",
        "0xf7858da8a6617f7c6d0ff2bcafdb6d2eedf64840",
        "0xf7b17e0b2478ad21ac594e4b0954ece63d059064",
        "0xf7c63e75b90c60d7b343106a39658f8b3ca6e4d2",
        "0xf8b4256122369c48eb8c3d901875d62458a675e8",
        "0xfa13971666d0e6f2715d68eb44bb7964fc22b14b",
        "0xfad70cb84e104817a7e9345d25ed0d3048af2d2d",
        "0xfcb21730ac0cd487d8701dfed1170e023b57cf7a",
        "0xfe908731af54c56dfd63948f18ce5878a3b8a1ad"
      ],
      "mention": {
        "end": 16,
        "start": 13,
        "text": "OKX"
      },
      "owner": "OKX"
    }
  ],
  "id": "v2-m12",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "74125aaf04f426d091519f7a015f43d7966b693ae469451f24dd4b8092ff85b4",
  "schema": {
    "columns": [
      {
        "column": "from_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "ef4e9ca4004ce1b499a582f82565887af1848f11e26eeb00f647d0229cba25b3"
}
```

Lý do tác giả: Known owner sender addresses are unioned before pair ranking.

Sample: 20 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x232ce3bd40fcd6f80f3d55a522d03f25df784ee2"
    ],
    [
      "string",
      "0xd862cdcfeb856c32b3c4f7563f4811d8ddfd42e2"
    ],
    [
      "number",
      "817"
    ]
  ],
  [
    [
      "string",
      "0x526526528f35ac738177003b8773b402b8df8143"
    ],
    [
      "string",
      "0x60667cee9359de0cab1b286f02986ea472e09789"
    ],
    [
      "number",
      "362"
    ]
  ],
  [
    [
      "string",
      "0x526526528f35ac738177003b8773b402b8df8143"
    ],
    [
      "string",
      "0x41fbba5cb38d22b2d80606406944cedd7c97f6f9"
    ],
    [
      "number",
      "270"
    ]
  ],
  [
    [
      "string",
      "0x526526528f35ac738177003b8773b402b8df8143"
    ],
    [
      "string",
      "0xe9a911b75ff5bb6e7b41a045b4d3ceedb6101381"
    ],
    [
      "number",
      "243"
    ]
  ],
  [
    [
      "string",
      "0x163f8c2467924be0ae7b5347228cabf260318753"
    ],
    [
      "string",
      "0x27bffb0f09c18539f9a47a39958bb149fe42a155"
    ],
    [
      "number",
      "228"
    ]
  ]
]
```

Multi-address: 26/226 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "4cd504a734d18691df4d73a88034d06fac2910b3150058a9c74581ff5ec7973c",
  "case_sha256": "bf229a433961a78b0becb25258113dcd32bba5ca8b6ed531845b4c7815958f64",
  "id": "v2-m12",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "74125aaf04f426d091519f7a015f43d7966b693ae469451f24dd4b8092ff85b4",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "ef4e9ca4004ce1b499a582f82565887af1848f11e26eeb00f647d0229cba25b3",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m13 — multi_address

For token events involving any known Bitfinex address as sender or recipient, give each active date's event count and distinct outer transaction count in date order; count an internal event only once. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "bitfinex_token_daily_transaction_reach"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:bitfinex_token_daily_transaction_reach",
  "id": "v2-m13",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `bitfinex_token_daily_transaction_reach`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
    COUNT(DISTINCT transaction_hash) AS transactions FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE from_owner='Bitfinex' OR to_owner='Bitfinex' GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x742d35cc6634c0532925a3b844bc454e4438f44e",
        "0x77134cbc06cb00b66f4c7e623d5fdbf6777635ec",
        "0x876eabf441b2ee5b5b0554fd502a8e0600950cfa",
        "0xc61b9bb3a7a0767e3179713f3a5c7a9aedce193c"
      ],
      "mention": {
        "end": 45,
        "start": 37,
        "text": "Bitfinex"
      },
      "owner": "Bitfinex"
    }
  ],
  "id": "v2-m13",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "either"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "8ebec8b516db682308b78f36fec917feb53ed89f5a8d0ac69a967c87de34c4a8",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "from_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "transaction_hash",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "ca28471717768d9b8191215695d0dbe8a4961e36593bff90d0358345de860263"
}
```

Lý do tác giả: OR prevents duplicate rows when both event endpoints belong to the owner.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "216"
    ],
    [
      "number",
      "216"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "234"
    ],
    [
      "number",
      "234"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "261"
    ],
    [
      "number",
      "261"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "240"
    ],
    [
      "number",
      "240"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "319"
    ],
    [
      "number",
      "319"
    ]
  ]
]
```

Multi-address: 2/4 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "95433448d4b4f2b84300540a6c982e389b66b7649c80bb9ca9ba5bcef8171712",
  "case_sha256": "29c4f50da4fe7af9ac40e1f4867b1f958b2a52cf74b9df780f8cfb8fdaf4a455",
  "id": "v2-m13",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "8ebec8b516db682308b78f36fec917feb53ed89f5a8d0ac69a967c87de34c4a8",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "ca28471717768d9b8191215695d0dbe8a4961e36593bff90d0358345de860263",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m14 — multi_address

Pool known KuCoin recipients and, for each token contract, return incoming event count minus distinct transaction count alongside both counts; order by the difference descending and then token address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "kucoin_inbound_event_fanout"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:kucoin_inbound_event_fanout",
  "id": "v2-m14",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `kucoin_inbound_event_fanout`. Property focus: `None`.

```sql
SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT transaction_hash) AS transactions,
    COUNT(*)-COUNT(DISTINCT transaction_hash) AS extra_events FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE to_owner='KuCoin' GROUP BY token_address ORDER BY extra_events DESC, token_address
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x04f2abb57b53122eb0306418f2220746d06af9fc",
        "0x061f7937b7b2bc7596539959804f86538b6368dc",
        "0x06679e7b7f91487cc9d59779501c414a1b3eb89d",
        "0x0669bcdc8ede4a973ed9b3480aff984de15d2d65",
        "0x0c32131b67a9306a42e5b66f869bc213d40e43f0",
        "0x0f1836312d18524368d05d537c0fabaff6ca6ccc",
        "0x0f75e66731ca8ab3471503562ff964cd40741f41",
        "0x10affefb7ce337348e0b258fffc6a1d5745c2be9",
        "0x10c3d6ef33446e51b6d5c70970f7ad71cc1f42be",
        "0x1136a49f3a1e3a3b6b2b6de30f8244d16f18509a",
        "0x1692e170361cefd1eb7240ec13d048fd9af6d667",
        "0x175ce6204bfda2a509c7e9c786b74407f569c9cc",
        "0x189b24f3eb15dc71b4fc57c5914e7e9b3246e449",
        "0x1b14376ee2d46ae5c27a43d902d96d4f3f264b83",
        "0x2677c4c8757da1857cc7cc4071e0e0dd32ccb975",
        "0x2933782b5a8d72f2754103d1489614f29bfa4625",
        "0x2c73858225cfbf15fd1b71ff27d006cb96c57e27",
        "0x37e4d1cd3fe31edf473ebcf3b6a75f419c8839d1",
        "0x3b6d76719a4ea8c53a7a26b50175b8de23c8e956",
        "0x41e29c02713929f800419abe5770faa8a5b4dadc",
        "0x4316e553902c3eab807663001d089fd6554a4566",
        "0x441454b3d857fe365b7defe8cb3e4f498ec91eac",
        "0x446b86a33e2a438f569b15855189e3da28d027ba",
        "0x44f1b02d78ed39962600df6440cf8eed3e02a96b",
        "0x45300136662dd4e58fc0df61e6290dffd992b785",
        "0x4a1dffc4e4168fd436dd9d9fb8edb223fa259a68",
        "0x58edf78281334335effa23101bbe3371b6a36a51",
        "0x5b234aaab0f61d346a3ef8faca474c1c19f80c1f",
        "0x651f1d419c548125d7e5456fb61f3df47c29600d",
        "0x69be413d648ae00f0fbd9856f1355e22b36ee5e0",
        "0x6d6cc65e2060d0a280fcd47b6c22ec5636797fec",
        "0x738cf6903e6c4e699d1c2dd9ab8b67fcdb3121ea",
        "0x7491f26a0fcb459111b3a1db2fbfc4035d096933",
        "0x77f59b595cac829575e262b4c8bbcb17abadb33a",
        "0x7b915c27a0ed48e2ce726ee40f20b2bf8a88a1b3",
        "0x7ebfa8b1161e66fffec05d7edbb55e1a2c2aebd6",
        "0x83c41363cbee0081dab75cb841fa24f3db46627e",
        "0x85cef5c097a4df05d27c9fa1a1c1fe16fe691e60",
        "0x88bd4d3e2997371bceefe8d9386c6b5b4de60346",
        "0x8dac80ce96f69f9762bc450faa4d7fbd5891ae18",
        "0x9f4cf329f4cf376b7aded854d6054859dd102a2a",
        "0xa152f8bb749c55e9943a3a0a3111d18ee2b3f94e",
        "0xa2d69adf0b62fa32825d73f086cd4689743543db",
        "0xa649ffc455ac7c5acc1bc35726fce54e25eb59f9",
        "0xaa10db8804d076601999c7cd769e02e44a99d5b2",
        "0xaa99fc695eb1bbfb359fbad718c7c6dafc03a839",
        "0xb514c67824443868d3a70352398f524ef6af6207",
        "0xb8e6d31e7b212b2b7250ee9c26c56cebbfbe6b23",
        "0xbee64116bd2b1b6373273d01664fbc5532dad06d",
        "0xcad621da75a66c7a8f4ff86d30a2bf981bfc8fdd",
        "0xce0d2213a0eaff4176d90b39879b7b4f870fa428",
        "0xd6216fc19db775df9774a6e33526131da7d19a2c",
        "0xd89350284c7732163765b23338f2ff27449e0bf5",
        "0xd91efec7e42f80156d1d9f660a69847188950747",
        "0xdd276dc5223d0120f9bf1776f38957cc8da23cb0",
        "0xe4507d13b059eaf66f7b509b6929f7295690d7cc",
        "0xe8c15aad9d4cd3f59c9dfa18828b91a8b2c49596",
        "0xec30d02f10353f8efc9601371f56e808751f396f",
        "0xf16e9b0d03470827a95cdfd0cb8a8a3b46969b91",
        "0xf8da05c625a6e601281110cba52b156e714e1dc2",
        "0xf97deb1c0bb4536ff16617d29e5f4b340fe231df"
      ],
      "mention": {
        "end": 17,
        "start": 11,
        "text": "KuCoin"
      },
      "owner": "KuCoin"
    }
  ],
  "id": "v2-m14",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "6ba9cb44e2a230708b146521ab5862f5a9bcae8941d98a04b815da2606739b20",
  "schema": {
    "columns": [
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "transaction_hash",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "ed78e467f66c1b4c8e196bfbd0ff053ae212f55eef349eacc81767da92258fd0"
}
```

Lý do tác giả: A transaction may emit multiple inbound events across owner addresses.

Sample: 324 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x451fc122e2c07805c06dfabd2fec8c7632d51418"
    ],
    [
      "number",
      "11"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "9"
    ]
  ],
  [
    [
      "string",
      "0xb74c0d1b1574f8a6d2d820d48311f80bdd4c6b29"
    ],
    [
      "number",
      "10"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "9"
    ]
  ],
  [
    [
      "string",
      "0x25f62db75faffd2eb97e74de912bf16cf0c97a73"
    ],
    [
      "number",
      "4"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "3"
    ]
  ],
  [
    [
      "string",
      "0x699e33bd8c66cc77fd2c179605652ed83d6626db"
    ],
    [
      "number",
      "3"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "2"
    ]
  ],
  [
    [
      "string",
      "0xcaac801d1a2ee1150990a957778ce2a5f975c104"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ]
  ]
]
```

Multi-address: 20/61 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "f9cb5e644b5be02e56b8cb22abb26bd3ea8cccc0a79ace60c7bc144a59a94cbc",
  "case_sha256": "bb2892a2e9e617d95a13efa6fb53311ccc0b25f356b928e30a686b3c0ce48280",
  "id": "v2-m14",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "6ba9cb44e2a230708b146521ab5862f5a9bcae8941d98a04b815da2606739b20",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "ed78e467f66c1b4c8e196bfbd0ff053ae212f55eef349eacc81767da92258fd0",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m15 — multi_address

For each known Bybit address that sent token events, return its event count and number of distinct token contracts; order by event count descending and then sender address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "bybit_outbound_address_contributions"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:bybit_outbound_address_contributions",
  "id": "v2-m15",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `bybit_outbound_address_contributions`. Property focus: `None`.

```sql
SELECT from_address, COUNT(*) AS events, COUNT(DISTINCT token_address) AS tokens
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_owner='Bybit' GROUP BY from_address ORDER BY events DESC, from_address
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x01e2fb8f565d5e3cb9e0e8f0b607a96169b94393",
        "0x076d55c8998da29531ef7fcac2a01fa21582eed2",
        "0x0ac92eb5716516a08e7760d314d42e1d5d3c03ae",
        "0x13f52026493dccf09065952d44101c3e42b41dda",
        "0x180a1b935d28494f9ff4233985562b18b3dcfa74",
        "0x18673311fec54ac2244a602e6d91845553d24e62",
        "0x187c9fbf5bd0f266883c03f320260c407c7b4100",
        "0x18e296053cbdf986196903e889b7dca7a73882f6",
        "0x1c3944173abee256456b1498299fc501ad5bbd6f",
        "0x1db92e2eebc8e0c075a02bea49a2935bcd2dfcf4",
        "0x223fea5291d43a2fb372c5f332e9ade371ded0b5",
        "0x25c76fa90e90f5a5a6914da07baed9a9647c3dfd",
        "0x25c7d768a7d53e6ebe5590c621437126c766e1ea",
        "0x260b364fe0d3d37e6fd3cda0fa50926a06c54cea",
        "0x2ebf891f4718eb8367013d8d975a1e5afcae277f",
        "0x30ba21597f22aafa4b0e86c250c8a6eebaf0da54",
        "0x33ae83071432116ae892693b45466949a38ac74c",
        "0x35696b0847ed8428a098cba726b6514582aa5fc7",
        "0x35bf33df55472938ad314678962b7c69204f0a8a",
        "0x36cf90ac2d130b987aff0bded378525be36d9686",
        "0x371c31f9221459e10565cfe78937cbda5db1791c",
        "0x3bd0e57e2917d3d9a93f479b3a23b28c3f31a789",
        "0x3cef1f90be0f15f1573bda7a3e045cca9cff1d15",
        "0x3db4cb6d753d9e0ba7cc84e576d17dcd01b6b67d",
        "0x3ef28b7e18c510b8fa031d7f8a1bb24a83ccceb0",
        "0x412dd3f282b1fa20d3232d86ae060dec644249f6",
        "0x41be1bae9815d86820bcfd94a5161000fab448a6",
        "0x429b41e5eb73e2266affbc2d7a41553bd8f1ede1",
        "0x448c642074d7be4c5fc25929bb5536f772cd9d5c",
        "0x4865d4bcf4ab92e1c9ba5011560e7d4c36f54106",
        "0x495c70e181c45f80806dcbd733140361a0f75cc2",
        "0x495eb9345788ee6be50c9c36ed67ffa2beb3699f",
        "0x4be65e82a07b05686b092aa7d4426ce8ecd70ddc",
        "0x4ce053dfe58541e08f149c1050eb3df09d7a40bc",
        "0x4e19698c366f7dcd1cfad4d7f621b4d275bb1a6c",
        "0x4e5e17e8ef17c9a7ef9798ddf78f3a2c38367d16",
        "0x554e61af48afb53bd28670c3a2aa14ce858e63dd",
        "0x5a076b2d0941f2bc9b49d05d3a1ff9c7acdc5e78",
        "0x5c4e79cc7d5b66effcbb19e22cae0c92bff7276d",
        "0x61b2aa17c1c1114e7583bb31f777ff4bdc7ab717",
        "0x6206ae3781f9f1b6fbcf44c7240b1be14f3169ef",
        "0x62425cd6bdcb6bfe51558ea465b063486b70dc9f",
        "0x63bee4a7e4aa5d76dc6ab9b9d1852aabb9a40936",
        "0x651641299c7ec0aa44ad7ed9b7e12702fed2022f",
        "0x6522b7f9d481eceb96557f44753a4b893f837e90",
        "0x695f7dea85bf8c0aaafef0a9484e74834e28ce8b",
        "0x6b9b774502e6afaafcac84f840ac8a0844a1abe3",
        "0x6bd869be16359f9e26f0608a50497f6ef122ee3e",
        "0x6f4565c9d673dbdd379aba0b13f8088d1af3bb0c",
        "0x70167b76543c4a12b49b2f2b70cbf04d99345786",
        "0x70f58622158d7e609ae5839c4ad0d477f468863f",
        "0x72187db55473b693ded367983212fe2db3768829",
        "0x77439637cac35bedd63fc9e769d7819ca1d24a48",
        "0x79ae8c1b31b1e61c4b9d1040217a051f954d4433",
        "0x7a84c1f1aa344d466b0f161f57b0321b98faf6ee",
        "0x7c41c7d883dbbe1edfcefca9d7a7592dd30c8b51",
        "0x7e8c73462aaa9d61c801bd9f5682db014387621a",
        "0x801bfd99636ec8961f7e2d2dd0a296d726f5f1ae",
        "0x80a9b4aab0ad3c73cce1c9223236b722db5d6628",
        "0x80d45515a84e762c6497a089913f26b41235bf65",
        "0x855e9a74196764ab41adb3e3b76eaf9e3d6d6d48",
        "0x869bcee3a0bad2211a65c63ec47dbd3d85a84d68",
        "0x86dbaa55f0e65857b58109c3cb725deff4da3851",
        "0x8859eb340330492cb66f3b193e22696de8251e66",
        "0x88a1493366d48225fc3cefbdae9ebb23e323ade3",
        "0x89688768bf9e2e809ca3ac7e22fe5d2f849ef822",
        "0x8a2458f32e5ec9935f20e7c2e06e8d4820f726e5",
        "0x8c28e696c89200d423f9a5eea7347747e78ed25f",
        "0x8d6d3479c94bb95e737b72186192ff5e7fedf3a2",
        "0x8ed5b6bc3d85be31209fac182466e0bcc30ba3eb",
        "0x8fa129f87b8a11ee1ca35abd46674f8b66984d4a",
        "0x922fa922da1b0b28d0af5aa274d7326eaa108c3d",
        "0x93228d328c9c74c2bfe9f97638bbb5ef322f2bd5",
        "0x933646d78ede6f1ef5cf4a0a03e3a819c8057922",
        "0x9814ba501c7ad64bed5ac731d0a4f9a506e18f8a",
        "0x9cdb59516b37f5c1bd166bc41c5b9f68a57225bd",
        "0xa1abfa21f80ecf401bd41365adbb6fef6fefdf09",
        "0xa2e5e8a607562b7bda05d5820e569c290b43be6d",
        "0xa31231e727ca53ff95f0d00a06c645110c4ab647",
        "0xa4287bc8a021025974a642806cf2ab717b857380",
        "0xa4b9569bf942c3aad23c0c2d322fe4aff8e1bf30",
        "0xa7a93fd0a276fc1c0197a5b5623ed117786eed06",
        "0xa9acc15d8b74a01e5605eb0f1e815ba98e3a16af",
        "0xa9cf4aa55c675badb68519e3cfa8f4be942e6d11",
        "0xab97925eb84fe0260779f58b7cb08d77dcb1ee2b",
        "0xad85405cbb1476825b78a021fa9e543bf7937549",
        "0xb24692d17babefd97ea2b4ca604a481a7cc2c8ea",
        "0xb5873e333161e5b45adac57379ec2b15d861178d",
        "0xb829e684df8e31b402a4d4aedf3bbc18a52e7589",
        "0xbaed383ede0e5d9d72430661f3285daa77e9439f",
        "0xbce9aecd3985d4cbb9d273453159a26301fa02ef",
        "0xc22166664e820cda6bf4cedbdbb4fa1e6a84c440",
        "0xc273a2e3fc4c8f8610ebe51123dc32d233913da7",
        "0xc63fe58d36bef77a9a98df32a547537f45aac71d",
        "0xc6c6a48ee8e9f593724161c72414d76e94cda93f",
        "0xc93e48d89f2d6dbc1672908aa68ce7c24d0413b4",
        "0xcab3f132a11e5b723fc20ddab8bb1b858d00a8e8",
        "0xcacc7e55d0a4b10daaed40b3db7bfe11d23b6f94",
        "0xcf4b3a3be828b111eee75a0534a988c8d9284aae",
        "0xd07e6ab4b75b3da5a96b5e81064a65fc04f98814",
        "0xd4d2e6ebca6c94dd28a0935ae468012fdda5d35a",
        "0xd7c4d4b3f076bf9fe391190c42676b4dc269ee02",
        "0xd860962a96cd471bbe60a83c33e65011d40eb65f",
        "0xdae4fdcb7fc93738ec6d5b1ea92b7c7f75e4f2f6",
        "0xdba34cfc849738b2075fd28446902d3f1689c09d",
        "0xe1ab8c08294f8ee707d4efa458eab8bbeeb09215",
        "0xe46620553d6b28e5d2520b366942990d8654f243",
        "0xe5791f93b997c7fc90753a1f2711e479773a2a87",
        "0xec949f12a3acab835f3eed8b54b7361a8fbb3ee0",
        "0xee5b5b923ffce93a870b3104b7ca09c3db80047a",
        "0xee6281d94fed46a90379f2033b6bbdcda4ef462e",
        "0xefef30bd1cca520619306c95091ab18473febc5c",
        "0xf2f40c3bb444288f6f64d8336dcc14dbd929fd94",
        "0xf358d867bf928cb06408ff2b7564fce336e24de8",
        "0xf42aac93ab142090db9fdc0bc86aab73cb36f173",
        "0xf440139a62b2b939699c5b3e09f88e40464ab9bc",
        "0xf833685f98eba1b99947d418c9512d27c8193b1a",
        "0xf89d7b9c864f589bbf53a82105107622b35eaa40",
        "0xf8f061cfc030928a4acb8c4980911b4f5afc4002"
      ],
      "mention": {
        "end": 20,
        "start": 15,
        "text": "Bybit"
      },
      "owner": "Bybit"
    }
  ],
  "id": "v2-m15",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "53be6907813536821af5446c09d972c5f0b9c0e55b771973cfa2872728d06431",
  "schema": {
    "columns": [
      {
        "column": "from_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "from_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "5949a75ac1e23226d6419b0b2c95b3a582e143227a23a5500c0c523b6d210ce6"
}
```

Lý do tác giả: Returning contributions of all active known addresses exposes representative-wallet loss.

Sample: 36 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x18e296053cbdf986196903e889b7dca7a73882f6"
    ],
    [
      "number",
      "104815"
    ],
    [
      "number",
      "5"
    ]
  ],
  [
    [
      "string",
      "0xf89d7b9c864f589bbf53a82105107622b35eaa40"
    ],
    [
      "number",
      "47379"
    ],
    [
      "number",
      "166"
    ]
  ],
  [
    [
      "string",
      "0x260b364fe0d3d37e6fd3cda0fa50926a06c54cea"
    ],
    [
      "number",
      "24026"
    ],
    [
      "number",
      "4"
    ]
  ],
  [
    [
      "string",
      "0x651641299c7ec0aa44ad7ed9b7e12702fed2022f"
    ],
    [
      "number",
      "7056"
    ],
    [
      "number",
      "10"
    ]
  ],
  [
    [
      "string",
      "0x187c9fbf5bd0f266883c03f320260c407c7b4100"
    ],
    [
      "number",
      "6095"
    ],
    [
      "number",
      "12"
    ]
  ]
]
```

Multi-address: 36/119 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "6017222f18cf17de557d0ea4ab2580a3980c198d6427aab947027a5901ab48be",
  "case_sha256": "0b65a71981368cf73e60f4e06e1686d01954869a2aeda24a84499ae97b59a783",
  "id": "v2-m15",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "53be6907813536821af5446c09d972c5f0b9c0e55b771973cfa2872728d06431",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "5949a75ac1e23226d6419b0b2c95b3a582e143227a23a5500c0c523b6d210ce6",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m16 — multi_address

For all known Gate.io recipients, summarize incoming token events per token contract with total events, valid raw-value casts, and positive cast values; sort by token address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "gate_inbound_raw_value_validity"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:gate_inbound_raw_value_validity",
  "id": "v2-m16",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `gate_inbound_raw_value_validity`. Property focus: `None`.

```sql
SELECT token_address, COUNT(*) AS events, COUNTIF(value_cast_valid) AS valid_values,
    COUNTIF(value_bignumeric>0) AS positive_values FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE to_owner='Gate.io' GROUP BY token_address ORDER BY token_address
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0d0707963952f2fba59dd06f2b425ace40b492fe",
        "0x0fc73ffb9a0ded685234428e103d26b3762df460",
        "0x1c4b70a3968436b9a0a9cf5205c787eb81bb558c",
        "0x1f92332145465f3e536b7be301dde8d420478387",
        "0x234ee9e35f8e9749a002fc42970d570db716453b",
        "0x246a2ecd9626f9eda55fffbff5216ed417a904f5",
        "0x287a66c7d9cba7504e90fa638911d74c4dc6a147",
        "0x2bea9375c50f41f828c4e8eb0da3194449b5f062",
        "0x2cc81b80a293408a89084c77a0983de0730f731a",
        "0x354e0184a6a6e634ccb07388e2617e05e427563c",
        "0x356b9e62b20f4666e914fb99a9f651e5574f2bf7",
        "0x35b31ae2604dd81d9456205025ea02418dba8242",
        "0x37e1bf9ab62e523f358dafaca86151519f0a2f8d",
        "0x444c55075086f531a1c02730f41c46b9bbb00a39",
        "0x4bbe1961bd0a6cd1fe3cd8947be15bd8ae2ee562",
        "0x54c82d26624e85000d1387ee7c9580c3c6d7b5b7",
        "0x60618b3c6e3164c4a72d352bde263a5d15f9f7ee",
        "0x6596da8b65995d5feacff8c2936f0b7a2051b0d0",
        "0x66bbafc7269f1a9e5b454445585275f2b4ead28e",
        "0x68cdf5d77e75515edf7aa564d36fe3cbe751226e",
        "0x76bbb8d5dbedde9cb34882c9588dfa9def00b8bc",
        "0x7750fe679d47a9e00575ad46043297a234e83fa2",
        "0x7793cd85c11a924478d358d49b05b37e91b5810f",
        "0x7a3f9b7120386249528c93e5eb373b78e54d5ba9",
        "0x840760aed6bbd878c46c5850d3af0a61afcd09c8",
        "0x85faa6c1f2450b9caea300838981c2e6e120c35c",
        "0x8cd6437feaeb1a3a0cd65a16de2ad26bff1f5e43",
        "0x9bbe47fe66b3580551aac3124cf9fc6560252b19",
        "0x9f1daa35a4ef099c03744dfe3e67a39c4697ebe5",
        "0xa10eca918c71806ac55083d8ac942d4674b0f9ef",
        "0xa2df23519a6059dbc6f027f6cf8e59bdaecaf56f",
        "0xa2f10222b338c9ff3c953b129d1a49258f83f6c7",
        "0xa4992ccf2a74132936b87cbf28b5d52304ba3be7",
        "0xaaac1183d07c69f5befd22a06211690e953dca17",
        "0xb11c93f04bb7cc8d2d4aba47fcf73170bcea940d",
        "0xbcf03ce48091e6b820a7c33e166e5d0109d8e712",
        "0xc882b111a75c0c657fc507c04fbfcd2cc984f071",
        "0xccc5eeebe15291620be733997af60735618548d7",
        "0xcf6f5ec73942314c3ec864202b40dcbb1f9477a0",
        "0xd6a8047940a1f71df5f809919c10d9ba0a88786e",
        "0xd793281182a0e3e023116004778f45c29fc14f19",
        "0xd87c8e083aecc5405b0107c90d8e0c7f70996b84",
        "0xe39ba3f5bcbf0ef7ed31a07e799b8d2010c885cf",
        "0xf379a3d1ab6625eef34347d054cfaeafdf8f24a7",
        "0xffeb0f61871acdb4838dfc6d5082f063e738e421"
      ],
      "mention": {
        "end": 21,
        "start": 14,
        "text": "Gate.io"
      },
      "owner": "Gate.io"
    }
  ],
  "id": "v2-m16",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "19680fb1ea8d0e397396da8ad05e80df85cb62f01af9dffbbdc52c1994f009a2",
  "schema": {
    "columns": [
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "value_bignumeric",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "value_cast_valid",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "5f60f2e2d5d91c3a4edb439afb709b0208ff4c670b9613273b72fdff132d2536"
}
```

Lý do tác giả: Raw numeric cast checks do not imply normalized ERC20 amounts.

Sample: 405 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x0000000000085d4780b73119b644ae5ecd22b376"
    ],
    [
      "number",
      "4"
    ],
    [
      "number",
      "4"
    ],
    [
      "number",
      "4"
    ]
  ],
  [
    [
      "string",
      "0x0000000000095413afc295d19edeb1ad7b71c952"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "0x0000000000c5dc95539589fbd24be07c6c14eca4"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "2"
    ]
  ],
  [
    [
      "string",
      "0x000000fa00b200406de700041cfc6b19bbfb4d13"
    ],
    [
      "number",
      "3"
    ],
    [
      "number",
      "3"
    ],
    [
      "number",
      "3"
    ]
  ],
  [
    [
      "string",
      "0x000006c2a22ff4a44ff1f5d0f2ed65f781f55555"
    ],
    [
      "number",
      "5"
    ],
    [
      "number",
      "5"
    ],
    [
      "number",
      "5"
    ]
  ]
]
```

Multi-address: 8/45 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "e78e596e99b837e8653cc49527cca60d5eed36f1337e836204e31a48a1f98feb",
  "case_sha256": "8f1f3e1a1ade57e3e71aaac55720954562f1b3c4639955d1a62aa5b36fdcfb0e",
  "id": "v2-m16",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "19680fb1ea8d0e397396da8ad05e80df85cb62f01af9dffbbdc52c1994f009a2",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "5f60f2e2d5d91c3a4edb439afb709b0208ff4c670b9613273b72fdff132d2536",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m17 — multi_address

Across known Binance recipients, report each active date's incoming outer transaction count and number of distinct non-null transaction types; order by date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "binance_inbound_daily_type_diversity"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:binance_inbound_daily_type_diversity",
  "id": "v2-m17",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `binance_inbound_daily_type_diversity`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS incoming,
    COUNT(DISTINCT transaction_type) AS types FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Binance'
    GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x030e37ddd7df1b43db172b23916d523f1599c6cb",
        "0x110daa3f3fac2a54bb508ac94f31f9df77057b29",
        "0x150aace136535a374f05b5ee209b6a61396db1c0",
        "0x18e226459ccf0eec276514a4fd3b226d8961e4d1",
        "0x1b46970cfe6a271e884f636663c257a5a571fb2c",
        "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        "0x22132139bf7f3921b1cadeab931f4fbf7bf2bc9e",
        "0x26bff98f6f37c8d560684eaf2afd1149bf76633e",
        "0x28c6c06298d514db089934071355e5743bf21d60",
        "0x308a2a0712570daeea77c8ba9c27a32cdc4000d4",
        "0x32e11a20337ebc79abd0eeab2d91bafbd9591149",
        "0x38aaef3782910bdd9ea3566c839788af6ff9b200",
        "0x42a93a9f5cfda54716c414b6eaf07cf512f46ead",
        "0x43684d03d81d3a4c70da68febdd61029d426f042",
        "0x4976a4a02f38326660d17bf34b431dc6e2eb2327",
        "0x4aec0e98fc1fb55b9cc2faaa7a81acca42cb4e96",
        "0x4ed6cf63bd9c009d247ee51224fc1c7041f517f1",
        "0x4fdfe365436b5273a42f135c6a6244a20404271e",
        "0x56eddb7aa87536c09ccc2793473599fd21a8b17f",
        "0x5a1e5b56aa33c056ed7bb93b88b1774a456f6694",
        "0x5a52e96bacdabb82fd05763e25335261b270efcb",
        "0x6357e4bdaff733dfe8f50d12d07c03b3bed0884b",
        "0x6454ac71ca260f99cca99a3f4241dfda20cfa965",
        "0x756b86fd69914db92229c07c7393d7d9948fed33",
        "0x835678a611b28684005a5e2233695fb6cbbb0007",
        "0x8498fc7280668874a5da79e87ca0896f4f0d1196",
        "0x86523c87c8ec98c7539e2c58cd813ee9d1a08d96",
        "0x87433fec6f8d9df13d1e17c4b11364ecd2e93a51",
        "0x8a6f8404c9ea4c33502a3f6a4bf8e41ef5ca10ea",
        "0x8e609ac80f4324e499a6efd24f221a2caa868224",
        "0x9696f59e4d72e237be84ffd425dcad154bf96976",
        "0x98adef6f2ac8572ec48965509d69a8dd5e8bba9d",
        "0xa345dcb63f984ed1c6d1a8901e0cdbd13b2b4d19",
        "0xa64b436964e7415c0e70b9989a53e1fb9a90e726",
        "0xa7c0d36c4698981fab42a7d8c783674c6fe2592d",
        "0xa9fc92f6faf9f103fc81d17de3e8daadc888afff",
        "0xad354cfbaa4a8572dd6df021514a3931a8329ef5",
        "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",
        "0xc47b3342df38d747033b6041f54e4e5e300c8d18",
        "0xc8daf809c7d7c27dd62d006196d8901ba57e5eae",
        "0xd27b39cb25fed854f9fce3a4e451f96e62089e48",
        "0xdbeb6c856ef5a167f5e1acb9dff65adb33207d8b",
        "0xdbf28a152d79b2b98eecd229b412ee98d21ec3bc",
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
        "0xe1940f578743367f38d3f25c2d2d32d6636929b6",
        "0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055",
        "0xf16924b866e58ac916ba933d1f1034bcbbb1958c",
        "0xf1f8cb7633d3ca3fd06c084d18ca5491a85ae9b4",
        "0xf977814e90da44bfa03b6295a0616a897441acec",
        "0xfc8059c2fb22005ede8a86d388e3d0f536a4dd44"
      ],
      "mention": {
        "end": 20,
        "start": 13,
        "text": "Binance"
      },
      "owner": "Binance"
    }
  ],
  "id": "v2-m17",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "b38b300a13b84625ba3226c74bfb8599f66e320bfe270d8db2c846ad66379550",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "transaction_type",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "10dbd6c568f7a458d6a8268885e3f22399196416d11f67462a0b9d8f791581c3"
}
```

Lý do tác giả: Different projection and aggregation intent from receipt outcome analysis.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "65"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "84"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "81"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "71"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "87"
    ],
    [
      "number",
      "1"
    ]
  ]
]
```

Multi-address: 8/50 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "73fd96775f39e498c15fceaa0d4ce7a3724ba9dd7338855bbfa1758af73ad6d7",
  "case_sha256": "bb70b0b139290994c29ec946e0b05054d8774b58e6912b81621ef969caf281b8",
  "id": "v2-m17",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "b38b300a13b84625ba3226c74bfb8599f66e320bfe270d8db2c846ad66379550",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "10dbd6c568f7a458d6a8268885e3f22399196416d11f67462a0b9d8f791581c3",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m18 — multi_address

Combining known Bitstamp recipients, report each date with incoming token events, its event count and distinct token count; order by date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "bitstamp_inbound_daily_token_counts"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:bitstamp_inbound_daily_token_counts",
  "id": "v2-m18",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `bitstamp_inbound_daily_token_counts`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
    COUNT(DISTINCT token_address) AS tokens FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Bitstamp'
    GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x1522900b6dafac587d499a862861c0869be6e428",
        "0x3262f13a39efaca789ae58390441c9ed76bc658a",
        "0x48ec5560bfd59b95859965cce48cc244cfdf6b0c",
        "0x4a2d57d669f2194fa7b5df619cba9f33ccea26bd",
        "0x4f90356dbc2286b4be8cf14738b05e3a9e9c0c7e",
        "0x593aebee9117eea447279e5973f64c68d8e977a0",
        "0x5c95a672e34b3252482ed9a215f2926d2887845d",
        "0x7f604d597c15b2e2f60dc645844f68b1d781b752",
        "0x88a4df73aac310484c60c4c0ac4904cab938c20b",
        "0xa3f74537f048b893d726c173cb322fd21a28b18a",
        "0xb66410ae75317faf13dba869b6df7b30892d1e46",
        "0xb6928299bb62226e6ad3c2dc22e490cdb2033b68",
        "0xee9fb7a615cb76b46d26be6ebc9114a627a81c5b",
        "0xf666814c2ae92ca0e06667f80dac1eb8a97e48ae"
      ],
      "mention": {
        "end": 24,
        "start": 16,
        "text": "Bitstamp"
      },
      "owner": "Bitstamp"
    }
  ],
  "id": "v2-m18",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "4e33186d179456b9c4de90e4a7d9b32a45a5885ae658fa43d6ea0a1b59a9942e",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "005345e25f2610be3ddf1c676c0442908f2e341700dddd740ec14142cec1be3f"
}
```

Lý do tác giả: Known address membership is complete even when some addresses are inactive.

Sample: 27 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "9"
    ],
    [
      "number",
      "7"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "6"
    ],
    [
      "number",
      "4"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "10"
    ],
    [
      "number",
      "7"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "5"
    ],
    [
      "number",
      "3"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "3"
    ],
    [
      "number",
      "3"
    ]
  ]
]
```

Multi-address: 6/14 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "761784ebcd8e60e36905f6ded59b07d73c544a99198b1811549397d61f1e434e",
  "case_sha256": "6dbcd1086a89671f13b6f1af3f01309afc3910edaf9ead2858fe487303f3719d",
  "id": "v2-m18",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "4e33186d179456b9c4de90e4a7d9b32a45a5885ae658fa43d6ea0a1b59a9942e",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "005345e25f2610be3ddf1c676c0442908f2e341700dddd740ec14142cec1be3f",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m19 — multi_address

Across known HTX senders of token events, rank recipient addresses by distinct token contracts received, also showing event count; return twenty rows and break ties by event count descending then recipient address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "htx_outbound_token_counterparty_breadth"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:htx_outbound_token_counterparty_breadth",
  "id": "v2-m19",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `htx_outbound_token_counterparty_breadth`. Property focus: `None`.

```sql
SELECT to_address, COUNT(DISTINCT token_address) AS tokens, COUNT(*) AS events
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_owner='HTX' GROUP BY to_address
    ORDER BY tokens DESC, events DESC, to_address LIMIT 20
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0511509a39377f1c6c78db4330fbfcc16d8a602f",
        "0x07ef60deca209ea0f3f3f08c1ad21a6db5ef9d33",
        "0x0a98fb70939162725ae66e626fe4b52cff62c2e5",
        "0x1062a747393198f70f71ec65a582423dba7e5ab3",
        "0x1205e4f0d2f02262e667fd72f95a68913b4f7462",
        "0x18709e89bd403f470088abdacebe86cc60dda12e",
        "0x18916e1a2933cb349145a280473a5de8eb6630cb",
        "0x2abc22eb9a09ebbe7b41737ccde147f586efeb6a",
        "0x30741289523c2e4d2a62c7d6722686d14e723851",
        "0x34189c75cbb13bdb4f5953cda6c3045cfca84a9e",
        "0x3d655889d197125fb90dcb72e4a287a8410ed1b9",
        "0x42dc966b7ecc3c6cc73e7bc04862859d5bddce65",
        "0x46705dfff24256421a05d056c29e81bdc09723b8",
        "0x4fb312915b779b1339388e14b6d079741ca83128",
        "0x598273ea2cabd9f798564877851788c5e0d5b7b9",
        "0x5c985e89dde482efe97ea9f1950ad149eb73829b",
        "0x6663613fbd927ce78abbf7f5ca7e2c3fe0d96d18",
        "0x6748f50f686bfbca6fe8ad62b22228b87f31ff2b",
        "0x6b2286fc3a9265bab3f064808022aca54de4b6ce",
        "0x918800e018a0eeea672740f88a60091c7d327a79",
        "0xa03400e098f4421b34a3a44a1b4e571419517687",
        "0xa5d7f0f7027fa8f4d1be8042e1e43bbdec36951e",
        "0xa929022c9107643515f5c777ce9a910f0d1e490c",
        "0xab5c66752a9e8167967685f1450532fb96d5d24f",
        "0xadb2b42f6bd96f5c65920b9ac88619dce4166f94",
        "0xc589b275e60dda57ad7e117c6dd837ab524a5666",
        "0xcac725bef4f114f728cbcfd744a731c2a463c3fc",
        "0xdb0e89a9b003a28a4055ef772e345e8089987bfd",
        "0xe4818f8fde0c977a01da4fa467365b8bf22b071e",
        "0xe8d8a02601f54acb6fb69537be1f1d7cc76ccd8c",
        "0xe93381fb4c4f14bda253907b18fad305d799241a",
        "0xeee28d484628d41a82d01e21d12e2e78d69920da",
        "0xf881bcb3705926cea9c598ab05a837cf41a833a9",
        "0xfa4b5be3f2f84f56703c42eb22142744e95a2c58",
        "0xfd54078badd5653571726c3370afb127351a6f26",
        "0xfdb16996831753d5331ff813c29a93c76834a0ad"
      ],
      "mention": {
        "end": 16,
        "start": 13,
        "text": "HTX"
      },
      "owner": "HTX"
    }
  ],
  "id": "v2-m19",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "b5ad0deb0c3c806ba6e7440e44a851d1207e1c981bf0d530bf96f1510226f78c",
  "schema": {
    "columns": [
      {
        "column": "from_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "a2b5b36b0e35ffb1c0cbc743cfb80e2aaef05646b4098136f60bcdc8cdefff56"
}
```

Lý do tác giả: Canonical owner HTX avoids the ambiguous token alias Huobi.

Sample: 20 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x9be5b8a7314552fa47feb1355cd5b4adc7bb7516"
    ],
    [
      "number",
      "601"
    ],
    [
      "number",
      "626"
    ]
  ],
  [
    [
      "string",
      "0xb6aadd5cbf25e7ce4e6d421f02d3deb650ed5602"
    ],
    [
      "number",
      "61"
    ],
    [
      "number",
      "140"
    ]
  ],
  [
    [
      "string",
      "0xf0a6d09f6b53a2ce72926648af008a0fca32921a"
    ],
    [
      "number",
      "57"
    ],
    [
      "number",
      "120"
    ]
  ],
  [
    [
      "string",
      "0x3c76d401744ac9c988d9e965c2f05a548c8d3591"
    ],
    [
      "number",
      "55"
    ],
    [
      "number",
      "108"
    ]
  ],
  [
    [
      "string",
      "0x3bacb00058feed76e3456bb9ca0c0ab91c8d093e"
    ],
    [
      "number",
      "49"
    ],
    [
      "number",
      "106"
    ]
  ]
]
```

Multi-address: 3/36 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "c58fc84c00f1433b11b8b7007f71cc75180fec55dc6eb11a2f2e8a908083cbc1",
  "case_sha256": "1d6d7a8e5d4c0cf41f6995009a10e7e3d91211cfc6dc89783c13932643ce9185",
  "id": "v2-m19",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "b5ad0deb0c3c806ba6e7440e44a851d1207e1c981bf0d530bf96f1510226f78c",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "a2b5b36b0e35ffb1c0cbc743cfb80e2aaef05646b4098136f60bcdc8cdefff56",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-m20 — multi_address

For all known Crypto-com addresses, give per-token counts of sent, received and either-role transfer events. Count an event between two group addresses once in the either-role total; sort by token address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "cryptocom_token_boundary_counts"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:cryptocom_token_boundary_counts",
  "id": "v2-m20",
  "primary_group": "multi_address",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `cryptocom_token_boundary_counts`. Property focus: `None`.

```sql
SELECT token_address, COUNTIF(from_owner='Crypto-com') AS sent,
    COUNTIF(to_owner='Crypto-com') AS received, COUNT(*) AS involved FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE from_owner='Crypto-com' OR to_owner='Crypto-com'
    GROUP BY token_address ORDER BY token_address
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x46340b20830761efd32832a74d7169b29feb9758",
        "0x6262998ced04146fa42253a5c0af90ca02dfd2a3",
        "0x72a53cdbbcc1b9efa39c834a540550e23463aacb",
        "0x7758e507850da48cd47df1fb5f875c23e3340c50",
        "0xcffad3200574698b78f32232aa9d63eabd290703",
        "0xf3b0073e3a7f747c7a38b36b805247b222c302a3"
      ],
      "mention": {
        "end": 24,
        "start": 14,
        "text": "Crypto-com"
      },
      "owner": "Crypto-com"
    }
  ],
  "id": "v2-m20",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "either"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "d534d816514576aa9124cc252a292b93474526a9f3a986a3de81ef871baf7cc8",
  "schema": {
    "columns": [
      {
        "column": "from_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "0305f0b193a72cf4d7556c9449442cd5f5a8ce7f6cd55fc6753daf38f3192a3a"
}
```

Lý do tác giả: Separate token identities; internal events do not double the either-role total.

Sample: 232 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x000006c2a22ff4a44ff1f5d0f2ed65f781f55555"
    ],
    [
      "number",
      "8"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "8"
    ]
  ],
  [
    [
      "string",
      "0x00006100f7090010005f1bd7ae6122c3c2cf0090"
    ],
    [
      "number",
      "1"
    ],
    [
      "null"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "0x00c83aecc790e8a4453e5dd3b0b4b3680501a7a7"
    ],
    [
      "number",
      "26"
    ],
    [
      "number",
      "4"
    ],
    [
      "number",
      "26"
    ]
  ],
  [
    [
      "string",
      "0x031de51f3e8016514bd0963d0b2ab825a591db9a"
    ],
    [
      "number",
      "11"
    ],
    [
      "number",
      "5"
    ],
    [
      "number",
      "14"
    ]
  ],
  [
    [
      "string",
      "0x04fa0d235c4abf4bcf4787af4cf447de572ef828"
    ],
    [
      "number",
      "4"
    ],
    [
      "number",
      "8"
    ],
    [
      "number",
      "11"
    ]
  ]
]
```

Multi-address: 3/6 active; union khác mọi địa chỉ riêng=True.

Review binding:

```json
{
  "annotation_sha256": "626c7f5af4398eae6f8843820da6787f7d412238bfd2b59ba32c748d4e68a468",
  "case_sha256": "b54307fa3624ae6a473f477933635570ffbacc91baf6fbe757d0f7ba1475de34",
  "id": "v2-m20",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "d534d816514576aa9124cc252a292b93474526a9f3a986a3de81ef871baf7cc8",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "0305f0b193a72cf4d7556c9449442cd5f5a8ce7f6cd55fc6753daf38f3192a3a",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a01 — alias

For OKEx, find the active date with the largest fraction of failed outgoing outer transactions among known 0/1 receipt statuses; return date, failed count, known-status count and fraction, breaking fraction ties by earlier date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "okex_peak_outbound_failure_date"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:okex_peak_outbound_failure_date",
  "id": "v2-a01",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `okex_peak_outbound_failure_date`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNTIF(receipt_status=0) AS failed,
    COUNT(*) AS known_status, SAFE_DIVIDE(COUNTIF(receipt_status=0),COUNT(*)) AS fraction
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_owner='OKX' AND receipt_status IN (0,1)
    GROUP BY day ORDER BY fraction DESC, day LIMIT 1
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0003b5aa5e30e97fcc596bb5d0f3a75255e08d4e",
        "0x01c2a9e7eeaee29b03708692ba5e1515036451e8",
        "0x01f66697aec1e7de7773115243247952245fd3a4",
        "0x01f7cea182239f9e9caf0f1ce0744bcb23c20585",
        "0x03ae1a796dfe0400439211133d065bda774b9d3e",
        "0x03d0aad7c6a0b36f47d852a28ff0fb7bc9ae46b6",
        "0x0475dd0e4194422a8cac486dc69173f535d0baf4",
        "0x0607c628054a7db3d36eed7c4a408eda8260de09",
        "0x06324bad3913cb69cb5e748a3ed72f9d692324bb",
        "0x06959153b974d0d5fdfd87d561db6d8d4fa0bb0b",
        "0x06d3a30cbb00660b85a30988d197b1c282c6dcb6",
        "0x073f564419b625a45d8aea3bb0de4d5647113ad7",
        "0x0750b999e493112c88cb226a13a2a67419f06ad6",
        "0x0799ddbf6f14db566ca4df4ff0575c4cc1e7749c",
        "0x08af9c4767236221c55069dd523e2f7a0013e898",
        "0x08f619716db7c6245401b543e59acac1d25cb483",
        "0x0938c63109801ee4243a487ab84dffa2bba4589e",
        "0x0a133528245eaf5bab72dc05a9dd8e0ea4b982f9",
        "0x0c48511102453352fe570370672cd556bf0e63f9",
        "0x0ff9491b236a36cc183823e39d7532194143fdb1",
        "0x11b113383ce08e84001dc614f141ae4c27221e31",
        "0x1278678b5b17eba14b313d287659ae9f3aa7c087",
        "0x12a8bdc0470ab29a229d828526641b7d1f170fcf",
        "0x16b5016803bcb4915701efc0a3b471bd4c168d93",
        "0x173810f8ca9c4c631aeb1d6c36d007f054fee980",
        "0x17e91b98988937cb59dc163b0b11781f9785591a",
        "0x1811068091a2459ee38a8dde52cce5b2acfc1b61",
        "0x19abcd6b8516d2b4d9aa3bbf700b38a30dc154fc",
        "0x1a557020c52f9d2495b2c12eb137ee7b5d467a4f",
        "0x1c628a9c66ff63454a4526a4f2b8af250da8d086",
        "0x1dfc6bec8499fcb5e3151c7c6d27feb9d7eae1d4",
        "0x1e43e7a911b1b0229ea7d64e11ae260c482a0870",
        "0x221ac9e1920932e95adf0c941f3524157f4bda4f",
        "0x25236e080106b5387df201fbbd9a6b870917676d",
        "0x26704ccfcd45b5780dcd58d38b12f5e0cdb481a0",
        "0x267b51c97632225da2b2e49aebe59eef1af32653",
        "0x276cdba3a39abf9cedba0f1948312c0681e6d5fd",
        "0x297611b7accb7f24032c27b3a496465624c7ef50",
        "0x2c8fbb630289363ac80705a1a61273f76fd5a161",
        "0x30c1dcde81e5dbf3121d0408abc7908980e83ae2",
        "0x313eb1c5e1970eb5ceef6aebad66b07c7338d369",
        "0x32dc16f4631a27b042a974d05c1ccf8a303e8199",
        "0x3425519651e4c42833633fe5c0e24ed89c1023a3",
        "0x3b9694465483cbb677b700a91c26f487193a6e03",
        "0x3b98b9e9cb75c1cb1729aab8f09ced2936505e4f",
        "0x3bb00393bfa5e76b7f31e93948f7d3cef12942ad",
        "0x3c5883c650d600bd543a9b5c8d9a3a6f5d16b8f4",
        "0x3d2335cac7b31411467ef03168c5869452fb7e86",
        "0x3d55ccb2a943d88d39dd2e62daf767c69fd0179f",
        "0x3e7d48c8ae2e50c2b9adedc8e276d3cc92b39458",
        "0x3f482c72a2b3e777746f5755cc0ff1323ea2ad16",
        "0x400d8280acf364f683e989462879fd8dd358067d",
        "0x4106a4be14867c70e52c51b9805514ae2e16de64",
        "0x42436286a9c8d63aafc2eebbca193064d68068f2",
        "0x42797deffe266a55fdc4c98d7d3885d7058cb3e5",
        "0x42cf18596ee08e877d532df1b7cf763059a7ea57",
        "0x445f16314284b43dfa1fd3cd77b9dea4a1bebd97",
        "0x45d9c02baed2d1670f7bad40fb5f657a05068d52",
        "0x45f329ff834a84fccea2319f91e1993540b22a2a",
        "0x461249076b88189f8ac9418de28b365859e46bfd",
        "0x47eb32dea1ab1436187939fa72d6d5ff884a87da",
        "0x48480aad203e8b030f82754b3c75869c9895c6bf",
        "0x48c4c83be7e3884ee5043a3abe5115eb020b5f4a",
        "0x4a11078a99b118bbfee78a5c187d98d264360433",
        "0x4bcbaf34862e6480329477917cf5cd7b9537a98d",
        "0x4d19c0a5357bc48be0017095d3c871d9afc3f21d",
        "0x4d619eb6db0b9b6184d9881c4828c0effff84eda",
        "0x4e2757e46103556f98d4d036d8efe18389b89f51",
        "0x5041ed759dd4afc3a72b8192c143f72f4724081a",
        "0x52738a51882f35d6b25a3fd0c86089ddbd206821",
        "0x52b311c52436789f3754bd199bf3886b8ccbab4c",
        "0x539c92186f7c6cc4cbf443f26ef84c595babbca1",
        "0x559432e18b281731c054cd703d4b49872be4ed53",
        "0x56fd42ecd77c88bdd959be54af10d1759b473dff",
        "0x593878f92dde464fc4e3b17cd7cc87117dca753c",
        "0x5a150733cb59bbdd5c7398a8fe7da7f97c8a213a",
        "0x5b27e98516fd2bd5001d4dfe3f5a2263f702f634",
        "0x5b873ffcad5dccdc61c1a53c391fb76cb316a841",
        "0x5c52cc7c96bde8594e5b77d5b76d042cb5fae5f2",
        "0x5ca38fb7cf2b587026a1650f0d2b0a13c41f5d0f",
        "0x5f5105b9a19e301208844263806df9b7212e655d",
        "0x5f8215ee653cb7225c741c7aa8591468d1f158b8",
        "0x608c27519c5e65a61cfc1d2c9e658e5c57a2e3d7",
        "0x611f7bf868a6212f871e89f7e44684045ddfb09d",
        "0x65a0947ba5175359bb457d3b34491edf4cbf7997",
        "0x65e891ec42fcaa19459fe6221163e1a3f8cf7ea6",
        "0x6667a4b7eff4a0b86781fb3b187622cd3c257f09",
        "0x66e6bdac6fae819f944901e3b6ecc9bfff61a706",
        "0x6709383e211ab08a6e3270532e756220400424a6",
        "0x68841a1806ff291314946eebd0cda8b348e73d6d",
        "0x68b5e9e083bfc28c33cfbf3f19d33e629015e907",
        "0x68e2ea1622aa67fb3a01a66d132daed8a48d1662",
        "0x69a722f0b5da3af02b4a205d6f0c285f4ed8f396",
        "0x6a4561ef7874a76b4bf0d3edca31dfcd51603414",
        "0x6b7ba57e1d43c2c975ba25139a04d193e64a11d0",
        "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
        "0x6d29fc1267b1691c0cd43a8d35b27135957ffea9",
        "0x6d8c32fcf2d95ff410ba492f6694f18cbee55ce1",
        "0x6dc1a070425f437ac08bb108f7093b177d7af3a6",
        "0x6ededbad1e864105fa2538ddfbf4e7214b9e6529",
        "0x6fb624b48d9299674022a23d92515e76ba880113",
        "0x6fd41d4a272247fd1104c710909a4af8bd38f522",
        "0x728d92a8023bfbe0d4f3fdd549ed3b4996a0eba9",
        "0x730df969955c0a2fa9e8f2484e9741a363afdbb3",
        "0x739768219c831ec1f747bf904f0e25c2d99c7dc1",
        "0x767a905b77b0a40801488c6af8b8b5992b43511c",
        "0x778e456fbfd14075f5ddbccf9be2d6a48e3b1ecb",
        "0x7926c83479e2708edfd83a39d62084693e192298",
        "0x793aa889e19a130ee4cb8b63c79aa3bdccc663cb",
        "0x7a91e803db0e58b6fecc4e42c86b366778475e3c",
        "0x7a93539c1bf9a96f87044925deb7a0849266213e",
        "0x7c7061221666e41b87ca5817cfa2fcac09b3d943",
        "0x7cfe28094f4531809992ed89060a61413116365d",
        "0x7d4a2c448fe5b07c62228140417b3565bbe1b86b",
        "0x7eb6c83ab7d8d9b8618c0ed973cbef71d1921ef2",
        "0x7f61dc44c15ca818f96c6fc40739e5aa732e240c",
        "0x7fe830ec109e112f549d6ee9d3e9540e7785997b",
        "0x7fea5b4568751533039179116e372e26b6b41b13",
        "0x80335e658ee73756bb8220bdb77f99e98322035f",
        "0x8167a1ebf00ff5886d1b5908419bb1159d8cf6a4",
        "0x83a32a54d31ee4f1f9dffad2a63a6d214e469ec3",
        "0x85dcd76d4fbd3aa0c85c27b9441222c19a14134b",
        "0x868dab0b8e21ec0a48b726a1ccf25826c78c6d7f",
        "0x86aee064cc073d0dc95ba86633067b2c615040bb",
        "0x8734bca44102bf8a663e1ba112308504606e1b08",
        "0x87d0d6c8cdd71a658ecf1566f13e4cbc562beaf9",
        "0x88c94d8e7d4203b185b3beb0a7b15a6b4f36b2a2",
        "0x89b2f6dafc9d46ce0ed7d7e45a4972d14f037a19",
        "0x8ad740adce08f2f3579884eac0a12e581304ac3b",
        "0x8c3cb9665833fd9f79eb14cba16d82bbab6f22d8",
        "0x8f1aae22d0b4335945950d0bbd0f3743d3fc6f22",
        "0x91d40e4818f4d4c57b4578d9eca6afc92ac8debe",
        "0x92ea7496eba5f001d620005f88f3e8e686e3d4ea",
        "0x932d7d2cbc06234919f34802a22a914282a00f87",
        "0x96fdc631f02207b72e5804428dee274cf2ac0bcd",
        "0x9723b6d608d4841eb4ab131687a5d4764eb30138",
        "0x98ec059dc3adfbdd63429454aeb0c990fba4a128",
        "0x9938ee74ba7a5c1abcd157272a18fcfc9ec9e8d5",
        "0x994d24172fcfafbb5fce0ac5392078fa1c025448",
        "0x9b645675e8d64759e5c36e30dcb766d8cec3d34f",
        "0x9ce5a8098270f07a0a56398febda76a8ee2858c4",
        "0x9d65bf1bce7a10814228f4d81d8cf99a6b0f44aa",
        "0x9db8b860692c41e709d48d089de64cf01e6e317e",
        "0x9e13bae2256f968d02fe0129a0f51788f4e2472f",
        "0x9e3bb2cd5a89fcc4b826230b144c4917881bea85",
        "0xa01533d5c66a4886d3bb39b156507d9de65653e6",
        "0xa2684f75740cfff46c29bae79a4ecc43043c003d",
        "0xa27cef8af2b6575903b676e5644657fae96f491f",
        "0xa68cfe488a785c8b38ce2db6c45cfe07cb620c2d",
        "0xa7efae728d2936e78bda97dc267687568dd593f3",
        "0xa9ac43f5b5e38155a288d1a01d2cbc4478e14573",
        "0xacf961ae22191f0d080497a3a3b427180f18ed67",
        "0xae0cbaba071d58efc278a815b2cb652286e192ff",
        "0xb072b7dc9521d97a3f12b04beb1e497f8875ec52",
        "0xb0a27099582833c0cb8c7a0565759ff145113d64",
        "0xb47a0ac7798d8308467b2b96ac632ed43c9cb6d7",
        "0xb4ec508adeb174610b4295e233a458b3475964f7",
        "0xb640e1e5a5f726a054cd518c968dfdac8c421ee5",
        "0xb8ede418d8116113efb7644a792e5d97aade6138",
        "0xb99cc7e10fe0acc68c50c7829f473d81e23249cc",
        "0xba0a39d37151fa4f938bec51cdae4675105760f4",
        "0xba7fd71d309bc0e96b64022fd8fea7299b256159",
        "0xba96a3f3d5e9f13a5f93c37001f946d42eb2e165",
        "0xbda23b750dd04f792ad365b5f2a6f1d8593796f2",
        "0xbe2ec156292587338d4e9f80f5439e6152d56fc5",
        "0xbf94f0ac752c739f623c463b5210a7fb2cbb420b",
        "0xbfbbfaccd1126a11b8f84c60b09859f80f3bd10f",
        "0xbfef5c888bb7a0a6b14b4c3ccc4364ea81aa573f",
        "0xc0d01a27fd89e6bbc68f43e94ade3dfca2c27674",
        "0xc18475f347cc757b3cc49025820248a5f27d97ce",
        "0xc275bf069df3e63184a1222359114b805b6cd2f5",
        "0xc5267f13b9b4ba7bb73bdd53a2a3c944733a2961",
        "0xc5451b523d5fffe1351337a221688a62806ad91a",
        "0xc5a93444cc4da6efb9e6fc6e5d3cb55a53b52396",
        "0xc6724cf116573eab588fb0d73dcdc16929493cea",
        "0xc68c17e6eec0fde3605c595c9b98de5c1a4cc3e4",
        "0xc708a1c712ba26dc618f972ad7a187f76c8596fd",
        "0xcab0c0a224bad992085430f87dc1855342763a88",
        "0xcb0963264231bb08b2f680ab3ed89a49c9641bb3",
        "0xcba38020cd7b6f51df6afaf507685add148f6ab6",
        "0xcbc767b519394a9e4682cc9a15dcd18c46a6045b",
        "0xcc5d36fb0126515cb7988bbeee8445f03c304b2a",
        "0xcd5bd47d3d1d8412b241ce9015c5032142948c12",
        "0xce9abe75d561f065f1c4adb188b260df9de32ca7",
        "0xd03e6a53a3298ba1cd9b0dbf525ad728f4f8ad6e",
        "0xd049e4ddf1133af3a7a27390b4c9018141df1a49",
        "0xd19d3341227967610b94e7aebe8c971d2d48f419",
        "0xd266529641eeffaa2b2a0bc99daa5b32ef241078",
        "0xd576392cb12b7749ba33f8d223f64e65ee32f03f",
        "0xd5f8c864f21824daf3a4b22d9c33693642ed7634",
        "0xd7764b4305bcca935e38a450e7956822113374b6",
        "0xd7f4a5613b38cb8c09229b7aed99803242fdf0a0",
        "0xd99d81949146b4c13a4a42c9a6addbbd2db932ad",
        "0xd9a3c9ba5aa4415a53b9190bcb00f14472790a70",
        "0xdad24044e36587d975d7b5bceb6467fac21e0c81",
        "0xdb0ed345cb52c2f2457918afa3eb4b682e264ad0",
        "0xdc3ce895714844b4775b6d06f0dae513542cee10",
        "0xdce83237fbf279c4522e7cac4b10428e2b8694da",
        "0xddf81e81ab956695600d8639356c045e5c8a8c94",
        "0xde01974fb4a98bafd7cbf8a06ecf6dcc94d7283f",
        "0xdeb6ad2a7820839464da79bac953ae6189215443",
        "0xe2effe5bd0617a5a2dc1ee579565911cef3a223b",
        "0xe3bb282457ce7b3be31f0441f3fc051b9fc6a9c3",
        "0xe404fe9b7b0d0e88e77731517202fb392f67cd74",
        "0xe6eea9812ccc5981ccf0ab333610c42c2d92d146",
        "0xe7b29ff45392876143c7b863d57fb2326afe0ff1",
        "0xe7c8fdd899ab06ac1023e8a3e867c5fa7e751450",
        "0xe9172daf64b05b26eb18f07ac8d6d723acb48f99",
        "0xe983845a04c681a295dd9ce1fa8c2c8505932da3",
        "0xea3b7dac6b96502a04c701d5e71b51912f70143f",
        "0xeaed6576334b003d1c5c4797d9c7bb025a20c038",
        "0xeb196a61f9a1e35bf5053b65aaa57c5541dcba86",
        "0xedc0a430dd32eb8cfcc3a344979f0e21bc48bf0d",
        "0xee1c6537e589a15a15f80961f5594c57bed936fb",
        "0xf02e3c0095f6de36c76364d4cc53eb06d1288fc1",
        "0xf418263a6468c80d3bcb71033c56aacf81b241ba",
        "0xf59869753f41db720127ceb8dbb8afaf89030de4",
        "0xf683b33e21e85ee6c0e25af2fff5b2b115f32617",
        "0xf7858da8a6617f7c6d0ff2bcafdb6d2eedf64840",
        "0xf7b17e0b2478ad21ac594e4b0954ece63d059064",
        "0xf7c63e75b90c60d7b343106a39658f8b3ca6e4d2",
        "0xf8b4256122369c48eb8c3d901875d62458a675e8",
        "0xfa13971666d0e6f2715d68eb44bb7964fc22b14b",
        "0xfad70cb84e104817a7e9345d25ed0d3048af2d2d",
        "0xfcb21730ac0cd487d8701dfed1170e023b57cf7a",
        "0xfe908731af54c56dfd63948f18ce5878a3b8a1ad"
      ],
      "mention": {
        "end": 8,
        "start": 4,
        "text": "OKEx"
      },
      "owner": "OKX"
    }
  ],
  "id": "v2-a01",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "d30c0f9de018b7cb2e6764f970af3452b335a606f12fb95b1147000b691334fe",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "receipt_status",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "253fbed5f82ddb2db622880848854b64dcb2bbf90d8336599c7b9967c5fdbda6"
}
```

Lý do tác giả: Historical name uniquely resolves to OKX, and fraction uses only known statuses.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "1951"
    ],
    [
      "number",
      "0"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "1b457eca36ae0968d699a46b778a325930035eeaf8edaa2eaf5ae746bf91764e",
  "case_sha256": "57cf95db13e222026a088dd9b688c9bdcd9a6c6206782adf5909161905c3d7e3",
  "id": "v2-a01",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "d30c0f9de018b7cb2e6764f970af3452b335a606f12fb95b1147000b691334fe",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "253fbed5f82ddb2db622880848854b64dcb2bbf90d8336599c7b9967c5fdbda6",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a02 — alias

For incoming outer calls to curve finance, return each transaction type with total and successful row counts, ordered by type. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "curve_finance_inbound_type_success"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:curve_finance_inbound_type_success",
  "id": "v2-a02",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `curve_finance_inbound_type_success`. Property focus: `None`.

```sql
SELECT transaction_type, COUNT(*) AS total, COUNTIF(receipt_status=1) AS succeeded
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Curve DEX' GROUP BY transaction_type ORDER BY transaction_type
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0c0e5f2ff0ff18a3be9b835635039256dc4b4963",
        "0x45312ea0eff7e09c83cbe249fa1d7598c4c8cd4e",
        "0x6a8cbed756804b16e05e741edabd5cb544ae21bf",
        "0x98ee851a00abee0d95d08cf4ca2bdce32aeaaf7f",
        "0xb9fc157394af804a3578134a6585c0dc9cc990d4",
        "0xf18056bbd320e96a48e3fbf8bc061322531aac99"
      ],
      "mention": {
        "end": 41,
        "start": 28,
        "text": "curve finance"
      },
      "owner": "Curve DEX"
    }
  ],
  "id": "v2-a02",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "632a550c30a830bb7fee54cc078b191a2c08f2d00b6075d8cd31f91756d7c545",
  "schema": {
    "columns": [
      {
        "column": "receipt_status",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "transaction_type",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "e47b7c08995094db3eb97bfb022f415567de428262e4bcc982f2828612967b91"
}
```

Lý do tác giả: Protocol owner Curve DEX, not the Curve governance token.

Sample: 2 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "0"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "number",
      "2"
    ],
    [
      "number",
      "198"
    ],
    [
      "number",
      "186"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "84599f8f0bee18fb80b1890de2114fe8ecdc5c834a981eebf49d74c9c6147847",
  "case_sha256": "ec034bec9cbe8008faf9b804d98b404500aab097b76c03d236c21531a7a15a98",
  "id": "v2-a02",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "632a550c30a830bb7fee54cc078b191a2c08f2d00b6075d8cd31f91756d7c545",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "e47b7c08995094db3eb97bfb022f415567de428262e4bcc982f2828612967b91",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a03 — alias

For outer transactions received by TC, return active dates with zero-value and positive-value counts plus total declared wei; order by date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "tc_inbound_value_buckets"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:tc_inbound_value_buckets",
  "id": "v2-a03",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `tc_inbound_value_buckets`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNTIF(value_wei=0) AS zero_value,
    COUNTIF(value_wei>0) AS positive_value, SUM(value_wei) AS declared_wei
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Tornado Cash' GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x03893a7c7463ae47d46bc7f091665f1893656003",
        "0x07687e702b410fa43f4cb4af7fa097918ffd2730",
        "0x0836222f2b2b24a3f36f98668ed8f0b38d1a872f",
        "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc",
        "0x169ad27a470d064dede56a2d3ff727986b15d52b",
        "0x178169b423a011fff22b9e3f3abea13414ddd0f1",
        "0x22aaa7720ddd5388a3c0a3333430953c68f1849b",
        "0x23773e65ed146a459791799d01336db287f25334",
        "0x2717c5e28cf931547b621a5dddb772ab6a35b701",
        "0x4736dcf1b7a3d580672cce6e7c65cd5cc9cfba9d",
        "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936",
        "0x610b717796ad172b316836ac95a2ffad065ceab4",
        "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf",
        "0xa160cdab225685da1d56aa342ad8841c3b53f291",
        "0xbb93e510bbcd0b7beb5a853875f9ec60275cf498",
        "0xd21be7248e0197ee08e0c20d4a96debdac3d20af",
        "0xd4b88df4d29f5cedd6857912842cff3b20c8cfa3",
        "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b",
        "0xd96f2b1c14db8458374d9aca76e26c3d18364307",
        "0xfd8610d20aa15b7b2e3be39b396a1bc3516c7144"
      ],
      "mention": {
        "end": 37,
        "start": 35,
        "text": "TC"
      },
      "owner": "Tornado Cash"
    }
  ],
  "id": "v2-a03",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "6f24df601ae324eadb6963cc750ec4af5a470334cd0987364a26126b11faa60d",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "value_wei",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "a671f945c7d74799328b733274fc2427e663b951e3ed240dc70989d684e961bf"
}
```

Lý do tác giả: TC is a dictionary alias of the privacy-service owner; all known endpoints included.

Sample: 28 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "3"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "0"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "100000000000000000000"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "3"
    ],
    [
      "number",
      "2100000000000000000"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "100000000000000000000"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "3"
    ],
    [
      "number",
      "11100000000000000000"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "1d85f0abe01d006ea3d103d076c8accc6d220da0aea4439613d51d986c3dd8fa",
  "case_sha256": "b712bfc538c20f6f19c1a7f3480cd9f9f9c6e8c48a55b3f5b1749bb4cdb1deca",
  "id": "v2-a03",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "6f24df601ae324eadb6963cc750ec4af5a470334cd0987364a26126b11faa60d",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "a671f945c7d74799328b733274fc2427e663b951e3ed240dc70989d684e961bf",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a04 — alias

For token events sent by uni v2, return each token contract with event count and number of distinct active UTC dates, sorted by active dates descending and then token address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "uni_v2_outbound_token_active_dates"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:uni_v2_outbound_token_active_dates",
  "id": "v2-a04",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `uni_v2_outbound_token_active_dates`. Property focus: `None`.

```sql
SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT DATE(block_timestamp)) AS days
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_owner='Uniswap V2' GROUP BY token_address
    ORDER BY days DESC, token_address
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",
        "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"
      ],
      "mention": {
        "end": 31,
        "start": 25,
        "text": "uni v2"
      },
      "owner": "Uniswap V2"
    }
  ],
  "id": "v2-a04",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "c55e93cee0f95bbbcb8fc5c3d434135ed9709ab0d54255cac9207845319d03c9",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "from_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "40465b3c269b716769cd2d10fc4e8b556abb7325c12b8c379454afb550df39ce"
}
```

Lý do tác giả: Version-qualified alias avoids ambiguous Uniswap family resolution.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    ],
    [
      "number",
      "2208"
    ],
    [
      "number",
      "30"
    ]
  ],
  [
    [
      "string",
      "0x6ad27352ceb1b55a1cbf885cefc2ed5a9183ae99"
    ],
    [
      "number",
      "9"
    ],
    [
      "number",
      "2"
    ]
  ],
  [
    [
      "string",
      "0x02d883afb22224e7ea301029f5b2b6d58f186d15"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "0x299c5a41b25b1d3e7a2703c4ba7ee9394dea6af5"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "0x3891b9e0bd5715c27ebfbbea899e9dfd9c19f911"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "9a8b90376b8bf4761a398b5530cb763ce94c4fd65758bc720234616d710c9fea",
  "case_sha256": "a97f486b8b7b17c6f29d8462e8bbe787bffccb3d7fe860cbbf58e7c6bc6b4b3b",
  "id": "v2-a04",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "c55e93cee0f95bbbcb8fc5c3d434135ed9709ab0d54255cac9207845319d03c9",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "40465b3c269b716769cd2d10fc4e8b556abb7325c12b8c379454afb550df39ce",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a05 — alias

For outer calls received by uni v3, report the count and minimum, average and maximum receipt gas used. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "uni_v3_inbound_gas_extrema"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:uni_v3_inbound_gas_extrema",
  "id": "v2-a05",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `uni_v3_inbound_gas_extrema`. Property focus: `None`.

```sql
SELECT COUNT(*) AS calls, MIN(receipt_gas_used) AS minimum,
    AVG(receipt_gas_used) AS average, MAX(receipt_gas_used) AS maximum
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Uniswap V3'
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "0x61ffe014ba17989e743c5f6cb21bf9697530b21e",
        "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45",
        "0xb27308f9f90d607463bb33ea1bebb41c27ce5ab6",
        "0xbfd8137f7d1516d3ea5ca83523914859ec47f573",
        "0xc36442b4a4522e871399cd717abdd847ab11fe88",
        "0xe592427a0aece92de3edee1f18e0157c05861564"
      ],
      "mention": {
        "end": 34,
        "start": 28,
        "text": "uni v3"
      },
      "owner": "Uniswap V3"
    }
  ],
  "id": "v2-a05",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "aa7ffd555d037150b02c46b7a88139ccc0b62712e9e7353d3927041e291d78f5",
  "schema": {
    "columns": [
      {
        "column": "receipt_gas_used",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "950c4e26483973561ebeecc7e1359c045d6158853be5276521539fd9c34c8bfa"
}
```

Lý do tác giả: Aggregates outer receipt gas for every known V3 endpoint, independent of token events.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "2426"
    ],
    [
      "number",
      "25790"
    ],
    [
      "number",
      "305873.72547403135"
    ],
    [
      "number",
      "5194727"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "d3d81674d5a26884a637ab856706269ec9754aafd16dacf41ca252468977bb51",
  "case_sha256": "c643309332fb14a9d023f785c78db4f9b98d54ab3cf0681f8122e6aec24473bd",
  "id": "v2-a05",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "aa7ffd555d037150b02c46b7a88139ccc0b62712e9e7353d3927041e291d78f5",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "950c4e26483973561ebeecc7e1359c045d6158853be5276521539fd9c34c8bfa",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a06 — alias

Group outer calls received by uni v4 by UTC hour of day, returning count and average gas price in wei, ordered by hour. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "uni_v4_hourly_call_cost"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:uni_v4_hourly_call_cost",
  "id": "v2-a06",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `uni_v4_hourly_call_cost`. Property focus: `None`.

```sql
SELECT EXTRACT(HOUR FROM block_timestamp AT TIME ZONE 'UTC') AS hour,
    COUNT(*) AS calls, AVG(gas_price_wei) AS average_price FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE to_owner='Uniswap V4' GROUP BY hour ORDER BY hour
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x000000000004444c5dc75cb358380d2e3de08a90",
        "0x52f0e24d1c21c8a0cb1e5a5dd6198556bd9e1203",
        "0x7ffe42c4a5deea5b0fec41c94c136cf115597227",
        "0xbd216513d74c8cf14cf4747e6aaa6420ff64ee9e"
      ],
      "mention": {
        "end": 36,
        "start": 30,
        "text": "uni v4"
      },
      "owner": "Uniswap V4"
    }
  ],
  "id": "v2-a06",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "5dbd684abdcafde524bd2567665172a77bd28aa71ed23ddcc86346f802ab9a1b",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "gas_price_wei",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "cc6eb54915fb24ecfa309fa5737cbe9fda8c77c6802a56c9bd45cef9f704571b"
}
```

Lý do tác giả: V4 is a distinct owner, not a renamed V3 address set.

Sample: 24 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "0"
    ],
    [
      "number",
      "43"
    ],
    [
      "number",
      "321612787.2790698"
    ]
  ],
  [
    [
      "number",
      "1"
    ],
    [
      "number",
      "35"
    ],
    [
      "number",
      "526612512.3428571"
    ]
  ],
  [
    [
      "number",
      "2"
    ],
    [
      "number",
      "43"
    ],
    [
      "number",
      "391169350.7209302"
    ]
  ],
  [
    [
      "number",
      "3"
    ],
    [
      "number",
      "31"
    ],
    [
      "number",
      "543937441.6129032"
    ]
  ],
  [
    [
      "number",
      "4"
    ],
    [
      "number",
      "28"
    ],
    [
      "number",
      "500708552.35714287"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "d12b3ad4446d0d95a8b7a5bd788d08bcad209fa974ed8e41b25e1adfbb36c3eb",
  "case_sha256": "7c059768573c5433eb3ba84c21787dc4220d3f05ccbfdeff68c0be58c0944bc6",
  "id": "v2-a06",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "5dbd684abdcafde524bd2567665172a77bd28aa71ed23ddcc86346f802ab9a1b",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "cc6eb54915fb24ecfa309fa5737cbe9fda8c77c6802a56c9bd45cef9f704571b",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a07 — alias

For op bridge, list known recipient addresses with incoming outer transactions, showing row count and total declared wei per address; sort by count descending and then address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "op_bridge_endpoint_contributions"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:op_bridge_endpoint_contributions",
  "id": "v2-a07",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `op_bridge_endpoint_contributions`. Property focus: `None`.

```sql
SELECT to_address, COUNT(*) AS calls, SUM(value_wei) AS declared_wei
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Optimism Bridge' GROUP BY to_address
    ORDER BY calls DESC, to_address
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1",
        "0xbeb5fc579115071764c7423a4f12edde41f106ed"
      ],
      "mention": {
        "end": 13,
        "start": 4,
        "text": "op bridge"
      },
      "owner": "Optimism Bridge"
    }
  ],
  "id": "v2-a07",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "40a1470bdd5bb36b8a724cd7a6305f698ec0c7d59d7126ad279dc83fc99fa9e0",
  "schema": {
    "columns": [
      {
        "column": "to_address",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "value_wei",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "4a0e253050aabbcd243f5c09ed55bc45897079381cced38e06d3af12b248422d"
}
```

Lý do tác giả: Alias denotes the known L1 bridge owner, not all transactions on an L2 chain.

Sample: 2 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0xbeb5fc579115071764c7423a4f12edde41f106ed"
    ],
    [
      "number",
      "587"
    ],
    [
      "number",
      "47737476187269737358"
    ]
  ],
  [
    [
      "string",
      "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1"
    ],
    [
      "number",
      "4"
    ],
    [
      "number",
      "69992476989780879208"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "fc93d0939fe7f3193ba934da45a34969e16816bdcc26d0cc876f79fc089f35a1",
  "case_sha256": "ebb9edfcd8228115d19d8ea55600f6b7f8c704fca72e27da2031d7d48513d4dd",
  "id": "v2-a07",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "40a1470bdd5bb36b8a724cd7a6305f698ec0c7d59d7126ad279dc83fc99fa9e0",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "4a0e253050aabbcd243f5c09ed55bc45897079381cced38e06d3af12b248422d",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a08 — alias

For optimism gateway, return the fifteen token contracts with the most incoming transfer events and their distinct outer transaction counts; include event count and break ties by token address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "optimism_gateway_inbound_token_transaction_mix"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:optimism_gateway_inbound_token_transaction_mix",
  "id": "v2-a08",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `optimism_gateway_inbound_token_transaction_mix`. Property focus: `None`.

```sql
SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT transaction_hash) AS transactions
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Optimism Bridge' GROUP BY token_address
    ORDER BY events DESC, token_address LIMIT 15
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1",
        "0xbeb5fc579115071764c7423a4f12edde41f106ed"
      ],
      "mention": {
        "end": 20,
        "start": 4,
        "text": "optimism gateway"
      },
      "owner": "Optimism Bridge"
    }
  ],
  "id": "v2-a08",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "182ef42774cd0f2179a69bdfcdb4e6e6ee27de09bdaf6f8954fa7bd386193559",
  "schema": {
    "columns": [
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "transaction_hash",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "c46ac678dd5b9d88feb4bdb0e671f790753353f6349ff6bf18c7285cf337ea98"
}
```

Lý do tác giả: Gateway alias uses endpoint role; token identity is unrestricted.

Sample: 6 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0xdac17f958d2ee523a2206206994597c13d831ec7"
    ],
    [
      "number",
      "34"
    ],
    [
      "number",
      "34"
    ]
  ],
  [
    [
      "string",
      "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "2"
    ]
  ],
  [
    [
      "string",
      "0xd533a949740bb3306d119cc777fa900ba034cd52"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "0x163f8c2467924be0ae7b5347228cabf260318753"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "0xca1207647ff814039530d7d35df0e1dd2e91fa84"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "1a59dc64aa5b52c1850e5f94f6b27f5e984a0f39f8ec4867db445ac19e4172fd",
  "case_sha256": "316934d1614db574c684e0151e8a77081ed781ab9c1a58ba02751962780696dc",
  "id": "v2-a08",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "182ef42774cd0f2179a69bdfcdb4e6e6ee27de09bdaf6f8954fa7bd386193559",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "c46ac678dd5b9d88feb4bdb0e671f790753353f6349ff6bf18c7285cf337ea98",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a09 — alias

For binance exchange, return the ten senders with the most incoming outer transactions, including count and average gas price in wei; resolve count ties by sender address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "binance_alias_inbound_sender_gas_prices"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:binance_alias_inbound_sender_gas_prices",
  "id": "v2-a09",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `binance_alias_inbound_sender_gas_prices`. Property focus: `None`.

```sql
SELECT from_address, COUNT(*) AS n, AVG(gas_price_wei) AS average_price
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Binance' GROUP BY from_address
    ORDER BY n DESC, from_address LIMIT 10
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x030e37ddd7df1b43db172b23916d523f1599c6cb",
        "0x110daa3f3fac2a54bb508ac94f31f9df77057b29",
        "0x150aace136535a374f05b5ee209b6a61396db1c0",
        "0x18e226459ccf0eec276514a4fd3b226d8961e4d1",
        "0x1b46970cfe6a271e884f636663c257a5a571fb2c",
        "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        "0x22132139bf7f3921b1cadeab931f4fbf7bf2bc9e",
        "0x26bff98f6f37c8d560684eaf2afd1149bf76633e",
        "0x28c6c06298d514db089934071355e5743bf21d60",
        "0x308a2a0712570daeea77c8ba9c27a32cdc4000d4",
        "0x32e11a20337ebc79abd0eeab2d91bafbd9591149",
        "0x38aaef3782910bdd9ea3566c839788af6ff9b200",
        "0x42a93a9f5cfda54716c414b6eaf07cf512f46ead",
        "0x43684d03d81d3a4c70da68febdd61029d426f042",
        "0x4976a4a02f38326660d17bf34b431dc6e2eb2327",
        "0x4aec0e98fc1fb55b9cc2faaa7a81acca42cb4e96",
        "0x4ed6cf63bd9c009d247ee51224fc1c7041f517f1",
        "0x4fdfe365436b5273a42f135c6a6244a20404271e",
        "0x56eddb7aa87536c09ccc2793473599fd21a8b17f",
        "0x5a1e5b56aa33c056ed7bb93b88b1774a456f6694",
        "0x5a52e96bacdabb82fd05763e25335261b270efcb",
        "0x6357e4bdaff733dfe8f50d12d07c03b3bed0884b",
        "0x6454ac71ca260f99cca99a3f4241dfda20cfa965",
        "0x756b86fd69914db92229c07c7393d7d9948fed33",
        "0x835678a611b28684005a5e2233695fb6cbbb0007",
        "0x8498fc7280668874a5da79e87ca0896f4f0d1196",
        "0x86523c87c8ec98c7539e2c58cd813ee9d1a08d96",
        "0x87433fec6f8d9df13d1e17c4b11364ecd2e93a51",
        "0x8a6f8404c9ea4c33502a3f6a4bf8e41ef5ca10ea",
        "0x8e609ac80f4324e499a6efd24f221a2caa868224",
        "0x9696f59e4d72e237be84ffd425dcad154bf96976",
        "0x98adef6f2ac8572ec48965509d69a8dd5e8bba9d",
        "0xa345dcb63f984ed1c6d1a8901e0cdbd13b2b4d19",
        "0xa64b436964e7415c0e70b9989a53e1fb9a90e726",
        "0xa7c0d36c4698981fab42a7d8c783674c6fe2592d",
        "0xa9fc92f6faf9f103fc81d17de3e8daadc888afff",
        "0xad354cfbaa4a8572dd6df021514a3931a8329ef5",
        "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",
        "0xc47b3342df38d747033b6041f54e4e5e300c8d18",
        "0xc8daf809c7d7c27dd62d006196d8901ba57e5eae",
        "0xd27b39cb25fed854f9fce3a4e451f96e62089e48",
        "0xdbeb6c856ef5a167f5e1acb9dff65adb33207d8b",
        "0xdbf28a152d79b2b98eecd229b412ee98d21ec3bc",
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
        "0xe1940f578743367f38d3f25c2d2d32d6636929b6",
        "0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055",
        "0xf16924b866e58ac916ba933d1f1034bcbbb1958c",
        "0xf1f8cb7633d3ca3fd06c084d18ca5491a85ae9b4",
        "0xf977814e90da44bfa03b6295a0616a897441acec",
        "0xfc8059c2fb22005ede8a86d388e3d0f536a4dd44"
      ],
      "mention": {
        "end": 20,
        "start": 4,
        "text": "binance exchange"
      },
      "owner": "Binance"
    }
  ],
  "id": "v2-a09",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "e9ac581b61ab759d957b7fd5c81dd6346ceaa048a4cfd4fe2285e79afacbff99",
  "schema": {
    "columns": [
      {
        "column": "from_address",
        "relation": "labeled_transactions"
      },
      {
        "column": "gas_price_wei",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "015ddc4cb54a595b2f17234a0f19839a48cb5d4e98121a54d8d7c47c182449ff"
}
```

Lý do tác giả: Noncanonical owner alias, with sender aggregation after recipient-address union.

Sample: 10 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x28c6c06298d514db089934071355e5743bf21d60"
    ],
    [
      "number",
      "1495"
    ],
    [
      "number",
      "1343401769.5792642"
    ]
  ],
  [
    [
      "string",
      "0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97"
    ],
    [
      "number",
      "89"
    ],
    [
      "number",
      "264472105.0224719"
    ]
  ],
  [
    [
      "string",
      "0x396343362be2a4da1ce0c1c210945346fb82aa49"
    ],
    [
      "number",
      "29"
    ],
    [
      "number",
      "262762296.5172414"
    ]
  ],
  [
    [
      "string",
      "0xeae7380dd4cef6fbd1144f49e4d1e6964258a4f4"
    ],
    [
      "number",
      "24"
    ],
    [
      "number",
      "432150590.8333333"
    ]
  ],
  [
    [
      "string",
      "0x8aca664682e9f2cd167ee7de147733fe4caa792a"
    ],
    [
      "number",
      "18"
    ],
    [
      "number",
      "1084547275"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "0f1d9f1235e15f5f5b2798c17a7b9bc12dad8a368da96ced6d6287224b53e142",
  "case_sha256": "05753de17c11b0db1f3b20a8c2d1144e14ef23729f181761ca4afa8b996374e3",
  "id": "v2-a09",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "e9ac581b61ab759d957b7fd5c81dd6346ceaa048a4cfd4fe2285e79afacbff99",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "015ddc4cb54a595b2f17234a0f19839a48cb5d4e98121a54d8d7c47c182449ff",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a10 — alias

For crypto.com, give outgoing outer transaction counts by receipt status and transaction type, ordering by status then type; retain the unknown-status group. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "cryptocom_outbound_known_status_histogram"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:cryptocom_outbound_known_status_histogram",
  "id": "v2-a10",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `cryptocom_outbound_known_status_histogram`. Property focus: `None`.

```sql
SELECT receipt_status, transaction_type, COUNT(*) AS n FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE from_owner='Crypto-com' GROUP BY receipt_status, transaction_type
    ORDER BY receipt_status, transaction_type
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x46340b20830761efd32832a74d7169b29feb9758",
        "0x6262998ced04146fa42253a5c0af90ca02dfd2a3",
        "0x72a53cdbbcc1b9efa39c834a540550e23463aacb",
        "0x7758e507850da48cd47df1fb5f875c23e3340c50",
        "0xcffad3200574698b78f32232aa9d63eabd290703",
        "0xf3b0073e3a7f747c7a38b36b805247b222c302a3"
      ],
      "mention": {
        "end": 14,
        "start": 4,
        "text": "crypto.com"
      },
      "owner": "Crypto-com"
    }
  ],
  "id": "v2-a10",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "28d6affffc8574cc6cba1fcdbb31a072731d4cf255ff471afd8367f7b66a761a",
  "schema": {
    "columns": [
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "receipt_status",
        "relation": "labeled_transactions"
      },
      {
        "column": "transaction_type",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "311ed65e65f05d2202ec5db69e3f32b9c153918703df1eeac75c0290dae2e6a4"
}
```

Lý do tác giả: Punctuation alias is dictionary-bound; NULL receipt status is not silently dropped.

Sample: 3 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "0"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "11"
    ]
  ],
  [
    [
      "number",
      "1"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "128863"
    ]
  ],
  [
    [
      "number",
      "1"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "3"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "adf5d3beedad063bb3de6ebf2a2341c30a1194bab7ef217d7142072297d65b60",
  "case_sha256": "7b12d1456269fc1a2b80b931ddd5c0b973125536bafd1b6e161fc80189716155",
  "id": "v2-a10",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "28d6affffc8574cc6cba1fcdbb31a072731d4cf255ff471afd8367f7b66a761a",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "311ed65e65f05d2202ec5db69e3f32b9c153918703df1eeac75c0290dae2e6a4",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a11 — alias

For hashkey, return the sum of declared incoming outer wei minus declared outgoing outer wei across its known addresses, and the either-role transaction count. Internal rows cancel in the value difference; include every receipt outcome. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "hashkey_declared_value_net"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:hashkey_declared_value_net",
  "id": "v2-a11",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `hashkey_declared_value_net`. Property focus: `None`.

```sql
SELECT SUM(IF(to_owner='HashKey Exchange',value_wei,0))
    - SUM(IF(from_owner='HashKey Exchange',value_wei,0)) AS net_declared_wei,
    COUNT(*) AS involved FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE from_owner='HashKey Exchange' OR to_owner='HashKey Exchange'
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0100dc5672f702e705fc693218a3ad38fed6553d",
        "0x48ee4a557e291c2a48d227e8a8dbe2217a825682",
        "0x7ffbafdc1e4f0a4b97130b075fb4a25f807a1807",
        "0xee1bf4d7c53af2beafc7dc1dcea222a8c6d87ad9",
        "0xffe15ff598e719d29dfe5e1d60be1a5521a779ae"
      ],
      "mention": {
        "end": 11,
        "start": 4,
        "text": "hashkey"
      },
      "owner": "HashKey Exchange"
    }
  ],
  "id": "v2-a11",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "either"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "30f1e1e945ea39df6cc6cc3aa644193d9f60fb6dde0f018b1c95ca302e25e9ee",
  "schema": {
    "columns": [
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "value_wei",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "6f0529d7b25a02875d10c93a54cea5726f0f55498b8a4ab54a5ca331fd87cd3d"
}
```

Lý do tác giả: Declared-value diagnostic, explicitly not balance change or realized ETH settlement.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "12307903110554387222068"
    ],
    [
      "number",
      "11942"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "aa55375a254dc43d2e623adc72b31244d7fa6bd014f2928c0451165b7b7e2a43",
  "case_sha256": "ba63714b908ef92eadb478b02331967f1e3d372f3d499ae9db0ca00da1c9e1f3",
  "id": "v2-a11",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "30f1e1e945ea39df6cc6cc3aa644193d9f60fb6dde0f018b1c95ca302e25e9ee",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "6f0529d7b25a02875d10c93a54cea5726f0f55498b8a4ab54a5ca331fd87cd3d",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a12 — alias

For OSL, return the number of outgoing outer transactions to a non-null recipient, the number with a null recipient, and the count of distinct non-null recipients. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "osl_outbound_contract_creation_split"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:osl_outbound_contract_creation_split",
  "id": "v2-a12",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `osl_outbound_contract_creation_split`. Property focus: `None`.

```sql
SELECT COUNTIF(to_address IS NOT NULL) AS addressed,
    COUNTIF(to_address IS NULL) AS creations, COUNT(DISTINCT to_address) AS recipients
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_owner='OSL HK'
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x00056e6cc2d2b1c9ab6ecf58f025afcb4530f2ef",
        "0x004310ebad86fd21264bf4689c683c90c589ce51",
        "0x005c575353dc8819f05e272c27e2e842f9afa24c",
        "0x0095670c02128d898a0a7a370f0711b8c8bd0385",
        "0x00f690a0ea0aee2ba5f679dcd1361d700697b2aa",
        "0x016f14c212bde7a8c7b3c544f0cc1d2b639ca1f0",
        "0x01b8b19295cf797922acf0036ff5f964d1ca69ef",
        "0x028ac7371e20afe22e5d426ac10ea1a89587c284",
        "0x02d2125aa93bdc804a3364dab7dd538f92b8e1c7",
        "0x03086d30203cf33c827a04dff4ea6b1189066601",
        "0x035826c7821f79c84edcfac76c881e406f4cd100",
        "0x035ec2dee558607bed7c32b79438875a7510c80b",
        "0x05d20f26826c7d85fee7039bb06fd432d9873fa9",
        "0x06a8bef8988634eab93de54b8f8dc87b48c8f06b",
        "0x06c5f8189e889d7ca436de8e91bb55811a7b1243",
        "0x06e8ec46a1892de32307a3f729b9a9f231e5b43f",
        "0x07aa658a35e0246c174c9f172ef3b56f112e4b35",
        "0x08980f38feb950d42096b53bf813ca5ffa6dcc07",
        "0x08e7199b58f95e7b4125e062df126c84bc3e0c29",
        "0x0a20be8dd9dc5a3d210780518ddba4c2c2fc5bce",
        "0x0b10ec9e8c8032b110cad91faaea328119e83ab4",
        "0x0b2afd5b7a604b1372737888dc56bf5c7a213754",
        "0x0b2fcc5d76444cfcb80d92234bee6a5a1a8794ec",
        "0x0bf95fd481fefc639ed6d867a7a18ada458d5630",
        "0x0ddfde5aadd3c037bbf223e332f3d292cc42fa99",
        "0x0e2d9465694411f3855461169eb5aebcc06a647f",
        "0x0e985c561167c531aa7a6a7f267780856a6c4843",
        "0x0fad0066f0fea30d94f1a4b24cb10f58ed070906",
        "0x0fb81f2187ad8a9aef480deef2d96a765352f33c",
        "0x0fc5539d60c2e02aa945b03c64ded6bf4e35a108",
        "0x109c6b7ad92f6464088eebbe13dab8b70103b2b2",
        "0x112f76f34d9c1ac3a1a88097b4fac232327fa2ed",
        "0x1133553f8358874e865cf72e9a52daaf26028dad",
        "0x13e04239bbb8eba7853f51f1b7703a3a6fd29516",
        "0x14dda602c8458810a288039ccf59e0d13bcd0614",
        "0x150abc561ff27a50cabd722b19a064852b0bc38c",
        "0x159acb0676146a3653884c490095395004e796fb",
        "0x15bf23291ce5340420e9e2e67ddae83e11fd2529",
        "0x15d1285a1c01aa7c69781e886b334d887835770b",
        "0x160a057a9e08afcd2fc3b318c3f26c7e32c50c23",
        "0x161655fd689927936faa4d2018a2a0c78c4c7bc6",
        "0x1759368842994588340d10414809e3fe234412ac",
        "0x1871418fa15c21c11f762fd07d1b51a7c45ad20d",
        "0x1876205fc7286833d3cbc30e633528116509de6f",
        "0x194fe1914eb943e700af07e10a1b2b9223902fcf",
        "0x19a5006020e655d33a3492c4de8aa6c4507e0b84",
        "0x19d33db48de46270bb256cda1e384115510e6360",
        "0x1a49956deaff8ddaecc2ca62a5564d132b2818d3",
        "0x1ba91ca89bb84ae32526256a0f14ab2c24e0e63b",
        "0x1c8f9981c83bc0a8e495875e6a654484ba4f9e89",
        "0x1c90c2ec4dd315f89095c0a6ab7834d93c320322",
        "0x1cba78d528d9d580ad79ba66d5d3fad3b5b3c7fb",
        "0x1ce50ed18cbf67850a3fb6634deaebffb50d679d",
        "0x1d4266f39ef64fea15935268184914136234a898",
        "0x1d5e94c693d4ca6ab87bee98434397bfdb5bcdb1",
        "0x1d9425b4e2234bb8821cd2145c3f5ca20a47ad8b",
        "0x1d9bfe3f40ced82b24a80926e0efa8358c4f4724",
        "0x1e854bbe5690690ae056236ba4db38cdb4450976",
        "0x1f272f40be7943576e4c1c025d5ca9b5bb29965a",
        "0x1fdc9cfb80be2b97aeb746a487d5af6f106f9ac8",
        "0x200dc7fd51c09c9e5e98bc44643155a5eeee56fb",
        "0x213d8a27bfb997e9682b37ba4531e3562220c86f",
        "0x214c6f55df15f53c549305043288ee3da1ae1b42",
        "0x2162119931221e4e02b4789a012d5ad3ad966f1d",
        "0x21cc7e2c3a3bc34de831dd017fda6120c8d8206a",
        "0x227541a74fd13d30aea8b2ee3fba4571c53d5e40",
        "0x2281c5ae8d66b0df302239c2a70c70ef6ab858e8",
        "0x22c076e5128967d025074644287c10954ec179a3",
        "0x239bfd27ef6ba4ccc10d3f938c9110a3902e567d",
        "0x23bafddae751c4c9307db0e0063f841d17ce0d65",
        "0x24465096da3a60c0b60942c1871c1a5f4890045a",
        "0x24addc243c787e419a3b3e43aeacfb65974a2d90",
        "0x24bd4145d932cb76c2007bb9e6f4e52a54ad8a26",
        "0x25027e37c68c5e255dfb96145b46169b34bc9060",
        "0x257dd2186ae4fcc30832a89f7fcae358e1d2a836",
        "0x25bd0f9d107431eb9bb6c79dda31c2462248c123",
        "0x2615ec9d5b6f5b73789feb22f05c5ddd5c5abcc8",
        "0x26901badbfbd4094ad313eb054140eec6e8c9ae5",
        "0x26b48f8203a4f214d828510a5d5f2de48e242532",
        "0x276987e37e320c79d17428a7868d4c5d6532d9e1",
        "0x27b7f94d389a218f238a3068bec927a19c70fe7f",
        "0x2865076ff91db866f9979b9d992cc5ee0451ece6",
        "0x29eb3c831270dde1eb2fdf9c9221cc699105a636",
        "0x2ab48426092a154e5bf6e8210fbfac137e55ea2f",
        "0x2b0530c9330b68fdbc1459f043094629d758d146",
        "0x2b0c4a6a65e3b518c92cfb1147d630ebf31567d3",
        "0x2b2975bf2eab904aa08546d86f5096b0e5fb3f12",
        "0x2cac222c6c59a21b0c1294f548fa881efbd1d046",
        "0x2cd6517de144d9dfa4742f680d40bb78722f2d33",
        "0x2d785cfde84bed9aa1707a68f30c252f3c8cf396",
        "0x2da7645b413c054c3bea075d6eb343f3d5b23628",
        "0x2e036f4841ba7fc72fcf9a5ede668b411e1e482d",
        "0x2e9d022cdfe1fe4ee331fb40d9776b4ced11965f",
        "0x2eb7541b69720097b793f5848d33545d4ba28615",
        "0x3086f4d04edbc7ba595188d64f7721bb5df12bd5",
        "0x31b77071a5422260e248e166abe3ac2a161a8f1e",
        "0x32375b03da733720fc4e004138746859f7f8ed81",
        "0x323b10348fba702ca75a67bb6fd3952e306a4f68",
        "0x3254de933b7b15dcb9ae4bcb2412fe58c27b3731",
        "0x327ed4a818b5aa31c9ac400bf56f170ec04f3f7c",
        "0x34b8f0af0e4f910d5f58f96493d1827c335f539e",
        "0x35114f1dce056a7f9cf92235d1b7f6f2bb4e612f",
        "0x35738af3befb41854490910deebbffb7db1a8575",
        "0x35dd748335c7cc152302992d86aeb97293d100fd",
        "0x35ea9bb7b2717e99f9c82ce3993bcd44a1457008",
        "0x36ec1290b822922a0275a9b11e7c94f156f9d9c7",
        "0x3756cbf65ab763be75983e8e399a4f0b548e720b",
        "0x37cea75c0684c1b7a5696826f12d38383b6efe99",
        "0x382bbccd25e1b69a0fc6a8d3da9903128e28a3fe",
        "0x38480eba998a882878e0a11d6742854b0dd140f6",
        "0x38aeae1371fe2a4ff776484f959b29e0ddc4c91a",
        "0x390a8d911d1a97b9bc224649132ade820be4f007",
        "0x3935efc51bf53fa1f6afc7de14a43b5eb1073b86",
        "0x3977f757f8f1b2a7101a75d32118c416f9f52c10",
        "0x398caf90c13d34c672f3986746aee7736cd039d9",
        "0x3a2f1d9f805bb78ced69d98ad8e118d776c31f51",
        "0x3bd8d19541d59e9f5af08a0634b14d5aba48bb86",
        "0x3c1318d91c060ee8c673396ad03c14383530a6e8",
        "0x3cecbcb0daec0bf63b90b0a5ba27603b34694ab3",
        "0x3d59e01719a8d401faf7e6827789e7192422dca0",
        "0x3d77fb07462be3835dc6c1658851ebb8ed67a8cc",
        "0x3e06f199b2971c722392a6fa160a51d08ecf3de5",
        "0x3efb35b78f883429b0dc89366b980e671b8fb130",
        "0x3f9603e87938a4c1c7dfd5cc045ffa945634eb79",
        "0x400391c5012f586fb567165fa48390e4125d758c",
        "0x4032edec12c9b997ec1e7e3bf998366d2311f527",
        "0x41c9503ceacde97c5a7e95278a18bcad3c2a7b52",
        "0x4225593eae0a06ab66e686b6a123b4e20c45787b",
        "0x426c90bc5815b781f8f8cc76652a2198697bd9d7",
        "0x430c98c329b9cb752107d3b6eb40551224168b42",
        "0x438ff9defabc34958d68bc3755aaad9213dc6e93",
        "0x44cb5be7d67e1a6923fda5eeb81c9d0d192e0e02",
        "0x4593f9c530f04afa16292a162eb482c864c42160",
        "0x46228b1b8dee6924f0d5690ef780ce50e4efbf63",
        "0x46828f5852b5c94083c52ee572b71b699ae43b7f",
        "0x46863ae958afa72ca27425a72f19cbc57ed22a20",
        "0x4699f5c806e73009f387d7f0ee3555bfdd805e0d",
        "0x46e435df56f0292f1cfdabe28f8bc7a505281357",
        "0x46f95276410243e5c3efd1005b78b08e90a183a8",
        "0x4722150413a85cb281eda3166459b5fe7bf79342",
        "0x494b308c632f20150c20ac736fe876fdab43b73d",
        "0x49b2034b74cf5624a3c46d0874be6614dc1bd37c",
        "0x49fcdf30d10e198f0d79287fcd06812787db2ffa",
        "0x4a581b4c48d41701bfd07950f6e4e922473cd590",
        "0x4a997b52bb9cc25790dc131902fe5e1ee301e829",
        "0x4d028ea683266fac762986dd353fc3a8037dd288",
        "0x4d5e6b9fd5986fee6751ac31edb1c675ee5cc66d",
        "0x4f2b1948c39e99f5f7d38c2c032c10dcd0ace585",
        "0x4f8fd058439f7456e8b25c1a457fcb25c1003990",
        "0x50de1986cf5befe0c8ee74d6df6dffe842dc2632",
        "0x50f7c1d7c95ef134d730ad4486f553d28df3f4fc",
        "0x517b8751f286683739745fede126193bf8a80ed8",
        "0x5225f8c6bdcf4370e62d97d6f9520062619f1cf8",
        "0x528b1aa2f0d8cb916d6a0612055001efad1b190e",
        "0x53790bcdeac0d0d5832f3b4115a86c16441c1378",
        "0x53f87798210a03aabd844a416edfef9f28396899",
        "0x53fd4561ce5c4f77c361d11e23f83c077b105f44",
        "0x562721233d76980abb2b2924ff5d0489c0916c38",
        "0x56a68968083ca9774c230f3e8e8d47ad3065b185",
        "0x57d5f04dabc0b9e0eef19b226a8426567ab51d62",
        "0x5930d2cb21fc778d1d36f4cdc3c5df31ece52bfc",
        "0x5a1117d48b6870b2a5994440d73eccc855cb2000",
        "0x5a7c0e74eb20b5ddd6a13b014e8922253eca8f47",
        "0x5c15432db7e5a2ce9070383336a1f7e95d358499",
        "0x5ccfa69d8073b78be3e37273d251da32919433d4",
        "0x5ec7d93bea8699935aa078013ade0cf6e40c39a8",
        "0x5ef27958264a08b37c52ad82938903f99b595d54",
        "0x6099248cc9cb22ccb37b8428e3410c1f1334c4b7",
        "0x61733e8035de15d8de6ced45667691e3909ba9cc",
        "0x62a3407da35179fbc3ec7e32a8fa78a8428d8952",
        "0x62b9eb217a42b81b643fc8d0cd46388938ec4d69",
        "0x63f26901ab71ae63c7b84bc310ce0dfca1da180a",
        "0x645ca2647827d50bb9dd470b17791fd9ccefcf64",
        "0x64f3c7f6b2568fdbc4c0ff9515afa1a180f3c2a1",
        "0x651d8fc366a2f11e6726e913f8972d56389a2a0c",
        "0x662dedaecf50eb07c1c8110b01856f28deae5c0e",
        "0x663a4ab954d2621e7205721ba635bb832ad9cc75",
        "0x686c35cbf6299cb09049ece4c6a1578a59ecc8af",
        "0x68d2871ec1ad14544bc3b8d6eec3c0ee57264a35",
        "0x69391edd8a83b7df81fe9c1f9978447a72c368da",
        "0x696fdf8b29c519b247925c46ba91b7712aa27a55",
        "0x6999efe710162bea5b01f4246f6a47a7d0597529",
        "0x6cd67e862b4360b40672ed9c55b743790554643e",
        "0x6dbc7e771e76a24709e6da608c0581892363a21e",
        "0x6e9332597285794e53d79c545589659e5417a6ef",
        "0x6f61975cb98ca348b82792968a8420bef3935268",
        "0x6f65c66f606ba809f3a3b0b4dca3714b35a262f1",
        "0x6f7c297f7a9def2f0068ea1c6798b6a4f1352c08",
        "0x6fa542aa042f41358a40c84b21f912c2c40849a7",
        "0x7003c71036d5b8f46d07bfc30e9b1ce5418fa165",
        "0x70112253f25691287cf76e58d0017c74407a74ad",
        "0x708a265943804e02582e94122528bab710878f7f",
        "0x70bf5a604a75b0cd010cdbe59511a1df64d08fa3",
        "0x7199322bc5f46b12ca37e029bc3eb31239ab4f1a",
        "0x71b2581389b7d06774c31beafea1a60d78adcd9d",
        "0x71d1441614e8559c8993145b2da08afc4b009117",
        "0x7316e84ac2c39477dd93c5a41a627541c86bfd98",
        "0x731c201b0fb68ce549838175a5ffe01ed3622a2e",
        "0x7449378e3f84cb45d473965084385722744cbb01",
        "0x7496322e10e5efd6a42cc827df882edcf81eb230",
        "0x74f78ce5dd1148a97945a8b5969efe42bc972f3c",
        "0x75e93f3c72d3bcd55579f4896991be48f0717bab",
        "0x76161a7b9c8109655a21a42bad938c0e67c12ad0",
        "0x762e01d3150a9bd2c8d97b6e82adff5876aa8843",
        "0x76302d07fd1283c9c788e060fad7f7486f32f40c",
        "0x76773a268dc91345de872b9b01d0faf114ffc15c",
        "0x76ad4c8d480f8969795c8ce0cb67161890480b85",
        "0x77ea89ce34a7accb1ed994ee5efbafe74ecef473",
        "0x782d4ffda74c303e039541858a7227804369eae0",
        "0x78f5f712cad7050bd8344a7ecf2029135f4fac35",
        "0x7a728b667cf5f76cf8993ed2baf2e5dcae9421ee",
        "0x7a8d9cd62e1f698ef6e72948fe621f383ccee5bc",
        "0x7b4559f6829052bff44047c5b4e1fd0d3a716b5f",
        "0x7b724b17697b64dd54da52274114aaf3dd40a159",
        "0x7b877cd40a371124b01f11cf22fe7c771b86ef73",
        "0x7c0bf050abd8f7437a60dbfba56df2a912b39b48",
        "0x7c16e4537db13af0ba3afcd89a244b58032d905e",
        "0x7cac15e2cfe05e8dc8a739c2d92397b3920e2567",
        "0x7cebb5a8b171361d90eaeba6a4eb9fbf7ee9b032",
        "0x7d3b9f80e86335d7ec0e0c2573d106329698a335",
        "0x7dbee788ebf565cf92b96aac300e9b3b8dc50420",
        "0x7e78af0e6df5425f93d606071a35213c17cc83a8",
        "0x7eb8f9f16cd23ed66e249bdf939647fbaaadbd1d",
        "0x7f10151d0b01d3348c0be034900e18274bb17ac2",
        "0x7f2fc994b219b540f7b88422e6865757c06ac52e",
        "0x804f21bdd365ea5759732764d9b89e36e18badfa",
        "0x80b36a9c5ed3a6e356bd0bd871d107f57293a67d",
        "0x817fca59b6c73f3160413383f3d9d199df3cf43e",
        "0x81ae0b2e38fca2edc548470df5ba2296352ee0ea",
        "0x81e0aca8100978c9affbb35add3b1886d5aa6bc0",
        "0x82395eefe26f17bb2e6d6cd837a21c79e6054707",
        "0x829a9e60d1a3e45a134e40559ebca1480de82ba2",
        "0x83c62f31d35cfe007888e77913207d1e89d09d6b",
        "0x84955b668efffdc127c34d0ee8c0a38060049566",
        "0x84cce256e91152d4beefc5f7b1164f7361f73c81",
        "0x84f8e8047645eb7fb342e71d6688ed759585fea5",
        "0x859542d86faeb60a3308c35508ee1c5bc9a14d81",
        "0x860d3689ccd8365ef6c0f51bf0f5126491b94d89",
        "0x8627890ccbadba4800753ba130e110c86522f2a8",
        "0x8637fea6fdb59f0f9beb01b95bac14ce4f495cc2",
        "0x8707d05929d76d7ae3edb55d69c1424a57524e30",
        "0x875e865d610ce6e8d2eaacbfc21f932ab9c8f9a0",
        "0x884fc0240ad1a7b62cfaf127c68543ba2cc2418e",
        "0x885c7431e6b01dbba2c03c1168c7c129a6e466d0",
        "0x8932929e863fd189c3e873be9012a10f38012968",
        "0x8a2bd0e455d24d8c7a9f15ffd902dc74b961bac6",
        "0x8a6680e3412f410b4f7b32812dfc2b528525ec00",
        "0x8c07329857346f0f9fb36c5426ce78886f22ee3c",
        "0x8caa6e12882ead0de48253f5bdebc6eb432c9c3b",
        "0x8dd4538c6647a83e138ecb2f73207facbdde8da7",
        "0x8e1090f515428b7c9f7e88c8989e44426d7e71e9",
        "0x8f9609b12d918a39dfa816e583b5d7006ad11125",
        "0x91054819e7a9b713d8c4285bf0e973af6ff21352",
        "0x91ebdb23db9a4ff5ec29eff04dd132951f34b688",
        "0x9238ac1b2cd7058a637f2f920f76bd14037e4f89",
        "0x9240e650ede4e657bb3b042892179a03232b85a1",
        "0x92450e2e16a92a2a2b732c5fb4a771ca00a39ec8",
        "0x92d2c650b8693323e7e8a3f0a0215c187911707a",
        "0x92d91a6246a5d6018b9296df57f11e7f33370847",
        "0x93270f39a3406bd97946211ad9270e474ebc4123",
        "0x948f965d581e33182593af9fbcd71e39d215c11f",
        "0x94e650b3a3d6c517552323657e4024fb4d103e0b",
        "0x9615c6eed69f2810968e6ee5f6ec46d665f1bb78",
        "0x96f79eb9bb29460c13633cc3a811e7b3ca09f62f",
        "0x97083a5961f34fd042ce2383195e5fdea998060d",
        "0x976935fdb232ad4733753e2be9828c649a2147fd",
        "0x97a4ca366c9b5af3c3bc70c941ca5f01b8b1c2a2",
        "0x97e5810ee1e8d84adaf68b0363f7c44cbc23a8ba",
        "0x98d2b12ba87348ae2c48dab85e3e22f5ba216e52",
        "0x99c849a75c94be15465ee373a17294ccecd8ab84",
        "0x9a7cc23ee5053bfc39371b57f0850118bc4cd180",
        "0x9bdcde4ae9aa06e1f8ee153735f232b666d5c877",
        "0x9c3378a0da7364ae2724b9631a7eea1f819d3990",
        "0x9c633df664f6adab67d9a8d9f91d5ee444229347",
        "0x9c7b90b4c21ef17a6f7abee4c674a3c0b6334e45",
        "0x9c807b9d1295052a70dfab4ed16805a50e70cc4b",
        "0x9cdd514d2fab61d3ea11aa2cd926a534f25ea862",
        "0x9dc301576f2209a95ecbb16c14c9daf40a6fed1d",
        "0x9de9aed34e139c7562253148ee9bddd5d2bb1a20",
        "0x9e290d4061373b58e5c4727b7233dd558d109bfc",
        "0x9e6599158e6475215ac8ff530aa294f50c04c748",
        "0x9f57f7d99ec6d075a4afc09d7606519565a7c9bb",
        "0x9fa45442ca4bddcd013f9bdcdcfd66d5ff6e9f79",
        "0xa17e7d9511a7d7c93bb3daf5cd164498d11e0bb9",
        "0xa1f2e6dc9719cf870eea8ed56a7896ab22afe4c5",
        "0xa24bd86e4b27bdadafc07689bd14167037d9ab12",
        "0xa28011f90ffce48588c6e61386271578c705f654",
        "0xa36056854f5b31cbe7b0d01754153d8bf861b670",
        "0xa3a90f6d18d935e47974045296d0196a11031db8",
        "0xa3b59e3e23769925d098a7a207188da9a2198789",
        "0xa3b7ccaf36184f63ca9d3a98aba7970df81e5424",
        "0xa4b31659d424c93ba7567721b30992cdea72c70a",
        "0xa5778e72d1bf0a69f8ab5fac991050851927ba1f",
        "0xa69184c33088e6157677cebfbf984226def09993",
        "0xa6cef719337587e4557694915ccac21b81904fb6",
        "0xa7738c21ade0841d5a4229e2488a5b7f7a6b3e3e",
        "0xa77a8c60bcdafa7a33123c7575895471cd551d80",
        "0xa78e14c77da1399a512b19627818f86accd732ae",
        "0xa84c2b35dde5d22b7ca509e76d6178ae33cb718d",
        "0xa8680a82f69a8bfeffde6bb29c10b81b0d96d64b",
        "0xa88a60cca4a87eb247f0820edc8a388c18df2407",
        "0xa8e1f90b3c378de8ea748c0c3522f0710cbce289",
        "0xa90fee24e14f408fbf575ede9665a7510afdbe13",
        "0xa9303481b928cfab76f8ec58fab9203cf59858b2",
        "0xa9347dbd3188ea41b24ace2df5d7ea549469d734",
        "0xa94ffcacd9d68cf48c238e9257ee647a7d474ed2",
        "0xa9c0e3f534850a9853aa0c088ccce0b0b3b0f4a6",
        "0xaa762a28f5a88a7449d386c6799e64c71048d282",
        "0xaa937699cc3d1c3237a3fa9017b80d9754ad7320",
        "0xaa992b65eaf2e4de0b1bc9d59a78227b3e4b6ed0",
        "0xab25cad501ba339d876d4c3ad0f0a3457a98f7df",
        "0xabc481015748e8ef56fe246fcd3b139ab2662c20",
        "0xabd65042691fe8a71d487f58f791f2be5c419314",
        "0xaceb4bd4e215c5c4e2f9dbe2db6d38b0622d3cca",
        "0xad7236fa8ea1b589f542463236d1e64b87e0e4fd",
        "0xadb5aefa5cd79ebed5685047c2ce2ab63cf6e413",
        "0xae311305a32171f1f601720342e0ad2ecaf67d9a",
        "0xaec98f7c8941643032ccb70da93d10332e18a44e",
        "0xb0a94a7665ba1f702ef5752fc122e5eae297c72d",
        "0xb0ec690d888deb405391c2e03b4077bdf9189cd6",
        "0xb0f45e8cd293a7326231a8b3b3f5eb4f06b91b68",
        "0xb1424a7edba2ef045a8dd75c4235ac1b7e0ae2d7",
        "0xb18aee9c69dce80c8b252c7f1c1848be45c0cbc8",
        "0xb18c3cbd1ffa2311f335443a50588e1eb1cbc0d7",
        "0xb1ed60c7f43b7d87d1dd26b392aea714f8f84227",
        "0xb2857d556108be1be8b9eb421d317d1adec8cc8a",
        "0xb290264d38d39f7e6d6527128532071d88a5f7f6",
        "0xb2be74d0462d0bb0422b4a55dccf1767b4b9b9d3",
        "0xb3cc3cefb38cb6745221b4f44a171ce5fc1fc5d7",
        "0xb5a0b71faac6478b6a64f5be7193cea87a6b04b6",
        "0xb5ea0d1f31b7202fa24d30a9343fa18da58858d7",
        "0xb6c8f7427ad21d629b772d03907f00bf25ce848b",
        "0xb7483e891dc2096be6b6ff9b131e28190e524a89",
        "0xb8b68d330bd3586309007714234bc689b9ced09b",
        "0xb91eefbb5e1f59d8f99854621edcbe75383ec2c1",
        "0xb9d12a25f349af07e73082ac2cf0e8d6a023309b",
        "0xba04b08d317dd17c57010d093b40cce986be4c9f",
        "0xbb69f77d60806ee86f35558069dadea4af2398a2",
        "0xbc08e1b59a6348eaaa56789b2765933b2bf20ff8",
        "0xbc1bd330c44a849df8f2e4d5c7d33d0892e14534",
        "0xbc3517a4989e3016ad68516de43e8a30e04c9f96",
        "0xbc6785cf39530a4f034f652ee85c824fffa59e03",
        "0xbc7904aca6068fe55e13b5f73c7f62fb0fa454a7",
        "0xbe5448dd2cac932586b058b114e1b750299e07cb",
        "0xbe6d925ff2bbe9e97f5afc67330dfda24554d149",
        "0xbf0f05f2ca0acf86b70d9fda576128c32288672f",
        "0xbf0ffa4d4e72ac38fdf8a601af2cac3258a31a12",
        "0xbf3c6b49e3851ff36b1e78307fee33d2af3b5517",
        "0xbfbb422d8e0952c2f426f8d8dc60acc9799a7c95",
        "0xc0c171e23e0fb8f73ffa7cd96cc6060338c11cdc",
        "0xc1079fb4418922bd5a67539c11824caf196b58ff",
        "0xc239fc5fdbb4da97750c687d6e5be5d28f869a2b",
        "0xc23c76d6dbf7c875dc1b8de952cc16cdf146fb6d",
        "0xc4026675eee9227f3aa992e08465e0224737b81f",
        "0xc40ee62572bea96088338cd0df9f45b78419ca02",
        "0xc5123aa04455e9df84a29456cc4485dcdc329cbb",
        "0xc524c7fe89a74b52e42efdd3e16b51bc1d1a3bba",
        "0xc550321fd40987237e63c70b99466bad3e7fe6c1",
        "0xc561b51025eb1c6cbb93b523f24afb74d9d3180b",
        "0xc6ba299136f2dc541eb4fdfc890a772e7c28eb93",
        "0xc8576e53a225bd715ee836f99d389820ae926881",
        "0xc8ee5d11adfd0e9d104662611a696f4c61f87d49",
        "0xc92e47c252d1f5a2150ff616974804b888cd9cd1",
        "0xca7401a11bfe190deb22ebec9bc838d58ea6bf7c",
        "0xcadc10557f30dad259ae73a1ab1873d9f3b53e9b",
        "0xcc8c88d2cbe9b9dc9fa5247fee5f5dde9083e72b",
        "0xcce7126777a248bdd0dd6d7171a58b431c52f02b",
        "0xcd2b51543b79dbcdd30c8768018911b102647008",
        "0xcd53e8b98c64d85cd344c2d2793810db48a0fab3",
        "0xcdcd05375d25d4ab860d3e872c1a885eb2f59c47",
        "0xce96e09f80ada651d56d3f64fe904fc34f2df721",
        "0xcefbcba79e5b1a6b259f5a8cd35a0a3e2a5cc638",
        "0xd01c5b6eef5e0751265927ef2ff7f53f697935ea",
        "0xd0445dd54480838408b306f6f151d74d36cfd7b5",
        "0xd0b30e3b07372b777b90d2fa53fe5ac5b4dbf694",
        "0xd0c8f7c0e9514f4be4d95a1721463b8e386cac33",
        "0xd0ea5db219e080a339dd09cf0b9a7369bc0fa5a4",
        "0xd2c3d79a3decce036b70eb666f19ffb7079041d6",
        "0xd300991159aaca18e3e565b5823974976dc94ba3",
        "0xd3d2604e7c849a16c99373a45cc1c5fdd0e80d3c",
        "0xd40b8684fc619f44fd9901a472d749818c981dbe",
        "0xd458216d778fbab58c4488dcf07d294a1f3c39b4",
        "0xd478077cfc8b16e3e56d514b8134d96ada9ae739",
        "0xd5abb346da8c1e06834c6c3d356d2507ecdb01fd",
        "0xd5fabc9810e7ed093a76bad6b348ae56593e9087",
        "0xd62dd1444f25746378315090733149fc6c94d2ef",
        "0xd65fbe9e41b67b962eaad5f2442901a16879db86",
        "0xd67cc95d6afa0407824ba1bf10d2694050536391",
        "0xd7f33b5f0f9500ca285d9f01ba923a0a01552988",
        "0xdc0cd6184c4374960743ef0fad70e6eeda8282fc",
        "0xdc369b75d53bb2956f38241184f4bd0635a11128",
        "0xdc8efefe752711c48bfc060eeec6d4e331b99574",
        "0xdd0ff78a7b47842f9743e8d0f9a7601955ea5f02",
        "0xdd11b2aa3f6533ef242c3f352114a13d3e9c0a51",
        "0xdd1690f0a4d168b4be41ac237fa7f300c035b16e",
        "0xde1573acb47e6546d913b3743593b8dfee481df9",
        "0xe0272600bfb73accc9869e09b9869aaadb0dd786",
        "0xe07dbba31b4b88ecf640f05ad55aca6f1852de01",
        "0xe15e8c6e7a6a520fe81d0a7f1207554dd00b20f1",
        "0xe2a45aa78ccabff8e6e1758639c575011a2f3334",
        "0xe44c6758340466de75ce4f3fe9bd251e1c4969cb",
        "0xe4910ab5647ecf2e0e608b162eaaf50c1b8e5678",
        "0xe4e962f1062f5cac5a0a5ae0efde82e85f564e69",
        "0xe6150ff77cc7ff35951440924a0bf494e998c85c",
        "0xe61693231838a87a7d3cf3d684d4489cb6d2fafd",
        "0xe6f04c80783f25b52ffee7947784a1fcefb5f21c",
        "0xe7a1da9f96be5b074ad6d9f25b02d4551628e8e1",
        "0xe7c469b0107cd510a04680acec9ba6d7c1f9df6d",
        "0xe7cfe7bfcb8a008d33391a36852162a601e7d2f5",
        "0xe80e835c953373bf3a8687db3477e0b4b6e7bac2",
        "0xe81c1d610862ccf8a9aae0ee81d1d8fae1ce4998",
        "0xe81fc019681b0f3426a413a8ef22727df9794024",
        "0xe99b45347ccb1912bebac38f09ebf01d6295f668",
        "0xe9c44e0aae8b61b5530aac734d9e05d10171aaf0",
        "0xeb23e2cacc9b2b9f3ed812ad946b523852f6e1f9",
        "0xed820585c0a6c84f2f0fa83713d0f9baa498eac4",
        "0xed99136a087643cf0a31c26d476adffbbe16b885",
        "0xee1b9c6be803406159c652f4837bb3a98791b1a4",
        "0xeee2424bc64659e6b012d855a73c82bc1f4ffd25",
        "0xefd9679b7c55c6fe97ca2bf55993c1878ca27d7a",
        "0xf045b513b4a706da570ef20727760ada3870a1b9",
        "0xf051b66e30a87bfb0d0aa3e64a18e87d8b65564e",
        "0xf147295d8834593532cc6a2cae5c855ea2a676b0",
        "0xf17f60098176c9bf66b6fd724765ef8fd21c8f82",
        "0xf2b6f8194fbe433f8a93b5716afdd355177947aa",
        "0xf2fa9bd07208f0cd916a70ac1c875fe978e99ed8",
        "0xf343b5c935ce17d5e7a473732c14cf1088043738",
        "0xf376c74ecb53e9debecdc2f3890d303870126d73",
        "0xf56c25ac3e0d870ced0488ad6441c690a78d92a4",
        "0xf68a2ecb54f5b5a135c36246375ad8e80f526bc9",
        "0xf6f6a1824a19da097beb09d8dcf51aec923b1a86",
        "0xf73d40ee6ae1ac62ba7a60b6f08e386d65d4f92c",
        "0xf7606dfb8d9cbf925c4345cbfa046c87a8ffc949",
        "0xf830f14e48146a1fa609377b88bc73e5ed537767",
        "0xf83b853ba13717606835bff4f0ba540be0a3790a",
        "0xf933500d4300b2a0b106d733aaac292abd1bb503",
        "0xfaceb60cc38e56447a855c9e302f346f4d4aa538",
        "0xfb7aaa0cc8bc81e5bd42530d44415e2e5e6ce9fb",
        "0xfd917696e306463d0aa0f83e380247ea7af96cc0",
        "0xfe03903f886da644c6e3cb59ebbd4b0921058bd6",
        "0xfe3a6bb7ecb279940f06e9aa45c1245b27b26170",
        "0xfe939972fa7c9363cb106bacae9b3011315f384c",
        "0xfeace12c4ecf09efd02b8e21d02e4329466ef19f",
        "0xfff6502ea167a8d9228a8bec24aac01ed91433cf"
      ],
      "mention": {
        "end": 7,
        "start": 4,
        "text": "OSL"
      },
      "owner": "OSL HK"
    }
  ],
  "id": "v2-a12",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "326d9a85fd88a5aa0c52c1b2ac1d88f17c8d8e63aec35628899f681b487ede9b",
  "schema": {
    "columns": [
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_address",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "15718cd6a79755ba90e1d57bf06e9e0f7b3bb1d421df764eec615d64e723bbb7"
}
```

Lý do tác giả: Short alias resolves to OSL HK; null recipient rows are explicitly counted.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "817"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "212"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "7b39a9f4ed673250b51811f0e0e2688af1bd41f6414f40f3d813e4b0dffb10e2",
  "case_sha256": "ed23610dad5acf7ccb08c2c9ec24a56635ddbbfd9c1e0b707cd04f901c644b8f",
  "id": "v2-a12",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "326d9a85fd88a5aa0c52c1b2ac1d88f17c8d8e63aec35628899f681b487ede9b",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "15718cd6a79755ba90e1d57bf06e9e0f7b3bb1d421df764eec615d64e723bbb7",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a13 — alias

For USDT as the transferred token, report each active date's ERC20 event count with a non-null normalized amount and sum of those normalized units; exclude events positively marked ERC721 and order by date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "usdt_daily_normalized_erc20_totals"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:usdt_daily_normalized_erc20_totals",
  "id": "v2-a13",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `usdt_daily_normalized_erc20_totals`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
    SUM(normalized_amount) AS normalized_units FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE token_owner='Tether' AND is_erc20 IS TRUE
    AND COALESCE(is_erc721,FALSE) IS FALSE AND normalized_amount IS NOT NULL
    GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0xdac17f958d2ee523a2206206994597c13d831ec7"
      ],
      "mention": {
        "end": 8,
        "start": 4,
        "text": "USDT"
      },
      "owner": "Tether"
    }
  ],
  "id": "v2-a13",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "token_contract"
      }
    ],
    "direction": [],
    "fact": "token_transfer"
  },
  "question_sha256": "e447160fdf240d32ab3ac732a40e64b436d2d4d7dc4257556d0eb479fad2b94c",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "is_erc20",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "is_erc721",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "normalized_amount",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_owner",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "44dc49e55a473d86d36a3756a9326308373ede6ee6f2adba3ad45528705ceb83"
}
```

Lý do tác giả: Token ticker alias is token identity; local normalized totals use DOUBLE, not exact accounting.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "23971"
    ],
    [
      "number",
      "1392186418.5159185"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "25237"
    ],
    [
      "number",
      "1792306727.1747925"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "21864"
    ],
    [
      "number",
      "2051228954.19319"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "22147"
    ],
    [
      "number",
      "1417518716.6998956"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "24292"
    ],
    [
      "number",
      "1227540634.5260854"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "146d2c8f2249868ed8d78e39cea005d6da833dbcf46715299538571a6dd9a8f6",
  "case_sha256": "a4037224e044ffb31fa67c5c9a1498c886fb367281a4875fab3dda6dc5fdac0d",
  "id": "v2-a13",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "e447160fdf240d32ab3ac732a40e64b436d2d4d7dc4257556d0eb479fad2b94c",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "44dc49e55a473d86d36a3756a9326308373ede6ee6f2adba3ad45528705ceb83",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a14 — alias

For WBTC as the transferred token, return each date with valid numeric raw values, the event count and minimum and maximum raw value, without decimal normalization; order by date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "wbtc_daily_raw_extrema"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:wbtc_daily_raw_extrema",
  "id": "v2-a14",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `wbtc_daily_raw_extrema`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
    MIN(value_bignumeric) AS minimum_raw, MAX(value_bignumeric) AS maximum_raw
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE token_owner='Wrapped Bitcoin' AND value_cast_valid
    GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"
      ],
      "mention": {
        "end": 8,
        "start": 4,
        "text": "WBTC"
      },
      "owner": "Wrapped Bitcoin"
    }
  ],
  "id": "v2-a14",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "token_contract"
      }
    ],
    "direction": [],
    "fact": "token_transfer"
  },
  "question_sha256": "1e3fafaf07279c31aec2156b2235ec8defcfcc2d28b0afd376b8d7f0b57e782e",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "value_bignumeric",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "value_cast_valid",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "17d7a5fd054f8f08e83c53db55542a7f08daade2b75f958ef3efd69aa26644d5"
}
```

Lý do tác giả: Raw cast range differs locally from BigQuery BIGNUMERIC; full parity remains pending.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "399"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "2400000000"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "621"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "627994208199"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "535"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "2500000000"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "672"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "2906241076"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "862"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "1397842315"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "e6403d23401c6a8040a92e12cbe26a1d1337f831f12dd816d6bcd12f2f19b319",
  "case_sha256": "5d4f45f065088c13de2ddeefc4734563a46066ed959212e6fc0f86da3c9fec73",
  "id": "v2-a14",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "1e3fafaf07279c31aec2156b2235ec8defcfcc2d28b0afd376b8d7f0b57e782e",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "17d7a5fd054f8f08e83c53db55542a7f08daade2b75f958ef3efd69aa26644d5",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a15 — alias

For LINK as the transferred token, return total event count and the counts with valid raw numeric values equal to zero and greater than zero. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "link_zero_raw_value_events"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:link_zero_raw_value_events",
  "id": "v2-a15",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `link_zero_raw_value_events`. Property focus: `None`.

```sql
SELECT COUNT(*) AS events, COUNTIF(value_bignumeric=0) AS zero_raw,
    COUNTIF(value_bignumeric>0) AS positive_raw FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE token_owner='Chainlink'
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x514910771af9ca656af840dff83e8264ecf986ca"
      ],
      "mention": {
        "end": 8,
        "start": 4,
        "text": "LINK"
      },
      "owner": "Chainlink"
    }
  ],
  "id": "v2-a15",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "token_contract"
      }
    ],
    "direction": [],
    "fact": "token_transfer"
  },
  "question_sha256": "4b9a08364d0cf4b173a1e1101a49823fe6bce3b42d99f5e7ad17210745d75377",
  "schema": {
    "columns": [
      {
        "column": "token_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "value_bignumeric",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "5af2eef32af5f46495c43eeade0546729791bea4ad684c005c3e4a2a1c5b2790"
}
```

Lý do tác giả: LINK uniquely resolves to Chainlink; invalid cast values enter neither raw bucket.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "14740"
    ],
    [
      "number",
      "117"
    ],
    [
      "number",
      "14623"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "903f901881e0a44be9d3c8eb35e0d1b1cfc9ee748debf4af9cd3ef4d773d2781",
  "case_sha256": "e07b3f8637b2acb3052901962907ddfa8bc0e87a79eb001fd393efb29ba5fc8d",
  "id": "v2-a15",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "4b9a08364d0cf4b173a1e1101a49823fe6bce3b42d99f5e7ad17210745d75377",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "5af2eef32af5f46495c43eeade0546729791bea4ad684c005c3e4a2a1c5b2790",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a16 — alias

For curve as a recipient of token events, report each active date's distinct token-contract count and distinct sender count; return dates chronologically. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "curve_inbound_daily_token_diversity"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:curve_inbound_daily_token_diversity",
  "id": "v2-a16",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `curve_inbound_daily_token_diversity`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(DISTINCT token_address) AS tokens,
    COUNT(DISTINCT from_address) AS senders FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Curve DEX'
    GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0c0e5f2ff0ff18a3be9b835635039256dc4b4963",
        "0x45312ea0eff7e09c83cbe249fa1d7598c4c8cd4e",
        "0x6a8cbed756804b16e05e741edabd5cb544ae21bf",
        "0x98ee851a00abee0d95d08cf4ca2bdce32aeaaf7f",
        "0xb9fc157394af804a3578134a6585c0dc9cc990d4",
        "0xf18056bbd320e96a48e3fbf8bc061322531aac99"
      ],
      "mention": {
        "end": 9,
        "start": 4,
        "text": "curve"
      },
      "owner": "Curve DEX"
    }
  ],
  "id": "v2-a16",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "7184c72be304aa1a7c43b74c3d634f0f051a01c59af5c2af212f21db6824a800",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "from_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "ba9b73b5135cea4a28a0985ae8ed1e197b2bbb483a70f92a69fb009a9cc17854"
}
```

Lý do tác giả: Alias refers to protocol endpoints, not a token ticker.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "9"
    ],
    [
      "number",
      "6"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "7"
    ],
    [
      "number",
      "8"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "16"
    ],
    [
      "number",
      "22"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "5"
    ],
    [
      "number",
      "5"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "20"
    ],
    [
      "number",
      "19"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "71e4c5c2e902332152974f7e497312bab3957d7144b3aa5cf9a24263f7030247",
  "case_sha256": "40641f907bc45ea38521f051a3d008048b689d31160b171422eae2a4775b70a4",
  "id": "v2-a16",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "7184c72be304aa1a7c43b74c3d634f0f051a01c59af5c2af212f21db6824a800",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "ba9b73b5135cea4a28a0985ae8ed1e197b2bbb483a70f92a69fb009a9cc17854",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a17 — alias

For token events sent by the mixer, group by token contract and raw-value cast-validity flag, returning counts ordered by token address and flag. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "the_mixer_outbound_cast_validity"
  ],
  "difficulty": "medium",
  "empty_reason": "Sample has no token events sent from the pinned Tornado Cash endpoint set. Legacy router activity is not evidence for these known pool endpoints; this sampled absence does not establish full-snapshot absence. Recheck in T09B.",
  "family_id": "t09a:the_mixer_outbound_cast_validity",
  "id": "v2-a17",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `the_mixer_outbound_cast_validity`. Property focus: `None`.

```sql
SELECT token_address, value_cast_valid, COUNT(*) AS events FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE from_owner='Tornado Cash' GROUP BY token_address, value_cast_valid
    ORDER BY token_address, value_cast_valid
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x03893a7c7463ae47d46bc7f091665f1893656003",
        "0x07687e702b410fa43f4cb4af7fa097918ffd2730",
        "0x0836222f2b2b24a3f36f98668ed8f0b38d1a872f",
        "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc",
        "0x169ad27a470d064dede56a2d3ff727986b15d52b",
        "0x178169b423a011fff22b9e3f3abea13414ddd0f1",
        "0x22aaa7720ddd5388a3c0a3333430953c68f1849b",
        "0x23773e65ed146a459791799d01336db287f25334",
        "0x2717c5e28cf931547b621a5dddb772ab6a35b701",
        "0x4736dcf1b7a3d580672cce6e7c65cd5cc9cfba9d",
        "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936",
        "0x610b717796ad172b316836ac95a2ffad065ceab4",
        "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf",
        "0xa160cdab225685da1d56aa342ad8841c3b53f291",
        "0xbb93e510bbcd0b7beb5a853875f9ec60275cf498",
        "0xd21be7248e0197ee08e0c20d4a96debdac3d20af",
        "0xd4b88df4d29f5cedd6857912842cff3b20c8cfa3",
        "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b",
        "0xd96f2b1c14db8458374d9aca76e26c3d18364307",
        "0xfd8610d20aa15b7b2e3be39b396a1bc3516c7144"
      ],
      "mention": {
        "end": 34,
        "start": 25,
        "text": "the mixer"
      },
      "owner": "Tornado Cash"
    }
  ],
  "id": "v2-a17",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "004571650aacd1905aa2afa7d75b26268fb7c94d89a7bdbc3d6e5b90f171d7fc",
  "schema": {
    "columns": [
      {
        "column": "from_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "value_cast_valid",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "ff23130f43c601271f1849721779f3b267309abb356a3433dd8b1962bd65af0f"
}
```

Lý do tác giả: Dictionary service alias names one owner; it is not a request for all mixers.

Sample: 0 rows; empty=True; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Sample has no token events sent from the pinned Tornado Cash endpoint set. Legacy router activity is not evidence for these known pool endpoints; this sampled absence does not establish full-snapshot absence. Recheck in T09B.

Preview (giá trị có type tag):

```json
[]
```

Review binding:

```json
{
  "annotation_sha256": "8f4116f767ab0a682dc80299379d9cfd890063d7564fd0334655b66f0964bbf9",
  "case_sha256": "3cccf62ea8ff5f12cbbc0821e67c6ba9f643af4f520f87649ee096ca2550774b",
  "id": "v2-a17",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "004571650aacd1905aa2afa7d75b26268fb7c94d89a7bdbc3d6e5b90f171d7fc",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "ff23130f43c601271f1849721779f3b267309abb356a3433dd8b1962bd65af0f",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a18 — alias

For pancake swap, report dates with successful incoming outer calls, including their count and distinct sender count, ordered by date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "pancake_swap_successful_call_days"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:pancake_swap_successful_call_days",
  "id": "v2-a18",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `pancake_swap_successful_call_days`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS calls,
    COUNT(DISTINCT from_address) AS senders FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE to_owner='PancakeSwap AMM' AND receipt_status=1 GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x1097053fd2ea711dad45caccc45eff7548fcb362",
        "0x4e742608c39eafd8525b03d39121ea00ccf3c727"
      ],
      "mention": {
        "end": 16,
        "start": 4,
        "text": "pancake swap"
      },
      "owner": "PancakeSwap AMM"
    }
  ],
  "id": "v2-a18",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "7631f8c997d21546b24fbda4f3d2d07d9e7ea91c37827fb533eccbc1e52b7070",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "from_address",
        "relation": "labeled_transactions"
      },
      {
        "column": "receipt_status",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "16b4134e7c61b536b412660841f0857e41fde087a76332ab95e0e9a3d34dceb7"
}
```

Lý do tác giả: Spaced alias is unambiguous in the pinned dictionary; bare PancakeSwap is ambiguous.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-12"
    ],
    [
      "number",
      "4"
    ],
    [
      "number",
      "1"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "0e96b3f991a6fc1362f97d627769cce6dc66b541907cff739c8171a41e0b691b",
  "case_sha256": "6d20ada7882ed6b42930f133cca21fc1fac56cc5425ff2e7993b564835ef8aed",
  "id": "v2-a18",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "7631f8c997d21546b24fbda4f3d2d07d9e7ea91c37827fb533eccbc1e52b7070",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "16b4134e7c61b536b412660841f0857e41fde087a76332ab95e0e9a3d34dceb7",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a19 — alias

For chainlink ccip, give incoming outer transaction count, zero-value call count and total receipt gas used per receipt status; order by status and retain unknown status. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "chainlink_ccip_receipt_status"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:chainlink_ccip_receipt_status",
  "id": "v2-a19",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `chainlink_ccip_receipt_status`. Property focus: `None`.

```sql
SELECT receipt_status, COUNT(*) AS calls, COUNTIF(value_wei=0) AS zero_value, SUM(receipt_gas_used) AS gas
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='CCIP' GROUP BY receipt_status ORDER BY receipt_status
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0xb22764f98dd05c789929716d677382df22c05cb6"
      ],
      "mention": {
        "end": 18,
        "start": 4,
        "text": "chainlink ccip"
      },
      "owner": "CCIP"
    }
  ],
  "id": "v2-a19",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "b644ec5e8f392d0ed04175efc8660af373cf00e768c20edabe1562c401c01f6b",
  "schema": {
    "columns": [
      {
        "column": "receipt_gas_used",
        "relation": "labeled_transactions"
      },
      {
        "column": "receipt_status",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "value_wei",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "99597005b686e07bb21f1d84ff22c3737b1baf7e822c22cd0cb3219e83943111"
}
```

Lý do tác giả: CCIP is a bridge owner distinct from the Chainlink token contract.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "1"
    ],
    [
      "number",
      "28"
    ],
    [
      "number",
      "28"
    ],
    [
      "number",
      "1203534"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "7f87d7aae3a349cf3af26946f4dc0367667a51862dbf29b5b4a0fc1adf0e870c",
  "case_sha256": "6af55756f766445aa9999814b368cbb7021ccf476d7775e7b9e4e96c2ae1f7d2",
  "id": "v2-a19",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "b644ec5e8f392d0ed04175efc8660af373cf00e768c20edabe1562c401c01f6b",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "99597005b686e07bb21f1d84ff22c3737b1baf7e822c22cd0cb3219e83943111",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-a20 — alias

For token events received by tornado cash classic, report token contract, event count, first timestamp and last timestamp; sort by token address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "tornado_classic_token_activity_bounds"
  ],
  "difficulty": "medium",
  "empty_reason": "Sample has no token events received by the pinned Tornado Cash endpoint set. The service alias is well-defined, but legacy sample selection does not establish pool coverage. Recheck the activity bounds on the full snapshot in T09B.",
  "family_id": "t09a:tornado_classic_token_activity_bounds",
  "id": "v2-a20",
  "primary_group": "alias",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `tornado_classic_token_activity_bounds`. Property focus: `None`.

```sql
SELECT token_address, COUNT(*) AS events, MIN(block_timestamp) AS first_event,
    MAX(block_timestamp) AS last_event FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Tornado Cash'
    GROUP BY token_address ORDER BY token_address
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x03893a7c7463ae47d46bc7f091665f1893656003",
        "0x07687e702b410fa43f4cb4af7fa097918ffd2730",
        "0x0836222f2b2b24a3f36f98668ed8f0b38d1a872f",
        "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc",
        "0x169ad27a470d064dede56a2d3ff727986b15d52b",
        "0x178169b423a011fff22b9e3f3abea13414ddd0f1",
        "0x22aaa7720ddd5388a3c0a3333430953c68f1849b",
        "0x23773e65ed146a459791799d01336db287f25334",
        "0x2717c5e28cf931547b621a5dddb772ab6a35b701",
        "0x4736dcf1b7a3d580672cce6e7c65cd5cc9cfba9d",
        "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936",
        "0x610b717796ad172b316836ac95a2ffad065ceab4",
        "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf",
        "0xa160cdab225685da1d56aa342ad8841c3b53f291",
        "0xbb93e510bbcd0b7beb5a853875f9ec60275cf498",
        "0xd21be7248e0197ee08e0c20d4a96debdac3d20af",
        "0xd4b88df4d29f5cedd6857912842cff3b20c8cfa3",
        "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b",
        "0xd96f2b1c14db8458374d9aca76e26c3d18364307",
        "0xfd8610d20aa15b7b2e3be39b396a1bc3516c7144"
      ],
      "mention": {
        "end": 49,
        "start": 29,
        "text": "tornado cash classic"
      },
      "owner": "Tornado Cash"
    }
  ],
  "id": "v2-a20",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "ef46a4ef41fd5020718c901cf55de79c484e1659e2ee1bb52d6f1bf4b9c796d4",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "8b9aaec657ebdefed29971f8934e5cea5d28b86675d651d40aae128ade7bb9c7"
}
```

Lý do tác giả: First/last timestamps apply to event receipts, not outer transaction senders.

Sample: 0 rows; empty=True; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Sample has no token events received by the pinned Tornado Cash endpoint set. The service alias is well-defined, but legacy sample selection does not establish pool coverage. Recheck the activity bounds on the full snapshot in T09B.

Preview (giá trị có type tag):

```json
[]
```

Review binding:

```json
{
  "annotation_sha256": "665b3916a7ef6c7ec9adc684f519108ea815a62555466b0e2f16f423c619739f",
  "case_sha256": "7b41cd0969ed311c3c53f034396cae4a3f1afa792a769227d36b614374e895d9",
  "id": "v2-a20",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "ef46a4ef41fd5020718c901cf55de79c484e1659e2ee1bb52d6f1bf4b9c796d4",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "8b9aaec657ebdefed29971f8934e5cea5d28b86675d651d40aae128ade7bb9c7",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c01 — class_level

Within dictionary-labeled centralized exchanges, give incoming outer transaction counts by owner and UTC day of week; return owner, weekday number with Sunday=1, and count, sorted by owner then weekday. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "exchange_inbound_weekday_histogram"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:exchange_inbound_weekday_histogram",
  "id": "v2-c01",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `exchange_inbound_weekday_histogram`. Property focus: `None`.

```sql
SELECT to_owner AS owner, EXTRACT(DAYOFWEEK FROM block_timestamp AT TIME ZONE 'UTC') AS weekday,
    COUNT(*) AS n FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_category='exchange'
    GROUP BY owner, weekday ORDER BY owner, weekday
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "exchange",
      "concept_class": "ExchangeAccount",
      "mention": {
        "end": 47,
        "start": 26,
        "text": "centralized exchanges"
      },
      "owners": [
        "Binance",
        "Bitfinex",
        "Bitget",
        "Bitkub",
        "Bitmex",
        "Bitrue",
        "Bitstamp",
        "Bitunix",
        "Bitvavo",
        "Bybit",
        "CoinEx",
        "Crypto-com",
        "Deribit",
        "Gate.io",
        "Gemini",
        "HTX",
        "HashKey Exchange",
        "Indodax",
        "Korbit",
        "KuCoin",
        "MEXC",
        "Nexo",
        "OKX",
        "OSL HK",
        "Phemex",
        "Poloniex",
        "Robinhood",
        "SwissBorg",
        "VALR",
        "WEEX"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c01",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "85cc6ccb19d903e78fa052a42c9959f02c7a2fd3afc9dbd1e812eb31d5252ef0",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_category",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "abf4fc6e28c2b4694b1026d9b6d7709faecb68526cb8c94a60cfd57aafa7d30f"
}
```

Lý do tác giả: All thirty dictionary ExchangeAccount owners, not all exchanges on Ethereum.

Sample: 196 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "Binance"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "257"
    ]
  ],
  [
    [
      "string",
      "Binance"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1214"
    ]
  ],
  [
    [
      "string",
      "Binance"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "482"
    ]
  ],
  [
    [
      "string",
      "Binance"
    ],
    [
      "number",
      "3"
    ],
    [
      "number",
      "1276"
    ]
  ],
  [
    [
      "string",
      "Binance"
    ],
    [
      "number",
      "4"
    ],
    [
      "number",
      "827"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "54836957cf321f9c4748c5692e4ac8f6dee01c5f3afcacfaba8a7e99e792e2d9",
  "case_sha256": "eddd50451d4d4053ce65a0478a1d5d59d9fb9ee37b4e5e399b2995b2a2d4f10d",
  "id": "v2-c01",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "85cc6ccb19d903e78fa052a42c9959f02c7a2fd3afc9dbd1e812eb31d5252ef0",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "abf4fc6e28c2b4694b1026d9b6d7709faecb68526cb8c94a60cfd57aafa7d30f",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c02 — class_level

For dictionary-labeled decentralized exchanges receiving successful outer calls, return owner, call count, average and maximum receipt gas used, sorted by owner. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "dex_successful_call_gas_by_owner"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:dex_successful_call_gas_by_owner",
  "id": "v2-c02",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `dex_successful_call_gas_by_owner`. Property focus: `None`.

```sql
SELECT to_owner AS owner, COUNT(*) AS calls, AVG(receipt_gas_used) AS average_gas,
    MAX(receipt_gas_used) AS maximum_gas FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE to_category='dex' AND receipt_status=1 GROUP BY owner ORDER BY owner
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "dex",
      "concept_class": "DEXProtocol",
      "mention": {
        "end": 46,
        "start": 23,
        "text": "decentralized exchanges"
      },
      "owners": [
        "Curve DEX",
        "PancakeSwap AMM",
        "Uniswap V2",
        "Uniswap V3",
        "Uniswap V4"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c02",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "e670a88a44674b7afb6435a3ec1d10b3de4e301743a2f04ee23803c0bf0a9d0b",
  "schema": {
    "columns": [
      {
        "column": "receipt_gas_used",
        "relation": "labeled_transactions"
      },
      {
        "column": "receipt_status",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_category",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "879e3181e1cc96002d81fe9a04b4d276fc1e57e66b88af9dd52dbb83d0b13e53"
}
```

Lý do tác giả: Protocol class is operational DEX endpoints, not governance-token holders.

Sample: 5 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "Curve DEX"
    ],
    [
      "number",
      "187"
    ],
    [
      "number",
      "2371694.090909091"
    ],
    [
      "number",
      "7174049"
    ]
  ],
  [
    [
      "string",
      "PancakeSwap AMM"
    ],
    [
      "number",
      "4"
    ],
    [
      "number",
      "2507604"
    ],
    [
      "number",
      "2507604"
    ]
  ],
  [
    [
      "string",
      "Uniswap V2"
    ],
    [
      "number",
      "4533"
    ],
    [
      "number",
      "189055.6569600706"
    ],
    [
      "number",
      "2737554"
    ]
  ],
  [
    [
      "string",
      "Uniswap V3"
    ],
    [
      "number",
      "2118"
    ],
    [
      "number",
      "335292.85033050046"
    ],
    [
      "number",
      "5194727"
    ]
  ],
  [
    [
      "string",
      "Uniswap V4"
    ],
    [
      "number",
      "1205"
    ],
    [
      "number",
      "167693.46473029046"
    ],
    [
      "number",
      "10067640"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "f317614e12d6cee50a4aa65b3afc93deec5441268824619f8b46e610b30f392c",
  "case_sha256": "4a65c60b7bec6737b1f2d50c264a76390e72b8afb027ff62b25dc17db85ea22e",
  "id": "v2-c02",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "e670a88a44674b7afb6435a3ec1d10b3de4e301743a2f04ee23803c0bf0a9d0b",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "879e3181e1cc96002d81fe9a04b4d276fc1e57e66b88af9dd52dbb83d0b13e53",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c03 — class_level

For each dictionary-labeled lending owner receiving outer transactions, show total rows, zero-value rows and positive-value rows; sort by owner. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "lending_inbound_value_profile"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:lending_inbound_value_profile",
  "id": "v2-c03",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `lending_inbound_value_profile`. Property focus: `None`.

```sql
SELECT to_owner AS owner, COUNT(*) AS total, COUNTIF(value_wei=0) AS zero_value,
    COUNTIF(value_wei>0) AS positive_value FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_category='lending'
    GROUP BY owner ORDER BY owner
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "lending",
      "concept_class": "LendingProtocol",
      "mention": {
        "end": 35,
        "start": 28,
        "text": "lending"
      },
      "owners": [
        "Concrete",
        "Gauntlet",
        "Lista Lending",
        "Sentora",
        "Veda"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c03",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "2610e93ec63e325bb44c099bebf2dd9296e6125dfe80555c713c3a90c20ab095",
  "schema": {
    "columns": [
      {
        "column": "to_category",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "value_wei",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "c19981d3e60db72fb4f699111438e263f165e9fcf6b8eb29f9fc1a032a7d4766"
}
```

Lý do tác giả: Includes only dictionary lending endpoints; token owners with similar names are excluded.

Sample: 4 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "Gauntlet"
    ],
    [
      "number",
      "292"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "291"
    ]
  ],
  [
    [
      "string",
      "Lista Lending"
    ],
    [
      "number",
      "490"
    ],
    [
      "number",
      "490"
    ],
    [
      "number",
      "0"
    ]
  ],
  [
    [
      "string",
      "Sentora"
    ],
    [
      "number",
      "264"
    ],
    [
      "number",
      "264"
    ],
    [
      "number",
      "0"
    ]
  ],
  [
    [
      "string",
      "Veda"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "0"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "b6699db53251f28a69a79da838cddb3b4bdced86ac7ce90584931ebbc15ed8f4",
  "case_sha256": "e13f6b55fdd486415e18927e632ce1444d1182a55f020e9d591c91c43900ba99",
  "id": "v2-c03",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "2610e93ec63e325bb44c099bebf2dd9296e6125dfe80555c713c3a90c20ab095",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "c19981d3e60db72fb4f699111438e263f165e9fcf6b8eb29f9fc1a032a7d4766",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c04 — class_level

For dictionary-labeled bridge owners that send token events, return owner, event count and distinct token-contract count, ordered by event count descending and then owner. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "bridge_outbound_token_breadth"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:bridge_outbound_token_breadth",
  "id": "v2-c04",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `bridge_outbound_token_breadth`. Property focus: `None`.

```sql
SELECT from_owner AS owner, COUNT(*) AS events, COUNT(DISTINCT token_address) AS tokens
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_category='bridge' GROUP BY owner ORDER BY events DESC, owner
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "bridge",
      "concept_class": "BridgeProtocol",
      "mention": {
        "end": 29,
        "start": 23,
        "text": "bridge"
      },
      "owners": [
        "Aster Bridge",
        "CCIP",
        "Merlins Seal",
        "Optimism Bridge",
        "USDT0"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c04",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "from"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "c1f3baf96dbd6988d0e0fbe882d9d12ec763fb45d0e4a83e99a3e5cd328d50e0",
  "schema": {
    "columns": [
      {
        "column": "from_category",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "from_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "82bc7fca202260007a1c6322678adae499bc4fd3d34305afa6ef2dcd573e41c7"
}
```

Lý do tác giả: Only labeled bridge endpoints; sending a bridge token is insufficient.

Sample: 3 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "Aster Bridge"
    ],
    [
      "number",
      "2806"
    ],
    [
      "number",
      "6"
    ]
  ],
  [
    [
      "string",
      "Optimism Bridge"
    ],
    [
      "number",
      "169"
    ],
    [
      "number",
      "36"
    ]
  ],
  [
    [
      "string",
      "USDT0"
    ],
    [
      "number",
      "40"
    ],
    [
      "number",
      "1"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "8ec67f2ce495d81c8a0b63d2859575230c7335b6a0f0f064e382f477fb4c3eef",
  "case_sha256": "bd6bc0062230998d9f5191ca52c9761353b533d27096c15612bd6fed3e2b60c2",
  "id": "v2-c04",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "c1f3baf96dbd6988d0e0fbe882d9d12ec763fb45d0e4a83e99a3e5cd328d50e0",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "82bc7fca202260007a1c6322678adae499bc4fd3d34305afa6ef2dcd573e41c7",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c05 — class_level

Count outer transactions involving dictionary-labeled mixers as sender or recipient by UTC hour of day; return hour and count in hour order, counting each transaction once. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "mixer_either_role_hour_counts"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:mixer_either_role_hour_counts",
  "id": "v2-c05",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `mixer_either_role_hour_counts`. Property focus: `None`.

```sql
SELECT EXTRACT(HOUR FROM block_timestamp AT TIME ZONE 'UTC') AS hour, COUNT(*) AS n
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_category='mixer' OR to_category='mixer'
    GROUP BY hour ORDER BY hour
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "mixer",
      "concept_class": "MixerAccount",
      "mention": {
        "end": 60,
        "start": 54,
        "text": "mixers"
      },
      "owners": [
        "Tornado Cash"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c05",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "either"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "b01d4c54d5164c93d4539546d53a544d9d44ca78f1008d5c89152018f12871bd",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "from_category",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_category",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "99dd9fbcf7919db166999b62ab4bcda7d84e63668f8fc513b0eb860ce7ad7a0a"
}
```

Lý do tác giả: OR selects union of endpoint roles without doubling internal rows.

Sample: 23 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "0"
    ],
    [
      "number",
      "4"
    ]
  ],
  [
    [
      "number",
      "1"
    ],
    [
      "number",
      "3"
    ]
  ],
  [
    [
      "number",
      "2"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "number",
      "3"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "number",
      "5"
    ],
    [
      "number",
      "2"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "f486efb5d7469c92612f7eb1b48648cecfb829eb7e471174bc28434eb7c23e46",
  "case_sha256": "b0698f91b9587b0f28908540265a2368a57141c1643222a5166cc9a6031281f0",
  "id": "v2-c05",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "b01d4c54d5164c93d4539546d53a544d9d44ca78f1008d5c89152018f12871bd",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "99dd9fbcf7919db166999b62ab4bcda7d84e63668f8fc513b0eb860ce7ad7a0a",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c06 — class_level

For dictionary-labeled staking recipients, return each token contract's incoming event count and distinct sender count, sorted by token address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "staking_inbound_token_mix"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:staking_inbound_token_mix",
  "id": "v2-c06",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `staking_inbound_token_mix`. Property focus: `None`.

```sql
SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT from_address) AS senders
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_category='staking' GROUP BY token_address ORDER BY token_address
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "staking",
      "concept_class": "StakingAccount",
      "mention": {
        "end": 30,
        "start": 23,
        "text": "staking"
      },
      "owners": [
        "Hastra"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c06",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "to"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "8f2c34fa52991cfaeacd4078820217db1769a1eaa21a707683ac82f5aaf9d83c",
  "schema": {
    "columns": [
      {
        "column": "from_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_category",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "306f10b85e7c6627eb2ae897904c90841d23ea963d15ebdfa264ff180b8731b6"
}
```

Lý do tác giả: Class membership remains annotated even if this small class has no sampled activity.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x6ad038ca6c04e885630851278ca0a856ad9a66cc"
    ],
    [
      "number",
      "792"
    ],
    [
      "number",
      "39"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "d3e1bbb63197b96d1fa2c5d2790b802d4c989d2163b72fd1898c74746f6cfb3d",
  "case_sha256": "f6c49ab3bd554904742a653b48a1542732a913e5888f194d60d991d88c0a6a9e",
  "id": "v2-c06",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "8f2c34fa52991cfaeacd4078820217db1769a1eaa21a707683ac82f5aaf9d83c",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "306f10b85e7c6627eb2ae897904c90841d23ea963d15ebdfa264ff180b8731b6",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c07 — class_level

Among outer transactions whose two endpoints belong to dictionary-labeled exchanges, return ordered sender-owner and recipient-owner pairs with row counts; include same-owner pairs and sort by count descending then the two owner names. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "exchange_internal_class_owner_pairs"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:exchange_internal_class_owner_pairs",
  "id": "v2-c07",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `exchange_internal_class_owner_pairs`. Property focus: `None`.

```sql
SELECT from_owner, to_owner, COUNT(*) AS n FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE from_category='exchange' AND to_category='exchange'
    GROUP BY from_owner, to_owner ORDER BY n DESC, from_owner, to_owner
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "exchange",
      "concept_class": "ExchangeAccount",
      "mention": {
        "end": 83,
        "start": 74,
        "text": "exchanges"
      },
      "owners": [
        "Binance",
        "Bitfinex",
        "Bitget",
        "Bitkub",
        "Bitmex",
        "Bitrue",
        "Bitstamp",
        "Bitunix",
        "Bitvavo",
        "Bybit",
        "CoinEx",
        "Crypto-com",
        "Deribit",
        "Gate.io",
        "Gemini",
        "HTX",
        "HashKey Exchange",
        "Indodax",
        "Korbit",
        "KuCoin",
        "MEXC",
        "Nexo",
        "OKX",
        "OSL HK",
        "Phemex",
        "Poloniex",
        "Robinhood",
        "SwissBorg",
        "VALR",
        "WEEX"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c07",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "either"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "4afb6bee606bdaac8e7f47d5ab00f0c8e5dd92e7ffb430b8a1cea9b4d5dbf457",
  "schema": {
    "columns": [
      {
        "column": "from_category",
        "relation": "labeled_transactions"
      },
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_category",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "4e894bd76d99330770de494cbca95908573131d740c99e9270b25e3a8d0bbfbb"
}
```

Lý do tác giả: Both endpoint predicates are required. Class direction either describes roles, not SQL OR.

Sample: 31 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "KuCoin"
    ],
    [
      "string",
      "KuCoin"
    ],
    [
      "number",
      "2821"
    ]
  ],
  [
    [
      "string",
      "Binance"
    ],
    [
      "string",
      "Binance"
    ],
    [
      "number",
      "1495"
    ]
  ],
  [
    [
      "string",
      "OKX"
    ],
    [
      "string",
      "OKX"
    ],
    [
      "number",
      "167"
    ]
  ],
  [
    [
      "string",
      "Bybit"
    ],
    [
      "string",
      "Bybit"
    ],
    [
      "number",
      "114"
    ]
  ],
  [
    [
      "string",
      "Deribit"
    ],
    [
      "string",
      "Deribit"
    ],
    [
      "number",
      "79"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "c3f62a6d3962cce16387f4d8bc34526edefd0ec191e1b8249293cd237da006e2",
  "case_sha256": "4d2eaa09cf675650764dcdca528b750077a6e8827dd9e899d00aca087d03954f",
  "id": "v2-c07",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "4afb6bee606bdaac8e7f47d5ab00f0c8e5dd92e7ffb430b8a1cea9b4d5dbf457",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "4e894bd76d99330770de494cbca95908573131d740c99e9270b25e3a8d0bbfbb",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c08 — class_level

For each dictionary-labeled DEX owner sending token events, report distinct recipient addresses, distinct outer transactions and event count; sort by owner. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "dex_outbound_token_recipient_reach"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:dex_outbound_token_recipient_reach",
  "id": "v2-c08",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `dex_outbound_token_recipient_reach`. Property focus: `None`.

```sql
SELECT from_owner AS owner, COUNT(DISTINCT to_address) AS recipients,
    COUNT(DISTINCT transaction_hash) AS transactions, COUNT(*) AS events
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_category='dex' GROUP BY owner ORDER BY owner
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "dex",
      "concept_class": "DEXProtocol",
      "mention": {
        "end": 31,
        "start": 28,
        "text": "DEX"
      },
      "owners": [
        "Curve DEX",
        "PancakeSwap AMM",
        "Uniswap V2",
        "Uniswap V3",
        "Uniswap V4"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c08",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "from"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "d18e9274117fabbd4cf5ee7d092b0697afb1f8de005c2f73c3775c87accd40ec",
  "schema": {
    "columns": [
      {
        "column": "from_category",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "from_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "transaction_hash",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "c8065bd0f3cc1024185b5b85e04cd594dc2ed57b14c3906905470966900c1f9b"
}
```

Lý do tác giả: Distinct counts are recomputed across the owner's complete labeled endpoint set.

Sample: 4 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "Curve DEX"
    ],
    [
      "number",
      "134"
    ],
    [
      "number",
      "114"
    ],
    [
      "number",
      "293"
    ]
  ],
  [
    [
      "string",
      "Uniswap V2"
    ],
    [
      "number",
      "792"
    ],
    [
      "number",
      "2224"
    ],
    [
      "number",
      "2246"
    ]
  ],
  [
    [
      "string",
      "Uniswap V3"
    ],
    [
      "number",
      "279"
    ],
    [
      "number",
      "653"
    ],
    [
      "number",
      "770"
    ]
  ],
  [
    [
      "string",
      "Uniswap V4"
    ],
    [
      "number",
      "4766"
    ],
    [
      "number",
      "19237"
    ],
    [
      "number",
      "25964"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "6a1c77163586a39411a808e6f102e40bd552d9e407d51a2ded7e4ac398b62caf",
  "case_sha256": "64b3dc6736a663e37018d923dcd92c7b372b347aa52c854382910e122558ac00",
  "id": "v2-c08",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "d18e9274117fabbd4cf5ee7d092b0697afb1f8de005c2f73c3775c87accd40ec",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "c8065bd0f3cc1024185b5b85e04cd594dc2ed57b14c3906905470966900c1f9b",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c09 — class_level

Across dictionary-labeled money market recipients, report each active date's incoming outer transaction count and distinct sender count, pooling owners and ordering by date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "money_market_daily_inbound_senders"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:money_market_daily_inbound_senders",
  "id": "v2-c09",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `money_market_daily_inbound_senders`. Property focus: `None`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS calls,
    COUNT(DISTINCT from_address) AS senders FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_category='lending'
    GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "lending",
      "concept_class": "LendingProtocol",
      "mention": {
        "end": 38,
        "start": 26,
        "text": "money market"
      },
      "owners": [
        "Concrete",
        "Gauntlet",
        "Lista Lending",
        "Sentora",
        "Veda"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c09",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "64c98baa96d30069551bb8ec99676f85feadcafc2db64fccdfe897a455aa3e7c",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "from_address",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_category",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "6dd2d7439ee2cd6e76cbde438be38e118fc9f7da91611c05dec333cf25dd4115"
}
```

Lý do tác giả: Money market maps to the dictionary LendingProtocol class, with explicit pooling.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "20"
    ],
    [
      "number",
      "5"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "49"
    ],
    [
      "number",
      "13"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "32"
    ],
    [
      "number",
      "17"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "24"
    ],
    [
      "number",
      "12"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "27"
    ],
    [
      "number",
      "17"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "557171118c79e8b975382fbed29a5e0e5967adbbe1dd12e18eaaadccea5fc710",
  "case_sha256": "0eb76c7325a63272a961a23e11d898cd84e87f0c17479f21ac069ddf6f412f25",
  "id": "v2-c09",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "64c98baa96d30069551bb8ec99676f85feadcafc2db64fccdfe897a455aa3e7c",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "6dd2d7439ee2cd6e76cbde438be38e118fc9f7da91611c05dec333cf25dd4115",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c10 — class_level

For dictionary-labeled cross chain bridge recipients, report owner and active date with incoming outer transaction count and sum of declared wei, sorted by owner then date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "bridge_daily_outer_declared_value"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:bridge_daily_outer_declared_value",
  "id": "v2-c10",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `bridge_daily_outer_declared_value`. Property focus: `None`.

```sql
SELECT to_owner AS owner, DATE(block_timestamp) AS day, COUNT(*) AS calls,
    SUM(value_wei) AS declared_wei FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_category='bridge'
    GROUP BY owner, day ORDER BY owner, day
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "bridge",
      "concept_class": "BridgeProtocol",
      "mention": {
        "end": 41,
        "start": 23,
        "text": "cross chain bridge"
      },
      "owners": [
        "Aster Bridge",
        "CCIP",
        "Merlins Seal",
        "Optimism Bridge",
        "USDT0"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c10",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "c971bccb1319fb0e5ca66bb87d3c1fcf02121f13b311034f532f30ccad10769e",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_category",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "value_wei",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "70939a09399779ed8819f40019eed65c5b93cb95f5f428714b6b564af8b451e8"
}
```

Lý do tác giả: Declared call values do not assert completed bridge transfers or L2 outcomes.

Sample: 102 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "Aster Bridge"
    ],
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "364"
    ],
    [
      "number",
      "87357971650000000000"
    ]
  ],
  [
    [
      "string",
      "Aster Bridge"
    ],
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "451"
    ],
    [
      "number",
      "211561054820000000000"
    ]
  ],
  [
    [
      "string",
      "Aster Bridge"
    ],
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "321"
    ],
    [
      "number",
      "73879217902448478485"
    ]
  ],
  [
    [
      "string",
      "Aster Bridge"
    ],
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "452"
    ],
    [
      "number",
      "111543270000000000000"
    ]
  ],
  [
    [
      "string",
      "Aster Bridge"
    ],
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "572"
    ],
    [
      "number",
      "1873430271570000000000"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "d35661c5c83342abcc33acf70adc1d78d31a09082ee26d7a42bffa4544b72de3",
  "case_sha256": "f76ddc834efa3bef2945fd0104266315c9d855411c1e4f245a475e50f4c9b4ab",
  "id": "v2-c10",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "c971bccb1319fb0e5ca66bb87d3c1fcf02121f13b311034f532f30ccad10769e",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "70939a09399779ed8819f40019eed65c5b93cb95f5f428714b6b564af8b451e8",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c11 — class_level

For dictionary-labeled centralized exchanges, count token events whose sender and recipient have the same exchange owner. Return owner, token contract and count ordered by owner then token address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "exchange_same_owner_token_events"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:exchange_same_owner_token_events",
  "id": "v2-c11",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `exchange_same_owner_token_events`. Property focus: `None`.

```sql
SELECT from_owner AS owner, token_address, COUNT(*) AS events FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE from_category='exchange' AND to_category='exchange' AND from_owner=to_owner
    GROUP BY owner, token_address ORDER BY owner, token_address
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "exchange",
      "concept_class": "ExchangeAccount",
      "mention": {
        "end": 44,
        "start": 23,
        "text": "centralized exchanges"
      },
      "owners": [
        "Binance",
        "Bitfinex",
        "Bitget",
        "Bitkub",
        "Bitmex",
        "Bitrue",
        "Bitstamp",
        "Bitunix",
        "Bitvavo",
        "Bybit",
        "CoinEx",
        "Crypto-com",
        "Deribit",
        "Gate.io",
        "Gemini",
        "HTX",
        "HashKey Exchange",
        "Indodax",
        "Korbit",
        "KuCoin",
        "MEXC",
        "Nexo",
        "OKX",
        "OSL HK",
        "Phemex",
        "Poloniex",
        "Robinhood",
        "SwissBorg",
        "VALR",
        "WEEX"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c11",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "either"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "795f554697a547d7a4b6cb810ebb5d53673fe5781c613f95600b0f0020aed2f4",
  "schema": {
    "columns": [
      {
        "column": "from_category",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "from_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_category",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "9596aeb369d09276eeea04cced84afc177d429678552640517a9ab02b28551f0"
}
```

Lý do tác giả: Same-owner condition differs from exchange-to-exchange activity in general.

Sample: 1485 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "Binance"
    ],
    [
      "string",
      "0x0000000000085d4780b73119b644ae5ecd22b376"
    ],
    [
      "number",
      "4"
    ]
  ],
  [
    [
      "string",
      "Binance"
    ],
    [
      "string",
      "0x000000fa00b200406de700041cfc6b19bbfb4d13"
    ],
    [
      "number",
      "20"
    ]
  ],
  [
    [
      "string",
      "Binance"
    ],
    [
      "string",
      "0x000006c2a22ff4a44ff1f5d0f2ed65f781f55555"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "Binance"
    ],
    [
      "string",
      "0x031de51f3e8016514bd0963d0b2ab825a591db9a"
    ],
    [
      "number",
      "33"
    ]
  ],
  [
    [
      "string",
      "Binance"
    ],
    [
      "string",
      "0x04fa0d235c4abf4bcf4787af4cf447de572ef828"
    ],
    [
      "number",
      "15"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "1f58fbfdc1cd882f37292a0bea79ac87c55f4dc60a652ade8116f2c855fe3f92",
  "case_sha256": "44eef8a95c160274b83ca2410b435ed331df1aec26ac2a07aa7973056f74f20b",
  "id": "v2-c11",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "795f554697a547d7a4b6cb810ebb5d53673fe5781c613f95600b0f0020aed2f4",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "9596aeb369d09276eeea04cced84afc177d429678552640517a9ab02b28551f0",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c12 — class_level

For dictionary-labeled dexes receiving token events, report owner, token contract, total events and invalid raw-value cast count; keep every observed owner-token pair and sort by owner then token address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "dex_inbound_uncastable_raw_values"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:dex_inbound_uncastable_raw_values",
  "id": "v2-c12",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `dex_inbound_uncastable_raw_values`. Property focus: `None`.

```sql
SELECT to_owner AS owner, token_address, COUNT(*) AS events,
    COUNTIF(NOT value_cast_valid) AS invalid_values FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_category='dex'
    GROUP BY owner, token_address ORDER BY owner, token_address
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "dex",
      "concept_class": "DEXProtocol",
      "mention": {
        "end": 28,
        "start": 23,
        "text": "dexes"
      },
      "owners": [
        "Curve DEX",
        "PancakeSwap AMM",
        "Uniswap V2",
        "Uniswap V3",
        "Uniswap V4"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c12",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "to"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "30f93cddf51280d75c5c7388babcc23f8db5ffd816fd17603ce511dd1af12b68",
  "schema": {
    "columns": [
      {
        "column": "to_category",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "value_cast_valid",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "4441f0e281b2c2caf38a1d019a76510b5f07128d099d6e888627fbc047a8eec5"
}
```

Lý do tác giả: Zero invalid values are retained; absence of errors is not absence of events.

Sample: 1702 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "Curve DEX"
    ],
    [
      "string",
      "0x00000000efe302beaa2b3e6e1b18d08d69a9012a"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "0"
    ]
  ],
  [
    [
      "string",
      "Curve DEX"
    ],
    [
      "string",
      "0x0043d16c636b43db2db46df6bb3d47051041be3f"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "0"
    ]
  ],
  [
    [
      "string",
      "Curve DEX"
    ],
    [
      "string",
      "0x0100546f2cd4c9d97f798ffc9755e47865ff7ee6"
    ],
    [
      "number",
      "3"
    ],
    [
      "number",
      "0"
    ]
  ],
  [
    [
      "string",
      "Curve DEX"
    ],
    [
      "string",
      "0x01791f726b4103694969820be083196cc7c045ff"
    ],
    [
      "number",
      "3"
    ],
    [
      "number",
      "0"
    ]
  ],
  [
    [
      "string",
      "Curve DEX"
    ],
    [
      "string",
      "0x01dc18a9cb8ce867da857c6ed028bed16fc520e3"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "0"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "93e2df73d1aa5063f291877198faaafc55389c5234f878ddceac6d905ab22dad",
  "case_sha256": "4cb07bd230c93dd6afdf26d9f742b84821b8e25487726150fe48f6cec52d4664",
  "id": "v2-c12",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "30f93cddf51280d75c5c7388babcc23f8db5ffd816fd17603ce511dd1af12b68",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "4441f0e281b2c2caf38a1d019a76510b5f07128d099d6e888627fbc047a8eec5",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c13 — class_level

For each dictionary-labeled privacy mixers owner receiving token events, return total events, positive valid raw-value events and distinct token count; order by owner. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "mixer_inbound_nonzero_raw_profile"
  ],
  "difficulty": "medium",
  "empty_reason": "The labeled MixerAccount class has no incoming token events in this sample. Membership remains the full pinned dictionary set; class coverage and the empty answer require full-snapshot review in T09B.",
  "family_id": "t09a:mixer_inbound_nonzero_raw_profile",
  "id": "v2-c13",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `mixer_inbound_nonzero_raw_profile`. Property focus: `None`.

```sql
SELECT to_owner AS owner, COUNT(*) AS events,
    COUNTIF(value_bignumeric>0) AS positive_values, COUNT(DISTINCT token_address) AS tokens
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_category='mixer' GROUP BY owner ORDER BY owner
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "mixer",
      "concept_class": "MixerAccount",
      "mention": {
        "end": 42,
        "start": 28,
        "text": "privacy mixers"
      },
      "owners": [
        "Tornado Cash"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c13",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "to"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "9e30254786107f80c79f2f7bc21a2cb6e9edaeae104245dfa73bd63d38e3d8aa",
  "schema": {
    "columns": [
      {
        "column": "to_category",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "value_bignumeric",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "822f53104269e3d1c4d67ef3a017da5e34b83d302d065f20b829a82cde4d1098"
}
```

Lý do tác giả: Class-level request is distinct from the singular service alias 'the mixer'.

Sample: 0 rows; empty=True; zero/NULL aggregate=False; error=None.

Giải thích rỗng: The labeled MixerAccount class has no incoming token events in this sample. Membership remains the full pinned dictionary set; class coverage and the empty answer require full-snapshot review in T09B.

Preview (giá trị có type tag):

```json
[]
```

Review binding:

```json
{
  "annotation_sha256": "6ad821630a720121c3771afd2ecb5702b3978b5ef3da297f9d58e4aeeafb8ecb",
  "case_sha256": "73de245eebe3d355c13f4f1d69cdbad33aba2ae7ed76d05067ea7e58bffa1f11",
  "id": "v2-c13",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "9e30254786107f80c79f2f7bc21a2cb6e9edaeae104245dfa73bd63d38e3d8aa",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "822f53104269e3d1c4d67ef3a017da5e34b83d302d065f20b829a82cde4d1098",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c14 — class_level

For token events sent by dictionary-labeled lending owners to dictionary-labeled exchanges, return ordered owner pairs, event count and distinct token count; sort by sender owner then recipient owner. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "lending_to_exchange_token_owner_flows"
  ],
  "difficulty": "hard",
  "empty_reason": "No sampled token event satisfies both labeled lending sender and labeled exchange recipient predicates. Neither class membership is pruned to observed rows. Recheck the ordered class-pair query on the full snapshot in T09B.",
  "family_id": "t09a:lending_to_exchange_token_owner_flows",
  "id": "v2-c14",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `lending_to_exchange_token_owner_flows`. Property focus: `None`.

```sql
SELECT from_owner, to_owner, COUNT(*) AS events, COUNT(DISTINCT token_address) AS tokens
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_category='lending' AND to_category='exchange'
    GROUP BY from_owner, to_owner ORDER BY from_owner, to_owner
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "lending",
      "concept_class": "LendingProtocol",
      "mention": {
        "end": 51,
        "start": 44,
        "text": "lending"
      },
      "owners": [
        "Concrete",
        "Gauntlet",
        "Lista Lending",
        "Sentora",
        "Veda"
      ]
    },
    {
      "category": "exchange",
      "concept_class": "ExchangeAccount",
      "mention": {
        "end": 90,
        "start": 81,
        "text": "exchanges"
      },
      "owners": [
        "Binance",
        "Bitfinex",
        "Bitget",
        "Bitkub",
        "Bitmex",
        "Bitrue",
        "Bitstamp",
        "Bitunix",
        "Bitvavo",
        "Bybit",
        "CoinEx",
        "Crypto-com",
        "Deribit",
        "Gate.io",
        "Gemini",
        "HTX",
        "HashKey Exchange",
        "Indodax",
        "Korbit",
        "KuCoin",
        "MEXC",
        "Nexo",
        "OKX",
        "OSL HK",
        "Phemex",
        "Poloniex",
        "Robinhood",
        "SwissBorg",
        "VALR",
        "WEEX"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c14",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      },
      {
        "target": "class:1",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "from"
      },
      {
        "target": "class:1",
        "value": "to"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "01f9395c19ee8b2b1d9014cad883cee412af835655902d6d37fa0d6c98152883",
  "schema": {
    "columns": [
      {
        "column": "from_category",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "from_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_category",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "1e41bffff540f13d99cf99a1aa7f1bbaab9d710d84a61cdb0c160c33fba287a1"
}
```

Lý do tác giả: Two distinct class mentions and directional targets; no token-owner join substitution.

Sample: 0 rows; empty=True; zero/NULL aggregate=False; error=None.

Giải thích rỗng: No sampled token event satisfies both labeled lending sender and labeled exchange recipient predicates. Neither class membership is pruned to observed rows. Recheck the ordered class-pair query on the full snapshot in T09B.

Preview (giá trị có type tag):

```json
[]
```

Review binding:

```json
{
  "annotation_sha256": "db136b4636c167ed87510d961e3ad13e7b71fa67e932c2f4e9a2af5ca325b835",
  "case_sha256": "4a18f96752ba5b2e95e76bf2205bbd8b114ec9326c2133487fc1f4daaa38b331",
  "id": "v2-c14",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "01f9395c19ee8b2b1d9014cad883cee412af835655902d6d37fa0d6c98152883",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "1e41bffff540f13d99cf99a1aa7f1bbaab9d710d84a61cdb0c160c33fba287a1",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c15 — class_level

For outer transactions from dictionary-labeled exchanges to dictionary-labeled bridge owners, return sender owner, recipient owner, total rows and successful rows; sort by the two owner names. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "exchange_to_bridge_outer_outcomes"
  ],
  "difficulty": "hard",
  "empty_reason": null,
  "family_id": "t09a:exchange_to_bridge_outer_outcomes",
  "id": "v2-c15",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `exchange_to_bridge_outer_outcomes`. Property focus: `None`.

```sql
SELECT from_owner, to_owner, COUNT(*) AS total, COUNTIF(receipt_status=1) AS succeeded
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_category='exchange' AND to_category='bridge'
    GROUP BY from_owner, to_owner ORDER BY from_owner, to_owner
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "exchange",
      "concept_class": "ExchangeAccount",
      "mention": {
        "end": 56,
        "start": 47,
        "text": "exchanges"
      },
      "owners": [
        "Binance",
        "Bitfinex",
        "Bitget",
        "Bitkub",
        "Bitmex",
        "Bitrue",
        "Bitstamp",
        "Bitunix",
        "Bitvavo",
        "Bybit",
        "CoinEx",
        "Crypto-com",
        "Deribit",
        "Gate.io",
        "Gemini",
        "HTX",
        "HashKey Exchange",
        "Indodax",
        "Korbit",
        "KuCoin",
        "MEXC",
        "Nexo",
        "OKX",
        "OSL HK",
        "Phemex",
        "Poloniex",
        "Robinhood",
        "SwissBorg",
        "VALR",
        "WEEX"
      ]
    },
    {
      "category": "bridge",
      "concept_class": "BridgeProtocol",
      "mention": {
        "end": 85,
        "start": 79,
        "text": "bridge"
      },
      "owners": [
        "Aster Bridge",
        "CCIP",
        "Merlins Seal",
        "Optimism Bridge",
        "USDT0"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c15",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      },
      {
        "target": "class:1",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "from"
      },
      {
        "target": "class:1",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "a48b0a1af8a9eaf1665aa8b2e61579bc12a66e1a691677791032ce9689cde2e6",
  "schema": {
    "columns": [
      {
        "column": "from_category",
        "relation": "labeled_transactions"
      },
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "receipt_status",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_category",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "5e4ed2d57104dc5d0771d603e8aff2004cf915c61ea7020e64690985a45cbe9e"
}
```

Lý do tác giả: Two endpoint class predicates; outer calls, not inferred cross-chain settlement.

Sample: 2 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "Bitfinex"
    ],
    [
      "string",
      "USDT0"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "2"
    ]
  ],
  [
    [
      "string",
      "Korbit"
    ],
    [
      "string",
      "Optimism Bridge"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "2"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "0f98590dcad12b7d93b2434ef187e9cfa0a598a429b86539223bb41598f758be",
  "case_sha256": "97aa4cabd9ab3b8d8be927593df9ddd8631e547196d69677a982303cf1886c89",
  "id": "v2-c15",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "a48b0a1af8a9eaf1665aa8b2e61579bc12a66e1a691677791032ce9689cde2e6",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "5e4ed2d57104dc5d0771d603e8aff2004cf915c61ea7020e64690985a45cbe9e",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c16 — class_level

For dictionary-labeled decentralized exchange recipients, summarize outer calls using more than 100000 receipt gas units: return owner, call count, average receipt gas and average gas limit, sorted by owner. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "dex_high_gas_call_profile"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:dex_high_gas_call_profile",
  "id": "v2-c16",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `dex_high_gas_call_profile`. Property focus: `None`.

```sql
SELECT to_owner AS owner, COUNT(*) AS calls, AVG(receipt_gas_used) AS average_gas,
    AVG(gas_limit) AS average_limit FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE to_category='dex' AND receipt_gas_used>100000 GROUP BY owner ORDER BY owner
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "dex",
      "concept_class": "DEXProtocol",
      "mention": {
        "end": 45,
        "start": 23,
        "text": "decentralized exchange"
      },
      "owners": [
        "Curve DEX",
        "PancakeSwap AMM",
        "Uniswap V2",
        "Uniswap V3",
        "Uniswap V4"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c16",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "bd141d75266ddc01939fa03fdb6a4470cc44475bfab555d57df75e0a2f38e269",
  "schema": {
    "columns": [
      {
        "column": "gas_limit",
        "relation": "labeled_transactions"
      },
      {
        "column": "receipt_gas_used",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_category",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "25321f7059759f7a9ed083e3fe7b5ecd66f0b3d4922b2e0451417539eaa999a4"
}
```

Lý do tác giả: Strict gas threshold applies to actual receipt gas, not the declared gas limit.

Sample: 5 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "Curve DEX"
    ],
    [
      "number",
      "197"
    ],
    [
      "number",
      "2266579.492385787"
    ],
    [
      "number",
      "3362072.614213198"
    ]
  ],
  [
    [
      "string",
      "PancakeSwap AMM"
    ],
    [
      "number",
      "4"
    ],
    [
      "number",
      "2507604"
    ],
    [
      "number",
      "2528673"
    ]
  ],
  [
    [
      "string",
      "Uniswap V2"
    ],
    [
      "number",
      "4455"
    ],
    [
      "number",
      "194016.6179573513"
    ],
    [
      "number",
      "581693.3456790124"
    ]
  ],
  [
    [
      "string",
      "Uniswap V3"
    ],
    [
      "number",
      "2225"
    ],
    [
      "number",
      "329539.5366292135"
    ],
    [
      "number",
      "569381.8026966292"
    ]
  ],
  [
    [
      "string",
      "Uniswap V4"
    ],
    [
      "number",
      "680"
    ],
    [
      "number",
      "259714.725"
    ],
    [
      "number",
      "411523.3161764706"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "4138ea1062095e428ee72634e5e55d647fac649b42abbc1ffb47983202dab9e2",
  "case_sha256": "4d796fee83144c66ea6e6dbd997f6ba0ae93ed7db77a8e0f4d5ef93d076a6165",
  "id": "v2-c16",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "bd141d75266ddc01939fa03fdb6a4470cc44475bfab555d57df75e0a2f38e269",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "25321f7059759f7a9ed083e3fe7b5ecd66f0b3d4922b2e0451417539eaa999a4",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c17 — class_level

For dictionary-labeled exchange recipients, count outer transactions with no matching token event, per owner; return owner and count alphabetically. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "exchange_inbound_without_token_events"
  ],
  "difficulty": "hard",
  "empty_reason": null,
  "family_id": "t09a:exchange_inbound_without_token_events",
  "id": "v2-c17",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `exchange_inbound_without_token_events`. Property focus: `None`.

```sql
SELECT t.to_owner AS owner, COUNT(*) AS transactions FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') t
    WHERE t.to_category='exchange' AND NOT EXISTS (SELECT 1 FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-07-01') e
    WHERE e.transaction_hash=t.transaction_hash AND e.block_number=t.block_number
    AND e.block_hash=t.block_hash) GROUP BY owner ORDER BY owner
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "exchange",
      "concept_class": "ExchangeAccount",
      "mention": {
        "end": 31,
        "start": 23,
        "text": "exchange"
      },
      "owners": [
        "Binance",
        "Bitfinex",
        "Bitget",
        "Bitkub",
        "Bitmex",
        "Bitrue",
        "Bitstamp",
        "Bitunix",
        "Bitvavo",
        "Bybit",
        "CoinEx",
        "Crypto-com",
        "Deribit",
        "Gate.io",
        "Gemini",
        "HTX",
        "HashKey Exchange",
        "Indodax",
        "Korbit",
        "KuCoin",
        "MEXC",
        "Nexo",
        "OKX",
        "OSL HK",
        "Phemex",
        "Poloniex",
        "Robinhood",
        "SwissBorg",
        "VALR",
        "WEEX"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c17",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "to"
      }
    ],
    "fact": "transaction_token_transfer_join"
  },
  "question_sha256": "ba5fa9d85f0d1dde17d6f32471d521508d0e90dd969be9f713f378b38b5a242e",
  "schema": {
    "columns": [
      {
        "column": "block_hash",
        "relation": "labeled_transactions"
      },
      {
        "column": "block_number",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_category",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "transaction_hash",
        "relation": "labeled_transactions"
      },
      {
        "column": "block_hash",
        "relation": "token_transfer_facts"
      },
      {
        "column": "block_number",
        "relation": "token_transfer_facts"
      },
      {
        "column": "transaction_hash",
        "relation": "token_transfer_facts"
      }
    ],
    "relations": [
      "labeled_transactions",
      "token_transfer_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "deee9331737fcf9cfe4089a14fe4f07bfb22cd5c10276d4e3490f820ce628f32"
}
```

Lý do tác giả: Outer-row anti-join; activity is not counted in token-event rows.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "Binance"
    ],
    [
      "number",
      "3927"
    ]
  ],
  [
    [
      "string",
      "Bitfinex"
    ],
    [
      "number",
      "650"
    ]
  ],
  [
    [
      "string",
      "Bitget"
    ],
    [
      "number",
      "35628"
    ]
  ],
  [
    [
      "string",
      "Bitkub"
    ],
    [
      "number",
      "30"
    ]
  ],
  [
    [
      "string",
      "Bitmex"
    ],
    [
      "number",
      "170"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "3d1b979f21e7bc0a70d3224908a12607508f91f36711e1e2400f6bdafbe5a31b",
  "case_sha256": "c347fc94968e04e28a870f3a7ed0841cf016eac108d2fdbccf18c90d9a6c5a9a",
  "id": "v2-c17",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "ba5fa9d85f0d1dde17d6f32471d521508d0e90dd969be9f713f378b38b5a242e",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "deee9331737fcf9cfe4089a14fe4f07bfb22cd5c10276d4e3490f820ce628f32",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c18 — class_level

For each dictionary-labeled liquid staking recipient owner with outer transactions, return count and the number of distinct UTC hours of day with activity; sort by owner. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "staking_outer_active_hour_breadth"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:staking_outer_active_hour_breadth",
  "id": "v2-c18",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `staking_outer_active_hour_breadth`. Property focus: `None`.

```sql
SELECT to_owner AS owner, COUNT(*) AS calls,
    COUNT(DISTINCT EXTRACT(HOUR FROM block_timestamp AT TIME ZONE 'UTC')) AS hours
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_category='staking' GROUP BY owner ORDER BY owner
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "staking",
      "concept_class": "StakingAccount",
      "mention": {
        "end": 42,
        "start": 28,
        "text": "liquid staking"
      },
      "owners": [
        "Hastra"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c18",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "81aa1bdc13531a6e11f4158b217edca3b3d9eb4e010fe0b821af3072005ecd72",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_category",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "25d3aace98c5fb0c6272bfe9e9c9c302a546c8db6c8a0ae777907ae2579dbd9a"
}
```

Lý do tác giả: Known staking class only; distinct hour-of-day values range from zero through 23.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "Hastra"
    ],
    [
      "number",
      "987"
    ],
    [
      "number",
      "24"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "1e24bf26bc7adaa7ca16025b8a83926e4a21dda766277a31783793d201cbd405",
  "case_sha256": "69c5b6ecb18c960d959e32af8909f82c884bda92b83e8e0fc70b2d776ff2bf8c",
  "id": "v2-c18",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "81aa1bdc13531a6e11f4158b217edca3b3d9eb4e010fe0b821af3072005ecd72",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "25d3aace98c5fb0c6272bfe9e9c9c302a546c8db6c8a0ae777907ae2579dbd9a",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c19 — class_level

For dictionary-labeled money market owners sending failed outer transactions, return owner, failed count and total receipt gas used times gas price in wei; sort by total descending then owner. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "lending_failed_outbound_gas_expense"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:lending_failed_outbound_gas_expense",
  "id": "v2-c19",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `lending_failed_outbound_gas_expense`. Property focus: `None`.

```sql
SELECT from_owner AS owner, COUNT(*) AS failed,
    SUM(CAST(receipt_gas_used AS NUMERIC)*gas_price_wei) AS gas_expense FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE from_category='lending' AND receipt_status=0 GROUP BY owner
    ORDER BY gas_expense DESC, owner
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "lending",
      "concept_class": "LendingProtocol",
      "mention": {
        "end": 35,
        "start": 23,
        "text": "money market"
      },
      "owners": [
        "Concrete",
        "Gauntlet",
        "Lista Lending",
        "Sentora",
        "Veda"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c19",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "class:0",
        "value": "from"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "1358bc71710dd4a5af592edc0579344e97ce2046f89de24176fbb3b3d789a479",
  "schema": {
    "columns": [
      {
        "column": "from_category",
        "relation": "labeled_transactions"
      },
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "gas_price_wei",
        "relation": "labeled_transactions"
      },
      {
        "column": "receipt_gas_used",
        "relation": "labeled_transactions"
      },
      {
        "column": "receipt_status",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "092c50d6cee4d8795ae46b2193405b01604f6ac152a80779a7db22611fe9b9f3"
}
```

Lý do tác giả: Contract-only owner sets may not originate outer transactions; an empty result is plausible.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "Gauntlet"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "53264292156875"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "0065bf8982f6b18a3e2e4c2cc12a17f1d47058f73279792d92e6cb5076e5356a",
  "case_sha256": "d4510d5857989d3d5d9426df66dc311428017a86873680b3de21f683e4ba52bb",
  "id": "v2-c19",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "1358bc71710dd4a5af592edc0579344e97ce2046f89de24176fbb3b3d789a479",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "092c50d6cee4d8795ae46b2193405b01604f6ac152a80779a7db22611fe9b9f3",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-c20 — class_level

In the pinned dictionary, summarize labeled DEX endpoint inventory by owner and address role, returning distinct address count; order by owner and role. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "dex_endpoint_inventory_by_role"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:dex_endpoint_inventory_by_role",
  "id": "v2-c20",
  "primary_group": "class_level",
  "property_focus": null,
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "class_level"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `dex_endpoint_inventory_by_role`. Property focus: `None`.

```sql
SELECT owner, address_role, COUNT(DISTINCT address) AS addresses FROM `nl2sparql-thesis.nl2sparql_analytics.entity_labels_v1`
    WHERE category='dex' GROUP BY owner, address_role ORDER BY owner, address_role
```

Annotation trực tiếp:

```json
{
  "classes": [
    {
      "category": "dex",
      "concept_class": "DEXProtocol",
      "mention": {
        "end": 47,
        "start": 44,
        "text": "DEX"
      },
      "owners": [
        "Curve DEX",
        "PancakeSwap AMM",
        "Uniswap V2",
        "Uniswap V3",
        "Uniswap V4"
      ]
    }
  ],
  "entities": [],
  "id": "v2-c20",
  "properties": {
    "address_role": [
      {
        "target": "class:0",
        "value": "endpoint"
      }
    ],
    "direction": [],
    "fact": null
  },
  "question_sha256": "e5668da2f9433f9093532affb845beb4d636a907b5914461d9f2a1e30350a05d",
  "schema": {
    "columns": [
      {
        "column": "address",
        "relation": "entity_labels_v1"
      },
      {
        "column": "address_role",
        "relation": "entity_labels_v1"
      },
      {
        "column": "category",
        "relation": "entity_labels_v1"
      },
      {
        "column": "owner",
        "relation": "entity_labels_v1"
      }
    ],
    "relations": [
      "entity_labels_v1"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "0716420f3b4458a5e56a9aae6e1dd5b66255f98ebe46ce6e0fb78a7f9cf7742b"
}
```

Lý do tác giả: Dictionary inventory, no transaction/event fact and no activity direction.

Sample: 18 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "Curve DEX"
    ],
    [
      "string",
      "crypto_factory"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "Curve DEX"
    ],
    [
      "string",
      "factory"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "Curve DEX"
    ],
    [
      "string",
      "router"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "Curve DEX"
    ],
    [
      "string",
      "stable_ng_factory"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "Curve DEX"
    ],
    [
      "string",
      "tricrypto_factory"
    ],
    [
      "number",
      "1"
    ]
  ]
]
```

Review binding:

```json
{
  "annotation_sha256": "0fb000ddd3391a42df2782c1b1aba8ffdba83d7fa4aaeb825aeb3fc687afa365",
  "case_sha256": "5c05c79e7484da6143df618fa71d56275c388ffe6daa7955f351cfa3c44a8004",
  "id": "v2-c20",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "e5668da2f9433f9093532affb845beb4d636a907b5914461d9f2a1e30350a05d",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "0716420f3b4458a5e56a9aae6e1dd5b66255f98ebe46ce6e0fb78a7f9cf7742b",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p01 — ambiguous_property

For positive-value outer transactions received by Binance, show each active date, incoming row count and distinct sender count; order by date. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "direction_binance_positive_inbound_senders"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:direction_binance_positive_inbound_senders",
  "id": "v2-p01",
  "primary_group": "ambiguous_property",
  "property_focus": "direction",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `direction_binance_positive_inbound_senders`. Property focus: `direction`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS incoming,
COUNT(DISTINCT from_address) AS senders FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01')
WHERE to_owner='Binance' AND value_wei>0 GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x030e37ddd7df1b43db172b23916d523f1599c6cb",
        "0x110daa3f3fac2a54bb508ac94f31f9df77057b29",
        "0x150aace136535a374f05b5ee209b6a61396db1c0",
        "0x18e226459ccf0eec276514a4fd3b226d8961e4d1",
        "0x1b46970cfe6a271e884f636663c257a5a571fb2c",
        "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        "0x22132139bf7f3921b1cadeab931f4fbf7bf2bc9e",
        "0x26bff98f6f37c8d560684eaf2afd1149bf76633e",
        "0x28c6c06298d514db089934071355e5743bf21d60",
        "0x308a2a0712570daeea77c8ba9c27a32cdc4000d4",
        "0x32e11a20337ebc79abd0eeab2d91bafbd9591149",
        "0x38aaef3782910bdd9ea3566c839788af6ff9b200",
        "0x42a93a9f5cfda54716c414b6eaf07cf512f46ead",
        "0x43684d03d81d3a4c70da68febdd61029d426f042",
        "0x4976a4a02f38326660d17bf34b431dc6e2eb2327",
        "0x4aec0e98fc1fb55b9cc2faaa7a81acca42cb4e96",
        "0x4ed6cf63bd9c009d247ee51224fc1c7041f517f1",
        "0x4fdfe365436b5273a42f135c6a6244a20404271e",
        "0x56eddb7aa87536c09ccc2793473599fd21a8b17f",
        "0x5a1e5b56aa33c056ed7bb93b88b1774a456f6694",
        "0x5a52e96bacdabb82fd05763e25335261b270efcb",
        "0x6357e4bdaff733dfe8f50d12d07c03b3bed0884b",
        "0x6454ac71ca260f99cca99a3f4241dfda20cfa965",
        "0x756b86fd69914db92229c07c7393d7d9948fed33",
        "0x835678a611b28684005a5e2233695fb6cbbb0007",
        "0x8498fc7280668874a5da79e87ca0896f4f0d1196",
        "0x86523c87c8ec98c7539e2c58cd813ee9d1a08d96",
        "0x87433fec6f8d9df13d1e17c4b11364ecd2e93a51",
        "0x8a6f8404c9ea4c33502a3f6a4bf8e41ef5ca10ea",
        "0x8e609ac80f4324e499a6efd24f221a2caa868224",
        "0x9696f59e4d72e237be84ffd425dcad154bf96976",
        "0x98adef6f2ac8572ec48965509d69a8dd5e8bba9d",
        "0xa345dcb63f984ed1c6d1a8901e0cdbd13b2b4d19",
        "0xa64b436964e7415c0e70b9989a53e1fb9a90e726",
        "0xa7c0d36c4698981fab42a7d8c783674c6fe2592d",
        "0xa9fc92f6faf9f103fc81d17de3e8daadc888afff",
        "0xad354cfbaa4a8572dd6df021514a3931a8329ef5",
        "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",
        "0xc47b3342df38d747033b6041f54e4e5e300c8d18",
        "0xc8daf809c7d7c27dd62d006196d8901ba57e5eae",
        "0xd27b39cb25fed854f9fce3a4e451f96e62089e48",
        "0xdbeb6c856ef5a167f5e1acb9dff65adb33207d8b",
        "0xdbf28a152d79b2b98eecd229b412ee98d21ec3bc",
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
        "0xe1940f578743367f38d3f25c2d2d32d6636929b6",
        "0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055",
        "0xf16924b866e58ac916ba933d1f1034bcbbb1958c",
        "0xf1f8cb7633d3ca3fd06c084d18ca5491a85ae9b4",
        "0xf977814e90da44bfa03b6295a0616a897441acec",
        "0xfc8059c2fb22005ede8a86d388e3d0f536a4dd44"
      ],
      "mention": {
        "end": 57,
        "start": 50,
        "text": "Binance"
      },
      "owner": "Binance"
    }
  ],
  "id": "v2-p01",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "21d4c215346cf8f3862579f3290db66c7d760866c417dcedc86b28166ffc1ebc",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "from_address",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "value_wei",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "cfcb7801f3b8820fe0579ff9c389acdc76d5d336a25c20269969628ff5415caa"
}
```

Lý do tác giả: Received selects outer to_address; declared positive value does not imply receipt success.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "26"
    ],
    [
      "number",
      "23"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "37"
    ],
    [
      "number",
      "28"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "30"
    ],
    [
      "number",
      "25"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "31"
    ],
    [
      "number",
      "31"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "37"
    ],
    [
      "number",
      "32"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Wrongly selects the owner as outer sender.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS incoming,
COUNT(DISTINCT from_address) AS senders FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01')
WHERE from_owner='Binance' AND value_wei>0 GROUP BY day ORDER BY day
```

Review binding:

```json
{
  "annotation_sha256": "f0bf7108491825321a8d20300db59df4725bf50b161654967c39599701e0e96e",
  "case_sha256": "9d09efaa059c7f141d56f74f1cec8da0b2a496a9681578fb93619aecea348f9f",
  "id": "v2-p01",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "21d4c215346cf8f3862579f3290db66c7d760866c417dcedc86b28166ffc1ebc",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "cfcb7801f3b8820fe0579ff9c389acdc76d5d336a25c20269969628ff5415caa",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p02 — ambiguous_property

For outer transactions sent by OKX, give each transaction type's failed, successful and total counts, sorted by type. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "direction_okx_outbound_outcomes_by_type"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:direction_okx_outbound_outcomes_by_type",
  "id": "v2-p02",
  "primary_group": "ambiguous_property",
  "property_focus": "direction",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `direction_okx_outbound_outcomes_by_type`. Property focus: `direction`.

```sql
SELECT transaction_type, COUNTIF(receipt_status=0) AS failed,
COUNTIF(receipt_status=1) AS succeeded, COUNT(*) AS total FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01')
WHERE from_owner='OKX' GROUP BY transaction_type ORDER BY transaction_type
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0003b5aa5e30e97fcc596bb5d0f3a75255e08d4e",
        "0x01c2a9e7eeaee29b03708692ba5e1515036451e8",
        "0x01f66697aec1e7de7773115243247952245fd3a4",
        "0x01f7cea182239f9e9caf0f1ce0744bcb23c20585",
        "0x03ae1a796dfe0400439211133d065bda774b9d3e",
        "0x03d0aad7c6a0b36f47d852a28ff0fb7bc9ae46b6",
        "0x0475dd0e4194422a8cac486dc69173f535d0baf4",
        "0x0607c628054a7db3d36eed7c4a408eda8260de09",
        "0x06324bad3913cb69cb5e748a3ed72f9d692324bb",
        "0x06959153b974d0d5fdfd87d561db6d8d4fa0bb0b",
        "0x06d3a30cbb00660b85a30988d197b1c282c6dcb6",
        "0x073f564419b625a45d8aea3bb0de4d5647113ad7",
        "0x0750b999e493112c88cb226a13a2a67419f06ad6",
        "0x0799ddbf6f14db566ca4df4ff0575c4cc1e7749c",
        "0x08af9c4767236221c55069dd523e2f7a0013e898",
        "0x08f619716db7c6245401b543e59acac1d25cb483",
        "0x0938c63109801ee4243a487ab84dffa2bba4589e",
        "0x0a133528245eaf5bab72dc05a9dd8e0ea4b982f9",
        "0x0c48511102453352fe570370672cd556bf0e63f9",
        "0x0ff9491b236a36cc183823e39d7532194143fdb1",
        "0x11b113383ce08e84001dc614f141ae4c27221e31",
        "0x1278678b5b17eba14b313d287659ae9f3aa7c087",
        "0x12a8bdc0470ab29a229d828526641b7d1f170fcf",
        "0x16b5016803bcb4915701efc0a3b471bd4c168d93",
        "0x173810f8ca9c4c631aeb1d6c36d007f054fee980",
        "0x17e91b98988937cb59dc163b0b11781f9785591a",
        "0x1811068091a2459ee38a8dde52cce5b2acfc1b61",
        "0x19abcd6b8516d2b4d9aa3bbf700b38a30dc154fc",
        "0x1a557020c52f9d2495b2c12eb137ee7b5d467a4f",
        "0x1c628a9c66ff63454a4526a4f2b8af250da8d086",
        "0x1dfc6bec8499fcb5e3151c7c6d27feb9d7eae1d4",
        "0x1e43e7a911b1b0229ea7d64e11ae260c482a0870",
        "0x221ac9e1920932e95adf0c941f3524157f4bda4f",
        "0x25236e080106b5387df201fbbd9a6b870917676d",
        "0x26704ccfcd45b5780dcd58d38b12f5e0cdb481a0",
        "0x267b51c97632225da2b2e49aebe59eef1af32653",
        "0x276cdba3a39abf9cedba0f1948312c0681e6d5fd",
        "0x297611b7accb7f24032c27b3a496465624c7ef50",
        "0x2c8fbb630289363ac80705a1a61273f76fd5a161",
        "0x30c1dcde81e5dbf3121d0408abc7908980e83ae2",
        "0x313eb1c5e1970eb5ceef6aebad66b07c7338d369",
        "0x32dc16f4631a27b042a974d05c1ccf8a303e8199",
        "0x3425519651e4c42833633fe5c0e24ed89c1023a3",
        "0x3b9694465483cbb677b700a91c26f487193a6e03",
        "0x3b98b9e9cb75c1cb1729aab8f09ced2936505e4f",
        "0x3bb00393bfa5e76b7f31e93948f7d3cef12942ad",
        "0x3c5883c650d600bd543a9b5c8d9a3a6f5d16b8f4",
        "0x3d2335cac7b31411467ef03168c5869452fb7e86",
        "0x3d55ccb2a943d88d39dd2e62daf767c69fd0179f",
        "0x3e7d48c8ae2e50c2b9adedc8e276d3cc92b39458",
        "0x3f482c72a2b3e777746f5755cc0ff1323ea2ad16",
        "0x400d8280acf364f683e989462879fd8dd358067d",
        "0x4106a4be14867c70e52c51b9805514ae2e16de64",
        "0x42436286a9c8d63aafc2eebbca193064d68068f2",
        "0x42797deffe266a55fdc4c98d7d3885d7058cb3e5",
        "0x42cf18596ee08e877d532df1b7cf763059a7ea57",
        "0x445f16314284b43dfa1fd3cd77b9dea4a1bebd97",
        "0x45d9c02baed2d1670f7bad40fb5f657a05068d52",
        "0x45f329ff834a84fccea2319f91e1993540b22a2a",
        "0x461249076b88189f8ac9418de28b365859e46bfd",
        "0x47eb32dea1ab1436187939fa72d6d5ff884a87da",
        "0x48480aad203e8b030f82754b3c75869c9895c6bf",
        "0x48c4c83be7e3884ee5043a3abe5115eb020b5f4a",
        "0x4a11078a99b118bbfee78a5c187d98d264360433",
        "0x4bcbaf34862e6480329477917cf5cd7b9537a98d",
        "0x4d19c0a5357bc48be0017095d3c871d9afc3f21d",
        "0x4d619eb6db0b9b6184d9881c4828c0effff84eda",
        "0x4e2757e46103556f98d4d036d8efe18389b89f51",
        "0x5041ed759dd4afc3a72b8192c143f72f4724081a",
        "0x52738a51882f35d6b25a3fd0c86089ddbd206821",
        "0x52b311c52436789f3754bd199bf3886b8ccbab4c",
        "0x539c92186f7c6cc4cbf443f26ef84c595babbca1",
        "0x559432e18b281731c054cd703d4b49872be4ed53",
        "0x56fd42ecd77c88bdd959be54af10d1759b473dff",
        "0x593878f92dde464fc4e3b17cd7cc87117dca753c",
        "0x5a150733cb59bbdd5c7398a8fe7da7f97c8a213a",
        "0x5b27e98516fd2bd5001d4dfe3f5a2263f702f634",
        "0x5b873ffcad5dccdc61c1a53c391fb76cb316a841",
        "0x5c52cc7c96bde8594e5b77d5b76d042cb5fae5f2",
        "0x5ca38fb7cf2b587026a1650f0d2b0a13c41f5d0f",
        "0x5f5105b9a19e301208844263806df9b7212e655d",
        "0x5f8215ee653cb7225c741c7aa8591468d1f158b8",
        "0x608c27519c5e65a61cfc1d2c9e658e5c57a2e3d7",
        "0x611f7bf868a6212f871e89f7e44684045ddfb09d",
        "0x65a0947ba5175359bb457d3b34491edf4cbf7997",
        "0x65e891ec42fcaa19459fe6221163e1a3f8cf7ea6",
        "0x6667a4b7eff4a0b86781fb3b187622cd3c257f09",
        "0x66e6bdac6fae819f944901e3b6ecc9bfff61a706",
        "0x6709383e211ab08a6e3270532e756220400424a6",
        "0x68841a1806ff291314946eebd0cda8b348e73d6d",
        "0x68b5e9e083bfc28c33cfbf3f19d33e629015e907",
        "0x68e2ea1622aa67fb3a01a66d132daed8a48d1662",
        "0x69a722f0b5da3af02b4a205d6f0c285f4ed8f396",
        "0x6a4561ef7874a76b4bf0d3edca31dfcd51603414",
        "0x6b7ba57e1d43c2c975ba25139a04d193e64a11d0",
        "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
        "0x6d29fc1267b1691c0cd43a8d35b27135957ffea9",
        "0x6d8c32fcf2d95ff410ba492f6694f18cbee55ce1",
        "0x6dc1a070425f437ac08bb108f7093b177d7af3a6",
        "0x6ededbad1e864105fa2538ddfbf4e7214b9e6529",
        "0x6fb624b48d9299674022a23d92515e76ba880113",
        "0x6fd41d4a272247fd1104c710909a4af8bd38f522",
        "0x728d92a8023bfbe0d4f3fdd549ed3b4996a0eba9",
        "0x730df969955c0a2fa9e8f2484e9741a363afdbb3",
        "0x739768219c831ec1f747bf904f0e25c2d99c7dc1",
        "0x767a905b77b0a40801488c6af8b8b5992b43511c",
        "0x778e456fbfd14075f5ddbccf9be2d6a48e3b1ecb",
        "0x7926c83479e2708edfd83a39d62084693e192298",
        "0x793aa889e19a130ee4cb8b63c79aa3bdccc663cb",
        "0x7a91e803db0e58b6fecc4e42c86b366778475e3c",
        "0x7a93539c1bf9a96f87044925deb7a0849266213e",
        "0x7c7061221666e41b87ca5817cfa2fcac09b3d943",
        "0x7cfe28094f4531809992ed89060a61413116365d",
        "0x7d4a2c448fe5b07c62228140417b3565bbe1b86b",
        "0x7eb6c83ab7d8d9b8618c0ed973cbef71d1921ef2",
        "0x7f61dc44c15ca818f96c6fc40739e5aa732e240c",
        "0x7fe830ec109e112f549d6ee9d3e9540e7785997b",
        "0x7fea5b4568751533039179116e372e26b6b41b13",
        "0x80335e658ee73756bb8220bdb77f99e98322035f",
        "0x8167a1ebf00ff5886d1b5908419bb1159d8cf6a4",
        "0x83a32a54d31ee4f1f9dffad2a63a6d214e469ec3",
        "0x85dcd76d4fbd3aa0c85c27b9441222c19a14134b",
        "0x868dab0b8e21ec0a48b726a1ccf25826c78c6d7f",
        "0x86aee064cc073d0dc95ba86633067b2c615040bb",
        "0x8734bca44102bf8a663e1ba112308504606e1b08",
        "0x87d0d6c8cdd71a658ecf1566f13e4cbc562beaf9",
        "0x88c94d8e7d4203b185b3beb0a7b15a6b4f36b2a2",
        "0x89b2f6dafc9d46ce0ed7d7e45a4972d14f037a19",
        "0x8ad740adce08f2f3579884eac0a12e581304ac3b",
        "0x8c3cb9665833fd9f79eb14cba16d82bbab6f22d8",
        "0x8f1aae22d0b4335945950d0bbd0f3743d3fc6f22",
        "0x91d40e4818f4d4c57b4578d9eca6afc92ac8debe",
        "0x92ea7496eba5f001d620005f88f3e8e686e3d4ea",
        "0x932d7d2cbc06234919f34802a22a914282a00f87",
        "0x96fdc631f02207b72e5804428dee274cf2ac0bcd",
        "0x9723b6d608d4841eb4ab131687a5d4764eb30138",
        "0x98ec059dc3adfbdd63429454aeb0c990fba4a128",
        "0x9938ee74ba7a5c1abcd157272a18fcfc9ec9e8d5",
        "0x994d24172fcfafbb5fce0ac5392078fa1c025448",
        "0x9b645675e8d64759e5c36e30dcb766d8cec3d34f",
        "0x9ce5a8098270f07a0a56398febda76a8ee2858c4",
        "0x9d65bf1bce7a10814228f4d81d8cf99a6b0f44aa",
        "0x9db8b860692c41e709d48d089de64cf01e6e317e",
        "0x9e13bae2256f968d02fe0129a0f51788f4e2472f",
        "0x9e3bb2cd5a89fcc4b826230b144c4917881bea85",
        "0xa01533d5c66a4886d3bb39b156507d9de65653e6",
        "0xa2684f75740cfff46c29bae79a4ecc43043c003d",
        "0xa27cef8af2b6575903b676e5644657fae96f491f",
        "0xa68cfe488a785c8b38ce2db6c45cfe07cb620c2d",
        "0xa7efae728d2936e78bda97dc267687568dd593f3",
        "0xa9ac43f5b5e38155a288d1a01d2cbc4478e14573",
        "0xacf961ae22191f0d080497a3a3b427180f18ed67",
        "0xae0cbaba071d58efc278a815b2cb652286e192ff",
        "0xb072b7dc9521d97a3f12b04beb1e497f8875ec52",
        "0xb0a27099582833c0cb8c7a0565759ff145113d64",
        "0xb47a0ac7798d8308467b2b96ac632ed43c9cb6d7",
        "0xb4ec508adeb174610b4295e233a458b3475964f7",
        "0xb640e1e5a5f726a054cd518c968dfdac8c421ee5",
        "0xb8ede418d8116113efb7644a792e5d97aade6138",
        "0xb99cc7e10fe0acc68c50c7829f473d81e23249cc",
        "0xba0a39d37151fa4f938bec51cdae4675105760f4",
        "0xba7fd71d309bc0e96b64022fd8fea7299b256159",
        "0xba96a3f3d5e9f13a5f93c37001f946d42eb2e165",
        "0xbda23b750dd04f792ad365b5f2a6f1d8593796f2",
        "0xbe2ec156292587338d4e9f80f5439e6152d56fc5",
        "0xbf94f0ac752c739f623c463b5210a7fb2cbb420b",
        "0xbfbbfaccd1126a11b8f84c60b09859f80f3bd10f",
        "0xbfef5c888bb7a0a6b14b4c3ccc4364ea81aa573f",
        "0xc0d01a27fd89e6bbc68f43e94ade3dfca2c27674",
        "0xc18475f347cc757b3cc49025820248a5f27d97ce",
        "0xc275bf069df3e63184a1222359114b805b6cd2f5",
        "0xc5267f13b9b4ba7bb73bdd53a2a3c944733a2961",
        "0xc5451b523d5fffe1351337a221688a62806ad91a",
        "0xc5a93444cc4da6efb9e6fc6e5d3cb55a53b52396",
        "0xc6724cf116573eab588fb0d73dcdc16929493cea",
        "0xc68c17e6eec0fde3605c595c9b98de5c1a4cc3e4",
        "0xc708a1c712ba26dc618f972ad7a187f76c8596fd",
        "0xcab0c0a224bad992085430f87dc1855342763a88",
        "0xcb0963264231bb08b2f680ab3ed89a49c9641bb3",
        "0xcba38020cd7b6f51df6afaf507685add148f6ab6",
        "0xcbc767b519394a9e4682cc9a15dcd18c46a6045b",
        "0xcc5d36fb0126515cb7988bbeee8445f03c304b2a",
        "0xcd5bd47d3d1d8412b241ce9015c5032142948c12",
        "0xce9abe75d561f065f1c4adb188b260df9de32ca7",
        "0xd03e6a53a3298ba1cd9b0dbf525ad728f4f8ad6e",
        "0xd049e4ddf1133af3a7a27390b4c9018141df1a49",
        "0xd19d3341227967610b94e7aebe8c971d2d48f419",
        "0xd266529641eeffaa2b2a0bc99daa5b32ef241078",
        "0xd576392cb12b7749ba33f8d223f64e65ee32f03f",
        "0xd5f8c864f21824daf3a4b22d9c33693642ed7634",
        "0xd7764b4305bcca935e38a450e7956822113374b6",
        "0xd7f4a5613b38cb8c09229b7aed99803242fdf0a0",
        "0xd99d81949146b4c13a4a42c9a6addbbd2db932ad",
        "0xd9a3c9ba5aa4415a53b9190bcb00f14472790a70",
        "0xdad24044e36587d975d7b5bceb6467fac21e0c81",
        "0xdb0ed345cb52c2f2457918afa3eb4b682e264ad0",
        "0xdc3ce895714844b4775b6d06f0dae513542cee10",
        "0xdce83237fbf279c4522e7cac4b10428e2b8694da",
        "0xddf81e81ab956695600d8639356c045e5c8a8c94",
        "0xde01974fb4a98bafd7cbf8a06ecf6dcc94d7283f",
        "0xdeb6ad2a7820839464da79bac953ae6189215443",
        "0xe2effe5bd0617a5a2dc1ee579565911cef3a223b",
        "0xe3bb282457ce7b3be31f0441f3fc051b9fc6a9c3",
        "0xe404fe9b7b0d0e88e77731517202fb392f67cd74",
        "0xe6eea9812ccc5981ccf0ab333610c42c2d92d146",
        "0xe7b29ff45392876143c7b863d57fb2326afe0ff1",
        "0xe7c8fdd899ab06ac1023e8a3e867c5fa7e751450",
        "0xe9172daf64b05b26eb18f07ac8d6d723acb48f99",
        "0xe983845a04c681a295dd9ce1fa8c2c8505932da3",
        "0xea3b7dac6b96502a04c701d5e71b51912f70143f",
        "0xeaed6576334b003d1c5c4797d9c7bb025a20c038",
        "0xeb196a61f9a1e35bf5053b65aaa57c5541dcba86",
        "0xedc0a430dd32eb8cfcc3a344979f0e21bc48bf0d",
        "0xee1c6537e589a15a15f80961f5594c57bed936fb",
        "0xf02e3c0095f6de36c76364d4cc53eb06d1288fc1",
        "0xf418263a6468c80d3bcb71033c56aacf81b241ba",
        "0xf59869753f41db720127ceb8dbb8afaf89030de4",
        "0xf683b33e21e85ee6c0e25af2fff5b2b115f32617",
        "0xf7858da8a6617f7c6d0ff2bcafdb6d2eedf64840",
        "0xf7b17e0b2478ad21ac594e4b0954ece63d059064",
        "0xf7c63e75b90c60d7b343106a39658f8b3ca6e4d2",
        "0xf8b4256122369c48eb8c3d901875d62458a675e8",
        "0xfa13971666d0e6f2715d68eb44bb7964fc22b14b",
        "0xfad70cb84e104817a7e9345d25ed0d3048af2d2d",
        "0xfcb21730ac0cd487d8701dfed1170e023b57cf7a",
        "0xfe908731af54c56dfd63948f18ce5878a3b8a1ad"
      ],
      "mention": {
        "end": 34,
        "start": 31,
        "text": "OKX"
      },
      "owner": "OKX"
    }
  ],
  "id": "v2-p02",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "5d1ed18a007a7a8a0cdaa90d07481867b91709eeea80beaeaa29adee81805c6f",
  "schema": {
    "columns": [
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "receipt_status",
        "relation": "labeled_transactions"
      },
      {
        "column": "transaction_type",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "7aa76cfc1532ca752a405820cf70546900754610244d3996abd80e421a2e24c9"
}
```

Lý do tác giả: Sent selects outer from_address; unknown receipt statuses contribute to total.

Sample: 2 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "0"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "30"
    ],
    [
      "number",
      "30"
    ]
  ],
  [
    [
      "number",
      "2"
    ],
    [
      "number",
      "0"
    ],
    [
      "number",
      "59039"
    ],
    [
      "number",
      "59039"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Wrongly selects the owner as outer recipient.

```sql
SELECT transaction_type, COUNTIF(receipt_status=0) AS failed,
COUNTIF(receipt_status=1) AS succeeded, COUNT(*) AS total FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01')
WHERE to_owner='OKX' GROUP BY transaction_type ORDER BY transaction_type
```

Review binding:

```json
{
  "annotation_sha256": "87c723c46be249ddf4872fb836491fa106fd9e7cd43fe71213e28094dad2bc4f",
  "case_sha256": "d9518b50ac3485be7a05bd46c826173a6f1f65c5cad404a1c6989bf8d2081f4f",
  "id": "v2-p02",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "5d1ed18a007a7a8a0cdaa90d07481867b91709eeea80beaeaa29adee81805c6f",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "7aa76cfc1532ca752a405820cf70546900754610244d3996abd80e421a2e24c9",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p03 — ambiguous_property

For outer transactions involving Bitfinex as either sender or recipient, return row count and distinct active UTC date count; count each internal transaction once. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "direction_bitfinex_either_role_active_dates"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:direction_bitfinex_either_role_active_dates",
  "id": "v2-p03",
  "primary_group": "ambiguous_property",
  "property_focus": "direction",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `direction_bitfinex_either_role_active_dates`. Property focus: `direction`.

```sql
SELECT COUNT(*) AS involved, COUNT(DISTINCT DATE(block_timestamp)) AS active_dates
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_owner='Bitfinex' OR to_owner='Bitfinex'
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x742d35cc6634c0532925a3b844bc454e4438f44e",
        "0x77134cbc06cb00b66f4c7e623d5fdbf6777635ec",
        "0x876eabf441b2ee5b5b0554fd502a8e0600950cfa",
        "0xc61b9bb3a7a0767e3179713f3a5c7a9aedce193c"
      ],
      "mention": {
        "end": 41,
        "start": 33,
        "text": "Bitfinex"
      },
      "owner": "Bitfinex"
    }
  ],
  "id": "v2-p03",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "either"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "e6c8589628bd2cae22c25bcb03870589461430082a4d591e071c9c2d21efcd85",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "4bb5a47d6f13daf74478e393680534d3cb903c3a747f5da32947cd55f6443ba3"
}
```

Lý do tác giả: Either is a set union, not outgoing alone and not a sum of role counts.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "7990"
    ],
    [
      "number",
      "30"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Drops the sender half of either-role union.

```sql
SELECT COUNT(*) AS involved, COUNT(DISTINCT DATE(block_timestamp)) AS active_dates
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Bitfinex'
```

Review binding:

```json
{
  "annotation_sha256": "2232e2a73c9c0e0a83c02cedba7ec4d08b626c7b46ce7c1673891804862fc158",
  "case_sha256": "65b11b58ae456583483b88fbce2cc00b1fcfb9c4d3feb7bd396a9636e8a0b830",
  "id": "v2-p03",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "e6c8589628bd2cae22c25bcb03870589461430082a4d591e071c9c2d21efcd85",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "4bb5a47d6f13daf74478e393680534d3cb903c3a747f5da32947cd55f6443ba3",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p04 — ambiguous_property

For outer transactions sent from Binance to OKX, return receipt status, row count and sum of declared wei, ordered by status. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "direction_binance_to_okx_receipt_groups"
  ],
  "difficulty": "medium",
  "empty_reason": "No sampled outer transaction has Binance sender and OKX recipient; the reversed owner-pair contrast is also empty. The sample cannot discriminate this direction case. Retain the intended pair and require a full-snapshot witness in T09B.",
  "family_id": "t09a:direction_binance_to_okx_receipt_groups",
  "id": "v2-p04",
  "primary_group": "ambiguous_property",
  "property_focus": "direction",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `direction_binance_to_okx_receipt_groups`. Property focus: `direction`.

```sql
SELECT receipt_status, COUNT(*) AS transactions, SUM(value_wei) AS declared_wei
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_owner='Binance' AND to_owner='OKX'
GROUP BY receipt_status ORDER BY receipt_status
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x030e37ddd7df1b43db172b23916d523f1599c6cb",
        "0x110daa3f3fac2a54bb508ac94f31f9df77057b29",
        "0x150aace136535a374f05b5ee209b6a61396db1c0",
        "0x18e226459ccf0eec276514a4fd3b226d8961e4d1",
        "0x1b46970cfe6a271e884f636663c257a5a571fb2c",
        "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        "0x22132139bf7f3921b1cadeab931f4fbf7bf2bc9e",
        "0x26bff98f6f37c8d560684eaf2afd1149bf76633e",
        "0x28c6c06298d514db089934071355e5743bf21d60",
        "0x308a2a0712570daeea77c8ba9c27a32cdc4000d4",
        "0x32e11a20337ebc79abd0eeab2d91bafbd9591149",
        "0x38aaef3782910bdd9ea3566c839788af6ff9b200",
        "0x42a93a9f5cfda54716c414b6eaf07cf512f46ead",
        "0x43684d03d81d3a4c70da68febdd61029d426f042",
        "0x4976a4a02f38326660d17bf34b431dc6e2eb2327",
        "0x4aec0e98fc1fb55b9cc2faaa7a81acca42cb4e96",
        "0x4ed6cf63bd9c009d247ee51224fc1c7041f517f1",
        "0x4fdfe365436b5273a42f135c6a6244a20404271e",
        "0x56eddb7aa87536c09ccc2793473599fd21a8b17f",
        "0x5a1e5b56aa33c056ed7bb93b88b1774a456f6694",
        "0x5a52e96bacdabb82fd05763e25335261b270efcb",
        "0x6357e4bdaff733dfe8f50d12d07c03b3bed0884b",
        "0x6454ac71ca260f99cca99a3f4241dfda20cfa965",
        "0x756b86fd69914db92229c07c7393d7d9948fed33",
        "0x835678a611b28684005a5e2233695fb6cbbb0007",
        "0x8498fc7280668874a5da79e87ca0896f4f0d1196",
        "0x86523c87c8ec98c7539e2c58cd813ee9d1a08d96",
        "0x87433fec6f8d9df13d1e17c4b11364ecd2e93a51",
        "0x8a6f8404c9ea4c33502a3f6a4bf8e41ef5ca10ea",
        "0x8e609ac80f4324e499a6efd24f221a2caa868224",
        "0x9696f59e4d72e237be84ffd425dcad154bf96976",
        "0x98adef6f2ac8572ec48965509d69a8dd5e8bba9d",
        "0xa345dcb63f984ed1c6d1a8901e0cdbd13b2b4d19",
        "0xa64b436964e7415c0e70b9989a53e1fb9a90e726",
        "0xa7c0d36c4698981fab42a7d8c783674c6fe2592d",
        "0xa9fc92f6faf9f103fc81d17de3e8daadc888afff",
        "0xad354cfbaa4a8572dd6df021514a3931a8329ef5",
        "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",
        "0xc47b3342df38d747033b6041f54e4e5e300c8d18",
        "0xc8daf809c7d7c27dd62d006196d8901ba57e5eae",
        "0xd27b39cb25fed854f9fce3a4e451f96e62089e48",
        "0xdbeb6c856ef5a167f5e1acb9dff65adb33207d8b",
        "0xdbf28a152d79b2b98eecd229b412ee98d21ec3bc",
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
        "0xe1940f578743367f38d3f25c2d2d32d6636929b6",
        "0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055",
        "0xf16924b866e58ac916ba933d1f1034bcbbb1958c",
        "0xf1f8cb7633d3ca3fd06c084d18ca5491a85ae9b4",
        "0xf977814e90da44bfa03b6295a0616a897441acec",
        "0xfc8059c2fb22005ede8a86d388e3d0f536a4dd44"
      ],
      "mention": {
        "end": 40,
        "start": 33,
        "text": "Binance"
      },
      "owner": "Binance"
    },
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0003b5aa5e30e97fcc596bb5d0f3a75255e08d4e",
        "0x01c2a9e7eeaee29b03708692ba5e1515036451e8",
        "0x01f66697aec1e7de7773115243247952245fd3a4",
        "0x01f7cea182239f9e9caf0f1ce0744bcb23c20585",
        "0x03ae1a796dfe0400439211133d065bda774b9d3e",
        "0x03d0aad7c6a0b36f47d852a28ff0fb7bc9ae46b6",
        "0x0475dd0e4194422a8cac486dc69173f535d0baf4",
        "0x0607c628054a7db3d36eed7c4a408eda8260de09",
        "0x06324bad3913cb69cb5e748a3ed72f9d692324bb",
        "0x06959153b974d0d5fdfd87d561db6d8d4fa0bb0b",
        "0x06d3a30cbb00660b85a30988d197b1c282c6dcb6",
        "0x073f564419b625a45d8aea3bb0de4d5647113ad7",
        "0x0750b999e493112c88cb226a13a2a67419f06ad6",
        "0x0799ddbf6f14db566ca4df4ff0575c4cc1e7749c",
        "0x08af9c4767236221c55069dd523e2f7a0013e898",
        "0x08f619716db7c6245401b543e59acac1d25cb483",
        "0x0938c63109801ee4243a487ab84dffa2bba4589e",
        "0x0a133528245eaf5bab72dc05a9dd8e0ea4b982f9",
        "0x0c48511102453352fe570370672cd556bf0e63f9",
        "0x0ff9491b236a36cc183823e39d7532194143fdb1",
        "0x11b113383ce08e84001dc614f141ae4c27221e31",
        "0x1278678b5b17eba14b313d287659ae9f3aa7c087",
        "0x12a8bdc0470ab29a229d828526641b7d1f170fcf",
        "0x16b5016803bcb4915701efc0a3b471bd4c168d93",
        "0x173810f8ca9c4c631aeb1d6c36d007f054fee980",
        "0x17e91b98988937cb59dc163b0b11781f9785591a",
        "0x1811068091a2459ee38a8dde52cce5b2acfc1b61",
        "0x19abcd6b8516d2b4d9aa3bbf700b38a30dc154fc",
        "0x1a557020c52f9d2495b2c12eb137ee7b5d467a4f",
        "0x1c628a9c66ff63454a4526a4f2b8af250da8d086",
        "0x1dfc6bec8499fcb5e3151c7c6d27feb9d7eae1d4",
        "0x1e43e7a911b1b0229ea7d64e11ae260c482a0870",
        "0x221ac9e1920932e95adf0c941f3524157f4bda4f",
        "0x25236e080106b5387df201fbbd9a6b870917676d",
        "0x26704ccfcd45b5780dcd58d38b12f5e0cdb481a0",
        "0x267b51c97632225da2b2e49aebe59eef1af32653",
        "0x276cdba3a39abf9cedba0f1948312c0681e6d5fd",
        "0x297611b7accb7f24032c27b3a496465624c7ef50",
        "0x2c8fbb630289363ac80705a1a61273f76fd5a161",
        "0x30c1dcde81e5dbf3121d0408abc7908980e83ae2",
        "0x313eb1c5e1970eb5ceef6aebad66b07c7338d369",
        "0x32dc16f4631a27b042a974d05c1ccf8a303e8199",
        "0x3425519651e4c42833633fe5c0e24ed89c1023a3",
        "0x3b9694465483cbb677b700a91c26f487193a6e03",
        "0x3b98b9e9cb75c1cb1729aab8f09ced2936505e4f",
        "0x3bb00393bfa5e76b7f31e93948f7d3cef12942ad",
        "0x3c5883c650d600bd543a9b5c8d9a3a6f5d16b8f4",
        "0x3d2335cac7b31411467ef03168c5869452fb7e86",
        "0x3d55ccb2a943d88d39dd2e62daf767c69fd0179f",
        "0x3e7d48c8ae2e50c2b9adedc8e276d3cc92b39458",
        "0x3f482c72a2b3e777746f5755cc0ff1323ea2ad16",
        "0x400d8280acf364f683e989462879fd8dd358067d",
        "0x4106a4be14867c70e52c51b9805514ae2e16de64",
        "0x42436286a9c8d63aafc2eebbca193064d68068f2",
        "0x42797deffe266a55fdc4c98d7d3885d7058cb3e5",
        "0x42cf18596ee08e877d532df1b7cf763059a7ea57",
        "0x445f16314284b43dfa1fd3cd77b9dea4a1bebd97",
        "0x45d9c02baed2d1670f7bad40fb5f657a05068d52",
        "0x45f329ff834a84fccea2319f91e1993540b22a2a",
        "0x461249076b88189f8ac9418de28b365859e46bfd",
        "0x47eb32dea1ab1436187939fa72d6d5ff884a87da",
        "0x48480aad203e8b030f82754b3c75869c9895c6bf",
        "0x48c4c83be7e3884ee5043a3abe5115eb020b5f4a",
        "0x4a11078a99b118bbfee78a5c187d98d264360433",
        "0x4bcbaf34862e6480329477917cf5cd7b9537a98d",
        "0x4d19c0a5357bc48be0017095d3c871d9afc3f21d",
        "0x4d619eb6db0b9b6184d9881c4828c0effff84eda",
        "0x4e2757e46103556f98d4d036d8efe18389b89f51",
        "0x5041ed759dd4afc3a72b8192c143f72f4724081a",
        "0x52738a51882f35d6b25a3fd0c86089ddbd206821",
        "0x52b311c52436789f3754bd199bf3886b8ccbab4c",
        "0x539c92186f7c6cc4cbf443f26ef84c595babbca1",
        "0x559432e18b281731c054cd703d4b49872be4ed53",
        "0x56fd42ecd77c88bdd959be54af10d1759b473dff",
        "0x593878f92dde464fc4e3b17cd7cc87117dca753c",
        "0x5a150733cb59bbdd5c7398a8fe7da7f97c8a213a",
        "0x5b27e98516fd2bd5001d4dfe3f5a2263f702f634",
        "0x5b873ffcad5dccdc61c1a53c391fb76cb316a841",
        "0x5c52cc7c96bde8594e5b77d5b76d042cb5fae5f2",
        "0x5ca38fb7cf2b587026a1650f0d2b0a13c41f5d0f",
        "0x5f5105b9a19e301208844263806df9b7212e655d",
        "0x5f8215ee653cb7225c741c7aa8591468d1f158b8",
        "0x608c27519c5e65a61cfc1d2c9e658e5c57a2e3d7",
        "0x611f7bf868a6212f871e89f7e44684045ddfb09d",
        "0x65a0947ba5175359bb457d3b34491edf4cbf7997",
        "0x65e891ec42fcaa19459fe6221163e1a3f8cf7ea6",
        "0x6667a4b7eff4a0b86781fb3b187622cd3c257f09",
        "0x66e6bdac6fae819f944901e3b6ecc9bfff61a706",
        "0x6709383e211ab08a6e3270532e756220400424a6",
        "0x68841a1806ff291314946eebd0cda8b348e73d6d",
        "0x68b5e9e083bfc28c33cfbf3f19d33e629015e907",
        "0x68e2ea1622aa67fb3a01a66d132daed8a48d1662",
        "0x69a722f0b5da3af02b4a205d6f0c285f4ed8f396",
        "0x6a4561ef7874a76b4bf0d3edca31dfcd51603414",
        "0x6b7ba57e1d43c2c975ba25139a04d193e64a11d0",
        "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
        "0x6d29fc1267b1691c0cd43a8d35b27135957ffea9",
        "0x6d8c32fcf2d95ff410ba492f6694f18cbee55ce1",
        "0x6dc1a070425f437ac08bb108f7093b177d7af3a6",
        "0x6ededbad1e864105fa2538ddfbf4e7214b9e6529",
        "0x6fb624b48d9299674022a23d92515e76ba880113",
        "0x6fd41d4a272247fd1104c710909a4af8bd38f522",
        "0x728d92a8023bfbe0d4f3fdd549ed3b4996a0eba9",
        "0x730df969955c0a2fa9e8f2484e9741a363afdbb3",
        "0x739768219c831ec1f747bf904f0e25c2d99c7dc1",
        "0x767a905b77b0a40801488c6af8b8b5992b43511c",
        "0x778e456fbfd14075f5ddbccf9be2d6a48e3b1ecb",
        "0x7926c83479e2708edfd83a39d62084693e192298",
        "0x793aa889e19a130ee4cb8b63c79aa3bdccc663cb",
        "0x7a91e803db0e58b6fecc4e42c86b366778475e3c",
        "0x7a93539c1bf9a96f87044925deb7a0849266213e",
        "0x7c7061221666e41b87ca5817cfa2fcac09b3d943",
        "0x7cfe28094f4531809992ed89060a61413116365d",
        "0x7d4a2c448fe5b07c62228140417b3565bbe1b86b",
        "0x7eb6c83ab7d8d9b8618c0ed973cbef71d1921ef2",
        "0x7f61dc44c15ca818f96c6fc40739e5aa732e240c",
        "0x7fe830ec109e112f549d6ee9d3e9540e7785997b",
        "0x7fea5b4568751533039179116e372e26b6b41b13",
        "0x80335e658ee73756bb8220bdb77f99e98322035f",
        "0x8167a1ebf00ff5886d1b5908419bb1159d8cf6a4",
        "0x83a32a54d31ee4f1f9dffad2a63a6d214e469ec3",
        "0x85dcd76d4fbd3aa0c85c27b9441222c19a14134b",
        "0x868dab0b8e21ec0a48b726a1ccf25826c78c6d7f",
        "0x86aee064cc073d0dc95ba86633067b2c615040bb",
        "0x8734bca44102bf8a663e1ba112308504606e1b08",
        "0x87d0d6c8cdd71a658ecf1566f13e4cbc562beaf9",
        "0x88c94d8e7d4203b185b3beb0a7b15a6b4f36b2a2",
        "0x89b2f6dafc9d46ce0ed7d7e45a4972d14f037a19",
        "0x8ad740adce08f2f3579884eac0a12e581304ac3b",
        "0x8c3cb9665833fd9f79eb14cba16d82bbab6f22d8",
        "0x8f1aae22d0b4335945950d0bbd0f3743d3fc6f22",
        "0x91d40e4818f4d4c57b4578d9eca6afc92ac8debe",
        "0x92ea7496eba5f001d620005f88f3e8e686e3d4ea",
        "0x932d7d2cbc06234919f34802a22a914282a00f87",
        "0x96fdc631f02207b72e5804428dee274cf2ac0bcd",
        "0x9723b6d608d4841eb4ab131687a5d4764eb30138",
        "0x98ec059dc3adfbdd63429454aeb0c990fba4a128",
        "0x9938ee74ba7a5c1abcd157272a18fcfc9ec9e8d5",
        "0x994d24172fcfafbb5fce0ac5392078fa1c025448",
        "0x9b645675e8d64759e5c36e30dcb766d8cec3d34f",
        "0x9ce5a8098270f07a0a56398febda76a8ee2858c4",
        "0x9d65bf1bce7a10814228f4d81d8cf99a6b0f44aa",
        "0x9db8b860692c41e709d48d089de64cf01e6e317e",
        "0x9e13bae2256f968d02fe0129a0f51788f4e2472f",
        "0x9e3bb2cd5a89fcc4b826230b144c4917881bea85",
        "0xa01533d5c66a4886d3bb39b156507d9de65653e6",
        "0xa2684f75740cfff46c29bae79a4ecc43043c003d",
        "0xa27cef8af2b6575903b676e5644657fae96f491f",
        "0xa68cfe488a785c8b38ce2db6c45cfe07cb620c2d",
        "0xa7efae728d2936e78bda97dc267687568dd593f3",
        "0xa9ac43f5b5e38155a288d1a01d2cbc4478e14573",
        "0xacf961ae22191f0d080497a3a3b427180f18ed67",
        "0xae0cbaba071d58efc278a815b2cb652286e192ff",
        "0xb072b7dc9521d97a3f12b04beb1e497f8875ec52",
        "0xb0a27099582833c0cb8c7a0565759ff145113d64",
        "0xb47a0ac7798d8308467b2b96ac632ed43c9cb6d7",
        "0xb4ec508adeb174610b4295e233a458b3475964f7",
        "0xb640e1e5a5f726a054cd518c968dfdac8c421ee5",
        "0xb8ede418d8116113efb7644a792e5d97aade6138",
        "0xb99cc7e10fe0acc68c50c7829f473d81e23249cc",
        "0xba0a39d37151fa4f938bec51cdae4675105760f4",
        "0xba7fd71d309bc0e96b64022fd8fea7299b256159",
        "0xba96a3f3d5e9f13a5f93c37001f946d42eb2e165",
        "0xbda23b750dd04f792ad365b5f2a6f1d8593796f2",
        "0xbe2ec156292587338d4e9f80f5439e6152d56fc5",
        "0xbf94f0ac752c739f623c463b5210a7fb2cbb420b",
        "0xbfbbfaccd1126a11b8f84c60b09859f80f3bd10f",
        "0xbfef5c888bb7a0a6b14b4c3ccc4364ea81aa573f",
        "0xc0d01a27fd89e6bbc68f43e94ade3dfca2c27674",
        "0xc18475f347cc757b3cc49025820248a5f27d97ce",
        "0xc275bf069df3e63184a1222359114b805b6cd2f5",
        "0xc5267f13b9b4ba7bb73bdd53a2a3c944733a2961",
        "0xc5451b523d5fffe1351337a221688a62806ad91a",
        "0xc5a93444cc4da6efb9e6fc6e5d3cb55a53b52396",
        "0xc6724cf116573eab588fb0d73dcdc16929493cea",
        "0xc68c17e6eec0fde3605c595c9b98de5c1a4cc3e4",
        "0xc708a1c712ba26dc618f972ad7a187f76c8596fd",
        "0xcab0c0a224bad992085430f87dc1855342763a88",
        "0xcb0963264231bb08b2f680ab3ed89a49c9641bb3",
        "0xcba38020cd7b6f51df6afaf507685add148f6ab6",
        "0xcbc767b519394a9e4682cc9a15dcd18c46a6045b",
        "0xcc5d36fb0126515cb7988bbeee8445f03c304b2a",
        "0xcd5bd47d3d1d8412b241ce9015c5032142948c12",
        "0xce9abe75d561f065f1c4adb188b260df9de32ca7",
        "0xd03e6a53a3298ba1cd9b0dbf525ad728f4f8ad6e",
        "0xd049e4ddf1133af3a7a27390b4c9018141df1a49",
        "0xd19d3341227967610b94e7aebe8c971d2d48f419",
        "0xd266529641eeffaa2b2a0bc99daa5b32ef241078",
        "0xd576392cb12b7749ba33f8d223f64e65ee32f03f",
        "0xd5f8c864f21824daf3a4b22d9c33693642ed7634",
        "0xd7764b4305bcca935e38a450e7956822113374b6",
        "0xd7f4a5613b38cb8c09229b7aed99803242fdf0a0",
        "0xd99d81949146b4c13a4a42c9a6addbbd2db932ad",
        "0xd9a3c9ba5aa4415a53b9190bcb00f14472790a70",
        "0xdad24044e36587d975d7b5bceb6467fac21e0c81",
        "0xdb0ed345cb52c2f2457918afa3eb4b682e264ad0",
        "0xdc3ce895714844b4775b6d06f0dae513542cee10",
        "0xdce83237fbf279c4522e7cac4b10428e2b8694da",
        "0xddf81e81ab956695600d8639356c045e5c8a8c94",
        "0xde01974fb4a98bafd7cbf8a06ecf6dcc94d7283f",
        "0xdeb6ad2a7820839464da79bac953ae6189215443",
        "0xe2effe5bd0617a5a2dc1ee579565911cef3a223b",
        "0xe3bb282457ce7b3be31f0441f3fc051b9fc6a9c3",
        "0xe404fe9b7b0d0e88e77731517202fb392f67cd74",
        "0xe6eea9812ccc5981ccf0ab333610c42c2d92d146",
        "0xe7b29ff45392876143c7b863d57fb2326afe0ff1",
        "0xe7c8fdd899ab06ac1023e8a3e867c5fa7e751450",
        "0xe9172daf64b05b26eb18f07ac8d6d723acb48f99",
        "0xe983845a04c681a295dd9ce1fa8c2c8505932da3",
        "0xea3b7dac6b96502a04c701d5e71b51912f70143f",
        "0xeaed6576334b003d1c5c4797d9c7bb025a20c038",
        "0xeb196a61f9a1e35bf5053b65aaa57c5541dcba86",
        "0xedc0a430dd32eb8cfcc3a344979f0e21bc48bf0d",
        "0xee1c6537e589a15a15f80961f5594c57bed936fb",
        "0xf02e3c0095f6de36c76364d4cc53eb06d1288fc1",
        "0xf418263a6468c80d3bcb71033c56aacf81b241ba",
        "0xf59869753f41db720127ceb8dbb8afaf89030de4",
        "0xf683b33e21e85ee6c0e25af2fff5b2b115f32617",
        "0xf7858da8a6617f7c6d0ff2bcafdb6d2eedf64840",
        "0xf7b17e0b2478ad21ac594e4b0954ece63d059064",
        "0xf7c63e75b90c60d7b343106a39658f8b3ca6e4d2",
        "0xf8b4256122369c48eb8c3d901875d62458a675e8",
        "0xfa13971666d0e6f2715d68eb44bb7964fc22b14b",
        "0xfad70cb84e104817a7e9345d25ed0d3048af2d2d",
        "0xfcb21730ac0cd487d8701dfed1170e023b57cf7a",
        "0xfe908731af54c56dfd63948f18ce5878a3b8a1ad"
      ],
      "mention": {
        "end": 47,
        "start": 44,
        "text": "OKX"
      },
      "owner": "OKX"
    }
  ],
  "id": "v2-p04",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      },
      {
        "target": "entity:1",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      },
      {
        "target": "entity:1",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "d14dde1f6cb2fa817480aa8071456cf1fc92aeb76403b5071190c601401dbb31",
  "schema": {
    "columns": [
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "receipt_status",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "value_wei",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "c3d38571e54fb1baa005f7ee04db1699e57e8563f6909a153dd949f7057526e1"
}
```

Lý do tác giả: Ordered endpoint pair has two distinct entity direction annotations.

Sample: 0 rows; empty=True; zero/NULL aggregate=False; error=None.

Giải thích rỗng: No sampled outer transaction has Binance sender and OKX recipient; the reversed owner-pair contrast is also empty. The sample cannot discriminate this direction case. Retain the intended pair and require a full-snapshot witness in T09B.

Preview (giá trị có type tag):

```json
[]
```

Property contrast: phân biệt trên sample=False; Reverses the ordered owner pair.

```sql
SELECT receipt_status, COUNT(*) AS transactions, SUM(value_wei) AS declared_wei
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Binance' AND from_owner='OKX'
GROUP BY receipt_status ORDER BY receipt_status
```

Review binding:

```json
{
  "annotation_sha256": "23fb83710b3e4fd496c785170419d732bb1d1deec9c914f14e163dcaf71c02c9",
  "case_sha256": "eba1e48eee26c433fd6486357989386006291f36407a62f4e541d44881caf853",
  "id": "v2-p04",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "d14dde1f6cb2fa817480aa8071456cf1fc92aeb76403b5071190c601401dbb31",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "c3d38571e54fb1baa005f7ee04db1699e57e8563f6909a153dd949f7057526e1",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p05 — ambiguous_property

For token events sent by KuCoin, report each token contract's distinct recipient count and event count; sort by token address. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "direction_kucoin_token_sender_recipients"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:direction_kucoin_token_sender_recipients",
  "id": "v2-p05",
  "primary_group": "ambiguous_property",
  "property_focus": "direction",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `direction_kucoin_token_sender_recipients`. Property focus: `direction`.

```sql
SELECT token_address, COUNT(DISTINCT to_address) AS recipients, COUNT(*) AS events
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_owner='KuCoin' GROUP BY token_address ORDER BY token_address
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x04f2abb57b53122eb0306418f2220746d06af9fc",
        "0x061f7937b7b2bc7596539959804f86538b6368dc",
        "0x06679e7b7f91487cc9d59779501c414a1b3eb89d",
        "0x0669bcdc8ede4a973ed9b3480aff984de15d2d65",
        "0x0c32131b67a9306a42e5b66f869bc213d40e43f0",
        "0x0f1836312d18524368d05d537c0fabaff6ca6ccc",
        "0x0f75e66731ca8ab3471503562ff964cd40741f41",
        "0x10affefb7ce337348e0b258fffc6a1d5745c2be9",
        "0x10c3d6ef33446e51b6d5c70970f7ad71cc1f42be",
        "0x1136a49f3a1e3a3b6b2b6de30f8244d16f18509a",
        "0x1692e170361cefd1eb7240ec13d048fd9af6d667",
        "0x175ce6204bfda2a509c7e9c786b74407f569c9cc",
        "0x189b24f3eb15dc71b4fc57c5914e7e9b3246e449",
        "0x1b14376ee2d46ae5c27a43d902d96d4f3f264b83",
        "0x2677c4c8757da1857cc7cc4071e0e0dd32ccb975",
        "0x2933782b5a8d72f2754103d1489614f29bfa4625",
        "0x2c73858225cfbf15fd1b71ff27d006cb96c57e27",
        "0x37e4d1cd3fe31edf473ebcf3b6a75f419c8839d1",
        "0x3b6d76719a4ea8c53a7a26b50175b8de23c8e956",
        "0x41e29c02713929f800419abe5770faa8a5b4dadc",
        "0x4316e553902c3eab807663001d089fd6554a4566",
        "0x441454b3d857fe365b7defe8cb3e4f498ec91eac",
        "0x446b86a33e2a438f569b15855189e3da28d027ba",
        "0x44f1b02d78ed39962600df6440cf8eed3e02a96b",
        "0x45300136662dd4e58fc0df61e6290dffd992b785",
        "0x4a1dffc4e4168fd436dd9d9fb8edb223fa259a68",
        "0x58edf78281334335effa23101bbe3371b6a36a51",
        "0x5b234aaab0f61d346a3ef8faca474c1c19f80c1f",
        "0x651f1d419c548125d7e5456fb61f3df47c29600d",
        "0x69be413d648ae00f0fbd9856f1355e22b36ee5e0",
        "0x6d6cc65e2060d0a280fcd47b6c22ec5636797fec",
        "0x738cf6903e6c4e699d1c2dd9ab8b67fcdb3121ea",
        "0x7491f26a0fcb459111b3a1db2fbfc4035d096933",
        "0x77f59b595cac829575e262b4c8bbcb17abadb33a",
        "0x7b915c27a0ed48e2ce726ee40f20b2bf8a88a1b3",
        "0x7ebfa8b1161e66fffec05d7edbb55e1a2c2aebd6",
        "0x83c41363cbee0081dab75cb841fa24f3db46627e",
        "0x85cef5c097a4df05d27c9fa1a1c1fe16fe691e60",
        "0x88bd4d3e2997371bceefe8d9386c6b5b4de60346",
        "0x8dac80ce96f69f9762bc450faa4d7fbd5891ae18",
        "0x9f4cf329f4cf376b7aded854d6054859dd102a2a",
        "0xa152f8bb749c55e9943a3a0a3111d18ee2b3f94e",
        "0xa2d69adf0b62fa32825d73f086cd4689743543db",
        "0xa649ffc455ac7c5acc1bc35726fce54e25eb59f9",
        "0xaa10db8804d076601999c7cd769e02e44a99d5b2",
        "0xaa99fc695eb1bbfb359fbad718c7c6dafc03a839",
        "0xb514c67824443868d3a70352398f524ef6af6207",
        "0xb8e6d31e7b212b2b7250ee9c26c56cebbfbe6b23",
        "0xbee64116bd2b1b6373273d01664fbc5532dad06d",
        "0xcad621da75a66c7a8f4ff86d30a2bf981bfc8fdd",
        "0xce0d2213a0eaff4176d90b39879b7b4f870fa428",
        "0xd6216fc19db775df9774a6e33526131da7d19a2c",
        "0xd89350284c7732163765b23338f2ff27449e0bf5",
        "0xd91efec7e42f80156d1d9f660a69847188950747",
        "0xdd276dc5223d0120f9bf1776f38957cc8da23cb0",
        "0xe4507d13b059eaf66f7b509b6929f7295690d7cc",
        "0xe8c15aad9d4cd3f59c9dfa18828b91a8b2c49596",
        "0xec30d02f10353f8efc9601371f56e808751f396f",
        "0xf16e9b0d03470827a95cdfd0cb8a8a3b46969b91",
        "0xf8da05c625a6e601281110cba52b156e714e1dc2",
        "0xf97deb1c0bb4536ff16617d29e5f4b340fe231df"
      ],
      "mention": {
        "end": 31,
        "start": 25,
        "text": "KuCoin"
      },
      "owner": "KuCoin"
    }
  ],
  "id": "v2-p05",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "da4e04330d092904e21086ef207aa519e97ea825075b3d32950c52f25be3f004",
  "schema": {
    "columns": [
      {
        "column": "from_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "53e3df4a45ac1888a9bc86e225dcceb77fd950be17d74f6006fd4439bd0beb99"
}
```

Lý do tác giả: Transfer-event sender is not the outer transaction sender.

Sample: 429 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x0000000000085d4780b73119b644ae5ecd22b376"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "2"
    ]
  ],
  [
    [
      "string",
      "0x0000000000c5dc95539589fbd24be07c6c14eca4"
    ],
    [
      "number",
      "10"
    ],
    [
      "number",
      "34"
    ]
  ],
  [
    [
      "string",
      "0x000000fa00b200406de700041cfc6b19bbfb4d13"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "2"
    ]
  ],
  [
    [
      "string",
      "0x000006c2a22ff4a44ff1f5d0f2ed65f781f55555"
    ],
    [
      "number",
      "16"
    ],
    [
      "number",
      "45"
    ]
  ],
  [
    [
      "string",
      "0x00bac91fd8f5b4a0dc03c8021139b76f6549ee7e"
    ],
    [
      "number",
      "32"
    ],
    [
      "number",
      "104"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Wrongly constrains the event recipient owner.

```sql
SELECT token_address, COUNT(DISTINCT to_address) AS recipients, COUNT(*) AS events
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='KuCoin' GROUP BY token_address ORDER BY token_address
```

Review binding:

```json
{
  "annotation_sha256": "ce4d88a486ebae01464670d0e501c24a93c6c2ca03ccd37beac0502b92a5e5c1",
  "case_sha256": "5c890375e30370907598df937c2e579784e5bdb5923f7bea2d796b8a9976884e",
  "id": "v2-p05",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "da4e04330d092904e21086ef207aa519e97ea825075b3d32950c52f25be3f004",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "53e3df4a45ac1888a9bc86e225dcceb77fd950be17d74f6006fd4439bd0beb99",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p06 — ambiguous_property

For token events received by Gate.io, show each active date's event count and distinct outer transaction count in date order. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "direction_gate_token_receipt_multiplicity"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:direction_gate_token_receipt_multiplicity",
  "id": "v2-p06",
  "primary_group": "ambiguous_property",
  "property_focus": "direction",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `direction_gate_token_receipt_multiplicity`. Property focus: `direction`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
COUNT(DISTINCT transaction_hash) AS transactions FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
WHERE to_owner='Gate.io' GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0d0707963952f2fba59dd06f2b425ace40b492fe",
        "0x0fc73ffb9a0ded685234428e103d26b3762df460",
        "0x1c4b70a3968436b9a0a9cf5205c787eb81bb558c",
        "0x1f92332145465f3e536b7be301dde8d420478387",
        "0x234ee9e35f8e9749a002fc42970d570db716453b",
        "0x246a2ecd9626f9eda55fffbff5216ed417a904f5",
        "0x287a66c7d9cba7504e90fa638911d74c4dc6a147",
        "0x2bea9375c50f41f828c4e8eb0da3194449b5f062",
        "0x2cc81b80a293408a89084c77a0983de0730f731a",
        "0x354e0184a6a6e634ccb07388e2617e05e427563c",
        "0x356b9e62b20f4666e914fb99a9f651e5574f2bf7",
        "0x35b31ae2604dd81d9456205025ea02418dba8242",
        "0x37e1bf9ab62e523f358dafaca86151519f0a2f8d",
        "0x444c55075086f531a1c02730f41c46b9bbb00a39",
        "0x4bbe1961bd0a6cd1fe3cd8947be15bd8ae2ee562",
        "0x54c82d26624e85000d1387ee7c9580c3c6d7b5b7",
        "0x60618b3c6e3164c4a72d352bde263a5d15f9f7ee",
        "0x6596da8b65995d5feacff8c2936f0b7a2051b0d0",
        "0x66bbafc7269f1a9e5b454445585275f2b4ead28e",
        "0x68cdf5d77e75515edf7aa564d36fe3cbe751226e",
        "0x76bbb8d5dbedde9cb34882c9588dfa9def00b8bc",
        "0x7750fe679d47a9e00575ad46043297a234e83fa2",
        "0x7793cd85c11a924478d358d49b05b37e91b5810f",
        "0x7a3f9b7120386249528c93e5eb373b78e54d5ba9",
        "0x840760aed6bbd878c46c5850d3af0a61afcd09c8",
        "0x85faa6c1f2450b9caea300838981c2e6e120c35c",
        "0x8cd6437feaeb1a3a0cd65a16de2ad26bff1f5e43",
        "0x9bbe47fe66b3580551aac3124cf9fc6560252b19",
        "0x9f1daa35a4ef099c03744dfe3e67a39c4697ebe5",
        "0xa10eca918c71806ac55083d8ac942d4674b0f9ef",
        "0xa2df23519a6059dbc6f027f6cf8e59bdaecaf56f",
        "0xa2f10222b338c9ff3c953b129d1a49258f83f6c7",
        "0xa4992ccf2a74132936b87cbf28b5d52304ba3be7",
        "0xaaac1183d07c69f5befd22a06211690e953dca17",
        "0xb11c93f04bb7cc8d2d4aba47fcf73170bcea940d",
        "0xbcf03ce48091e6b820a7c33e166e5d0109d8e712",
        "0xc882b111a75c0c657fc507c04fbfcd2cc984f071",
        "0xccc5eeebe15291620be733997af60735618548d7",
        "0xcf6f5ec73942314c3ec864202b40dcbb1f9477a0",
        "0xd6a8047940a1f71df5f809919c10d9ba0a88786e",
        "0xd793281182a0e3e023116004778f45c29fc14f19",
        "0xd87c8e083aecc5405b0107c90d8e0c7f70996b84",
        "0xe39ba3f5bcbf0ef7ed31a07e799b8d2010c885cf",
        "0xf379a3d1ab6625eef34347d054cfaeafdf8f24a7",
        "0xffeb0f61871acdb4838dfc6d5082f063e738e421"
      ],
      "mention": {
        "end": 36,
        "start": 29,
        "text": "Gate.io"
      },
      "owner": "Gate.io"
    }
  ],
  "id": "v2-p06",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "790544f336fdf48e0b167f5a7672b3d2fa90b800f39c42422c75b5ae4c6a8261",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "transaction_hash",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "32e8ed75505a6f3b704714dd99daf2aaa87593f007584220fd8fcfaa71b7619d"
}
```

Lý do tác giả: Received constrains the event endpoint, not the token contract nor outer recipient.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "742"
    ],
    [
      "number",
      "742"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "637"
    ],
    [
      "number",
      "637"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "688"
    ],
    [
      "number",
      "688"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "721"
    ],
    [
      "number",
      "721"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "1027"
    ],
    [
      "number",
      "1027"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Wrongly constrains event sender owner.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
COUNT(DISTINCT transaction_hash) AS transactions FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
WHERE from_owner='Gate.io' GROUP BY day ORDER BY day
```

Review binding:

```json
{
  "annotation_sha256": "f2ba754dc1d7a68955889b44e17adf988a85fb9435618b487c54a007f6d450e1",
  "case_sha256": "404a383a8cdf48f56ca04eb53c25cb6826293f8e20837fda277154e110c199f8",
  "id": "v2-p06",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "790544f336fdf48e0b167f5a7672b3d2fa90b800f39c42422c75b5ae4c6a8261",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "32e8ed75505a6f3b704714dd99daf2aaa87593f007584220fd8fcfaa71b7619d",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p07 — ambiguous_property

For token events with MEXC at either endpoint, return total event count and the count having that owner at both endpoints. Count an internal event once in each output. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "direction_mexc_event_union_internal_count"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:direction_mexc_event_union_internal_count",
  "id": "v2-p07",
  "primary_group": "ambiguous_property",
  "property_focus": "direction",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `direction_mexc_event_union_internal_count`. Property focus: `direction`.

```sql
SELECT COUNT(*) AS involved,
COUNTIF(from_owner='MEXC' AND to_owner='MEXC') AS internal_events FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
WHERE from_owner='MEXC' OR to_owner='MEXC'
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0162cd2ba40e23378bf0fd41f919e1be075f025f",
        "0x12c5e4eeeaa20e25847b5453d23246983c512db7",
        "0x1ed0be7d0a9580e202f6b98c29725d5c11d10b71",
        "0x1f7370792a057227024e7a8cc15b40e3ed171ffc",
        "0x2ff5fc5b63f2bfce5d6bb9ea4d170cf1aa40693c",
        "0x3cc936b795a188f0e246cbb2d74c5bd190aecf18",
        "0x469afe803c54a36674c55231489cf4b61da8c1bc",
        "0x4ac71ec43df19581d95eab5596c6fadc89170989",
        "0x6e5a3b0021949452d31a43be17d808de54752a44",
        "0x75e89d5979e4f6fba9f97c104c2f0afb3f1dcb88",
        "0x76bf215ade956642b056b9043e014988941bbddd",
        "0x9642b23ed1e01df1092b92641051881a322f5d4e",
        "0xb5a6fd438017dbb0a2e5fcdcca715da227582ce4",
        "0xbcb302a64adb7f2c8697e17c1e948f5b058f0e49",
        "0xc411ab12837f63935b71b6c6643d0f7000e55e4b",
        "0xc906895c8833481571118f0c59877bff6be38ac1",
        "0xd67f25ef2399a0c769b1a35634c5ce77166714db",
        "0xe4e3eca65460c14a5245b09fee15a92ba09458b6",
        "0xee136c0389733849dd710ac7104e92c6bf497574",
        "0xf016e1d45ef23bdd414e7a2e4d46e1b34577b508",
        "0xf95334a86d09a6eec74d69da344efaca424b13a9"
      ],
      "mention": {
        "end": 26,
        "start": 22,
        "text": "MEXC"
      },
      "owner": "MEXC"
    }
  ],
  "id": "v2-p07",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "either"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "ed59d4ad98ea6f5efea609bb891b1532b8111867fa82234b8d6acff7341d24e4",
  "schema": {
    "columns": [
      {
        "column": "from_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "d4e7b88bceda770d6f3a9226e48d99b81e085f40d53c464dd880b05cbb3f2b5d"
}
```

Lý do tác giả: Either-role filter and both-role output are different Boolean conditions.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "211917"
    ],
    [
      "number",
      "314"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Confuses either endpoint with both endpoints.

```sql
SELECT COUNT(*) AS involved,
COUNTIF(from_owner='MEXC' AND to_owner='MEXC') AS internal_events FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
WHERE from_owner='MEXC' AND to_owner='MEXC'
```

Review binding:

```json
{
  "annotation_sha256": "4b6ffb1450cb397252375faa3fcacc0a3552032e6ee1d79a54f452758f93f752",
  "case_sha256": "d6c217e7cbdfd6e5a56759a0cc9e85470f4f98da939c2cc8e2723900e7191cd9",
  "id": "v2-p07",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "ed59d4ad98ea6f5efea609bb891b1532b8111867fa82234b8d6acff7341d24e4",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "d4e7b88bceda770d6f3a9226e48d99b81e085f40d53c464dd880b05cbb3f2b5d",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p08 — ambiguous_property

For outer calls addressed to Binance, count the token-transfer events emitted inside those calls and the distinct calls that emitted them, per date in chronological order. Do not filter the transfer-event recipient. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "fact_logs_inside_binance_outer_calls"
  ],
  "difficulty": "hard",
  "empty_reason": null,
  "family_id": "t09a:fact_logs_inside_binance_outer_calls",
  "id": "v2-p08",
  "primary_group": "ambiguous_property",
  "property_focus": "fact",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `fact_logs_inside_binance_outer_calls`. Property focus: `fact`.

```sql
SELECT DATE(t.block_timestamp) AS day, COUNT(*) AS events,
COUNT(DISTINCT t.transaction_hash) AS transactions FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') t JOIN `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-07-01') e
ON t.transaction_hash=e.transaction_hash AND t.block_number=e.block_number
AND t.block_hash=e.block_hash WHERE t.to_owner='Binance' GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x030e37ddd7df1b43db172b23916d523f1599c6cb",
        "0x110daa3f3fac2a54bb508ac94f31f9df77057b29",
        "0x150aace136535a374f05b5ee209b6a61396db1c0",
        "0x18e226459ccf0eec276514a4fd3b226d8961e4d1",
        "0x1b46970cfe6a271e884f636663c257a5a571fb2c",
        "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        "0x22132139bf7f3921b1cadeab931f4fbf7bf2bc9e",
        "0x26bff98f6f37c8d560684eaf2afd1149bf76633e",
        "0x28c6c06298d514db089934071355e5743bf21d60",
        "0x308a2a0712570daeea77c8ba9c27a32cdc4000d4",
        "0x32e11a20337ebc79abd0eeab2d91bafbd9591149",
        "0x38aaef3782910bdd9ea3566c839788af6ff9b200",
        "0x42a93a9f5cfda54716c414b6eaf07cf512f46ead",
        "0x43684d03d81d3a4c70da68febdd61029d426f042",
        "0x4976a4a02f38326660d17bf34b431dc6e2eb2327",
        "0x4aec0e98fc1fb55b9cc2faaa7a81acca42cb4e96",
        "0x4ed6cf63bd9c009d247ee51224fc1c7041f517f1",
        "0x4fdfe365436b5273a42f135c6a6244a20404271e",
        "0x56eddb7aa87536c09ccc2793473599fd21a8b17f",
        "0x5a1e5b56aa33c056ed7bb93b88b1774a456f6694",
        "0x5a52e96bacdabb82fd05763e25335261b270efcb",
        "0x6357e4bdaff733dfe8f50d12d07c03b3bed0884b",
        "0x6454ac71ca260f99cca99a3f4241dfda20cfa965",
        "0x756b86fd69914db92229c07c7393d7d9948fed33",
        "0x835678a611b28684005a5e2233695fb6cbbb0007",
        "0x8498fc7280668874a5da79e87ca0896f4f0d1196",
        "0x86523c87c8ec98c7539e2c58cd813ee9d1a08d96",
        "0x87433fec6f8d9df13d1e17c4b11364ecd2e93a51",
        "0x8a6f8404c9ea4c33502a3f6a4bf8e41ef5ca10ea",
        "0x8e609ac80f4324e499a6efd24f221a2caa868224",
        "0x9696f59e4d72e237be84ffd425dcad154bf96976",
        "0x98adef6f2ac8572ec48965509d69a8dd5e8bba9d",
        "0xa345dcb63f984ed1c6d1a8901e0cdbd13b2b4d19",
        "0xa64b436964e7415c0e70b9989a53e1fb9a90e726",
        "0xa7c0d36c4698981fab42a7d8c783674c6fe2592d",
        "0xa9fc92f6faf9f103fc81d17de3e8daadc888afff",
        "0xad354cfbaa4a8572dd6df021514a3931a8329ef5",
        "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",
        "0xc47b3342df38d747033b6041f54e4e5e300c8d18",
        "0xc8daf809c7d7c27dd62d006196d8901ba57e5eae",
        "0xd27b39cb25fed854f9fce3a4e451f96e62089e48",
        "0xdbeb6c856ef5a167f5e1acb9dff65adb33207d8b",
        "0xdbf28a152d79b2b98eecd229b412ee98d21ec3bc",
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
        "0xe1940f578743367f38d3f25c2d2d32d6636929b6",
        "0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055",
        "0xf16924b866e58ac916ba933d1f1034bcbbb1958c",
        "0xf1f8cb7633d3ca3fd06c084d18ca5491a85ae9b4",
        "0xf977814e90da44bfa03b6295a0616a897441acec",
        "0xfc8059c2fb22005ede8a86d388e3d0f536a4dd44"
      ],
      "mention": {
        "end": 36,
        "start": 29,
        "text": "Binance"
      },
      "owner": "Binance"
    }
  ],
  "id": "v2-p08",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction_token_transfer_join"
  },
  "question_sha256": "ac8703b2373ef96867b3d333f8609bd7974447bf828ea926756bec56212bbf67",
  "schema": {
    "columns": [
      {
        "column": "block_hash",
        "relation": "labeled_transactions"
      },
      {
        "column": "block_number",
        "relation": "labeled_transactions"
      },
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "transaction_hash",
        "relation": "labeled_transactions"
      },
      {
        "column": "block_hash",
        "relation": "token_transfer_facts"
      },
      {
        "column": "block_number",
        "relation": "token_transfer_facts"
      },
      {
        "column": "transaction_hash",
        "relation": "token_transfer_facts"
      }
    ],
    "relations": [
      "labeled_transactions",
      "token_transfer_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "c85cf01d6c15b8b2d84d9046423df33b4b4c411e7888f8e18b366c8991fc391d"
}
```

Lý do tác giả: Entity direction applies to outer calls; log endpoints may be unrelated.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "61"
    ],
    [
      "number",
      "39"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "70"
    ],
    [
      "number",
      "47"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "80"
    ],
    [
      "number",
      "51"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "58"
    ],
    [
      "number",
      "40"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "68"
    ],
    [
      "number",
      "50"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Substitutes token-event recipient for outer-call recipient.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
    COUNT(DISTINCT transaction_hash) AS transactions FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
    WHERE to_owner='Binance' GROUP BY day ORDER BY day
```

Review binding:

```json
{
  "annotation_sha256": "d98c40282a929ea7e98463ee04ac94f8ea4956da81eb36d1c7ddafae681e03d5",
  "case_sha256": "8008e1bfa8a7cbb27359750901283a5cca90777204b508d07af4ffc8707bcf3b",
  "id": "v2-p08",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "ac8703b2373ef96867b3d333f8609bd7974447bf828ea926756bec56212bbf67",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "c85cf01d6c15b8b2d84d9046423df33b4b4c411e7888f8e18b366c8991fc391d",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p09 — ambiguous_property

How many distinct outer transactions sent by Binance emitted at least two token-transfer events? Count qualifying outer transactions rather than their logs. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "fact_binance_outer_calls_with_multiple_logs"
  ],
  "difficulty": "hard",
  "empty_reason": null,
  "family_id": "t09a:fact_binance_outer_calls_with_multiple_logs",
  "id": "v2-p09",
  "primary_group": "ambiguous_property",
  "property_focus": "fact",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `fact_binance_outer_calls_with_multiple_logs`. Property focus: `fact`.

```sql
WITH calls AS (SELECT t.transaction_hash, COUNT(*) AS logs FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') t JOIN `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-07-01') e
ON t.transaction_hash=e.transaction_hash AND t.block_number=e.block_number
AND t.block_hash=e.block_hash WHERE t.from_owner='Binance'
GROUP BY t.transaction_hash HAVING logs>=2)
SELECT COUNT(*) AS outer_transactions FROM calls
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x030e37ddd7df1b43db172b23916d523f1599c6cb",
        "0x110daa3f3fac2a54bb508ac94f31f9df77057b29",
        "0x150aace136535a374f05b5ee209b6a61396db1c0",
        "0x18e226459ccf0eec276514a4fd3b226d8961e4d1",
        "0x1b46970cfe6a271e884f636663c257a5a571fb2c",
        "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        "0x22132139bf7f3921b1cadeab931f4fbf7bf2bc9e",
        "0x26bff98f6f37c8d560684eaf2afd1149bf76633e",
        "0x28c6c06298d514db089934071355e5743bf21d60",
        "0x308a2a0712570daeea77c8ba9c27a32cdc4000d4",
        "0x32e11a20337ebc79abd0eeab2d91bafbd9591149",
        "0x38aaef3782910bdd9ea3566c839788af6ff9b200",
        "0x42a93a9f5cfda54716c414b6eaf07cf512f46ead",
        "0x43684d03d81d3a4c70da68febdd61029d426f042",
        "0x4976a4a02f38326660d17bf34b431dc6e2eb2327",
        "0x4aec0e98fc1fb55b9cc2faaa7a81acca42cb4e96",
        "0x4ed6cf63bd9c009d247ee51224fc1c7041f517f1",
        "0x4fdfe365436b5273a42f135c6a6244a20404271e",
        "0x56eddb7aa87536c09ccc2793473599fd21a8b17f",
        "0x5a1e5b56aa33c056ed7bb93b88b1774a456f6694",
        "0x5a52e96bacdabb82fd05763e25335261b270efcb",
        "0x6357e4bdaff733dfe8f50d12d07c03b3bed0884b",
        "0x6454ac71ca260f99cca99a3f4241dfda20cfa965",
        "0x756b86fd69914db92229c07c7393d7d9948fed33",
        "0x835678a611b28684005a5e2233695fb6cbbb0007",
        "0x8498fc7280668874a5da79e87ca0896f4f0d1196",
        "0x86523c87c8ec98c7539e2c58cd813ee9d1a08d96",
        "0x87433fec6f8d9df13d1e17c4b11364ecd2e93a51",
        "0x8a6f8404c9ea4c33502a3f6a4bf8e41ef5ca10ea",
        "0x8e609ac80f4324e499a6efd24f221a2caa868224",
        "0x9696f59e4d72e237be84ffd425dcad154bf96976",
        "0x98adef6f2ac8572ec48965509d69a8dd5e8bba9d",
        "0xa345dcb63f984ed1c6d1a8901e0cdbd13b2b4d19",
        "0xa64b436964e7415c0e70b9989a53e1fb9a90e726",
        "0xa7c0d36c4698981fab42a7d8c783674c6fe2592d",
        "0xa9fc92f6faf9f103fc81d17de3e8daadc888afff",
        "0xad354cfbaa4a8572dd6df021514a3931a8329ef5",
        "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",
        "0xc47b3342df38d747033b6041f54e4e5e300c8d18",
        "0xc8daf809c7d7c27dd62d006196d8901ba57e5eae",
        "0xd27b39cb25fed854f9fce3a4e451f96e62089e48",
        "0xdbeb6c856ef5a167f5e1acb9dff65adb33207d8b",
        "0xdbf28a152d79b2b98eecd229b412ee98d21ec3bc",
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
        "0xe1940f578743367f38d3f25c2d2d32d6636929b6",
        "0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055",
        "0xf16924b866e58ac916ba933d1f1034bcbbb1958c",
        "0xf1f8cb7633d3ca3fd06c084d18ca5491a85ae9b4",
        "0xf977814e90da44bfa03b6295a0616a897441acec",
        "0xfc8059c2fb22005ede8a86d388e3d0f536a4dd44"
      ],
      "mention": {
        "end": 52,
        "start": 45,
        "text": "Binance"
      },
      "owner": "Binance"
    }
  ],
  "id": "v2-p09",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "transaction_token_transfer_join"
  },
  "question_sha256": "3182dd9cac05160f07e64ba97a0dfa1b692089415f1dfa8ac848d448762815d3",
  "schema": {
    "columns": [
      {
        "column": "block_hash",
        "relation": "labeled_transactions"
      },
      {
        "column": "block_number",
        "relation": "labeled_transactions"
      },
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "transaction_hash",
        "relation": "labeled_transactions"
      },
      {
        "column": "block_hash",
        "relation": "token_transfer_facts"
      },
      {
        "column": "block_number",
        "relation": "token_transfer_facts"
      },
      {
        "column": "transaction_hash",
        "relation": "token_transfer_facts"
      }
    ],
    "relations": [
      "labeled_transactions",
      "token_transfer_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "a3db99f248b27914ea723cec249d5be075d987c1f4c77aef870b13f9e25da7d5"
}
```

Lý do tác giả: First groups logs by outer hash, then counts qualifying transactions once.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "845"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Sums qualifying logs instead of counting outer transactions.

```sql
WITH calls AS (SELECT t.transaction_hash, COUNT(*) AS logs FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') t JOIN `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-07-01') e
ON t.transaction_hash=e.transaction_hash AND t.block_number=e.block_number
AND t.block_hash=e.block_hash WHERE t.from_owner='Binance'
GROUP BY t.transaction_hash HAVING logs>=2)
SELECT SUM(logs) AS outer_transactions FROM calls
```

Review binding:

```json
{
  "annotation_sha256": "a617c33b99c2df21b262b4c6564c3d81f78a7831ec1d13d6de8c8b164dfbec9e",
  "case_sha256": "82c56b83b75ed4b1fd646684614a8771a85d9f1065c8a708a972ff59dc727ed4",
  "id": "v2-p09",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "3182dd9cac05160f07e64ba97a0dfa1b692089415f1dfa8ac848d448762815d3",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "a3db99f248b27914ea723cec249d5be075d987c1f4c77aef870b13f9e25da7d5",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p10 — ambiguous_property

For token-transfer log events received by Binance, return token contract, total log count and count with positive valid raw numeric value; sort by token address. Multiple logs in one outer transaction count separately. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "fact_binance_token_event_positive_counts"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:fact_binance_token_event_positive_counts",
  "id": "v2-p10",
  "primary_group": "ambiguous_property",
  "property_focus": "fact",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `fact_binance_token_event_positive_counts`. Property focus: `fact`.

```sql
SELECT token_address, COUNT(*) AS events,
COUNTIF(value_bignumeric>0) AS positive_events FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Binance'
GROUP BY token_address ORDER BY token_address
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x030e37ddd7df1b43db172b23916d523f1599c6cb",
        "0x110daa3f3fac2a54bb508ac94f31f9df77057b29",
        "0x150aace136535a374f05b5ee209b6a61396db1c0",
        "0x18e226459ccf0eec276514a4fd3b226d8961e4d1",
        "0x1b46970cfe6a271e884f636663c257a5a571fb2c",
        "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        "0x22132139bf7f3921b1cadeab931f4fbf7bf2bc9e",
        "0x26bff98f6f37c8d560684eaf2afd1149bf76633e",
        "0x28c6c06298d514db089934071355e5743bf21d60",
        "0x308a2a0712570daeea77c8ba9c27a32cdc4000d4",
        "0x32e11a20337ebc79abd0eeab2d91bafbd9591149",
        "0x38aaef3782910bdd9ea3566c839788af6ff9b200",
        "0x42a93a9f5cfda54716c414b6eaf07cf512f46ead",
        "0x43684d03d81d3a4c70da68febdd61029d426f042",
        "0x4976a4a02f38326660d17bf34b431dc6e2eb2327",
        "0x4aec0e98fc1fb55b9cc2faaa7a81acca42cb4e96",
        "0x4ed6cf63bd9c009d247ee51224fc1c7041f517f1",
        "0x4fdfe365436b5273a42f135c6a6244a20404271e",
        "0x56eddb7aa87536c09ccc2793473599fd21a8b17f",
        "0x5a1e5b56aa33c056ed7bb93b88b1774a456f6694",
        "0x5a52e96bacdabb82fd05763e25335261b270efcb",
        "0x6357e4bdaff733dfe8f50d12d07c03b3bed0884b",
        "0x6454ac71ca260f99cca99a3f4241dfda20cfa965",
        "0x756b86fd69914db92229c07c7393d7d9948fed33",
        "0x835678a611b28684005a5e2233695fb6cbbb0007",
        "0x8498fc7280668874a5da79e87ca0896f4f0d1196",
        "0x86523c87c8ec98c7539e2c58cd813ee9d1a08d96",
        "0x87433fec6f8d9df13d1e17c4b11364ecd2e93a51",
        "0x8a6f8404c9ea4c33502a3f6a4bf8e41ef5ca10ea",
        "0x8e609ac80f4324e499a6efd24f221a2caa868224",
        "0x9696f59e4d72e237be84ffd425dcad154bf96976",
        "0x98adef6f2ac8572ec48965509d69a8dd5e8bba9d",
        "0xa345dcb63f984ed1c6d1a8901e0cdbd13b2b4d19",
        "0xa64b436964e7415c0e70b9989a53e1fb9a90e726",
        "0xa7c0d36c4698981fab42a7d8c783674c6fe2592d",
        "0xa9fc92f6faf9f103fc81d17de3e8daadc888afff",
        "0xad354cfbaa4a8572dd6df021514a3931a8329ef5",
        "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",
        "0xc47b3342df38d747033b6041f54e4e5e300c8d18",
        "0xc8daf809c7d7c27dd62d006196d8901ba57e5eae",
        "0xd27b39cb25fed854f9fce3a4e451f96e62089e48",
        "0xdbeb6c856ef5a167f5e1acb9dff65adb33207d8b",
        "0xdbf28a152d79b2b98eecd229b412ee98d21ec3bc",
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
        "0xe1940f578743367f38d3f25c2d2d32d6636929b6",
        "0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055",
        "0xf16924b866e58ac916ba933d1f1034bcbbb1958c",
        "0xf1f8cb7633d3ca3fd06c084d18ca5491a85ae9b4",
        "0xf977814e90da44bfa03b6295a0616a897441acec",
        "0xfc8059c2fb22005ede8a86d388e3d0f536a4dd44"
      ],
      "mention": {
        "end": 49,
        "start": 42,
        "text": "Binance"
      },
      "owner": "Binance"
    }
  ],
  "id": "v2-p10",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "b3a2791f5774a1eb845fa5b551a2bf902913a08c49b977239e5aa7fd6ae12782",
  "schema": {
    "columns": [
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "value_bignumeric",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "bb6276452f606381cb6806b156677cabda531b76ec0e1c855a308370933adb7c"
}
```

Lý do tác giả: One row per token log; the positive raw-value bucket does not normalize units.

Sample: 255 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x0000000000085d4780b73119b644ae5ecd22b376"
    ],
    [
      "number",
      "67"
    ],
    [
      "number",
      "67"
    ]
  ],
  [
    [
      "string",
      "0x000000fa00b200406de700041cfc6b19bbfb4d13"
    ],
    [
      "number",
      "246"
    ],
    [
      "number",
      "246"
    ]
  ],
  [
    [
      "string",
      "0x000006c2a22ff4a44ff1f5d0f2ed65f781f55555"
    ],
    [
      "number",
      "11"
    ],
    [
      "number",
      "11"
    ]
  ],
  [
    [
      "string",
      "0x00c83aecc790e8a4453e5dd3b0b4b3680501a7a7"
    ],
    [
      "number",
      "5"
    ],
    [
      "number",
      "5"
    ]
  ],
  [
    [
      "string",
      "0x01791f726b4103694969820be083196cc7c045ff"
    ],
    [
      "number",
      "13"
    ],
    [
      "number",
      "13"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Deduplicates events into transaction hashes and changes the requested row unit.

```sql
SELECT token_address, COUNT(DISTINCT transaction_hash) AS events,
COUNTIF(value_bignumeric>0) AS positive_events FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Binance'
GROUP BY token_address ORDER BY token_address
```

Review binding:

```json
{
  "annotation_sha256": "3a46cef97361cd9f9cf5cfe0f8d83dc2b03d91c606cfd04f9a7d54e00c23228c",
  "case_sha256": "d586bc2b234c82544a7481d5e4f095e892f8c3608d477117b119462602350bb5",
  "id": "v2-p10",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "b3a2791f5774a1eb845fa5b551a2bf902913a08c49b977239e5aa7fd6ae12782",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "bb6276452f606381cb6806b156677cabda531b76ec0e1c855a308370933adb7c",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p11 — ambiguous_property

For outer transactions calling the Tether contract, return receipt status, outer transaction count and total receipt gas used, ordered by status; a call need not emit a transfer log. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "fact_tether_contract_outer_call_gas"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:fact_tether_contract_outer_call_gas",
  "id": "v2-p11",
  "primary_group": "ambiguous_property",
  "property_focus": "fact",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `fact_tether_contract_outer_call_gas`. Property focus: `fact`.

```sql
SELECT receipt_status, COUNT(*) AS outer_transactions, SUM(receipt_gas_used) AS gas
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Tether' GROUP BY receipt_status ORDER BY receipt_status
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0xdac17f958d2ee523a2206206994597c13d831ec7"
      ],
      "mention": {
        "end": 41,
        "start": 35,
        "text": "Tether"
      },
      "owner": "Tether"
    }
  ],
  "id": "v2-p11",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "7ac8980ed87e0c7202a12d18772f37505178371fba22024b022ad6380c2c0179",
  "schema": {
    "columns": [
      {
        "column": "receipt_gas_used",
        "relation": "labeled_transactions"
      },
      {
        "column": "receipt_status",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "90b55902f5bd4b86e92ca79d86b09bd227d3f8ca146e4da0a28bc5ae1b5eef3f"
}
```

Lý do tác giả: A token contract used as outer recipient has endpoint role for this intent.

Sample: 2 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "0"
    ],
    [
      "number",
      "344"
    ],
    [
      "number",
      "30262584"
    ]
  ],
  [
    [
      "number",
      "1"
    ],
    [
      "number",
      "368772"
    ],
    [
      "number",
      "19930986094"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Requires token logs and duplicates gas once per log.

```sql
SELECT t.receipt_status, COUNT(*) AS outer_transactions, SUM(t.receipt_gas_used) AS gas
    FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') t JOIN `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-07-01') e ON t.transaction_hash=e.transaction_hash
    AND t.block_number=e.block_number AND t.block_hash=e.block_hash
    WHERE t.to_owner='Tether' GROUP BY t.receipt_status ORDER BY t.receipt_status
```

Review binding:

```json
{
  "annotation_sha256": "f3037fda77adfef323c394b333f7708084b004a11e5b36eeb1562fd65f26970d",
  "case_sha256": "7d9817edc9e8d52a580fb76fcbaceae132ac1a190dd976b3ab8065e7014f17cc",
  "id": "v2-p11",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "7ac8980ed87e0c7202a12d18772f37505178371fba22024b022ad6380c2c0179",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "90b55902f5bd4b86e92ca79d86b09bd227d3f8ca146e4da0a28bc5ae1b5eef3f",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p12 — ambiguous_property

For outer calls received by Uniswap V3 that emitted no token-transfer log, return active date and outer call count in date order. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "fact_uniswap_v3_calls_without_logs"
  ],
  "difficulty": "hard",
  "empty_reason": null,
  "family_id": "t09a:fact_uniswap_v3_calls_without_logs",
  "id": "v2-p12",
  "primary_group": "ambiguous_property",
  "property_focus": "fact",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `fact_uniswap_v3_calls_without_logs`. Property focus: `fact`.

```sql
SELECT DATE(t.block_timestamp) AS day, COUNT(*) AS outer_transactions FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') t
WHERE t.to_owner='Uniswap V3' AND NOT EXISTS (SELECT 1 FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-07-01') e
WHERE e.transaction_hash=t.transaction_hash AND e.block_number=t.block_number
AND e.block_hash=t.block_hash) GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "0x61ffe014ba17989e743c5f6cb21bf9697530b21e",
        "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45",
        "0xb27308f9f90d607463bb33ea1bebb41c27ce5ab6",
        "0xbfd8137f7d1516d3ea5ca83523914859ec47f573",
        "0xc36442b4a4522e871399cd717abdd847ab11fe88",
        "0xe592427a0aece92de3edee1f18e0157c05861564"
      ],
      "mention": {
        "end": 38,
        "start": 28,
        "text": "Uniswap V3"
      },
      "owner": "Uniswap V3"
    }
  ],
  "id": "v2-p12",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction_token_transfer_join"
  },
  "question_sha256": "e8f3fc92e232ae919b65b75379b80749b63c9bc7224984c82fe7e3b6c2ace1bd",
  "schema": {
    "columns": [
      {
        "column": "block_hash",
        "relation": "labeled_transactions"
      },
      {
        "column": "block_number",
        "relation": "labeled_transactions"
      },
      {
        "column": "block_timestamp",
        "relation": "labeled_transactions"
      },
      {
        "column": "to_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "transaction_hash",
        "relation": "labeled_transactions"
      },
      {
        "column": "block_hash",
        "relation": "token_transfer_facts"
      },
      {
        "column": "block_number",
        "relation": "token_transfer_facts"
      },
      {
        "column": "transaction_hash",
        "relation": "token_transfer_facts"
      }
    ],
    "relations": [
      "labeled_transactions",
      "token_transfer_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "6870b6bbcccc3013262250cf7920d826ced7639f361b608661d8f3a016c5c6b5"
}
```

Lý do tác giả: Absence of logs requires a second fact and NOT EXISTS.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "5"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "4"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "16"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "19"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "20"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Counts calls with logs instead of those without logs.

```sql
SELECT DATE(t.block_timestamp) AS day, COUNT(*) AS outer_transactions FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') t
WHERE t.to_owner='Uniswap V3' AND EXISTS (SELECT 1 FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-07-01') e
WHERE e.transaction_hash=t.transaction_hash AND e.block_number=t.block_number
AND e.block_hash=t.block_hash) GROUP BY day ORDER BY day
```

Review binding:

```json
{
  "annotation_sha256": "e73b5d4058003c055b22225c076a104678146dc89811dceac3ef150802329d46",
  "case_sha256": "ba4c922115df52031c74c81e98df61d617d2c79fa921014c74737bf073817627",
  "id": "v2-p12",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "e8f3fc92e232ae919b65b75379b80749b63c9bc7224984c82fe7e3b6c2ace1bd",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "6870b6bbcccc3013262250cf7920d826ced7639f361b608661d8f3a016c5c6b5",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p13 — ambiguous_property

Count token events received by OKX inside outer transactions sent by Binance. Return token contract, event count and distinct outer transaction count, sorted by token address; use the outer sender rather than the event sender. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "fact_outer_sender_and_event_recipient_pair"
  ],
  "difficulty": "hard",
  "empty_reason": "No sampled token event has OKX recipient inside a Binance-sent outer transaction. The event-sender contrast is also empty, so this sample does not verify the cross-fact property distinction. Recheck the join and witness on the full snapshot in T09B.",
  "family_id": "t09a:fact_outer_sender_and_event_recipient_pair",
  "id": "v2-p13",
  "primary_group": "ambiguous_property",
  "property_focus": "fact",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `fact_outer_sender_and_event_recipient_pair`. Property focus: `fact`.

```sql
SELECT e.token_address, COUNT(*) AS events,
COUNT(DISTINCT t.transaction_hash) AS outer_transactions FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') t JOIN `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') e
ON t.transaction_hash=e.transaction_hash AND t.block_number=e.block_number
AND t.block_hash=e.block_hash WHERE t.from_owner='Binance' AND e.to_owner='OKX'
GROUP BY e.token_address ORDER BY e.token_address
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x0003b5aa5e30e97fcc596bb5d0f3a75255e08d4e",
        "0x01c2a9e7eeaee29b03708692ba5e1515036451e8",
        "0x01f66697aec1e7de7773115243247952245fd3a4",
        "0x01f7cea182239f9e9caf0f1ce0744bcb23c20585",
        "0x03ae1a796dfe0400439211133d065bda774b9d3e",
        "0x03d0aad7c6a0b36f47d852a28ff0fb7bc9ae46b6",
        "0x0475dd0e4194422a8cac486dc69173f535d0baf4",
        "0x0607c628054a7db3d36eed7c4a408eda8260de09",
        "0x06324bad3913cb69cb5e748a3ed72f9d692324bb",
        "0x06959153b974d0d5fdfd87d561db6d8d4fa0bb0b",
        "0x06d3a30cbb00660b85a30988d197b1c282c6dcb6",
        "0x073f564419b625a45d8aea3bb0de4d5647113ad7",
        "0x0750b999e493112c88cb226a13a2a67419f06ad6",
        "0x0799ddbf6f14db566ca4df4ff0575c4cc1e7749c",
        "0x08af9c4767236221c55069dd523e2f7a0013e898",
        "0x08f619716db7c6245401b543e59acac1d25cb483",
        "0x0938c63109801ee4243a487ab84dffa2bba4589e",
        "0x0a133528245eaf5bab72dc05a9dd8e0ea4b982f9",
        "0x0c48511102453352fe570370672cd556bf0e63f9",
        "0x0ff9491b236a36cc183823e39d7532194143fdb1",
        "0x11b113383ce08e84001dc614f141ae4c27221e31",
        "0x1278678b5b17eba14b313d287659ae9f3aa7c087",
        "0x12a8bdc0470ab29a229d828526641b7d1f170fcf",
        "0x16b5016803bcb4915701efc0a3b471bd4c168d93",
        "0x173810f8ca9c4c631aeb1d6c36d007f054fee980",
        "0x17e91b98988937cb59dc163b0b11781f9785591a",
        "0x1811068091a2459ee38a8dde52cce5b2acfc1b61",
        "0x19abcd6b8516d2b4d9aa3bbf700b38a30dc154fc",
        "0x1a557020c52f9d2495b2c12eb137ee7b5d467a4f",
        "0x1c628a9c66ff63454a4526a4f2b8af250da8d086",
        "0x1dfc6bec8499fcb5e3151c7c6d27feb9d7eae1d4",
        "0x1e43e7a911b1b0229ea7d64e11ae260c482a0870",
        "0x221ac9e1920932e95adf0c941f3524157f4bda4f",
        "0x25236e080106b5387df201fbbd9a6b870917676d",
        "0x26704ccfcd45b5780dcd58d38b12f5e0cdb481a0",
        "0x267b51c97632225da2b2e49aebe59eef1af32653",
        "0x276cdba3a39abf9cedba0f1948312c0681e6d5fd",
        "0x297611b7accb7f24032c27b3a496465624c7ef50",
        "0x2c8fbb630289363ac80705a1a61273f76fd5a161",
        "0x30c1dcde81e5dbf3121d0408abc7908980e83ae2",
        "0x313eb1c5e1970eb5ceef6aebad66b07c7338d369",
        "0x32dc16f4631a27b042a974d05c1ccf8a303e8199",
        "0x3425519651e4c42833633fe5c0e24ed89c1023a3",
        "0x3b9694465483cbb677b700a91c26f487193a6e03",
        "0x3b98b9e9cb75c1cb1729aab8f09ced2936505e4f",
        "0x3bb00393bfa5e76b7f31e93948f7d3cef12942ad",
        "0x3c5883c650d600bd543a9b5c8d9a3a6f5d16b8f4",
        "0x3d2335cac7b31411467ef03168c5869452fb7e86",
        "0x3d55ccb2a943d88d39dd2e62daf767c69fd0179f",
        "0x3e7d48c8ae2e50c2b9adedc8e276d3cc92b39458",
        "0x3f482c72a2b3e777746f5755cc0ff1323ea2ad16",
        "0x400d8280acf364f683e989462879fd8dd358067d",
        "0x4106a4be14867c70e52c51b9805514ae2e16de64",
        "0x42436286a9c8d63aafc2eebbca193064d68068f2",
        "0x42797deffe266a55fdc4c98d7d3885d7058cb3e5",
        "0x42cf18596ee08e877d532df1b7cf763059a7ea57",
        "0x445f16314284b43dfa1fd3cd77b9dea4a1bebd97",
        "0x45d9c02baed2d1670f7bad40fb5f657a05068d52",
        "0x45f329ff834a84fccea2319f91e1993540b22a2a",
        "0x461249076b88189f8ac9418de28b365859e46bfd",
        "0x47eb32dea1ab1436187939fa72d6d5ff884a87da",
        "0x48480aad203e8b030f82754b3c75869c9895c6bf",
        "0x48c4c83be7e3884ee5043a3abe5115eb020b5f4a",
        "0x4a11078a99b118bbfee78a5c187d98d264360433",
        "0x4bcbaf34862e6480329477917cf5cd7b9537a98d",
        "0x4d19c0a5357bc48be0017095d3c871d9afc3f21d",
        "0x4d619eb6db0b9b6184d9881c4828c0effff84eda",
        "0x4e2757e46103556f98d4d036d8efe18389b89f51",
        "0x5041ed759dd4afc3a72b8192c143f72f4724081a",
        "0x52738a51882f35d6b25a3fd0c86089ddbd206821",
        "0x52b311c52436789f3754bd199bf3886b8ccbab4c",
        "0x539c92186f7c6cc4cbf443f26ef84c595babbca1",
        "0x559432e18b281731c054cd703d4b49872be4ed53",
        "0x56fd42ecd77c88bdd959be54af10d1759b473dff",
        "0x593878f92dde464fc4e3b17cd7cc87117dca753c",
        "0x5a150733cb59bbdd5c7398a8fe7da7f97c8a213a",
        "0x5b27e98516fd2bd5001d4dfe3f5a2263f702f634",
        "0x5b873ffcad5dccdc61c1a53c391fb76cb316a841",
        "0x5c52cc7c96bde8594e5b77d5b76d042cb5fae5f2",
        "0x5ca38fb7cf2b587026a1650f0d2b0a13c41f5d0f",
        "0x5f5105b9a19e301208844263806df9b7212e655d",
        "0x5f8215ee653cb7225c741c7aa8591468d1f158b8",
        "0x608c27519c5e65a61cfc1d2c9e658e5c57a2e3d7",
        "0x611f7bf868a6212f871e89f7e44684045ddfb09d",
        "0x65a0947ba5175359bb457d3b34491edf4cbf7997",
        "0x65e891ec42fcaa19459fe6221163e1a3f8cf7ea6",
        "0x6667a4b7eff4a0b86781fb3b187622cd3c257f09",
        "0x66e6bdac6fae819f944901e3b6ecc9bfff61a706",
        "0x6709383e211ab08a6e3270532e756220400424a6",
        "0x68841a1806ff291314946eebd0cda8b348e73d6d",
        "0x68b5e9e083bfc28c33cfbf3f19d33e629015e907",
        "0x68e2ea1622aa67fb3a01a66d132daed8a48d1662",
        "0x69a722f0b5da3af02b4a205d6f0c285f4ed8f396",
        "0x6a4561ef7874a76b4bf0d3edca31dfcd51603414",
        "0x6b7ba57e1d43c2c975ba25139a04d193e64a11d0",
        "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
        "0x6d29fc1267b1691c0cd43a8d35b27135957ffea9",
        "0x6d8c32fcf2d95ff410ba492f6694f18cbee55ce1",
        "0x6dc1a070425f437ac08bb108f7093b177d7af3a6",
        "0x6ededbad1e864105fa2538ddfbf4e7214b9e6529",
        "0x6fb624b48d9299674022a23d92515e76ba880113",
        "0x6fd41d4a272247fd1104c710909a4af8bd38f522",
        "0x728d92a8023bfbe0d4f3fdd549ed3b4996a0eba9",
        "0x730df969955c0a2fa9e8f2484e9741a363afdbb3",
        "0x739768219c831ec1f747bf904f0e25c2d99c7dc1",
        "0x767a905b77b0a40801488c6af8b8b5992b43511c",
        "0x778e456fbfd14075f5ddbccf9be2d6a48e3b1ecb",
        "0x7926c83479e2708edfd83a39d62084693e192298",
        "0x793aa889e19a130ee4cb8b63c79aa3bdccc663cb",
        "0x7a91e803db0e58b6fecc4e42c86b366778475e3c",
        "0x7a93539c1bf9a96f87044925deb7a0849266213e",
        "0x7c7061221666e41b87ca5817cfa2fcac09b3d943",
        "0x7cfe28094f4531809992ed89060a61413116365d",
        "0x7d4a2c448fe5b07c62228140417b3565bbe1b86b",
        "0x7eb6c83ab7d8d9b8618c0ed973cbef71d1921ef2",
        "0x7f61dc44c15ca818f96c6fc40739e5aa732e240c",
        "0x7fe830ec109e112f549d6ee9d3e9540e7785997b",
        "0x7fea5b4568751533039179116e372e26b6b41b13",
        "0x80335e658ee73756bb8220bdb77f99e98322035f",
        "0x8167a1ebf00ff5886d1b5908419bb1159d8cf6a4",
        "0x83a32a54d31ee4f1f9dffad2a63a6d214e469ec3",
        "0x85dcd76d4fbd3aa0c85c27b9441222c19a14134b",
        "0x868dab0b8e21ec0a48b726a1ccf25826c78c6d7f",
        "0x86aee064cc073d0dc95ba86633067b2c615040bb",
        "0x8734bca44102bf8a663e1ba112308504606e1b08",
        "0x87d0d6c8cdd71a658ecf1566f13e4cbc562beaf9",
        "0x88c94d8e7d4203b185b3beb0a7b15a6b4f36b2a2",
        "0x89b2f6dafc9d46ce0ed7d7e45a4972d14f037a19",
        "0x8ad740adce08f2f3579884eac0a12e581304ac3b",
        "0x8c3cb9665833fd9f79eb14cba16d82bbab6f22d8",
        "0x8f1aae22d0b4335945950d0bbd0f3743d3fc6f22",
        "0x91d40e4818f4d4c57b4578d9eca6afc92ac8debe",
        "0x92ea7496eba5f001d620005f88f3e8e686e3d4ea",
        "0x932d7d2cbc06234919f34802a22a914282a00f87",
        "0x96fdc631f02207b72e5804428dee274cf2ac0bcd",
        "0x9723b6d608d4841eb4ab131687a5d4764eb30138",
        "0x98ec059dc3adfbdd63429454aeb0c990fba4a128",
        "0x9938ee74ba7a5c1abcd157272a18fcfc9ec9e8d5",
        "0x994d24172fcfafbb5fce0ac5392078fa1c025448",
        "0x9b645675e8d64759e5c36e30dcb766d8cec3d34f",
        "0x9ce5a8098270f07a0a56398febda76a8ee2858c4",
        "0x9d65bf1bce7a10814228f4d81d8cf99a6b0f44aa",
        "0x9db8b860692c41e709d48d089de64cf01e6e317e",
        "0x9e13bae2256f968d02fe0129a0f51788f4e2472f",
        "0x9e3bb2cd5a89fcc4b826230b144c4917881bea85",
        "0xa01533d5c66a4886d3bb39b156507d9de65653e6",
        "0xa2684f75740cfff46c29bae79a4ecc43043c003d",
        "0xa27cef8af2b6575903b676e5644657fae96f491f",
        "0xa68cfe488a785c8b38ce2db6c45cfe07cb620c2d",
        "0xa7efae728d2936e78bda97dc267687568dd593f3",
        "0xa9ac43f5b5e38155a288d1a01d2cbc4478e14573",
        "0xacf961ae22191f0d080497a3a3b427180f18ed67",
        "0xae0cbaba071d58efc278a815b2cb652286e192ff",
        "0xb072b7dc9521d97a3f12b04beb1e497f8875ec52",
        "0xb0a27099582833c0cb8c7a0565759ff145113d64",
        "0xb47a0ac7798d8308467b2b96ac632ed43c9cb6d7",
        "0xb4ec508adeb174610b4295e233a458b3475964f7",
        "0xb640e1e5a5f726a054cd518c968dfdac8c421ee5",
        "0xb8ede418d8116113efb7644a792e5d97aade6138",
        "0xb99cc7e10fe0acc68c50c7829f473d81e23249cc",
        "0xba0a39d37151fa4f938bec51cdae4675105760f4",
        "0xba7fd71d309bc0e96b64022fd8fea7299b256159",
        "0xba96a3f3d5e9f13a5f93c37001f946d42eb2e165",
        "0xbda23b750dd04f792ad365b5f2a6f1d8593796f2",
        "0xbe2ec156292587338d4e9f80f5439e6152d56fc5",
        "0xbf94f0ac752c739f623c463b5210a7fb2cbb420b",
        "0xbfbbfaccd1126a11b8f84c60b09859f80f3bd10f",
        "0xbfef5c888bb7a0a6b14b4c3ccc4364ea81aa573f",
        "0xc0d01a27fd89e6bbc68f43e94ade3dfca2c27674",
        "0xc18475f347cc757b3cc49025820248a5f27d97ce",
        "0xc275bf069df3e63184a1222359114b805b6cd2f5",
        "0xc5267f13b9b4ba7bb73bdd53a2a3c944733a2961",
        "0xc5451b523d5fffe1351337a221688a62806ad91a",
        "0xc5a93444cc4da6efb9e6fc6e5d3cb55a53b52396",
        "0xc6724cf116573eab588fb0d73dcdc16929493cea",
        "0xc68c17e6eec0fde3605c595c9b98de5c1a4cc3e4",
        "0xc708a1c712ba26dc618f972ad7a187f76c8596fd",
        "0xcab0c0a224bad992085430f87dc1855342763a88",
        "0xcb0963264231bb08b2f680ab3ed89a49c9641bb3",
        "0xcba38020cd7b6f51df6afaf507685add148f6ab6",
        "0xcbc767b519394a9e4682cc9a15dcd18c46a6045b",
        "0xcc5d36fb0126515cb7988bbeee8445f03c304b2a",
        "0xcd5bd47d3d1d8412b241ce9015c5032142948c12",
        "0xce9abe75d561f065f1c4adb188b260df9de32ca7",
        "0xd03e6a53a3298ba1cd9b0dbf525ad728f4f8ad6e",
        "0xd049e4ddf1133af3a7a27390b4c9018141df1a49",
        "0xd19d3341227967610b94e7aebe8c971d2d48f419",
        "0xd266529641eeffaa2b2a0bc99daa5b32ef241078",
        "0xd576392cb12b7749ba33f8d223f64e65ee32f03f",
        "0xd5f8c864f21824daf3a4b22d9c33693642ed7634",
        "0xd7764b4305bcca935e38a450e7956822113374b6",
        "0xd7f4a5613b38cb8c09229b7aed99803242fdf0a0",
        "0xd99d81949146b4c13a4a42c9a6addbbd2db932ad",
        "0xd9a3c9ba5aa4415a53b9190bcb00f14472790a70",
        "0xdad24044e36587d975d7b5bceb6467fac21e0c81",
        "0xdb0ed345cb52c2f2457918afa3eb4b682e264ad0",
        "0xdc3ce895714844b4775b6d06f0dae513542cee10",
        "0xdce83237fbf279c4522e7cac4b10428e2b8694da",
        "0xddf81e81ab956695600d8639356c045e5c8a8c94",
        "0xde01974fb4a98bafd7cbf8a06ecf6dcc94d7283f",
        "0xdeb6ad2a7820839464da79bac953ae6189215443",
        "0xe2effe5bd0617a5a2dc1ee579565911cef3a223b",
        "0xe3bb282457ce7b3be31f0441f3fc051b9fc6a9c3",
        "0xe404fe9b7b0d0e88e77731517202fb392f67cd74",
        "0xe6eea9812ccc5981ccf0ab333610c42c2d92d146",
        "0xe7b29ff45392876143c7b863d57fb2326afe0ff1",
        "0xe7c8fdd899ab06ac1023e8a3e867c5fa7e751450",
        "0xe9172daf64b05b26eb18f07ac8d6d723acb48f99",
        "0xe983845a04c681a295dd9ce1fa8c2c8505932da3",
        "0xea3b7dac6b96502a04c701d5e71b51912f70143f",
        "0xeaed6576334b003d1c5c4797d9c7bb025a20c038",
        "0xeb196a61f9a1e35bf5053b65aaa57c5541dcba86",
        "0xedc0a430dd32eb8cfcc3a344979f0e21bc48bf0d",
        "0xee1c6537e589a15a15f80961f5594c57bed936fb",
        "0xf02e3c0095f6de36c76364d4cc53eb06d1288fc1",
        "0xf418263a6468c80d3bcb71033c56aacf81b241ba",
        "0xf59869753f41db720127ceb8dbb8afaf89030de4",
        "0xf683b33e21e85ee6c0e25af2fff5b2b115f32617",
        "0xf7858da8a6617f7c6d0ff2bcafdb6d2eedf64840",
        "0xf7b17e0b2478ad21ac594e4b0954ece63d059064",
        "0xf7c63e75b90c60d7b343106a39658f8b3ca6e4d2",
        "0xf8b4256122369c48eb8c3d901875d62458a675e8",
        "0xfa13971666d0e6f2715d68eb44bb7964fc22b14b",
        "0xfad70cb84e104817a7e9345d25ed0d3048af2d2d",
        "0xfcb21730ac0cd487d8701dfed1170e023b57cf7a",
        "0xfe908731af54c56dfd63948f18ce5878a3b8a1ad"
      ],
      "mention": {
        "end": 34,
        "start": 31,
        "text": "OKX"
      },
      "owner": "OKX"
    },
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x030e37ddd7df1b43db172b23916d523f1599c6cb",
        "0x110daa3f3fac2a54bb508ac94f31f9df77057b29",
        "0x150aace136535a374f05b5ee209b6a61396db1c0",
        "0x18e226459ccf0eec276514a4fd3b226d8961e4d1",
        "0x1b46970cfe6a271e884f636663c257a5a571fb2c",
        "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        "0x22132139bf7f3921b1cadeab931f4fbf7bf2bc9e",
        "0x26bff98f6f37c8d560684eaf2afd1149bf76633e",
        "0x28c6c06298d514db089934071355e5743bf21d60",
        "0x308a2a0712570daeea77c8ba9c27a32cdc4000d4",
        "0x32e11a20337ebc79abd0eeab2d91bafbd9591149",
        "0x38aaef3782910bdd9ea3566c839788af6ff9b200",
        "0x42a93a9f5cfda54716c414b6eaf07cf512f46ead",
        "0x43684d03d81d3a4c70da68febdd61029d426f042",
        "0x4976a4a02f38326660d17bf34b431dc6e2eb2327",
        "0x4aec0e98fc1fb55b9cc2faaa7a81acca42cb4e96",
        "0x4ed6cf63bd9c009d247ee51224fc1c7041f517f1",
        "0x4fdfe365436b5273a42f135c6a6244a20404271e",
        "0x56eddb7aa87536c09ccc2793473599fd21a8b17f",
        "0x5a1e5b56aa33c056ed7bb93b88b1774a456f6694",
        "0x5a52e96bacdabb82fd05763e25335261b270efcb",
        "0x6357e4bdaff733dfe8f50d12d07c03b3bed0884b",
        "0x6454ac71ca260f99cca99a3f4241dfda20cfa965",
        "0x756b86fd69914db92229c07c7393d7d9948fed33",
        "0x835678a611b28684005a5e2233695fb6cbbb0007",
        "0x8498fc7280668874a5da79e87ca0896f4f0d1196",
        "0x86523c87c8ec98c7539e2c58cd813ee9d1a08d96",
        "0x87433fec6f8d9df13d1e17c4b11364ecd2e93a51",
        "0x8a6f8404c9ea4c33502a3f6a4bf8e41ef5ca10ea",
        "0x8e609ac80f4324e499a6efd24f221a2caa868224",
        "0x9696f59e4d72e237be84ffd425dcad154bf96976",
        "0x98adef6f2ac8572ec48965509d69a8dd5e8bba9d",
        "0xa345dcb63f984ed1c6d1a8901e0cdbd13b2b4d19",
        "0xa64b436964e7415c0e70b9989a53e1fb9a90e726",
        "0xa7c0d36c4698981fab42a7d8c783674c6fe2592d",
        "0xa9fc92f6faf9f103fc81d17de3e8daadc888afff",
        "0xad354cfbaa4a8572dd6df021514a3931a8329ef5",
        "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",
        "0xc47b3342df38d747033b6041f54e4e5e300c8d18",
        "0xc8daf809c7d7c27dd62d006196d8901ba57e5eae",
        "0xd27b39cb25fed854f9fce3a4e451f96e62089e48",
        "0xdbeb6c856ef5a167f5e1acb9dff65adb33207d8b",
        "0xdbf28a152d79b2b98eecd229b412ee98d21ec3bc",
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
        "0xe1940f578743367f38d3f25c2d2d32d6636929b6",
        "0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055",
        "0xf16924b866e58ac916ba933d1f1034bcbbb1958c",
        "0xf1f8cb7633d3ca3fd06c084d18ca5491a85ae9b4",
        "0xf977814e90da44bfa03b6295a0616a897441acec",
        "0xfc8059c2fb22005ede8a86d388e3d0f536a4dd44"
      ],
      "mention": {
        "end": 76,
        "start": 69,
        "text": "Binance"
      },
      "owner": "Binance"
    }
  ],
  "id": "v2-p13",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      },
      {
        "target": "entity:1",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      },
      {
        "target": "entity:1",
        "value": "from"
      }
    ],
    "fact": "transaction_token_transfer_join"
  },
  "question_sha256": "a6025fe098c098f483b43756e3aeeb32ffc1d663dbe5074af1fc31b6f412b959",
  "schema": {
    "columns": [
      {
        "column": "block_hash",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "block_number",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "transaction_hash",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "block_hash",
        "relation": "labeled_transactions"
      },
      {
        "column": "block_number",
        "relation": "labeled_transactions"
      },
      {
        "column": "from_owner",
        "relation": "labeled_transactions"
      },
      {
        "column": "transaction_hash",
        "relation": "labeled_transactions"
      }
    ],
    "relations": [
      "labeled_token_transfers",
      "labeled_transactions"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "ad021292b0942e44adbb68c7d047886ea6e982d95114925eee2b915250805569"
}
```

Lý do tác giả: Each entity constrains a different fact: outer sender versus log recipient.

Sample: 0 rows; empty=True; zero/NULL aggregate=False; error=None.

Giải thích rỗng: No sampled token event has OKX recipient inside a Binance-sent outer transaction. The event-sender contrast is also empty, so this sample does not verify the cross-fact property distinction. Recheck the join and witness on the full snapshot in T09B.

Preview (giá trị có type tag):

```json
[]
```

Property contrast: phân biệt trên sample=False; Uses event sender instead of the requested outer sender.

```sql
SELECT e.token_address, COUNT(*) AS events,
COUNT(DISTINCT t.transaction_hash) AS outer_transactions FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-06-01', DATE '2026-07-01') t JOIN `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') e
ON t.transaction_hash=e.transaction_hash AND t.block_number=e.block_number
AND t.block_hash=e.block_hash WHERE e.from_owner='Binance' AND e.to_owner='OKX'
GROUP BY e.token_address ORDER BY e.token_address
```

Review binding:

```json
{
  "annotation_sha256": "037effd3009112a04d05a3349871cefa3aaa2c55bd8fd7950150c9cd688e299a",
  "case_sha256": "10696d19b9fe029b1ba6e60902b651cee291235fa16b2008b927c2a78f9283ba",
  "id": "v2-p13",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "a6025fe098c098f483b43756e3aeeb32ffc1d663dbe5074af1fc31b6f412b959",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "ad021292b0942e44adbb68c7d047886ea6e982d95114925eee2b915250805569",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p14 — ambiguous_property

List transaction hash and log index for USDT token-transfer events linked to failed outer transactions with receipt status 0, ordered by hash then log index. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "fact_usdt_logs_in_failed_outer_transactions"
  ],
  "difficulty": "hard",
  "empty_reason": "No sampled USDT event joins a failed outer transaction. This is a deliberate negative control: reverted EVM transactions normally do not retain transfer logs. The successful-transaction contrast is nonempty; full-snapshot integrity review is still pending.",
  "family_id": "t09a:fact_usdt_logs_in_failed_outer_transactions",
  "id": "v2-p14",
  "primary_group": "ambiguous_property",
  "property_focus": "fact",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "ambiguous_property"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `fact_usdt_logs_in_failed_outer_transactions`. Property focus: `fact`.

```sql
SELECT e.transaction_hash, e.log_index FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') e JOIN `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01') t
ON e.transaction_hash=t.transaction_hash AND e.block_number=t.block_number
AND e.block_hash=t.block_hash WHERE e.token_owner='Tether' AND t.receipt_status=0
ORDER BY e.transaction_hash, e.log_index
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0xdac17f958d2ee523a2206206994597c13d831ec7"
      ],
      "mention": {
        "end": 44,
        "start": 40,
        "text": "USDT"
      },
      "owner": "Tether"
    }
  ],
  "id": "v2-p14",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "token_contract"
      }
    ],
    "direction": [],
    "fact": "transaction_token_transfer_join"
  },
  "question_sha256": "18e8099702be547430736a89874b995edb2e3fcb3bc574102f4f79d49be93a7e",
  "schema": {
    "columns": [
      {
        "column": "block_hash",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "block_number",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "log_index",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "transaction_hash",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "block_hash",
        "relation": "transaction_facts"
      },
      {
        "column": "block_number",
        "relation": "transaction_facts"
      },
      {
        "column": "receipt_status",
        "relation": "transaction_facts"
      },
      {
        "column": "transaction_hash",
        "relation": "transaction_facts"
      }
    ],
    "relations": [
      "labeled_token_transfers",
      "transaction_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "85bfe7b0015adeca4d240b8598ac49cddbb891b7b337699848020f30257f4697"
}
```

Lý do tác giả: Negative control: reverted outer transactions normally retain no logs; preserve a justified empty answer.

Sample: 0 rows; empty=True; zero/NULL aggregate=False; error=None.

Giải thích rỗng: No sampled USDT event joins a failed outer transaction. This is a deliberate negative control: reverted EVM transactions normally do not retain transfer logs. The successful-transaction contrast is nonempty; full-snapshot integrity review is still pending.

Preview (giá trị có type tag):

```json
[]
```

Property contrast: phân biệt trên sample=True; Selects successful outer transactions, losing the negative-control fact condition.

```sql
SELECT e.transaction_hash, e.log_index FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') e JOIN `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01') t
ON e.transaction_hash=t.transaction_hash AND e.block_number=t.block_number
AND e.block_hash=t.block_hash WHERE e.token_owner='Tether' AND t.receipt_status=1
ORDER BY e.transaction_hash, e.log_index
```

Review binding:

```json
{
  "annotation_sha256": "f61b139f724e23d693a2de09b745c27be0f280d30a382602e3c39f0a0cc6a854",
  "case_sha256": "5407c6341eaaa0ac5385f56c2bf8597f1e110869584fb92f88769888110d50cd",
  "id": "v2-p14",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "18e8099702be547430736a89874b995edb2e3fcb3bc574102f4f79d49be93a7e",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "85bfe7b0015adeca4d240b8598ac49cddbb891b7b337699848020f30257f4697",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p15 — ambiguous_property

For USDT as token identity, report each active date's distinct sender count, distinct recipient count and transfer-event count, ordered by date; do not restrict either endpoint to the token contract. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "role_usdt_token_daily_endpoint_reach"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:role_usdt_token_daily_endpoint_reach",
  "id": "v2-p15",
  "primary_group": "ambiguous_property",
  "property_focus": "address_role",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "ambiguous_property"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `role_usdt_token_daily_endpoint_reach`. Property focus: `address_role`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(DISTINCT from_address) AS senders,
COUNT(DISTINCT to_address) AS recipients, COUNT(*) AS events FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
WHERE token_owner='Tether' GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0xdac17f958d2ee523a2206206994597c13d831ec7"
      ],
      "mention": {
        "end": 8,
        "start": 4,
        "text": "USDT"
      },
      "owner": "Tether"
    }
  ],
  "id": "v2-p15",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "token_contract"
      }
    ],
    "direction": [],
    "fact": "token_transfer"
  },
  "question_sha256": "3a0d5ac4e7e3f9771e2852b3255201c055b5c931e1127569b1384a06c5d0c199",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "from_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_owner",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "c8f688380f7e85d7da33d0e7cf76508c3ff045f9ac8be3a7322cfbfd4af8aa12"
}
```

Lý do tác giả: Token mention maps to token_address, not sender or recipient.

Sample: 30 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "6436"
    ],
    [
      "number",
      "15036"
    ],
    [
      "number",
      "23971"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "7125"
    ],
    [
      "number",
      "16537"
    ],
    [
      "number",
      "25237"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "5195"
    ],
    [
      "number",
      "13855"
    ],
    [
      "number",
      "21864"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "5596"
    ],
    [
      "number",
      "14480"
    ],
    [
      "number",
      "22147"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "6306"
    ],
    [
      "number",
      "15472"
    ],
    [
      "number",
      "24292"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Misreads token identity as event recipient endpoint.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(DISTINCT from_address) AS senders,
COUNT(DISTINCT to_address) AS recipients, COUNT(*) AS events FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
WHERE to_owner='Tether' GROUP BY day ORDER BY day
```

Review binding:

```json
{
  "annotation_sha256": "1b2a046785aa13bb8de7f3a8c4b54282d439e3d0a6ce02bcd1b0d7bcb277b4d9",
  "case_sha256": "df97b3fc5185b4f18329c38666a472fa31b158238ffa9b91812bfbd01e62190f",
  "id": "v2-p15",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "3a0d5ac4e7e3f9771e2852b3255201c055b5c931e1127569b1384a06c5d0c199",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "c8f688380f7e85d7da33d0e7cf76508c3ff045f9ac8be3a7322cfbfd4af8aa12",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p16 — ambiguous_property

For token events whose recipient is the USDT contract address, return transferred token contract, event count and distinct sender count, sorted by token address; allow any transferred token. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "role_usdt_contract_as_event_recipient"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:role_usdt_contract_as_event_recipient",
  "id": "v2-p16",
  "primary_group": "ambiguous_property",
  "property_focus": "address_role",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "alias",
    "ambiguous_property"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `role_usdt_contract_as_event_recipient`. Property focus: `address_role`.

```sql
SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT from_address) AS senders
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE to_owner='Tether' GROUP BY token_address ORDER BY token_address
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0xdac17f958d2ee523a2206206994597c13d831ec7"
      ],
      "mention": {
        "end": 44,
        "start": 40,
        "text": "USDT"
      },
      "owner": "Tether"
    }
  ],
  "id": "v2-p16",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "2b9cd5f6bf6439d34b4cdc2d5fb8b75527c66fdf4b79c7302dd4f2e5565ac146",
  "schema": {
    "columns": [
      {
        "column": "from_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_address",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "ba8da9d096d37f4c04e8c3a901dc5938038afc49f65073200d3709d4345f4024"
}
```

Lý do tác giả: The ticker names an endpoint here; token_address need not equal the mentioned contract.

Sample: 4 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x0f6b862e05a9b528b0002261f9eb616e6c4452e9"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "0x2f42b7d686ca3effc69778b6ed8493a7787b4d6e"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "0xdac17f958d2ee523a2206206994597c13d831ec7"
    ],
    [
      "number",
      "42"
    ],
    [
      "number",
      "8"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Misreads recipient endpoint as transferred token identity.

```sql
SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT from_address) AS senders
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE token_owner='Tether' GROUP BY token_address ORDER BY token_address
```

Review binding:

```json
{
  "annotation_sha256": "74a57c7caa8ac9f8843be99d4f83579c2d80e7c035455e65ec5c561ae987a826",
  "case_sha256": "635f7b93a40f2fd870dee766c7ad8d0013e6536c2553237c017dc22440e7f5f0",
  "id": "v2-p16",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "2b9cd5f6bf6439d34b4cdc2d5fb8b75527c66fdf4b79c7302dd4f2e5565ac146",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "ba8da9d096d37f4c04e8c3a901dc5938038afc49f65073200d3709d4345f4024",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p17 — ambiguous_property

For outer calls addressed to 0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2, return receipt status, call count and sum of declared wei, ordered by status. Treat the address as the called endpoint. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "role_explicit_weth_outer_recipient"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:role_explicit_weth_outer_recipient",
  "id": "v2-p17",
  "primary_group": "ambiguous_property",
  "property_focus": "address_role",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `role_explicit_weth_outer_recipient`. Property focus: `address_role`.

```sql
SELECT receipt_status, COUNT(*) AS calls, SUM(value_wei) AS declared_wei FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01')
WHERE to_address='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
GROUP BY receipt_status ORDER BY receipt_status
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "explicit_address",
      "addresses": [
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
      ],
      "mention": {
        "end": 71,
        "start": 29,
        "text": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
      },
      "owner": "WETH"
    }
  ],
  "id": "v2-p17",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "to"
      }
    ],
    "fact": "transaction"
  },
  "question_sha256": "93ec5da58fde8608012150ca1656837f0d6a164ee441118d17edd562c8b75a09",
  "schema": {
    "columns": [
      {
        "column": "receipt_status",
        "relation": "transaction_facts"
      },
      {
        "column": "to_address",
        "relation": "transaction_facts"
      },
      {
        "column": "value_wei",
        "relation": "transaction_facts"
      }
    ],
    "relations": [
      "transaction_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "5da486a92182a20ad7e07ad8df5f469757be903e60aa9f416fafd9527097b5b4"
}
```

Lý do tác giả: Explicit literal has explicit_address scope and known owner WETH.

Sample: 2 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "0"
    ],
    [
      "number",
      "2174"
    ],
    [
      "number",
      "129543076508034883910"
    ]
  ],
  [
    [
      "number",
      "1"
    ],
    [
      "number",
      "242574"
    ],
    [
      "number",
      "305542633185090909026459"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Uses the literal as transferred token identity, ignoring the requested outer recipient.

```sql
SELECT t.receipt_status, COUNT(*) AS calls, SUM(t.value_wei) AS declared_wei FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-07-01') t
    WHERE EXISTS (SELECT 1 FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-07-01') e WHERE e.transaction_hash=t.transaction_hash
    AND e.block_number=t.block_number AND e.block_hash=t.block_hash
    AND e.token_address='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2')
    GROUP BY t.receipt_status ORDER BY t.receipt_status
```

Review binding:

```json
{
  "annotation_sha256": "765d84fa7a8daab92a51119816706ca2b07e019305485bcf01fbce1673d8ec04",
  "case_sha256": "1d9e555ab63a7f73073fd35343af0dd6eb13148be5c7fd06e92cfcc49f327c26",
  "id": "v2-p17",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "93ec5da58fde8608012150ca1656837f0d6a164ee441118d17edd562c8b75a09",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "5da486a92182a20ad7e07ad8df5f469757be903e60aa9f416fafd9527097b5b4",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p18 — ambiguous_property

For WETH as the transferred token, return total event count and the count whose sender equals recipient; the contract address is token identity, not an endpoint restriction. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "role_weth_token_self_event_counts"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:role_weth_token_self_event_counts",
  "id": "v2-p18",
  "primary_group": "ambiguous_property",
  "property_focus": "address_role",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `role_weth_token_self_event_counts`. Property focus: `address_role`.

```sql
SELECT COUNT(*) AS events, COUNTIF(from_address=to_address) AS self_events
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE token_owner='WETH'
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
      ],
      "mention": {
        "end": 8,
        "start": 4,
        "text": "WETH"
      },
      "owner": "WETH"
    }
  ],
  "id": "v2-p18",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "token_contract"
      }
    ],
    "direction": [],
    "fact": "token_transfer"
  },
  "question_sha256": "1ab68964d6e5aa30a28c79d87d552c142848086bb9b4f1d7833d6fc4526ca862",
  "schema": {
    "columns": [
      {
        "column": "from_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_owner",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "7f0cf8418fbecf284c4efc17293666e820ee52b6ebc5cc371ca94a1155bd36b7"
}
```

Lý do tác giả: Self-event comparison does not make the named token an endpoint target.

Sample: 1 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "number",
      "105518"
    ],
    [
      "number",
      "221"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Treats the token identity as sender of arbitrary token events.

```sql
SELECT COUNT(*) AS events, COUNTIF(from_address=to_address) AS self_events
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_owner='WETH'
```

Review binding:

```json
{
  "annotation_sha256": "074c05eb84ff57118bbf83fd7285872e356a3319ee01244914395a4c0f78d43d",
  "case_sha256": "f2c9134105a25698a724d73ea2c8734b5cafb72f3d66d9644374fdb763a10f5b",
  "id": "v2-p18",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "1ab68964d6e5aa30a28c79d87d552c142848086bb9b4f1d7833d6fc4526ca862",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "7f0cf8418fbecf284c4efc17293666e820ee52b6ebc5cc371ca94a1155bd36b7",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p19 — ambiguous_property

For Chainlink tokens received by Binance, show each active date's event count and distinct sender count, ordered by date. The first named owner specifies token identity and the second specifies the recipient endpoint. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "role_chainlink_token_binance_endpoint"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:role_chainlink_token_binance_endpoint",
  "id": "v2-p19",
  "primary_group": "ambiguous_property",
  "property_focus": "address_role",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property",
    "multi_address"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `role_chainlink_token_binance_endpoint`. Property focus: `address_role`.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
COUNT(DISTINCT from_address) AS senders FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
WHERE token_owner='Chainlink' AND to_owner='Binance' GROUP BY day ORDER BY day
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x514910771af9ca656af840dff83e8264ecf986ca"
      ],
      "mention": {
        "end": 13,
        "start": 4,
        "text": "Chainlink"
      },
      "owner": "Chainlink"
    },
    {
      "address_scope": "known_owner_addresses",
      "addresses": [
        "0x030e37ddd7df1b43db172b23916d523f1599c6cb",
        "0x110daa3f3fac2a54bb508ac94f31f9df77057b29",
        "0x150aace136535a374f05b5ee209b6a61396db1c0",
        "0x18e226459ccf0eec276514a4fd3b226d8961e4d1",
        "0x1b46970cfe6a271e884f636663c257a5a571fb2c",
        "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        "0x22132139bf7f3921b1cadeab931f4fbf7bf2bc9e",
        "0x26bff98f6f37c8d560684eaf2afd1149bf76633e",
        "0x28c6c06298d514db089934071355e5743bf21d60",
        "0x308a2a0712570daeea77c8ba9c27a32cdc4000d4",
        "0x32e11a20337ebc79abd0eeab2d91bafbd9591149",
        "0x38aaef3782910bdd9ea3566c839788af6ff9b200",
        "0x42a93a9f5cfda54716c414b6eaf07cf512f46ead",
        "0x43684d03d81d3a4c70da68febdd61029d426f042",
        "0x4976a4a02f38326660d17bf34b431dc6e2eb2327",
        "0x4aec0e98fc1fb55b9cc2faaa7a81acca42cb4e96",
        "0x4ed6cf63bd9c009d247ee51224fc1c7041f517f1",
        "0x4fdfe365436b5273a42f135c6a6244a20404271e",
        "0x56eddb7aa87536c09ccc2793473599fd21a8b17f",
        "0x5a1e5b56aa33c056ed7bb93b88b1774a456f6694",
        "0x5a52e96bacdabb82fd05763e25335261b270efcb",
        "0x6357e4bdaff733dfe8f50d12d07c03b3bed0884b",
        "0x6454ac71ca260f99cca99a3f4241dfda20cfa965",
        "0x756b86fd69914db92229c07c7393d7d9948fed33",
        "0x835678a611b28684005a5e2233695fb6cbbb0007",
        "0x8498fc7280668874a5da79e87ca0896f4f0d1196",
        "0x86523c87c8ec98c7539e2c58cd813ee9d1a08d96",
        "0x87433fec6f8d9df13d1e17c4b11364ecd2e93a51",
        "0x8a6f8404c9ea4c33502a3f6a4bf8e41ef5ca10ea",
        "0x8e609ac80f4324e499a6efd24f221a2caa868224",
        "0x9696f59e4d72e237be84ffd425dcad154bf96976",
        "0x98adef6f2ac8572ec48965509d69a8dd5e8bba9d",
        "0xa345dcb63f984ed1c6d1a8901e0cdbd13b2b4d19",
        "0xa64b436964e7415c0e70b9989a53e1fb9a90e726",
        "0xa7c0d36c4698981fab42a7d8c783674c6fe2592d",
        "0xa9fc92f6faf9f103fc81d17de3e8daadc888afff",
        "0xad354cfbaa4a8572dd6df021514a3931a8329ef5",
        "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",
        "0xc47b3342df38d747033b6041f54e4e5e300c8d18",
        "0xc8daf809c7d7c27dd62d006196d8901ba57e5eae",
        "0xd27b39cb25fed854f9fce3a4e451f96e62089e48",
        "0xdbeb6c856ef5a167f5e1acb9dff65adb33207d8b",
        "0xdbf28a152d79b2b98eecd229b412ee98d21ec3bc",
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
        "0xe1940f578743367f38d3f25c2d2d32d6636929b6",
        "0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055",
        "0xf16924b866e58ac916ba933d1f1034bcbbb1958c",
        "0xf1f8cb7633d3ca3fd06c084d18ca5491a85ae9b4",
        "0xf977814e90da44bfa03b6295a0616a897441acec",
        "0xfc8059c2fb22005ede8a86d388e3d0f536a4dd44"
      ],
      "mention": {
        "end": 40,
        "start": 33,
        "text": "Binance"
      },
      "owner": "Binance"
    }
  ],
  "id": "v2-p19",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "token_contract"
      },
      {
        "target": "entity:1",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:1",
        "value": "to"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "e27034402e6178774413f78171220fac662926b7fca2a806aa4b8888f4b3970e",
  "schema": {
    "columns": [
      {
        "column": "block_timestamp",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "from_address",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "to_owner",
        "relation": "labeled_token_transfers"
      },
      {
        "column": "token_owner",
        "relation": "labeled_token_transfers"
      }
    ],
    "relations": [
      "labeled_token_transfers"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "911012a96fb529d61aeb52ac7f4d9a0b72dc88b2f17f0bba15e1cdcd7a67ebe6"
}
```

Lý do tác giả: Two entity targets have different roles and independent identity sets.

Sample: 21 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "date",
      "2026-06-01"
    ],
    [
      "number",
      "4"
    ],
    [
      "number",
      "4"
    ]
  ],
  [
    [
      "date",
      "2026-06-02"
    ],
    [
      "number",
      "5"
    ],
    [
      "number",
      "5"
    ]
  ],
  [
    [
      "date",
      "2026-06-03"
    ],
    [
      "number",
      "5"
    ],
    [
      "number",
      "5"
    ]
  ],
  [
    [
      "date",
      "2026-06-04"
    ],
    [
      "number",
      "3"
    ],
    [
      "number",
      "3"
    ]
  ],
  [
    [
      "date",
      "2026-06-05"
    ],
    [
      "number",
      "2"
    ],
    [
      "number",
      "2"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Swaps the token identity and recipient endpoint constraints.

```sql
SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
COUNT(DISTINCT from_address) AS senders FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-06-01', DATE '2026-07-01')
WHERE to_owner='Chainlink' AND token_owner='Binance' GROUP BY day ORDER BY day
```

Review binding:

```json
{
  "annotation_sha256": "1160da03257d340ea13d65b8a56b67544405ddc173cc165c353c35a52ddec95b",
  "case_sha256": "6b5b95465da0183dd1a1a4f5f40d0c67dc4771b81bc38fc05e912f8128632555",
  "id": "v2-p19",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "e27034402e6178774413f78171220fac662926b7fca2a806aa4b8888f4b3970e",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "911012a96fb529d61aeb52ac7f4d9a0b72dc88b2f17f0bba15e1cdcd7a67ebe6",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________

## v2-p20 — ambiguous_property

For transfer events sent from 0xdac17f958d2ee523a2206206994597c13d831ec7 as an endpoint, return transferred token address, event count and distinct recipient count, ordered by token address; permit any token identity. Use June 2026 UTC, with July 1 excluded.

Case metadata (cũng được gắn hash review):

```json
{
  "categories": [
    "role_explicit_tether_event_sender"
  ],
  "difficulty": "medium",
  "empty_reason": null,
  "family_id": "t09a:role_explicit_tether_event_sender",
  "id": "v2-p20",
  "primary_group": "ambiguous_property",
  "property_focus": "address_role",
  "provenance": {
    "author": "codex-t09a",
    "author_type": "agent",
    "method": "independent_authoring"
  },
  "specifics": [
    "ambiguous_property"
  ],
  "subset": "entity",
  "window": {
    "end_date": "2026-07-01",
    "start_date": "2026-06-01"
  }
}
```

Intent: `role_explicit_tether_event_sender`. Property focus: `address_role`.

```sql
SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT to_address) AS recipients
FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-07-01') WHERE from_address='0xdac17f958d2ee523a2206206994597c13d831ec7'
GROUP BY token_address ORDER BY token_address
```

Annotation trực tiếp:

```json
{
  "classes": [],
  "entities": [
    {
      "address_scope": "explicit_address",
      "addresses": [
        "0xdac17f958d2ee523a2206206994597c13d831ec7"
      ],
      "mention": {
        "end": 72,
        "start": 30,
        "text": "0xdac17f958d2ee523a2206206994597c13d831ec7"
      },
      "owner": "Tether"
    }
  ],
  "id": "v2-p20",
  "properties": {
    "address_role": [
      {
        "target": "entity:0",
        "value": "endpoint"
      }
    ],
    "direction": [
      {
        "target": "entity:0",
        "value": "from"
      }
    ],
    "fact": "token_transfer"
  },
  "question_sha256": "d977693bb7436cd1f9a90550899890f15873a368cc4677a5c84ca2aaf95b923c",
  "schema": {
    "columns": [
      {
        "column": "from_address",
        "relation": "token_transfer_facts"
      },
      {
        "column": "to_address",
        "relation": "token_transfer_facts"
      },
      {
        "column": "token_address",
        "relation": "token_transfer_facts"
      }
    ],
    "relations": [
      "token_transfer_facts"
    ]
  },
  "schema_version": 2,
  "sql_sha256": "270a650f0b5679249b860828bc13f6db7aaba12f8e21ddfa8ce49543ae243d86"
}
```

Lý do tác giả: A token contract may be queried as an endpoint even when there are no matching sample events.

Sample: 2 rows; empty=False; zero/NULL aggregate=False; error=None.

Giải thích rỗng: Không có kết quả rỗng được ghi nhận.

Preview (giá trị có type tag):

```json
[
  [
    [
      "string",
      "0x548054687ef6c56c6d82e8269e5fd93d8b88fcb2"
    ],
    [
      "number",
      "5"
    ],
    [
      "number",
      "1"
    ]
  ],
  [
    [
      "string",
      "0x7346c3c1cecd42a52ecc7f871190a821ee1169ce"
    ],
    [
      "number",
      "1"
    ],
    [
      "number",
      "1"
    ]
  ]
]
```

Property contrast: phân biệt trên sample=True; Uses literal token identity instead of sender endpoint.

```sql
SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT to_address) AS recipients
FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-07-01') WHERE token_address='0xdac17f958d2ee523a2206206994597c13d831ec7'
GROUP BY token_address ORDER BY token_address
```

Review binding:

```json
{
  "annotation_sha256": "5762c2602a51b42eaf6ccf08bf7f81bcbf563978f17d66ff1d4dad5c6e1eedcf",
  "case_sha256": "9ef5e6547272dddbc5423c0da3834edfa782438337ffe20d8d7870201fdef0c0",
  "id": "v2-p20",
  "note": "Draft annotation; independent human review pending.",
  "question_sha256": "d977693bb7436cd1f9a90550899890f15873a368cc4677a5c84ca2aaf95b923c",
  "reviewed_at": null,
  "reviewer": null,
  "reviewer_kind": null,
  "schema_version": 2,
  "sql_sha256": "270a650f0b5679249b860828bc13f6db7aaba12f8e21ddfa8ce49543ae243d86",
  "status": "pending"
}
```

Nhận xét của người review: ____________________

Người review / thời điểm / quyết định: ____________________


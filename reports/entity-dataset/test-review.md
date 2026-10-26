# T05 — Hồ sơ review 100 câu test

Reviewer: Codex (agent semantic review). Human review: **còn chờ xác nhận**.

Test SHA-256: `2e2f63071718e045d4ca24cea8aecbdaf37c7749d4f33ce3e2d687cd1173c8ee`.

Review SHA-256: `05db653283352ffd157d9109bd9c07fb19b6aca3c13fb70d5186783120c38f32`.

Các ghi chú dưới đây là review của agent cho bản dataset có hash ở trên.
Kết quả chạy và rỗng/0 nằm trong [validation.md](validation.md) và [validation.json](validation.json).

## t35-001 — generic

How many Ethereum transactions were recorded during the first seven days of June 2026?

```sql
SELECT COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08')
```

Review: COUNT transaction rows; UTC half-open first-week window.

## t35-002 — generic

Count the successful Ethereum transactions in the first seven days of June 2026.

```sql
SELECT COUNTIF(is_success IS TRUE) AS successful_transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08')
```

Review: COUNTIF success TRUE, not all transactions.

## t35-003 — generic

How many failed Ethereum transactions occurred during the first seven days of June 2026?

```sql
SELECT COUNTIF(is_success IS FALSE) AS failed_transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08')
```

Review: COUNTIF success FALSE; NULL status is not failure.

## t35-004 — generic

What total wei value did transactions carry in the first seven days of June 2026?

```sql
SELECT COALESCE(SUM(value_wei), 0) AS total_value_wei FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08')
```

Review: SUM recorded value_wei, all statuses; not settled balance change.

## t35-005 — generic

How many Ethereum blocks fall within the first seven days of June 2026?

```sql
SELECT COUNT(*) AS block_count FROM `nl2sparql-thesis.nl2sparql_analytics.block_facts`(DATE '2026-06-01', DATE '2026-06-08')
```

Review: COUNT block facts, not transactions.

## t35-006 — generic

What was the average transaction count per block during the first seven days of June 2026?

```sql
SELECT AVG(transaction_count) AS average_transactions_per_block FROM `nl2sparql-thesis.nl2sparql_analytics.block_facts`(DATE '2026-06-01', DATE '2026-06-08')
```

Review: AVG transactions per block using block facts, not sampled transaction frequency.

## t35-007 — generic

How many token-transfer events occurred in the first seven days of June 2026?

```sql
SELECT COUNT(*) AS token_transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-06-08')
```

Review: COUNT log events; multiple logs per transaction remain multiple events.

## t35-008 — generic

Count token transfers with a usable normalized amount during the first seven days of June 2026.

```sql
SELECT COUNTIF(normalized_amount IS NOT NULL) AS normalized_transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-06-08')
```

Review: COUNT non-NULL normalized amounts, not SUM amounts.

## t35-028 — generic

How many Ethereum transactions were recorded during June 22 through June 30, 2026?

```sql
SELECT COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-22', DATE '2026-07-01')
```

Review: COUNT transaction rows; UTC half-open first-week window. Same reviewed intent in its explicit later UTC window.

## t35-029 — generic

Count the successful Ethereum transactions in June 22 through June 30, 2026.

```sql
SELECT COUNTIF(is_success IS TRUE) AS successful_transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-22', DATE '2026-07-01')
```

Review: COUNTIF success TRUE, not all transactions. Same reviewed intent in its explicit later UTC window.

## t35-030 — generic

How many failed Ethereum transactions occurred during June 22 through June 30, 2026?

```sql
SELECT COUNTIF(is_success IS FALSE) AS failed_transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-22', DATE '2026-07-01')
```

Review: COUNTIF success FALSE; NULL status is not failure. Same reviewed intent in its explicit later UTC window.

## t35-031 — generic

What total wei value did transactions carry in June 22 through June 30, 2026?

```sql
SELECT COALESCE(SUM(value_wei), 0) AS total_value_wei FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-22', DATE '2026-07-01')
```

Review: SUM recorded value_wei, all statuses; not settled balance change. Same reviewed intent in its explicit later UTC window.

## t35-032 — generic

How many Ethereum blocks fall within June 22 through June 30, 2026?

```sql
SELECT COUNT(*) AS block_count FROM `nl2sparql-thesis.nl2sparql_analytics.block_facts`(DATE '2026-06-22', DATE '2026-07-01')
```

Review: COUNT block facts, not transactions. Same reviewed intent in its explicit later UTC window.

## t35-033 — generic

What was the average transaction count per block during June 22 through June 30, 2026?

```sql
SELECT AVG(transaction_count) AS average_transactions_per_block FROM `nl2sparql-thesis.nl2sparql_analytics.block_facts`(DATE '2026-06-22', DATE '2026-07-01')
```

Review: AVG transactions per block using block facts, not sampled transaction frequency. Same reviewed intent in its explicit later UTC window.

## t35-034 — generic

How many token-transfer events occurred in June 22 through June 30, 2026?

```sql
SELECT COUNT(*) AS token_transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-22', DATE '2026-07-01')
```

Review: COUNT log events; multiple logs per transaction remain multiple events. Same reviewed intent in its explicit later UTC window.

## t35-039 — generic

Give the daily transaction totals for the first seven days of June 2026.

```sql
SELECT DATE(block_timestamp) AS activity_date, COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08') GROUP BY activity_date ORDER BY activity_date ASC
```

Review: Daily transaction counts; UTC DATE(timestamp); ascending date.

## t35-040 — generic

For each day in the first seven days of June 2026, how many transactions succeeded and failed?

```sql
SELECT DATE(block_timestamp) AS activity_date, COUNTIF(is_success IS TRUE) AS successful_count, COUNTIF(is_success IS FALSE) AS failed_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08') GROUP BY activity_date ORDER BY activity_date ASC
```

Review: Daily success/failure counts; neither bucket includes NULL status.

## t35-041 — generic

What were the average gas price and receipt gas used by day in the first seven days of June 2026?

```sql
SELECT DATE(block_timestamp) AS activity_date, AVG(gas_price_wei) AS average_gas_price_wei, AVG(receipt_gas_used) AS average_receipt_gas_used FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08') GROUP BY activity_date ORDER BY activity_date ASC
```

Review: Daily AVG of gas price in wei and receipt gas used; not total gas or fees.

## t35-042 — generic

Which ten block beneficiary addresses appeared most often during the first seven days of June 2026?

```sql
SELECT beneficiary_address AS beneficiary_address, COUNT(*) AS block_count FROM `nl2sparql-thesis.nl2sparql_analytics.block_facts`(DATE '2026-06-01', DATE '2026-06-08') WHERE beneficiary_address IS NOT NULL GROUP BY beneficiary_address ORDER BY block_count DESC, beneficiary_address ASC LIMIT 10
```

Review: Top 10 beneficiaries by block count; address tie-break; no validator-identity claim.

## t35-043 — generic

Summarize daily block count, gas used, and transaction count for the first seven days of June 2026.

```sql
SELECT DATE(block_timestamp) AS activity_date, COUNT(*) AS block_count, SUM(gas_used) AS total_gas_used, SUM(transaction_count) AS total_transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.block_facts`(DATE '2026-06-01', DATE '2026-06-08') GROUP BY activity_date ORDER BY activity_date ASC
```

Review: Independent block aggregates by UTC day; block transaction totals exceed sampled rows.

## t35-044 — generic

Which ten token addresses produced the most transfer events during the first seven days of June 2026?

```sql
SELECT token_address AS token_address, COUNT(*) AS transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-06-08') GROUP BY token_address ORDER BY transfer_count DESC, token_address ASC LIMIT 10
```

Review: Top 10 token contracts by event count; address tie-break.

## t35-045 — generic

Which ten token symbols moved the largest normalized amount during the first seven days of June 2026?

```sql
SELECT token_symbol AS token_symbol, SUM(normalized_amount) AS total_normalized_amount FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-06-08') WHERE normalized_amount IS NOT NULL AND token_symbol IS NOT NULL GROUP BY token_symbol ORDER BY total_normalized_amount DESC, token_symbol ASC LIMIT 10
```

Review: Top token symbols by normalized units; symbol collisions grouped deliberately; not monetary values.

## t35-046 — generic

Compare ERC-20, ERC-721, and other transfer-event counts in the first seven days of June 2026.

```sql
SELECT CASE WHEN is_erc721 IS TRUE THEN 'erc721' WHEN is_erc20 IS TRUE THEN 'erc20' ELSE 'other_or_unknown' END AS token_standard, COUNT(*) AS transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-06-08') GROUP BY token_standard ORDER BY token_standard ASC
```

Review: ERC721 precedence, then ERC20, else other/unknown including NULL flags.

## t35-047 — generic

Which ten addresses sent the most token-transfer events during the first seven days of June 2026?

```sql
SELECT from_address AS sender_address, COUNT(*) AS transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-06-08') WHERE from_address IS NOT NULL GROUP BY from_address ORDER BY transfer_count DESC, sender_address ASC LIMIT 10
```

Review: Log from_address, not enclosing transaction sender; event count; address tie-break.

## t35-048 — generic

Which ten addresses received the most token-transfer events during the first seven days of June 2026?

```sql
SELECT to_address AS recipient_address, COUNT(*) AS transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-06-08') WHERE to_address IS NOT NULL GROUP BY to_address ORDER BY transfer_count DESC, recipient_address ASC LIMIT 10
```

Review: Log to_address, not enclosing transaction recipient; event count; address tie-break.

## t35-049 — generic

Break down transaction totals by transaction type for the first seven days of June 2026.

```sql
SELECT transaction_type AS transaction_type, COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08') GROUP BY transaction_type ORDER BY transaction_count DESC, transaction_type ASC
```

Review: Count by transaction_type; NULL type retained as a group.

## t35-050 — generic

Which ten created contract addresses were associated with the highest transaction value in the first seven days of June 2026?

```sql
SELECT receipt_contract_address AS created_contract_address, value_wei AS transaction_value_wei FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08') WHERE receipt_contract_address IS NOT NULL ORDER BY transaction_value_wei DESC, created_contract_address ASC LIMIT 10
```

Review: Creation receipt addresses ranked by attached transaction value; not current balance.

## t35-051 — generic

For labeled recipient addresses, which concept classes received the most transactions during the first seven days of June 2026?

```sql
SELECT labels.concept_class AS recipient_concept_class, COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08') AS tx JOIN `nl2sparql-thesis.nl2sparql_analytics.entity_labels_v1` AS labels ON tx.to_address = labels.address GROUP BY recipient_concept_class ORDER BY transaction_count DESC, recipient_concept_class ASC LIMIT 10
```

Review: All labeled recipients, not only protocols; wording corrected at T05; SQL unchanged.

## t35-052 — generic

Which ten sender addresses initiated the most transactions during June 8 through June 14, 2026?

```sql
SELECT from_address AS sender_address, COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-08', DATE '2026-06-15') GROUP BY from_address ORDER BY transaction_count DESC, sender_address ASC LIMIT 10
```

Review: Top 10 outer senders by transaction count; address tie-break.

## t35-053 — generic

Which ten recipient addresses received the most transactions during June 8 through June 14, 2026?

```sql
SELECT to_address AS recipient_address, COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-08', DATE '2026-06-15') WHERE to_address IS NOT NULL GROUP BY to_address ORDER BY transaction_count DESC, recipient_address ASC LIMIT 10
```

Review: Top 10 non-NULL outer recipients by count; excludes contract-creation NULL recipients.

## t35-070 — generic

For each day in June 15 through June 21, 2026, how many transactions succeeded and failed?

```sql
SELECT DATE(block_timestamp) AS activity_date, COUNTIF(is_success IS TRUE) AS successful_count, COUNTIF(is_success IS FALSE) AS failed_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-15', DATE '2026-06-22') GROUP BY activity_date ORDER BY activity_date ASC
```

Review: Daily success/failure counts; neither bucket includes NULL status. Same reviewed intent in its explicit later UTC window.

## t35-080 — generic

Which ten created contract addresses were associated with the highest transaction value in June 15 through June 21, 2026?

```sql
SELECT receipt_contract_address AS created_contract_address, value_wei AS transaction_value_wei FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-15', DATE '2026-06-22') WHERE receipt_contract_address IS NOT NULL ORDER BY transaction_value_wei DESC, created_contract_address ASC LIMIT 10
```

Review: Creation receipt addresses ranked by attached transaction value; not current balance. Same reviewed intent in its explicit later UTC window.

## t35-084 — generic

Give the daily transaction totals for June 22 through June 30, 2026.

```sql
SELECT DATE(block_timestamp) AS activity_date, COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-22', DATE '2026-07-01') GROUP BY activity_date ORDER BY activity_date ASC
```

Review: Daily transaction counts; UTC DATE(timestamp); ascending date. Same reviewed intent in its explicit later UTC window.

## t35-086 — generic

What were the average gas price and receipt gas used by day in June 22 through June 30, 2026?

```sql
SELECT DATE(block_timestamp) AS activity_date, AVG(gas_price_wei) AS average_gas_price_wei, AVG(receipt_gas_used) AS average_receipt_gas_used FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-22', DATE '2026-07-01') GROUP BY activity_date ORDER BY activity_date ASC
```

Review: Daily AVG of gas price in wei and receipt gas used; not total gas or fees. Same reviewed intent in its explicit later UTC window.

## t35-087 — generic

Which ten block beneficiary addresses appeared most often during June 22 through June 30, 2026?

```sql
SELECT beneficiary_address AS beneficiary_address, COUNT(*) AS block_count FROM `nl2sparql-thesis.nl2sparql_analytics.block_facts`(DATE '2026-06-22', DATE '2026-07-01') WHERE beneficiary_address IS NOT NULL GROUP BY beneficiary_address ORDER BY block_count DESC, beneficiary_address ASC LIMIT 10
```

Review: Top 10 beneficiaries by block count; address tie-break; no validator-identity claim. Same reviewed intent in its explicit later UTC window.

## t35-088 — generic

Summarize daily block count, gas used, and transaction count for June 22 through June 30, 2026.

```sql
SELECT DATE(block_timestamp) AS activity_date, COUNT(*) AS block_count, SUM(gas_used) AS total_gas_used, SUM(transaction_count) AS total_transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.block_facts`(DATE '2026-06-22', DATE '2026-07-01') GROUP BY activity_date ORDER BY activity_date ASC
```

Review: Independent block aggregates by UTC day; block transaction totals exceed sampled rows. Same reviewed intent in its explicit later UTC window.

## t35-089 — generic

Which ten token addresses produced the most transfer events during June 22 through June 30, 2026?

```sql
SELECT token_address AS token_address, COUNT(*) AS transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-22', DATE '2026-07-01') GROUP BY token_address ORDER BY transfer_count DESC, token_address ASC LIMIT 10
```

Review: Top 10 token contracts by event count; address tie-break. Same reviewed intent in its explicit later UTC window.

## t35-090 — generic

Which ten token symbols moved the largest normalized amount during June 22 through June 30, 2026?

```sql
SELECT token_symbol AS token_symbol, SUM(normalized_amount) AS total_normalized_amount FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-22', DATE '2026-07-01') WHERE normalized_amount IS NOT NULL AND token_symbol IS NOT NULL GROUP BY token_symbol ORDER BY total_normalized_amount DESC, token_symbol ASC LIMIT 10
```

Review: Top token symbols by normalized units; symbol collisions grouped deliberately; not monetary values. Same reviewed intent in its explicit later UTC window.

## t35-091 — generic

Compare ERC-20, ERC-721, and other transfer-event counts in June 22 through June 30, 2026.

```sql
SELECT CASE WHEN is_erc721 IS TRUE THEN 'erc721' WHEN is_erc20 IS TRUE THEN 'erc20' ELSE 'other_or_unknown' END AS token_standard, COUNT(*) AS transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-22', DATE '2026-07-01') GROUP BY token_standard ORDER BY token_standard ASC
```

Review: ERC721 precedence, then ERC20, else other/unknown including NULL flags. Same reviewed intent in its explicit later UTC window.

## t35-093 — generic

Which ten addresses received the most token-transfer events during June 22 through June 30, 2026?

```sql
SELECT to_address AS recipient_address, COUNT(*) AS transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-22', DATE '2026-07-01') WHERE to_address IS NOT NULL GROUP BY to_address ORDER BY transfer_count DESC, recipient_address ASC LIMIT 10
```

Review: Log to_address, not enclosing transaction recipient; event count; address tie-break. Same reviewed intent in its explicit later UTC window.

## t35-094 — generic

Break down transaction totals by transaction type for June 22 through June 30, 2026.

```sql
SELECT transaction_type AS transaction_type, COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-22', DATE '2026-07-01') GROUP BY transaction_type ORDER BY transaction_count DESC, transaction_type ASC
```

Review: Count by transaction_type; NULL type retained as a group. Same reviewed intent in its explicit later UTC window.

## t35-096 — generic

For labeled recipient addresses, which concept classes received the most transactions during June 22 through June 30, 2026?

```sql
SELECT labels.concept_class AS recipient_concept_class, COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-22', DATE '2026-07-01') AS tx JOIN `nl2sparql-thesis.nl2sparql_analytics.entity_labels_v1` AS labels ON tx.to_address = labels.address GROUP BY recipient_concept_class ORDER BY transaction_count DESC, recipient_concept_class ASC LIMIT 10
```

Review: All labeled recipients, not only protocols; wording corrected at T05; SQL unchanged. Same reviewed intent in its explicit later UTC window.

## t35-098 — generic

For each day in the first seven days of June 2026, compare observed transaction rows with transaction totals independently aggregated from block facts.

```sql
WITH tx_daily AS (SELECT DATE(block_timestamp) AS activity_date, COUNT(*) AS observed_transaction_rows FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08') GROUP BY activity_date), block_daily AS (SELECT DATE(block_timestamp) AS activity_date, SUM(transaction_count) AS joined_block_transaction_total FROM `nl2sparql-thesis.nl2sparql_analytics.block_facts`(DATE '2026-06-01', DATE '2026-06-08') GROUP BY activity_date) SELECT tx_daily.activity_date AS activity_date, tx_daily.observed_transaction_rows AS observed_transaction_rows, block_daily.joined_block_transaction_total AS joined_block_transaction_total FROM tx_daily JOIN block_daily USING (activity_date) ORDER BY activity_date ASC
```

Review: Independent daily tx/block aggregates joined on UTC date; no row-multiplying fact join.

## t35-099 — generic

During the first seven days of June 2026, compare transaction counts and wei value for ERC-20, ERC-721, and other recipient contracts.

```sql
SELECT CASE WHEN contracts.is_erc721 IS TRUE THEN 'erc721' WHEN contracts.is_erc20 IS TRUE THEN 'erc20' ELSE 'other_or_unknown' END AS recipient_contract_class, COUNT(*) AS transaction_count, COALESCE(SUM(tx.value_wei), 0) AS total_value_wei FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08') AS tx JOIN `nl2sparql-thesis.nl2sparql_analytics.contract_dimension`(DATE '2026-06-08') AS contracts ON tx.to_address = contracts.address GROUP BY recipient_contract_class ORDER BY recipient_contract_class ASC
```

Review: Recipient contract dimension at window end; ERC721 precedence; count and recorded wei.

## t35-100 — generic

Which ten transactions had the most token-transfer events during the first seven days of June 2026? Break event-count ties by the greatest native wei value, then transaction hash.

```sql
WITH transfer_counts AS (SELECT transaction_hash AS transaction_hash, block_number AS block_number, block_hash AS block_hash, COUNT(*) AS transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-06-08') GROUP BY transaction_hash, block_number, block_hash) SELECT tx.transaction_hash AS transaction_hash, tx.value_wei AS native_value_wei, transfer_counts.transfer_count AS transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08') AS tx JOIN transfer_counts ON tx.transaction_hash = transfer_counts.transaction_hash AND tx.block_number = transfer_counts.block_number AND tx.block_hash = transfer_counts.block_hash ORDER BY transfer_count DESC, native_value_wei DESC, transaction_hash ASC LIMIT 10
```

Review: Event-count priority, then native wei, then hash; wording corrected at T05; composite block/hash join.

## t35-101 — generic

Which labeled sender concept classes originated the greatest total wei value during the first seven days of June 2026?

```sql
SELECT labels.concept_class AS sender_concept_class, COUNT(*) AS transaction_count, COALESCE(SUM(tx.value_wei), 0) AS total_value_wei FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08') AS tx JOIN `nl2sparql-thesis.nl2sparql_analytics.entity_labels_v1` AS labels ON tx.from_address = labels.address GROUP BY sender_concept_class ORDER BY total_value_wei DESC, sender_concept_class ASC LIMIT 10
```

Review: Sender class, not recipient; order by total recorded wei; all statuses.

## t35-102 — generic

For labeled recipient owners, which token symbols delivered the largest normalized amounts during the first seven days of June 2026?

```sql
SELECT labels.owner AS recipient_owner, transfers.token_symbol AS token_symbol, SUM(transfers.normalized_amount) AS total_normalized_amount FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-01', DATE '2026-06-08') AS transfers JOIN `nl2sparql-thesis.nl2sparql_analytics.entity_labels_v1` AS labels ON transfers.to_address = labels.address WHERE transfers.normalized_amount IS NOT NULL AND transfers.token_symbol IS NOT NULL GROUP BY recipient_owner, token_symbol ORDER BY total_normalized_amount DESC, recipient_owner ASC, token_symbol ASC LIMIT 20
```

Review: Recipient owner and token symbol; valid normalized units; not dollar values.

## t35-103 — generic

How did transaction count and total wei value change between the early and late portions of June 8 through June 14, 2026?

```sql
WITH period_totals AS (SELECT CASE WHEN block_timestamp < TIMESTAMP(DATE '2026-06-11') THEN 'early' ELSE 'late' END AS period_name, COUNT(*) AS transaction_count, COALESCE(SUM(value_wei), 0) AS total_value_wei FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-08', DATE '2026-06-15') GROUP BY period_name) SELECT period_name AS period_name, transaction_count AS transaction_count, total_value_wei AS total_value_wei FROM period_totals ORDER BY period_name ASC
```

Review: Early June 8-10; late June 11-14; threshold June 11 UTC; count and recorded wei.

## t35-119 — generic

Which labeled sender concept classes originated the greatest total wei value during June 22 through June 30, 2026?

```sql
SELECT labels.concept_class AS sender_concept_class, COUNT(*) AS transaction_count, COALESCE(SUM(tx.value_wei), 0) AS total_value_wei FROM `nl2sparql-thesis.nl2sparql_analytics.transaction_facts`(DATE '2026-06-22', DATE '2026-07-01') AS tx JOIN `nl2sparql-thesis.nl2sparql_analytics.entity_labels_v1` AS labels ON tx.from_address = labels.address GROUP BY sender_concept_class ORDER BY total_value_wei DESC, sender_concept_class ASC LIMIT 10
```

Review: Sender class, not recipient; order by total recorded wei; all statuses. Same reviewed intent in its explicit later UTC window.

## t35-120 — generic

For labeled recipient owners, which token symbols delivered the largest normalized amounts during June 22 through June 30, 2026?

```sql
SELECT labels.owner AS recipient_owner, transfers.token_symbol AS token_symbol, SUM(transfers.normalized_amount) AS total_normalized_amount FROM `nl2sparql-thesis.nl2sparql_analytics.token_transfer_facts`(DATE '2026-06-22', DATE '2026-07-01') AS transfers JOIN `nl2sparql-thesis.nl2sparql_analytics.entity_labels_v1` AS labels ON transfers.to_address = labels.address WHERE transfers.normalized_amount IS NOT NULL AND transfers.token_symbol IS NOT NULL GROUP BY recipient_owner, token_symbol ORDER BY total_normalized_amount DESC, recipient_owner ASC, token_symbol ASC LIMIT 20
```

Review: Recipient owner and token symbol; valid normalized units; not dollar values. Same reviewed intent in its explicit later UTC window.

## t05-e001 — entity

How many transactions were sent from all Binance-labeled addresses? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE from_owner = 'Binance'
```

Review: All labeled Binance endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `multi_address`.

## t05-e002 — entity

Count transactions received across the labeled wallets of Bitfinex. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'Bitfinex'
```

Review: All labeled Bitfinex endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `multi_address`.

## t05-e003 — entity

How many token-transfer log events have a Bitget address as their sender? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01')
WHERE from_owner = 'Bitget'
```

Review: All labeled Bitget endpoints; token log endpoints, independent of the enclosing transaction.

Nhãn: `ambiguous_property`, `multi_address`.

## t05-e004 — entity

Across every labeled Bitkub address, what is the incoming transaction count? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'Bitkub'
```

Review: All labeled Bitkub endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `multi_address`.

## t05-e005 — entity

How many distinct transaction rows involve Bitmex as sender, recipient, or both? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE from_owner = 'Bitmex' OR to_owner = 'Bitmex'
```

Review: All labeled Bitmex endpoints; outer transaction endpoints, all receipt statuses. OR counts an internal transaction once.

Nhãn: `ambiguous_property`, `multi_address`.

## t05-e006 — entity

Count token-transfer events received by any address belonging to Bitstamp. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'Bitstamp'
```

Review: All labeled Bitstamp endpoints; token log endpoints, independent of the enclosing transaction.

Nhãn: `ambiguous_property`, `multi_address`.

## t05-e007 — entity

What is the transaction count with a labeled Bitvavo address on the sending side? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE from_owner = 'Bitvavo'
```

Review: All labeled Bitvavo endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `multi_address`.

## t05-e008 — entity

Taking all Bybit wallets together, how many transactions did they send? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE from_owner = 'Bybit'
```

Review: All labeled Bybit endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `multi_address`.

## t05-e009 — entity

How many transactions name any CoinEx wallet as recipient? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'CoinEx'
```

Review: All labeled CoinEx endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `multi_address`.

## t05-e010 — entity

Count incoming transactions for Crypto.com across all of its labeled accounts. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'Crypto-com'
```

Review: All labeled Crypto-com endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `alias`, `multi_address`.

## t05-e011 — entity

How many transactions target the labeled Curve Finance contracts? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'Curve DEX'
```

Review: All labeled Curve DEX endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `alias`, `multi_address`.

## t05-e012 — entity

Count outgoing token-transfer log events across Deribit wallets. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01')
WHERE from_owner = 'Deribit'
```

Review: All labeled Deribit endpoints; token log endpoints, independent of the enclosing transaction.

Nhãn: `ambiguous_property`, `multi_address`.

## t05-e013 — entity

Give the number of transactions touching Gate.io on either endpoint; count each row once. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE from_owner = 'Gate.io' OR to_owner = 'Gate.io'
```

Review: All labeled Gate.io endpoints; outer transaction endpoints, all receipt statuses. OR counts an internal transaction once.

Nhãn: `ambiguous_property`, `multi_address`.

## t05-e014 — entity

What number of transactions were addressed to the labeled Gauntlet vaults? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'Gauntlet'
```

Review: All labeled Gauntlet endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `multi_address`.

## t05-e015 — entity

Count transactions originating at any of the known Gemini addresses. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE from_owner = 'Gemini'
```

Review: All labeled Gemini endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `multi_address`.

## t05-e016 — entity

How many transactions were received by the exchange Huobi Global across its labeled wallets? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'HTX'
```

Review: All labeled HTX endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `alias`, `multi_address`.

## t05-e017 — entity

How many token-transfer events were credited to HashKey addresses? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'HashKey Exchange'
```

Review: All labeled HashKey Exchange endpoints; token log endpoints, independent of the enclosing transaction.

Nhãn: `alias`, `ambiguous_property`, `multi_address`.

## t05-e018 — entity

Count the transactions sent by Indodax, combining every labeled address. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE from_owner = 'Indodax'
```

Review: All labeled Indodax endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `multi_address`.

## t05-e019 — entity

What is the total number of transactions received across Korbit accounts? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'Korbit'
```

Review: All labeled Korbit endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `multi_address`.

## t05-e020 — entity

Count transfer-log events whose recipient is one of the labeled KuCoin wallets. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'KuCoin'
```

Review: All labeled KuCoin endpoints; token log endpoints, independent of the enclosing transaction.

Nhãn: `ambiguous_property`, `multi_address`.

## t05-e021 — entity

How many transactions reached MEXC when all labeled recipient addresses are included? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'MEXC'
```

Review: All labeled MEXC endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `multi_address`.

## t05-e022 — entity

Across all Nexo-labeled addresses, count the outgoing transactions. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE from_owner = 'Nexo'
```

Review: All labeled Nexo endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `multi_address`.

## t05-e023 — entity

How many token-transfer events have an OKEx wallet in the recipient field? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'OKX'
```

Review: All labeled OKX endpoints; token log endpoints, independent of the enclosing transaction.

Nhãn: `alias`, `ambiguous_property`, `multi_address`.

## t05-e024 — entity

Count transaction rows with OSL on at least one endpoint, including internal transfers only once. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE from_owner = 'OSL HK' OR to_owner = 'OSL HK'
```

Review: All labeled OSL HK endpoints; outer transaction endpoints, all receipt statuses. OR counts an internal transaction once.

Nhãn: `alias`, `ambiguous_property`, `multi_address`.

## t05-e025 — entity

How many transactions were directed to the contracts labeled OP Bridge? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'Optimism Bridge'
```

Review: All labeled Optimism Bridge endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `alias`, `multi_address`.

## t05-e026 — entity

Count transfer events sent by the complete set of labeled Phemex accounts. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01')
WHERE from_owner = 'Phemex'
```

Review: All labeled Phemex endpoints; token log endpoints, independent of the enclosing transaction.

Nhãn: `ambiguous_property`, `multi_address`.

## t05-e027 — entity

What is the incoming transaction count for Poloniex across its known wallets? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'Poloniex'
```

Review: All labeled Poloniex endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `multi_address`.

## t05-e028 — entity

How many transactions have a Sentora-labeled vault as recipient? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'Sentora'
```

Review: All labeled Sentora endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `multi_address`.

## t05-e029 — entity

How many transfer-log events originated from all SwissBorg addresses combined? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01')
WHERE from_owner = 'SwissBorg'
```

Review: All labeled SwissBorg endpoints; token log endpoints, independent of the enclosing transaction.

Nhãn: `ambiguous_property`, `multi_address`.

## t05-e030 — entity

Count transactions received by the labeled Uni V2 contracts, across all addresses. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'Uniswap V2'
```

Review: All labeled Uniswap V2 endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `alias`, `multi_address`.

## t05-e031 — entity

How many token-transfer events were received across the contracts known as Uni V3? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'Uniswap V3'
```

Review: All labeled Uniswap V3 endpoints; token log endpoints, independent of the enclosing transaction.

Nhãn: `alias`, `ambiguous_property`, `multi_address`.

## t05-e032 — entity

How many transactions target any labeled Uni V4 address? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'Uniswap V4'
```

Review: All labeled Uniswap V4 endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `alias`, `multi_address`.

## t05-e033 — entity

Count transactions delivered to VALR using every labeled recipient address. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01')
WHERE to_owner = 'VALR'
```

Review: All labeled VALR endpoints; outer transaction endpoints, all receipt statuses.

Nhãn: `multi_address`.

## t05-e034 — entity

What number of token-transfer log events were sent by all WEEX wallets? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS event_count
FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01')
WHERE from_owner = 'WEEX'
```

Review: All labeled WEEX endpoints; token log endpoints, independent of the enclosing transaction.

Nhãn: `ambiguous_property`, `multi_address`.

## t05-e035 — entity

How many transactions were received by TC? Interpret TC as the mixer service, including its router, not the TORN token. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01') WHERE to_owner = 'Tornado Cash'
```

Review: TC resolves to the service owner; only router activity is observed. Not a multi-address witness.

Nhãn: `alias`.

## t05-e036 — entity

Count transfer events of the TORN token, irrespective of who sent or received them. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01') WHERE token_owner = 'Tornado Cash Token'
```

Review: Filter token contract owner, not service endpoints or the transaction sender.

Nhãn: `alias`, `ambiguous_property`.

## t05-e037 — entity

How many token-transfer events were sent by BNB exchange, counting every log event rather than distinct transactions? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01') WHERE from_owner = 'Binance'
```

Review: BNB exchange maps to Binance, not the BNB token; multiple logs remain multiple events.

Nhãn: `alias`, `ambiguous_property`.

## t05-e038 — entity

Count the USDT transfer-log events across all senders and recipients. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01') WHERE token_owner = 'Tether'
```

Review: USDT maps to Tether; use token_owner, not from_owner or to_owner.

Nhãn: `alias`, `ambiguous_property`.

## t05-e039 — entity

For every centralized exchange owner, how many transactions were received across its labeled addresses? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT to_owner AS owner, COUNT(*) AS event_count FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01') WHERE to_category = 'exchange' GROUP BY owner ORDER BY event_count DESC, owner
```

Review: All owners of category exchange; include all labeled address roles; omit owners with no matching rows.

Nhãn: `class_level`.

## t05-e040 — entity

Across all DEXes, count outgoing token-transfer log events per owner. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT from_owner AS owner, COUNT(*) AS event_count FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01') WHERE from_category = 'dex' GROUP BY owner ORDER BY event_count DESC, owner
```

Review: All owners of category dex; include all labeled address roles; omit owners with no matching rows.

Nhãn: `class_level`.

## t05-e041 — entity

For each labeled mixer service, count received transactions; include routers and pools. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT to_owner AS owner, COUNT(*) AS event_count FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01') WHERE to_category = 'mixer' GROUP BY owner ORDER BY event_count DESC, owner
```

Review: All owners of category mixer; include all labeled address roles; omit owners with no matching rows.

Nhãn: `class_level`.

## t05-e042 — entity

Which bridge owners received transactions, and how many did each receive? Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT to_owner AS owner, COUNT(*) AS event_count FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01') WHERE to_category = 'bridge' GROUP BY owner ORDER BY event_count DESC, owner
```

Review: All owners of category bridge; include all labeled address roles; omit owners with no matching rows.

Nhãn: `class_level`.

## t05-e043 — entity

For all lending protocol owners with incoming transactions, report the transaction count per owner. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT to_owner AS owner, COUNT(*) AS event_count FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01') WHERE to_category = 'lending' GROUP BY owner ORDER BY event_count DESC, owner
```

Review: All owners of category lending; include all labeled address roles; omit owners with no matching rows.

Nhãn: `class_level`.

## t05-e044 — entity

Count direct transactions from any centralized exchange address to any DEX contract, grouped by sender owner and recipient owner. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT from_owner, to_owner, COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01') WHERE from_category = 'exchange' AND to_category = 'dex' GROUP BY from_owner, to_owner ORDER BY transaction_count DESC, from_owner, to_owner
```

Review: Directed class-to-class outer transactions; no multi-hop or transfer-log inference. Known empty local result retained as a negative control.

Nhãn: `ambiguous_property`, `class_level`.

Kết quả rỗng local: No direct outer transaction from an exchange-labeled sender to a DEX-labeled recipient is observed in this local sample. Both classes are individually active; this does not imply absence of exchange/DEX activity or token-transfer paths.

## t05-e045 — entity

For transactions from BNB exchange into SwissBorg, how many rows are there? Count the outer transaction, regardless of token-transfer logs. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01') WHERE from_owner = 'Binance' AND to_owner = 'SwissBorg'
```

Review: BNB exchange resolves to Binance, the sender, SwissBorg recipient. Token events in those transactions are not counted.

Nhãn: `alias`, `ambiguous_property`.

## t05-e046 — entity

In transactions sent by BNB exchange, how many token-transfer events were received by SwissBorg? The log recipient, not the transaction recipient, must be SwissBorg. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS transfer_count FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01') AS transfers JOIN `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01') AS tx ON transfers.transaction_hash = tx.transaction_hash AND transfers.block_number = tx.block_number AND transfers.block_hash = tx.block_hash WHERE tx.from_owner = 'Binance' AND transfers.to_owner = 'SwissBorg'
```

Review: Composite hash/number/block-hash join; tx.from_owner and transfers.to_owner are distinct predicates.

Nhãn: `alias`, `ambiguous_property`.

## t05-e047 — entity

Count successful transactions sent to Uniswap V3 contracts, excluding transactions that only transfer the UNI governance token to another recipient. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01') WHERE to_owner = 'Uniswap V3' AND is_success IS TRUE
```

Review: Successful outer transactions to the protocol endpoints; governance token transfers alone do not qualify.

Nhãn: `ambiguous_property`.

## t05-e048 — entity

Count transactions involving the Huobi Global exchange on either endpoint, with each internal transaction counted once. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01') WHERE from_owner = 'HTX' OR to_owner = 'HTX'
```

Review: Either endpoint uses OR. Huobi Global is the unambiguous exchange alias; bare Huobi also names a token.

Nhãn: `alias`, `ambiguous_property`.

## t05-e049 — entity

How many direct transactions went between Bybit and Bitkub in either direction? Include both orientations exactly once. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT COUNT(*) AS transaction_count FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_transactions`(DATE '2026-05-31', DATE '2026-07-01') WHERE (from_owner = 'Bybit' AND to_owner = 'Bitkub') OR (from_owner = 'Bitkub' AND to_owner = 'Bybit')
```

Review: Union of the two directed owner pairs; not any transaction touching either owner.

Nhãn: `ambiguous_property`.

## t05-e050 — entity

Show the 20 most recent token-transfer log events sent by TC, the mixer service. Return the transaction hash, log index, token address, and recipient address. Use the local sample for UTC [2026-05-31, 2026-07-01).

```sql
SELECT transaction_hash, log_index, token_address, to_address FROM `nl2sparql-thesis.nl2sparql_analytics.labeled_token_transfers`(DATE '2026-05-31', DATE '2026-07-01') WHERE from_owner = 'Tornado Cash' ORDER BY block_timestamp DESC, transaction_hash, log_index LIMIT 20
```

Review: Service log sender, not TORN token contract; an empty list is valid for this sample.

Nhãn: `alias`, `ambiguous_property`.

Kết quả rỗng local: No token-transfer endpoints labeled Tornado Cash occur in the local sample; observed service activity is router transactions only.

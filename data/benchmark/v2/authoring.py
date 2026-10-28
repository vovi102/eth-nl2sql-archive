"""T09A handwritten question/SQL/semantic specifications, independent of predictions.

This file only packages the records below. It never inspects development
questions/SQL, generation outputs, a linker, or the annotation bootstrapper.
The manifest helper reads development split bytes only to pin their hashes.
Schema columns and semantic properties are declared by the author separately
from SQL; the normal validators subsequently compare these declarations to SQL.
Run from the repository root with `.venv/bin/python data/benchmark/v2/authoring.py`.
Do not run after freezing. All human review records start pending.
"""

# ruff: noqa: E501 -- authored question/SQL strings retain their literal bytes.

import json
import re
from pathlib import Path

from eth_nl2sql.config import DICTIONARY_DIR, read_jsonl, write_json, write_jsonl
from eth_nl2sql.data.annotations import pending_review, text_digest
from eth_nl2sql.data.benchmark import draft_manifest
from eth_nl2sql.linking.dictionary import load_dictionary, owner_id

DIRECTORY = Path(__file__).resolve().parent
D = load_dictionary(DICTIONARY_DIR)
P = "nl2sparql-thesis.nl2sparql_analytics"
W = "DATE '2026-06-01', DATE '2026-07-01'"
TX = f"`{P}.transaction_facts`({W})"
LT = f"`{P}.labeled_transactions`({W})"
TT = f"`{P}.token_transfer_facts`({W})"
LL = f"`{P}.labeled_token_transfers`({W})"
BL = f"`{P}.block_facts`({W})"
CD = f"`{P}.contract_dimension`(DATE '2026-07-01')"
TD = f"`{P}.token_dimension`"
EL = f"`{P}.entity_labels_v1`"
cases, annotations, notes, contrasts = [], [], [], []
EMPTY_REASONS = {
    "v2-a17": "Sample has no token events sent from the pinned Tornado Cash endpoint set. "
    "Legacy router activity is not evidence for these known pool endpoints; this sampled absence "
    "does not establish full-snapshot absence. Recheck in T09B.",
    "v2-a20": "Sample has no token events received by the pinned Tornado Cash endpoint set. "
    "The service alias is well-defined, but legacy sample selection does not establish pool "
    "coverage. Recheck the activity bounds on the full snapshot in T09B.",
    "v2-c13": "The labeled MixerAccount class has no incoming token events in this sample. "
    "Membership remains the full pinned dictionary set; class coverage and the empty answer "
    "require full-snapshot review in T09B.",
    "v2-c14": "No sampled token event satisfies both labeled lending sender and labeled exchange "
    "recipient predicates. Neither class membership is pruned to observed rows. Recheck the "
    "ordered class-pair query on the full snapshot in T09B.",
    "v2-p04": "No sampled outer transaction has Binance sender and OKX recipient; the reversed "
    "owner-pair contrast is also empty. The sample cannot discriminate this direction case. "
    "Retain the intended pair and require a full-snapshot witness in T09B.",
    "v2-p13": "No sampled token event has OKX recipient inside a Binance-sent outer transaction. "
    "The event-sender contrast is also empty, so this sample does not verify the cross-fact "
    "property distinction. Recheck the join and witness on the full snapshot in T09B.",
    "v2-p14": "No sampled USDT event joins a failed outer transaction. This is a deliberate "
    "negative control: reverted EVM transactions normally do not retain transfer logs. The "
    "successful-transaction contrast is nonempty; full-snapshot integrity review is still pending.",
}


def add(
    key,
    group,
    intent,
    question,
    sql,
    schema,
    *,
    fact=None,
    entities=(),
    classes=(),
    focus=None,
    difficulty="medium",
    note,
    contrast=None,
):
    """Mechanical serialization of explicit author declarations, without SQL inference."""
    question = question + " Use June 2026 UTC, with July 1 excluded."
    sql = sql.strip()
    case_id = f"v2-{key}"

    def mention(text):
        matches = list(re.finditer(r"(?<!\w)" + re.escape(text) + r"(?!\w)", question))
        assert len(matches) == 1, (case_id, text)
        start = matches[0].start()
        return {"text": text, "start": start, "end": start + len(text)}

    es, cs, directions, roles = [], [], [], []
    specifics = set() if group == "generic" else {group}
    for text, owner, direction, role in entities:
        explicit = text.startswith("0x")
        target = D.by_id[owner_id(owner)]
        es.append(
            {
                "mention": mention(text),
                "owner": owner,
                "addresses": [text.lower()] if explicit else list(target.addresses),
                "address_scope": "explicit_address" if explicit else "known_owner_addresses",
            }
        )
        reference = f"entity:{len(es) - 1}"
        if direction:
            directions.append({"target": reference, "value": direction})
        if role:
            roles.append({"target": reference, "value": role})
        if not explicit and len(target.addresses) > 1 and role == "endpoint":
            specifics.add("multi_address")
        if not explicit and text.casefold() != owner.casefold():
            specifics.add("alias")
    for text, category, direction in classes:
        target = D.by_id[f"concept:{category}"]
        concept_class = target.concept_classes[0]
        cs.append(
            {
                "mention": mention(text),
                "category": category,
                "concept_class": concept_class,
                "owners": sorted(t.name for t in D.owners_of_class(concept_class)),
            }
        )
        reference = f"class:{len(cs) - 1}"
        if direction:
            directions.append({"target": reference, "value": direction})
        roles.append({"target": reference, "value": "endpoint"})
    if classes:
        specifics.add("class_level")
    case = {
        "id": case_id,
        "question": question,
        "sql": sql,
        "family_id": f"t09a:{intent}",
        "primary_group": group,
        "specifics": sorted(specifics),
        "subset": "generic" if group == "generic" else "entity",
        "difficulty": difficulty,
        "categories": [intent],
        "provenance": {
            "author": "codex-t09a",
            "author_type": "agent",
            "method": "independent_authoring",
        },
        "property_focus": focus,
        "empty_reason": EMPTY_REASONS.get(case_id),
        "window": {"start_date": "2026-06-01", "end_date": "2026-07-01"},
    }
    columns = [
        {"relation": relation, "column": column}
        for relation, fields in schema.items()
        for column in fields.split()
    ]
    annotation = {
        "schema_version": 2,
        "id": case_id,
        "question_sha256": text_digest(question),
        "sql_sha256": text_digest(sql),
        "schema": {
            "relations": sorted(schema),
            "columns": sorted(columns, key=lambda c: (c["relation"], c["column"])),
        },
        "entities": es,
        "classes": cs,
        "properties": {"direction": directions, "fact": fact, "address_role": roles},
    }
    cases.append(case)
    annotations.append(annotation)
    notes.append(
        {
            "id": case_id,
            "intent": intent,
            "author_rationale": note,
            "annotation_origin": "explicit author declarations; no prediction/bootstrap",
        }
    )
    if contrast:
        wrong_sql, rationale = contrast
        contrasts.append(
            {"id": case_id, "focus": focus, "sql": wrong_sql.strip(), "rationale": rationale}
        )


# Twenty distinct general analytics intents. These records do not use an old renderer.
add(
    "g01",
    "generic",
    "daily_known_status_failure_share",
    "For each date, report failed and successful outer transaction counts and the failed fraction among transactions whose receipt status is 0 or 1; order by date.",
    f"""SELECT DATE(block_timestamp) AS day, COUNTIF(receipt_status = 0) AS failed,
    COUNTIF(receipt_status = 1) AS succeeded,
    SAFE_DIVIDE(COUNTIF(receipt_status = 0), COUNT(*)) AS failure_fraction
    FROM {TX} WHERE receipt_status IN (0, 1) GROUP BY day ORDER BY day""",
    {"transaction_facts": "block_timestamp receipt_status"},
    fact="transaction",
    note="Denominator excludes unknown receipt status; failed outer transactions remain included.",
)
add(
    "g02",
    "generic",
    "failed_gas_expenditure_by_type",
    "Group failed outer transactions by transaction type and return their count and total gas expenditure in wei, calculated as receipt gas used times gas price; sort by expenditure descending, then type.",
    f"""SELECT transaction_type, COUNT(*) AS failed, SUM(CAST(receipt_gas_used AS NUMERIC) * gas_price_wei) AS spent_wei
    FROM {TX} WHERE receipt_status = 0 GROUP BY transaction_type
    ORDER BY spent_wei DESC, transaction_type""",
    {"transaction_facts": "transaction_type receipt_gas_used gas_price_wei receipt_status"},
    fact="transaction",
    note="Uses actual receipt gas, not the gas limit; no ETH/token conflation.",
)
add(
    "g03",
    "generic",
    "block_daily_transaction_spread",
    "Using the transaction counts recorded in blocks, give each day's minimum, maximum and range of transactions per block, in date order.",
    f"""SELECT DATE(block_timestamp) AS day, MIN(transaction_count) AS minimum,
    MAX(transaction_count) AS maximum, MAX(transaction_count)-MIN(transaction_count) AS spread
    FROM {BL} GROUP BY day ORDER BY day""",
    {"block_facts": "block_timestamp transaction_count"},
    note="Uses block metadata rather than counting sampled outer transactions.",
)
add(
    "g04",
    "generic",
    "beneficiary_block_gas_summary",
    "Return the ten fee recipient addresses credited with the most blocks, including their block count and average block gas used; break count ties by address.",
    f"""SELECT beneficiary_address, COUNT(*) AS blocks, AVG(gas_used) AS average_gas
    FROM {BL} GROUP BY beneficiary_address ORDER BY blocks DESC, beneficiary_address LIMIT 10""",
    {"block_facts": "beneficiary_address gas_used"},
    note="Beneficiary is the fee recipient, not an asserted validator identity.",
)
add(
    "g05",
    "generic",
    "busiest_utc_hours",
    "Which five UTC hours of day contain the most outer transaction rows? Return hour and count, resolving count ties with the earlier hour.",
    f"""SELECT EXTRACT(HOUR FROM block_timestamp AT TIME ZONE 'UTC') AS utc_hour, COUNT(*) AS n
    FROM {TX} GROUP BY utc_hour ORDER BY n DESC, utc_hour LIMIT 5""",
    {"transaction_facts": "block_timestamp"},
    fact="transaction",
    difficulty="easy",
    note="Explicit UTC hour extraction; all stored outer rows are counted.",
)
add(
    "g06",
    "generic",
    "creation_receipt_daily_addresses",
    "For each date with successful contract creations, count distinct non-null contract addresses recorded in transaction receipts; return dates chronologically.",
    f"""SELECT DATE(block_timestamp) AS day, COUNT(DISTINCT receipt_contract_address) AS contracts
    FROM {TX} WHERE receipt_status = 1 AND receipt_contract_address IS NOT NULL
    GROUP BY day ORDER BY day""",
    {"transaction_facts": "block_timestamp receipt_contract_address receipt_status"},
    fact="transaction",
    note="Receipt contract address identifies creation, not the transaction recipient.",
)
add(
    "g07",
    "generic",
    "mixed_outcome_endpoint_pairs",
    "Find sender-recipient pairs with both a failed and a successful outer transaction. Return each pair and the two counts, keeping the twenty pairs with the most combined rows; break ties by sender then recipient.",
    f"""SELECT from_address, to_address, COUNTIF(receipt_status = 0) AS failed,
    COUNTIF(receipt_status = 1) AS succeeded FROM {TX} WHERE receipt_status IN (0, 1)
    GROUP BY from_address, to_address HAVING failed > 0 AND succeeded > 0
    ORDER BY failed+succeeded DESC, from_address, to_address LIMIT 20""",
    {"transaction_facts": "from_address to_address receipt_status"},
    fact="transaction",
    difficulty="hard",
    note="HAVING requires both outcomes for the same ordered endpoint pair.",
)
add(
    "g08",
    "generic",
    "self_transaction_daily_value",
    "On dates with outer transactions whose sender equals recipient, report their row count and sum of declared value in wei; order by date.",
    f"""SELECT DATE(block_timestamp) AS day, COUNT(*) AS n, SUM(value_wei) AS declared_wei
    FROM {TX} WHERE from_address = to_address GROUP BY day ORDER BY day""",
    {"transaction_facts": "block_timestamp value_wei from_address to_address"},
    fact="transaction",
    note="Declared outer value is not a net balance change; self-address equality is deliberate.",
)
add(
    "g09",
    "generic",
    "receipt_gas_utilization_buckets",
    "Bucket outer transactions with positive gas limits and known receipt gas into utilization below 25%, 25% to below 75%, and at least 75%; return bucket and count ordered by bucket label.",
    f"""SELECT CASE WHEN SAFE_DIVIDE(receipt_gas_used, gas_limit) < 0.25 THEN 'a_below_25'
    WHEN SAFE_DIVIDE(receipt_gas_used, gas_limit) < 0.75 THEN 'b_25_to_75'
    ELSE 'c_at_least_75' END AS bucket, COUNT(*) AS n
    FROM {TX} WHERE gas_limit > 0 AND receipt_gas_used IS NOT NULL
    GROUP BY bucket ORDER BY bucket""",
    {"transaction_facts": "receipt_gas_used gas_limit"},
    fact="transaction",
    note="Boundary values 25% and 75% enter the next bucket; missing gas is excluded.",
)
add(
    "g10",
    "generic",
    "token_event_transaction_multiplicity",
    "For each token contract with transfer logs, show event count, distinct outer transaction count, and events per distinct transaction; return the fifteen highest event counts, breaking ties by token address.",
    f"""SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT transaction_hash) AS transactions,
    SAFE_DIVIDE(COUNT(*), COUNT(DISTINCT transaction_hash)) AS events_per_transaction
    FROM {TT} GROUP BY token_address ORDER BY events DESC, token_address LIMIT 15""",
    {"token_transfer_facts": "token_address transaction_hash"},
    fact="token_transfer",
    note="A transfer row is a log event; no join multiplies event rows.",
)
add(
    "g11",
    "generic",
    "repeated_token_in_one_transaction",
    "List the twenty transaction-hash and token-contract combinations with the most transfer logs, requiring at least three logs; return both keys and log count, breaking ties by the two keys.",
    f"""SELECT transaction_hash, token_address, COUNT(*) AS logs FROM {TT}
    GROUP BY transaction_hash, token_address HAVING logs >= 3
    ORDER BY logs DESC, transaction_hash, token_address LIMIT 20""",
    {"token_transfer_facts": "transaction_hash token_address"},
    fact="token_transfer",
    note="Multiplicity is measured per transaction and token, not per endpoint.",
)
add(
    "g12",
    "generic",
    "normalization_gap_by_token",
    "Among transfer events positively classified as ERC20 and not as ERC721, report token addresses with missing normalized amounts, their total event counts and missing-amount counts; show the twenty largest gaps and break ties by token address.",
    f"""SELECT token_address, COUNT(*) AS events, COUNTIF(normalized_amount IS NULL) AS missing
    FROM {TT} WHERE is_erc20 IS TRUE AND COALESCE(is_erc721, FALSE) IS FALSE
    GROUP BY token_address HAVING missing > 0 ORDER BY missing DESC, token_address LIMIT 20""",
    {"token_transfer_facts": "token_address normalized_amount is_erc20 is_erc721"},
    fact="token_transfer",
    note="Missing decimals/cast metadata can make normalization NULL; no amount is fabricated.",
)
add(
    "g13",
    "generic",
    "duplicate_token_symbols",
    "In the token metadata, find nonempty symbols assigned to more than one distinct contract address. Return symbol and address count, ordered by count descending and then symbol, limited to twenty rows.",
    f"""SELECT symbol, COUNT(DISTINCT address) AS addresses FROM {TD}
    WHERE symbol IS NOT NULL AND symbol <> '' GROUP BY symbol HAVING addresses > 1
    ORDER BY addresses DESC, symbol LIMIT 20""",
    {"token_dimension": "symbol address"},
    note="Metadata-only query; symbol is not assumed to uniquely identify a token.",
)
add(
    "g14",
    "generic",
    "dual_standard_contract_flags",
    "From the latest available contract metadata before the cutoff, list up to twenty addresses marked as both ERC20 and ERC721, ordered by address; also return their recorded creation time.",
    f"""SELECT address, created_at FROM {CD} WHERE is_erc20 IS TRUE AND is_erc721 IS TRUE
    ORDER BY address LIMIT 20""",
    {"contract_dimension": "address created_at is_erc20 is_erc721"},
    note="Latest-per-address dimension metadata; an empty list is a valid coverage observation.",
)
add(
    "g15",
    "generic",
    "observed_vs_declared_block_rows",
    "For blocks with at least one observed outer transaction but fewer observed rows than the block's declared transaction count, return block number, both counts and their difference. Show the twenty largest differences, breaking ties by block number.",
    f"""SELECT b.block_number, b.transaction_count AS declared, COUNT(t.transaction_hash) AS observed,
    b.transaction_count-COUNT(t.transaction_hash) AS gap FROM {BL} b JOIN {TX} t
    ON t.block_number=b.block_number AND t.block_hash=b.block_hash
    GROUP BY b.block_number, b.transaction_count HAVING observed < b.transaction_count
    ORDER BY gap DESC, b.block_number LIMIT 20""",
    {
        "block_facts": "block_number block_hash transaction_count",
        "transaction_facts": "transaction_hash block_number block_hash",
    },
    fact="transaction",
    difficulty="hard",
    note="A sample-coverage diagnostic, expected to be empty on complete transaction coverage.",
)
add(
    "g16",
    "generic",
    "outer_transaction_log_summary",
    "For successful outer transactions with transfer events, return hash, declared wei value, event count and distinct token count. Keep the twenty transactions with the most events, resolving ties by hash.",
    f"""SELECT t.transaction_hash, t.value_wei, COUNT(*) AS events,
    COUNT(DISTINCT e.token_address) AS tokens FROM {TX} t JOIN {TT} e
    ON t.transaction_hash=e.transaction_hash AND t.block_number=e.block_number
    AND t.block_hash=e.block_hash WHERE t.receipt_status=1
    GROUP BY t.transaction_hash, t.value_wei ORDER BY events DESC, t.transaction_hash LIMIT 20""",
    {
        "transaction_facts": "transaction_hash value_wei block_number block_hash receipt_status",
        "token_transfer_facts": "token_address transaction_hash block_number block_hash",
    },
    fact="transaction_token_transfer_join",
    difficulty="hard",
    note="Join uses hash plus block identity; transaction value is grouped, never summed across logs.",
)
add(
    "g17",
    "generic",
    "successful_transactions_without_transfer_logs",
    "Count successful outer transactions with no matching token-transfer event, grouped by transaction type and ordered by type.",
    f"""SELECT t.transaction_type, COUNT(*) AS transactions FROM {TX} t
    WHERE t.receipt_status=1 AND NOT EXISTS (SELECT 1 FROM {TT} e
    WHERE e.transaction_hash=t.transaction_hash AND e.block_number=t.block_number
    AND e.block_hash=t.block_hash) GROUP BY t.transaction_type ORDER BY t.transaction_type""",
    {
        "transaction_facts": "transaction_type receipt_status transaction_hash block_number block_hash",
        "token_transfer_facts": "transaction_hash block_number block_hash",
    },
    fact="transaction_token_transfer_join",
    difficulty="hard",
    note="NOT EXISTS avoids fanout and keeps transactions without transfer events.",
)
add(
    "g18",
    "generic",
    "three_day_block_gas_mean",
    "Compute total block gas used for each date and its trailing mean over that date and the preceding two observed dates; return dates in order, using the available dates at the start.",
    f"""WITH daily AS (SELECT DATE(block_timestamp) AS day, SUM(gas_used) AS gas
    FROM {BL} GROUP BY day) SELECT day, gas,
    AVG(gas) OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS trailing_mean
    FROM daily ORDER BY day""",
    {"block_facts": "block_timestamp gas_used"},
    difficulty="hard",
    note="Question specifies observed-date rows, including partial windows at the start.",
)
add(
    "g19",
    "generic",
    "token_decimal_metadata_histogram",
    "Using token metadata, return each known decimals value from 0 through 38 with its number of distinct token addresses, ordered by decimals.",
    f"""SELECT decimals, COUNT(DISTINCT address) AS tokens FROM {TD}
    WHERE decimals BETWEEN 0 AND 38 GROUP BY decimals ORDER BY decimals""",
    {"token_dimension": "decimals address"},
    difficulty="easy",
    note="Metadata snapshot is not a time series; UTC window supplies the benchmark cutoff context.",
)
add(
    "g20",
    "generic",
    "daily_union_of_transaction_endpoints",
    "For each date, count distinct non-null addresses appearing as either sender or recipient of an outer transaction, counting an address only once that day even if it has both roles; order by date.",
    f"""WITH endpoints AS (SELECT DATE(block_timestamp) AS day, from_address AS address
    FROM {TX} UNION ALL SELECT DATE(block_timestamp) AS day, to_address AS address FROM {TX})
    SELECT day, COUNT(DISTINCT address) AS active_addresses FROM endpoints
    WHERE address IS NOT NULL GROUP BY day ORDER BY day""",
    {"transaction_facts": "block_timestamp from_address to_address"},
    fact="transaction",
    difficulty="hard",
    note="UNION ALL followed by distinct address count avoids double counting roles.",
)

# Twenty multi-address intents: owner filters denote every known dictionary address.
add(
    "m01",
    "multi_address",
    "binance_inbound_daily_outcomes",
    "Across all known Binance addresses, tabulate incoming outer transactions by date with separate total, successful and failed counts; order by date.",
    f"""SELECT DATE(block_timestamp) AS day, COUNT(*) AS total,
    COUNTIF(receipt_status=1) AS succeeded, COUNTIF(receipt_status=0) AS failed
    FROM {LT} WHERE to_owner='Binance' GROUP BY day ORDER BY day""",
    {"labeled_transactions": "block_timestamp receipt_status to_owner"},
    fact="transaction",
    entities=[("Binance", "Binance", "to", "endpoint")],
    note="All known recipient addresses participate; unknown status is included only in total.",
)
add(
    "m02",
    "multi_address",
    "okx_inbound_type_gas",
    "Combine the known OKX recipient addresses and summarize incoming outer transactions by type, returning row count and sum of receipt gas used; sort by type.",
    f"""SELECT transaction_type, COUNT(*) AS n, SUM(receipt_gas_used) AS gas
    FROM {LT} WHERE to_owner='OKX' GROUP BY transaction_type ORDER BY transaction_type""",
    {"labeled_transactions": "transaction_type receipt_gas_used to_owner"},
    fact="transaction",
    entities=[("OKX", "OKX", "to", "endpoint")],
    note="Receipt gas summarizes outer calls to the full owner address set.",
)
add(
    "m03",
    "multi_address",
    "bitfinex_outbound_daily_declared_value",
    "Pool the known Bitfinex sender addresses and give each active date's outgoing outer transaction count and sum of declared wei value, ordered by date.",
    f"""SELECT DATE(block_timestamp) AS day, COUNT(*) AS n, SUM(value_wei) AS declared_wei
    FROM {LT} WHERE from_owner='Bitfinex' GROUP BY day ORDER BY day""",
    {"labeled_transactions": "block_timestamp value_wei from_owner"},
    fact="transaction",
    entities=[("Bitfinex", "Bitfinex", "from", "endpoint")],
    note="All outcomes retained; declared value is not claimed to be realized ETH flow.",
)
add(
    "m04",
    "multi_address",
    "kucoin_inbound_sender_reach",
    "Treat every known KuCoin recipient address as one group. Return incoming outer transaction count and the number of distinct senders across that group.",
    f"""SELECT COUNT(*) AS incoming, COUNT(DISTINCT from_address) AS senders
    FROM {LT} WHERE to_owner='KuCoin'""",
    {"labeled_transactions": "from_address to_owner"},
    fact="transaction",
    entities=[("KuCoin", "KuCoin", "to", "endpoint")],
    note="Distinct sender count is computed after owner union, not summed across wallets.",
)
add(
    "m05",
    "multi_address",
    "binance_outbound_recipient_reach",
    "For the union of known Binance sender addresses, report outgoing outer transaction count, distinct non-null recipients and the largest declared wei value.",
    f"""SELECT COUNT(*) AS outgoing, COUNT(DISTINCT to_address) AS recipients,
    MAX(value_wei) AS largest_wei FROM {LT} WHERE from_owner='Binance'""",
    {"labeled_transactions": "to_address value_wei from_owner"},
    fact="transaction",
    entities=[("Binance", "Binance", "from", "endpoint")],
    note="Includes creation transactions in count; their NULL recipient is excluded by DISTINCT.",
)
add(
    "m06",
    "multi_address",
    "bybit_inbound_zero_value_split",
    "Using all known Bybit recipient addresses, split incoming outer transaction rows into zero and nonzero declared wei values, and return the total alongside those counts.",
    f"""SELECT COUNT(*) AS total, COUNTIF(value_wei=0) AS zero_value,
    COUNTIF(value_wei<>0) AS nonzero_value FROM {LT} WHERE to_owner='Bybit'""",
    {"labeled_transactions": "value_wei to_owner"},
    fact="transaction",
    entities=[("Bybit", "Bybit", "to", "endpoint")],
    note="Owner address union is essential even for zero-value outer calls.",
)
add(
    "m07",
    "multi_address",
    "gate_outbound_counterparty_ranking",
    "Combine known Gate.io senders and rank non-null recipient addresses by outgoing outer transaction count. Return twenty recipients with count and average receipt gas, breaking count ties by address.",
    f"""SELECT to_address, COUNT(*) AS n, AVG(receipt_gas_used) AS average_gas
    FROM {LT} WHERE from_owner='Gate.io' AND to_address IS NOT NULL
    GROUP BY to_address ORDER BY n DESC, to_address LIMIT 20""",
    {"labeled_transactions": "to_address receipt_gas_used from_owner"},
    fact="transaction",
    entities=[("Gate.io", "Gate.io", "from", "endpoint")],
    note="Counterparty ranking aggregates all owner sender addresses before limiting.",
)
add(
    "m08",
    "multi_address",
    "bitget_inbound_hour_histogram",
    "Merge known Bitget recipient addresses and count incoming outer transactions by UTC hour of day, returning hours in order.",
    f"""SELECT EXTRACT(HOUR FROM block_timestamp AT TIME ZONE 'UTC') AS hour, COUNT(*) AS incoming
    FROM {LT} WHERE to_owner='Bitget' GROUP BY hour ORDER BY hour""",
    {"labeled_transactions": "block_timestamp to_owner"},
    fact="transaction",
    entities=[("Bitget", "Bitget", "to", "endpoint")],
    note="UTC hour grouping follows union of all dictionary-known recipients.",
)
add(
    "m09",
    "multi_address",
    "deribit_positive_outbound_daily",
    "Across known Deribit senders, report dates with positive-value outgoing outer transactions, their counts and minimum positive wei value; order by date.",
    f"""SELECT DATE(block_timestamp) AS day, COUNT(*) AS n, MIN(value_wei) AS minimum_wei
    FROM {LT} WHERE from_owner='Deribit' AND value_wei>0 GROUP BY day ORDER BY day""",
    {"labeled_transactions": "block_timestamp value_wei from_owner"},
    fact="transaction",
    entities=[("Deribit", "Deribit", "from", "endpoint")],
    note="Positive declared value predicate belongs to both union and single-address checks.",
)
add(
    "m10",
    "multi_address",
    "mexc_outer_both_role_counts",
    "For the complete known MEXC address group, return counts of outer transactions sent, received, and involving the group in either role. An internal transaction contributes once to the either-role count and once to each directional count.",
    f"""SELECT COUNTIF(from_owner='MEXC') AS sent, COUNTIF(to_owner='MEXC') AS received,
    COUNT(*) AS involved FROM {LT} WHERE from_owner='MEXC' OR to_owner='MEXC'""",
    {"labeled_transactions": "from_owner to_owner"},
    fact="transaction",
    entities=[("MEXC", "MEXC", "either", "endpoint")],
    note="OR selects each outer row once; directional counts intentionally overlap.",
)
add(
    "m11",
    "multi_address",
    "binance_inbound_token_mix",
    "Combine every known Binance recipient address and report incoming token events by token contract, including event count and distinct sender count; show the twenty most frequent tokens, breaking ties by token address.",
    f"""SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT from_address) AS senders
    FROM {LL} WHERE to_owner='Binance' GROUP BY token_address
    ORDER BY events DESC, token_address LIMIT 20""",
    {"labeled_token_transfers": "token_address from_address to_owner"},
    fact="token_transfer",
    entities=[("Binance", "Binance", "to", "endpoint")],
    note="Event counts, not normalized amounts across heterogeneous tokens.",
)
add(
    "m12",
    "multi_address",
    "okx_outbound_token_counterparties",
    "Across known OKX token-event senders, return the twenty most frequent token-contract and recipient pairs with their event counts; resolve ties by token address then recipient.",
    f"""SELECT token_address, to_address, COUNT(*) AS events FROM {LL}
    WHERE from_owner='OKX' GROUP BY token_address, to_address
    ORDER BY events DESC, token_address, to_address LIMIT 20""",
    {"labeled_token_transfers": "token_address to_address from_owner"},
    fact="token_transfer",
    entities=[("OKX", "OKX", "from", "endpoint")],
    note="Known owner sender addresses are unioned before pair ranking.",
)
add(
    "m13",
    "multi_address",
    "bitfinex_token_daily_transaction_reach",
    "For token events involving any known Bitfinex address as sender or recipient, give each active date's event count and distinct outer transaction count in date order; count an internal event only once.",
    f"""SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
    COUNT(DISTINCT transaction_hash) AS transactions FROM {LL}
    WHERE from_owner='Bitfinex' OR to_owner='Bitfinex' GROUP BY day ORDER BY day""",
    {"labeled_token_transfers": "block_timestamp transaction_hash from_owner to_owner"},
    fact="token_transfer",
    entities=[("Bitfinex", "Bitfinex", "either", "endpoint")],
    note="OR prevents duplicate rows when both event endpoints belong to the owner.",
)
add(
    "m14",
    "multi_address",
    "kucoin_inbound_event_fanout",
    "Pool known KuCoin recipients and, for each token contract, return incoming event count minus distinct transaction count alongside both counts; order by the difference descending and then token address.",
    f"""SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT transaction_hash) AS transactions,
    COUNT(*)-COUNT(DISTINCT transaction_hash) AS extra_events FROM {LL}
    WHERE to_owner='KuCoin' GROUP BY token_address ORDER BY extra_events DESC, token_address""",
    {"labeled_token_transfers": "token_address transaction_hash to_owner"},
    fact="token_transfer",
    entities=[("KuCoin", "KuCoin", "to", "endpoint")],
    note="A transaction may emit multiple inbound events across owner addresses.",
)
add(
    "m15",
    "multi_address",
    "bybit_outbound_address_contributions",
    "For each known Bybit address that sent token events, return its event count and number of distinct token contracts; order by event count descending and then sender address.",
    f"""SELECT from_address, COUNT(*) AS events, COUNT(DISTINCT token_address) AS tokens
    FROM {LL} WHERE from_owner='Bybit' GROUP BY from_address ORDER BY events DESC, from_address""",
    {"labeled_token_transfers": "from_address token_address from_owner"},
    fact="token_transfer",
    entities=[("Bybit", "Bybit", "from", "endpoint")],
    note="Returning contributions of all active known addresses exposes representative-wallet loss.",
)
add(
    "m16",
    "multi_address",
    "gate_inbound_raw_value_validity",
    "For all known Gate.io recipients, summarize incoming token events per token contract with total events, valid raw-value casts, and positive cast values; sort by token address.",
    f"""SELECT token_address, COUNT(*) AS events, COUNTIF(value_cast_valid) AS valid_values,
    COUNTIF(value_bignumeric>0) AS positive_values FROM {LL}
    WHERE to_owner='Gate.io' GROUP BY token_address ORDER BY token_address""",
    {"labeled_token_transfers": "token_address value_cast_valid value_bignumeric to_owner"},
    fact="token_transfer",
    entities=[("Gate.io", "Gate.io", "to", "endpoint")],
    note="Raw numeric cast checks do not imply normalized ERC20 amounts.",
)
add(
    "m17",
    "multi_address",
    "binance_inbound_daily_type_diversity",
    "Across known Binance recipients, report each active date's incoming outer transaction count and number of distinct non-null transaction types; order by date.",
    f"""SELECT DATE(block_timestamp) AS day, COUNT(*) AS incoming,
    COUNT(DISTINCT transaction_type) AS types FROM {LT} WHERE to_owner='Binance'
    GROUP BY day ORDER BY day""",
    {"labeled_transactions": "block_timestamp transaction_type to_owner"},
    fact="transaction",
    entities=[("Binance", "Binance", "to", "endpoint")],
    note="Different projection and aggregation intent from receipt outcome analysis.",
)
add(
    "m18",
    "multi_address",
    "bitstamp_inbound_daily_token_counts",
    "Combining known Bitstamp recipients, report each date with incoming token events, its event count and distinct token count; order by date.",
    f"""SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
    COUNT(DISTINCT token_address) AS tokens FROM {LL} WHERE to_owner='Bitstamp'
    GROUP BY day ORDER BY day""",
    {"labeled_token_transfers": "block_timestamp token_address to_owner"},
    fact="token_transfer",
    entities=[("Bitstamp", "Bitstamp", "to", "endpoint")],
    note="Known address membership is complete even when some addresses are inactive.",
)
add(
    "m19",
    "multi_address",
    "htx_outbound_token_counterparty_breadth",
    "Across known HTX senders of token events, rank recipient addresses by distinct token contracts received, also showing event count; return twenty rows and break ties by event count descending then recipient address.",
    f"""SELECT to_address, COUNT(DISTINCT token_address) AS tokens, COUNT(*) AS events
    FROM {LL} WHERE from_owner='HTX' GROUP BY to_address
    ORDER BY tokens DESC, events DESC, to_address LIMIT 20""",
    {"labeled_token_transfers": "to_address token_address from_owner"},
    fact="token_transfer",
    entities=[("HTX", "HTX", "from", "endpoint")],
    note="Canonical owner HTX avoids the ambiguous token alias Huobi.",
)
add(
    "m20",
    "multi_address",
    "cryptocom_token_boundary_counts",
    "For all known Crypto-com addresses, give per-token counts of sent, received and either-role transfer events. Count an event between two group addresses once in the either-role total; sort by token address.",
    f"""SELECT token_address, COUNTIF(from_owner='Crypto-com') AS sent,
    COUNTIF(to_owner='Crypto-com') AS received, COUNT(*) AS involved FROM {LL}
    WHERE from_owner='Crypto-com' OR to_owner='Crypto-com'
    GROUP BY token_address ORDER BY token_address""",
    {"labeled_token_transfers": "token_address from_owner to_owner"},
    fact="token_transfer",
    entities=[("Crypto-com", "Crypto-com", "either", "endpoint")],
    note="Separate token identities; internal events do not double the either-role total.",
)

# Twenty alias intents. Ambiguous bare 'uniswap', 'uni', 'huobi', 'pancakeswap' are excluded.
add(
    "a01",
    "alias",
    "okex_peak_outbound_failure_date",
    "For OKEx, find the active date with the largest fraction of failed outgoing outer transactions among known 0/1 receipt statuses; return date, failed count, known-status count and fraction, breaking fraction ties by earlier date.",
    f"""SELECT DATE(block_timestamp) AS day, COUNTIF(receipt_status=0) AS failed,
    COUNT(*) AS known_status, SAFE_DIVIDE(COUNTIF(receipt_status=0),COUNT(*)) AS fraction
    FROM {LT} WHERE from_owner='OKX' AND receipt_status IN (0,1)
    GROUP BY day ORDER BY fraction DESC, day LIMIT 1""",
    {"labeled_transactions": "block_timestamp receipt_status from_owner"},
    fact="transaction",
    entities=[("OKEx", "OKX", "from", "endpoint")],
    note="Historical name uniquely resolves to OKX, and fraction uses only known statuses.",
)
add(
    "a02",
    "alias",
    "curve_finance_inbound_type_success",
    "For incoming outer calls to curve finance, return each transaction type with total and successful row counts, ordered by type.",
    f"""SELECT transaction_type, COUNT(*) AS total, COUNTIF(receipt_status=1) AS succeeded
    FROM {LT} WHERE to_owner='Curve DEX' GROUP BY transaction_type ORDER BY transaction_type""",
    {"labeled_transactions": "transaction_type receipt_status to_owner"},
    fact="transaction",
    entities=[("curve finance", "Curve DEX", "to", "endpoint")],
    note="Protocol owner Curve DEX, not the Curve governance token.",
)
add(
    "a03",
    "alias",
    "tc_inbound_value_buckets",
    "For outer transactions received by TC, return active dates with zero-value and positive-value counts plus total declared wei; order by date.",
    f"""SELECT DATE(block_timestamp) AS day, COUNTIF(value_wei=0) AS zero_value,
    COUNTIF(value_wei>0) AS positive_value, SUM(value_wei) AS declared_wei
    FROM {LT} WHERE to_owner='Tornado Cash' GROUP BY day ORDER BY day""",
    {"labeled_transactions": "block_timestamp value_wei to_owner"},
    fact="transaction",
    entities=[("TC", "Tornado Cash", "to", "endpoint")],
    note="TC is a dictionary alias of the privacy-service owner; all known endpoints included.",
)
add(
    "a04",
    "alias",
    "uni_v2_outbound_token_active_dates",
    "For token events sent by uni v2, return each token contract with event count and number of distinct active UTC dates, sorted by active dates descending and then token address.",
    f"""SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT DATE(block_timestamp)) AS days
    FROM {LL} WHERE from_owner='Uniswap V2' GROUP BY token_address
    ORDER BY days DESC, token_address""",
    {"labeled_token_transfers": "token_address block_timestamp from_owner"},
    fact="token_transfer",
    entities=[("uni v2", "Uniswap V2", "from", "endpoint")],
    note="Version-qualified alias avoids ambiguous Uniswap family resolution.",
)
add(
    "a05",
    "alias",
    "uni_v3_inbound_gas_extrema",
    "For outer calls received by uni v3, report the count and minimum, average and maximum receipt gas used.",
    f"""SELECT COUNT(*) AS calls, MIN(receipt_gas_used) AS minimum,
    AVG(receipt_gas_used) AS average, MAX(receipt_gas_used) AS maximum
    FROM {LT} WHERE to_owner='Uniswap V3'""",
    {"labeled_transactions": "receipt_gas_used to_owner"},
    fact="transaction",
    entities=[("uni v3", "Uniswap V3", "to", "endpoint")],
    note="Aggregates outer receipt gas for every known V3 endpoint, independent of token events.",
)
add(
    "a06",
    "alias",
    "uni_v4_hourly_call_cost",
    "Group outer calls received by uni v4 by UTC hour of day, returning count and average gas price in wei, ordered by hour.",
    f"""SELECT EXTRACT(HOUR FROM block_timestamp AT TIME ZONE 'UTC') AS hour,
    COUNT(*) AS calls, AVG(gas_price_wei) AS average_price FROM {LT}
    WHERE to_owner='Uniswap V4' GROUP BY hour ORDER BY hour""",
    {"labeled_transactions": "block_timestamp gas_price_wei to_owner"},
    fact="transaction",
    entities=[("uni v4", "Uniswap V4", "to", "endpoint")],
    note="V4 is a distinct owner, not a renamed V3 address set.",
)
add(
    "a07",
    "alias",
    "op_bridge_endpoint_contributions",
    "For op bridge, list known recipient addresses with incoming outer transactions, showing row count and total declared wei per address; sort by count descending and then address.",
    f"""SELECT to_address, COUNT(*) AS calls, SUM(value_wei) AS declared_wei
    FROM {LT} WHERE to_owner='Optimism Bridge' GROUP BY to_address
    ORDER BY calls DESC, to_address""",
    {"labeled_transactions": "to_address value_wei to_owner"},
    fact="transaction",
    entities=[("op bridge", "Optimism Bridge", "to", "endpoint")],
    note="Alias denotes the known L1 bridge owner, not all transactions on an L2 chain.",
)
add(
    "a08",
    "alias",
    "optimism_gateway_inbound_token_transaction_mix",
    "For optimism gateway, return the fifteen token contracts with the most incoming transfer events and their distinct outer transaction counts; include event count and break ties by token address.",
    f"""SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT transaction_hash) AS transactions
    FROM {LL} WHERE to_owner='Optimism Bridge' GROUP BY token_address
    ORDER BY events DESC, token_address LIMIT 15""",
    {"labeled_token_transfers": "token_address transaction_hash to_owner"},
    fact="token_transfer",
    entities=[("optimism gateway", "Optimism Bridge", "to", "endpoint")],
    note="Gateway alias uses endpoint role; token identity is unrestricted.",
)
add(
    "a09",
    "alias",
    "binance_alias_inbound_sender_gas_prices",
    "For binance exchange, return the ten senders with the most incoming outer transactions, including count and average gas price in wei; resolve count ties by sender address.",
    f"""SELECT from_address, COUNT(*) AS n, AVG(gas_price_wei) AS average_price
    FROM {LT} WHERE to_owner='Binance' GROUP BY from_address
    ORDER BY n DESC, from_address LIMIT 10""",
    {"labeled_transactions": "from_address gas_price_wei to_owner"},
    fact="transaction",
    entities=[("binance exchange", "Binance", "to", "endpoint")],
    note="Noncanonical owner alias, with sender aggregation after recipient-address union.",
)
add(
    "a10",
    "alias",
    "cryptocom_outbound_known_status_histogram",
    "For crypto.com, give outgoing outer transaction counts by receipt status and transaction type, ordering by status then type; retain the unknown-status group.",
    f"""SELECT receipt_status, transaction_type, COUNT(*) AS n FROM {LT}
    WHERE from_owner='Crypto-com' GROUP BY receipt_status, transaction_type
    ORDER BY receipt_status, transaction_type""",
    {"labeled_transactions": "receipt_status transaction_type from_owner"},
    fact="transaction",
    entities=[("crypto.com", "Crypto-com", "from", "endpoint")],
    note="Punctuation alias is dictionary-bound; NULL receipt status is not silently dropped.",
)
add(
    "a11",
    "alias",
    "hashkey_declared_value_net",
    "For hashkey, return the sum of declared incoming outer wei minus declared outgoing outer wei across its known addresses, and the either-role transaction count. Internal rows cancel in the value difference; include every receipt outcome.",
    f"""SELECT SUM(IF(to_owner='HashKey Exchange',value_wei,0))
    - SUM(IF(from_owner='HashKey Exchange',value_wei,0)) AS net_declared_wei,
    COUNT(*) AS involved FROM {LT}
    WHERE from_owner='HashKey Exchange' OR to_owner='HashKey Exchange'""",
    {"labeled_transactions": "from_owner to_owner value_wei"},
    fact="transaction",
    entities=[("hashkey", "HashKey Exchange", "either", "endpoint")],
    note="Declared-value diagnostic, explicitly not balance change or realized ETH settlement.",
)
add(
    "a12",
    "alias",
    "osl_outbound_contract_creation_split",
    "For OSL, return the number of outgoing outer transactions to a non-null recipient, the number with a null recipient, and the count of distinct non-null recipients.",
    f"""SELECT COUNTIF(to_address IS NOT NULL) AS addressed,
    COUNTIF(to_address IS NULL) AS creations, COUNT(DISTINCT to_address) AS recipients
    FROM {LT} WHERE from_owner='OSL HK'""",
    {"labeled_transactions": "to_address from_owner"},
    fact="transaction",
    entities=[("OSL", "OSL HK", "from", "endpoint")],
    note="Short alias resolves to OSL HK; null recipient rows are explicitly counted.",
)
add(
    "a13",
    "alias",
    "usdt_daily_normalized_erc20_totals",
    "For USDT as the transferred token, report each active date's ERC20 event count with a non-null normalized amount and sum of those normalized units; exclude events positively marked ERC721 and order by date.",
    f"""SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
    SUM(normalized_amount) AS normalized_units FROM {LL}
    WHERE token_owner='Tether' AND is_erc20 IS TRUE
    AND COALESCE(is_erc721,FALSE) IS FALSE AND normalized_amount IS NOT NULL
    GROUP BY day ORDER BY day""",
    {"labeled_token_transfers": "block_timestamp normalized_amount token_owner is_erc20 is_erc721"},
    fact="token_transfer",
    entities=[("USDT", "Tether", None, "token_contract")],
    note="Token ticker alias is token identity; local normalized totals use DOUBLE, not exact accounting.",
)
add(
    "a14",
    "alias",
    "wbtc_daily_raw_extrema",
    "For WBTC as the transferred token, return each date with valid numeric raw values, the event count and minimum and maximum raw value, without decimal normalization; order by date.",
    f"""SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
    MIN(value_bignumeric) AS minimum_raw, MAX(value_bignumeric) AS maximum_raw
    FROM {LL} WHERE token_owner='Wrapped Bitcoin' AND value_cast_valid
    GROUP BY day ORDER BY day""",
    {"labeled_token_transfers": "block_timestamp value_bignumeric token_owner value_cast_valid"},
    fact="token_transfer",
    entities=[("WBTC", "Wrapped Bitcoin", None, "token_contract")],
    note="Raw cast range differs locally from BigQuery BIGNUMERIC; full parity remains pending.",
)
add(
    "a15",
    "alias",
    "link_zero_raw_value_events",
    "For LINK as the transferred token, return total event count and the counts with valid raw numeric values equal to zero and greater than zero.",
    f"""SELECT COUNT(*) AS events, COUNTIF(value_bignumeric=0) AS zero_raw,
    COUNTIF(value_bignumeric>0) AS positive_raw FROM {LL} WHERE token_owner='Chainlink'""",
    {"labeled_token_transfers": "value_bignumeric token_owner"},
    fact="token_transfer",
    entities=[("LINK", "Chainlink", None, "token_contract")],
    note="LINK uniquely resolves to Chainlink; invalid cast values enter neither raw bucket.",
)
add(
    "a16",
    "alias",
    "curve_inbound_daily_token_diversity",
    "For curve as a recipient of token events, report each active date's distinct token-contract count and distinct sender count; return dates chronologically.",
    f"""SELECT DATE(block_timestamp) AS day, COUNT(DISTINCT token_address) AS tokens,
    COUNT(DISTINCT from_address) AS senders FROM {LL} WHERE to_owner='Curve DEX'
    GROUP BY day ORDER BY day""",
    {"labeled_token_transfers": "block_timestamp token_address from_address to_owner"},
    fact="token_transfer",
    entities=[("curve", "Curve DEX", "to", "endpoint")],
    note="Alias refers to protocol endpoints, not a token ticker.",
)
add(
    "a17",
    "alias",
    "the_mixer_outbound_cast_validity",
    "For token events sent by the mixer, group by token contract and raw-value cast-validity flag, returning counts ordered by token address and flag.",
    f"""SELECT token_address, value_cast_valid, COUNT(*) AS events FROM {LL}
    WHERE from_owner='Tornado Cash' GROUP BY token_address, value_cast_valid
    ORDER BY token_address, value_cast_valid""",
    {"labeled_token_transfers": "token_address value_cast_valid from_owner"},
    fact="token_transfer",
    entities=[("the mixer", "Tornado Cash", "from", "endpoint")],
    note="Dictionary service alias names one owner; it is not a request for all mixers.",
)
add(
    "a18",
    "alias",
    "pancake_swap_successful_call_days",
    "For pancake swap, report dates with successful incoming outer calls, including their count and distinct sender count, ordered by date.",
    f"""SELECT DATE(block_timestamp) AS day, COUNT(*) AS calls,
    COUNT(DISTINCT from_address) AS senders FROM {LT}
    WHERE to_owner='PancakeSwap AMM' AND receipt_status=1 GROUP BY day ORDER BY day""",
    {"labeled_transactions": "block_timestamp from_address to_owner receipt_status"},
    fact="transaction",
    entities=[("pancake swap", "PancakeSwap AMM", "to", "endpoint")],
    note="Spaced alias is unambiguous in the pinned dictionary; bare PancakeSwap is ambiguous.",
)
add(
    "a19",
    "alias",
    "chainlink_ccip_receipt_status",
    "For chainlink ccip, give incoming outer transaction count, zero-value call count and total receipt gas used per receipt status; order by status and retain unknown status.",
    f"""SELECT receipt_status, COUNT(*) AS calls, COUNTIF(value_wei=0) AS zero_value, SUM(receipt_gas_used) AS gas
    FROM {LT} WHERE to_owner='CCIP' GROUP BY receipt_status ORDER BY receipt_status""",
    {"labeled_transactions": "receipt_status value_wei receipt_gas_used to_owner"},
    fact="transaction",
    entities=[("chainlink ccip", "CCIP", "to", "endpoint")],
    note="CCIP is a bridge owner distinct from the Chainlink token contract.",
)
add(
    "a20",
    "alias",
    "tornado_classic_token_activity_bounds",
    "For token events received by tornado cash classic, report token contract, event count, first timestamp and last timestamp; sort by token address.",
    f"""SELECT token_address, COUNT(*) AS events, MIN(block_timestamp) AS first_event,
    MAX(block_timestamp) AS last_event FROM {LL} WHERE to_owner='Tornado Cash'
    GROUP BY token_address ORDER BY token_address""",
    {"labeled_token_transfers": "token_address block_timestamp to_owner"},
    fact="token_transfer",
    entities=[("tornado cash classic", "Tornado Cash", "to", "endpoint")],
    note="First/last timestamps apply to event receipts, not outer transaction senders.",
)

# Twenty class intents. Scope always explicitly limited to dictionary-labeled owners.
add(
    "c01",
    "class_level",
    "exchange_inbound_weekday_histogram",
    "Within dictionary-labeled centralized exchanges, give incoming outer transaction counts by owner and UTC day of week; return owner, weekday number with Sunday=1, and count, sorted by owner then weekday.",
    f"""SELECT to_owner AS owner, EXTRACT(DAYOFWEEK FROM block_timestamp AT TIME ZONE 'UTC') AS weekday,
    COUNT(*) AS n FROM {LT} WHERE to_category='exchange'
    GROUP BY owner, weekday ORDER BY owner, weekday""",
    {"labeled_transactions": "to_owner block_timestamp to_category"},
    fact="transaction",
    classes=[("centralized exchanges", "exchange", "to")],
    note="All thirty dictionary ExchangeAccount owners, not all exchanges on Ethereum.",
)
add(
    "c02",
    "class_level",
    "dex_successful_call_gas_by_owner",
    "For dictionary-labeled decentralized exchanges receiving successful outer calls, return owner, call count, average and maximum receipt gas used, sorted by owner.",
    f"""SELECT to_owner AS owner, COUNT(*) AS calls, AVG(receipt_gas_used) AS average_gas,
    MAX(receipt_gas_used) AS maximum_gas FROM {LT}
    WHERE to_category='dex' AND receipt_status=1 GROUP BY owner ORDER BY owner""",
    {"labeled_transactions": "to_owner receipt_gas_used to_category receipt_status"},
    fact="transaction",
    classes=[("decentralized exchanges", "dex", "to")],
    note="Protocol class is operational DEX endpoints, not governance-token holders.",
)
add(
    "c03",
    "class_level",
    "lending_inbound_value_profile",
    "For each dictionary-labeled lending owner receiving outer transactions, show total rows, zero-value rows and positive-value rows; sort by owner.",
    f"""SELECT to_owner AS owner, COUNT(*) AS total, COUNTIF(value_wei=0) AS zero_value,
    COUNTIF(value_wei>0) AS positive_value FROM {LT} WHERE to_category='lending'
    GROUP BY owner ORDER BY owner""",
    {"labeled_transactions": "to_owner value_wei to_category"},
    fact="transaction",
    classes=[("lending", "lending", "to")],
    note="Includes only dictionary lending endpoints; token owners with similar names are excluded.",
)
add(
    "c04",
    "class_level",
    "bridge_outbound_token_breadth",
    "For dictionary-labeled bridge owners that send token events, return owner, event count and distinct token-contract count, ordered by event count descending and then owner.",
    f"""SELECT from_owner AS owner, COUNT(*) AS events, COUNT(DISTINCT token_address) AS tokens
    FROM {LL} WHERE from_category='bridge' GROUP BY owner ORDER BY events DESC, owner""",
    {"labeled_token_transfers": "from_owner token_address from_category"},
    fact="token_transfer",
    classes=[("bridge", "bridge", "from")],
    note="Only labeled bridge endpoints; sending a bridge token is insufficient.",
)
add(
    "c05",
    "class_level",
    "mixer_either_role_hour_counts",
    "Count outer transactions involving dictionary-labeled mixers as sender or recipient by UTC hour of day; return hour and count in hour order, counting each transaction once.",
    f"""SELECT EXTRACT(HOUR FROM block_timestamp AT TIME ZONE 'UTC') AS hour, COUNT(*) AS n
    FROM {LT} WHERE from_category='mixer' OR to_category='mixer'
    GROUP BY hour ORDER BY hour""",
    {"labeled_transactions": "block_timestamp from_category to_category"},
    fact="transaction",
    classes=[("mixers", "mixer", "either")],
    note="OR selects union of endpoint roles without doubling internal rows.",
)
add(
    "c06",
    "class_level",
    "staking_inbound_token_mix",
    "For dictionary-labeled staking recipients, return each token contract's incoming event count and distinct sender count, sorted by token address.",
    f"""SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT from_address) AS senders
    FROM {LL} WHERE to_category='staking' GROUP BY token_address ORDER BY token_address""",
    {"labeled_token_transfers": "token_address from_address to_category"},
    fact="token_transfer",
    classes=[("staking", "staking", "to")],
    note="Class membership remains annotated even if this small class has no sampled activity.",
)
add(
    "c07",
    "class_level",
    "exchange_internal_class_owner_pairs",
    "Among outer transactions whose two endpoints belong to dictionary-labeled exchanges, return ordered sender-owner and recipient-owner pairs with row counts; include same-owner pairs and sort by count descending then the two owner names.",
    f"""SELECT from_owner, to_owner, COUNT(*) AS n FROM {LT}
    WHERE from_category='exchange' AND to_category='exchange'
    GROUP BY from_owner, to_owner ORDER BY n DESC, from_owner, to_owner""",
    {"labeled_transactions": "from_owner to_owner from_category to_category"},
    fact="transaction",
    classes=[("exchanges", "exchange", "either")],
    note="Both endpoint predicates are required. Class direction either describes roles, not SQL OR.",
)
add(
    "c08",
    "class_level",
    "dex_outbound_token_recipient_reach",
    "For each dictionary-labeled DEX owner sending token events, report distinct recipient addresses, distinct outer transactions and event count; sort by owner.",
    f"""SELECT from_owner AS owner, COUNT(DISTINCT to_address) AS recipients,
    COUNT(DISTINCT transaction_hash) AS transactions, COUNT(*) AS events
    FROM {LL} WHERE from_category='dex' GROUP BY owner ORDER BY owner""",
    {"labeled_token_transfers": "from_owner to_address transaction_hash from_category"},
    fact="token_transfer",
    classes=[("DEX", "dex", "from")],
    note="Distinct counts are recomputed across the owner's complete labeled endpoint set.",
)
add(
    "c09",
    "class_level",
    "money_market_daily_inbound_senders",
    "Across dictionary-labeled money market recipients, report each active date's incoming outer transaction count and distinct sender count, pooling owners and ordering by date.",
    f"""SELECT DATE(block_timestamp) AS day, COUNT(*) AS calls,
    COUNT(DISTINCT from_address) AS senders FROM {LT} WHERE to_category='lending'
    GROUP BY day ORDER BY day""",
    {"labeled_transactions": "block_timestamp from_address to_category"},
    fact="transaction",
    classes=[("money market", "lending", "to")],
    note="Money market maps to the dictionary LendingProtocol class, with explicit pooling.",
)
add(
    "c10",
    "class_level",
    "bridge_daily_outer_declared_value",
    "For dictionary-labeled cross chain bridge recipients, report owner and active date with incoming outer transaction count and sum of declared wei, sorted by owner then date.",
    f"""SELECT to_owner AS owner, DATE(block_timestamp) AS day, COUNT(*) AS calls,
    SUM(value_wei) AS declared_wei FROM {LT} WHERE to_category='bridge'
    GROUP BY owner, day ORDER BY owner, day""",
    {"labeled_transactions": "to_owner block_timestamp value_wei to_category"},
    fact="transaction",
    classes=[("cross chain bridge", "bridge", "to")],
    note="Declared call values do not assert completed bridge transfers or L2 outcomes.",
)
add(
    "c11",
    "class_level",
    "exchange_same_owner_token_events",
    "For dictionary-labeled centralized exchanges, count token events whose sender and recipient have the same exchange owner. Return owner, token contract and count ordered by owner then token address.",
    f"""SELECT from_owner AS owner, token_address, COUNT(*) AS events FROM {LL}
    WHERE from_category='exchange' AND to_category='exchange' AND from_owner=to_owner
    GROUP BY owner, token_address ORDER BY owner, token_address""",
    {"labeled_token_transfers": "from_owner token_address from_category to_category to_owner"},
    fact="token_transfer",
    classes=[("centralized exchanges", "exchange", "either")],
    note="Same-owner condition differs from exchange-to-exchange activity in general.",
)
add(
    "c12",
    "class_level",
    "dex_inbound_uncastable_raw_values",
    "For dictionary-labeled dexes receiving token events, report owner, token contract, total events and invalid raw-value cast count; keep every observed owner-token pair and sort by owner then token address.",
    f"""SELECT to_owner AS owner, token_address, COUNT(*) AS events,
    COUNTIF(NOT value_cast_valid) AS invalid_values FROM {LL} WHERE to_category='dex'
    GROUP BY owner, token_address ORDER BY owner, token_address""",
    {"labeled_token_transfers": "to_owner token_address value_cast_valid to_category"},
    fact="token_transfer",
    classes=[("dexes", "dex", "to")],
    note="Zero invalid values are retained; absence of errors is not absence of events.",
)
add(
    "c13",
    "class_level",
    "mixer_inbound_nonzero_raw_profile",
    "For each dictionary-labeled privacy mixers owner receiving token events, return total events, positive valid raw-value events and distinct token count; order by owner.",
    f"""SELECT to_owner AS owner, COUNT(*) AS events,
    COUNTIF(value_bignumeric>0) AS positive_values, COUNT(DISTINCT token_address) AS tokens
    FROM {LL} WHERE to_category='mixer' GROUP BY owner ORDER BY owner""",
    {"labeled_token_transfers": "to_owner value_bignumeric token_address to_category"},
    fact="token_transfer",
    classes=[("privacy mixers", "mixer", "to")],
    note="Class-level request is distinct from the singular service alias 'the mixer'.",
)
add(
    "c14",
    "class_level",
    "lending_to_exchange_token_owner_flows",
    "For token events sent by dictionary-labeled lending owners to dictionary-labeled exchanges, return ordered owner pairs, event count and distinct token count; sort by sender owner then recipient owner.",
    f"""SELECT from_owner, to_owner, COUNT(*) AS events, COUNT(DISTINCT token_address) AS tokens
    FROM {LL} WHERE from_category='lending' AND to_category='exchange'
    GROUP BY from_owner, to_owner ORDER BY from_owner, to_owner""",
    {"labeled_token_transfers": "from_owner to_owner token_address from_category to_category"},
    fact="token_transfer",
    classes=[("lending", "lending", "from"), ("exchanges", "exchange", "to")],
    difficulty="hard",
    note="Two distinct class mentions and directional targets; no token-owner join substitution.",
)
add(
    "c15",
    "class_level",
    "exchange_to_bridge_outer_outcomes",
    "For outer transactions from dictionary-labeled exchanges to dictionary-labeled bridge owners, return sender owner, recipient owner, total rows and successful rows; sort by the two owner names.",
    f"""SELECT from_owner, to_owner, COUNT(*) AS total, COUNTIF(receipt_status=1) AS succeeded
    FROM {LT} WHERE from_category='exchange' AND to_category='bridge'
    GROUP BY from_owner, to_owner ORDER BY from_owner, to_owner""",
    {"labeled_transactions": "from_owner to_owner receipt_status from_category to_category"},
    fact="transaction",
    classes=[("exchanges", "exchange", "from"), ("bridge", "bridge", "to")],
    difficulty="hard",
    note="Two endpoint class predicates; outer calls, not inferred cross-chain settlement.",
)
add(
    "c16",
    "class_level",
    "dex_high_gas_call_profile",
    "For dictionary-labeled decentralized exchange recipients, summarize outer calls using more than 100000 receipt gas units: return owner, call count, average receipt gas and average gas limit, sorted by owner.",
    f"""SELECT to_owner AS owner, COUNT(*) AS calls, AVG(receipt_gas_used) AS average_gas,
    AVG(gas_limit) AS average_limit FROM {LT}
    WHERE to_category='dex' AND receipt_gas_used>100000 GROUP BY owner ORDER BY owner""",
    {"labeled_transactions": "to_owner receipt_gas_used gas_limit to_category"},
    fact="transaction",
    classes=[("decentralized exchange", "dex", "to")],
    note="Strict gas threshold applies to actual receipt gas, not the declared gas limit.",
)
add(
    "c17",
    "class_level",
    "exchange_inbound_without_token_events",
    "For dictionary-labeled exchange recipients, count outer transactions with no matching token event, per owner; return owner and count alphabetically.",
    f"""SELECT t.to_owner AS owner, COUNT(*) AS transactions FROM {LT} t
    WHERE t.to_category='exchange' AND NOT EXISTS (SELECT 1 FROM {TT} e
    WHERE e.transaction_hash=t.transaction_hash AND e.block_number=t.block_number
    AND e.block_hash=t.block_hash) GROUP BY owner ORDER BY owner""",
    {
        "labeled_transactions": "to_owner to_category transaction_hash block_number block_hash",
        "token_transfer_facts": "transaction_hash block_number block_hash",
    },
    fact="transaction_token_transfer_join",
    classes=[("exchange", "exchange", "to")],
    difficulty="hard",
    note="Outer-row anti-join; activity is not counted in token-event rows.",
)
add(
    "c18",
    "class_level",
    "staking_outer_active_hour_breadth",
    "For each dictionary-labeled liquid staking recipient owner with outer transactions, return count and the number of distinct UTC hours of day with activity; sort by owner.",
    f"""SELECT to_owner AS owner, COUNT(*) AS calls,
    COUNT(DISTINCT EXTRACT(HOUR FROM block_timestamp AT TIME ZONE 'UTC')) AS hours
    FROM {LT} WHERE to_category='staking' GROUP BY owner ORDER BY owner""",
    {"labeled_transactions": "to_owner block_timestamp to_category"},
    fact="transaction",
    classes=[("liquid staking", "staking", "to")],
    note="Known staking class only; distinct hour-of-day values range from zero through 23.",
)
add(
    "c19",
    "class_level",
    "lending_failed_outbound_gas_expense",
    "For dictionary-labeled money market owners sending failed outer transactions, return owner, failed count and total receipt gas used times gas price in wei; sort by total descending then owner.",
    f"""SELECT from_owner AS owner, COUNT(*) AS failed,
    SUM(CAST(receipt_gas_used AS NUMERIC)*gas_price_wei) AS gas_expense FROM {LT}
    WHERE from_category='lending' AND receipt_status=0 GROUP BY owner
    ORDER BY gas_expense DESC, owner""",
    {
        "labeled_transactions": "from_owner receipt_gas_used gas_price_wei from_category receipt_status"
    },
    fact="transaction",
    classes=[("money market", "lending", "from")],
    note="Contract-only owner sets may not originate outer transactions; an empty result is plausible.",
)
add(
    "c20",
    "class_level",
    "dex_endpoint_inventory_by_role",
    "In the pinned dictionary, summarize labeled DEX endpoint inventory by owner and address role, returning distinct address count; order by owner and role.",
    f"""SELECT owner, address_role, COUNT(DISTINCT address) AS addresses FROM {EL}
    WHERE category='dex' GROUP BY owner, address_role ORDER BY owner, address_role""",
    {"entity_labels_v1": "owner address_role address category"},
    classes=[("DEX", "dex", None)],
    note="Dictionary inventory, no transaction/event fact and no activity direction.",
)

# Seven direction diagnostics with explicitly wrong-direction contrasts.
p01 = f"""SELECT DATE(block_timestamp) AS day, COUNT(*) AS incoming,
COUNT(DISTINCT from_address) AS senders FROM {LT}
WHERE to_owner='Binance' AND value_wei>0 GROUP BY day ORDER BY day"""
add(
    "p01",
    "ambiguous_property",
    "direction_binance_positive_inbound_senders",
    "For positive-value outer transactions received by Binance, show each active date, incoming row count and distinct sender count; order by date.",
    p01,
    {"labeled_transactions": "block_timestamp from_address to_owner value_wei"},
    fact="transaction",
    entities=[("Binance", "Binance", "to", "endpoint")],
    focus="direction",
    note="Received selects outer to_address; declared positive value does not imply receipt success.",
    contrast=(p01.replace("to_owner", "from_owner"), "Wrongly selects the owner as outer sender."),
)
p02 = f"""SELECT transaction_type, COUNTIF(receipt_status=0) AS failed,
COUNTIF(receipt_status=1) AS succeeded, COUNT(*) AS total FROM {LT}
WHERE from_owner='OKX' GROUP BY transaction_type ORDER BY transaction_type"""
add(
    "p02",
    "ambiguous_property",
    "direction_okx_outbound_outcomes_by_type",
    "For outer transactions sent by OKX, give each transaction type's failed, successful and total counts, sorted by type.",
    p02,
    {"labeled_transactions": "transaction_type receipt_status from_owner"},
    fact="transaction",
    entities=[("OKX", "OKX", "from", "endpoint")],
    focus="direction",
    note="Sent selects outer from_address; unknown receipt statuses contribute to total.",
    contrast=(
        p02.replace("from_owner", "to_owner"),
        "Wrongly selects the owner as outer recipient.",
    ),
)
p03 = f"""SELECT COUNT(*) AS involved, COUNT(DISTINCT DATE(block_timestamp)) AS active_dates
FROM {LT} WHERE from_owner='Bitfinex' OR to_owner='Bitfinex'"""
add(
    "p03",
    "ambiguous_property",
    "direction_bitfinex_either_role_active_dates",
    "For outer transactions involving Bitfinex as either sender or recipient, return row count and distinct active UTC date count; count each internal transaction once.",
    p03,
    {"labeled_transactions": "block_timestamp from_owner to_owner"},
    fact="transaction",
    entities=[("Bitfinex", "Bitfinex", "either", "endpoint")],
    focus="direction",
    note="Either is a set union, not outgoing alone and not a sum of role counts.",
    contrast=(
        p03.replace("from_owner='Bitfinex' OR ", ""),
        "Drops the sender half of either-role union.",
    ),
)
p04 = f"""SELECT receipt_status, COUNT(*) AS transactions, SUM(value_wei) AS declared_wei
FROM {LT} WHERE from_owner='Binance' AND to_owner='OKX'
GROUP BY receipt_status ORDER BY receipt_status"""
add(
    "p04",
    "ambiguous_property",
    "direction_binance_to_okx_receipt_groups",
    "For outer transactions sent from Binance to OKX, return receipt status, row count and sum of declared wei, ordered by status.",
    p04,
    {"labeled_transactions": "receipt_status value_wei from_owner to_owner"},
    fact="transaction",
    entities=[("Binance", "Binance", "from", "endpoint"), ("OKX", "OKX", "to", "endpoint")],
    focus="direction",
    note="Ordered endpoint pair has two distinct entity direction annotations.",
    contrast=(
        p04.replace(
            "from_owner='Binance' AND to_owner='OKX'", "to_owner='Binance' AND from_owner='OKX'"
        ),
        "Reverses the ordered owner pair.",
    ),
)
p05 = f"""SELECT token_address, COUNT(DISTINCT to_address) AS recipients, COUNT(*) AS events
FROM {LL} WHERE from_owner='KuCoin' GROUP BY token_address ORDER BY token_address"""
add(
    "p05",
    "ambiguous_property",
    "direction_kucoin_token_sender_recipients",
    "For token events sent by KuCoin, report each token contract's distinct recipient count and event count; sort by token address.",
    p05,
    {"labeled_token_transfers": "token_address to_address from_owner"},
    fact="token_transfer",
    entities=[("KuCoin", "KuCoin", "from", "endpoint")],
    focus="direction",
    note="Transfer-event sender is not the outer transaction sender.",
    contrast=(
        p05.replace("from_owner", "to_owner"),
        "Wrongly constrains the event recipient owner.",
    ),
)
p06 = f"""SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
COUNT(DISTINCT transaction_hash) AS transactions FROM {LL}
WHERE to_owner='Gate.io' GROUP BY day ORDER BY day"""
add(
    "p06",
    "ambiguous_property",
    "direction_gate_token_receipt_multiplicity",
    "For token events received by Gate.io, show each active date's event count and distinct outer transaction count in date order.",
    p06,
    {"labeled_token_transfers": "block_timestamp transaction_hash to_owner"},
    fact="token_transfer",
    entities=[("Gate.io", "Gate.io", "to", "endpoint")],
    focus="direction",
    note="Received constrains the event endpoint, not the token contract nor outer recipient.",
    contrast=(p06.replace("to_owner", "from_owner"), "Wrongly constrains event sender owner."),
)
p07 = f"""SELECT COUNT(*) AS involved,
COUNTIF(from_owner='MEXC' AND to_owner='MEXC') AS internal_events FROM {LL}
WHERE from_owner='MEXC' OR to_owner='MEXC'"""
add(
    "p07",
    "ambiguous_property",
    "direction_mexc_event_union_internal_count",
    "For token events with MEXC at either endpoint, return total event count and the count having that owner at both endpoints. Count an internal event once in each output.",
    p07,
    {"labeled_token_transfers": "from_owner to_owner"},
    fact="token_transfer",
    entities=[("MEXC", "MEXC", "either", "endpoint")],
    focus="direction",
    note="Either-role filter and both-role output are different Boolean conditions.",
    contrast=(
        p07.replace(
            "WHERE from_owner='MEXC' OR to_owner='MEXC'",
            "WHERE from_owner='MEXC' AND to_owner='MEXC'",
        ),
        "Confuses either endpoint with both endpoints.",
    ),
)

# Seven fact diagnostics. Contrasts deliberately change row unit or drop a required fact.
p08 = f"""SELECT DATE(t.block_timestamp) AS day, COUNT(*) AS events,
COUNT(DISTINCT t.transaction_hash) AS transactions FROM {LT} t JOIN {TT} e
ON t.transaction_hash=e.transaction_hash AND t.block_number=e.block_number
AND t.block_hash=e.block_hash WHERE t.to_owner='Binance' GROUP BY day ORDER BY day"""
add(
    "p08",
    "ambiguous_property",
    "fact_logs_inside_binance_outer_calls",
    "For outer calls addressed to Binance, count the token-transfer events emitted inside those calls and the distinct calls that emitted them, per date in chronological order. Do not filter the transfer-event recipient.",
    p08,
    {
        "labeled_transactions": "block_timestamp transaction_hash block_number block_hash to_owner",
        "token_transfer_facts": "transaction_hash block_number block_hash",
    },
    fact="transaction_token_transfer_join",
    entities=[("Binance", "Binance", "to", "endpoint")],
    focus="fact",
    difficulty="hard",
    note="Entity direction applies to outer calls; log endpoints may be unrelated.",
    contrast=(
        f"""SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
    COUNT(DISTINCT transaction_hash) AS transactions FROM {LL}
    WHERE to_owner='Binance' GROUP BY day ORDER BY day""",
        "Substitutes token-event recipient for outer-call recipient.",
    ),
)
p09 = f"""WITH calls AS (SELECT t.transaction_hash, COUNT(*) AS logs FROM {LT} t JOIN {TT} e
ON t.transaction_hash=e.transaction_hash AND t.block_number=e.block_number
AND t.block_hash=e.block_hash WHERE t.from_owner='Binance'
GROUP BY t.transaction_hash HAVING logs>=2)
SELECT COUNT(*) AS outer_transactions FROM calls"""
add(
    "p09",
    "ambiguous_property",
    "fact_binance_outer_calls_with_multiple_logs",
    "How many distinct outer transactions sent by Binance emitted at least two token-transfer events? Count qualifying outer transactions rather than their logs.",
    p09,
    {
        "labeled_transactions": "transaction_hash block_number block_hash from_owner",
        "token_transfer_facts": "transaction_hash block_number block_hash",
    },
    fact="transaction_token_transfer_join",
    entities=[("Binance", "Binance", "from", "endpoint")],
    focus="fact",
    difficulty="hard",
    note="First groups logs by outer hash, then counts qualifying transactions once.",
    contrast=(
        p09.replace(
            "COUNT(*) AS outer_transactions FROM calls",
            "SUM(logs) AS outer_transactions FROM calls",
        ),
        "Sums qualifying logs instead of counting outer transactions.",
    ),
)
p10 = f"""SELECT token_address, COUNT(*) AS events,
COUNTIF(value_bignumeric>0) AS positive_events FROM {LL} WHERE to_owner='Binance'
GROUP BY token_address ORDER BY token_address"""
add(
    "p10",
    "ambiguous_property",
    "fact_binance_token_event_positive_counts",
    "For token-transfer log events received by Binance, return token contract, total log count and count with positive valid raw numeric value; sort by token address. Multiple logs in one outer transaction count separately.",
    p10,
    {"labeled_token_transfers": "token_address value_bignumeric to_owner"},
    fact="token_transfer",
    entities=[("Binance", "Binance", "to", "endpoint")],
    focus="fact",
    note="One row per token log; the positive raw-value bucket does not normalize units.",
    contrast=(
        p10.replace("COUNT(*) AS events", "COUNT(DISTINCT transaction_hash) AS events"),
        "Deduplicates events into transaction hashes and changes the requested row unit.",
    ),
)
p11 = f"""SELECT receipt_status, COUNT(*) AS outer_transactions, SUM(receipt_gas_used) AS gas
FROM {LT} WHERE to_owner='Tether' GROUP BY receipt_status ORDER BY receipt_status"""
add(
    "p11",
    "ambiguous_property",
    "fact_tether_contract_outer_call_gas",
    "For outer transactions calling the Tether contract, return receipt status, outer transaction count and total receipt gas used, ordered by status; a call need not emit a transfer log.",
    p11,
    {"labeled_transactions": "receipt_status receipt_gas_used to_owner"},
    fact="transaction",
    entities=[("Tether", "Tether", "to", "endpoint")],
    focus="fact",
    note="A token contract used as outer recipient has endpoint role for this intent.",
    contrast=(
        f"""SELECT t.receipt_status, COUNT(*) AS outer_transactions, SUM(t.receipt_gas_used) AS gas
    FROM {LT} t JOIN {TT} e ON t.transaction_hash=e.transaction_hash
    AND t.block_number=e.block_number AND t.block_hash=e.block_hash
    WHERE t.to_owner='Tether' GROUP BY t.receipt_status ORDER BY t.receipt_status""",
        "Requires token logs and duplicates gas once per log.",
    ),
)
p12 = f"""SELECT DATE(t.block_timestamp) AS day, COUNT(*) AS outer_transactions FROM {LT} t
WHERE t.to_owner='Uniswap V3' AND NOT EXISTS (SELECT 1 FROM {TT} e
WHERE e.transaction_hash=t.transaction_hash AND e.block_number=t.block_number
AND e.block_hash=t.block_hash) GROUP BY day ORDER BY day"""
add(
    "p12",
    "ambiguous_property",
    "fact_uniswap_v3_calls_without_logs",
    "For outer calls received by Uniswap V3 that emitted no token-transfer log, return active date and outer call count in date order.",
    p12,
    {
        "labeled_transactions": "block_timestamp to_owner transaction_hash block_number block_hash",
        "token_transfer_facts": "transaction_hash block_number block_hash",
    },
    fact="transaction_token_transfer_join",
    entities=[("Uniswap V3", "Uniswap V3", "to", "endpoint")],
    focus="fact",
    difficulty="hard",
    note="Absence of logs requires a second fact and NOT EXISTS.",
    contrast=(
        p12.replace("NOT EXISTS", "EXISTS"),
        "Counts calls with logs instead of those without logs.",
    ),
)
p13 = f"""SELECT e.token_address, COUNT(*) AS events,
COUNT(DISTINCT t.transaction_hash) AS outer_transactions FROM {LT} t JOIN {LL} e
ON t.transaction_hash=e.transaction_hash AND t.block_number=e.block_number
AND t.block_hash=e.block_hash WHERE t.from_owner='Binance' AND e.to_owner='OKX'
GROUP BY e.token_address ORDER BY e.token_address"""
add(
    "p13",
    "ambiguous_property",
    "fact_outer_sender_and_event_recipient_pair",
    "Count token events received by OKX inside outer transactions sent by Binance. Return token contract, event count and distinct outer transaction count, sorted by token address; use the outer sender rather than the event sender.",
    p13,
    {
        "labeled_transactions": "transaction_hash block_number block_hash from_owner",
        "labeled_token_transfers": "token_address transaction_hash block_number block_hash to_owner",
    },
    fact="transaction_token_transfer_join",
    entities=[("OKX", "OKX", "to", "endpoint"), ("Binance", "Binance", "from", "endpoint")],
    focus="fact",
    difficulty="hard",
    note="Each entity constrains a different fact: outer sender versus log recipient.",
    contrast=(
        p13.replace("t.from_owner='Binance'", "e.from_owner='Binance'"),
        "Uses event sender instead of the requested outer sender.",
    ),
)
p14 = f"""SELECT e.transaction_hash, e.log_index FROM {LL} e JOIN {TX} t
ON e.transaction_hash=t.transaction_hash AND e.block_number=t.block_number
AND e.block_hash=t.block_hash WHERE e.token_owner='Tether' AND t.receipt_status=0
ORDER BY e.transaction_hash, e.log_index"""
add(
    "p14",
    "ambiguous_property",
    "fact_usdt_logs_in_failed_outer_transactions",
    "List transaction hash and log index for USDT token-transfer events linked to failed outer transactions with receipt status 0, ordered by hash then log index.",
    p14,
    {
        "labeled_token_transfers": "transaction_hash log_index block_number block_hash token_owner",
        "transaction_facts": "transaction_hash block_number block_hash receipt_status",
    },
    fact="transaction_token_transfer_join",
    entities=[("USDT", "Tether", None, "token_contract")],
    focus="fact",
    difficulty="hard",
    note="Negative control: reverted outer transactions normally retain no logs; preserve a justified empty answer.",
    contrast=(
        p14.replace("t.receipt_status=0", "t.receipt_status=1"),
        "Selects successful outer transactions, losing the negative-control fact condition.",
    ),
)

# Six token-identity versus endpoint role diagnostics, including literal addresses.
p15 = f"""SELECT DATE(block_timestamp) AS day, COUNT(DISTINCT from_address) AS senders,
COUNT(DISTINCT to_address) AS recipients, COUNT(*) AS events FROM {LL}
WHERE token_owner='Tether' GROUP BY day ORDER BY day"""
add(
    "p15",
    "ambiguous_property",
    "role_usdt_token_daily_endpoint_reach",
    "For USDT as token identity, report each active date's distinct sender count, distinct recipient count and transfer-event count, ordered by date; do not restrict either endpoint to the token contract.",
    p15,
    {"labeled_token_transfers": "block_timestamp from_address to_address token_owner"},
    fact="token_transfer",
    entities=[("USDT", "Tether", None, "token_contract")],
    focus="address_role",
    note="Token mention maps to token_address, not sender or recipient.",
    contrast=(
        p15.replace("token_owner", "to_owner"),
        "Misreads token identity as event recipient endpoint.",
    ),
)
p16 = f"""SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT from_address) AS senders
FROM {LL} WHERE to_owner='Tether' GROUP BY token_address ORDER BY token_address"""
add(
    "p16",
    "ambiguous_property",
    "role_usdt_contract_as_event_recipient",
    "For token events whose recipient is the USDT contract address, return transferred token contract, event count and distinct sender count, sorted by token address; allow any transferred token.",
    p16,
    {"labeled_token_transfers": "token_address from_address to_owner"},
    fact="token_transfer",
    entities=[("USDT", "Tether", "to", "endpoint")],
    focus="address_role",
    note="The ticker names an endpoint here; token_address need not equal the mentioned contract.",
    contrast=(
        p16.replace("to_owner", "token_owner"),
        "Misreads recipient endpoint as transferred token identity.",
    ),
)
p17 = f"""SELECT receipt_status, COUNT(*) AS calls, SUM(value_wei) AS declared_wei FROM {TX}
WHERE to_address='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
GROUP BY receipt_status ORDER BY receipt_status"""
add(
    "p17",
    "ambiguous_property",
    "role_explicit_weth_outer_recipient",
    "For outer calls addressed to 0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2, return receipt status, call count and sum of declared wei, ordered by status. Treat the address as the called endpoint.",
    p17,
    {"transaction_facts": "receipt_status value_wei to_address"},
    fact="transaction",
    entities=[("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "WETH", "to", "endpoint")],
    focus="address_role",
    note="Explicit literal has explicit_address scope and known owner WETH.",
    contrast=(
        f"""SELECT t.receipt_status, COUNT(*) AS calls, SUM(t.value_wei) AS declared_wei FROM {TX} t
    WHERE EXISTS (SELECT 1 FROM {TT} e WHERE e.transaction_hash=t.transaction_hash
    AND e.block_number=t.block_number AND e.block_hash=t.block_hash
    AND e.token_address='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2')
    GROUP BY t.receipt_status ORDER BY t.receipt_status""",
        "Uses the literal as transferred token identity, ignoring the requested outer recipient.",
    ),
)
p18 = f"""SELECT COUNT(*) AS events, COUNTIF(from_address=to_address) AS self_events
FROM {LL} WHERE token_owner='WETH'"""
add(
    "p18",
    "ambiguous_property",
    "role_weth_token_self_event_counts",
    "For WETH as the transferred token, return total event count and the count whose sender equals recipient; the contract address is token identity, not an endpoint restriction.",
    p18,
    {"labeled_token_transfers": "from_address to_address token_owner"},
    fact="token_transfer",
    entities=[("WETH", "WETH", None, "token_contract")],
    focus="address_role",
    note="Self-event comparison does not make the named token an endpoint target.",
    contrast=(
        p18.replace("token_owner", "from_owner"),
        "Treats the token identity as sender of arbitrary token events.",
    ),
)
p19 = f"""SELECT DATE(block_timestamp) AS day, COUNT(*) AS events,
COUNT(DISTINCT from_address) AS senders FROM {LL}
WHERE token_owner='Chainlink' AND to_owner='Binance' GROUP BY day ORDER BY day"""
add(
    "p19",
    "ambiguous_property",
    "role_chainlink_token_binance_endpoint",
    "For Chainlink tokens received by Binance, show each active date's event count and distinct sender count, ordered by date. The first named owner specifies token identity and the second specifies the recipient endpoint.",
    p19,
    {"labeled_token_transfers": "block_timestamp from_address token_owner to_owner"},
    fact="token_transfer",
    entities=[
        ("Chainlink", "Chainlink", None, "token_contract"),
        ("Binance", "Binance", "to", "endpoint"),
    ],
    focus="address_role",
    note="Two entity targets have different roles and independent identity sets.",
    contrast=(
        p19.replace(
            "token_owner='Chainlink' AND to_owner='Binance'",
            "to_owner='Chainlink' AND token_owner='Binance'",
        ),
        "Swaps the token identity and recipient endpoint constraints.",
    ),
)
p20 = f"""SELECT token_address, COUNT(*) AS events, COUNT(DISTINCT to_address) AS recipients
FROM {TT} WHERE from_address='0xdac17f958d2ee523a2206206994597c13d831ec7'
GROUP BY token_address ORDER BY token_address"""
add(
    "p20",
    "ambiguous_property",
    "role_explicit_tether_event_sender",
    "For transfer events sent from 0xdac17f958d2ee523a2206206994597c13d831ec7 as an endpoint, return transferred token address, event count and distinct recipient count, ordered by token address; permit any token identity.",
    p20,
    {"token_transfer_facts": "token_address to_address from_address"},
    fact="token_transfer",
    entities=[("0xdac17f958d2ee523a2206206994597c13d831ec7", "Tether", "from", "endpoint")],
    focus="address_role",
    note="A token contract may be queried as an endpoint even when there are no matching sample events.",
    contrast=(
        p20.replace("WHERE from_address", "WHERE token_address"),
        "Uses literal token identity instead of sender endpoint.",
    ),
)


def materialize():
    manifest_path = DIRECTORY / "manifest.json"
    if json.loads(manifest_path.read_text())["status"] != "draft":
        raise ValueError("T09A packaging requires a draft; a frozen benchmark is immutable")
    # A rerun must not discard a human's review or manually documented empty reasons.
    existing_reviews = read_jsonl(DIRECTORY / "reviews.jsonl")
    if any(r["status"] != "pending" for r in existing_reviews):
        raise ValueError(
            "Review has started; edit the draft artifacts and rebind review deliberately"
        )
    previous = {c["id"]: c for c in read_jsonl(DIRECTORY / "test.jsonl")}
    for case in cases:
        old = previous.get(case["id"], {})
        if (
            case["empty_reason"] is None
            and old.get("question") == case["question"]
            and old.get("sql") == case["sql"]
        ):
            case["empty_reason"] = old.get("empty_reason")
    assert len(cases) == len(annotations) == 100
    assert len({c["family_id"] for c in cases}) == 100
    write_jsonl(DIRECTORY / "test.jsonl", cases)
    write_jsonl(DIRECTORY / "annotations.jsonl", annotations)
    write_jsonl(
        DIRECTORY / "reviews.jsonl",
        [pending_review(c, a) for c, a in zip(cases, annotations, strict=True)],
    )
    write_jsonl(DIRECTORY / "author-notes.jsonl", notes)
    write_jsonl(DIRECTORY / "property-contrasts.jsonl", contrasts)
    write_json(manifest_path, draft_manifest(DIRECTORY, DIRECTORY.parents[1], DICTIONARY_DIR))


if __name__ == "__main__":
    materialize()

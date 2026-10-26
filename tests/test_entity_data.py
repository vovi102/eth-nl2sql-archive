"""Entity dataset contracts and raw-table semantic witnesses."""

import json

from conftest import BINANCE, TETHER, USER, ts, tx

from eth_nl2sql.config import DATA_DIR, DICTIONARY_DIR, read_jsonl
from eth_nl2sql.data.dataset_audit import _review_status, owner_support, relation_oracle
from eth_nl2sql.data.entities import SOURCE, split_audit


def test_all_entity_templates_present_on_both_sides_of_family_split():
    templates = json.loads((DATA_DIR / "templates/entity_templates.json").read_text())
    assert len(templates) == 10
    expected = {t["id"] for t in templates}
    for split in ("train", "dev"):
        rows = [r for r in read_jsonl(DATA_DIR / f"{split}.jsonl") if r.get("source") == SOURCE]
        assert {r["template_id"] for r in rows} == expected


def test_entity_test_coverage_and_unambiguous_aliases():
    rows = [r for r in read_jsonl(DATA_DIR / "test.jsonl") if r["subset"] == "entity"]
    assert len(rows) == 50
    assert {s for r in rows for s in r["specifics"]} == {
        "multi_address",
        "alias",
        "class_level",
        "ambiguous_property",
    }
    multi = [r for r in rows if "multi_address" in r["specifics"]]
    owners = {o for r in multi for o in r["entity_expectations"]["owners"]}
    assert len(owners) == 34
    assert "Tornado Cash" not in owners
    aliases = json.loads((DICTIONARY_DIR / "aliases.json").read_text())
    for row in rows:
        for alias, owner in row["entity_expectations"].get("aliases", {}).items():
            assert alias.casefold() in row["question"].casefold()
            assert aliases[alias.casefold()] == owner


def test_semantic_review_covers_current_question_and_sql_and_expires_on_edit():
    rows = read_jsonl(DATA_DIR / "test.jsonl")
    review = json.loads((DATA_DIR / "test-review.json").read_text())
    assert _review_status(rows, review)["passed"]
    modified = [{**rows[0], "question": "A different intent"}, *rows[1:]]
    result = _review_status(modified, review)
    assert not result["passed"]
    assert result["stale_or_missing_ids"] == [rows[0]["id"]]


def test_raw_witness_rejects_single_address_and_counts_internal_transaction_once(store):
    store.execute(
        "INSERT INTO transactions VALUES (" + ", ".join("?" * 14) + ")",
        tx("0xINTERNAL", BINANCE[0], BINANCE[1], 1, day=6),
    )
    expected = {
        "owners": ["Binance"],
        "fact": "transactions",
        "direction": "either",
        "start_date": "2026-06-01",
        "end_date": "2026-06-08",
    }
    support = owner_support(store, expected)
    assert support["matching_events"] == 4
    assert sum(support["per_address"].values()) == 5
    assert support["active_addresses"] == 2
    assert support["max_single_address_events"] == 3
    assert support["single_address_changes_answer"]
    expected["direction"] = "from"
    expected["success_only"] = True
    assert owner_support(store, expected)["matching_events"] == 1


def test_class_oracle_uses_category_without_requiring_named_owner(store):
    expected = {
        "owners": [],
        "fact": "transactions",
        "direction": "to",
        "start_date": "2026-06-01",
        "end_date": "2026-06-08",
        "category": "exchange",
    }
    assert relation_oracle(store, expected) == (("Binance", 2),)


def test_relation_oracle_distinguishes_outer_recipient_from_log_recipient(store):
    # T3 has Binance sending to USER. Its added transfer log goes to Binance.
    # Another log with the same tx hash but a different block must not join.
    store.executemany(
        "INSERT INTO token_transfers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (TETHER, USER, BINANCE[0], "1", "0xT3", 7, ts(3), 300, "0xB300"),
            (TETHER, USER, BINANCE[0], "1", "0xT3", 8, ts(3), 300, "0xOTHERBLOCK"),
        ],
    )
    expected = {
        "owners": ["Binance", "Binance"],
        "fact": "transactions",
        "direction": "from_to",
        "start_date": "2026-06-01",
        "end_date": "2026-06-08",
    }
    assert relation_oracle(store, expected) == ((0,),)
    expected.update(fact="joined_transaction_token_transfer", direction="tx_from_log_to")
    assert relation_oracle(store, expected) == ((1,),)


def test_leakage_checks_canonical_sql_despite_different_text_and_format():
    rows = {
        "train": [
            {
                "id": "a",
                "question": "Train wording",
                "family_id": "f1",
                "sql": "SELECT COUNT(*) AS n FROM "
                "`nl2sparql-thesis.nl2sparql_analytics.entity_labels_v1`",
            }
        ],
        "dev": [],
        "test": [
            {
                "id": "b",
                "question": "Unrelated test wording",
                "family_id": "f2",
                "sql": "select count(*) as n\nfrom "
                "`nl2sparql-thesis.nl2sparql_analytics.entity_labels_v1`",
            }
        ],
    }
    report = split_audit(rows)
    assert not report["passed"]
    pair = report["pairs"]["train/test"]
    assert pair["canonical_sql_overlap_count"] == 1
    assert not pair["normalized_question_overlap"]
    assert not pair["family_overlap"]

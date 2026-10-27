"""Parity gates bind the dictionary, actual differences and their explanations."""

import hashlib
import json

from eth_nl2sql.config import DATA_DIR
from eth_nl2sql.results import row_digests
from eth_nl2sql.store.execute import execute
from eth_nl2sql.store.manifest import file_digest
from eth_nl2sql.store.parity import check

P = "nl2sparql-thesis.nl2sparql_analytics"


def references(store, tmp_path, *, mismatch=False):
    golds = []
    for i in range(20):
        sql = (
            f"SELECT count(*) + {i} AS n FROM `{P}.transaction_facts`"
            "(DATE '2026-06-01', DATE '2026-06-08')"
        )
        rows = execute(store, sql).rows
        golds.append(
            {
                "sql": sql,
                "sql_sha256": hashlib.sha256(sql.encode()).hexdigest(),
                "fields": [{"name": "n"}],
                "row_count": len(rows),
                "row_digests": row_digests(rows),
            }
        )
    if mismatch:
        golds[-1]["row_digests"] = row_digests([(99999,)])
    witnesses = [{"id": "w1", "sql": golds[0]["sql"], "row_count": 1}]
    a, b = tmp_path / "gold.json", tmp_path / "witness.json"
    a.write_text(json.dumps(golds))
    b.write_text(json.dumps(witnesses))
    profile = {
        "complete_snapshot": True,
        "labels_sha256": file_digest(DATA_DIR / "entities/v1/entities.json"),
    }
    store.execute(
        "INSERT OR REPLACE INTO store_metadata VALUES ('profile', ?)", [json.dumps(profile)]
    )
    return a, b


def test_parity_requires_v1_dictionary(store, tmp_path):
    a, b = references(store, tmp_path)
    store.execute(
        "UPDATE store_metadata SET value=? WHERE key='profile'",
        [json.dumps({"complete_snapshot": True, "labels_sha256": "v2"})],
    )
    report = check(store, a, b)
    assert report["skipped"] and not report["passed"]
    assert "v1" in report["reason"]


def test_complete_matching_parity_passes_with_reference_provenance(store, tmp_path):
    a, b = references(store, tmp_path)
    report = check(store, a, b)
    assert report["passed"] and report["gold_exact"]["rate"] == 1
    assert report["references"]["gold_sha256"] == file_digest(a)


def test_numeric_gate_requires_explanations_bound_to_the_observed_mismatch(store, tmp_path):
    a, b = references(store, tmp_path, mismatch=True)
    report = check(store, a, b)
    assert report["numeric_gate_passed"] and report["gold_exact"]["rate"] == 0.95
    assert not report["passed"] and len(report["unexplained"]) == 1
    mismatch = report["gold_mismatches"][0]
    explanation = {
        "reason": "Test evidence",
        "evidence": ["captured-results.json"],
        "observed_sha256": "stale",
    }
    explanations = {mismatch["key"]: explanation}
    assert not check(store, a, b, explanations=explanations)["passed"]
    explanation["observed_sha256"] = mismatch["observed_sha256"]
    assert check(store, a, b, explanations=explanations)["passed"]


def test_witness_mismatch_must_also_be_explained(store, tmp_path):
    a, b = references(store, tmp_path)
    witnesses = json.loads(b.read_text())
    witnesses[0]["row_count"] = 2
    b.write_text(json.dumps(witnesses))
    report = check(store, a, b)
    assert report["gold_exact"]["rate"] == 1 and not report["passed"]
    assert report["unexplained"] == ["witness:w1"]


def test_empty_references_cannot_pass(store, tmp_path):
    a, b = references(store, tmp_path)
    a.write_text("[]")
    report = check(store, a, b)
    assert not report["passed"] and report["skipped"]

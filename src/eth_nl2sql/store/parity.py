"""Check that the local store reproduces results observed on BigQuery.

Two references come from luanvan: the row digests of 88 gold queries executed
on BigQuery in the c03 campaign, and the row counts of 206 Stage A witness
queries. Both require the store to be built with the v1 label dictionary.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

from eth_nl2sql.results import is_order_sensitive, results_equal, row_digests
from eth_nl2sql.store.execute import ExecutionError, execute
from eth_nl2sql.store.manifest import store_profile
from eth_nl2sql.validation import ValidationError

GATE = 0.95


def check(con: duckdb.DuckDBPyConnection, gold_path: Path, witness_path: Path) -> dict:
    gold_cases = json.loads(gold_path.read_text())
    profile = store_profile(con)
    if not profile.get("complete_snapshot"):
        witnesses = json.loads(witness_path.read_text())
        return {
            "passed": False,
            "skipped": True,
            "gate": GATE,
            "reason": "parity requires a complete snapshot; this store is sampled or unrecorded",
            "store": profile,
            "gold_exact": {"matched": 0, "total": len(gold_cases), "rate": None},
            "witness_row_counts": {"matched": 0, "total": len(witnesses), "rate": None},
            "gold_mismatches": [],
            "witness_mismatches": [],
        }
    mismatches = []
    gold_matches = 0
    for case in gold_cases:
        try:
            result = execute(con, case["sql"], timeout_s=600)
        except (ValidationError, ExecutionError) as exc:
            mismatches.append({"sql_sha256": case["sql_sha256"], "reason": f"{exc.code}: {exc}"})
            continue
        local = row_digests(result.rows)
        if results_equal(
            case["row_digests"],
            local,
            gold_arity=len(case["fields"]),
            predicted_arity=len(result.columns),
            ordered=is_order_sensitive(case["sql"]),
        ):
            gold_matches += 1
        else:
            mismatches.append(
                {
                    "sql_sha256": case["sql_sha256"],
                    "reason": "rows differ",
                    "bigquery_rows": case["row_count"],
                    "local_rows": len(result.rows),
                    "columns": [field["name"] for field in case["fields"]],
                    "sql": case["sql"],
                }
            )

    witnesses = json.loads(witness_path.read_text())
    witness_matches = 0
    witness_mismatches = []
    for witness in witnesses:
        try:
            rows = len(execute(con, witness["sql"], timeout_s=600).rows)
        except (ValidationError, ExecutionError) as exc:
            witness_mismatches.append({"id": witness["id"], "reason": f"{exc.code}: {exc}"})
            continue
        if rows == witness["row_count"]:
            witness_matches += 1
        else:
            witness_mismatches.append(
                {"id": witness["id"], "bigquery_rows": witness["row_count"], "local_rows": rows}
            )

    gold_rate = gold_matches / len(gold_cases)
    return {
        "gold_exact": {"matched": gold_matches, "total": len(gold_cases), "rate": gold_rate},
        "witness_row_counts": {
            "matched": witness_matches,
            "total": len(witnesses),
            "rate": witness_matches / len(witnesses),
        },
        "gate": GATE,
        "passed": gold_rate >= GATE,
        "gold_mismatches": mismatches,
        "witness_mismatches": witness_mismatches,
    }

"""Check that the local store reproduces results observed on BigQuery.

Two references come from luanvan: the row digests of 88 gold queries executed
on BigQuery in the c03 campaign, and the row counts of 206 Stage A witness
queries. Both require the store to be built with the v1 label dictionary.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import duckdb

from eth_nl2sql.config import DATA_DIR
from eth_nl2sql.results import is_order_sensitive, results_equal, row_digests
from eth_nl2sql.store.execute import ExecutionError, execute
from eth_nl2sql.store.manifest import file_digest, store_profile
from eth_nl2sql.validation import ValidationError

GATE = 0.95


def check(
    con: duckdb.DuckDBPyConnection,
    gold_path: Path,
    witness_path: Path,
    *,
    explanations: dict | None = None,
) -> dict:
    gold_cases = json.loads(gold_path.read_text())
    witnesses = json.loads(witness_path.read_text())
    profile = store_profile(con)
    reason = None
    if not profile.get("complete_snapshot"):
        reason = "parity requires a complete snapshot; this store is sampled or unrecorded"
    elif profile.get("labels_sha256") != file_digest(DATA_DIR / "entities/v1/entities.json"):
        reason = "parity requires the frozen v1 label dictionary used by the BigQuery fixtures"
    elif not gold_cases or not witnesses:
        reason = "parity requires nonempty BigQuery gold and witness references"
    if reason:
        return {
            "passed": False,
            "skipped": True,
            "gate": GATE,
            "reason": reason,
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
                    "expected_digests": case["row_digests"][:20],
                    "local_digests": list(local[:20]),
                }
            )

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
                {
                    "id": witness["id"],
                    "bigquery_rows": witness["row_count"],
                    "local_rows": rows,
                    "sql": witness["sql"],
                }
            )

    unexplained = []
    for kind, differences, field in (
        ("gold", mismatches, "sql_sha256"),
        ("witness", witness_mismatches, "id"),
    ):
        for mismatch in differences:
            key = f"{kind}:{mismatch[field]}"
            binding = hashlib.sha256(json.dumps(mismatch, sort_keys=True).encode()).hexdigest()
            explanation = (explanations or {}).get(key, {})
            explained = (
                isinstance(explanation, dict)
                and bool(str(explanation.get("reason", "")).strip())
                and bool(explanation.get("evidence"))
                and explanation.get("observed_sha256") == binding
            )
            mismatch.update(key=key, observed_sha256=binding, explained=bool(explained))
            if explained:
                mismatch["explanation"] = explanation
            else:
                unexplained.append(key)
    gold_rate = gold_matches / len(gold_cases)
    return {
        "store": profile,
        "skipped": False,
        "references": {
            "gold_sha256": file_digest(gold_path),
            "witness_sha256": file_digest(witness_path),
        },
        "gold_exact": {"matched": gold_matches, "total": len(gold_cases), "rate": gold_rate},
        "witness_row_counts": {
            "matched": witness_matches,
            "total": len(witnesses),
            "rate": witness_matches / len(witnesses),
        },
        "gate": GATE,
        "passed": gold_rate >= GATE and not unexplained,
        "numeric_gate_passed": gold_rate >= GATE,
        "all_differences_explained": not unexplained,
        "unexplained": unexplained,
        "gold_mismatches": mismatches,
        "witness_mismatches": witness_mismatches,
    }

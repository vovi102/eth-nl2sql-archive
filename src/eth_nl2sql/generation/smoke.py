"""Compile model outputs against the real, empty managed schema before resuming.

No gold queries or snapshot data are needed. This checks executable SQL, not EX.
The production executor enforces TVF arity/date windows and DuckDB binds columns.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence

from eth_nl2sql.generation.extract import extract_sql
from eth_nl2sql.store.compile import compile_queries


def inspect_predictions(rows: Sequence[Mapping], *, timeout_s: float = 10.0) -> dict:
    queries = []
    for row in rows:
        sql, format_ok = extract_sql(row.get("raw_output") or "")
        queries.append(
            {
                "id": row["id"],
                "sql": sql,
                "format_ok": format_ok,
                "finish_reason": row.get("finish_reason"),
            }
        )
    cases = compile_queries(queries, timeout_s=timeout_s)
    counts = dict(Counter(case["status"] for case in cases))
    return {
        "rows": len(cases),
        "passed": bool(cases) and counts.get("ok", 0) == len(cases),
        "compile_passed": counts.get("ok", 0),
        "status_counts": counts,
        "purpose": "TVF signatures/windows and compilation on empty schema; no EX computed",
        "cases": cases,
    }


def require_smoke_pass(report: Mapping) -> None:
    if not report["passed"]:
        raise ValueError(f"SQL smoke failed: {report['status_counts']}; inspect smoke report")

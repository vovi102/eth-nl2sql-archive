"""Compile SQL against an empty managed store, without requiring snapshot data."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from eth_nl2sql.store.build import connect, create_schema
from eth_nl2sql.store.execute import ExecutionError, execute
from eth_nl2sql.validation import ValidationError


def compile_queries(rows: Iterable[Mapping], *, timeout_s: float = 60.0) -> list[dict]:
    results = []
    con = connect()
    try:
        create_schema(con)
        for row in rows:
            case = {**row, "status": "no_sql"}
            if row.get("sql"):
                try:
                    execute(con, row["sql"], timeout_s=timeout_s)
                    case["status"] = "ok"
                except (ValidationError, ExecutionError) as exc:
                    case.update(status=exc.code, error=str(exc))
            results.append(case)
    finally:
        con.close()
    return results

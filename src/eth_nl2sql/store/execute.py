"""Execute GoogleSQL against the local DuckDB store.

The query is validated (`validation.py`), its managed relation names are
rewritten to the local views/macros, and it is transpiled to DuckDB with SQLGlot.
Table-function date arguments are evaluated before execution so that the
BigQuery bounds rule (start < end, at most 31 days) and the snapshot coverage
are enforced even when a window would select no rows.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import date, datetime

import duckdb
from sqlglot import exp

from eth_nl2sql.store.build import MAX_WINDOW_DAYS, SNAPSHOT_END, SNAPSHOT_START
from eth_nl2sql.validation import PROJECT_DATASET, relation_name, validate_sql

TABLE_FUNCTIONS = {
    "transaction_facts": ("start_date", "end_date"),
    "block_facts": ("start_date", "end_date"),
    "token_transfer_facts": ("start_date", "end_date"),
    "labeled_transactions": ("start_date", "end_date"),
    "labeled_token_transfers": ("start_date", "end_date"),
    "contract_dimension": ("end_date",),
}

_COMPILE_ERRORS = (duckdb.BinderException, duckdb.CatalogException, duckdb.ParserException)


class ExecutionError(Exception):
    """A query that could not run. ``code`` is one of: window_invalid,
    window_outside_snapshot, compile_error, runtime_error, timeout."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class QueryResult:
    columns: tuple[str, ...]
    types: tuple[str, ...]
    rows: tuple[tuple, ...]
    elapsed_ms: float


def to_duckdb(sql: str) -> tuple[str, list[tuple[str, list[exp.Expression]]]]:
    """Return DuckDB SQL plus every table-function call with its argument expressions."""
    tree = validate_sql(sql)
    calls: list[tuple[str, list[exp.Expression]]] = []
    for table in list(tree.find_all(exp.Table)):
        name = relation_name(table)
        if not name.startswith(f"{PROJECT_DATASET}."):
            continue
        short = name.rsplit(".", 1)[-1]
        if isinstance(table.this, exp.Anonymous):
            args = list(table.this.expressions)
            table.set("this", exp.Anonymous(this=short, expressions=args))
            calls.append((short, args))
        else:
            if short in TABLE_FUNCTIONS:
                raise ExecutionError("compile_error", f"{short} requires date arguments")
            table.set("this", exp.to_identifier(short))
        table.set("db", None)
        table.set("catalog", None)
    return tree.sql(dialect="duckdb"), calls


_TIMESTAMP_TYPES = {
    exp.DataType.Type.TIMESTAMP,
    exp.DataType.Type.TIMESTAMPTZ,
    exp.DataType.Type.DATETIME,
}


def _as_date(value: object) -> date | None:
    # DuckDB returns DATE + INTERVAL as a timestamp, where BigQuery keeps a DATE.
    if isinstance(value, datetime):
        return value.date() if value.time() == datetime.min.time() else None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def check_windows(
    con: duckdb.DuckDBPyConnection, calls: list[tuple[str, list[exp.Expression]]]
) -> None:
    for name, args in calls:
        parameters = TABLE_FUNCTIONS.get(name)
        if parameters is None:
            raise ExecutionError("compile_error", f"{name} is not a table function")
        if len(args) != len(parameters):
            raise ExecutionError(
                "window_invalid", f"{name} expects {len(parameters)} DATE argument(s)"
            )
        if any(isinstance(arg, exp.Cast) and arg.to.this in _TIMESTAMP_TYPES for arg in args):
            raise ExecutionError(
                "window_invalid", f"{name} arguments must be DATEs, not timestamps"
            )
        try:
            raw = con.execute(
                "SELECT " + ", ".join(arg.sql(dialect="duckdb") for arg in args)
            ).fetchone()
        except duckdb.Error as exc:
            raise ExecutionError(
                "window_invalid", f"{name} arguments must be constant dates: {exc}"
            ) from exc
        values = dict(zip(parameters, (_as_date(value) for value in raw), strict=True))
        if any(value is None for value in values.values()):
            raise ExecutionError("window_invalid", f"{name} arguments must be non-null DATEs")
        end = values["end_date"]
        start = values.get("start_date")
        if start is not None:
            if start >= end or (end - start).days > MAX_WINDOW_DAYS:
                raise ExecutionError(
                    "window_invalid",
                    f"{name} window must be half-open with at most {MAX_WINDOW_DAYS} days",
                )
            if start < SNAPSHOT_START or end > SNAPSHOT_END:
                raise ExecutionError(
                    "window_outside_snapshot",
                    f"{name} window {start}..{end} is outside the local snapshot "
                    f"{SNAPSHOT_START}..{SNAPSHOT_END}",
                )
        elif not SNAPSHOT_START < end <= SNAPSHOT_END:
            raise ExecutionError(
                "window_outside_snapshot", f"{name} end_date {end} is outside the local snapshot"
            )


def execute(con: duckdb.DuckDBPyConnection, sql: str, *, timeout_s: float = 60.0) -> QueryResult:
    """Run one validated GoogleSQL query. Raises ValidationError or ExecutionError."""
    duck_sql, calls = to_duckdb(sql)
    check_windows(con, calls)
    cursor = con.cursor()
    cursor.execute("SET TimeZone = 'UTC'")
    timer = threading.Timer(timeout_s, cursor.interrupt)
    started = time.perf_counter()
    timer.start()
    try:
        cursor.execute(duck_sql)
        rows = tuple(cursor.fetchall())
        description = cursor.description
    except duckdb.InterruptException as exc:
        raise ExecutionError("timeout", f"query exceeded {timeout_s:g}s") from exc
    except _COMPILE_ERRORS as exc:
        raise ExecutionError("compile_error", str(exc)) from exc
    except duckdb.Error as exc:
        raise ExecutionError("runtime_error", str(exc)) from exc
    finally:
        timer.cancel()
        cursor.close()
    return QueryResult(
        columns=tuple(column[0] for column in description),
        types=tuple(str(column[1]) for column in description),
        rows=rows,
        elapsed_ms=(time.perf_counter() - started) * 1000.0,
    )

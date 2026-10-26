"""Typed result canonicalization and comparison (ported from luanvan `result_semantics.py`).

Row digests are byte-compatible with luanvan, so local results can be compared
with the BigQuery gold digests recorded in luanvan's c03 campaign. Values are
tagged by their Python type as returned by DuckDB (int/Decimal/float -> number,
datetime -> UTC timestamp, ...). ``float_digits`` optionally rounds floats to a
number of significant digits, which execution-accuracy scoring uses so that
equivalent formulations (e.g. AVG vs SUM/COUNT) are not split by the last bit.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, time
from decimal import Decimal

from sqlglot import exp

from eth_nl2sql.validation import parse_query


def _decimal_text(value: int | Decimal | float) -> str:
    number = value if isinstance(value, Decimal) else Decimal(str(value))
    if number.is_zero():
        return "0"
    rendered = format(number.normalize(), "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def canonical_value(value: object, *, float_digits: int | None = None) -> object:
    """Return luanvan's tagged, immutable representation of one result value."""
    if value is None:
        return ("null",)
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, float):
        if math.isnan(value):
            return ("float_special", "nan")
        if math.isinf(value):
            return ("float_special", "+inf" if value > 0 else "-inf")
        if float_digits is not None:
            value = float(f"{value:.{float_digits}g}")
        return ("number", _decimal_text(value))
    if isinstance(value, (int, Decimal)):
        return ("number", _decimal_text(value))
    if isinstance(value, datetime):
        aware = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        return ("timestamp", aware.astimezone(UTC).isoformat().replace("+00:00", "Z"))
    if isinstance(value, date):
        return ("date", value.isoformat())
    if isinstance(value, time):
        return ("time", value.isoformat())
    if isinstance(value, (bytes, bytearray, memoryview)):
        return ("bytes", base64.b64encode(bytes(value)).decode("ascii"))
    if isinstance(value, str):
        return ("string", value)
    if isinstance(value, Mapping):
        return (
            "struct",
            tuple(
                (str(key), canonical_value(item, float_digits=float_digits))
                for key, item in sorted(value.items())
            ),
        )
    if isinstance(value, Sequence):
        return ("array", tuple(canonical_value(item, float_digits=float_digits) for item in value))
    raise TypeError(f"unsupported result value: {type(value).__name__}")


def _json_ready(value: object) -> object:
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    return value


def canonical_json(value: object) -> bytes:
    """luanvan's canonical JSON: compact, sorted keys, UTF-8, one trailing newline."""
    text = json.dumps(
        _json_ready(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (text + "\n").encode("utf-8")


def row_digests(
    rows: Sequence[Sequence[object]], *, float_digits: int | None = None
) -> tuple[str, ...]:
    """Digest each row in its returned order."""
    return tuple(
        hashlib.sha256(
            canonical_json(
                tuple(canonical_value(value, float_digits=float_digits) for value in row)
            )
        ).hexdigest()
        for row in rows
    )


def is_order_sensitive(sql: str) -> bool:
    """A gold query defines a row sequence only when it has a top-level ORDER BY."""
    return parse_query(sql).args.get("order") is not None


def results_equal(
    gold: Sequence[str],
    predicted: Sequence[str],
    *,
    gold_arity: int,
    predicted_arity: int,
    ordered: bool,
) -> bool:
    """Compare digests under the gold query's order semantics; column names are ignored."""
    if gold_arity != predicted_arity or len(gold) != len(predicted):
        return False
    if ordered:
        return tuple(gold) == tuple(predicted)
    return Counter(gold) == Counter(predicted)


def answer_scores(gold: Sequence[str], predicted: Sequence[str]) -> tuple[float, float, float]:
    """Multiset precision, recall and F1 over row digests."""
    gold_counter, predicted_counter = Counter(gold), Counter(predicted)
    if not gold_counter and not predicted_counter:
        return 1.0, 1.0, 1.0
    if not gold_counter or not predicted_counter:
        return 0.0, 0.0, 0.0
    overlap = sum((gold_counter & predicted_counter).values())
    precision = overlap / sum(predicted_counter.values())
    recall = overlap / sum(gold_counter.values())
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def _sql(node: exp.Expression) -> str:
    return node.sql(dialect="bigquery", pretty=False)


def _normalized_aliases(expression: exp.Expression) -> exp.Expression:
    normalized = expression.copy()
    alias_map: dict[str, str] = {}
    for index, table in enumerate(normalized.find_all(exp.Table)):
        if table.alias:
            replacement = f"_t{index}"
            alias_map[table.alias.casefold()] = replacement
            table.set("alias", exp.TableAlias(this=exp.to_identifier(replacement)))
    for column in normalized.find_all(exp.Column):
        if column.table and column.table.casefold() in alias_map:
            column.set("table", exp.to_identifier(alias_map[column.table.casefold()]))
    for index, alias in enumerate(normalized.find_all(exp.Alias)):
        alias.set("alias", exp.to_identifier(f"_c{index}"))
    return normalized


def _replace_literals(expression: exp.Expression) -> exp.Expression:
    def transform(node: exp.Expression) -> exp.Expression:
        if isinstance(node, exp.Literal):
            return exp.Literal.string("__STRING__") if node.is_string else exp.Literal.number("0")
        if isinstance(node, exp.Boolean):
            return exp.true()
        return node

    return expression.transform(transform, copy=True)


def sql_signatures(sql: str) -> tuple[str, str]:
    """Return (canonical SQL, alias- and literal-normalized structure) as in luanvan."""
    expression = parse_query(sql)
    canonical = _sql(expression)
    structure = _sql(_replace_literals(_normalized_aliases(expression)))
    return canonical, structure

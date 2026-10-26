"""Execution-based evaluation of generated SQL on the local store.

For each test question the gold SQL and the extracted prediction run on the
same DuckDB store; execution accuracy (EX) compares typed result rows under the
gold query's order semantics. Every failure stays in the denominator.
"""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

import duckdb

from eth_nl2sql.generation.extract import extract_sql
from eth_nl2sql.results import (
    answer_scores,
    is_order_sensitive,
    results_equal,
    row_digests,
    sql_signatures,
)
from eth_nl2sql.store.execute import ExecutionError, execute
from eth_nl2sql.validation import ValidationError

STATUSES = (
    "ok",
    "no_sql",
    "parse_error",
    "unsafe",
    "window_invalid",
    "window_outside_snapshot",
    "compile_error",
    "runtime_error",
    "timeout",
)


@dataclass(frozen=True)
class Gold:
    digests: tuple[str, ...]
    arity: int
    ordered: bool
    canonical: str
    structure: str


@dataclass
class CaseResult:
    id: str
    subset: str
    specifics: list[str]
    difficulty: str
    status: str
    format_ok: bool
    execution_match: bool
    exact_match: bool
    structural_match: bool
    answer_f1: float
    generation_ms: float | None
    execution_ms: float | None
    predicted_sql: str | None
    error: str | None


def run_gold(
    con: duckdb.DuckDBPyConnection, cases: Sequence[Mapping], *, float_digits: int, timeout_s: float
) -> dict[str, Gold]:
    """Execute every gold query; a failing gold query is a data error, not a model error."""
    gold = {}
    for case in cases:
        result = execute(con, case["sql"], timeout_s=timeout_s)
        canonical, structure = sql_signatures(case["sql"])
        gold[case["id"]] = Gold(
            row_digests(result.rows, float_digits=float_digits),
            len(result.columns),
            is_order_sensitive(case["sql"]),
            canonical,
            structure,
        )
    return gold


def score_case(
    con: duckdb.DuckDBPyConnection,
    case: Mapping,
    prediction: Mapping | None,
    gold: Gold,
    *,
    float_digits: int,
    timeout_s: float,
) -> CaseResult:
    raw = (prediction or {}).get("raw_output") or ""
    sql, format_ok = extract_sql(raw)
    result = CaseResult(
        id=case["id"],
        subset=case.get("subset", "generic"),
        specifics=list(case.get("specifics", [])),
        difficulty=case.get("difficulty", "unknown"),
        status="no_sql",
        format_ok=format_ok,
        execution_match=False,
        exact_match=False,
        structural_match=False,
        answer_f1=0.0,
        generation_ms=(prediction or {}).get("latency_ms"),
        execution_ms=None,
        predicted_sql=sql,
        error=None,
    )
    if sql is None:
        return result
    try:
        executed = execute(con, sql, timeout_s=timeout_s)
    except (ValidationError, ExecutionError) as exc:
        result.status = exc.code
        result.error = str(exc)[:500]
        return result
    canonical, structure = sql_signatures(sql)
    digests = row_digests(executed.rows, float_digits=float_digits)
    result.status = "ok"
    result.execution_ms = executed.elapsed_ms
    result.exact_match = canonical == gold.canonical
    result.structural_match = structure == gold.structure
    result.execution_match = results_equal(
        gold.digests,
        digests,
        gold_arity=gold.arity,
        predicted_arity=len(executed.columns),
        ordered=gold.ordered,
    )
    result.answer_f1 = answer_scores(gold.digests, digests)[2]
    return result


def evaluate_predictions(
    con: duckdb.DuckDBPyConnection,
    cases: Sequence[Mapping],
    predictions: Mapping[str, Mapping],
    *,
    float_digits: int = 12,
    timeout_s: float = 120.0,
) -> list[CaseResult]:
    gold = run_gold(con, cases, float_digits=float_digits, timeout_s=timeout_s)
    return [
        score_case(
            con,
            case,
            predictions.get(case["id"]),
            gold[case["id"]],
            float_digits=float_digits,
            timeout_s=timeout_s,
        )
        for case in cases
    ]


def bootstrap_ci(
    values: Sequence[float], *, samples: int = 10_000, seed: int = 42, level: float = 0.95
) -> tuple[float, float]:
    if not values:
        return math.nan, math.nan
    generator = random.Random(seed)
    size = len(values)
    means = sorted(
        sum(values[generator.randrange(size)] for _ in range(size)) / size for _ in range(samples)
    )
    alpha = (1 - level) / 2
    return _quantile(means, alpha), _quantile(means, 1 - alpha)


def _quantile(ordered: Sequence[float], probability: float) -> float:
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    fraction = position - lower
    return float(ordered[lower] * (1 - fraction) + ordered[upper] * fraction)


def mcnemar_exact(left: Sequence[bool], right: Sequence[bool]) -> dict:
    """Two-sided exact McNemar test on paired per-question outcomes."""
    left_only = sum(1 for a, b in zip(left, right, strict=True) if a and not b)
    right_only = sum(1 for a, b in zip(left, right, strict=True) if b and not a)
    discordant = left_only + right_only
    if discordant == 0:
        p_value = 1.0
    else:
        tail = sum(math.comb(discordant, k) for k in range(min(left_only, right_only) + 1))
        p_value = min(1.0, 2 * tail / 2**discordant)
    return {"left_only": left_only, "right_only": right_only, "p_value": p_value}


def _rate(results: Sequence[CaseResult], attribute: str) -> float:
    return sum(bool(getattr(r, attribute)) for r in results) / len(results) if results else math.nan


def _percentiles(values: Sequence[float]) -> dict:
    observed = sorted(v for v in values if v is not None)
    if not observed:
        return {"n": 0, "p50": None, "p95": None}
    return {"n": len(observed), "p50": _quantile(observed, 0.5), "p95": _quantile(observed, 0.95)}


def summarize(results: Sequence[CaseResult], *, samples: int = 10_000, seed: int = 42) -> dict:
    ex = [float(r.execution_match) for r in results]
    groups: dict[str, list[CaseResult]] = defaultdict(list)
    for r in results:
        groups[f"subset:{r.subset}"].append(r)
        groups[f"difficulty:{r.difficulty}"].append(r)
        for specific in r.specifics:
            groups[f"specific:{specific}"].append(r)
    return {
        "n": len(results),
        "execution_accuracy": _rate(results, "execution_match"),
        "execution_accuracy_ci95": bootstrap_ci(ex, samples=samples, seed=seed),
        "valid_sql_rate": sum(r.status == "ok" for r in results) / len(results),
        "format_ok_rate": _rate(results, "format_ok"),
        "exact_match": _rate(results, "exact_match"),
        "structural_match": _rate(results, "structural_match"),
        "answer_f1": sum(r.answer_f1 for r in results) / len(results),
        "status_counts": dict(Counter(r.status for r in results)),
        "by_group": {
            name: {"n": len(members), "execution_accuracy": _rate(members, "execution_match")}
            for name, members in sorted(groups.items())
        },
        "generation_ms": _percentiles([r.generation_ms for r in results]),
        "execution_ms": _percentiles([r.execution_ms for r in results]),
    }


def case_rows(results: Sequence[CaseResult]) -> list[dict]:
    return [asdict(result) for result in results]

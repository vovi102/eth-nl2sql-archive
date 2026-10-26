"""Render RESULTS.md from evaluated runs."""

from __future__ import annotations

import json
from pathlib import Path

from eth_nl2sql.config import read_jsonl
from eth_nl2sql.evaluate import mcnemar_exact

ORDER = ("b1", "b1l", "b2", "b2l", "b3", "b3l", "gold-echo")
# (left, right, what the comparison answers)
PAIRS = (
    ("b1", "b1l", "linking, zero-shot"),
    ("b2", "b2l", "linking, five-shot"),
    ("b3", "b3l", "linking, fine-tuned"),
    ("b1l", "b3l", "fine-tuning vs zero-shot"),
    ("b2l", "b3l", "fine-tuning vs five-shot"),
)
SPECIFICS = ("multi_address", "alias", "class_level", "ambiguous_property")


def _pct(value: float | None) -> str:
    return "–" if value is None else f"{100 * value:.1f}"


def _ms(value: float | None) -> str:
    return "–" if value is None else f"{value / 1000:.1f}"


def write_report(runs_dir: Path, split: str, out: Path) -> Path:
    evaluations = {}
    for name in ORDER:
        path = runs_dir / name / f"eval-{split}.json"
        if path.exists():
            evaluations[name] = json.loads(path.read_text())
    lines = [
        "# Results",
        "",
        f"Split `{split}`; execution accuracy (EX) on the local DuckDB replica. "
        "Regenerate with `eth-nl2sql report`.",
        "",
        "| Config | N | EX % (95% CI) | Valid SQL % | Format OK % | EM % | Generic EX % "
        "| Entity EX % | Gen p50 s | Gen p95 s |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, ev in evaluations.items():
        low, high = ev["execution_accuracy_ci95"]
        groups = ev["by_group"]
        lines.append(
            f"| {name} | {ev['n']} | {_pct(ev['execution_accuracy'])} ({_pct(low)}–{_pct(high)}) "
            f"| {_pct(ev['valid_sql_rate'])} | {_pct(ev['format_ok_rate'])} "
            f"| {_pct(ev['exact_match'])} "
            f"| {_pct(groups.get('subset:generic', {}).get('execution_accuracy'))} "
            f"| {_pct(groups.get('subset:entity', {}).get('execution_accuracy'))} "
            f"| {_ms(ev['generation_ms']['p50'])} | {_ms(ev['generation_ms']['p95'])} |"
        )
    lines += [
        "",
        "## EX by blockchain-specific case",
        "",
        "| Config | " + " | ".join(SPECIFICS) + " |",
    ]
    lines.append("|---|" + "---:|" * len(SPECIFICS))
    for name, ev in evaluations.items():
        cells = [
            _pct(ev["by_group"].get(f"specific:{specific}", {}).get("execution_accuracy"))
            for specific in SPECIFICS
        ]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Paired comparisons (exact McNemar)",
        "",
        "| Left | Right | Question | Left only | Right only | p |",
        "|---|---|---|---:|---:|---:|",
    ]
    for left, right, question in PAIRS:
        if left not in evaluations or right not in evaluations:
            continue
        left_cases = {
            r["id"]: r["execution_match"]
            for r in read_jsonl(runs_dir / left / f"cases-{split}.jsonl")
        }
        right_cases = {
            r["id"]: r["execution_match"]
            for r in read_jsonl(runs_dir / right / f"cases-{split}.jsonl")
        }
        ids = sorted(left_cases)
        test = mcnemar_exact([left_cases[i] for i in ids], [right_cases[i] for i in ids])
        lines.append(
            f"| {left} | {right} | {question} | {test['left_only']} | {test['right_only']} "
            f"| {test['p_value']:.3f} |"
        )
    out.write_text("\n".join(lines) + "\n")
    return out

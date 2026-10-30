"""Render RESULTS.md from evaluated runs."""

from __future__ import annotations

import json
import os
import statistics
from collections.abc import Mapping
from pathlib import Path

from eth_nl2sql.artifacts import json_digest
from eth_nl2sql.config import read_jsonl, sha256_file, write_json
from eth_nl2sql.data.annotations import GROUPS
from eth_nl2sql.evaluate import mcnemar_exact
from eth_nl2sql.experiments import SEEDS
from eth_nl2sql.generation.runs import CONFIGS
from eth_nl2sql.linking.variants import EXPERIMENTS

ORDER = ("b1", "b1l", "b2", *EXPERIMENTS, "b3-base", "b3l-base", "b3", "b3l", "gold-echo")
# (left, right, what the comparison answers)
PAIRS = (
    ("b1", "b1l", "linking, zero-shot"),
    ("b2", "b2l", "linking, five-shot"),
    ("b3", "b3l", "linking, fine-tuned"),
    ("b3-base", "b3l-base", "linking, compact base"),
    ("b3-base", "b3", "fine-tuning, identical compact prompt"),
    ("b3l-base", "b3l", "fine-tuning, identical compact prompt + linking"),
    ("b1l", "b3l", "fine-tuning vs zero-shot"),
    ("b2l", "b3l", "fine-tuning vs five-shot"),
)
SPECIFICS = tuple(group for group in GROUPS if group != "generic")


def _pct(value: float | None) -> str:
    return "–" if value is None else f"{100 * value:.1f}"


def _ms(value: float | None) -> str:
    return "–" if value is None else f"{value / 1000:.1f}"


METRICS = (
    "execution_accuracy",
    "valid_sql_rate",
    "format_ok_rate",
    "exact_match",
    "structural_match",
    "answer_f1",
)


def _mean_std(values: list[float]) -> dict:
    return {
        "mean": statistics.mean(values),
        "std": statistics.stdev(values) if len(values) > 1 else None,
    }


def aggregate_seed_evaluations(
    evaluations: Mapping[int, dict],
    *,
    expected_seeds=SEEDS,
) -> dict:
    """Across-training-seed statistics; each seed evaluates the SAME N questions."""
    if not evaluations:
        raise ValueError("No seed evaluations")
    first = next(iter(evaluations.values()))
    context = (
        "config",
        "split",
        "n",
        "dataset_sha256",
        "case_ids_sha256",
        "store",
        "evaluation_settings_sha256",
        "model_sha256",
        "prompts_sha256",
        "generation_sha256",
    )
    if CONFIGS[first["config"]].fine_tuned:
        context += ("training_protocol_sha256",)
    for seed, ev in evaluations.items():
        if ev.get("seed") != seed or any(key not in ev for key in context):
            raise ValueError("Missing seed/evaluation provenance")
        if any(ev[key] != first[key] for key in context):
            raise ValueError(
                "Cannot aggregate seeds with different data, prompts, model or protocol"
            )
        if ev["by_group"].keys() != first["by_group"].keys() or any(
            group["n"] != first["by_group"][key]["n"] for key, group in ev["by_group"].items()
        ):
            raise ValueError("Cannot aggregate different question groups")
    missing = sorted(set(expected_seeds) - evaluations.keys())
    return {
        "config": first["config"],
        "split": first["split"],
        "n_questions": first["n"],
        "n_seeds": len(evaluations),
        "seeds": sorted(evaluations),
        "expected_seeds": list(expected_seeds),
        "missing_seeds": missing,
        "complete": not missing,
        "std_definition": "sample standard deviation across training seeds (ddof=1)",
        "per_seed": {str(seed): ev for seed, ev in sorted(evaluations.items())},
        "metrics": {key: _mean_std([ev[key] for ev in evaluations.values()]) for key in METRICS},
        "by_group": {
            group: {
                "n_questions": first["by_group"][group]["n"],
                **_mean_std(
                    [ev["by_group"][group]["execution_accuracy"] for ev in evaluations.values()]
                ),
            }
            for group in first["by_group"]
        },
    }


def _load_evaluations(runs_dir: Path, split: str) -> tuple[dict, dict, dict]:
    evaluations, directories, aggregates = {}, {}, {}
    for name in ORDER:
        seeded = {}
        for seed in SEEDS:
            directory = runs_dir / name / f"seed-{seed}"
            path = directory / f"eval-{split}.json"
            if not path.exists():
                continue
            ev = json.loads(path.read_text())
            manifest_path = path.with_suffix(".manifest.json")
            if not manifest_path.exists():
                raise ValueError(f"Missing evaluation manifest: {manifest_path}")
            manifest = json.loads(manifest_path.read_text())
            cases_path = directory / f"cases-{split}.jsonl"
            if (
                manifest.get("version") != 1
                or manifest.get("provenance") != ev
                or manifest.get("evaluation_sha256") != sha256_file(path)
                or manifest.get("cases_sha256") != sha256_file(cases_path)
            ):
                raise ValueError(f"Evaluation artifact hash mismatch: {directory}")
            predictions = directory / f"predictions-{split}.jsonl"
            prediction_manifest = predictions.with_suffix(".manifest.json")
            if ev.get("predictions_sha256") != sha256_file(predictions) or ev.get(
                "prediction_manifest_sha256"
            ) != sha256_file(prediction_manifest):
                raise ValueError(f"Evaluation uses stale predictions: {directory}")
            cases = read_jsonl(cases_path)
            ids = [c["id"] for c in cases]
            if (
                len(ids) != len(set(ids))
                or len(ids) != ev["n"]
                or json_digest(sorted(ids)) != ev["case_ids_sha256"]
                or ev["config"] != name
                or ev["split"] != split
                or ev["seed"] != seed
            ):
                raise ValueError(f"Evaluation IDs/config/seed mismatch: {directory}")
            label = f"{name}/seed-{seed}"
            evaluations[label], directories[label], seeded[seed] = ev, directory, ev
        if seeded:
            expected = SEEDS if CONFIGS[name].fine_tuned else tuple(sorted(seeded))
            aggregates[name] = aggregate_seed_evaluations(seeded, expected_seeds=expected)
        else:
            # Legacy development artifacts (including gold-echo) remain readable.
            path = runs_dir / name / f"eval-{split}.json"
            if path.exists():
                evaluations[name] = json.loads(path.read_text())
                directories[name] = path.parent
    return evaluations, directories, aggregates


def write_report(runs_dir: Path, split: str, out: Path) -> Path:
    evaluations, directories, aggregates = _load_evaluations(runs_dir, split)
    lines = [
        "# Results",
        "",
        f"Split `{split}`; execution accuracy (EX) on the local DuckDB replica. "
        "Regenerate with `eth-nl2sql report`.",
        "",
        "Evaluation role: "
        + (
            "final benchmark v2."
            if split == "test"
            else "development; sample execution does not establish full snapshot parity."
        ),
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
        # Compare per seed, using a single seed-42 base control when appropriate.
        paired_labels = []
        if left in evaluations and right in evaluations:
            paired_labels.append((left, right))
        for seed in SEEDS:
            left_label, right_label = f"{left}/seed-{seed}", f"{right}/seed-{seed}"
            if left_label not in evaluations and left in CONFIGS and not CONFIGS[left].fine_tuned:
                left_label = f"{left}/seed-42" if f"{left}/seed-42" in evaluations else left
            if (
                right_label not in evaluations
                and right in CONFIGS
                and not CONFIGS[right].fine_tuned
            ):
                right_label = f"{right}/seed-42" if f"{right}/seed-42" in evaluations else right
            pair = (left_label, right_label)
            if (
                left_label in evaluations
                and right_label in evaluations
                and pair not in paired_labels
            ):
                paired_labels.append(pair)
        for left_label, right_label in paired_labels:
            left_ev, right_ev = evaluations[left_label], evaluations[right_label]
            for key in (
                "dataset_sha256",
                "store",
                "evaluation_settings_sha256",
                "model_sha256",
                "generation_sha256",
            ):
                if key in left_ev and key in right_ev and left_ev[key] != right_ev[key]:
                    raise ValueError(
                        f"Paired comparison differs in {key}: {left_label}, {right_label}"
                    )
            left_cases = {
                r["id"]: r["execution_match"]
                for r in read_jsonl(directories[left_label] / f"cases-{split}.jsonl")
            }
            right_cases = {
                r["id"]: r["execution_match"]
                for r in read_jsonl(directories[right_label] / f"cases-{split}.jsonl")
            }
            if left_cases.keys() != right_cases.keys():
                raise ValueError(f"Paired comparison IDs differ: {left_label}, {right_label}")
            ids = sorted(left_cases)
            test = mcnemar_exact([left_cases[i] for i in ids], [right_cases[i] for i in ids])
            lines.append(
                f"| {left_label} | {right_label} | {question} | {test['left_only']} "
                f"| {test['right_only']} | {test['p_value']:.3f} |"
            )
    lines += [
        "",
        "## Across training seeds",
        "",
        "N is the number of shared questions per seed; seeds are repeated training runs. "
        "Mean and sample standard deviation (ddof=1) describe variation across seeds. "
        "Question bootstrap CIs remain in the per-seed table above; predictions are never pooled.",
        "",
        "| Config | Seeds present | Missing | N questions "
        "| EX % mean ± SD | Valid SQL % mean ± SD |",
        "|---|---|---|---:|---|---|",
    ]
    for name, aggregate in aggregates.items():
        ex, valid = (aggregate["metrics"][key] for key in ("execution_accuracy", "valid_sql_rate"))
        lines.append(
            f"| {name} | {', '.join(map(str, aggregate['seeds']))} "
            f"| {', '.join(map(str, aggregate['missing_seeds'])) or '–'} "
            f"| {aggregate['n_questions']} | {_pct(ex['mean'])} ± {_pct(ex['std'])} "
            f"| {_pct(valid['mean'])} ± {_pct(valid['std'])} |"
        )
    diagnosis = runs_dir.parent / "reports/experiments/diagnosis"
    if split == "dev_eval" and (diagnosis / "evaluation/manifest.json").is_file():
        checksums = json.loads((diagnosis / "evaluation/manifest.json").read_text())
        for name, expected in checksums.items():
            if sha256_file(diagnosis / "evaluation" / name) != expected:
                raise ValueError(f"Diagnostic evaluation hash mismatch: {name}")
        candidate = json.loads((diagnosis / "evaluation/dates-columns.json").read_text())
        base = json.loads((diagnosis / "evaluation/base-dates-columns.json").read_text())
        link = Path(os.path.relpath(diagnosis / "README.md", out.parent)).as_posix()
        lines += [
            "",
            "## Frozen-adapter prompt diagnosis",
            "",
            "Separate development inference intervention; no new QLoRA training. "
            "These results use a different prompt from the original controls above "
            "and are excluded from the seed aggregates.",
            "",
            "| Condition | N | EX % | Valid SQL % |",
            "|---|---:|---:|---:|",
            *(
                f"| {name} | {ev['n']} | {_pct(ev['execution_accuracy'])} "
                f"| {_pct(ev['valid_sql_rate'])} |"
                for name, ev in (("b3/42 + dates/columns", candidate), ("Matched base", base))
            ),
            "",
            f"See the [diagnostic report]({link}) for scope, limits and the scaling decision.",
        ]
    write_json(runs_dir / f"seed-summary-{split}.json", aggregates)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    return out

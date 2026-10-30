"""Evaluate complete runs and publish their cases, metrics and bound provenance."""

from __future__ import annotations

import json
from pathlib import Path

from eth_nl2sql import config as cfg
from eth_nl2sql.artifacts import json_digest


def evaluate_runs(
    runs_dir: Path,
    name: str,
    split: str,
    seed_selection: str | int,
    store: Path,
    *,
    cases: list[dict],
    experiment: dict,
    split_path: Path,
    benchmark_manifest: Path,
) -> list[dict]:
    from eth_nl2sql.evaluate import case_rows, evaluate_predictions, summarize
    from eth_nl2sql.experiments import (
        adapter_path,
        checked_rows,
        generation_provenance,
        prediction_manifest,
        run_directory,
        selected_seeds,
        verify_predictions,
        write_manifest,
    )
    from eth_nl2sql.store.build import connect
    from eth_nl2sql.store.manifest import store_profile

    settings = experiment["evaluation"]
    seeds = (None,) if name == "gold-echo" else selected_seeds(seed_selection, experiment)
    summaries = []
    for seed in seeds:
        out_dir = runs_dir / name if seed is None else run_directory(runs_dir, name, seed)
        predictions_path = out_dir / f"predictions-{split}.jsonl"
        provenance = None
        if seed is not None:
            prompts_path = runs_dir / name / f"prompts-{split}.jsonl"
            prompts = checked_rows(prompts_path)
            if {r["id"] for r in prompts} != {c["id"] for c in cases}:
                raise ValueError("Prompt IDs differ from the evaluation split")
            provenance = generation_provenance(
                prompts_path, experiment, name, seed, adapter_path(name, out_dir)
            )
            prediction_info = verify_predictions(predictions_path, prompts, provenance)
            if prediction_info.get("status") != "complete":
                raise ValueError("Complete generation for the entire split before evaluation")
        rows = cfg.read_jsonl(predictions_path)
        predictions = {row["id"]: row for row in rows}
        if len(predictions) != len(rows) or set(predictions) - {c["id"] for c in cases}:
            raise ValueError("Duplicate or unknown prediction IDs")
        if seed is not None and set(predictions) != {c["id"] for c in cases}:
            raise ValueError("Complete generation for the entire split before evaluation")
        with connect(store) as con:
            profile = store_profile(con)
            if split == "test":
                manifest = json.loads(benchmark_manifest.read_text())
                if profile != manifest["store"]:
                    raise ValueError("Evaluation store differs from the frozen benchmark store")
            results = evaluate_predictions(
                con,
                cases,
                predictions,
                float_digits=settings["float_digits"],
                timeout_s=settings["timeout_s"],
            )
        summary = summarize(
            results, samples=settings["bootstrap_samples"], seed=settings["bootstrap_seed"]
        )
        summary.update(
            {
                "store": profile,
                "config": name,
                "seed": seed,
                "split": split,
                "missing_predictions": sorted({c["id"] for c in cases} - set(predictions)),
                "predictions_sha256": cfg.sha256_file(predictions_path),
                "dataset_sha256": cfg.sha256_file(split_path),
                "case_ids_sha256": json_digest(sorted(c["id"] for c in cases)),
                "evaluation_settings_sha256": json_digest(settings),
                "evaluation_role": "final_benchmark" if split == "test" else "development",
            }
        )
        if provenance is not None:
            summary.update(
                {
                    k: provenance[k]
                    for k in (
                        "model_sha256",
                        "prompts_sha256",
                        "adapter_sha256",
                        "generation_sha256",
                    )
                }
            )
            summary["prediction_manifest_sha256"] = cfg.sha256_file(
                prediction_manifest(predictions_path)
            )
            training_manifest = out_dir / "training-manifest.json"
            if training_manifest.exists():
                training = json.loads(training_manifest.read_text())["provenance"]
                summary["training_protocol_sha256"] = json_digest(
                    {k: v for k, v in training.items() if k != "seed"}
                )
        if split == "test":
            summary["benchmark_manifest_sha256"] = cfg.sha256_file(benchmark_manifest)
        cases_path = out_dir / f"cases-{split}.jsonl"
        evaluation_path = out_dir / f"eval-{split}.json"
        cfg.write_jsonl(cases_path, case_rows(results))
        cfg.write_json(evaluation_path, summary)
        write_manifest(
            evaluation_path.with_suffix(".manifest.json"),
            summary,
            evaluation_sha256=cfg.sha256_file(evaluation_path),
            cases_sha256=cfg.sha256_file(cases_path),
        )
        summaries.append(summary)
    return summaries

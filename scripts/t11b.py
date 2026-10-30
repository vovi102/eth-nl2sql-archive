"""T11B development pilot and isolated QLoRA jobs with intact output collection."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eth_nl2sql import config as cfg  # noqa: E402
from eth_nl2sql.experiments import (  # noqa: E402
    SEEDS,
    checked_rows,
    generation_provenance,
    verify_predictions,
)
from eth_nl2sql.generation.runs import CONFIGS, Job, training_configs  # noqa: E402
from eth_nl2sql.generation.smoke import inspect_predictions  # noqa: E402
from eth_nl2sql.gpu_workflow import (  # noqa: E402
    StageRunner,
    archive_outputs,
    benchmark_hashes,
    collect_outputs,
    offline_environment,
    package_inputs,
    require_cuda,
    source_files,
    verify_cache,
    verify_inputs,
    write_runtime,
)

REPORT = ROOT / "reports/experiments"
NAMES = ("b1", *training_configs())


def package(output: Path) -> None:
    files = source_files(ROOT, "t11*.py")
    files += [ROOT / f"data/{s}.jsonl" for s in ("train", "dev")]
    for name in NAMES:
        files += [ROOT / f"runs/{name}/prompts-dev_eval.jsonl"]
        if CONFIGS[name].fine_tuned:
            files += [ROOT / f"runs/{name}/sft-{s}.jsonl" for s in ("train", "dev")]
    manifest = {
        "task": "T11B",
        "evaluation_role": "development",
        "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "working_tree_patch": subprocess.check_output(
            ["git", "diff", "HEAD", "--", "src", "scripts", "configs"], text=True
        ),
        # Per-file hashes also cover new/uncommitted files in this exact bundle.
        "test_v2": benchmark_hashes(ROOT),
        "settings": cfg.load(),
        "dev_eval_sha256": cfg.sha256_file(ROOT / "data/dev_eval.jsonl"),
    }
    package_inputs(ROOT, REPORT, output, files, manifest)


def prediction_rows(name: str, seed: int) -> tuple[list, dict]:
    prompts = ROOT / f"runs/{name}/prompts-dev_eval.jsonl"
    directory = ROOT / f"runs/{name}/seed-{seed}"
    adapter = directory / "adapter" if CONFIGS[name].fine_tuned else None
    path = directory / "predictions-dev_eval.jsonl"
    inputs = checked_rows(prompts)
    manifest = verify_predictions(
        path, inputs, generation_provenance(prompts, cfg.load(), name, seed, adapter)
    )
    rows = cfg.read_jsonl(path)
    if [r["id"] for r in rows] != [r["id"] for r in inputs[: len(rows)]]:
        raise ValueError("Predictions differ from the declared development prefix")
    return rows, manifest


def gpu(job: str, home: Path) -> None:
    selected = Job.parse(job)
    job = selected.identifier
    directory = REPORT / job
    directory.mkdir(parents=True, exist_ok=True)
    name, seed = selected.config.name, selected.seed
    status = {"job": job, "status": "running", "evaluation_role": "development"}
    env = offline_environment(home)
    cli = StageRunner(ROOT, directory, env, stream=True)

    try:
        manifest = verify_inputs(ROOT, REPORT)
        cfg.write_json(directory / "inputs-manifest.json", manifest)
        write_runtime(directory)
        require_cuda("T11B")
        verify_cache(home, ROOT / "configs/t11-model-files.json")
        if selected.config.fine_tuned:
            cli(
                "preflight-training",
                "preflight",
                "--config",
                name,
                "--seed",
                str(seed),
                "--training",
            )
            cli("train", "train", "--config", name, "--seed", str(seed))
        cli("generate-10", "generate", "--config", name, "--seed", str(seed), "--limit", "10")
        rows, _ = prediction_rows(name, seed)
        if len(rows) != 10:
            raise ValueError("Expected exactly ten smoke predictions")
        smoke = inspect_predictions(rows)
        cfg.write_json(directory / "smoke.json", smoke)
        # A failed smoke is a measured result. Never silently resume it to 100.
        if selected.config.fine_tuned and smoke["passed"]:
            cli("generate-100", "generate", "--config", name, "--seed", str(seed))
            rows, manifest = prediction_rows(name, seed)
            if len(rows) != 100 or manifest["status"] != "complete":
                raise ValueError("Incomplete development generation")
        status.update(
            status="complete_pending_local_evaluation", rows=len(rows), smoke_passed=smoke["passed"]
        )
    except BaseException as exc:
        status.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        cfg.write_json(directory / "status.json", status)
        archive_outputs(
            ROOT,
            (directory, ROOT / f"runs/{name}/seed-{seed}"),
            directory / "outputs-manifest.json",
            ROOT.parent / f"t11b-{job}-artifacts.zip",
        )


def collect(job: str, archive: Path) -> None:
    job = Job.parse(job).identifier
    manifest = collect_outputs(
        ROOT,
        archive,
        f"reports/experiments/{job}/outputs-manifest.json",
        can_replace=lambda p: p.name in ("preflight-training.json", "inputs-manifest.json"),
    )
    cfg.write_json(REPORT / job / "outputs-manifest.json", manifest)
    cfg.write_json(
        REPORT / job / "download.json",
        {
            "sha256": cfg.sha256_file(archive),
            "bytes": archive.stat().st_size,
            "verified_files": len(manifest),
        },
    )


def evaluate(job: str) -> None:
    from eth_nl2sql.evaluate import case_rows, evaluate_predictions, summarize
    from eth_nl2sql.store.build import connect
    from eth_nl2sql.store.manifest import store_profile

    selected = Job.parse(job)
    name, seed = selected.config.name, selected.seed
    predictions, _ = prediction_rows(name, seed)
    if len(predictions) == 100:
        # Complete runs use the production split/provenance checks and feed the
        # normal per-seed results table. Partial pilots stay in this report only.
        subprocess.run(
            [
                sys.executable,
                "-m",
                "eth_nl2sql.cli",
                "evaluate",
                "--config",
                name,
                "--seed",
                str(seed),
                "--split",
                "dev_eval",
            ],
            cwd=ROOT,
            check=True,
        )
        run = ROOT / f"runs/{name}/seed-{seed}"
        summary = json.loads((run / "eval-dev_eval.json").read_text())
        cfg.write_json(REPORT / job / "eval.json", {**summary, "scope": "full dev_eval"})
        shutil.copy2(run / "cases-dev_eval.jsonl", REPORT / job / "cases.jsonl")
        subprocess.run([sys.executable, "-m", "eth_nl2sql.cli", "report"], cwd=ROOT, check=True)
        print(json.dumps({k: summary[k] for k in ("n", "valid_sql_rate", "execution_accuracy")}))
        return
    ids = {r["id"] for r in predictions}
    cases = [r for r in cfg.read_jsonl(ROOT / "data/dev_eval.jsonl") if r["id"] in ids]
    settings = cfg.load()["evaluation"]
    with connect(cfg.STORE_PATH) as con:
        profile = store_profile(con)
        results = evaluate_predictions(
            con,
            cases,
            {r["id"]: r for r in predictions},
            float_digits=settings["float_digits"],
            timeout_s=settings["timeout_s"],
        )
    summary = summarize(
        results, samples=settings["bootstrap_samples"], seed=settings["bootstrap_seed"]
    )
    summary.update(
        config=name,
        seed=seed,
        evaluation_role="development",
        store=profile,
        scope="first ten dev_eval cases" if len(cases) == 10 else "full dev_eval",
        dataset_sha256=cfg.sha256_file(ROOT / "data/dev_eval.jsonl"),
        predictions_sha256=cfg.sha256_file(
            ROOT / f"runs/{name}/seed-{seed}/predictions-dev_eval.jsonl"
        ),
    )
    cfg.write_json(REPORT / job / "eval.json", summary)
    cfg.write_jsonl(REPORT / job / "cases.jsonl", case_rows(results))
    print(
        json.dumps(
            {
                k: summary[k]
                for k in ("n", "scope", "valid_sql_rate", "execution_accuracy", "status_counts")
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("package", "gpu", "collect", "evaluate"))
    parser.add_argument("--archive", type=Path, default=ROOT / ".cache/t11b-inputs.zip")
    parser.add_argument(
        "--job",
        default="pilot",
        choices=(
            "pilot",
            *(f"{name}-seed-{seed}" for name in training_configs() for seed in SEEDS),
        ),
    )
    parser.add_argument("--hf-home", type=Path)
    args = parser.parse_args()
    if args.stage == "package":
        package(args.archive)
    elif args.stage == "gpu":
        if args.hf_home is None:
            parser.error("gpu requires --hf-home")
        gpu(args.job, args.hf_home)
    elif args.stage == "collect":
        collect(args.job, args.archive)
    else:
        evaluate(args.job)

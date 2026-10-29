"""T11B development pilot and isolated QLoRA jobs with intact output collection."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from t11a import test_hashes, verify_cache  # noqa: E402

from eth_nl2sql import config as cfg  # noqa: E402
from eth_nl2sql.experiments import (  # noqa: E402
    checked_rows,
    generation_provenance,
    verify_predictions,
)
from eth_nl2sql.generation.smoke import inspect_predictions  # noqa: E402

REPORT = ROOT / "reports/gpu-development-t11b"
NAMES = ("b1", "b3", "b3l")


def package(output: Path) -> None:
    files = [ROOT / p for p in ("pyproject.toml", "uv.lock", "README.md")]
    files += sorted((ROOT / "src").rglob("*.py"))
    files += sorted((ROOT / "scripts").glob("t11*.py"))
    files += sorted((ROOT / "configs").glob("*"))
    files += [ROOT / f"data/{s}.jsonl" for s in ("train", "dev")]
    for name in NAMES:
        files += [ROOT / f"runs/{name}/prompts-dev_eval.jsonl"]
        if name != "b1":
            files += [ROOT / f"runs/{name}/sft-{s}.jsonl" for s in ("train", "dev")]
    manifest = {
        "task": "T11B",
        "evaluation_role": "development",
        "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "working_tree_patch": subprocess.check_output(
            ["git", "diff", "HEAD", "--", "src", "scripts", "configs"], text=True
        ),
        # Per-file hashes also cover new/uncommitted files in this exact bundle.
        "files": {p.relative_to(ROOT).as_posix(): cfg.sha256_file(p) for p in files},
        "test_v2": test_hashes(),
        "settings": cfg.load(),
        "dev_eval_sha256": cfg.sha256_file(ROOT / "data/dev_eval.jsonl"),
    }
    cfg.write_json(REPORT / "inputs-manifest.json", manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT))
        archive.write(
            REPORT / "inputs-manifest.json", REPORT.relative_to(ROOT) / "inputs-manifest.json"
        )
        archive.writestr(
            "data/dev_eval.jsonl",
            "".join(
                json.dumps({k: row[k] for k in ("id", "question")}) + "\n"
                for row in cfg.read_jsonl(ROOT / "data/dev_eval.jsonl")
            ),
        )
    cfg.write_json(
        REPORT / "bundle.json",
        {
            "sha256": cfg.sha256_file(output),
            "bytes": output.stat().st_size,
        },
    )


def prediction_rows(name: str, seed: int) -> tuple[list, dict]:
    prompts = ROOT / f"runs/{name}/prompts-dev_eval.jsonl"
    directory = ROOT / f"runs/{name}/seed-{seed}"
    adapter = directory / "adapter" if name != "b1" else None
    path = directory / "predictions-dev_eval.jsonl"
    manifest = verify_predictions(
        path, checked_rows(prompts), generation_provenance(prompts, cfg.load(), name, seed, adapter)
    )
    rows = cfg.read_jsonl(path)
    inputs = checked_rows(prompts)
    if [r["id"] for r in rows] != [r["id"] for r in inputs[: len(rows)]]:
        raise ValueError("Predictions differ from the declared development prefix")
    return rows, manifest


def gpu(job: str, home: Path) -> None:
    directory = REPORT / job
    directory.mkdir(parents=True, exist_ok=True)
    name, seed = ("b1", 42) if job == "pilot" else (job.split("-seed-")[0], int(job[-2:]))
    status = {"job": job, "status": "running", "evaluation_role": "development"}
    stages = []
    os.environ.update(
        HF_HOME=str(home),
        HF_HUB_CACHE=str(home / "hub"),
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
    )

    def cli(stage, *args):
        print("Starting:", stage, flush=True)
        started = time.monotonic()
        with (directory / f"{stage}.log").open("w") as log:
            process = subprocess.Popen(
                [sys.executable, "-u", "-m", "eth_nl2sql.cli", *args],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            for line in process.stdout:
                log.write(line)
                log.flush()
                print(f"{stage}: {line}", end="", flush=True)
            returncode = process.wait()
        stages.append(
            {
                "stage": stage,
                "runtime_s": time.monotonic() - started,
                "returncode": returncode,
            }
        )
        cfg.write_json(directory / "stages.json", stages)
        if returncode:
            print((directory / f"{stage}.log").read_text()[-6000:], flush=True)
            raise RuntimeError(f"{stage} failed")

    try:
        manifest = json.loads((REPORT / "inputs-manifest.json").read_text())
        cfg.write_json(directory / "inputs-manifest.json", manifest)
        for path, digest in manifest["files"].items():
            if cfg.sha256_file(ROOT / path) != digest:
                raise ValueError(f"Input hash mismatch: {path}")
        verify_cache(home, ROOT / "configs/t11-model-files.json")
        cfg.write_json(
            directory / "runtime.json",
            {
                "python": sys.version,
                "packages": {
                    d.metadata["Name"]: d.version for d in importlib.metadata.distributions()
                },
            },
        )
        if job != "pilot":
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
        if job != "pilot" and smoke["passed"]:
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
        artifacts = [p for p in directory.rglob("*") if p.is_file()]
        artifacts += [p for p in (ROOT / f"runs/{name}/seed-{seed}").rglob("*") if p.is_file()]
        cfg.write_json(
            directory / "outputs-manifest.json",
            {p.relative_to(ROOT).as_posix(): cfg.sha256_file(p) for p in artifacts},
        )
        with zipfile.ZipFile(
            ROOT.parent / f"t11b-{job}-artifacts.zip", "w", zipfile.ZIP_DEFLATED
        ) as z:
            for path in [*artifacts, directory / "outputs-manifest.json"]:
                z.write(path, path.relative_to(ROOT))


def collect(job: str, archive: Path) -> None:
    with zipfile.ZipFile(archive) as z:
        manifest = json.loads(z.read(f"reports/gpu-development-t11b/{job}/outputs-manifest.json"))
        for name, expected in manifest.items():
            destination = ROOT / name
            if not destination.resolve().is_relative_to(ROOT):
                raise ValueError("Invalid artifact path")
            content = z.read(name)
            if hashlib.sha256(content).hexdigest() != expected:
                raise ValueError(f"Artifact hash mismatch: {name}")
            if destination.exists() and cfg.sha256_file(destination) != expected:
                if destination.name not in ("preflight-training.json", "inputs-manifest.json"):
                    raise ValueError(f"Refusing to replace existing artifact: {name}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
    shutil.copy2(archive, REPORT / job / "artifacts.zip")
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

    name, seed = ("b1", 42) if job == "pilot" else (job.split("-seed-")[0], int(job[-2:]))
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
            *(f"{name}-seed-{seed}" for name in ("b3", "b3l") for seed in (42, 43, 44)),
        ),
    )
    parser.add_argument("--hf-home", type=Path)
    args = parser.parse_args()
    if args.stage == "package":
        package(args.archive)
    elif args.stage == "gpu":
        gpu(args.job, args.hf_home)
    elif args.stage == "collect":
        collect(args.job, args.archive)
    else:
        evaluate(args.job)

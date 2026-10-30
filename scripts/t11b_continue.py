"""Collect the B1 pilot, then review b3/42 before running the remaining QLoRA seeds.

Runs sequentially and persists state/logs locally, including when the chat disconnects.
Each GPU job has its own private notebook and immutable checksummed input bundle.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import math
import os
import shutil
import subprocess
import sys
import time
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from t11b import REPORT, ROOT, collect, evaluate

from eth_nl2sql import config as cfg
from eth_nl2sql.experiments import SEEDS
from eth_nl2sql.generation.runs import CONFIGS, Job, training_configs
from eth_nl2sql.kaggle import load_settings

JOBS = (
    "pilot",
    *(Job(CONFIGS[name], seed).identifier for seed in SEEDS for name in training_configs()),
)


def run(argv: list[str], log: Path) -> str:
    print("Running:", " ".join(argv), flush=True)
    attempts = 1 if "push" in argv else 3
    for attempt in range(attempts):
        result = subprocess.run(
            argv, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        if result.returncode == 0 or attempt == attempts - 1:
            break
        time.sleep(5)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(result.stdout)
    if result.returncode:
        raise RuntimeError(f"Command failed; inspect {log}")
    return result.stdout


def review(job: str) -> dict:
    selected = Job.parse(job)
    job = selected.identifier
    directory = REPORT / job
    evaluation = json.loads((directory / "eval.json").read_text())
    result = {
        "job": job,
        "evaluated_rows": evaluation["n"],
        "valid_sql_rate": evaluation["valid_sql_rate"],
        "execution_accuracy": evaluation["execution_accuracy"],
        "scope": evaluation["scope"],
        "issues": [],
    }
    if selected.is_pilot:
        result["decision"] = "continue_to_first_training_run"
        return result
    name, seed = selected.config.name, selected.seed
    training = json.loads((ROOT / f"runs/{name}/seed-{seed}/training-summary.json").read_text())
    losses = [r["eval_loss"] for r in training["log_history"] if "eval_loss" in r]
    result.update(
        best_eval_loss=training["best_eval_loss"],
        eval_loss_history=losses,
        runtime_s=training["runtime_s"],
        hardware=training["hardware"],
        per_gpu_peak_allocated_gib=training["per_gpu_peak_allocated_gib"],
        peak_gpu_reserved_gib=training["peak_gpu_reserved_gib"],
    )
    if not losses or any(not math.isfinite(loss) for loss in losses):
        result["issues"].append("Missing or non-finite dev loss")
    if not math.isfinite(training["best_eval_loss"]):
        result["issues"].append("Non-finite best dev loss")
    if not training["hardware"]["gpus"] or not training["peak_gpu_memory_gib"]:
        result["issues"].append("Missing actual GPU measurements")
    if evaluation["valid_sql_rate"] == 0 or evaluation["execution_accuracy"] == 0:
        result["issues"].append("No executable or execution-correct SQL; diagnose before scaling")
    result["decision"] = "stop_for_diagnosis" if result["issues"] else "continue"
    return result


def required_quota_hours(job: str, jobs: dict) -> float:
    """Use measured prior training runtime, allowing for generation and bootstrap."""
    selected = Job.parse(job)
    name = selected.config.name
    measured = [
        (Job.parse(key).config.name, row["review"]["runtime_s"])
        for key, row in jobs.items()
        if "runtime_s" in row.get("review", {})
    ]
    same = [seconds for config, seconds in measured if config == name]
    if same:
        estimate = max(same)
    elif measured:
        # The first linked run has longer prompts than the unlinked run.
        estimate = max(seconds for _, seconds in measured) * (1.5 if selected.config.linking else 1)
    else:
        return 0.5
    return estimate / 3600 * 1.1 + 0.5


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    settings = load_settings()
    parser.add_argument("--pilot-kernel")
    parser.add_argument("--owner", default=settings.owner)
    parser.add_argument("--run-tag", default=settings.run_tag)
    parser.add_argument("--cache-kernel")
    args = parser.parse_args()
    deployment = replace(settings, owner=args.owner, run_tag=args.run_tag)
    lock = (REPORT / "continuation.lock").open("a+")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit(
            "A T11B controller is already running; inspect continuation.json"
        ) from None
    lock.seek(0)
    lock.truncate()
    lock.write(str(os.getpid()) + "\n")
    lock.flush()
    state_path = REPORT / "continuation.json"
    state = (
        json.loads(state_path.read_text())
        if state_path.exists()
        else {
            "status": "running",
            "jobs": {},
            "order": list(JOBS),
            "started_utc": datetime.now(UTC).isoformat(),
        }
    )
    state.pop("error", None)
    try:
        for job in JOBS:
            directory = REPORT / job
            directory.mkdir(parents=True, exist_ok=True)
            record = state["jobs"].setdefault(job, {})
            if record.get("status") == "evaluated":
                if record["review"]["decision"] == "stop_for_diagnosis":
                    state.update(status="stopped_for_diagnosis", current_job=job)
                    return
                continue
            state.update(status="running", current_job=job)
            cfg.write_json(state_path, state)
            kernel = record.get("kernel") or (
                (args.pilot_kernel or deployment.kernel("t11b", "pilot"))
                if Job.parse(job).is_pilot
                else deployment.kernel("t11b", job)
            )
            record["kernel"] = kernel
            if job != "pilot" and not record.get("submitted"):
                while True:
                    quota = json.loads(
                        run(
                            ["kaggle", "quota", "--format", "json"], directory / "quota-before.json"
                        )
                    )
                    gpu = next(row for row in quota if row["resource"] == "GPU")
                    required = required_quota_hours(job, state["jobs"])
                    if float(gpu["remaining"].removesuffix("h")) >= required:
                        state.update(status="running")
                        break
                    state.update(status="waiting_for_quota", required_gpu_hours=required, quota=gpu)
                    cfg.write_json(state_path, state)
                    # Keep authorized seeds queued until the account quota refreshes.
                    for _ in range(30):
                        time.sleep(60)
                archive = ROOT / f".cache/t11b-{job}-inputs.zip"
                run(
                    [sys.executable, "scripts/t11b.py", "package", "--archive", str(archive)],
                    directory / "package.log",
                )
                shutil.copy2(REPORT / "inputs-manifest.json", directory / "inputs-manifest.json")
                shutil.copy2(REPORT / "bundle.json", directory / "bundle.json")
                notebook = ROOT / f".cache/t11b-{job}"
                run(
                    [
                        sys.executable,
                        "scripts/t11b_notebook.py",
                        "--archive",
                        str(archive),
                        "--output",
                        str(notebook),
                        "--kernel",
                        kernel,
                        "--job",
                        job,
                        "--cache-kernel",
                        args.cache_kernel or deployment.cache_kernel,
                    ],
                    directory / "notebook.log",
                )
                run(
                    [
                        "kaggle",
                        "kernels",
                        "push",
                        "-p",
                        str(notebook),
                        "--accelerator",
                        "NvidiaTeslaT4",
                        "--timeout",
                        "43200",
                    ],
                    directory / "push.log",
                )
            record["submitted"] = True
            cfg.write_json(state_path, state)
            while True:
                status = run(
                    ["kaggle", "kernels", "status", kernel], directory / "kaggle-status.txt"
                )
                record.update(
                    remote_status=status.strip(), checked_utc=datetime.now(UTC).isoformat()
                )
                cfg.write_json(state_path, state)
                if any(s in status for s in ("COMPLETE", "ERROR", "CANCEL")):
                    break
                time.sleep(30)
            download = ROOT / f".cache/t11b-download-{job}"
            run(
                [
                    "kaggle",
                    "kernels",
                    "output",
                    kernel,
                    "-p",
                    str(download),
                    "--file-pattern",
                    f"^t11b-{job}-artifacts[.]zip$",
                    "--page-size",
                    "200",
                    "--quiet",
                    "--force",
                ],
                directory / "download.log",
            )
            archive = download / f"t11b-{job}-artifacts.zip"
            if not archive.exists():
                run(
                    [
                        "kaggle",
                        "kernels",
                        "output",
                        kernel,
                        "-p",
                        str(download),
                        "--file-pattern",
                        "[.]log$",
                        "--page-size",
                        "200",
                        "--quiet",
                    ],
                    directory / "download-failure.log",
                )
                raise RuntimeError(f"No intact artifact archive for {job}; inspect downloaded logs")
            collect(job, archive)
            if "COMPLETE" not in status:
                raise RuntimeError(f"{job} failed on Kaggle; artifacts collected for diagnosis")
            evaluate(job)
            record.update(status="evaluated", review=review(job))
            cfg.write_json(directory / "review.json", record["review"])
            cfg.write_json(state_path, state)
            run(["kaggle", "quota", "--format", "json"], directory / "quota-after.json")
            if record["review"]["decision"] == "stop_for_diagnosis":
                state.update(status="stopped_for_diagnosis")
                return
        state.update(status="complete", completed_utc=datetime.now(UTC).isoformat())
    except BaseException as exc:
        state.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        cfg.write_json(state_path, state)


if __name__ == "__main__":
    main()

"""Review each development job before continuing the QLoRA matrix."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from dataclasses import replace
from datetime import UTC, datetime

from t11b import REPORT, ROOT, collect, evaluate

from eth_nl2sql import config as cfg
from eth_nl2sql.experiments import SEEDS
from eth_nl2sql.generation.runs import CONFIGS, Job, training_configs
from eth_nl2sql.kaggle import KaggleClient, KaggleSettings, exclusive_lock, load_settings

JOBS = (
    "pilot",
    *(Job(CONFIGS[name], seed).identifier for seed in SEEDS for name in training_configs()),
)


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


def continue_jobs(
    deployment: KaggleSettings, *, pilot_kernel: str | None = None, cache_kernel: str | None = None
) -> None:
    with exclusive_lock(REPORT / "continuation.lock"):
        decision_path = REPORT / "diagnosis/scaling-decision.json"
        if decision_path.exists() and json.loads(decision_path.read_text())["decision"] == (
            "hold_for_further_development"
        ):
            print("Development is on hold; review the scaling decision before continuing.")
            return
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
                selected = Job.parse(job)
                directory = REPORT / job
                record = state["jobs"].setdefault(job, {})
                if record.get("status") == "evaluated":
                    if record["review"]["decision"] == "stop_for_diagnosis":
                        state.update(status="stopped_for_diagnosis", current_job=job)
                        return
                    continue
                directory.mkdir(parents=True, exist_ok=True)
                client = KaggleClient(ROOT, directory)
                state.update(status="running", current_job=job)
                kernel = record.setdefault(
                    "kernel",
                    pilot_kernel
                    if selected.is_pilot and pilot_kernel
                    else (deployment.kernel(selected)),
                )
                cfg.write_json(state_path, state)
                with client.session(kernel):
                    if not record.get("submitted"):
                        notebook = ROOT / f".cache/t11b-{job}"
                        if not (directory / "submission.json").exists():
                            while True:
                                quota = json.loads(
                                    client.command(
                                        ["kaggle", "quota", "--format", "json"], "quota-before.json"
                                    )
                                )
                                gpu = next(row for row in quota if row["resource"] == "GPU")
                                required = required_quota_hours(job, state["jobs"])
                                if float(gpu["remaining"].removesuffix("h")) >= required:
                                    state.update(status="running")
                                    break
                                state.update(
                                    status="waiting_for_quota",
                                    required_gpu_hours=required,
                                    quota=gpu,
                                )
                                cfg.write_json(state_path, state)
                                client.sleep(60)
                            archive = ROOT / f".cache/t11b-{job}-inputs.zip"
                            client.command(
                                [
                                    sys.executable,
                                    "scripts/t11b.py",
                                    "package",
                                    "--archive",
                                    str(archive),
                                ],
                                "package.log",
                            )
                            for name in ("inputs-manifest.json", "bundle.json"):
                                shutil.copy2(REPORT / name, directory / name)
                            client.command(
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
                                    cache_kernel or deployment.cache_kernel,
                                ],
                                "notebook.log",
                            )
                        record["kernel_ref"] = client.push(
                            notebook, producer=selected.config.fine_tuned
                        )
                        record["submitted"] = True
                        cfg.write_json(state_path, state)
                    reference = record.get("kernel_ref", kernel)
                    outcome = client.collect(
                        reference,
                        f"t11b-{job}-artifacts.zip",
                        lambda path, job=job: collect(job, path),
                        timeout_s=86400,
                        require_version=(kernel == deployment.kernel()),
                    )
                    if outcome != "COMPLETE":
                        raise RuntimeError(
                            f"{job} failed on Kaggle; output collected for diagnosis"
                        )
                evaluate(job)
                record.update(status="evaluated", review=review(job))
                cfg.write_json(directory / "review.json", record["review"])
                cfg.write_json(state_path, state)
                client.command(["kaggle", "quota", "--format", "json"], "quota-after.json")
                if record["review"]["decision"] == "stop_for_diagnosis":
                    state.update(status="stopped_for_diagnosis")
                    return
            state.update(status="complete", completed_utc=datetime.now(UTC).isoformat())
        except BaseException as exc:
            state.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            raise
        finally:
            cfg.write_json(state_path, state)


def main() -> None:
    settings = load_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-kernel")
    parser.add_argument("--owner", default=settings.owner)
    parser.add_argument("--cache-kernel")
    args = parser.parse_args()
    continue_jobs(
        replace(settings, owner=args.owner),
        pilot_kernel=args.pilot_kernel,
        cache_kernel=args.cache_kernel,
    )


if __name__ == "__main__":
    main()

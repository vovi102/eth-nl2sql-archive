"""Collect and score only the submitted diagnostic job; never submit or scale."""

from __future__ import annotations

import argparse
import fcntl
import json
import subprocess
import time
from datetime import UTC, datetime

from t11b_diagnose import ROOT, WORK
from t11b_diagnosis_report import collect, evaluate

from eth_nl2sql import config as cfg

KERNEL = "aohkvd/eth-nl2sql-t11b-diagnosis-20261029/1"


def run(argv: list[str], name: str) -> str:
    process = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=300)
    (WORK / name).write_text(process.stdout + process.stderr)
    if process.returncode:
        raise RuntimeError(f"Command failed; inspect {WORK / name}")
    return process.stdout


def main(kernel: str = KERNEL) -> None:
    lock = (WORK / "collection.lock").open("a+")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("A diagnostic collector is already running") from None
    state_path = WORK / "collection.json"
    state = {
        "kernel": kernel,
        "status": "waiting_for_artifacts",
        "started_utc": datetime.now(UTC).isoformat(),
        "submit_or_expand": False,
    }
    cfg.write_json(state_path, state)
    started = time.monotonic()
    try:
        while time.monotonic() - started < 7200:
            try:
                status = run(["kaggle", "kernels", "status", kernel], "kaggle-status.txt")
                state.update(
                    remote_status=status.strip(), checked_utc=datetime.now(UTC).isoformat()
                )
                cfg.write_json(state_path, state)
                print(status.strip(), flush=True)
                if any(word in status for word in ("COMPLETE", "ERROR", "CANCEL")):
                    break
            except (RuntimeError, subprocess.TimeoutExpired) as exc:
                state.update(observation_error=str(exc), checked_utc=datetime.now(UTC).isoformat())
                cfg.write_json(state_path, state)
            time.sleep(30)
        else:
            raise TimeoutError("Artifact observation timed out; remote job was not cancelled")
        download = ROOT / ".cache/t11b-diagnosis-download"
        archive = download / "t11b-diagnosis-artifacts.zip"
        run(
            [
                "kaggle",
                "kernels",
                "output",
                kernel,
                "-p",
                str(download),
                "--file-pattern",
                "^t11b-diagnosis-artifacts[.]zip$",
                "--quiet",
            ],
            "download.log",
        )
        if not archive.is_file():
            raise RuntimeError("Remote job ended without the diagnostic output ZIP")
        collect(archive)
        gpu_status = json.loads((WORK / "output/status.json").read_text())
        if gpu_status["status"] == "failed":
            state.update(status="failed_gpu_job", gpu_status=gpu_status)
        else:
            result = evaluate()
            state.update(
                status="evaluated", decision=result["decision"], full_rows=result["full_rows"]
            )
        try:
            run(["kaggle", "quota", "--format", "json"], "quota-after.json")
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            state["quota_observation_error"] = str(exc)
        print(json.dumps(state), flush=True)
    except BaseException as exc:
        state.update(status="collection_failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        state["finished_utc"] = datetime.now(UTC).isoformat()
        cfg.write_json(state_path, state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel", default=KERNEL)
    main(parser.parse_args().kernel)

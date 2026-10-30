"""Submit only when requested, then collect and score one diagnostic version."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from t11b_diagnose import ROOT, WORK
from t11b_diagnosis_report import collect, evaluate

from eth_nl2sql import config as cfg
from eth_nl2sql.kaggle import KaggleClient, exclusive_lock, load_settings


def main(kernel: str | None = None, *, notebook: Path | None = None) -> None:
    client = KaggleClient(ROOT, WORK)
    with exclusive_lock(WORK / "collection.lock"):
        state_path = WORK / "collection.json"
        previous = json.loads(state_path.read_text()) if state_path.exists() else {}
        receipt = WORK / "submission.json"
        submitted = json.loads(receipt.read_text()) if receipt.exists() else {}
        reference = kernel or submitted.get("kernel_ref") or previous.get("kernel")
        target = "/".join((reference or load_settings().kernel()).split("/")[:2])
        state = {
            "kernel": reference or target,
            "status": "waiting_for_artifacts",
            "started_utc": datetime.now(UTC).isoformat(),
            "expanded_seeds": False,
        }
        try:
            with client.session(target):
                if notebook is not None:
                    metadata = json.loads((notebook / "kernel-metadata.json").read_text())
                    if metadata["id"] != target:
                        raise ValueError("Notebook kernel differs from the selected deployment")
                    reference = client.push(notebook)
                    state["kernel"] = reference
                cfg.write_json(state_path, state)
                outcome = client.collect(
                    reference or target, "t11b-diagnosis-artifacts.zip", collect
                )
            gpu_status = json.loads((WORK / "output/status.json").read_text())
            if outcome != "COMPLETE" or gpu_status["status"] == "failed":
                state.update(status="failed_gpu_job", gpu_status=gpu_status)
            else:
                result = evaluate()
                state.update(
                    status="evaluated", decision=result["decision"], full_rows=result["full_rows"]
                )
            try:
                client.command(["kaggle", "quota", "--format", "json"], "quota-after.json")
            except RuntimeError as exc:
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
    parser.add_argument("--kernel", help="OWNER/SLUG/VERSION; defaults to the saved submission")
    parser.add_argument("--notebook", type=Path, help="Explicitly submit this built notebook first")
    args = parser.parse_args()
    main(args.kernel, notebook=args.notebook)

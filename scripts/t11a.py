"""T11A: package development inputs, run real GPU controls, and collect intact outputs.

Run with the repository environment; see reports/experiments/README.md.
The GPU phase calls the production CLI in separate processes to exercise resume.
"""

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
    checked_rows,
    generation_provenance,
    verify_predictions,
)
from eth_nl2sql.generation.runs import CONFIGS as RUN_CONFIGS  # noqa: E402
from eth_nl2sql.generation.runs import training_configs  # noqa: E402
from eth_nl2sql.gpu_workflow import (  # noqa: E402
    StageRunner,
    archive_outputs,
    benchmark_hashes,
    collect_outputs,
    offline_environment,
    package_inputs,
    require_cuda,
    source_files,
    write_runtime,
)
from eth_nl2sql.gpu_workflow import (  # noqa: E402
    verify_cache as verify_cache,
)
from eth_nl2sql.gpu_workflow import (  # noqa: E402
    verify_inputs as check_inputs,
)

REPORT = ROOT / "reports/experiments/base-controls"
CONTROLS = ("b3-base", "b3l-base")
CONFIGS = (*training_configs(), *CONTROLS)


def test_hashes() -> dict:
    return benchmark_hashes(ROOT)


def package(output: Path) -> None:
    dirty = subprocess.check_output(["git", "diff", "HEAD", "--", "src", "scripts", "configs"])
    if dirty:
        raise ValueError("Commit code/config changes before packaging GPU inputs")
    settings = cfg.load()
    links = {}
    for split in ("train", "dev", "dev_eval"):
        path = ROOT / f"data/linking/{split}.jsonl"
        manifest = json.loads(path.with_suffix(".manifest.json").read_text())
        if manifest["encoder"] != settings["models"]["encoder"]:
            raise ValueError(f"{split} must use the pinned encoder")
        if manifest["predictions_sha256"] != cfg.sha256_file(path):
            raise ValueError(f"Stale linking cache: {split}")
        links[split] = manifest
    identity_keys = (
        "encoder",
        "code",
        "catalog_sha256",
        "synonyms_sha256",
        "dictionary",
        "runtime",
    )
    if any(any(links[s][k] != links["train"][k] for k in identity_keys) for s in links):
        raise ValueError("Linking pipeline differs across splits")
    for base, trained in zip(CONTROLS, ("b3", "b3l"), strict=True):
        a = checked_rows(ROOT / f"runs/{base}/prompts-dev_eval.jsonl")
        b = checked_rows(ROOT / f"runs/{trained}/prompts-dev_eval.jsonl")
        if len(a) != 100 or [(r["id"], r["messages"]) for r in a] != [
            (r["id"], r["messages"]) for r in b
        ]:
            raise ValueError("Compact control prompts differ from adapter prompts")
    files = source_files(ROOT, "t11a*.py")
    files += [ROOT / f"data/linking/{s}.manifest.json" for s in links]
    for name in CONFIGS:
        files += [ROOT / f"runs/{name}/prompts-dev_eval.jsonl"]
        if RUN_CONFIGS[name].fine_tuned:
            files += [ROOT / f"runs/{name}/sft-{s}.jsonl" for s in ("train", "dev")]
    manifest = {
        "task": "T11A",
        "evaluation_role": "development",
        "expected_rows": 100,
        "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "generator": settings["models"]["generator"],
        "encoder": settings["models"]["encoder"],
        "generation": settings["generation"],
        "dataset_sha256": {s: cfg.sha256_file(ROOT / f"data/{s}.jsonl") for s in links},
        "linking": links,
        "test_v2_unchanged": test_hashes(),
    }
    package_inputs(
        ROOT,
        REPORT,
        output,
        files,
        manifest,
        bundle_metadata={"code_commit": manifest["code_commit"]},
    )
    print(json.dumps({"archive": str(output), "bytes": output.stat().st_size}))


def verify_inputs() -> dict:
    return check_inputs(ROOT, REPORT)


def verify_run(name: str, expected: int) -> tuple[Path, list, dict]:
    prompts = ROOT / f"runs/{name}/prompts-dev_eval.jsonl"
    path = ROOT / f"runs/{name}/seed-42/predictions-dev_eval.jsonl"
    inputs = checked_rows(prompts)
    manifest = verify_predictions(
        path, inputs, generation_provenance(prompts, cfg.load(), name, 42, None)
    )
    rows = cfg.read_jsonl(path)
    if len(rows) != expected or [r["id"] for r in rows] != [r["id"] for r in inputs[:expected]]:
        raise ValueError(f"{name}: expected exactly {expected} ordered unique predictions")
    if expected == 100 and manifest["status"] != "complete":
        raise ValueError(f"{name}: generation is incomplete")
    if any(not r["raw_output"].strip() for r in rows):
        raise ValueError(f"{name}: empty model output")
    return path, rows, manifest


def gpu(home: Path, pins: Path) -> None:
    REPORT.mkdir(parents=True, exist_ok=True)
    status = {"task": "T11A", "evaluation_role": "development", "status": "running"}
    env = offline_environment(home)
    cli = StageRunner(ROOT, REPORT, env)

    try:
        status["inputs"] = verify_inputs()
        write_runtime(REPORT)
        require_cuda("T11A")
        status["cache"] = verify_cache(home, pins)
        for name in training_configs():
            cli(f"preflight-{name}", "preflight", "--config", name, "--training")
        for name in CONTROLS:
            cli(f"preflight-{name}", "preflight", "--config", name)
        for name in CONTROLS:
            cli(f"smoke-{name}", "generate", "--config", name, "--limit", "10")
            path, rows, manifest = verify_run(name, 10)
            smoke = REPORT / f"{name}-smoke-10.jsonl"
            shutil.copy2(path, smoke)
            cfg.write_json(REPORT / f"{name}-smoke-manifest.json", manifest)
            from eth_nl2sql.generation.smoke import inspect_predictions, require_smoke_pass

            inspection = inspect_predictions(rows)
            cfg.write_json(REPORT / f"{name}-smoke-inspection.json", inspection)
            require_smoke_pass(inspection)
            before = cfg.sha256_file(path)
            cli(f"smoke-noop-{name}", "generate", "--config", name, "--limit", "10")
            if cfg.sha256_file(path) != before:
                raise ValueError("Repeated smoke changed existing predictions")
            cli(f"resume-{name}", "generate", "--config", name)
            path, completed, manifest = verify_run(name, 100)
            if completed[:10] != rows:
                raise ValueError("Resume changed the first ten predictions")
            cfg.write_json(
                REPORT / f"{name}-resume.json",
                {
                    "passed": True,
                    "smoke_rows": 10,
                    "final_rows": 100,
                    "first_ten_unchanged": True,
                    "repeated_smoke_noop": True,
                    "session_generated_rows": [s["generated_rows"] for s in manifest["sessions"]],
                },
            )
        status["status"] = "gpu_complete_pending_local_evaluation"
    except BaseException as exc:
        status.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        cfg.write_json(REPORT / "gpu-status.json", status)
        archive_outputs(
            ROOT,
            (ROOT / "runs", REPORT),
            REPORT / "outputs-manifest.json",
            ROOT.parent / "t11a-artifacts.zip",
        )


def collect(archive: Path) -> None:
    manifest = collect_outputs(
        ROOT,
        archive,
        (REPORT / "outputs-manifest.json").relative_to(ROOT).as_posix(),
        can_replace=lambda p: (
            any(part.startswith("seed-") for part in p.parts) or p.parts[0] == "reports"
        ),
    )
    cfg.write_json(
        REPORT / "download-manifest.json",
        {
            "archive_sha256": cfg.sha256_file(archive),
            "files": manifest,
        },
    )
    for name in CONTROLS:
        verify_run(name, 100)
    original = json.loads((REPORT / "inputs-manifest.json").read_text())
    if original["test_v2_unchanged"] != test_hashes():
        raise ValueError("Test v2 changed")
    print("All downloaded files verified; both controls have 100 predictions. Ready for local EX.")


def summarize() -> None:
    inputs = json.loads((REPORT / "inputs-manifest.json").read_text())
    if inputs["test_v2_unchanged"] != test_hashes():
        raise ValueError("Test v2 changed")
    for split, expected in inputs["dataset_sha256"].items():
        if cfg.sha256_file(ROOT / f"data/{split}.jsonl") != expected:
            raise ValueError(f"Development dataset changed: {split}")
    summary = {"task": "T11A", "evaluation_role": "development", "controls": {}}
    for name in CONTROLS:
        path, rows, manifest = verify_run(name, 100)
        evaluation = json.loads(path.with_name("eval-dev_eval.json").read_text())
        if (
            evaluation["n"] != 100
            or evaluation["missing_predictions"]
            or evaluation["predictions_sha256"] != cfg.sha256_file(path)
            or evaluation["evaluation_role"] != "development"
        ):
            raise ValueError(f"Incomplete/stale evaluation: {name}")
        sessions = manifest["sessions"]
        if any(s.get("peak_gpu_memory_gib") is None or not s["hardware"]["gpus"] for s in sessions):
            raise ValueError(f"Missing real GPU measurements: {name}")
        resume = json.loads((REPORT / f"{name}-resume.json").read_text())
        if not resume["passed"]:
            raise ValueError(f"Resume check failed: {name}")
        summary["controls"][name] = {
            "n": 100,
            "execution_accuracy": evaluation["execution_accuracy"],
            "execution_accuracy_ci95": evaluation["execution_accuracy_ci95"],
            "status_counts": evaluation["status_counts"],
            "sql_error_rows": sum(v for k, v in evaluation["status_counts"].items() if k != "ok"),
            "length_limited_rows": manifest["length_limited_rows"],
            "latency_ms": evaluation["generation_ms"],
            "store": evaluation["store"],
            "session_runtime_s": sum(s["runtime_s"] for s in sessions),
            "peak_gpu_allocated_gib": max(s["peak_gpu_memory_gib"] for s in sessions),
            "peak_gpu_reserved_gib": max(s["peak_gpu_reserved_gib"] for s in sessions),
            "sessions": sessions,
            "resume": resume,
            "predictions_sha256": cfg.sha256_file(path),
        }
    summary["preflight"] = {}
    for name in training_configs():
        preflight = json.loads((ROOT / f"runs/{name}/seed-42/preflight-training.json").read_text())
        if not preflight["passed"]:
            raise ValueError(f"Training preflight failed: {name}")
        summary["preflight"][name] = {
            "context_limit": preflight["context_limit"],
            "max_length": preflight["max_length"],
            **{
                s: {
                    k: preflight[s][k]
                    for k in (
                        "input_rows",
                        "kept_rows",
                        "dropped_over_max_length",
                        "dropped_fraction",
                        "min_tokens",
                        "max_tokens",
                    )
                }
                for s in ("train", "dev")
            },
        }
    summary["status"] = "complete"
    summary["completion_uses_accuracy_threshold"] = False
    cfg.write_json(REPORT / "summary.json", summary)
    print(json.dumps({"status": "complete", "summary": str(REPORT / "summary.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("package", "gpu", "collect", "summarize"))
    parser.add_argument("--archive", type=Path, default=ROOT / ".cache/t11a-inputs.zip")
    parser.add_argument("--hf-home", type=Path)
    parser.add_argument("--pins", type=Path, default=ROOT / "configs/t11-model-files.json")
    args = parser.parse_args()
    if args.stage == "package":
        package(args.archive)
    elif args.stage == "gpu":
        if args.hf_home is None:
            parser.error("gpu requires --hf-home")
        gpu(args.hf_home, args.pins)
    elif args.stage == "collect":
        collect(args.archive)
    else:
        summarize()

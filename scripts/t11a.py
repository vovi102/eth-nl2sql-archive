"""T11A: package development inputs, run real GPU controls, and collect intact outputs.

Run with the repository environment; see reports/gpu-development-t11a/README.md.
The GPU phase calls the production CLI in separate processes to exercise resume.
"""

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

from eth_nl2sql import config as cfg  # noqa: E402
from eth_nl2sql.experiments import (  # noqa: E402
    checked_rows,
    generation_provenance,
    verify_predictions,
)

REPORT = ROOT / "reports/gpu-development-t11a"
CONTROLS = ("b3-base", "b3l-base")
CONFIGS = ("b3", "b3l", *CONTROLS)


def test_hashes() -> dict:
    return {
        p.relative_to(ROOT).as_posix(): cfg.sha256_file(p)
        for p in sorted((ROOT / "data/benchmark/v2").rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts
    }


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
        "encoder", "code", "catalog_sha256", "synonyms_sha256", "dictionary", "runtime",
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
    files = [ROOT / p for p in ("pyproject.toml", "uv.lock", "README.md")]
    files += sorted((ROOT / "src").rglob("*.py"))
    files += sorted((ROOT / "scripts").glob("t11a*.py"))
    files += sorted((ROOT / "configs").glob("*"))
    files += [ROOT / f"data/linking/{s}.manifest.json" for s in links]
    for name in CONFIGS:
        files += [ROOT / f"runs/{name}/prompts-dev_eval.jsonl"]
        if name in ("b3", "b3l"):
            files += [ROOT / f"runs/{name}/sft-{s}.jsonl" for s in ("train", "dev")]
    manifest = {
        "task": "T11A", "evaluation_role": "development", "expected_rows": 100,
        "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "generator": settings["models"]["generator"],
        "encoder": settings["models"]["encoder"], "generation": settings["generation"],
        "dataset_sha256": {s: cfg.sha256_file(ROOT / f"data/{s}.jsonl") for s in links},
        "linking": links, "test_v2_unchanged": test_hashes(),
        "files": {p.relative_to(ROOT).as_posix(): cfg.sha256_file(p) for p in files},
    }
    cfg.write_json(REPORT / "inputs-manifest.json", manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT))
        archive.write(
            REPORT / "inputs-manifest.json", REPORT.relative_to(ROOT) / "inputs-manifest.json"
        )
        # Generation needs IDs/questions only. Evaluation gold stays on the local machine.
        rows = cfg.read_jsonl(ROOT / "data/dev_eval.jsonl")
        archive.writestr("data/dev_eval.jsonl", "".join(
            json.dumps({k: r[k] for k in ("id", "question")}) + "\n" for r in rows
        ))
    cfg.write_json(REPORT / "bundle.json", {
        "sha256": cfg.sha256_file(output), "bytes": output.stat().st_size,
        "code_commit": manifest["code_commit"],
    })
    print(json.dumps({"archive": str(output), "bytes": output.stat().st_size}))


def verify_inputs() -> dict:
    manifest = json.loads((REPORT / "inputs-manifest.json").read_text())
    for name, expected in manifest["files"].items():
        if cfg.sha256_file(ROOT / name) != expected:
            raise ValueError(f"Input hash mismatch: {name}")
    return manifest


def verify_cache(home: Path, pins: Path) -> dict:
    settings = cfg.load()["models"]["generator"]
    pin = json.loads(pins.read_text())["models"]["model"]
    if any(pin[k] != settings[k] for k in ("repo_id", "revision")):
        raise ValueError("Mounted model pin differs from experiment.toml")
    snapshot = home / "hub" / ("models--" + pin["repo_id"].replace("/", "--"))
    snapshot /= "snapshots/" + pin["revision"]
    result = {}
    for name, expected in pin["files"].items():
        path = snapshot / name
        size = path.stat().st_size
        h = hashlib.sha256() if expected["algorithm"] == "sha256" else hashlib.sha1()
        if expected["algorithm"] == "git-blob-sha1":
            h.update(f"blob {size}\0".encode())
        with path.open("rb") as handle:
            while chunk := handle.read(8 * 1024 * 1024):
                h.update(chunk)
        if size != expected["bytes"] or h.hexdigest() != expected["digest"]:
            raise ValueError(f"Mounted model file failed checksum: {name}")
        result[name] = {"bytes": size, "digest": h.hexdigest(), "passed": True}
        print("Verified model file:", name, flush=True)
    return result


def verify_run(name: str, expected: int) -> tuple[Path, list, dict]:
    prompts = ROOT / f"runs/{name}/prompts-dev_eval.jsonl"
    path = ROOT / f"runs/{name}/seed-42/predictions-dev_eval.jsonl"
    inputs = checked_rows(prompts)
    manifest = verify_predictions(path, inputs, generation_provenance(
        prompts, cfg.load(), name, 42, None
    ))
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
    stages = []
    status = {"task": "T11A", "evaluation_role": "development", "status": "running"}
    env = dict(os.environ, HF_HOME=str(home), HF_HUB_CACHE=str(home / "hub"),
               HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    os.environ.update(env)

    def cli(stage: str, *args: str) -> None:
        print("Starting:", stage, flush=True)
        start = time.monotonic()
        with (REPORT / f"{stage}.log").open("w") as log:
            result = subprocess.run([sys.executable, "-m", "eth_nl2sql.cli", *args],
                                    cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        stages.append({"stage": stage, "runtime_s": time.monotonic() - start,
                       "returncode": result.returncode})
        cfg.write_json(REPORT / "stages.json", stages)
        if result.returncode:
            raise RuntimeError(f"{stage} failed; inspect {stage}.log")

    try:
        status["inputs"] = verify_inputs()
        cfg.write_json(REPORT / "runtime.json", {
            "python": sys.version, "packages": {
                d.metadata["Name"]: d.version for d in importlib.metadata.distributions()
            }, "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        })
        import torch

        if not torch.cuda.is_available():
            raise ValueError("T11A requires an actual CUDA GPU")
        status["cache"] = verify_cache(home, pins)
        for name in ("b3", "b3l"):
            cli(f"preflight-{name}", "preflight", "--config", name, "--training")
        for name in CONTROLS:
            cli(f"preflight-{name}", "preflight", "--config", name)
        for name in CONTROLS:
            cli(f"smoke-{name}", "generate", "--config", name, "--limit", "10")
            path, rows, manifest = verify_run(name, 10)
            smoke = REPORT / f"{name}-smoke-10.jsonl"
            shutil.copy2(path, smoke)
            cfg.write_json(REPORT / f"{name}-smoke-manifest.json", manifest)
            before = cfg.sha256_file(path)
            cli(f"smoke-noop-{name}", "generate", "--config", name, "--limit", "10")
            if cfg.sha256_file(path) != before:
                raise ValueError("Repeated smoke changed existing predictions")
            cli(f"resume-{name}", "generate", "--config", name)
            path, completed, manifest = verify_run(name, 100)
            if completed[:10] != rows:
                raise ValueError("Resume changed the first ten predictions")
            cfg.write_json(REPORT / f"{name}-resume.json", {
                "passed": True, "smoke_rows": 10, "final_rows": 100,
                "first_ten_unchanged": True, "repeated_smoke_noop": True,
                "session_generated_rows": [s["generated_rows"] for s in manifest["sessions"]],
            })
        status["status"] = "gpu_complete_pending_local_evaluation"
    except BaseException as exc:
        status.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        cfg.write_json(REPORT / "gpu-status.json", status)
        artifacts = [p for base in (ROOT / "runs", REPORT) for p in base.rglob("*") if p.is_file()]
        cfg.write_json(ROOT / "outputs-manifest.json", {
            p.relative_to(ROOT).as_posix(): cfg.sha256_file(p) for p in artifacts
        })
        with zipfile.ZipFile(ROOT.parent / "t11a-artifacts.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for path in [*artifacts, ROOT / "outputs-manifest.json"]:
                z.write(path, path.relative_to(ROOT))


def collect(archive: Path) -> None:
    with zipfile.ZipFile(archive) as z:
        manifest = json.loads(z.read("outputs-manifest.json"))
        for name, expected in manifest.items():
            dest = ROOT / name
            if not dest.resolve().is_relative_to(ROOT):
                raise ValueError(f"Invalid artifact path: {name}")
            data = z.read(name)
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError(f"Downloaded artifact hash mismatch: {name}")
            # Never replace prepared prompts/SFT with different files during collection.
            if dest.exists() and "/seed-" not in name and not name.startswith("reports/"):
                if dest.read_bytes() != data:
                    raise ValueError(f"Local input differs: {name}")
        for name in manifest:
            dest = ROOT / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(name))
        cfg.write_json(REPORT / "download-manifest.json", {
            "archive_sha256": cfg.sha256_file(archive), "files": manifest,
        })
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
        if (evaluation["n"] != 100 or evaluation["missing_predictions"]
                or evaluation["predictions_sha256"] != cfg.sha256_file(path)
                or evaluation["evaluation_role"] != "development"):
            raise ValueError(f"Incomplete/stale evaluation: {name}")
        sessions = manifest["sessions"]
        if any(s.get("peak_gpu_memory_gib") is None or not s["hardware"]["gpus"] for s in sessions):
            raise ValueError(f"Missing real GPU measurements: {name}")
        resume = json.loads((REPORT / f"{name}-resume.json").read_text())
        if not resume["passed"]:
            raise ValueError(f"Resume check failed: {name}")
        summary["controls"][name] = {
            "n": 100, "execution_accuracy": evaluation["execution_accuracy"],
            "execution_accuracy_ci95": evaluation["execution_accuracy_ci95"],
            "status_counts": evaluation["status_counts"],
            "sql_error_rows": sum(v for k, v in evaluation["status_counts"].items() if k != "ok"),
            "length_limited_rows": manifest["length_limited_rows"],
            "latency_ms": evaluation["generation_ms"], "store": evaluation["store"],
            "session_runtime_s": sum(s["runtime_s"] for s in sessions),
            "peak_gpu_allocated_gib": max(s["peak_gpu_memory_gib"] for s in sessions),
            "peak_gpu_reserved_gib": max(s["peak_gpu_reserved_gib"] for s in sessions),
            "sessions": sessions, "resume": resume,
            "predictions_sha256": cfg.sha256_file(path),
        }
    summary["preflight"] = {}
    for name in ("b3", "b3l"):
        preflight = json.loads((ROOT / f"runs/{name}/seed-42/preflight-training.json").read_text())
        if not preflight["passed"]:
            raise ValueError(f"Training preflight failed: {name}")
        summary["preflight"][name] = {
            "context_limit": preflight["context_limit"], "max_length": preflight["max_length"],
            **{s: {k: preflight[s][k] for k in (
                "input_rows", "kept_rows", "dropped_over_max_length", "dropped_fraction",
                "min_tokens", "max_tokens",
            )} for s in ("train", "dev")},
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

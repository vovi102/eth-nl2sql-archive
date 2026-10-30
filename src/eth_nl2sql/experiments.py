"""Seed isolation, content provenance and resource measurement for GPU runs."""

from __future__ import annotations

import gc
import json
import platform
import re
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from pathlib import Path

from eth_nl2sql.artifacts import atomic_write_json, json_digest
from eth_nl2sql.config import ROOT, read_jsonl, sha256_file
from eth_nl2sql.generation.prompt import messages_digest
from eth_nl2sql.generation.runs import CONFIGS

SEEDS = (42, 43, 44)


# Compatibility for existing experiment consumers.
digest = json_digest


def selected_seeds(value: str | int, config: Mapping) -> tuple[int, ...]:
    configured = tuple(config.get("training", {}).get("seeds", SEEDS))
    if configured != SEEDS:
        raise ValueError(f"T10 requires the fixed training seeds {SEEDS}")
    values = configured if value == "all" else (int(value),)
    if any(seed not in SEEDS for seed in values):
        raise ValueError(f"Seed must be one of {SEEDS}")
    return values


def run_directory(runs_dir: Path, name: str, seed: int) -> Path:
    if name not in CONFIGS or seed not in SEEDS:
        raise ValueError(f"Unknown run/seed: {name}/{seed}")
    return runs_dir / name / f"seed-{seed}"


def model_digest(config: Mapping) -> str:
    spec = config["models"]["generator"]
    if not spec.get("repo_id") or not spec.get("revision"):
        raise ValueError("Generator repo_id and pinned revision are required")
    if not re.fullmatch(r"[0-9a-f]{40}", spec["revision"]):
        raise ValueError("Generator revision must be an immutable 40-character commit SHA")
    if spec.get("load_in_4bit") is not True:
        raise ValueError("The GPU backend requires load_in_4bit=true")
    return json_digest(spec)


def source_digest(*names: str) -> str:
    return json_digest({name: sha256_file(ROOT / "src/eth_nl2sql" / name) for name in names})


def tree_digest(directory: Path, *, exclude: str | None = None) -> str:
    files = {
        p.relative_to(directory).as_posix(): sha256_file(p)
        for p in sorted(directory.rglob("*"))
        if p.is_file() and p.name != exclude
    }
    if not files:
        raise ValueError(f"Missing or empty artifact directory: {directory}")
    return json_digest(files)


def checked_rows(path: Path, *, training: bool = False) -> list[dict]:
    rows = read_jsonl(path)
    if not rows:
        raise ValueError(f"Empty input: {path}")
    ids = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"Expected an object row in {path}")
        identifier = row.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError(f"Missing/duplicate row ID in {path}: {identifier!r}")
        ids.add(identifier)
        messages = row.get("messages")
        if (
            not isinstance(messages, list)
            or not messages
            or any(
                not isinstance(m, dict)
                or m.get("role") not in ("system", "user", "assistant")
                or not isinstance(m.get("content"), str)
                or not m["content"].strip()
                for m in messages
            )
        ):
            raise ValueError(f"Invalid messages for {identifier} in {path}")
        if training:
            if not isinstance(row.get("target"), str) or not row["target"].strip():
                raise ValueError(f"Empty SQL target for {identifier} in {path}")
        if not training or "prompt_sha256" in row:
            if row.get("prompt_sha256") != messages_digest(messages):
                raise ValueError(f"Prompt hash mismatch for {identifier} in {path}")
    return rows


def training_provenance(
    train_path: Path, dev_path: Path, config: Mapping, name: str, seed: int
) -> dict:
    selected_seeds(seed, config)
    if not CONFIGS[name].fine_tuned:
        raise ValueError(f"{name} is a base model configuration")
    return {
        "config": name,
        "seed": seed,
        "run_config": asdict(CONFIGS[name]),
        "generator": dict(config["models"]["generator"]),
        "model_sha256": model_digest(config),
        "qlora": dict(config["qlora"]),
        "qlora_sha256": json_digest(config["qlora"]),
        "train_sha256": sha256_file(train_path),
        "dev_sha256": sha256_file(dev_path),
        "code_sha256": source_digest(
            "train_qlora.py", "generation/backend.py", "generation/prompt.py", "generation/runs.py"
        ),
    }


def check_manifest(path: Path, provenance: Mapping) -> dict:
    if not path.is_file():
        raise ValueError(f"Missing provenance manifest: {path}")
    manifest = json.loads(path.read_text())
    if manifest.get("version") != 1 or manifest.get("provenance") != provenance:
        raise ValueError(f"Provenance mismatch: {path}; use a new run directory")
    return manifest


def manifest_record(provenance: Mapping, **extra) -> dict:
    return {"version": 1, "provenance": dict(provenance), **extra}


def adapter_path(name: str, out_dir: Path, requested: Path | None = None) -> Path | None:
    if not CONFIGS[name].fine_tuned:
        if requested is not None:
            raise ValueError(f"{name} must run without an adapter")
        return None
    expected = out_dir / "adapter"
    if requested is not None and requested.resolve() != expected.resolve():
        raise ValueError(f"{name} requires the adapter for this seed: {expected}")
    return expected


def adapter_digest(adapter: Path | None, config: Mapping, name: str, seed: int) -> str | None:
    run = CONFIGS[name]
    if not run.fine_tuned:
        if adapter is not None:
            raise ValueError(f"{name} is a base control and must not load an adapter")
        return None
    if adapter is None:
        raise ValueError(f"{name}/seed-{seed} requires its trained adapter")
    # SFT inputs travel with the config; paths are intentionally absent from the
    # identity so an intact run can be copied between Kaggle and the local machine.
    parent = adapter.parent
    inputs = parent.parent
    provenance = training_provenance(
        inputs / "sft-train.jsonl", inputs / "sft-dev.jsonl", config, name, seed
    )
    manifest = check_manifest(parent / "training-manifest.json", provenance)
    current = tree_digest(adapter)
    if manifest.get("status") != "complete" or manifest.get("adapter_sha256") != current:
        raise ValueError(f"Incomplete training or adapter hash mismatch: {adapter}")
    return current


def generation_provenance(
    prompts: Path, config: Mapping, name: str, seed: int, adapter: Path | None
) -> dict:
    selected_seeds(seed, config)
    return {
        "config": name,
        "seed": seed,
        "run_config": asdict(CONFIGS[name]),
        "generator": dict(config["models"]["generator"]),
        "prompts_sha256": sha256_file(prompts),
        "model_sha256": model_digest(config),
        "adapter_sha256": adapter_digest(adapter, config, name, seed),
        "generation": dict(config["generation"]),
        "generation_sha256": json_digest(config["generation"]),
        "code_sha256": source_digest("generation/backend.py", "generation/prompt.py"),
    }


def prediction_manifest(path: Path) -> Path:
    return path.with_suffix(".manifest.json")


def verify_predictions(path: Path, prompts: Sequence[Mapping], provenance: Mapping) -> dict:
    manifest = check_manifest(prediction_manifest(path), provenance)
    if not path.exists():
        if manifest.get("predictions_sha256"):
            raise ValueError(f"Missing predictions: {path}")
        return manifest
    expected_hash = manifest.get("predictions_sha256")
    if expected_hash and sha256_file(path) != expected_hash:
        raise ValueError(f"Prediction artifact hash mismatch: {path}")
    by_id = {row["id"]: row for row in prompts}
    seen = set()
    for row in read_jsonl(path):
        identifier = row.get("id")
        checksum = row.get("record_sha256")
        if (
            identifier not in by_id
            or identifier in seen
            or row.get("prompt_sha256") != by_id[identifier]["prompt_sha256"]
            or row.get("provenance_sha256") != json_digest(provenance)
            or checksum != json_digest({k: v for k, v in row.items() if k != "record_sha256"})
        ):
            raise ValueError(f"Prediction provenance/hash mismatch: {path}, {identifier}")
        seen.add(identifier)
    return manifest


class ResourceMonitor:
    """Measure the whole GPU stage, including model loading, on every visible GPU."""

    def __init__(self) -> None:
        import torch

        # Trainer/model reference cycles must not keep the previous seed on GPU.
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        self.started = time.perf_counter()
        self.gpus = []
        for index in range(torch.cuda.device_count()):
            torch.cuda.synchronize(index)
            torch.cuda.reset_peak_memory_stats(index)
            self.gpus.append(torch.cuda.get_device_name(index))

    def summary(self) -> dict:
        import torch

        allocated, reserved = [], []
        for index in range(len(self.gpus)):
            torch.cuda.synchronize(index)
            allocated.append(torch.cuda.max_memory_allocated(index) / 2**30)
            reserved.append(torch.cuda.max_memory_reserved(index) / 2**30)
        return {
            "runtime_s": time.perf_counter() - self.started,
            "peak_gpu_memory_gib": max(allocated, default=None),
            "peak_gpu_reserved_gib": max(reserved, default=None),
            "per_gpu_peak_allocated_gib": allocated,
            "hardware": {
                "platform": platform.platform(),
                "python": platform.python_version(),
                "torch": torch.__version__,
                "cuda": torch.version.cuda,
                "gpus": self.gpus,
            },
        }


def write_manifest(path: Path, provenance: Mapping, **extra) -> None:
    atomic_write_json(path, manifest_record(provenance, **extra))

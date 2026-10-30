"""Checksummed bundles, GPU stage logs and intact artifact collection for T11."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path, PurePosixPath

from eth_nl2sql import config as cfg


def benchmark_hashes(root: Path) -> dict:
    return {
        p.relative_to(root).as_posix(): cfg.sha256_file(p)
        for p in sorted((root / "data/benchmark/v2").rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts
    }


def source_files(root: Path, script_pattern: str) -> list[Path]:
    return [
        *(root / p for p in ("pyproject.toml", "uv.lock", "README.md")),
        *sorted((root / "src").rglob("*.py")),
        *sorted((root / "scripts").glob(script_pattern)),
        *(p for p in sorted((root / "configs").glob("*")) if p.is_file()),
    ]


def package_inputs(
    root: Path,
    report: Path,
    output: Path,
    files: list[Path],
    manifest: dict,
    *,
    bundle_metadata: dict | None = None,
    persist_reports: bool = True,
) -> dict:
    manifest = {
        **manifest,
        "files": {p.relative_to(root).as_posix(): cfg.sha256_file(p) for p in files},
    }
    manifest_path = report / "inputs-manifest.json"
    if persist_reports:
        cfg.write_json(manifest_path, manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:

        def write(name: str, data: bytes) -> None:
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)

        for path in files:
            write(path.relative_to(root).as_posix(), path.read_bytes())
        write(
            manifest_path.relative_to(root).as_posix(),
            (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(),
        )
        # Evaluation gold stays local; the GPU receives only IDs and questions.
        write(
            "data/dev_eval.jsonl",
            "".join(
                json.dumps({k: row[k] for k in ("id", "question")}) + "\n"
                for row in cfg.read_jsonl(root / "data/dev_eval.jsonl")
            ).encode(),
        )
    if persist_reports:
        cfg.write_json(
            report / "bundle.json",
            {
                "sha256": cfg.sha256_file(output),
                "bytes": output.stat().st_size,
                **(bundle_metadata or {}),
            },
        )
    return manifest


def verify_inputs(root: Path, report: Path) -> dict:
    manifest = json.loads((report / "inputs-manifest.json").read_text())
    for name, expected in manifest["files"].items():
        if cfg.sha256_file(root / name) != expected:
            raise ValueError(f"Input hash mismatch: {name}")
    return manifest


def verify_cache(home: Path, pins: Path, *, component: str = "model") -> dict:
    settings = cfg.load()["models"]["generator"]
    models = json.loads(pins.read_text())["models"]
    if any(models["model"][k] != settings[k] for k in ("repo_id", "revision")):
        raise ValueError("Mounted model pin differs from experiment.toml")
    if component == "all":
        return {name: _verify_cached_model(home, pin) for name, pin in models.items()}
    if component not in models:
        raise ValueError(f"Unknown cache component: {component}")
    return _verify_cached_model(home, models[component])


def _verify_cached_model(home: Path, pin: dict) -> dict:
    snapshot = home / "hub" / ("models--" + pin["repo_id"].replace("/", "--"))
    snapshot /= "snapshots/" + pin["revision"]
    result = {}
    for name, expected in pin["files"].items():
        path = snapshot / name
        if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts:
            raise ValueError(f"Invalid model cache path: {name}")
        if expected["algorithm"] not in ("sha256", "sha1", "git-blob-sha1"):
            raise ValueError(f"Unknown model checksum algorithm: {expected['algorithm']}")
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


def offline_environment(home: Path) -> dict[str, str]:
    env = dict(
        os.environ,
        HF_HOME=str(home),
        HF_HUB_CACHE=str(home / "hub"),
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        TOKENIZERS_PARALLELISM="false",
    )
    os.environ.update(env)
    return env


def write_runtime(directory: Path) -> None:
    cfg.write_json(
        directory / "runtime.json",
        {
            "python": sys.version,
            "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        },
    )


def require_cuda(task: str) -> None:
    import torch

    if not torch.cuda.is_available():
        raise ValueError(f"{task} requires an actual CUDA GPU")


class StageRunner:
    def __init__(
        self,
        root: Path,
        directory: Path,
        env: dict[str, str],
        *,
        stream: bool = False,
    ) -> None:
        self.root, self.directory, self.env = root, directory, env
        self.stream = stream
        self.stages: list[dict] = []

    def __call__(self, stage: str, *args: str) -> None:
        print("Starting:", stage, flush=True)
        started = time.monotonic()
        argv = [sys.executable, "-u", "-m", "eth_nl2sql.cli", *args]
        with (self.directory / f"{stage}.log").open("w") as log:
            if self.stream:
                process = subprocess.Popen(
                    argv,
                    cwd=self.root,
                    env=self.env,
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
                process.stdout.close()
            else:
                returncode = subprocess.run(
                    argv,
                    cwd=self.root,
                    env=self.env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                ).returncode
        self.stages.append(
            {
                "stage": stage,
                "runtime_s": time.monotonic() - started,
                "returncode": returncode,
            }
        )
        cfg.write_json(self.directory / "stages.json", self.stages)
        if returncode:
            raise RuntimeError(f"{stage} failed; inspect {stage}.log")


def archive_outputs(
    root: Path,
    directories: Iterable[Path],
    manifest_path: Path,
    archive: Path,
) -> None:
    files = sorted(
        {
            p
            for base in directories
            for p in base.rglob("*")
            if p.is_file() and p not in (manifest_path, archive)
        }
    )
    cfg.write_json(
        manifest_path, {p.relative_to(root).as_posix(): cfg.sha256_file(p) for p in files}
    )
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in [*files, manifest_path]:
            bundle.write(path, path.relative_to(root))


def collect_outputs(
    root: Path,
    archive: Path,
    manifest_name: str,
    *,
    can_replace: Callable[[PurePosixPath], bool],
    expected_json: Mapping[str, object] | None = None,
) -> dict:
    """Validate the entire archive before writing any files into the workspace."""
    with zipfile.ZipFile(archive) as bundle:
        manifest_bytes = bundle.read(manifest_name)
        manifest = json.loads(manifest_bytes)
        manifest_path = root / manifest_name
        if not manifest_path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Invalid artifact manifest path: {manifest_name}")
        for name, expected in (expected_json or {}).items():
            if name not in manifest or json.loads(bundle.read(name)) != expected:
                raise ValueError(f"Artifact differs from the submitted input: {name}")
        for name, expected in manifest.items():
            relative = PurePosixPath(name)
            destination = root / name
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or not destination.resolve().is_relative_to(root.resolve())
            ):
                raise ValueError(f"Invalid artifact path: {name}")
            with bundle.open(name) as handle:
                checksum = hashlib.file_digest(handle, "sha256").hexdigest()
            if checksum != expected:
                raise ValueError(f"Artifact hash mismatch: {name}")
            if (
                destination.exists()
                and cfg.sha256_file(destination) != expected
                and not can_replace(relative)
            ):
                raise ValueError(f"Refusing to replace existing artifact: {name}")
        for name in manifest:
            destination = root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(name) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_bytes(manifest_bytes)
    return manifest

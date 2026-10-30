"""Acquire pinned model files on Kaggle; verify bytes without loading a model."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from eth_nl2sql import config as cfg
from eth_nl2sql.gpu_workflow import verify_cache


def fetch_cache(
    home: Path,
    pins: Path,
    *,
    token: str,
    download: Callable | None = None,
) -> dict:
    if not token.strip():
        raise ValueError("A Hugging Face token from Kaggle Secrets is required")
    models = json.loads(pins.read_text())["models"]
    settings = cfg.load()["models"]["generator"]
    if any(models["model"][key] != settings[key] for key in ("repo_id", "revision")):
        raise ValueError("Model cache pin differs from experiment.toml")
    for model in models.values():
        if not re.fullmatch(r"[0-9a-f]{40}", model["revision"]) or not model["files"]:
            raise ValueError("Model cache requires pinned revisions and file checksums")
        for name in model["files"]:
            if Path(name).is_absolute() or ".." in Path(name).parts:
                raise ValueError(f"Invalid model file path: {name}")
    if download is None:
        if not home.resolve().is_relative_to(Path("/kaggle/working")):
            raise ValueError("Acquire model weights only under /kaggle/working")
        home.parent.mkdir(parents=True, exist_ok=True)
        required = sum(
            file["bytes"] for model in models.values() for file in model["files"].values()
        )
        if shutil.disk_usage(home.parent).free < required + 1024**3:
            raise ValueError("Insufficient disk space for the pinned cache and download margin")
        os.environ.update(
            HF_HOME=str(home),
            HF_HUB_DISABLE_IMPLICIT_TOKEN="1",
            HF_HUB_DISABLE_TELEMETRY="1",
            HF_HUB_DISABLE_XET="1",
            HF_HUB_OFFLINE="0",
            HF_HUB_DISABLE_PROGRESS_BARS="1",
        )
        import requests
        from huggingface_hub import configure_http_backend, hf_hub_download

        def session():
            result = requests.Session()
            result.trust_env = False
            return result

        configure_http_backend(backend_factory=session)
        download = hf_hub_download
    for component, model in models.items():
        for name in model["files"]:
            try:
                download(
                    repo_id=model["repo_id"],
                    revision=model["revision"],
                    filename=name,
                    cache_dir=home / "hub",
                    token=token if component == "model" else False,
                )
            except Exception:
                raise RuntimeError(
                    f"Cache acquisition failed for {component}/{name}; check access and network"
                ) from None
    result = verify_cache(home, pins, component="all")
    cfg.write_json(home.parent / "model-cache-verification.json", result)
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("fetch", "verify"))
    parser.add_argument("--pins", type=Path, default=cfg.ROOT / "configs/t11-model-files.json")
    parser.add_argument("--hf-home", type=Path, required=True)
    parser.add_argument("--allow-downloads", action="store_true")
    parser.add_argument("--token-stdin", action="store_true")
    args = parser.parse_args(argv)
    if args.action == "fetch":
        if not args.allow_downloads or not args.token_stdin:
            parser.error("fetch requires --allow-downloads and --token-stdin")
        result = fetch_cache(args.hf_home, args.pins, token=sys.stdin.read().strip())
    else:
        result = verify_cache(args.hf_home, args.pins, component="all")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

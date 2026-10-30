"""Build, inspect, publish inputs and run Kaggle workflows as separate operations."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from eth_nl2sql import config as cfg
from eth_nl2sql.generation.runs import Job
from eth_nl2sql.gpu_notebook import NotebookSpec, build_notebook, notebook_source
from eth_nl2sql.gpu_workflow import benchmark_hashes, package_inputs, source_files
from eth_nl2sql.kaggle import KaggleClient, load_settings

WORKFLOWS = ("fine_tune", "model_cache")


def build_workflows(root: Path, output: Path, *, job: str = "b3-seed-42") -> dict:
    """Prepare both notebooks and their inputs without changing research evidence."""
    selected = Job.parse(job)
    if not selected.config.fine_tuned:
        raise ValueError("The fine-tuning notebook requires an adapter-producing job")
    settings = load_settings(root / "configs/kaggle.toml")
    files = source_files(root, "*.py")
    files += [root / f"data/{split}.jsonl" for split in ("train", "dev")]
    directory = root / "runs" / selected.config.name
    files += [directory / "prompts-dev_eval.jsonl"]
    files += [directory / f"sft-{split}.jsonl" for split in ("train", "dev")]

    def git(*args: str) -> str | None:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() if result.returncode == 0 else None

    manifest = {
        "script_pattern": "*.py",
        "task": "development",
        "evaluation_role": "development",
        "code_commit": git("rev-parse", "HEAD"),
        "working_tree_changes": bool(
            git(
                "status",
                "--porcelain",
                "--",
                "src",
                "scripts",
                "configs",
                "pyproject.toml",
                "uv.lock",
                "README.md",
            )
        ),
        "test_v2": benchmark_hashes(root),
        "settings": cfg.load(root / "configs/experiment.toml"),
        "dev_eval_sha256": cfg.sha256_file(root / "data/dev_eval.jsonl"),
    }
    output.mkdir(parents=True, exist_ok=True)
    archive = output / "inputs.bundle"
    package_inputs(
        root,
        root / "reports/experiments",
        archive,
        files,
        manifest,
        persist_reports=False,
    )
    specs = {
        "fine_tune": NotebookSpec(
            "t11b",
            "scripts/t11b.py",
            "configs/t11b-gpu-requirements.txt",
            job=selected.identifier,
            live_logs=True,
            name="fine_tune",
        ),
        "model_cache": NotebookSpec(
            "model-cache",
            "scripts/model_cache.py",
            "configs/model-cache-requirements.txt",
            role="model_cache",
            name="model_cache",
        ),
    }
    result = {}
    for name, spec in specs.items():
        target = output / name
        kernel = settings.cache_kernel if name == "model_cache" else settings.kernel(job)
        build_notebook(
            archive,
            target,
            kernel,
            spec,
            cache_kernel=settings.cache_kernel,
            input_dataset=settings.input_dataset,
        )
        local = root / "notebooks" / f"{name}.ipynb"
        local.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target / f"{name}.ipynb", local)
        result[name] = {"notebook": str(local), "deployment": str(target), "kernel": kernel}
    cfg.write_json(output / "build.json", {"job": selected.identifier, "workflows": result})
    return result


def local_status(root: Path, deployment: Path, name: str | None = None) -> dict:
    record = json.loads((deployment / "deployment.json").read_text())
    changed = [
        path
        for path, expected in record["files"].items()
        if not (root / path).is_file() or cfg.sha256_file(root / path) != expected
    ]
    if (
        record.get("dev_eval_sha256")
        and cfg.sha256_file(root / "data/dev_eval.jsonl") != record["dev_eval_sha256"]
    ):
        changed.append("data/dev_eval.jsonl")
    # Also notice added/deleted source files, which an old manifest cannot enumerate.
    if record.get("script_pattern"):
        current_sources = {
            p.relative_to(root).as_posix() for p in source_files(root, record["script_pattern"])
        }
        recorded_sources = {p for p in record["files"] if not p.startswith(("data/", "runs/"))}
        changed += sorted(current_sources ^ recorded_sources)
    if name is not None:
        local = root / "notebooks" / f"{name}.ipynb"
        built = deployment / f"{name}.ipynb"
        if not local.exists() or notebook_source(json.loads(local.read_text())) != notebook_source(
            json.loads(built.read_text())
        ):
            changed.append(f"notebooks/{name}.ipynb")
    metadata = json.loads((deployment / "kernel-metadata.json").read_text())
    staged = deployment / metadata["code_file"]
    if not staged.is_file() or cfg.sha256_file(staged) != record["notebook_sha256"]:
        changed.append("staged_notebook")
    archive = deployment / "inputs" / record["input_file"]
    if not archive.is_file() or cfg.sha256_file(archive) != record["provenance"]["input_sha256"]:
        changed.append("staged_inputs")
    return {
        "status": "needs_build" if changed else "current",
        "changed": sorted(set(changed)),
        "provenance": record["provenance"],
    }


def _command(args: argparse.Namespace) -> None:
    root, output = cfg.ROOT, args.output.resolve()
    if args.action == "build":
        result = build_workflows(root, output, job=args.job)
    else:
        names = (args.workflow.replace("-", "_"),) if args.workflow else WORKFLOWS
        if args.deployment and not args.workflow:
            names = (args.deployment.name,)
        result = {}
        for name in names:
            deployment = args.deployment.resolve() if args.deployment else output / name
            canonical = None if args.deployment else name
            client = KaggleClient(root, output / "observations" / name)
            if args.action == "status":
                if not (deployment / "deployment.json").exists():
                    result[name] = {"local": {"status": "needs_build"}}
                    continue
                record = {"local": local_status(root, deployment, canonical)}
                if not args.offline:
                    try:
                        record["kaggle"] = client.sync_status(deployment)
                    except (RuntimeError, subprocess.TimeoutExpired) as exc:
                        record["kaggle"] = {"status": "unavailable", "error": str(exc)}
                result[name] = record
            else:
                state = local_status(root, deployment, canonical)
                if state["status"] != "current":
                    raise ValueError("Local source changed; run eth-nl2sql kaggle build first")
                if args.action == "publish-inputs":
                    result[name] = client.publish_inputs(deployment, create=args.create)
                else:
                    metadata = json.loads((deployment / "kernel-metadata.json").read_text())
                    with client.session(metadata["id"]):
                        result[name] = {
                            "kernel_ref": client.push(
                                deployment, producer=metadata["id"] != load_settings().kernel()
                            )
                        }
    print(json.dumps(result, indent=2))


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser("kaggle", help="build and inspect local/Kaggle notebook parity")
    actions = parser.add_subparsers(dest="action", required=True)
    for name in ("build", "status", "publish-inputs", "run"):
        command = actions.add_parser(name)
        command.set_defaults(handler=_command)
        command.add_argument("--output", type=Path, default=cfg.ROOT / ".cache/kaggle")
        if name == "build":
            command.add_argument("--job", default="b3-seed-42")
        else:
            command.add_argument("--deployment", type=Path, help="inspect a legacy builder output")
            command.add_argument(
                "--workflow",
                choices=("fine-tune", "model-cache"),
                default=None if name == "status" else "fine-tune",
            )
        if name == "status":
            command.add_argument("--offline", action="store_true", help="check local inputs only")
        if name == "publish-inputs":
            command.add_argument(
                "--create", action="store_true", help="first private dataset version"
            )

"""Readable Kaggle notebooks backed by checksummed input attachments."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from pprint import pformat
from string import Template

from eth_nl2sql import config as cfg
from eth_nl2sql.artifacts import json_digest
from eth_nl2sql.kaggle import load_settings

LIVE_PROCESS = """process = subprocess.Popen(argv, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in process.stdout:
            log.write(line)
            log.flush()
            print(line, end='', flush=True)
        result = subprocess.CompletedProcess(argv, process.wait())"""

_EXTRACT = """import hashlib, json, os, subprocess, sys, tempfile, zipfile
from pathlib import Path

matches = list(Path('/kaggle/input').rglob(INPUT_FILE))
if len(matches) != 1:
    raise ValueError('Attach the matching workflow inputs dataset: ' + INPUT_FILE)
archive = matches[0]
h = hashlib.sha256()
with archive.open('rb') as handle:
    while chunk := handle.read(8 * 1024 * 1024):
        h.update(chunk)
if h.hexdigest() != INPUT_SHA256:
    raise ValueError('Input archive checksum mismatch; rebuild and publish matching inputs')
root = Path('/kaggle/working/eth-nl2sql')
root.mkdir(exist_ok=False)
with zipfile.ZipFile(archive) as bundle:
    for member in bundle.infolist():
        if not (root / member.filename).resolve().is_relative_to(root):
            raise ValueError('Invalid bundle path')
        if (member.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError('Symlink in input bundle')
    bundle.extractall(root)
print('Verified inputs:', INPUT_SHA256)
print('Code commit:', PROVENANCE.get('code_commit'))
print('Source fingerprint:', PROVENANCE.get('source_sha256'))
"""

_RUNTIME = Template("""scratch = Path(tempfile.mkdtemp(prefix='workflow-runtime-', dir='/tmp'))
log_root = Path('/kaggle/working/$task-bootstrap')
log_root.mkdir()

def run(stage, argv, env=None):
    print('Starting:', stage, flush=True)
    with (log_root / (stage + '.log')).open('w') as log:
        $process
    if result.returncode:
        print((log_root / (stage + '.log')).read_text()[-6000:], flush=True)
        raise RuntimeError(stage + ' failed')
    print('Completed:', stage, flush=True)

run('bootstrap-uv', [sys.executable, '-m', 'pip', '--isolated', 'install',
    '--no-deps', '--target', str(scratch / 'bootstrap'), 'uv==0.11.14'])
uv = str(scratch / 'bootstrap/bin/uv')
runtime = scratch / 'runtime'
run('python311', [uv, '--no-config', 'venv', '--python', '3.11.15',
    '--managed-python', str(runtime)])
python = str(runtime / 'bin/python')
run('install-locked-environment', [uv, '--no-config', '--no-cache', 'pip', 'sync',
    '--python', python, '--require-hashes', '--index-url', 'https://pypi.org/simple',
    str(root / '$requirements')])
""")

_TRAIN = Template("""matches = list(Path('/kaggle/input').rglob($model_glob))
if len(matches) != 1:
    raise ValueError('Expected one attached pinned model cache: ' + str(matches))
home = matches[0].parents[4]
env = dict(os.environ, PYTHONPATH=str(root / 'src'), OMP_NUM_THREADS='2',
    HF_HOME=str(home), HF_HUB_CACHE=str(home / 'hub'), HF_HUB_OFFLINE='1',
    TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
    HF_HUB_DISABLE_IMPLICIT_TOKEN='1', WANDB_DISABLED='true')
run('gpu-pipeline', [python, str(root / '$script'), 'gpu',
    $job_args'--hf-home', str(home)], env)
print('Copy $artifact back intact for local development EX.', flush=True)
""")

_CACHE = """from kaggle_secrets import UserSecretsClient

# Add HF_TOKEN in Kaggle Add-ons > Secrets. It is passed only over stdin.
token = UserSecretsClient().get_secret('HF_TOKEN')
env = dict(os.environ, PYTHONPATH=str(root / 'src'), HF_HUB_DISABLE_IMPLICIT_TOKEN='1')
result = subprocess.run(
    [python, str(root / 'scripts/model_cache.py'), 'fetch',
     '--hf-home', '/kaggle/working/model-cache', '--allow-downloads', '--token-stdin'],
    input=token, text=True, env=env,
)
del token
if result.returncode:
    raise RuntimeError('Model cache acquisition or verification failed')
print('Verified model cache is ready for use by the fine-tuning notebook.')
"""


@dataclass(frozen=True)
class NotebookSpec:
    task: str
    script: str
    requirements: str
    job: str | None = None
    live_logs: bool = False
    extra_kernel_sources: tuple[str, ...] = ()
    role: str = "experiment"
    name: str | None = None


def render_bootstrap(spec: NotebookSpec) -> str:
    """Render the executable cells; input identity is supplied by the first cell."""
    return _EXTRACT + "\n" + _runtime(spec) + "\n" + _pipeline(spec)


def _runtime(spec: NotebookSpec) -> str:
    return _RUNTIME.substitute(
        task=spec.task,
        requirements=spec.requirements,
        process=LIVE_PROCESS
        if spec.live_logs
        else "result = subprocess.run(argv, env=env, stdout=log, stderr=subprocess.STDOUT)",
    )


def _pipeline(spec: NotebookSpec) -> str:
    if spec.role == "model_cache":
        return _CACHE
    model = cfg.load()["models"]["generator"]
    model_glob = (
        "models--"
        + model["repo_id"].replace("/", "--")
        + "/snapshots/"
        + model["revision"]
        + "/config.json"
    )
    return _TRAIN.substitute(
        model_glob=repr(model_glob),
        script=spec.script,
        job_args=f"'--job', {spec.job!r}, " if spec.job is not None else "",
        artifact=f"{spec.task}-{spec.job}-artifacts.zip"
        if spec.job
        else f"{spec.task}-artifacts.zip",
    )


def notebook_source(notebook: dict) -> list[dict]:
    """Ignore execution output and Kaggle's injected metadata when comparing code."""
    return [
        {"cell_type": cell["cell_type"], "source": "".join(cell["source"])}
        for cell in notebook["cells"]
    ]


def _cell(kind: str, name: str, source: str) -> dict:
    cell = {"cell_type": kind, "id": name, "metadata": {}, "source": source}
    if kind == "code":
        compile(source, name, "exec")
        cell.update(execution_count=None, outputs=[])
    return cell


def build_notebook(
    archive: Path,
    output: Path,
    kernel: str,
    spec: NotebookSpec,
    *,
    cache_kernel: str | None = None,
    input_dataset: str | None = None,
) -> None:
    settings = load_settings()
    owner, title = kernel.split("/")
    if not owner or not title:
        raise ValueError("Kernel must be OWNER/SLUG")
    sources = (
        []
        if spec.role == "model_cache"
        else list(
            dict.fromkeys((cache_kernel or settings.cache_kernel, *spec.extra_kernel_sources))
        )
    )
    if kernel in sources:
        raise ValueError("A notebook must not overwrite one of its source kernels")
    with zipfile.ZipFile(archive) as bundle:
        candidates = [n for n in bundle.namelist() if n.endswith("inputs-manifest.json")]
        manifests = [json.loads(bundle.read(name)) for name in candidates]
        manifest = next(
            (m for m in manifests if spec.script in m.get("files", {})),
            manifests[0] if len(manifests) == 1 else {},
        )
        question_hash = (
            hashlib.sha256(bundle.read("data/dev_eval.jsonl")).hexdigest()
            if "data/dev_eval.jsonl" in bundle.namelist()
            else None
        )
    files = manifest.get("files", {})
    checksum = cfg.sha256_file(archive)
    provenance = {
        "code_commit": manifest.get("code_commit"),
        "source_sha256": json_digest(
            {k: v for k, v in files.items() if not k.startswith(("data/", "runs/"))}
        ),
        "data_sha256": json_digest(
            {
                **{k: v for k, v in files.items() if k.startswith(("data/", "runs/"))},
                "data/dev_eval.jsonl": question_hash,
            }
        ),
        "job": spec.job,
        "script": spec.script,
        "config": spec.job.split("-seed-")[0] if spec.job else None,
        "seed": int(spec.job.rsplit("-seed-", 1)[1]) if spec.job and "-seed-" in spec.job else None,
        "input_sha256": checksum,
        "working_tree_changes": bool(manifest.get("working_tree_changes")),
    }
    filename = f"{spec.name or spec.task}.ipynb"
    # A .bundle extension preserves the ZIP bytes when Kaggle ingests the dataset.
    input_file = f"inputs-{checksum}.bundle"
    dataset = input_dataset or settings.input_dataset
    configuration = (
        f"INPUT_FILE = {input_file!r}\nINPUT_SHA256 = {checksum!r}\n"
        f"PROVENANCE = {pformat(provenance, width=88)}\n"
    )
    overview = (
        f"# {title.replace('-', ' ').title()}\n\n"
        "Generated from local source. Edit src/ and scripts/, then run "
        "`eth-nl2sql kaggle build`; deploy this exact notebook.\n\n"
        f"- Kernel: `{kernel}`\n- Git commit: `{provenance['code_commit'] or 'unknown'}`\n"
        f"- Includes uncommitted source: `{provenance['working_tree_changes']}`\n"
        f"- Job / config / seed: `{spec.job or 'model cache'}` / "
        f"`{provenance['config']}` / `{provenance['seed']}`\n"
        f"- Entry point: `{spec.script}`\n- Input dataset: `{dataset}`\n"
        f"- Source SHA256: `{provenance['source_sha256']}`\n"
        f"- Data SHA256: `{provenance['data_sha256']}`\n"
        f"- Input ZIP SHA256: `{checksum}`\n\n"
        "Only questions and IDs from dev_eval are sent to Kaggle; evaluation stays local."
    )
    runtime, pipeline = _runtime(spec), _pipeline(spec)
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
            "language_info": {"name": "python"},
            "eth_nl2sql": provenance,
        },
        "cells": [
            _cell("markdown", "overview", overview),
            _cell("code", "input-identity", configuration),
            _cell("markdown", "verify-heading", "## Verify and unpack attached inputs"),
            _cell("code", "verify-inputs", _EXTRACT),
            _cell("markdown", "environment-heading", "## Install the locked environment"),
            _cell("code", "environment", runtime),
            _cell(
                "markdown",
                "run-heading",
                "## Build model cache"
                if spec.role == "model_cache"
                else "## Run the development experiment",
            ),
            _cell("code", "run-workflow", pipeline),
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / filename).write_text(json.dumps(notebook, indent=2) + "\n")
    metadata = {
        "id": kernel,
        "title": title,
        "code_file": filename,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": spec.role != "model_cache",
        "enable_internet": True,
        "enable_tpu": False,
        "machine_shape": "" if spec.role == "model_cache" else "NvidiaTeslaT4",
        "dataset_sources": [dataset],
        "kernel_sources": sources,
        "competition_sources": [],
        "model_sources": [],
    }
    cfg.write_json(output / "kernel-metadata.json", metadata)
    inputs = output / "inputs"
    inputs.mkdir(exist_ok=True)
    for previous in inputs.glob("inputs-*.bundle"):
        if previous.name != input_file:
            previous.unlink()
    shutil.copyfile(archive, inputs / input_file)
    cfg.write_json(
        inputs / "dataset-metadata.json",
        {
            "id": dataset,
            "title": dataset.split("/")[1].replace("-", " ").title(),
            "licenses": [{"name": "other"}],
        },
    )
    cfg.write_json(
        output / "deployment.json",
        {
            "provenance": provenance,
            "files": files,
            "input_file": input_file,
            "input_dataset": dataset,
            "input_bytes": archive.stat().st_size,
            "notebook_sha256": cfg.sha256_file(output / filename),
            "script_pattern": manifest.get("script_pattern"),
            "dev_eval_sha256": manifest.get("dev_eval_sha256"),
        },
    )
    print(json.dumps({"output": str(output), "notebook_bytes": (output / filename).stat().st_size}))

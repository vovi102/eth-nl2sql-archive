"""Parameterized, repeatable Kaggle notebook generation."""

from __future__ import annotations

import base64
import hashlib
import json
import zlib
from dataclasses import dataclass
from pathlib import Path
from string import Template

from eth_nl2sql import config as cfg
from eth_nl2sql.kaggle import load_settings

LIVE_PROCESS = """process = subprocess.Popen(argv, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in process.stdout:
            log.write(line)
            log.flush()
            print(line, end='', flush=True)
        result = subprocess.CompletedProcess(argv, process.wait())"""

_TEMPLATE = Template("""import base64, hashlib, io, json, os, subprocess, sys, tempfile, zipfile
from pathlib import Path

payload = base64.b64decode(PAYLOAD)
assert hashlib.sha256(payload).hexdigest() == BUNDLE_SHA256
${decode}root = Path('/kaggle/working/eth-nl2sql')
root.mkdir(exist_ok=False)
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    for name in z.namelist():
        if not (root / name).resolve().is_relative_to(root):
            raise ValueError('Invalid bundle path')
    z.extractall(root)
scratch = Path(tempfile.mkdtemp(prefix='$task-runtime-', dir='/tmp'))
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
run('install-locked-gpu', [uv, '--no-config', '--no-cache', 'pip', 'sync',
    '--python', python, '--require-hashes', '--index-url', 'https://pypi.org/simple',
    str(root / '$requirements')])
matches = list(Path('/kaggle/input').rglob($model_glob))
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


@dataclass(frozen=True)
class NotebookSpec:
    task: str
    script: str
    requirements: str
    job: str | None = None
    compressed: bool = False
    live_logs: bool = False


def render_bootstrap(spec: NotebookSpec) -> str:
    model = cfg.load()["models"]["generator"]
    model_glob = (
        "models--"
        + model["repo_id"].replace("/", "--")
        + "/snapshots/"
        + model["revision"]
        + "/config.json"
    )
    return _TEMPLATE.substitute(
        task=spec.task,
        script=spec.script,
        requirements=spec.requirements,
        decode="import zlib\npayload = zlib.decompress(payload)\n" if spec.compressed else "",
        process=LIVE_PROCESS
        if spec.live_logs
        else ("result = subprocess.run(argv, env=env, stdout=log, stderr=subprocess.STDOUT)"),
        model_glob=repr(model_glob),
        job_args=f"'--job', {spec.job!r}, " if spec.job is not None else "",
        artifact=(
            f"{spec.task}-{spec.job}-artifacts.zip" if spec.job else f"{spec.task}-artifacts.zip"
        ),
    )


def build_notebook(
    archive: Path,
    output: Path,
    kernel: str,
    spec: NotebookSpec,
    *,
    cache_kernel: str | None = None,
    bootstrap: str | None = None,
) -> None:
    data = archive.read_bytes()
    if spec.compressed:
        # Share repeated content across ZIP members to fit the source-size limit.
        data = zlib.compress(data, level=9)
    source = (
        f"PAYLOAD = {base64.b64encode(data).decode()!r}\n"
        f"BUNDLE_SHA256 = {hashlib.sha256(data).hexdigest()!r}\n"
        + (render_bootstrap(spec) if bootstrap is None else bootstrap)
    )
    if spec.compressed and len(source.encode()) >= 1_000_000:
        raise ValueError("Embedded notebook source exceeds Kaggle's 1 MB limit")
    filename = f"{spec.task}.ipynb"
    compile(source, filename, "exec")
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
            "language_info": {"name": "python"},
        },
        "cells": [
            {
                "cell_type": "code",
                "id": f"{spec.task}-gpu-pipeline",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": source,
            }
        ],
    }
    owner, title = kernel.split("/")
    if not owner or not title:
        raise ValueError("Kernel must be OWNER/SLUG")
    output.mkdir(parents=True, exist_ok=True)
    (output / filename).write_text(json.dumps(notebook))
    cfg.write_json(
        output / "kernel-metadata.json",
        {
            "id": kernel,
            "title": title,
            "code_file": filename,
            "language": "python",
            "kernel_type": "notebook",
            "is_private": True,
            "enable_gpu": True,
            "enable_internet": True,
            "enable_tpu": False,
            "machine_shape": "NvidiaTeslaT4",
            "dataset_sources": [],
            "kernel_sources": [cache_kernel or load_settings().cache_kernel],
            "competition_sources": [],
            "model_sources": [],
        },
    )
    print(json.dumps({"output": str(output), "notebook_bytes": (output / filename).stat().st_size}))

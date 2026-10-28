"""Build a private Kaggle notebook with an embedded, checksummed T11A input bundle."""

import argparse
import base64
import hashlib
import json
from pathlib import Path

BOOTSTRAP = '''import base64, hashlib, io, json, os, subprocess, sys, tempfile, zipfile
from pathlib import Path

payload = base64.b64decode(PAYLOAD)
assert hashlib.sha256(payload).hexdigest() == BUNDLE_SHA256
root = Path('/kaggle/working/eth-nl2sql')
root.mkdir(exist_ok=False)
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    for name in z.namelist():
        if not (root / name).resolve().is_relative_to(root):
            raise ValueError('Invalid bundle path')
    z.extractall(root)
scratch = Path(tempfile.mkdtemp(prefix='t11a-runtime-', dir='/tmp'))
log_root = Path('/kaggle/working/t11a-bootstrap')
log_root.mkdir()

def run(stage, argv, env=None):
    print('Starting:', stage, flush=True)
    with (log_root / (stage + '.log')).open('w') as log:
        result = subprocess.run(argv, env=env, stdout=log, stderr=subprocess.STDOUT)
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
    str(root / 'configs/t11-gpu-requirements.txt')])
matches = list(Path('/kaggle/input').rglob(
    'models--meta-llama--Meta-Llama-3-8B-Instruct/snapshots/'
    '8afb486c1db24fe5011ec46dfbe5b5dccdb575c2/config.json'))
if len(matches) != 1:
    raise ValueError('Expected one attached pinned model cache: ' + str(matches))
home = matches[0].parents[4]
env = dict(os.environ, PYTHONPATH=str(root / 'src'), OMP_NUM_THREADS='2',
    HF_HOME=str(home), HF_HUB_CACHE=str(home / 'hub'), HF_HUB_OFFLINE='1',
    TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
    HF_HUB_DISABLE_IMPLICIT_TOKEN='1', WANDB_DISABLED='true')
run('gpu-pipeline', [python, str(root / 'scripts/t11a.py'), 'gpu',
    '--hf-home', str(home)], env)
print('Copy t11a-artifacts.zip back intact for local development EX.', flush=True)
'''


def build(archive: Path, output: Path, kernel: str) -> None:
    data = archive.read_bytes()
    source = (
        f"PAYLOAD = {base64.b64encode(data).decode()!r}\n"
        f"BUNDLE_SHA256 = {hashlib.sha256(data).hexdigest()!r}\n" + BOOTSTRAP
    )
    output.mkdir(parents=True, exist_ok=True)
    notebook = {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
            "language_info": {"name": "python"},
        },
        "cells": [{"cell_type": "code", "id": "t11a-gpu-pipeline", "metadata": {},
                   "execution_count": None, "outputs": [], "source": source}],
    }
    (output / "t11a.ipynb").write_text(json.dumps(notebook))
    (output / "kernel-metadata.json").write_text(json.dumps({
        "id": kernel, "title": kernel.split("/")[1], "code_file": "t11a.ipynb",
        "language": "python", "kernel_type": "notebook", "is_private": True,
        "enable_gpu": True, "enable_internet": True, "enable_tpu": False,
        "machine_shape": "NvidiaTeslaT4", "dataset_sources": [],
        "kernel_sources": ["aohkvd/nl2sql-environment-cache"],
        "competition_sources": [], "model_sources": [],
    }, indent=2) + "\n")
    print(json.dumps({
        "output": str(output), "notebook_bytes": (output / "t11a.ipynb").stat().st_size,
    }))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path(".cache/t11a-inputs.zip"))
    parser.add_argument("--output", type=Path, default=Path(".cache/t11a-kaggle"))
    parser.add_argument("--kernel", default="aohkvd/eth-nl2sql-t11a-20261028")
    args = parser.parse_args()
    build(args.archive, args.output, args.kernel)

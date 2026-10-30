"""Build the private, pinned-runtime frozen-adapter diagnostic notebook."""

import argparse
import json
import tempfile
import zlib
from pathlib import Path

import t11a_notebook
from t11b_notebook import LIVE_PROCESS


def build(archive: Path, output: Path, kernel: str) -> None:
    original = t11a_notebook.BOOTSTRAP
    try:
        t11a_notebook.BOOTSTRAP = (
            original.replace("t11a", "t11b-diagnosis")
            .replace("configs/t11-gpu-requirements.txt", "configs/t11b-gpu-requirements.txt")
            .replace("scripts/t11b-diagnosis.py", "scripts/t11b_diagnose.py")
            .replace(
                "root = Path('/kaggle/working/eth-nl2sql')",
                "import zlib\npayload = zlib.decompress(payload)\n"
                "root = Path('/kaggle/working/eth-nl2sql')",
            )
            .replace(
                "result = subprocess.run(argv, env=env, stdout=log, stderr=subprocess.STDOUT)",
                LIVE_PROCESS,
            )
        )
        with tempfile.NamedTemporaryFile(suffix=".zlib") as payload:
            payload.write(zlib.compress(archive.read_bytes(), level=9))
            payload.flush()
            t11a_notebook.build(Path(payload.name), output, kernel)
    finally:
        t11a_notebook.BOOTSTRAP = original
    metadata = json.loads((output / "kernel-metadata.json").read_text())
    metadata["kernel_sources"].append("aohkvd/eth-nl2sql-t11b-b3-seed-42-20261028")
    (output / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    source = json.loads((output / "t11a.ipynb").read_text())["cells"][0]["source"]
    if len(source.encode()) >= 1_000_000:
        raise ValueError("Embedded notebook source exceeds Kaggle's 1 MB limit")
    compile(source, "t11b-diagnosis-notebook", "exec")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path(".cache/t11b-diagnosis-inputs.zip"))
    parser.add_argument("--output", type=Path, default=Path(".cache/t11b-diagnosis-notebook"))
    parser.add_argument("--kernel", default="aohkvd/eth-nl2sql-t11b-diagnosis-20261029")
    args = parser.parse_args()
    build(args.archive, args.output, args.kernel)

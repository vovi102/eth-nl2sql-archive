"""Build an isolated private Kaggle notebook for one T11B development job."""

import argparse
import json
import tempfile
import zlib
from pathlib import Path

import t11a_notebook

LIVE_PROCESS = """process = subprocess.Popen(argv, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in process.stdout:
            log.write(line)
            log.flush()
            print(line, end='', flush=True)
        result = subprocess.CompletedProcess(argv, process.wait())"""


def build(archive: Path, output: Path, kernel: str, job: str) -> None:
    t11a_notebook.BOOTSTRAP = (
        t11a_notebook.BOOTSTRAP.replace("t11a", "t11b")
        .replace("configs/t11-gpu-requirements.txt", "configs/t11b-gpu-requirements.txt")
        .replace(
            "root = Path('/kaggle/working/eth-nl2sql')",
            "import zlib\npayload = zlib.decompress(payload)\n"
            "root = Path('/kaggle/working/eth-nl2sql')",
        )
        .replace("'--hf-home', str(home)", f"'--job', {job!r}, '--hf-home', str(home)")
        .replace(
            "result = subprocess.run(argv, env=env, stdout=log, stderr=subprocess.STDOUT)",
            LIVE_PROCESS,
        )
    )
    # A second compression pass shares repeated content across ZIP members and
    # keeps embedded notebook source below Kaggle's 1 MiB source-size limit.
    with tempfile.NamedTemporaryFile(suffix=".zlib") as payload:
        payload.write(zlib.compress(archive.read_bytes(), level=9))
        payload.flush()
        t11a_notebook.build(Path(payload.name), output, kernel)
    source = json.loads((output / "t11a.ipynb").read_text())["cells"][0]["source"]
    if len(source.encode()) >= 1_000_000:
        raise ValueError("Embedded notebook source exceeds Kaggle's 1 MB limit")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path(".cache/t11b-inputs.zip"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--kernel", required=True)
    parser.add_argument("--job", required=True)
    args = parser.parse_args()
    build(args.archive, args.output, args.kernel, args.job)

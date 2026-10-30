"""Build an isolated private Kaggle notebook for one T11B development job."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eth_nl2sql.generation.runs import Job  # noqa: E402
from eth_nl2sql.gpu_notebook import (  # noqa: E402
    LIVE_PROCESS as LIVE_PROCESS,  # Compatibility for the separate diagnostic builder.
)
from eth_nl2sql.gpu_notebook import (  # noqa: E402
    NotebookSpec,
    build_notebook,
)
from eth_nl2sql.kaggle import load_settings  # noqa: E402


def build(
    archive: Path,
    output: Path,
    kernel: str,
    job: str,
    *,
    cache_kernel: str | None = None,
) -> None:
    selected = Job.parse(job)
    spec = NotebookSpec(
        "t11b",
        "scripts/t11b.py",
        "configs/t11b-gpu-requirements.txt",
        job=selected.identifier,
        compressed=True,
        live_logs=True,
    )
    build_notebook(archive, output, kernel, spec, cache_kernel=cache_kernel)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path(".cache/t11b-inputs.zip"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--kernel", required=True)
    parser.add_argument("--job", required=True)
    parser.add_argument("--cache-kernel", default=load_settings().cache_kernel)
    args = parser.parse_args()
    build(args.archive, args.output, args.kernel, args.job, cache_kernel=args.cache_kernel)

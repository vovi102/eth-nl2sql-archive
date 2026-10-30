"""Build a private Kaggle notebook with an embedded, checksummed T11A input bundle."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eth_nl2sql.gpu_notebook import (  # noqa: E402
    NotebookSpec,
    build_notebook,
    render_bootstrap,
)
from eth_nl2sql.kaggle import load_settings  # noqa: E402

SPEC = NotebookSpec("t11a", "scripts/t11a.py", "configs/t11-gpu-requirements.txt")
# Compatibility for the separate diagnostic builder; T11B uses its own explicit spec.
BOOTSTRAP = render_bootstrap(SPEC)


def build(archive: Path, output: Path, kernel: str, *, cache_kernel: str | None = None) -> None:
    build_notebook(archive, output, kernel, SPEC, cache_kernel=cache_kernel, bootstrap=BOOTSTRAP)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path(".cache/t11a-inputs.zip"))
    parser.add_argument("--output", type=Path, default=Path(".cache/t11a-kaggle"))
    parser.add_argument("--kernel", default=load_settings().kernel("t11a"))
    parser.add_argument("--cache-kernel", default=load_settings().cache_kernel)
    args = parser.parse_args()
    build(args.archive, args.output, args.kernel, cache_kernel=args.cache_kernel)

"""Build the private, pinned-runtime frozen-adapter diagnostic notebook."""

import argparse
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eth_nl2sql.gpu_notebook import NotebookSpec, build_notebook  # noqa: E402
from eth_nl2sql.kaggle import load_settings  # noqa: E402


def build(archive: Path, output: Path, kernel: str, *, cache_kernel: str | None = None) -> None:
    with zipfile.ZipFile(archive) as bundle:
        plan = json.loads(bundle.read("reports/experiments/diagnosis/plan.json"))
    if not plan.get("adapter_kernel"):
        raise ValueError("Rebuild the diagnostic bundle with an explicit adapter_kernel")
    adapter_kernel = plan["adapter_kernel"]
    spec = NotebookSpec(
        "t11b-diagnosis",
        "scripts/t11b_diagnose.py",
        "configs/t11b-gpu-requirements.txt",
        compressed=True,
        live_logs=True,
        extra_kernel_sources=(adapter_kernel,),
    )
    build_notebook(archive, output, kernel, spec, cache_kernel=cache_kernel)


if __name__ == "__main__":
    settings = load_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path(".cache/t11b-diagnosis-inputs.zip"))
    parser.add_argument("--output", type=Path, default=Path(".cache/t11b-diagnosis-notebook"))
    parser.add_argument("--kernel", default=settings.kernel())
    parser.add_argument("--cache-kernel", default=settings.cache_kernel)
    args = parser.parse_args()
    build(args.archive, args.output, args.kernel, cache_kernel=args.cache_kernel)

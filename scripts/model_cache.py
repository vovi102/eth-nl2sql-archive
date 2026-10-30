"""Acquire or verify the model cache using the shared cache workflow."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from eth_nl2sql.model_cache import main  # noqa: E402

if __name__ == "__main__":
    main()

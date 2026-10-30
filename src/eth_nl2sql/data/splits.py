"""Development data and the separately versioned final benchmark."""

from pathlib import Path

from eth_nl2sql import config as cfg
from eth_nl2sql.config import DATA_DIR, read_jsonl

DEVELOPMENT_SPLITS = ("train", "dev", "dev_eval")


def split_paths(data_dir: Path = DATA_DIR) -> dict[str, Path]:
    return {
        **{name: data_dir / f"{name}.jsonl" for name in DEVELOPMENT_SPLITS},
        "test": data_dir / "benchmark" / "v2" / "test.jsonl",
    }


def read_split(name: str, data_dir: Path = DATA_DIR) -> list[dict]:
    path = split_paths(data_dir)[name]
    if not path.is_file():
        raise ValueError(
            f"Split {name!r} is not authored yet: {path}; use dev_eval for development"
        )
    rows = read_jsonl(path)
    if not rows:
        raise ValueError(f"Split {name!r} is empty: {path}")
    return rows


def read_checked_split(name: str, dictionary: Path = cfg.DICTIONARY_DIR) -> list[dict]:
    """Enforce the final-benchmark release gate before reading a managed split."""
    if name == "test":
        from eth_nl2sql.data.benchmark import require_frozen

        require_frozen(split_paths(cfg.DATA_DIR)["test"].parent, cfg.DATA_DIR, dictionary)
    return read_split(name, cfg.DATA_DIR)

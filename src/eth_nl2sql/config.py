"""Repository paths and the experiment configuration."""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs" / "experiment.toml"
CATALOG_PATH = ROOT / "configs" / "catalog.json"
SYNONYMS_PATH = ROOT / "configs" / "schema_synonyms.json"
DATA_DIR = ROOT / "data"
STORE_PATH = DATA_DIR / "store" / "eth.duckdb"
PARQUET_DIR = DATA_DIR / "store" / "parquet"
DICTIONARY_DIR = DATA_DIR / "entities" / "v2"


def load(path: Path = CONFIG_PATH) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    )


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

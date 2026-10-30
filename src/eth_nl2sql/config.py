"""Repository paths and the experiment configuration."""

from __future__ import annotations

import tomllib
from pathlib import Path

# Compatibility for callers that predate artifacts.py.
from eth_nl2sql.artifacts import read_jsonl as read_jsonl
from eth_nl2sql.artifacts import sha256_file as sha256_file
from eth_nl2sql.artifacts import write_json as write_json
from eth_nl2sql.artifacts import write_jsonl as write_jsonl

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

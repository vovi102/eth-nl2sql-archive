"""Verify Parquet artifacts and retain the dataset scope inside DuckDB."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from pathlib import Path, PurePosixPath

import duckdb
import pyarrow.parquet as pq


def file_digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def verify_parquet(directory: Path) -> dict:
    from eth_nl2sql.store.build import RAW_SCHEMAS, SNAPSHOT_END, SNAPSHOT_START

    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("missing Parquet manifest; run prepare-local or snapshot-run first")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("version") != 1 or not isinstance(manifest.get("complete_snapshot"), bool):
        raise ValueError("invalid Parquet manifest version/scope")
    if manifest.get("window") != [SNAPSHOT_START.isoformat(), SNAPSHOT_END.isoformat()]:
        raise ValueError("Parquet manifest window differs from the managed store window")
    paths = set()
    tables = set()
    for record in manifest["files"]:
        relative = PurePosixPath(record["path"])
        table = record["table"]
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or len(relative.parts) != 2
            or table not in RAW_SCHEMAS
            or relative.parts[0] != table
            or relative.suffix != ".parquet"
            or relative.as_posix() in paths
        ):
            raise ValueError(f"invalid/duplicate Parquet manifest path: {relative}")
        paths.add(relative.as_posix())
        tables.add(table)
        path = directory / relative
        if not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError(f"Parquet path escapes its directory: {relative}")
        if path.stat().st_size != record["bytes"] or file_digest(path) != record["sha256"]:
            raise ValueError(f"Parquet size/checksum mismatch: {relative}")
        parquet = pq.ParquetFile(path)
        if parquet.metadata.num_rows != record["rows"]:
            raise ValueError(f"Parquet row count mismatch: {relative}")
        missing = set(RAW_SCHEMAS[table]) - set(parquet.schema_arrow.names)
        if missing:
            raise ValueError(f"Parquet missing columns for {table}: {sorted(missing)}")
    observed = {p.relative_to(directory).as_posix() for p in directory.rglob("*.parquet")}
    if observed != paths or tables != set(RAW_SCHEMAS):
        raise ValueError("Parquet files differ from manifest or a required table is missing")
    if manifest["complete_snapshot"]:
        days = [
            (SNAPSHOT_START + timedelta(days=i)).isoformat()
            for i in range((SNAPSHOT_END - SNAPSHOT_START).days)
        ]
        expected = {
            f"{table}/{day}.parquet"
            for table in ("transactions", "blocks", "token_transfers")
            for day in days
        }
        expected |= {"contracts/referenced.parquet", "amended_tokens/all.parquet"}
        if paths != expected:
            raise ValueError("full snapshot is missing expected daily partitions")
    return manifest


def store_profile(con: duckdb.DuckDBPyConnection) -> dict:
    try:
        row = con.execute("SELECT value FROM store_metadata WHERE key='profile'").fetchone()
    except duckdb.CatalogException:
        row = None
    return json.loads(row[0]) if row else {"scope": "unrecorded", "complete_snapshot": False}

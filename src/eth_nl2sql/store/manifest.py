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


def verify_record(directory: Path, record: dict) -> None:
    from eth_nl2sql.store.build import RAW_SCHEMAS

    relative = PurePosixPath(record["path"])
    table = record["table"]
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or len(relative.parts) != 2
        or table not in RAW_SCHEMAS
        or relative.parts[0] != table
        or relative.suffix != ".parquet"
    ):
        raise ValueError(f"invalid Parquet manifest path: {relative}")
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


def verify_parquet(directory: Path, *, manifest: dict | None = None) -> dict:
    from eth_nl2sql.store.build import RAW_SCHEMAS, SNAPSHOT_END, SNAPSHOT_START

    if manifest is None:
        manifest_path = directory / "manifest.json"
        if not manifest_path.is_file():
            raise ValueError("missing Parquet manifest; run prepare-local or snapshot-run first")
        manifest = json.loads(manifest_path.read_text())
    if manifest.get("version") not in (1, 2) or not isinstance(
        manifest.get("complete_snapshot"), bool
    ):
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
        verify_record(directory, record)
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
        from eth_nl2sql.store.snapshot import (
            FREE_MONTHLY_BYTES,
            MAX_BYTES_PER_QUERY,
            extraction_queries,
            query_digest,
        )

        if manifest.get("version") != 2 or manifest.get("scope") != "full_ethereum_window":
            raise ValueError("full snapshot requires version 2 job provenance")
        if (
            manifest.get("free_only") is not True
            or not manifest.get("project")
            or not manifest.get("location")
            or not 0 < manifest.get("budget_bytes", 0) <= FREE_MONTHLY_BYTES
        ):
            raise ValueError("full snapshot lacks a free-only policy or cumulative budget")
        jobs = manifest.get("jobs", {})
        queries = {f"{q.table}/{q.name}.parquet": q for q in extraction_queries()}
        if set(jobs) != expected:
            raise ValueError("full snapshot job journal differs from expected partitions")
        for record in manifest["files"]:
            key = record["path"]
            job = jobs[key]
            if (
                job.get("sql") != queries[key].sql
                or job.get("query_sha256") != query_digest(queries[key])
                or record.get("query_sha256") != query_digest(queries[key])
                or not job.get("job_id")
                or record.get("job_id") != job["job_id"]
                or job.get("state") != "done"
                or job.get("source_rows") != record["rows"]
                or record.get("project") != manifest.get("project")
                or record.get("location") != manifest.get("location")
                or job.get("project") != manifest.get("project")
                or job.get("location") != manifest.get("location")
                or record.get("bytes_billed") != job.get("bytes_billed")
                or not 0
                <= job.get("bytes_billed", -1)
                <= job["maximum_bytes_billed"]
                <= MAX_BYTES_PER_QUERY
            ):
                raise ValueError(f"invalid full snapshot job provenance: {key}")
        if sum(j["bytes_billed"] for j in jobs.values()) > manifest["budget_bytes"]:
            raise ValueError("full snapshot exceeds its cumulative budget")
    return manifest


def store_profile(con: duckdb.DuckDBPyConnection) -> dict:
    try:
        row = con.execute("SELECT value FROM store_metadata WHERE key='profile'").fetchone()
    except duckdb.CatalogException:
        row = None
    return json.loads(row[0]) if row else {"scope": "unrecorded", "complete_snapshot": False}

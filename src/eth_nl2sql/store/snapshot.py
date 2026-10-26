"""One-time extraction of the snapshot window from the BigQuery public dataset.

`plan()` dry-runs every extraction query (free) and reports the bytes that a
real run would scan. `run()` executes them and writes one Parquet file per
(table, day); existing files are skipped, so an interrupted run can simply be
restarted. Only the columns the catalog uses are read (`transactions.input` is
not), and `contracts` is limited to addresses that appear in the window.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from eth_nl2sql.store.build import RAW_SCHEMAS, SNAPSHOT_END, SNAPSHOT_START

PUBLIC = "bigquery-public-data.crypto_ethereum"
MAX_BYTES_PER_QUERY = 50 * 2**30  # luanvan catalog cost_policy.maximum_bytes_billed
TIME_COLUMN = {
    "transactions": "block_timestamp",
    "blocks": "timestamp",
    "token_transfers": "block_timestamp",
}


@dataclass(frozen=True)
class ExtractionQuery:
    table: str
    name: str  # output file stem
    sql: str


def _window(column: str, start: date, end: date) -> str:
    return f"{column} >= TIMESTAMP('{start}') AND {column} < TIMESTAMP('{end}')"


def _columns(table: str) -> str:
    return ", ".join(f"`{column}`" for column in RAW_SCHEMAS[table])


def extraction_queries(
    start: date = SNAPSHOT_START, end: date = SNAPSHOT_END
) -> list[ExtractionQuery]:
    queries = []
    day = start
    while day < end:
        following = day + timedelta(days=1)
        for table, column in TIME_COLUMN.items():
            queries.append(
                ExtractionQuery(
                    table,
                    day.isoformat(),
                    f"SELECT {_columns(table)} FROM `{PUBLIC}.{table}` "
                    f"WHERE {_window(column, day, following)}",
                )
            )
        day = following
    window_tx = _window("block_timestamp", start, end)
    sources = (
        ("token_address", "token_transfers"),
        ("from_address", "token_transfers"),
        ("to_address", "token_transfers"),
        ("to_address", "transactions"),
        ("receipt_contract_address", "transactions"),
    )
    referenced = "\nUNION DISTINCT ".join(
        f"SELECT LOWER({column}) AS address FROM `{PUBLIC}.{table}` WHERE {window_tx}"
        for column, table in sources
    )
    queries.append(
        ExtractionQuery(
            "contracts",
            "referenced",
            f"WITH referenced AS (\n{referenced}\n)\n"
            f"SELECT {_columns('contracts')} FROM `{PUBLIC}.contracts` "
            f"WHERE block_timestamp < TIMESTAMP('{end}') "
            f"AND LOWER(address) IN (SELECT address FROM referenced WHERE address IS NOT NULL)",
        )
    )
    queries.append(
        ExtractionQuery(
            "amended_tokens",
            "all",
            f"SELECT {_columns('amended_tokens')} FROM `{PUBLIC}.amended_tokens`",
        )
    )
    return queries


def _client(project: str):
    from google.cloud import bigquery

    return bigquery.Client(project=project)


def plan(project: str) -> dict:
    """Dry-run every extraction query; no bytes are billed."""
    from google.cloud import bigquery

    client = _client(project)
    config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    per_table: dict[str, int] = {}
    largest = 0
    for query in extraction_queries():
        job = client.query(query.sql, job_config=config)
        size = int(job.total_bytes_processed or 0)
        per_table[query.table] = per_table.get(query.table, 0) + size
        largest = max(largest, size)
    total = sum(per_table.values())
    return {
        "project": project,
        "window": [SNAPSHOT_START.isoformat(), SNAPSHOT_END.isoformat()],
        "queries": len(extraction_queries()),
        "bytes_by_table": per_table,
        "total_bytes": total,
        "total_gib": round(total / 2**30, 2),
        "largest_query_gib": round(largest / 2**30, 2),
    }


def run(project: str, out_dir: Path) -> dict:
    """Execute the extraction; skips files that already exist."""
    import pyarrow.parquet as pq
    from google.cloud import bigquery

    from eth_nl2sql.store.manifest import file_digest

    client = _client(project)
    config = bigquery.QueryJobConfig(maximum_bytes_billed=MAX_BYTES_PER_QUERY)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    window = [SNAPSHOT_START.isoformat(), SNAPSHOT_END.isoformat()]
    manifest = (
        json.loads(manifest_path.read_text())
        if manifest_path.exists()
        else {
            "version": 1,
            "scope": "full_ethereum_window",
            "window": window,
            "complete_snapshot": False,
            "files": [],
        }
    )
    if manifest.get("scope") != "full_ethereum_window" or manifest.get("window") != window:
        raise ValueError("existing Parquet directory belongs to a different data scope/window")
    recorded = {r["path"]: r for r in manifest["files"]}
    written, skipped, billed = 0, 0, 0
    for query in extraction_queries():
        target = out_dir / query.table / f"{query.name}.parquet"
        relative = f"{query.table}/{query.name}.parquet"
        query_hash = hashlib.sha256(query.sql.encode()).hexdigest()
        if target.exists():
            record = recorded.get(relative)
            if (
                not record
                or record.get("query_sha256") != query_hash
                or file_digest(target) != record["sha256"]
            ):
                raise ValueError(f"existing snapshot file lacks matching provenance: {target}")
            skipped += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        job = client.query(query.sql, job_config=config)
        table = job.result().to_arrow(create_bqstorage_client=True)
        partial = target.with_suffix(".parquet.partial")
        pq.write_table(table, partial)
        partial.rename(target)
        record = {
            "table": query.table,
            "path": relative,
            "rows": table.num_rows,
            "bytes": target.stat().st_size,
            "sha256": file_digest(target),
            "query_sha256": query_hash,
            "job_id": job.job_id,
        }
        recorded[relative] = record
        manifest["files"] = list(recorded.values())
        staged_manifest = manifest_path.with_suffix(".json.partial")
        staged_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
        staged_manifest.replace(manifest_path)
        billed += int(job.total_bytes_billed or 0)
        written += 1
        print(f"{query.table}/{query.name}: {table.num_rows} rows", flush=True)
    manifest["complete_snapshot"] = True
    staged_manifest = manifest_path.with_suffix(".json.partial")
    staged_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    staged_manifest.replace(manifest_path)
    return {"written": written, "skipped": skipped, "billed_gib": round(billed / 2**30, 2)}

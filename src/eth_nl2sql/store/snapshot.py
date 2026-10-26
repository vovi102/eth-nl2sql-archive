"""One-time extraction of the snapshot window from the BigQuery public dataset.

`plan()` dry-runs every extraction query (free) and reports the bytes that a
real run would scan. `run()` executes them and writes one Parquet file per
(table, day); existing files are skipped, so an interrupted run can simply be
restarted. Only the columns the catalog uses are read (`transactions.input` is
not), and `contracts` is limited to addresses that appear in the window.
"""

from __future__ import annotations

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
    return ", ".join(RAW_SCHEMAS[table])


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

    client = _client(project)
    config = bigquery.QueryJobConfig(maximum_bytes_billed=MAX_BYTES_PER_QUERY)
    written, skipped, billed = 0, 0, 0
    for query in extraction_queries():
        target = out_dir / query.table / f"{query.name}.parquet"
        if target.exists():
            skipped += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        job = client.query(query.sql, job_config=config)
        table = job.result().to_arrow(create_bqstorage_client=True)
        partial = target.with_suffix(".parquet.partial")
        pq.write_table(table, partial)
        partial.rename(target)
        billed += int(job.total_bytes_billed or 0)
        written += 1
        print(f"{query.table}/{query.name}: {table.num_rows} rows", flush=True)
    return {"written": written, "skipped": skipped, "billed_gib": round(billed / 2**30, 2)}

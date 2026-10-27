"""Offline integrity checks for a complete, provenance-verified Ethereum window."""

from datetime import UTC, datetime
from pathlib import Path

from eth_nl2sql.store.build import RAW_SCHEMAS, SNAPSHOT_END, SNAPSHOT_START, connect
from eth_nl2sql.store.manifest import file_digest, verify_parquet


def validate_snapshot(directory: Path) -> dict:
    manifest = verify_parquet(directory)
    if not manifest["complete_snapshot"]:
        raise ValueError("data validation requires a complete snapshot")
    checks = {}
    rows = {}
    with connect() as con:
        con.execute("SET memory_limit='2GB'")
        con.execute("SET threads=4")
        for table, schema in RAW_SCHEMAS.items():
            paths = [str(directory / r["path"]) for r in manifest["files"] if r["table"] == table]
            con.read_parquet(paths).create_view(table)
            rows[table] = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            checks[f"{table}_manifest_rows"] = rows[table] == sum(
                r["rows"] for r in manifest["files"] if r["table"] == table
            )
            expressions = [
                f'count(*) FILTER (WHERE "{col}" IS NOT NULL '
                f'AND TRY_CAST("{col}" AS {kind}) IS NULL)'
                for col, kind in schema.items()
            ]
            invalid = con.execute(f"SELECT {', '.join(expressions)} FROM {table}").fetchone()
            checks[f"{table}_types"] = not any(invalid)
        for record in manifest["files"]:
            table = record["table"]
            if table not in {"blocks", "transactions", "token_transfers"}:
                continue
            column = "timestamp" if table == "blocks" else "block_timestamp"
            day = Path(record["path"]).stem
            invalid = con.execute(
                f'SELECT count(*) FROM read_parquet(?) WHERE "{column}" IS NULL '
                f'OR CAST("{column}" AS DATE) != CAST(? AS DATE)',
                [str(directory / record["path"]), day],
            ).fetchone()[0]
            checks[f"partition:{record['path']}"] = invalid == 0
        for table, keys in {
            "transactions": ("hash",),
            "blocks": ("number",),
            "token_transfers": ("transaction_hash", "log_index"),
            "contracts": ("address", "block_timestamp", "block_number", "block_hash"),
            "amended_tokens": ("address",),
        }.items():
            columns = ", ".join(f'"{k}"' for k in keys)
            nulls = " OR ".join(f'"{k}" IS NULL' for k in keys)
            invalid = con.execute(
                f"SELECT count(*)-count(DISTINCT ({columns})), "
                f"count(*) FILTER (WHERE {nulls}) FROM {table}"
            ).fetchone()
            checks[f"{table}_keys"] = invalid == (0, 0)
        queries = {
            "transaction_block_join": """SELECT count(*) FROM transactions t LEFT JOIN blocks b
                ON t.block_number=b.number AND lower(t.block_hash)=lower(b.hash)
                AND t.block_timestamp=b.timestamp WHERE b.number IS NULL""",
            "transfer_transaction_join": """SELECT count(*) FROM token_transfers f
                LEFT JOIN transactions t ON lower(f.transaction_hash)=lower(t.hash)
                AND f.block_number=t.block_number AND lower(f.block_hash)=lower(t.block_hash)
                AND f.block_timestamp=t.block_timestamp WHERE t.hash IS NULL""",
            "block_transaction_counts": """SELECT count(*) FROM blocks b LEFT JOIN (
                SELECT block_number, count(*) AS n FROM transactions GROUP BY block_number
                ) t ON b.number=t.block_number WHERE b.transaction_count != coalesce(t.n, 0)""",
            "contracts_before_end": "SELECT count(*) FROM contracts "
            f"WHERE block_timestamp >= TIMESTAMPTZ '{SNAPSHOT_END}'",
        }
        violations = {name: con.execute(sql).fetchone()[0] for name, sql in queries.items()}
        checks.update({name: count == 0 for name, count in violations.items()})
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "passed": all(checks.values()),
        "complete_snapshot": True,
        "manifest_sha256": file_digest(directory / "manifest.json"),
        "window": [SNAPSHOT_START.isoformat(), SNAPSHOT_END.isoformat()],
        "partitions": len(manifest["files"]),
        "rows": rows,
        "checks": checks,
        "join_violations": violations,
    }

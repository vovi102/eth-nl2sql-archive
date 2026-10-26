"""Prepare the historical CSV subset without inventing missing measurements."""

from __future__ import annotations

import csv
import hashlib
import json
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb

from eth_nl2sql.data.audit import audit_import
from eth_nl2sql.store.build import RAW_SCHEMAS

CSV_TABLES = ("blocks", "transactions", "token_transfers", "contracts")
PUBLIC = "bigquery-public-data.crypto_ethereum"


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def quote(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


@contextmanager
def csv_connection(directory: Path):
    """Disk-backed, bounded-memory workspace; never modifies the imported CSVs."""
    with TemporaryDirectory(prefix="eth-nl2sql-local-") as temporary:
        con = duckdb.connect(
            str(Path(temporary) / "work.duckdb"),
            config={"threads": 2, "memory_limit": "768MB", "temp_directory": temporary},
        )
        try:
            con.execute("SET TimeZone='UTC'")
            con.execute("SET preserve_insertion_order=false")
            for table in CSV_TABLES:
                path = directory / f"{table}.csv"
                with path.open(newline="") as handle:
                    columns = next(csv.reader(handle))
                projection = ", ".join(
                    f"CAST({quote(c)} AS {RAW_SCHEMAS[table].get(c, 'VARCHAR')}) AS {quote(c)}"
                    for c in columns
                )
                con.execute(
                    f"CREATE TABLE raw_{table} AS SELECT {projection} FROM "
                    "read_csv(?, columns=?, header=true, auto_detect=false, strict_mode=true)",
                    [str(path), dict.fromkeys(columns, "VARCHAR")],
                )
            yield con
        finally:
            con.close()


def _join_checks(con: duckdb.DuckDBPyConnection) -> dict:
    joins = {}
    for column in ("number", "hash", "timestamp"):
        count = con.execute(
            f"SELECT COUNT(*) FROM (SELECT {quote(column)} FROM raw_blocks "
            f"GROUP BY {quote(column)} HAVING COUNT(*) > 1)"
        ).fetchone()[0]
        if count:
            raise ValueError(f"blocks.{column} is not unique; joins would multiply rows")
    queries = {
        "transactions_to_blocks": (
            "SELECT COUNT(*), COUNT(*) FILTER (WHERE b.number IS NULL), "
            "COUNT(*) FILTER (WHERE t.block_timestamp <> b.timestamp) "
            "FROM raw_transactions t LEFT JOIN raw_blocks b ON t.block_number=b.number"
        ),
        "transfers_to_transactions": (
            "SELECT COUNT(*), COUNT(*) FILTER (WHERE t.hash IS NULL), "
            "COUNT(*) FILTER (WHERE tt.block_timestamp <> t.block_timestamp) "
            "FROM raw_token_transfers tt LEFT JOIN raw_transactions t "
            "ON lower(tt.transaction_hash)=lower(t.hash)"
        ),
        "contracts_to_local_blocks": (
            "SELECT COUNT(*), COUNT(*) FILTER (WHERE b.number IS NULL), 0 "
            "FROM raw_contracts c LEFT JOIN raw_blocks b ON c.block_timestamp=b.timestamp"
        ),
    }
    for name, sql in queries.items():
        rows, missing, inconsistent = con.execute(sql).fetchone()
        joins[name] = {
            "rows": rows,
            "matched": rows - missing,
            "missing": missing,
            "timestamp_mismatches": inconsistent,
        }
    return joins


def _mapping() -> dict:
    return {
        "transactions.block_hash": "blocks.hash joined by block_number",
        "token_transfers.block_number": "transactions.block_number joined by transaction_hash",
        "token_transfers.block_hash": "transactions -> blocks.hash",
        "contracts.block_number/block_hash": (
            "local block timestamp where present; supplement for historical blocks"
        ),
        "transactions.transaction_index/receipt_gas_used/receipt_contract_address": (
            "BigQuery transactions supplement"
        ),
        "blocks.base_fee_per_gas": "BigQuery blocks supplement",
        "amended_tokens": "BigQuery amended_tokens supplement",
    }


def plan_local(directory: Path) -> dict:
    audit = audit_import(directory)
    if not audit["passed"]:
        raise ValueError("CSV audit failed; run check-data and inspect its report")
    with csv_connection(directory) as con:
        joins = _join_checks(con)
        token_count = con.execute(
            "SELECT COUNT(DISTINCT lower(token_address)) FROM raw_token_transfers"
        ).fetchone()[0]
    invalid = any(
        value["missing"] or value["timestamp_mismatches"]
        for name, value in joins.items()
        if name != "contracts_to_local_blocks"
    )
    return {
        "version": 1,
        "scope": audit["scope"],
        "complete_snapshot": False,
        "source_manifest_sha256": audit["import_manifest_sha256"],
        "source_files": audit["files"],
        "joins_ok": not invalid,
        "joins": joins,
        "distinct_transfer_token_addresses": token_count,
        "mapping": _mapping(),
        "supplements_required": ["transactions", "blocks", "contracts", "amended_tokens"],
    }


def supplement_queries(directory: Path) -> list[tuple[str, str, dict]]:
    """Reproduce the historical selection and request only its missing attributes."""
    source = json.loads((directory / "manifest.json").read_text())
    period = source["data_period"]
    start = period["start"]
    end = (date.fromisoformat(period["end"]) + timedelta(days=1)).isoformat()
    with (directory / "entities.csv").open(newline="") as handle:
        labeled = sorted({row["address"].lower() for row in csv.DictReader(handle)})
    with duckdb.connect(config={"threads": 2, "memory_limit": "512MB"}) as con:
        tokens = [
            row[0]
            for row in con.execute(
                "SELECT DISTINCT lower(token_address) FROM read_csv(?, all_varchar=true) "
                "WHERE token_address IS NOT NULL",
                [str(directory / "token_transfers.csv")],
            ).fetchall()
        ]
    with (directory / "contracts.csv").open(newline="") as handle:
        contracts = {row["address"].lower() for row in csv.DictReader(handle)}
    addresses = sorted(contracts | set(tokens))
    window = f"block_timestamp >= TIMESTAMP('{start}') AND block_timestamp < TIMESTAMP('{end}')"
    return [
        (
            "transactions",
            f"SELECT `hash`, block_number, block_timestamp, block_hash, transaction_index, "
            f"receipt_gas_used, receipt_contract_address FROM `{PUBLIC}.transactions` "
            f"WHERE {window} "
            "AND (lower(from_address) IN UNNEST(@labeled) OR lower(to_address) IN UNNEST(@labeled) "
            "OR MOD(ABS(FARM_FINGERPRINT(`hash`)), 100) = 0)",
            {"labeled": labeled},
        ),
        (
            "blocks",
            f"SELECT number, `hash`, base_fee_per_gas FROM `{PUBLIC}.blocks` "
            f"WHERE timestamp >= TIMESTAMP('{start}') AND timestamp < TIMESTAMP('{end}')",
            {},
        ),
        (
            "contracts",
            f"SELECT address, is_erc20, is_erc721, block_timestamp, block_number, block_hash "
            f"FROM `{PUBLIC}.contracts` WHERE block_timestamp < TIMESTAMP('{end}') "
            "AND lower(address) IN UNNEST(@addresses)",
            {"addresses": addresses},
        ),
        (
            "amended_tokens",
            f"SELECT address, symbol, name, decimals FROM `{PUBLIC}.amended_tokens`",
            {},
        ),
    ]


SUPPLEMENT_SCHEMAS = {
    "transactions": {
        key: RAW_SCHEMAS["transactions"][key]
        for key in (
            "hash",
            "block_number",
            "block_timestamp",
            "block_hash",
            "transaction_index",
            "receipt_gas_used",
            "receipt_contract_address",
        )
    },
    "blocks": {key: RAW_SCHEMAS["blocks"][key] for key in ("number", "hash", "base_fee_per_gas")},
    "contracts": RAW_SCHEMAS["contracts"],
    "amended_tokens": RAW_SCHEMAS["amended_tokens"],
}


def _load_supplements(con, directory: Path, source_hash: str) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest.get("source_manifest_sha256") != source_hash:
        raise ValueError("supplements belong to a different CSV import")
    for table, schema in SUPPLEMENT_SCHEMAS.items():
        record = manifest.get("files", {}).get(table)
        if not record or record.get("path") != f"{table}.parquet":
            raise ValueError(f"missing or invalid supplement manifest entry: {table}")
        path = directory / record["path"]
        if digest(path) != record["sha256"]:
            raise ValueError(f"supplement checksum mismatch: {table}")
        projection = ", ".join(
            f"CAST({quote(c)} AS {kind}) AS {quote(c)}" for c, kind in schema.items()
        )
        con.execute(
            f"CREATE TABLE supplement_{table} AS SELECT {projection} FROM read_parquet(?)",
            [str(path)],
        )
        count = con.execute(f"SELECT COUNT(*) FROM supplement_{table}").fetchone()[0]
        if count != record["rows"] or count == 0:
            raise ValueError(f"supplement row count mismatch or empty table: {table}")
        keys = {
            "transactions": ("hash",),
            "blocks": ("number",),
            "contracts": ("address", "block_timestamp"),
            "amended_tokens": ("address",),
        }[table]
        key_columns = ", ".join(
            f"lower({quote(c)})" if schema[c] == "VARCHAR" else quote(c) for c in keys
        )
        invalid = con.execute(
            f"SELECT COUNT(*) FROM (SELECT {key_columns} FROM supplement_{table} "
            f"GROUP BY {key_columns} HAVING COUNT(*) > 1)"
        ).fetchone()[0]
        nulls = " OR ".join(f"{quote(c)} IS NULL" for c in keys)
        if (
            invalid
            or con.execute(f"SELECT COUNT(*) FROM supplement_{table} WHERE {nulls}").fetchone()[0]
        ):
            raise ValueError(f"supplement has duplicate/missing keys: {table}")
    return manifest


def _enrich(con: duckdb.DuckDBPyConnection) -> dict:
    """Require measured matches, preserving the historical contract flags."""
    checks = {
        "transactions": (
            "SELECT COUNT(*) FROM raw_transactions t JOIN raw_blocks b ON t.block_number=b.number "
            "LEFT JOIN supplement_transactions s ON lower(t.hash)=lower(s.hash) "
            "WHERE s.hash IS NULL OR s.block_number IS DISTINCT FROM t.block_number "
            "OR s.block_timestamp IS DISTINCT FROM t.block_timestamp "
            "OR lower(s.block_hash) IS DISTINCT FROM lower(b.hash)"
        ),
        "blocks": (
            "SELECT COUNT(*) FROM raw_blocks b LEFT JOIN supplement_blocks s ON b.number=s.number "
            "WHERE s.number IS NULL OR lower(s.hash) IS DISTINCT FROM lower(b.hash)"
        ),
        "contracts": (
            "SELECT COUNT(*) FROM raw_contracts c LEFT JOIN supplement_contracts s "
            "ON lower(c.address)=lower(s.address) AND c.block_timestamp=s.block_timestamp "
            "WHERE s.address IS NULL"
        ),
    }
    for table, sql in checks.items():
        if con.execute(sql).fetchone()[0]:
            raise ValueError(f"supplement has missing or inconsistent historical rows: {table}")
    tx_columns = ", ".join(
        (
            "lower(b.hash) AS block_hash"
            if c == "block_hash"
            else f"s.{quote(c)}"
            if c in {"transaction_index", "receipt_gas_used", "receipt_contract_address"}
            else f"t.{quote(c)}"
        )
        for c in RAW_SCHEMAS["transactions"]
    )
    con.execute(
        f"CREATE TABLE prepared_transactions AS SELECT {tx_columns} FROM raw_transactions t "
        "JOIN raw_blocks b ON t.block_number=b.number "
        "JOIN supplement_transactions s ON lower(t.hash)=lower(s.hash)"
    )
    block_columns = ", ".join(
        f"{'s' if c == 'base_fee_per_gas' else 'b'}.{quote(c)}" for c in RAW_SCHEMAS["blocks"]
    )
    con.execute(
        f"CREATE TABLE prepared_blocks AS SELECT {block_columns} FROM raw_blocks b "
        "JOIN supplement_blocks s ON b.number=s.number"
    )
    transfer_columns = ", ".join(
        f"{'t' if c in {'block_number', 'block_hash'} else 'tt'}.{quote(c)}"
        for c in RAW_SCHEMAS["token_transfers"]
    )
    con.execute(
        f"CREATE TABLE prepared_token_transfers AS SELECT {transfer_columns} "
        "FROM raw_token_transfers tt JOIN prepared_transactions t "
        "ON lower(tt.transaction_hash)=lower(t.hash)"
    )
    flag_changes = con.execute(
        "SELECT COUNT(*) FROM raw_contracts c JOIN supplement_contracts s "
        "ON lower(c.address)=lower(s.address) AND c.block_timestamp=s.block_timestamp "
        "WHERE c.is_erc20 IS DISTINCT FROM s.is_erc20 OR c.is_erc721 IS DISTINCT FROM s.is_erc721"
    ).fetchone()[0]
    con.execute(
        "CREATE TABLE prepared_contracts AS SELECT s.address, "
        "CASE WHEN c.address IS NOT NULL THEN c.is_erc20 ELSE s.is_erc20 END AS is_erc20, "
        "CASE WHEN c.address IS NOT NULL THEN c.is_erc721 ELSE s.is_erc721 END AS is_erc721, "
        "s.block_timestamp, s.block_number, s.block_hash FROM supplement_contracts s "
        "LEFT JOIN raw_contracts c ON lower(c.address)=lower(s.address) "
        "AND c.block_timestamp=s.block_timestamp"
    )
    con.execute("CREATE TABLE prepared_amended_tokens AS SELECT * FROM supplement_amended_tokens")
    for table in ("transactions", "blocks", "token_transfers"):
        difference = con.execute(
            f"SELECT (SELECT COUNT(*) FROM raw_{table})-(SELECT COUNT(*) FROM prepared_{table})"
        ).fetchone()[0]
        if difference:
            raise ValueError(f"enrichment changed source row count: {table}")
    return {"historical_contract_flag_changes_preserved": flag_changes}


def prepare_local(directory: Path, parquet_dir: Path, supplements: Path, *, progress=print) -> dict:
    """Export complete typed schemas for the sampled store, atomically."""
    if parquet_dir.exists():
        raise ValueError(f"output already exists; choose a new parquet directory: {parquet_dir}")
    audit = audit_import(directory, progress=progress)
    if not audit["passed"]:
        raise ValueError("CSV audit failed; inspect check-data before preparing data")
    source_hash = audit["import_manifest_sha256"]
    period = audit["expected_period_inclusive"]
    manifest = {
        "version": 1,
        "scope": audit["scope"],
        "complete_snapshot": False,
        "window": [
            period["start"],
            (date.fromisoformat(period["end"]) + timedelta(days=1)).isoformat(),
        ],
        "source_import_manifest_sha256": source_hash,
        "source_files": audit["files"],
        "mapping": _mapping(),
        "files": [],
    }
    parquet_dir.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".prepare-local-", dir=parquet_dir.parent) as temporary:
        staging = Path(temporary)
        with csv_connection(directory) as con:
            progress("Checking joins and supplement provenance")
            manifest["joins"] = _join_checks(con)
            if any(
                v["missing"] or v["timestamp_mismatches"]
                for k, v in manifest["joins"].items()
                if k != "contracts_to_local_blocks"
            ):
                raise ValueError("local joins have unmatched or inconsistent rows")
            manifest["supplements"] = _load_supplements(con, supplements, source_hash)
            manifest["enrichment"] = _enrich(con)
            for table in RAW_SCHEMAS:
                progress(f"Exporting {table} to Parquet")
                target = staging / table / "data.parquet"
                target.parent.mkdir()
                con.execute(
                    f"COPY (SELECT * FROM prepared_{table}) TO ? "
                    "(FORMAT PARQUET, COMPRESSION ZSTD)",
                    [str(target)],
                )
                count = con.execute(f"SELECT COUNT(*) FROM prepared_{table}").fetchone()[0]
                manifest["files"].append(
                    {
                        "table": table,
                        "path": f"{table}/data.parquet",
                        "rows": count,
                        "sha256": digest(target),
                        "bytes": target.stat().st_size,
                    }
                )
        (staging / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        staging.replace(parquet_dir)
    return manifest

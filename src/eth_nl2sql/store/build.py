"""Build the local DuckDB replica of luanvan's managed BigQuery label layer.

Raw tables mirror the BigQuery public `crypto_ethereum` columns the catalog uses.
The eight managed objects are ported from luanvan `sql/label_layer.py`: two
views and six table macros that take the same date parameters as the BigQuery
table functions. Date-window bounds are checked statically by `execute.py`.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import duckdb

SNAPSHOT_START = date(2026, 5, 31)
SNAPSHOT_END = date(2026, 7, 1)  # exclusive
MAX_WINDOW_DAYS = 31

RAW_SCHEMAS = {
    "transactions": {
        "hash": "VARCHAR",
        "transaction_index": "BIGINT",
        "from_address": "VARCHAR",
        "to_address": "VARCHAR",
        "value": "DECIMAL(38,9)",
        "gas": "BIGINT",
        "gas_price": "BIGINT",
        "receipt_gas_used": "BIGINT",
        "receipt_contract_address": "VARCHAR",
        "receipt_status": "BIGINT",
        "block_timestamp": "TIMESTAMPTZ",
        "block_number": "BIGINT",
        "block_hash": "VARCHAR",
        "transaction_type": "BIGINT",
    },
    "blocks": {
        "timestamp": "TIMESTAMPTZ",
        "number": "BIGINT",
        "hash": "VARCHAR",
        "miner": "VARCHAR",
        "gas_used": "BIGINT",
        "transaction_count": "BIGINT",
        "base_fee_per_gas": "BIGINT",
    },
    "token_transfers": {
        "token_address": "VARCHAR",
        "from_address": "VARCHAR",
        "to_address": "VARCHAR",
        "value": "VARCHAR",
        "transaction_hash": "VARCHAR",
        "log_index": "BIGINT",
        "block_timestamp": "TIMESTAMPTZ",
        "block_number": "BIGINT",
        "block_hash": "VARCHAR",
    },
    "contracts": {
        "address": "VARCHAR",
        "is_erc20": "BOOLEAN",
        "is_erc721": "BOOLEAN",
        "block_timestamp": "TIMESTAMPTZ",
        "block_number": "BIGINT",
        "block_hash": "VARCHAR",
    },
    "amended_tokens": {
        "address": "VARCHAR",
        "symbol": "VARCHAR",
        "name": "VARCHAR",
        "decimals": "VARCHAR",
    },
}

LABEL_SCHEMA = {
    "address": "VARCHAR",
    "chain_id": "BIGINT",
    "primary_label": "VARCHAR",
    "owner": "VARCHAR",
    "category": "VARCHAR",
    "concept_class": "VARCHAR",
    "address_role": "VARCHAR",
    "aliases": "VARCHAR[]",
    "confidence": "VARCHAR",
    "verified_date": "DATE",
    "sources": (
        "STRUCT(name VARCHAR, url VARCHAR, revision VARCHAR, locator VARCHAR, "
        "retrieved_date DATE, note VARCHAR)[]"
    ),
    "dictionary_sha256": "VARCHAR",
}

_LABEL_COLUMNS = (
    "primary_label",
    "owner",
    "category",
    "concept_class",
    "address_role",
    "confidence",
)

_TRANSACTION_FIELDS = (
    "transaction_hash",
    "transaction_index",
    "block_timestamp",
    "block_number",
    "block_hash",
    "from_address",
    "to_address",
    "value_wei",
    "gas_limit",
    "gas_price_wei",
    "receipt_gas_used",
    "receipt_status",
    "is_success",
    "receipt_contract_address",
    "transaction_type",
)

_TRANSFER_FIELDS = (
    "transaction_hash",
    "log_index",
    "block_timestamp",
    "block_number",
    "block_hash",
    "token_address",
    "from_address",
    "to_address",
    "value_raw",
    "value_bignumeric",
    "value_cast_valid",
    "is_erc20",
    "is_erc721",
    "token_symbol",
    "token_name",
    "token_decimals",
    "normalized_amount",
)


def _labeled(facts: str, fields: tuple[str, ...], prefixes: tuple[str, ...]) -> str:
    projection = [f"facts.{name} AS {name}" for name in fields]
    joins = []
    for prefix in prefixes:
        alias = f"{prefix}_label"
        projection += [f"{alias}.{name} AS {prefix}_{name}" for name in _LABEL_COLUMNS]
        joins.append(
            f"LEFT JOIN entity_labels_v1 AS {alias} ON facts.{prefix}_address = {alias}.address"
        )
    return (
        f"SELECT {', '.join(projection)} "
        f"FROM {facts}(start_date, end_date) AS facts {' '.join(joins)}"
    )


MANAGED_DDL = (
    """CREATE OR REPLACE VIEW entity_labels_v1 AS
SELECT address, chain_id, primary_label, owner, category, concept_class, address_role,
       aliases, confidence, verified_date, sources, dictionary_sha256
FROM entity_labels_snapshot""",
    """CREATE OR REPLACE VIEW token_dimension AS
SELECT lower(tok.address) AS address, tok.symbol AS symbol, tok.name AS name,
       TRY_CAST(tok.decimals AS BIGINT) AS decimals
FROM amended_tokens AS tok""",
    """CREATE OR REPLACE MACRO transaction_facts(start_date, end_date) AS TABLE
SELECT lower(t.hash) AS transaction_hash, t.transaction_index AS transaction_index,
       t.block_timestamp AS block_timestamp, t.block_number AS block_number,
       lower(t.block_hash) AS block_hash, lower(t.from_address) AS from_address,
       lower(t.to_address) AS to_address, t.value AS value_wei, t.gas AS gas_limit,
       t.gas_price AS gas_price_wei, t.receipt_gas_used AS receipt_gas_used,
       t.receipt_status AS receipt_status, t.receipt_status = 1 AS is_success,
       lower(t.receipt_contract_address) AS receipt_contract_address,
       t.transaction_type AS transaction_type
FROM transactions AS t
WHERE t.block_timestamp >= CAST(start_date AS TIMESTAMPTZ)
  AND t.block_timestamp < CAST(end_date AS TIMESTAMPTZ)""",
    """CREATE OR REPLACE MACRO block_facts(start_date, end_date) AS TABLE
SELECT b.number AS block_number, lower(b.hash) AS block_hash, b.timestamp AS block_timestamp,
       lower(b.miner) AS beneficiary_address, b.gas_used AS gas_used,
       b.transaction_count AS transaction_count, b.base_fee_per_gas AS base_fee_per_gas_wei
FROM blocks AS b
WHERE b.timestamp >= CAST(start_date AS TIMESTAMPTZ)
  AND b.timestamp < CAST(end_date AS TIMESTAMPTZ)""",
    """CREATE OR REPLACE MACRO contract_dimension(end_date) AS TABLE
SELECT lower(c.address) AS address, c.is_erc20 AS is_erc20, c.is_erc721 AS is_erc721,
       c.block_timestamp AS created_at, c.block_number AS block_number,
       lower(c.block_hash) AS block_hash
FROM contracts AS c
WHERE c.block_timestamp < CAST(end_date AS TIMESTAMPTZ)
QUALIFY row_number() OVER (
  PARTITION BY lower(c.address)
  ORDER BY c.block_timestamp DESC, c.block_number DESC, c.block_hash DESC
) = 1""",
    # BIGNUMERIC has no exact DuckDB equivalent: raw values use HUGEINT and the
    # decimal-normalized amount uses DOUBLE (see METHODOLOGY, parity limits).
    """CREATE OR REPLACE MACRO token_transfer_facts(start_date, end_date) AS TABLE
SELECT lower(tt.transaction_hash) AS transaction_hash, tt.log_index AS log_index,
       tt.block_timestamp AS block_timestamp, tt.block_number AS block_number,
       lower(tt.block_hash) AS block_hash, lower(tt.token_address) AS token_address,
       lower(tt.from_address) AS from_address, lower(tt.to_address) AS to_address,
       tt.value AS value_raw, TRY_CAST(tt.value AS HUGEINT) AS value_bignumeric,
       tt.value IS NOT NULL AND TRY_CAST(tt.value AS HUGEINT) IS NOT NULL AS value_cast_valid,
       c.is_erc20 AS is_erc20, c.is_erc721 AS is_erc721,
       tok.symbol AS token_symbol, tok.name AS token_name, tok.decimals AS token_decimals,
       CASE
         WHEN c.is_erc20 IS TRUE
           AND COALESCE(c.is_erc721, FALSE) IS FALSE
           AND tok.decimals BETWEEN 0 AND 38
         THEN TRY_CAST(tt.value AS DOUBLE) / power(10, tok.decimals)
       END AS normalized_amount
FROM token_transfers AS tt
LEFT JOIN contract_dimension(end_date) AS c ON lower(tt.token_address) = c.address
LEFT JOIN token_dimension AS tok ON lower(tt.token_address) = tok.address
WHERE tt.block_timestamp >= CAST(start_date AS TIMESTAMPTZ)
  AND tt.block_timestamp < CAST(end_date AS TIMESTAMPTZ)""",
    "CREATE OR REPLACE MACRO labeled_transactions(start_date, end_date) AS TABLE "
    + _labeled("transaction_facts", _TRANSACTION_FIELDS, ("from", "to")),
    "CREATE OR REPLACE MACRO labeled_token_transfers(start_date, end_date) AS TABLE "
    + _labeled("token_transfer_facts", _TRANSFER_FIELDS, ("from", "to", "token")),
)


def connect(path: Path | str | None = None, *, read_only: bool = True) -> duckdb.DuckDBPyConnection:
    """Open the store with UTC session time, which the date macros rely on."""
    if path is None:
        con = duckdb.connect(":memory:")
    else:
        con = duckdb.connect(str(path), read_only=read_only)
    con.execute("SET TimeZone = 'UTC'")
    return con


def _columns_ddl(schema: dict[str, str]) -> str:
    return ", ".join(f'"{name}" {sql_type}' for name, sql_type in schema.items())


def create_schema(con: duckdb.DuckDBPyConnection) -> None:
    """Create empty raw tables, the label table and all managed objects."""
    for table, schema in RAW_SCHEMAS.items():
        con.execute(f"CREATE TABLE IF NOT EXISTS {table} ({_columns_ddl(schema)})")
    con.execute(f"CREATE TABLE IF NOT EXISTS entity_labels_snapshot ({_columns_ddl(LABEL_SCHEMA)})")
    for ddl in MANAGED_DDL:
        con.execute(ddl)


def load_parquet(con: duckdb.DuckDBPyConnection, parquet_dir: Path) -> dict[str, int]:
    """Load `<parquet_dir>/<table>/*.parquet` into the raw tables with exact column types."""
    counts = {}
    for table, schema in RAW_SCHEMAS.items():
        files = sorted((parquet_dir / table).glob("*.parquet"))
        if not files:
            raise FileNotFoundError(f"no parquet files for {table} under {parquet_dir}")
        columns = ", ".join(f'CAST("{name}" AS {kind})' for name, kind in schema.items())
        file_list = ", ".join(f"'{file.as_posix()}'" for file in files)
        con.execute(f"DELETE FROM {table}")
        con.execute(f"INSERT INTO {table} SELECT {columns} FROM read_parquet([{file_list}])")
        counts[table] = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return counts


def label_rows(entities_path: Path) -> list[tuple]:
    """Build one label row per address exactly as luanvan's BigQuery snapshot did."""
    payload = entities_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    rows = []
    seen = set()
    for entry in json.loads(payload):
        address = entry["address"].lower()
        if address in seen:
            raise ValueError(f"duplicate label address {address}")
        seen.add(address)
        rows.append(
            (
                address,
                entry["chain_id"],
                entry["primary_label"],
                entry["owner"],
                entry["category"],
                entry["concept_class"],
                entry["address_role"],
                list(entry["aliases"]),
                entry["confidence"],
                date.fromisoformat(entry["verified_date"]),
                [
                    {
                        "name": source["name"],
                        "url": source["url"],
                        "revision": source["revision"],
                        "locator": source["locator"],
                        "retrieved_date": date.fromisoformat(source["retrieved_date"]),
                        "note": source["note"],
                    }
                    for source in entry["sources"]
                ],
                digest,
            )
        )
    return rows


def load_labels(con: duckdb.DuckDBPyConnection, entities_path: Path) -> int:
    rows = label_rows(entities_path)
    con.execute("DELETE FROM entity_labels_snapshot")
    placeholders = ", ".join("?" for _ in LABEL_SCHEMA)
    con.executemany(f"INSERT INTO entity_labels_snapshot VALUES ({placeholders})", rows)
    return len(rows)


def build_store(store_path: Path, parquet_dir: Path, entities_path: Path) -> dict[str, int]:
    """Create or refresh the DuckDB store from snapshot parquet files and a label dictionary."""
    store_path.parent.mkdir(parents=True, exist_ok=True)
    con = connect(store_path, read_only=False)
    try:
        create_schema(con)
        counts = load_parquet(con, parquet_dir)
        counts["entity_labels_snapshot"] = load_labels(con, entities_path)
        con.execute("CHECKPOINT")
        return counts
    finally:
        con.close()

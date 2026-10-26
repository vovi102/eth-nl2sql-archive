"""End-to-end CSV enrichment, Parquet integrity and sampled-store behavior."""

import csv
import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from conftest import BINANCE, ETH, MINI_DICTIONARY, TETHER, USER

from eth_nl2sql.data.audit import IMPORT_FILES
from eth_nl2sql.store.build import build_store, connect
from eth_nl2sql.store.execute import execute
from eth_nl2sql.store.local import digest, plan_local, prepare_local, supplement_queries
from eth_nl2sql.store.manifest import store_profile, verify_parquet
from eth_nl2sql.store.parity import check

P = "nl2sparql-thesis.nl2sparql_analytics"


def _csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _supplement(directory, name, rows, manifest):
    path = directory / f"{name}.parquet"
    pq.write_table(pa.Table.from_pylist(rows), path)
    manifest["files"][name] = {"path": path.name, "sha256": digest(path), "rows": len(rows)}
    (directory / "manifest.json").write_text(json.dumps(manifest))


@pytest.fixture()
def local_source(tmp_path):
    source, supplements = tmp_path / "csv", tmp_path / "supplements"
    source.mkdir()
    supplements.mkdir()
    blocks = [
        {
            "number": day * 100,
            "hash": f"b{day}",
            "timestamp": f"2026-06-0{day}T12:00:00+00:00",
            "miner": USER,
            "gas_used": day * 1000,
            "gas_limit": 10000,
            "transaction_count": 1,
        }
        for day in (1, 2)
    ]
    transactions = [
        {
            "hash": f"tx{day}",
            "from_address": USER,
            "to_address": BINANCE[day - 1],
            "value": str(ETH + day),
            "gas": 90000,
            "gas_price": 10,
            "block_number": day * 100,
            "block_timestamp": block["timestamp"],
            "transaction_type": 2,
            "receipt_status": 1,
            "tier": "tier1",
        }
        for day, block in enumerate(blocks, 1)
    ]
    contracts = [
        {
            "address": TETHER,
            "is_erc20": True,
            "is_erc721": False,
            "block_timestamp": "2017-01-01T00:00:00+00:00",
        },
        {
            "address": BINANCE[2],
            "is_erc20": False,
            "is_erc721": False,
            "block_timestamp": blocks[0]["timestamp"],
        },
    ]
    transfers = [
        {
            "transaction_hash": f"tx{day}",
            "from_address": USER,
            "to_address": BINANCE[day - 1],
            "value": str(day * 1000000),
            "token_address": TETHER,
            "block_timestamp": blocks[day - 1]["timestamp"],
            "log_index": 0,
        }
        for day in (1, 2)
    ]
    data = {
        "blocks": blocks,
        "transactions": transactions,
        "contracts": contracts,
        "token_transfers": transfers,
        "entities": [{"address": TETHER, "owner": "Tether", "aliases": "USDT"}],
    }
    for name, rows in data.items():
        _csv(source / f"{name}.csv", rows)
    period = {"start": "2026-05-31", "end": "2026-06-30"}
    row_counts = {f"{name}.csv": len(rows) for name, rows in data.items() if name != "entities"}
    (source / "manifest.json").write_text(
        json.dumps(
            {
                "data_period": period,
                "rows": row_counts,
                "dictionary": {"address_count": 1},
            }
        )
    )
    files = []
    for name in IMPORT_FILES:
        path = source / name
        record = {"path": name, "bytes": path.stat().st_size, "sha256": digest(path)}
        if path.suffix == ".csv":
            record.update(
                columns=list(data[path.stem][0]), rows_from_source_manifest=row_counts.get(name)
            )
        files.append(record)
    (source / "import-manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "files": files,
                "total_bytes": sum(r["bytes"] for r in files),
                "data_period_from_source_manifest": period,
                "scope": "sampled_subset",
            }
        )
    )
    manifest = {"source_manifest_sha256": digest(source / "import-manifest.json"), "files": {}}
    _supplement(
        supplements,
        "transactions",
        [
            {
                "hash": t["hash"],
                "block_number": t["block_number"],
                "block_timestamp": t["block_timestamp"],
                "block_hash": b["hash"],
                "transaction_index": 0,
                "receipt_gas_used": 21000,
                "receipt_contract_address": None,
            }
            for t, b in zip(transactions, blocks, strict=True)
        ],
        manifest,
    )
    _supplement(
        supplements,
        "blocks",
        [
            {
                "number": b["number"],
                "hash": b["hash"],
                "base_fee_per_gas": 7,
            }
            for b in blocks
        ],
        manifest,
    )
    _supplement(
        supplements,
        "contracts",
        [
            {
                **c,
                "block_number": 1 if i == 0 else 100,
                "block_hash": "old" if i == 0 else "b1",
            }
            for i, c in enumerate(contracts)
        ],
        manifest,
    )
    _supplement(
        supplements,
        "amended_tokens",
        [
            {
                "address": TETHER,
                "symbol": "USDT",
                "name": "Tether USD",
                "decimals": "6",
            }
        ],
        manifest,
    )
    return source, supplements


def test_plan_and_build_preserve_measurements_and_record_subset_scope(local_source, tmp_path):
    source, supplements = local_source
    before = {p.name: digest(p) for p in source.iterdir()}
    plan = plan_local(source)
    assert plan["joins_ok"]
    assert plan["joins"]["transactions_to_blocks"]["matched"] == 2
    assert plan["joins"]["contracts_to_local_blocks"]["missing"] == 1
    parquet, store = tmp_path / "parquet", tmp_path / "store.duckdb"
    manifest = prepare_local(source, parquet, supplements, progress=lambda _: None)
    assert not manifest["complete_snapshot"]
    assert len(verify_parquet(parquet)["files"]) == 5
    counts = build_store(store, parquet, MINI_DICTIONARY / "entities.json")
    assert counts["transactions"] == counts["token_transfers"] == 2
    with connect(store) as con:
        assert store_profile(con)["scope"] == "sampled_subset"
        assert not store_profile(con)["complete_snapshot"]
        rows = execute(
            con,
            f"SELECT transaction_hash, value_wei, block_hash, receipt_gas_used "
            f"FROM `{P}.transaction_facts`(DATE '2026-06-01', DATE '2026-06-03') "
            "ORDER BY transaction_hash",
        ).rows
        assert rows == (
            ("tx1", Decimal(ETH + 1), "b1", 21000),
            ("tx2", Decimal(ETH + 2), "b2", 21000),
        )
        tokens = execute(
            con,
            f"SELECT SUM(normalized_amount) AS amount FROM "
            f"`{P}.token_transfer_facts`(DATE '2026-06-01', DATE '2026-06-03')",
        ).rows
        assert tokens == ((3.0,),)
        transfers = con.execute(
            "SELECT block_number, block_hash FROM token_transfers ORDER BY block_number"
        ).fetchall()
        assert transfers == [(100, "b1"), (200, "b2")]
        parity = check(
            con,
            Path(__file__).parent / "fixtures/bq_gold_results.json",
            Path(__file__).parent / "fixtures/stage_a_witnesses.json",
        )
        assert parity["skipped"] and not parity["passed"]
    assert before == {p.name: digest(p) for p in source.iterdir()}


@pytest.mark.parametrize(
    "damage", ["checksum", "source", "missing_tx", "duplicate_tx", "block_hash"]
)
def test_bad_supplements_never_publish_parquet(local_source, tmp_path, damage):
    source, supplements = local_source
    path = supplements / "transactions.parquet"
    manifest = json.loads((supplements / "manifest.json").read_text())
    if damage == "checksum":
        path.write_bytes(path.read_bytes() + b"changed")
    elif damage == "source":
        manifest["source_manifest_sha256"] = "wrong"
        (supplements / "manifest.json").write_text(json.dumps(manifest))
    else:
        rows = pq.read_table(path).to_pylist()
        if damage == "missing_tx":
            rows.pop()
        elif damage == "duplicate_tx":
            rows.append(rows[0])
        else:
            rows[0]["block_hash"] = "different canonical block"
        _supplement(supplements, "transactions", rows, manifest)
    output = tmp_path / "parquet"
    with pytest.raises(ValueError):
        prepare_local(source, output, supplements, progress=lambda _: None)
    assert not output.exists()


@pytest.mark.parametrize(
    "damage", ["missing", "extra", "checksum", "rows", "columns", "full_scope"]
)
def test_bad_parquet_manifest_cannot_replace_existing_database(local_source, tmp_path, damage):
    source, supplements = local_source
    parquet, store = tmp_path / "parquet", tmp_path / "store.duckdb"
    prepare_local(source, parquet, supplements, progress=lambda _: None)
    build_store(store, parquet, MINI_DICTIONARY / "entities.json")
    original = digest(store)
    manifest_path = parquet / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    record = next(r for r in manifest["files"] if r["table"] == "transactions")
    target = parquet / record["path"]
    if damage == "missing":
        target.unlink()
    elif damage == "extra":
        (target.parent / "extra.parquet").write_bytes(target.read_bytes())
    elif damage == "checksum":
        record["sha256"] = "bad"
    elif damage == "rows":
        record["rows"] += 1
    elif damage == "columns":
        table = pq.read_table(target).drop(["receipt_gas_used"])
        pq.write_table(table, target)
        record.update(sha256=digest(target), bytes=target.stat().st_size)
    else:
        manifest["complete_snapshot"] = True
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises((ValueError, FileNotFoundError)):
        build_store(store, parquet, MINI_DICTIONARY / "entities.json")
    assert digest(store) == original


def test_failed_label_load_leaves_previous_store_untouched(local_source, tmp_path):
    source, supplements = local_source
    parquet, store = tmp_path / "parquet", tmp_path / "store.duckdb"
    prepare_local(source, parquet, supplements, progress=lambda _: None)
    build_store(store, parquet, MINI_DICTIONARY / "entities.json")
    original = digest(store)
    invalid = tmp_path / "bad-entities.json"
    rows = json.loads((MINI_DICTIONARY / "entities.json").read_text())
    invalid.write_text(json.dumps(rows + rows[:1]))
    with pytest.raises(ValueError, match="duplicate label address"):
        build_store(store, parquet, invalid)
    assert digest(store) == original
    assert not list(tmp_path.glob(".build-store-*"))


def test_supplement_queries_use_historical_cohort_and_required_metadata(local_source):
    source, _ = local_source
    queries = {name: (sql, parameters) for name, sql, parameters in supplement_queries(source)}
    assert set(queries) == {"transactions", "blocks", "contracts", "amended_tokens"}
    sql, parameters = queries["transactions"]
    assert "FARM_FINGERPRINT(`hash`)" in sql
    assert parameters["labeled"] == [TETHER]
    assert "receipt_gas_used" in sql and "transaction_index" in sql
    assert TETHER in queries["contracts"][1]["addresses"]


@pytest.mark.parametrize("mode", ["success", "storage", "over_budget", "empty"])
def test_supplement_download_enforces_budget_and_verified_resume(
    local_source, tmp_path, monkeypatch, mode
):
    bigquery = pytest.importorskip("google.cloud.bigquery")
    from eth_nl2sql.store import supplements as module

    source, _ = local_source
    calls = []
    closed = []
    batch = pa.record_batch({"measured": [1, 2]})

    class Client:
        def __init__(self, project):
            pass

        def query(self, sql, *, job_config):
            calls.append(job_config)
            if job_config.dry_run:
                return SimpleNamespace(
                    total_bytes_processed=module.MAX_BYTES + 1 if mode == "over_budget" else 1024
                )
            result = SimpleNamespace(
                to_arrow_iterable=lambda **kwargs: iter([] if mode == "empty" else [batch])
            )
            return SimpleNamespace(
                result=lambda **kwargs: result, job_id="measured-job", total_bytes_billed=1024
            )

    monkeypatch.setattr(bigquery, "Client", Client)
    if mode == "storage":
        storage_module = pytest.importorskip("google.cloud.bigquery_storage")

        class Storage:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                closed.append(True)

        monkeypatch.setattr(storage_module, "BigQueryReadClient", Storage)
    monkeypatch.setattr(
        module, "_specs", lambda _: iter([("transactions", "SELECT measured", "binding", [])])
    )
    out = tmp_path / "downloaded"
    if mode not in {"success", "storage"}:
        with pytest.raises(ValueError):
            module.download("test", source, out, progress=lambda _: None, storage_api=False)
        assert not list(out.glob("*.parquet"))
        if mode == "empty":
            pending = json.loads((out / "manifest.json").read_text())
            assert (
                pending["files"] == {}
                and pending["jobs"]["transactions"]["job_id"] == "measured-job"
            )
        else:
            assert not (out / "manifest.json").exists()
        assert len(calls) == (1 if mode == "over_budget" else 2)
        return
    report = module.download(
        "test", source, out, progress=lambda _: None, storage_api=mode == "storage"
    )
    assert report["files"]["transactions"]["rows"] == 2
    assert calls[-1].maximum_bytes_billed == module.MAX_BYTES
    assert closed == ([True] if mode == "storage" else [])
    count = len(calls)
    module.download("test", source, out, progress=lambda _: None, storage_api=False)
    assert len(calls) == count
    target = out / "transactions.parquet"
    target.write_bytes(target.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="unverified existing supplement"):
        module.download("test", source, out, progress=lambda _: None, storage_api=False)
    assert len(calls) == count

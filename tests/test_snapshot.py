"""Bounded extraction, interruption recovery and provenance without live queries."""

import json
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pyarrow as pa
import pytest

from eth_nl2sql.store import snapshot
from eth_nl2sql.store.build import RAW_SCHEMAS
from eth_nl2sql.store.manifest import verify_parquet
from eth_nl2sql.store.quality import validate_snapshot

MIB = 2**20


def batch_for(query):
    stamp = (
        datetime.fromisoformat(query.name).replace(tzinfo=UTC)
        if query.name[0].isdigit()
        else datetime(2017, 1, 1, tzinfo=UTC)
    )
    data = {}
    for name, kind in RAW_SCHEMAS[query.table].items():
        if kind == "TIMESTAMPTZ":
            data[name] = pa.array([stamp], type=pa.timestamp("us", tz="UTC"))
        elif kind == "BIGINT":
            data[name] = pa.array([1], type=pa.int64())
        elif kind.startswith("DECIMAL"):
            data[name] = pa.array([Decimal(1)], type=pa.decimal128(38, 9))
        elif kind == "BOOLEAN":
            data[name] = pa.array([True])
        else:
            data[name] = pa.array(["1"])
    if query.table in {"transactions", "blocks", "token_transfers"}:
        number = (stamp.date() - snapshot.SNAPSHOT_START).days + 1
        if query.table == "blocks":
            data.update(number=pa.array([number]), hash=pa.array([f"block{number}"]))
        else:
            data.update(block_number=pa.array([number]), block_hash=pa.array([f"block{number}"]))
            data["hash" if query.table == "transactions" else "transaction_hash"] = pa.array(
                [f"tx{number}"]
            )
    return pa.record_batch(data)


@pytest.fixture
def remote(monkeypatch, tmp_path):
    pytest.importorskip("google.cloud.bigquery")
    from google.api_core.exceptions import NotFound

    state = SimpleNamespace(
        jobs={}, submitted=[], fetched=[], dry=[], fail=None, quota=snapshot.FREE_MONTHLY_BYTES
    )
    queries = {q.sql: q for q in snapshot.extraction_queries()}

    class Client:
        def close(self):
            pass

        def query(self, sql, *, job_config, **kwargs):
            if job_config.dry_run:
                state.dry.append(sql)
                return SimpleNamespace(total_bytes_processed=10 * MIB, referenced_tables=[1])
            job_id = kwargs["job_id"]
            # The reservation must already be durable before the remote RPC.
            manifest = json.loads((tmp_path / "parquet/manifest.json").read_text())
            assert any(j["job_id"] == job_id for j in manifest["jobs"].values())
            assert kwargs["job_retry"] is None
            state.submitted.append((job_id, job_config.maximum_bytes_billed))

            def batches(**options):
                assert "create_bqstorage_client" not in options
                yield batch_for(queries[sql])
                if state.fail == "stream":
                    raise RuntimeError("interrupted Arrow stream")

            result = SimpleNamespace(total_rows=1, to_arrow_iterable=batches)

            def get_result(**kwargs):
                if state.fail == "result":
                    raise RuntimeError("interrupted polling")
                return result

            job = SimpleNamespace(
                job_id=job_id,
                query=sql,
                project="test",
                location="US",
                cache_hit=False,
                total_bytes_processed=10 * MIB,
                total_bytes_billed=8 * MIB,
                maximum_bytes_billed=job_config.maximum_bytes_billed,
                result=get_result,
            )
            state.jobs[job_id] = job
            if state.fail == "submission":
                raise RuntimeError("response lost after server accepted the job")
            return job

        def get_job(self, job_id, **kwargs):
            state.fetched.append(job_id)
            if job_id not in state.jobs:
                raise NotFound("missing job")
            return state.jobs[job_id]

    monkeypatch.setattr(snapshot, "_client", lambda *args: Client())
    monkeypatch.setattr(
        snapshot,
        "sandbox_status",
        lambda *args: {
            "remaining_bytes": state.quota,
            "billing_enabled": False,
            "billing_account_attached": False,
        },
    )
    state.out = tmp_path / "parquet"
    return state


def run(remote, **kwargs):
    return snapshot.run("test", remote.out, progress=lambda _: None, **kwargs)


def test_full_snapshot_streaming_and_network_free_resume(remote, monkeypatch):
    result = run(remote)
    assert result["written"] == 95 and result["bytes_billed"] == 95 * 8 * MIB
    assert len(remote.submitted) == 95
    manifest = verify_parquet(remote.out)
    assert manifest["complete_snapshot"] and len(manifest["jobs"]) == 95
    assert validate_snapshot(remote.out)["passed"]
    monkeypatch.setattr(snapshot, "_client", lambda *args: pytest.fail("resume contacted BigQuery"))
    assert run(remote)["skipped"] == 95
    # A valid checksum does not establish the date or join semantics.
    import pyarrow.parquet as pq

    from eth_nl2sql.store.manifest import file_digest

    record = manifest["files"][0]
    target = remote.out / record["path"]
    table = pq.read_table(target)
    column = table.schema.get_field_index("block_timestamp")
    table = table.set_column(
        column,
        table.schema.field(column),
        pa.array([datetime(2020, 1, 1, tzinfo=UTC)], type=table.schema.field(column).type),
    )
    pq.write_table(table, target)
    record.update(bytes=target.stat().st_size, sha256=file_digest(target))
    (remote.out / "manifest.json").write_text(json.dumps(manifest))
    quality = validate_snapshot(remote.out)
    assert not quality["passed"]
    assert not quality["checks"][f"partition:{record['path']}"]


@pytest.mark.parametrize("failure", ["stream", "submission", "result"])
def test_resume_downloads_same_job_after_interruption(remote, failure):
    remote.fail = failure
    with pytest.raises(RuntimeError):
        run(remote)
    assert len(remote.submitted) == 1
    pending = json.loads((remote.out / "manifest.json").read_text())
    job = next(iter(pending["jobs"].values()))
    assert job["job_id"] == remote.submitted[0][0] and not pending["complete_snapshot"]
    remote.fail = None
    result = run(remote)
    assert result["resumed_jobs"] == 1
    assert len(remote.submitted) == 95 and len(remote.jobs) == 95
    assert result["bytes_billed"] == 95 * 8 * MIB
    assert verify_parquet(remote.out)["complete_snapshot"]


def test_budget_preflight_rejects_before_any_billable_job(remote):
    with pytest.raises(ValueError, match="budget"):
        run(remote, budget_bytes=100 * MIB)
    assert not remote.submitted and not (remote.out / "manifest.json").exists()


def test_zero_free_allowance_rejects_before_billable_job(remote):
    remote.quota = 0
    with pytest.raises(ValueError, match="free monthly quota"):
        run(remote)
    assert not remote.submitted


def test_server_maximum_never_exceeds_remaining_budget(remote):
    result = run(remote, budget_bytes=1000 * MIB)
    spent = 0
    for _, maximum in remote.submitted:
        assert maximum <= min(snapshot.MAX_BYTES_PER_QUERY, 1000 * MIB - spent)
        spent += 8 * MIB
    assert result["bytes_billed"] == spent <= 1000 * MIB


@pytest.mark.parametrize(
    "damage",
    [
        "checksum",
        "query",
        "rows",
        "orphan",
        "project",
        "budget",
        "job_project",
        "job_location",
        "job_cap",
    ],
)
def test_resume_rejects_unverified_files_or_binding_before_network(remote, monkeypatch, damage):
    remote.fail = "stream"
    with pytest.raises(RuntimeError):
        run(remote)
    path = remote.out / "manifest.json"
    manifest = json.loads(path.read_text())
    pending = next(iter(manifest["jobs"].values()))
    relative = next(iter(manifest["jobs"]))
    if damage in {"checksum", "rows", "orphan"}:
        import pyarrow.parquet as pq

        from eth_nl2sql.store.manifest import file_digest

        target = remote.out / relative
        pq.write_table(pa.Table.from_batches([batch_for(snapshot.extraction_queries()[0])]), target)
        record = {
            "path": relative,
            "table": "transactions",
            "rows": 1,
            "bytes": target.stat().st_size,
            "sha256": file_digest(target),
            "query_sha256": pending["query_sha256"],
        }
        manifest["files"] = [] if damage == "orphan" else [record]
        if damage == "checksum":
            target.write_bytes(target.read_bytes() + b"corruption")
        elif damage == "rows":
            record["rows"] += 1
    elif damage == "query":
        pending["query_sha256"] = "changed"
    elif damage == "project":
        manifest["project"] = "other"
    elif damage == "job_project":
        pending["project"] = "other"
    elif damage == "job_location":
        pending["location"] = "EU"
    elif damage == "job_cap":
        pending["maximum_bytes_billed"] = snapshot.MAX_BYTES_PER_QUERY + 1
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(snapshot, "_client", lambda *args: pytest.fail("network before integrity"))
    with pytest.raises(ValueError):
        run(remote, **({"budget_bytes": 1} if damage == "budget" else {}))


def test_expired_recorded_job_is_never_reexecuted(remote):
    remote.fail = "stream"
    with pytest.raises(RuntimeError):
        run(remote)
    remote.jobs.clear()
    with pytest.raises(ValueError, match="refusing to rerun"):
        run(remote)
    assert len(remote.submitted) == 1


def test_concurrent_extractor_is_rejected_before_network(remote, monkeypatch):
    monkeypatch.setattr(snapshot, "_client", lambda *args: pytest.fail("lock failed"))
    with snapshot._lock(remote.out), pytest.raises(ValueError, match="another snapshot process"):
        run(remote)


def test_dry_run_contains_partition_sql_and_hash_and_enforces_total(remote):
    report = snapshot.plan("test", budget_bytes=100 * MIB)
    assert not report["passed"] and len(report["partitions"]) == 95
    assert report["estimated_billed_bytes"] == 950 * MIB
    assert all(len(r["query_sha256"]) == 64 for r in report["partitions"])
    assert not remote.submitted


@pytest.mark.parametrize(
    "billing",
    [
        {"billingEnabled": True, "billingAccountName": "attached"},
        {"billingEnabled": False, "billingAccountName": "inactive-but-attached"},
        {},
    ],
)
def test_free_only_rejects_attached_or_unknown_billing_before_listing_jobs(monkeypatch, billing):
    monkeypatch.setattr(snapshot, "_billing_info", lambda *args: billing)
    client = SimpleNamespace(
        _credentials=None, list_jobs=lambda **_: pytest.fail("billing guard did not run first")
    )
    with pytest.raises(ValueError, match="no billing account"):
        snapshot.sandbox_status("test", client)


def test_monthly_quota_counts_project_jobs_and_allows_resuming_own_active_job(monkeypatch):
    monkeypatch.setattr(snapshot, "_billing_info", lambda *args: {"billingEnabled": False})

    def job(identifier, state="DONE", billed=10 * MIB):
        return SimpleNamespace(
            job_id=identifier,
            job_type="query",
            dry_run=False,
            parent_job_id=None,
            state=state,
            error_result=None,
            total_bytes_billed=billed,
        )

    jobs = [job("old"), job("own-pending", "RUNNING", None)]

    def list_jobs(**kwargs):
        assert kwargs["all_users"]
        assert kwargs["min_creation_time"].day == 1
        assert kwargs["min_creation_time"].tzinfo is UTC
        return jobs

    client = SimpleNamespace(_credentials=None, list_jobs=list_jobs)
    report = snapshot.sandbox_status("test", client, {"own-pending"})
    assert report["used_bytes"] == 10 * MIB
    assert report["remaining_bytes"] == snapshot.FREE_MONTHLY_BYTES - 10 * MIB
    assert report["active_snapshot_jobs"] == ["own-pending"]
    with pytest.raises(ValueError, match="query job is active"):
        snapshot.sandbox_status("test", client)


def test_resume_recovers_crash_between_file_rename_and_manifest_commit(remote, monkeypatch):
    original = snapshot.atomic_write_json
    interrupted = False

    def write(path, value, *, durable=False):
        nonlocal interrupted
        assert durable
        if path.name == "manifest.json" and value.get("files") and not interrupted:
            interrupted = True
            raise RuntimeError("interrupted before file record was committed")
        original(path, value, durable=durable)

    monkeypatch.setattr(snapshot, "atomic_write_json", write)
    with pytest.raises(RuntimeError):
        run(remote)
    assert len(remote.submitted) == 1 and len(list(remote.out.rglob("*.parquet"))) == 1
    result = run(remote)
    assert result["skipped"] == 1 and len(remote.submitted) == 95
    assert verify_parquet(remote.out)["complete_snapshot"]


@pytest.mark.parametrize("reason", ["less_quota", "old_reservation"])
def test_missing_planned_job_cannot_exceed_new_quota_or_reuse_a_stale_id(remote, reason):
    remote.fail = "submission"
    with pytest.raises(RuntimeError):
        run(remote)
    remote.jobs.clear()
    remote.fail = None
    if reason == "less_quota":
        # Enough for the estimated remainder, less than the original 50 GiB
        # server cap. An existing planned job cannot silently raise this cap.
        remote.quota = 2**30
    else:
        path = remote.out / "manifest.json"
        manifest = json.loads(path.read_text())
        next(iter(manifest["jobs"].values()))["planned_at"] = "2020-01-01T00:00:00+00:00"
        path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="planned job"):
        run(remote)
    assert len(remote.submitted) == 1

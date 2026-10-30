"""One-time extraction of the snapshot window from the BigQuery public dataset.

Dry runs are saved per partition. Jobs are journaled before submission and
downloaded in bounded Arrow batches; restart retrieves the same job. The
default execution policy requires a project with no billing account attached.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import uuid
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from eth_nl2sql.artifacts import atomic_write_json
from eth_nl2sql.store import PUBLIC_DATASET
from eth_nl2sql.store.build import RAW_SCHEMAS, SNAPSHOT_END, SNAPSHOT_START

MAX_BYTES_PER_QUERY = 50 * 2**30  # luanvan catalog cost_policy.maximum_bytes_billed
FREE_MONTHLY_BYTES = 2**40
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
                    f"SELECT {_columns(table)} FROM `{PUBLIC_DATASET}.{table}` "
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
        f"SELECT LOWER({column}) AS address FROM `{PUBLIC_DATASET}.{table}` WHERE {window_tx}"
        for column, table in sources
    )
    queries.append(
        ExtractionQuery(
            "contracts",
            "referenced",
            f"WITH referenced AS (\n{referenced}\n)\n"
            f"SELECT {_columns('contracts')} FROM `{PUBLIC_DATASET}.contracts` "
            f"WHERE block_timestamp < TIMESTAMP('{end}') "
            f"AND LOWER(address) IN (SELECT address FROM referenced WHERE address IS NOT NULL)",
        )
    )
    queries.append(
        ExtractionQuery(
            "amended_tokens",
            "all",
            f"SELECT {_columns('amended_tokens')} FROM `{PUBLIC_DATASET}.amended_tokens`",
        )
    )
    return queries


def _client(project: str, location: str = "US"):
    from google.cloud import bigquery

    return bigquery.Client(project=project, location=location)


def query_digest(query: ExtractionQuery) -> str:
    return hashlib.sha256(query.sql.encode()).hexdigest()


@contextmanager
def _lock(directory: Path):
    import fcntl

    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".snapshot.lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("another snapshot process holds this directory") from exc
        yield


def _billing_info(project: str, credentials) -> dict:
    """Use an existing authenticated reader; never enable services or attach billing."""
    from google.auth.transport.requests import AuthorizedSession

    with AuthorizedSession(credentials) as session:
        response = session.get(
            f"https://cloudbilling.googleapis.com/v1/projects/{project}/billingInfo", timeout=30
        )
        if response.status_code == 403:
            # ADC may have BigQuery-only OAuth scopes. The installed gcloud
            # login can independently read the same project's billing state.
            result = subprocess.run(
                ["gcloud", "billing", "projects", "describe", project, "--format=json", "--quiet"],
                capture_output=True,
                text=True,
                timeout=60,
                check=True,
            )
            billing = json.loads(result.stdout)
        else:
            response.raise_for_status()
            billing = response.json()
    if billing.get("projectId") != project:
        raise ValueError("billing response does not identify the requested project")
    return billing


def sandbox_status(project: str, client, allowed_job_ids: set[str] | None = None) -> dict:
    """Read billing attachment and project-wide monthly jobs, without running SQL."""
    billing = _billing_info(project, client._credentials)
    if billing.get("billingEnabled") is not False or billing.get("billingAccountName"):
        raise ValueError("free-only execution requires a project with no billing account attached")
    now = datetime.now(UTC)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    billed = 0
    jobs = []
    active_jobs = []
    quota_errors = []
    for job in client.list_jobs(all_users=True, min_creation_time=start, timeout=30):
        if job.job_type != "query" or job.dry_run or job.parent_job_id:
            continue
        if job.state != "DONE":
            if job.job_id not in (allowed_job_ids or set()):
                raise ValueError(
                    f"cannot establish free quota while query job is active: {job.job_id}"
                )
            active_jobs.append(job.job_id)
            continue
        if job.error_result:
            if job.error_result.get("reason") == "quotaExceeded":
                quota_errors.append({"job_id": job.job_id, "error": job.error_result})
        if job.total_bytes_billed is None:
            job = client.get_job(job.job_id, location=job.location, timeout=30)
        amount = int(job.total_bytes_billed or 0)
        billed += amount
        jobs.append({"job_id": job.job_id, "bytes_billed": amount})
    return {
        "checked_at": now.isoformat(),
        "project": project,
        "billing_enabled": False,
        "billing_account_attached": False,
        "month_utc": start.strftime("%Y-%m"),
        "all_users": True,
        "monthly_limit_bytes": FREE_MONTHLY_BYTES,
        "used_bytes": billed,
        "remaining_bytes": max(0, FREE_MONTHLY_BYTES - billed),
        "jobs": jobs,
        "active_snapshot_jobs": active_jobs,
        "quota_errors": quota_errors,
        "usage_note": "Conservative project-wide job-byte accounting, not a billing invoice.",
    }


def plan(project: str, *, location: str = "US", budget_bytes: int | None = None) -> dict:
    """Dry-run all partitions, retaining SQL, binding, estimate and failures."""
    from google.cloud import bigquery

    client = _client(project, location)
    config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    per_table: dict[str, int] = {}
    records = []
    try:
        for query in extraction_queries():
            record = {
                "path": f"{query.table}/{query.name}.parquet",
                "table": query.table,
                "sql": query.sql,
                "query_sha256": query_digest(query),
            }
            records.append(record)
            try:
                job = client.query(query.sql, job_config=config, timeout=30)
                if job.total_bytes_processed is None:
                    raise ValueError("BigQuery returned no byte estimate")
                size = int(job.total_bytes_processed)
                # BigQuery billing rounds up to MiB, with at least 10 MiB per
                # referenced table. This is an estimate, not a spending guard.
                minimum = max(1, len(job.referenced_tables or [])) * 10 * 2**20
                estimated_billed = max(minimum, math.ceil(size / 2**20) * 2**20)
                record.update(
                    estimated_bytes=size,
                    estimated_billed_bytes=estimated_billed,
                    within_limit=estimated_billed <= MAX_BYTES_PER_QUERY,
                )
                per_table[query.table] = per_table.get(query.table, 0) + size
            except Exception as exc:
                record["error"] = f"{type(exc).__name__}: {exc}"
                break
    finally:
        client.close()
    total = sum(per_table.values())
    estimated_billed = sum(r.get("estimated_billed_bytes", 0) for r in records)
    return {
        "version": 2,
        "generated_at": datetime.now(UTC).isoformat(),
        "dry_run": True,
        "project": project,
        "location": location,
        "window": [SNAPSHOT_START.isoformat(), SNAPSHOT_END.isoformat()],
        "queries": len(extraction_queries()),
        "partitions": records,
        "passed": len(records) == len(extraction_queries())
        and all(r.get("within_limit", False) for r in records)
        and (budget_bytes is None or estimated_billed <= budget_bytes),
        "maximum_bytes_per_query": MAX_BYTES_PER_QUERY,
        "budget_bytes": budget_bytes,
        "bytes_by_table": per_table,
        "total_bytes": total,
        "estimated_billed_bytes": estimated_billed,
        "total_gib": round(total / 2**30, 2),
        "largest_query_gib": round(
            max((r.get("estimated_bytes", 0) for r in records), default=0) / 2**30, 2
        ),
    }


def _progress(message: str) -> None:
    print(message, flush=True)


def run(
    project: str,
    out_dir: Path,
    *,
    budget_bytes: int | None = None,
    location: str = "US",
    storage_api: bool = False,
    progress=_progress,
) -> dict:
    """Run under a cumulative cap, reusing verified files and journaled jobs.

    A server-side maximum is bounded by both the per-query cap and the remaining
    cumulative budget. Billing must be unattached; the cap cannot be increased
    on resume. Download failure never authorizes a replacement query job.
    """
    with _lock(out_dir):
        return _run(project, out_dir, budget_bytes, location, storage_api, progress)


def _run(project, out_dir, budget_bytes, location, storage_api, progress):
    import pyarrow as pa
    import pyarrow.parquet as pq
    from google.api_core.exceptions import Conflict, NotFound
    from google.cloud import bigquery

    from eth_nl2sql.store.manifest import file_digest, verify_parquet, verify_record

    manifest_path = out_dir / "manifest.json"
    window = [SNAPSHOT_START.isoformat(), SNAPSHOT_END.isoformat()]
    queries = {f"{q.table}/{q.name}.parquet": q for q in extraction_queries()}
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    if manifest is not None and (
        manifest.get("version") != 2
        or manifest.get("scope") != "full_ethereum_window"
        or manifest.get("window") != window
        or manifest.get("project") != project
        or manifest.get("location") != location
        or manifest.get("free_only") is not True
        or type(manifest.get("budget_bytes")) is not int
        or not 0 < manifest["budget_bytes"] <= FREE_MONTHLY_BYTES
        or not isinstance(manifest.get("complete_snapshot"), bool)
    ):
        raise ValueError("existing snapshot has a different scope/window/project/location/version")
    recorded = {r["path"]: r for r in manifest["files"]} if manifest else {}
    if manifest and len(recorded) != len(manifest["files"]):
        raise ValueError("duplicate snapshot file records")
    # Validate every existing artifact before any network activity or new query.
    observed = {p.relative_to(out_dir).as_posix() for p in out_dir.rglob("*.parquet")}
    if set(recorded) - observed or observed - set(queries):
        raise ValueError("snapshot files are missing or unexpected")
    recovered = False
    for relative in observed:
        record = recorded.get(relative)
        if record is None and manifest:
            record = manifest["jobs"].get(relative, {}).get("download")
            if record:
                recorded[relative] = record
                recovered = True
        if not record or record.get("query_sha256") != query_digest(queries[relative]):
            raise ValueError(f"existing snapshot file lacks matching provenance: {relative}")
        verify_record(out_dir, record)
    if recovered:
        manifest["files"] = list(recorded.values())
        atomic_write_json(manifest_path, manifest, durable=True)
    if manifest:
        for relative, pending in manifest["jobs"].items():
            if (
                relative not in queries
                or pending.get("query_sha256") != query_digest(queries[relative])
                or pending.get("sql") != queries[relative].sql
                or pending.get("project") != project
                or pending.get("location") != location
                or not pending.get("job_id")
                or pending.get("state") not in {"planned", "submitted", "done"}
                or type(pending.get("maximum_bytes_billed")) is not int
                or not 0 < pending["maximum_bytes_billed"] <= MAX_BYTES_PER_QUERY
                or (
                    "bytes_billed" in pending
                    and not 0 <= pending["bytes_billed"] <= pending["maximum_bytes_billed"]
                )
            ):
                raise ValueError(f"pending snapshot job has different query provenance: {relative}")
        for relative, record in recorded.items():
            pending = manifest["jobs"].get(relative, {})
            if (
                pending.get("state") != "done"
                or record.get("job_id") != pending.get("job_id")
                or record.get("project") != project
                or record.get("location") != location
                or record.get("bytes_billed") != pending.get("bytes_billed")
                or record["rows"] != pending.get("source_rows")
            ):
                raise ValueError(f"snapshot file and job provenance disagree: {relative}")
        if budget_bytes is not None and budget_bytes != manifest["budget_bytes"]:
            raise ValueError("snapshot budget cannot change on resume")
    if len(recorded) == len(queries):
        manifest["complete_snapshot"] = True
        verify_parquet(out_dir, manifest=manifest)
        atomic_write_json(manifest_path, manifest, durable=True)
        return {
            "written": 0,
            "skipped": len(recorded),
            "resumed_jobs": 0,
            "bytes_billed": sum(j["bytes_billed"] for j in manifest["jobs"].values()),
        }

    with ExitStack() as resources:
        client = _client(project, location)
        resources.callback(client.close)
        free = sandbox_status(
            project, client, {j["job_id"] for j in manifest["jobs"].values()} if manifest else set()
        )
        atomic_write_json(out_dir / "sandbox-status.json", free, durable=True)
        if manifest is None:
            budget_bytes = free["remaining_bytes"] if budget_bytes is None else budget_bytes
            if not 0 < budget_bytes <= free["remaining_bytes"]:
                raise ValueError("snapshot budget exceeds remaining free monthly quota")
            manifest = {
                "version": 2,
                "scope": "full_ethereum_window",
                "window": window,
                "project": project,
                "location": location,
                "complete_snapshot": False,
                "budget_bytes": budget_bytes,
                "free_only": True,
                "created_at": datetime.now(UTC).isoformat(),
                "jobs": {},
                "files": [],
            }
        jobs = manifest["jobs"]
        reserved = {p: j.get("bytes_billed", j["maximum_bytes_billed"]) for p, j in jobs.items()}
        billed = sum(reserved.values())
        remaining = manifest["budget_bytes"] - billed
        quota_remaining = free["remaining_bytes"]
        missing = [p for p in queries if p not in recorded and p not in jobs]
        dry_run = plan(project, location=location)
        atomic_write_json(out_dir / "dry-run.json", dry_run, durable=True)
        estimates = {r["path"]: r for r in dry_run["partitions"]}
        needed = sum(estimates.get(p, {}).get("estimated_billed_bytes", 0) for p in missing)
        if not dry_run["passed"] or needed > min(remaining, quota_remaining):
            raise ValueError(
                "dry-run failed or remaining partitions exceed the free snapshot budget"
            )
        atomic_write_json(manifest_path, manifest, durable=True)
        written, resumed = 0, 0
        storage = None
        if storage_api:
            from google.cloud import bigquery_storage

            storage = resources.enter_context(bigquery_storage.BigQueryReadClient())
        for relative, query in queries.items():
            if relative in recorded:
                continue
            target = out_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            pending = jobs.get(relative)
            if pending is None:
                cap = min(MAX_BYTES_PER_QUERY, remaining, quota_remaining)
                if estimates[relative]["estimated_billed_bytes"] > cap:
                    raise ValueError(f"remaining budget cannot cover {relative}")
                pending = {
                    "job_id": "eth_t06_" + uuid.uuid4().hex,
                    "project": project,
                    "location": location,
                    "state": "planned",
                    "planned_at": datetime.now(UTC).isoformat(),
                    "query_sha256": query_digest(query),
                    "sql": query.sql,
                    "estimated_bytes": estimates[relative]["estimated_bytes"],
                    "maximum_bytes_billed": cap,
                }
                jobs[relative] = pending
                atomic_write_json(manifest_path, manifest, durable=True)
            submitted_now = False
            try:
                job = client.get_job(pending["job_id"], location=location, timeout=30)
                resumed += 1
            except NotFound as exc:
                if pending["state"] != "planned":
                    raise ValueError(
                        f"journaled job expired/missing; refusing to rerun {relative}"
                    ) from exc
                age = datetime.now(UTC) - datetime.fromisoformat(pending["planned_at"])
                if age > timedelta(days=1):
                    raise ValueError("missing planned job is too old to submit safely") from exc
                available = min(remaining + reserved.get(relative, 0), quota_remaining)
                if pending["maximum_bytes_billed"] > available:
                    raise ValueError("planned job cap exceeds the remaining free budget") from exc
                config = bigquery.QueryJobConfig(
                    maximum_bytes_billed=pending["maximum_bytes_billed"],
                    use_query_cache=True,
                    labels={"task": "t06", "table": query.table},
                )
                submitted_now = True
                try:
                    job = client.query(
                        query.sql,
                        job_config=config,
                        job_id=pending["job_id"],
                        location=location,
                        job_retry=None,
                        timeout=30,
                    )
                except Conflict:
                    job = client.get_job(pending["job_id"], location=location, timeout=30)
            if (
                job.query != query.sql
                or job.project != project
                or job.location != location
                or job.maximum_bytes_billed != pending["maximum_bytes_billed"]
            ):
                raise ValueError(f"BigQuery job provenance differs for {relative}")
            pending["state"] = "submitted"
            atomic_write_json(manifest_path, manifest, durable=True)
            progress(f"Downloading {relative} (job {job.job_id})")
            result = job.result(page_size=50_000, job_retry=None)
            if job.total_bytes_billed is None or job.total_bytes_processed is None:
                raise ValueError(f"BigQuery omitted completed job byte statistics for {relative}")
            amount = int(job.total_bytes_billed or 0)
            accounted = reserved.get(relative, 0)
            remaining += accounted - amount
            if submitted_now:
                quota_remaining -= amount
            pending.update(
                state="done",
                bytes_billed=amount,
                bytes_processed=int(job.total_bytes_processed or 0),
                cache_hit=bool(job.cache_hit),
                source_rows=int(result.total_rows),
                created_at=str(getattr(job, "created", None)),
                ended_at=str(getattr(job, "ended", None)),
                download_api="storage" if storage_api else "rest",
            )
            atomic_write_json(manifest_path, manifest, durable=True)
            if remaining < 0 or amount > pending["maximum_bytes_billed"]:
                raise ValueError("BigQuery job exceeded the recorded spending cap")
            partial = target.with_suffix(".parquet.partial")
            writer = None
            rows = 0
            try:
                kwargs = (
                    {"bqstorage_client": storage, "max_stream_count": 2, "max_queue_size": 2}
                    if storage is not None
                    else {}
                )
                for batch in result.to_arrow_iterable(**kwargs):
                    if writer is None:
                        if set(batch.schema.names) != set(RAW_SCHEMAS[query.table]):
                            raise ValueError(f"unexpected BigQuery columns for {relative}")
                        writer = pq.ParquetWriter(partial, batch.schema, compression="zstd")
                    writer.write_table(pa.Table.from_batches([batch]))
                    rows += batch.num_rows
                if not rows:
                    raise ValueError(f"BigQuery returned an empty required partition: {relative}")
                if rows != result.total_rows:
                    raise ValueError(f"download row count differs from BigQuery for {relative}")
            finally:
                if writer is not None:
                    writer.close()
            record = {
                "table": query.table,
                "path": relative,
                "rows": rows,
                "bytes": partial.stat().st_size,
                "sha256": file_digest(partial),
                "query_sha256": query_digest(query),
                "job_id": job.job_id,
                "project": project,
                "location": location,
                "bytes_billed": amount,
            }
            # Journal checksum first. A crash between rename and journal commit
            # can be recovered against this measured record without a new job.
            pending["download"] = record
            atomic_write_json(manifest_path, manifest, durable=True)
            partial.replace(target)
            recorded[relative] = record
            manifest["files"] = list(recorded.values())
            atomic_write_json(manifest_path, manifest, durable=True)
            written += 1
            progress(f"Saved {relative}: {rows:,} rows; billed {amount / 2**30:.3f} GiB")
        # Verify every checksum and partition before advertising completeness.
        manifest["complete_snapshot"] = True
        try:
            verify_parquet(out_dir, manifest=manifest)
        except Exception:
            manifest["complete_snapshot"] = False
            atomic_write_json(manifest_path, manifest, durable=True)
            raise
        atomic_write_json(manifest_path, manifest, durable=True)
        return {
            "written": written,
            "skipped": len(observed),
            "resumed_jobs": resumed,
            "bytes_billed": sum(j["bytes_billed"] for j in jobs.values()),
            "budget_bytes": manifest["budget_bytes"],
            "complete_snapshot": True,
        }

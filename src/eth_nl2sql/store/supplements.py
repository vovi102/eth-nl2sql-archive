"""Bounded BigQuery enrichment of the historical local CSV subset."""

from __future__ import annotations

import hashlib
import json
from contextlib import ExitStack
from pathlib import Path

from eth_nl2sql.data.audit import verify_import
from eth_nl2sql.store.local import digest, supplement_queries

MAX_BYTES = 50 * 2**30


def _specs(directory: Path):
    from google.cloud import bigquery

    for name, sql, parameters in supplement_queries(directory):
        fingerprint = hashlib.sha256(
            json.dumps([sql, parameters], sort_keys=True).encode()
        ).hexdigest()
        params = [bigquery.ArrayQueryParameter(k, "STRING", v) for k, v in parameters.items()]
        yield name, sql, fingerprint, params


def plan(project: str, directory: Path) -> dict:
    from google.cloud import bigquery

    client = bigquery.Client(project=project)
    queries = []
    for name, sql, fingerprint, parameters in _specs(directory):
        job = client.query(
            sql,
            job_config=bigquery.QueryJobConfig(
                dry_run=True,
                use_query_cache=False,
                query_parameters=parameters,
            ),
        )
        size = int(job.total_bytes_processed or 0)
        queries.append(
            {
                "table": name,
                "sql": sql,
                "query_sha256": fingerprint,
                "estimated_bytes": size,
                "within_limit": size <= MAX_BYTES,
            }
        )
    return {
        "project": project,
        "dry_run": True,
        "maximum_bytes_per_query": MAX_BYTES,
        "source_manifest_sha256": digest(directory / "import-manifest.json"),
        "queries": queries,
        "total_gib": sum(q["estimated_bytes"] for q in queries) / 2**30,
    }


def _write_manifest(path: Path, value: dict) -> None:
    partial = path.with_suffix(".json.partial")
    partial.write_text(json.dumps(value, indent=2) + "\n")
    partial.replace(path)


def _progress(message: str) -> None:
    print(message, flush=True)


def download(
    project: str, directory: Path, out_dir: Path, *, progress=_progress, storage_api: bool = True
) -> dict:
    """Dry-run each query, stream Arrow batches and retain verified provenance.

    Only existing outputs matching both the query/input binding and checksum are
    reused. Missing measured attributes are never synthesized.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq
    from google.cloud import bigquery

    client = bigquery.Client(project=project)
    if not verify_import(directory)["passed"]:
        raise ValueError("source import integrity check failed before BigQuery execution")
    source_hash = digest(directory / "import-manifest.json")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "manifest.json"
    manifest = (
        json.loads(path.read_text())
        if path.exists()
        else {
            "version": 1,
            "source_manifest_sha256": source_hash,
            "project": project,
            "files": {},
        }
    )
    if manifest["source_manifest_sha256"] != source_hash:
        raise ValueError("supplements belong to a different source import")
    for name, sql, fingerprint, parameters in _specs(directory):
        target = out_dir / f"{name}.parquet"
        existing = manifest["files"].get(name)
        if target.exists():
            if (
                not existing
                or existing["query_sha256"] != fingerprint
                or digest(target) != existing["sha256"]
            ):
                raise ValueError(f"unverified existing supplement: {target}")
            progress(f"Reusing verified {name}")
            continue
        estimate = client.query(
            sql,
            job_config=bigquery.QueryJobConfig(
                dry_run=True,
                use_query_cache=False,
                query_parameters=parameters,
            ),
        )
        estimated = int(estimate.total_bytes_processed or 0)
        if estimated > MAX_BYTES:
            raise ValueError(f"{name} estimates {estimated} bytes, above limit {MAX_BYTES}")
        progress(f"Downloading {name}; estimated scan {estimated / 2**30:.3f} GiB")
        pending = manifest.setdefault("jobs", {}).get(name)
        if pending:
            if pending["query_sha256"] != fingerprint:
                raise ValueError(f"pending job belongs to a different query: {name}")
            job = client.get_job(pending["job_id"], location=pending.get("location"))
        else:
            job = client.query(
                sql,
                job_config=bigquery.QueryJobConfig(
                    maximum_bytes_billed=MAX_BYTES,
                    query_parameters=parameters,
                ),
            )
        result = job.result(page_size=50_000)
        manifest["jobs"][name] = {
            "job_id": job.job_id,
            "location": getattr(job, "location", None),
            "query_sha256": fingerprint,
            "bytes_billed": int(job.total_bytes_billed or 0),
        }
        _write_manifest(path, manifest)
        partial = target.with_suffix(".parquet.partial")
        writer = None
        resources = ExitStack()
        rows = 0
        try:
            if storage_api:
                from google.cloud import bigquery_storage

                storage = resources.enter_context(bigquery_storage.BigQueryReadClient())
                batches = result.to_arrow_iterable(
                    bqstorage_client=storage, max_stream_count=2, max_queue_size=2
                )
            else:
                batches = result.to_arrow_iterable()
            for batch in batches:
                if writer is None:
                    writer = pq.ParquetWriter(partial, batch.schema, compression="zstd")
                writer.write_table(pa.Table.from_batches([batch]))
                rows += batch.num_rows
            if not rows:
                raise ValueError(f"BigQuery returned no rows for required supplement {name}")
        finally:
            if writer is not None:
                writer.close()
            resources.close()
        partial.replace(target)
        manifest["files"][name] = {
            "path": target.name,
            "sha256": digest(target),
            "rows": rows,
            "query_sha256": fingerprint,
            "sql": sql,
            "job_id": job.job_id,
            "estimated_bytes": estimated,
            "bytes_billed": int(job.total_bytes_billed or 0),
        }
        _write_manifest(path, manifest)
        progress(f"Saved {name}: {rows:,} rows")
    return manifest

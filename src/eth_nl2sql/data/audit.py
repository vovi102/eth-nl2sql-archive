"""Verify and profile the imported LuanVan CSV subset without changing it."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb

from eth_nl2sql.store.build import RAW_SCHEMAS

IMPORT_FILES = (
    "blocks.csv",
    "contracts.csv",
    "entities.csv",
    "token_transfers.csv",
    "transactions.csv",
    "manifest.json",
)
KEYS = {
    "blocks": ("number",),
    "contracts": ("address", "block_timestamp"),
    "entities": ("address",),
    "token_transfers": ("transaction_hash", "log_index"),
    "transactions": ("hash",),
}
TIMESTAMPS = {
    "blocks": "timestamp",
    "contracts": "block_timestamp",
    "token_transfers": "block_timestamp",
    "transactions": "block_timestamp",
}


def _sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _empty(name: str) -> str:
    column = _quote(name)
    return f"({column} IS NULL OR TRIM({column}) = '')"


def _issue(report: dict, severity: str, code: str, detail: str, file: str | None = None):
    report["issues"].append({"severity": severity, "code": code, "file": file, "detail": detail})


def _has_errors(report: dict) -> bool:
    return any(issue["severity"] == "error" for issue in report["issues"])


def _period(value: dict) -> tuple[date, date]:
    start, end = date.fromisoformat(value["start"]), date.fromisoformat(value["end"])
    if end < start:
        raise ValueError("data period end precedes start")
    return start, end


def _read_manifest(directory: Path, report: dict) -> dict | None:
    path = directory / "import-manifest.json"
    try:
        payload = path.read_bytes()
        manifest = json.loads(payload)
        if (
            not isinstance(manifest, dict)
            or type(manifest.get("version")) is not int
            or manifest["version"] != 1
        ):
            raise ValueError("expected an import manifest with version 1")
        _period(manifest["data_period_from_source_manifest"])
        files = manifest["files"]
        if not isinstance(files, list):
            raise ValueError("files must be a list")
        names = []
        for record in files:
            # Only known basenames are used. Historical serialized project/source
            # paths are metadata, so the import remains portable after relocation.
            name = Path(record["path"]).name
            names.append(name)
            if name not in IMPORT_FILES:
                raise ValueError(f"unexpected manifest file: {name}")
            if type(record["bytes"]) is not int or record["bytes"] < 0:
                raise ValueError(f"invalid byte count for {name}")
            if not re.fullmatch(r"[0-9a-f]{64}", record["sha256"]):
                raise ValueError(f"invalid SHA-256 for {name}")
            rows = record.get("rows_from_source_manifest")
            if rows is not None and (type(rows) is not int or rows < 0):
                raise ValueError(f"invalid expected row count for {name}")
            if name.endswith(".csv"):
                columns = record["columns"]
                if (
                    not isinstance(columns, list)
                    or not columns
                    or any(not isinstance(c, str) or not c for c in columns)
                    or len(set(columns)) != len(columns)
                ):
                    raise ValueError(f"invalid columns for {name}")
        if len(names) != len(set(names)) or set(names) != set(IMPORT_FILES):
            raise ValueError("manifest must list every expected file exactly once")
        if manifest["total_bytes"] != sum(record["bytes"] for record in files):
            raise ValueError("total_bytes does not match file byte counts")
        report["import_manifest_sha256"] = hashlib.sha256(payload).hexdigest()
        return manifest
    except (OSError, ValueError, KeyError, TypeError) as exc:
        _issue(report, "error", "invalid_manifest", str(exc), path.name)
        return None


def _verify_files(directory: Path, manifest: dict, report: dict) -> None:
    for record in manifest["files"]:
        name = Path(record["path"]).name
        path = directory / name
        observed = {"name": name, "expected_bytes": record["bytes"], "verified": False}
        report["files"].append(observed)
        try:
            observed["bytes"] = path.stat().st_size
            observed["sha256"] = _sha256(path)
            if observed["bytes"] != record["bytes"]:
                _issue(report, "error", "size_mismatch", "file size differs from manifest", name)
            if observed["sha256"] != record["sha256"]:
                _issue(report, "error", "checksum_mismatch", "SHA-256 differs from manifest", name)
            if name.endswith(".csv"):
                with path.open(newline="", encoding="utf-8-sig") as handle:
                    observed["columns"] = next(csv.reader(handle), [])
                if observed["columns"] != record["columns"]:
                    _issue(
                        report, "error", "header_mismatch", "CSV header differs from manifest", name
                    )
            observed["verified"] = not any(
                issue["severity"] == "error" and issue["file"] == name for issue in report["issues"]
            )
        except (OSError, UnicodeError, csv.Error) as exc:
            _issue(report, "error", "unreadable_file", str(exc), name)


def _duplicates(con: duckdb.DuckDBPyConnection, columns: list | tuple, where: str = "TRUE"):
    grouping = ", ".join(_quote(column) for column in columns)
    return con.execute(
        "SELECT COUNT(*), COALESCE(SUM(n - 1), 0)::BIGINT FROM "
        f"(SELECT COUNT(*) AS n FROM audit_rows WHERE {where} "
        f"GROUP BY {grouping} HAVING COUNT(*) > 1)"
    ).fetchone()


def _timestamp_profile(con: duckdb.DuckDBPyConnection, table: str, start: date, end: date) -> dict:
    column = _quote(TIMESTAMPS[table])
    stamp = f"TRY_CAST({column} AS TIMESTAMPTZ)"
    following = end + timedelta(days=1)
    lower_bound = "FALSE" if table == "contracts" else f"{stamp} < ?::TIMESTAMPTZ"
    params = [following] if table == "contracts" else [start, following]
    low, high, invalid, outside = con.execute(
        f"SELECT MIN({stamp}), MAX({stamp}), "
        f"COUNT(*) FILTER (WHERE {stamp} IS NULL), "
        f"COUNT(*) FILTER (WHERE {lower_bound} OR {stamp} >= ?::TIMESTAMPTZ) FROM audit_rows",
        params,
    ).fetchone()
    days = con.execute(
        f"SELECT CAST({stamp} AS DATE) AS day, COUNT(*) FROM audit_rows "
        f"WHERE {stamp} >= ?::TIMESTAMPTZ AND {stamp} < ?::TIMESTAMPTZ "
        "GROUP BY day ORDER BY day",
        [start, following],
    ).fetchall()
    daily = {day.isoformat(): count for day, count in days}
    expected = [(start + timedelta(days=n)).isoformat() for n in range((end - start).days + 1)]
    return {
        "column": TIMESTAMPS[table],
        "min_utc": low.isoformat() if low else None,
        "max_utc": high.isoformat() if high else None,
        "invalid_or_missing": invalid,
        "outside_expected_period": outside,
        "window_rule": "before_end_exclusive" if table == "contracts" else "within_period",
        "daily_rows_in_period": daily,
        "missing_days": [] if table == "contracts" else [d for d in expected if d not in daily],
    }


def _profile(
    con: duckdb.DuckDBPyConnection, path: Path, record: dict, start: date, end: date
) -> dict:
    columns = record["columns"]
    con.execute("DROP TABLE IF EXISTS audit_rows")
    con.execute(
        "CREATE TEMP TABLE audit_rows AS SELECT * FROM read_csv(?, header=true, columns=?, "
        "auto_detect=false, strict_mode=true, null_padding=false)",
        [str(path), dict.fromkeys(columns, "VARCHAR")],
    )
    expressions = ["COUNT(*)"] + [f"COUNT(*) FILTER (WHERE {_empty(c)})" for c in columns]
    counts = con.execute(f"SELECT {', '.join(expressions)} FROM audit_rows").fetchone()
    table = path.stem
    keys = KEYS[table]
    missing_keys = sorted(set(keys) - set(columns))
    if missing_keys:
        raise ValueError(f"missing identity columns: {missing_keys}")
    valid_key = " AND ".join(f"NOT {_empty(key)}" for key in keys)
    null_keys = con.execute(f"SELECT COUNT(*) FROM audit_rows WHERE NOT ({valid_key})").fetchone()[
        0
    ]
    groups, extra_keys = _duplicates(con, keys, valid_key)
    _, extra_rows = _duplicates(con, columns)
    addresses = [c for c in columns if c == "address" or c.endswith("_address")]
    invalid_addresses = {
        c: con.execute(
            f"SELECT COUNT(*) FROM audit_rows WHERE NOT {_empty(c)} "
            f"AND NOT regexp_full_match({_quote(c)}, '0x[0-9a-fA-F]{{40}}')"
        ).fetchone()[0]
        for c in addresses
    }
    profile = {
        "rows": counts[0],
        "expected_rows": record.get("rows_from_source_manifest"),
        "null_or_blank_by_column": dict(zip(columns, counts[1:], strict=True)),
        "identity_columns": list(keys),
        "rows_with_missing_identity": null_keys,
        "duplicate_key_groups": groups,
        "duplicate_key_extra_rows": extra_keys,
        "duplicate_full_extra_rows": extra_rows,
        "invalid_addresses": invalid_addresses,
        "missing_columns_for_current_store": sorted(set(RAW_SCHEMAS.get(table, {})) - set(columns)),
    }
    if table in TIMESTAMPS:
        if TIMESTAMPS[table] not in columns:
            raise ValueError(f"missing timestamp column: {TIMESTAMPS[table]}")
        profile["timestamps"] = _timestamp_profile(con, table, start, end)
    if table == "transactions" and "tier" in columns:
        profile["tier_counts"] = dict(
            con.execute(
                "SELECT tier, COUNT(*) FROM audit_rows GROUP BY tier ORDER BY tier"
            ).fetchall()
        )
    return profile


def _quality_issues(report: dict, table: str, profile: dict) -> None:
    name = f"{table}.csv"
    expected = profile["expected_rows"]
    if expected is not None and profile["rows"] != expected:
        _issue(
            report,
            "error",
            "row_count_mismatch",
            f"expected {expected}, got {profile['rows']}",
            name,
        )
    for field in ("rows_with_missing_identity", "duplicate_key_extra_rows"):
        if profile[field]:
            _issue(report, "error", field, f"{profile[field]} rows", name)
    if profile["rows"] == 0:
        _issue(report, "error", "empty_table", "CSV has no data rows", name)
    for column, count in profile["invalid_addresses"].items():
        if count:
            _issue(report, "error", "invalid_address", f"{column}: {count} invalid addresses", name)
    timestamps = profile.get("timestamps", {})
    for field in ("invalid_or_missing", "outside_expected_period"):
        if timestamps.get(field):
            _issue(report, "error", field, f"{timestamps[field]} timestamps", name)
    if timestamps.get("missing_days"):
        _issue(report, "warning", "missing_days", ", ".join(timestamps["missing_days"]), name)
    if profile["missing_columns_for_current_store"]:
        _issue(
            report,
            "warning",
            "missing_store_columns",
            ", ".join(profile["missing_columns_for_current_store"]),
            name,
        )


def verify_import(directory: Path, *, progress: Callable[[str], None] | None = None) -> dict:
    """Verify manifest/file integrity without rescanning CSV data quality."""
    directory = directory.resolve()
    report = {
        "version": 1,
        "directory": str(directory),
        "integrity_ok": False,
        "quality_ok": None,
        "passed": False,
        "store_schema_complete": False,
        "full_snapshot_verified": False,
        "files": [],
        "tables": {},
        "issues": [],
    }
    manifest = _read_manifest(directory, report)
    if manifest is None:
        return report
    report["scope"] = manifest.get("scope", "unspecified")
    report["expected_period_inclusive"] = manifest["data_period_from_source_manifest"]
    if progress:
        progress("Checking file sizes, SHA-256 and CSV headers")
    _verify_files(directory, manifest, report)
    report["integrity_ok"] = not _has_errors(report)
    if not report["integrity_ok"]:
        return report
    try:
        source = json.loads((directory / "manifest.json").read_text())
        if not isinstance(source, dict) or not isinstance(source.get("rows"), dict):
            raise ValueError("source manifest must have a rows object")
        if not isinstance(source.get("dictionary", {}), dict):
            raise ValueError("source manifest dictionary must be an object")
        if any(type(n) is not int or n < 0 for n in source["rows"].values()):
            raise ValueError("source manifest row counts must be nonnegative integers")
        if source["data_period"] != manifest["data_period_from_source_manifest"]:
            raise ValueError("source and import manifest data periods differ")
        for record in manifest["files"]:
            name = Path(record["path"]).name
            if record.get("rows_from_source_manifest") != source.get("rows", {}).get(name):
                raise ValueError(f"source and import manifest row counts differ: {name}")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        _issue(report, "error", "source_manifest_mismatch", str(exc), "manifest.json")
        report["integrity_ok"] = False
        return report
    report["passed"] = True
    return report


def audit_import(directory: Path, *, progress: Callable[[str], None] | None = None) -> dict:
    """Return integrity, full CSV profiles and store compatibility separately."""
    directory = directory.resolve()
    report = verify_import(directory, progress=progress)
    if not report["passed"]:
        return report
    manifest = json.loads((directory / "import-manifest.json").read_text())
    source = json.loads((directory / "manifest.json").read_text())
    start, end = _period(manifest["data_period_from_source_manifest"])
    with TemporaryDirectory(prefix="eth-nl2sql-audit-") as temporary:
        con = duckdb.connect(
            config={"threads": 2, "memory_limit": "512MB", "temp_directory": temporary}
        )
        try:
            con.execute("SET TimeZone='UTC'")
            for record in manifest["files"]:
                name = Path(record["path"]).name
                if not name.endswith(".csv"):
                    continue
                if progress:
                    progress(f"Profiling every row of {name}")
                try:
                    profile = _profile(con, directory / name, record, start, end)
                    report["tables"][Path(name).stem] = profile
                    _quality_issues(report, Path(name).stem, profile)
                except (duckdb.Error, ValueError) as exc:
                    _issue(report, "error", "csv_profile_failed", str(exc)[:1000], name)
        finally:
            con.close()
    report["missing_tables_for_current_store"] = sorted(set(RAW_SCHEMAS) - set(report["tables"]))
    report["store_schema_complete"] = not report["missing_tables_for_current_store"] and all(
        not p["missing_columns_for_current_store"] for p in report["tables"].values()
    )
    if report["missing_tables_for_current_store"]:
        _issue(
            report,
            "warning",
            "missing_store_tables",
            ", ".join(report["missing_tables_for_current_store"]),
        )
    dictionary_count = source.get("dictionary", {}).get("address_count")
    entity_count = report["tables"].get("entities", {}).get("rows")
    if (
        dictionary_count is not None
        and entity_count is not None
        and dictionary_count != entity_count
    ):
        _issue(
            report,
            "warning",
            "historical_dictionary_count_differs",
            f"source manifest dictionary: {dictionary_count}; entities.csv: {entity_count}",
            "entities.csv",
        )
    _issue(
        report,
        "warning",
        "full_snapshot_not_verified",
        "The imported data is a declared subset; date coverage does not prove full-chain coverage.",
    )
    report["quality_ok"] = not _has_errors(report)
    report["passed"] = report["integrity_ok"] and report["quality_ok"]
    return report


def render_report(report: dict) -> str:
    """Render a concise human-readable companion to the complete JSON profile."""
    lines = [
        "# T02 — Kiểm tra dữ liệu CSV nhập từ LuanVan",
        "",
        f"Thư mục: `{report['directory']}`.",
        "",
        f"- File khớp manifest: **{report['integrity_ok']}**.",
        f"- Chất lượng dữ liệu đạt các kiểm tra: **{report['quality_ok']}**.",
        f"- Đủ schema cho store hiện tại: **{report['store_schema_complete']}**.",
        "- Snapshot đầy đủ đã được chứng minh: **False**.",
        "",
        "Null/blank là ô NULL, rỗng hoặc chỉ có khoảng trắng; không phải mọi ô trống đều là lỗi.",
        "Khóa thiếu hoặc trùng, địa chỉ sai định dạng, số dòng lệch và timestamp sai là lỗi.",
        "Thiếu cột/bảng cho store, ngày vắng trong dữ liệu lấy mẫu là cảnh báo.",
        "",
        "## Số dòng và trùng lặp",
        "",
        "| Bảng | Dòng thực tế | Dòng theo nguồn | Khóa "
        "| Dòng trùng khóa dư | Dòng trùng toàn bộ dư |",
        "|---|---:|---:|---|---:|---:|",
    ]
    for table, profile in sorted(report["tables"].items()):
        expected = profile["expected_rows"]
        lines.append(
            f"| {table} | {profile['rows']:,} | {expected if expected is not None else '—'} "
            f"| {', '.join(profile['identity_columns'])} | {profile['duplicate_key_extra_rows']} "
            f"| {profile['duplicate_full_extra_rows']} |"
        )
    lines += [
        "",
        "## Timestamp (UTC)",
        "",
        "| Bảng | Nhỏ nhất | Lớn nhất | Sai/thiếu | Ngoài kỳ | Ngày vắng |",
        "|---|---|---|---:|---:|---|",
    ]
    for table, profile in sorted(report["tables"].items()):
        stamp = profile.get("timestamps")
        if stamp:
            missing = ", ".join(stamp["missing_days"]) or "—"
            lines.append(
                f"| {table} | {stamp['min_utc']} | {stamp['max_utc']} "
                f"| {stamp['invalid_or_missing']} | {stamp['outside_expected_period']} "
                f"| {missing} |"
            )
    lines += [
        "",
        "Contract cũ được phép nằm trước kỳ; mọi timestamp phải trước ngày kết thúc + 1 (UTC).",
        "Khoảng ngày trong manifest được hiểu là bao gồm cả ngày đầu và ngày cuối.",
        "Số dòng theo từng ngày được ghi trong báo cáo JSON.",
        "",
        "## Null/blank",
        "",
        "| Bảng | Cột | Số ô |",
        "|---|---|---:|",
    ]
    for table, profile in sorted(report["tables"].items()):
        nonzero = {c: n for c, n in profile["null_or_blank_by_column"].items() if n}
        for column, count in nonzero.items():
            lines.append(f"| {table} | {column} | {count:,} |")
        if not nonzero:
            lines.append(f"| {table} | Không có | 0 |")
    lines += ["", "## Vấn đề và giới hạn", ""]
    for issue in report["issues"]:
        location = f" ({issue['file']})" if issue["file"] else ""
        detail = issue["detail"].replace("\n", " ")
        lines.append(f"- **{issue['severity']} / {issue['code']}**{location}: {detail}")
    return "\n".join(lines) + "\n"

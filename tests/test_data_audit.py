"""Audit small real CSV imports, including corruption and data quality failures."""

import csv
import hashlib
import json
from pathlib import Path

import pytest

from eth_nl2sql.cli import main
from eth_nl2sql.data.audit import IMPORT_FILES, audit_import

A, B = "0x" + "1" * 40, "0x" + "2" * 40
PERIOD = {"start": "2026-05-31", "end": "2026-06-02"}


def _write_csv(path: Path, columns: list[str], rows: list[list]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)


def _seal(directory: Path, *, update_counts: bool = True) -> None:
    source_path = directory / "manifest.json"
    source = json.loads(source_path.read_text())
    csv_data = {}
    for path in directory.glob("*.csv"):
        with path.open(newline="") as handle:
            columns, *rows = list(csv.reader(handle))
        csv_data[path.name] = (columns, rows)
        if update_counts and path.stem != "entities":
            source["rows"][path.name] = len(rows)
    source_path.write_text(json.dumps(source))
    records = []
    for name in IMPORT_FILES:
        path = directory / name
        record = {
            "path": f"old/project/data/{name}",
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        if name in csv_data:
            record["columns"] = csv_data[name][0]
            record["rows_from_source_manifest"] = source["rows"].get(name)
        records.append(record)
    (directory / "import-manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "data_period_from_source_manifest": PERIOD,
                "scope": "sampled_subset",
                "complete_snapshot_for_current_store": False,
                "files": records,
                "total_bytes": sum(record["bytes"] for record in records),
            }
        )
    )


@pytest.fixture()
def imported(tmp_path):
    directory = tmp_path / "import"
    directory.mkdir()
    _write_csv(
        directory / "blocks.csv",
        ["number", "hash", "timestamp"],
        [
            ["1", "b1", "2026-05-31T12:00:00+00:00"],
            ["2", "b2", "2026-06-02T12:00:00+00:00"],
        ],
    )
    _write_csv(
        directory / "contracts.csv",
        ["address", "block_timestamp"],
        [
            [A, "2016-01-01T00:00:00+00:00"],
        ],
    )
    _write_csv(directory / "entities.csv", ["address", "owner"], [[A, "Owner, A"], [B, "B"]])
    _write_csv(
        directory / "token_transfers.csv",
        [
            "transaction_hash",
            "log_index",
            "from_address",
            "to_address",
            "block_timestamp",
        ],
        [["tx1", "0", A, B, "2026-05-31T12:00:00+00:00"]],
    )
    _write_csv(
        directory / "transactions.csv",
        [
            "hash",
            "from_address",
            "to_address",
            "block_timestamp",
            "tier",
        ],
        [
            ["tx1", A, "", "2026-05-31T12:00:00+00:00", "tier1"],
            ["tx2", B, A, "2026-06-02T12:00:00+00:00", "tier2"],
        ],
    )
    (directory / "manifest.json").write_text(
        json.dumps(
            {
                "data_period": PERIOD,
                "rows": {},
                "dictionary": {"address_count": 1},
            }
        )
    )
    _seal(directory)
    return directory


def _rewrite_transactions(directory: Path, change, *, update_counts=True):
    path = directory / "transactions.csv"
    with path.open(newline="") as handle:
        columns, *rows = list(csv.reader(handle))
    change(rows)
    _write_csv(path, columns, rows)
    _seal(directory, update_counts=update_counts)


def test_audit_counts_nulls_duplicates_utc_coverage_and_store_gaps(imported, monkeypatch, tmp_path):
    before = {p.name: p.read_bytes() for p in imported.iterdir()}
    monkeypatch.chdir(tmp_path)
    report = audit_import(imported)
    assert report["passed"] and report["integrity_ok"] and report["quality_ok"]
    assert not report["store_schema_complete"] and not report["full_snapshot_verified"]
    assert report["missing_tables_for_current_store"] == ["amended_tokens"]
    tx = report["tables"]["transactions"]
    assert tx["rows"] == tx["expected_rows"] == 2
    assert tx["null_or_blank_by_column"]["to_address"] == 1
    assert tx["duplicate_key_extra_rows"] == tx["duplicate_full_extra_rows"] == 0
    assert tx["timestamps"]["missing_days"] == ["2026-06-01"]
    assert tx["timestamps"]["daily_rows_in_period"] == {"2026-05-31": 1, "2026-06-02": 1}
    assert tx["tier_counts"] == {"tier1": 1, "tier2": 1}
    assert "receipt_gas_used" in tx["missing_columns_for_current_store"]
    assert report["tables"]["contracts"]["timestamps"]["outside_expected_period"] == 0
    assert report["tables"]["contracts"]["timestamps"]["missing_days"] == []
    assert report["tables"]["entities"]["rows"] == 2
    assert "historical_dictionary_count_differs" in {i["code"] for i in report["issues"]}
    assert before == {p.name: p.read_bytes() for p in imported.iterdir()}


@pytest.mark.parametrize(
    "damage,code", [("delete", "unreadable_file"), ("tamper", "checksum_mismatch")]
)
def test_missing_or_changed_file_fails_before_profiling(imported, damage, code):
    path = imported / "blocks.csv"
    if damage == "delete":
        path.unlink()
    else:
        path.write_bytes(path.read_bytes().replace(b"b1", b"b9"))
    report = audit_import(imported)
    assert not report["passed"] and not report["integrity_ok"]
    assert report["tables"] == {} and report["quality_ok"] is None
    assert code in {i["code"] for i in report["issues"]}


@pytest.mark.parametrize(
    "damage", ["json", "duplicate", "omitted", "total", "version", "bytes", "sha"]
)
def test_invalid_manifest_is_reported_without_traceback(imported, damage):
    path = imported / "import-manifest.json"
    manifest = json.loads(path.read_text())
    if damage == "duplicate":
        manifest["files"].append(manifest["files"][0])
    elif damage == "omitted":
        manifest["files"].pop()
    elif damage == "total":
        manifest["total_bytes"] += 1
    elif damage == "version":
        manifest["version"] = 99
    elif damage == "bytes":
        manifest["files"][0]["bytes"] = "wrong"
    elif damage == "sha":
        manifest["files"][0]["sha256"] = "not-a-checksum"
    path.write_text("{" if damage == "json" else json.dumps(manifest))
    report = audit_import(imported)
    assert not report["passed"]
    assert report["issues"][0]["code"] == "invalid_manifest"


@pytest.mark.parametrize("identical", [False, True])
def test_duplicate_keys_and_full_rows_are_counted_separately(imported, identical):
    def change(rows):
        extra = rows[0].copy()
        if not identical:
            extra[-1] = "tier2"
        rows.append(extra)

    _rewrite_transactions(imported, change)
    report = audit_import(imported)
    tx = report["tables"]["transactions"]
    assert tx["duplicate_key_groups"] == tx["duplicate_key_extra_rows"] == 1
    assert tx["duplicate_full_extra_rows"] == int(identical)
    assert report["integrity_ok"] and not report["quality_ok"] and not report["passed"]


@pytest.mark.parametrize(
    "column,value,code",
    [
        (0, "", "rows_with_missing_identity"),
        (1, "0xBAD", "invalid_address"),
        (3, "not-a-date", "invalid_or_missing"),
        (3, "", "invalid_or_missing"),
        (3, "2026-06-03T00:00:00+00:00", "outside_expected_period"),
        (3, "2026-05-31T00:30:00+01:00", "outside_expected_period"),
    ],
)
def test_invalid_values_fail_data_quality_even_with_valid_checksums(imported, column, value, code):
    _rewrite_transactions(imported, lambda rows: rows[0].__setitem__(column, value))
    report = audit_import(imported)
    assert report["integrity_ok"] and not report["quality_ok"]
    assert code in {i["code"] for i in report["issues"]}


def test_timestamp_offsets_are_checked_in_utc(imported):
    _rewrite_transactions(
        imported, lambda rows: rows[1].__setitem__(3, "2026-06-03T00:30:00+01:00")
    )
    report = audit_import(imported)
    assert report["passed"]
    assert report["tables"]["transactions"]["timestamps"]["max_utc"] == "2026-06-02T23:30:00+00:00"


def test_actual_row_count_is_compared_to_historical_count(imported):
    _rewrite_transactions(imported, lambda rows: rows.pop(), update_counts=False)
    report = audit_import(imported)
    assert report["integrity_ok"] and not report["quality_ok"]
    assert "row_count_mismatch" in {i["code"] for i in report["issues"]}


def test_malformed_csv_is_not_silently_padded_or_skipped(imported):
    _rewrite_transactions(imported, lambda rows: rows[0].append("extra field"))
    report = audit_import(imported)
    assert report["integrity_ok"] and not report["quality_ok"]
    assert "csv_profile_failed" in {i["code"] for i in report["issues"]}


@pytest.mark.parametrize("rows", [None, [], {"blocks.csv": -1}])
def test_invalid_source_metadata_returns_a_structured_error(imported, rows):
    source = imported / "manifest.json"
    source.write_text(json.dumps({"data_period": PERIOD, "rows": rows}))
    manifest_path = imported / "import-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    record = next(r for r in manifest["files"] if r["path"].endswith("/manifest.json"))
    record["bytes"] = source.stat().st_size
    record["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    manifest["total_bytes"] = sum(r["bytes"] for r in manifest["files"])
    manifest_path.write_text(json.dumps(manifest))
    report = audit_import(imported)
    assert not report["passed"] and not report["integrity_ok"]
    assert report["issues"][0]["code"] == "source_manifest_mismatch"


def test_header_and_historical_row_metadata_are_checked(imported):
    manifest_path = imported / "import-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    record = next(r for r in manifest["files"] if r["path"].endswith("/blocks.csv"))
    record["columns"][0] = "wrong_header"
    manifest_path.write_text(json.dumps(manifest))
    assert "header_mismatch" in {i["code"] for i in audit_import(imported)["issues"]}
    _seal(imported)
    manifest = json.loads(manifest_path.read_text())
    record = next(r for r in manifest["files"] if r["path"].endswith("/blocks.csv"))
    record["rows_from_source_manifest"] += 1
    manifest_path.write_text(json.dumps(manifest))
    assert "source_manifest_mismatch" in {i["code"] for i in audit_import(imported)["issues"]}


@pytest.mark.parametrize("collision", ["input", "reports"])
def test_cli_refuses_to_overwrite_raw_data_or_mix_report_formats(imported, tmp_path, collision):
    before = {p.name: p.read_bytes() for p in imported.iterdir()}
    out = imported / "transactions.csv" if collision == "input" else tmp_path / "report"
    report = tmp_path / "report"
    with pytest.raises(SystemExit):
        main(
            ["check-data", "--directory", str(imported), "--out", str(out), "--report", str(report)]
        )
    assert before == {p.name: p.read_bytes() for p in imported.iterdir()}


@pytest.mark.parametrize("bad_file", [False, True])
def test_cli_writes_json_and_markdown_and_returns_failure_for_bad_input(
    imported, tmp_path, capsys, bad_file
):
    out, report_path = tmp_path / "results" / "audit.json", tmp_path / "results" / "audit.md"
    if bad_file:
        (imported / "blocks.csv").unlink()
    args = [
        "check-data",
        "--directory",
        str(imported),
        "--out",
        str(out),
        "--report",
        str(report_path),
    ]
    if bad_file:
        with pytest.raises(SystemExit) as error:
            main(args)
        assert error.value.code == 1
    else:
        main(args)
    summary = json.loads(capsys.readouterr().out)
    assert summary["passed"] is not bad_file
    assert json.loads(out.read_text())["passed"] is not bad_file
    assert "T02" in report_path.read_text()

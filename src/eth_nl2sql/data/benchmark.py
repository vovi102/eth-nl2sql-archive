"""Audit draft benchmarks; release requires human review and a full store."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import duckdb
from sqlglot.errors import SqlglotError

from eth_nl2sql.config import CATALOG_PATH, read_jsonl, sha256_file, write_json
from eth_nl2sql.data.annotations import (
    GROUPS,
    PROPERTY_COUNTS,
    SCHEMA_PATH,
    audit_annotations,
    structure_errors,
)
from eth_nl2sql.data.dataset_audit import owner_support
from eth_nl2sql.data.entities import canonical_sql, split_audit
from eth_nl2sql.data.splits import DEVELOPMENT_SPLITS, split_paths
from eth_nl2sql.linking.dictionary import load_dictionary, normalize_phrase
from eth_nl2sql.store.execute import ExecutionError, execute
from eth_nl2sql.store.manifest import store_profile

BENCHMARK_FILES = ("test.jsonl", "annotations.jsonl", "reviews.jsonl")


def dependency_hashes(data_dir: Path, dictionary: Path) -> dict:
    paths = {
        "catalog": CATALOG_PATH,
        "annotation_schema": SCHEMA_PATH,
        **{
            f"split:{name}": path
            for name, path in split_paths(data_dir).items()
            if name in DEVELOPMENT_SPLITS
        },
        **{
            f"dictionary:{name}": dictionary / name
            for name in ("manifest.json", "entities.json", "aliases.json", "concepts.json")
        },
    }
    return {name: sha256_file(path) for name, path in paths.items()}


def draft_manifest(directory: Path, data_dir: Path, dictionary: Path) -> dict:
    existing = directory / "manifest.json"
    if existing.is_file():
        value = json.loads(existing.read_text())
        if not isinstance(value, dict):
            raise ValueError("manifest must be an object")
        if value.get("status") == "frozen":
            raise ValueError(
                "benchmark is already frozen; create a new version instead of overwriting"
            )
    return {
        "schema_version": 2,
        "benchmark_version": "v2",
        "status": "draft",
        "target_size": 100,
        "primary_counts": dict.fromkeys(GROUPS, 20),
        "property_counts": PROPERTY_COUNTS,
        "files": {name: sha256_file(directory / name) for name in BENCHMARK_FILES},
        "dependencies": dependency_hashes(data_dir, dictionary),
        "store": None,
        "frozen_at": None,
    }


def _read_rows(path: Path, issues: list[str]) -> list[dict]:
    try:
        return read_jsonl(path)
    except (OSError, ValueError) as exc:
        issues.append(f"{path.name}: {exc}")
        return []


def audit_benchmark(
    directory: Path, data_dir: Path, dictionary: Path, con: duckdb.DuckDBPyConnection | None = None
) -> dict:
    issues, blockers = [], []
    try:
        manifest = json.loads((directory / "manifest.json").read_text())
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be an object")
    except (OSError, ValueError) as exc:
        return {"passed": False, "release_ready": False, "issues": [str(exc)]}
    manifest_errors = structure_errors(manifest, "manifest")
    if manifest_errors:
        return {"passed": False, "release_ready": False, "issues": manifest_errors}
    if manifest.get("schema_version") != 2 or manifest.get("benchmark_version") != "v2":
        issues.append("unsupported benchmark/schema version")
    if manifest.get("status") not in {"draft", "frozen"}:
        issues.append("manifest status must be draft or frozen")
    if (
        manifest.get("target_size") != 100
        or manifest.get("primary_counts") != dict.fromkeys(GROUPS, 20)
        or manifest.get("property_counts") != PROPERTY_COUNTS
    ):
        issues.append("manifest quotas differ from the v2 protocol")
    hashes = manifest.get("files")
    if not isinstance(hashes, dict):
        hashes = {}
    if set(hashes) != set(BENCHMARK_FILES):
        issues.append("manifest must hash all benchmark data/annotation/review files")
    for name in BENCHMARK_FILES:
        path = directory / name
        if not path.is_file() or sha256_file(path) != hashes.get(name):
            issues.append(f"benchmark checksum mismatch or missing file: {name}")
    try:
        if manifest.get("dependencies") != dependency_hashes(data_dir, dictionary):
            issues.append(
                "dependency hashes differ (development splits, catalog/schema or dictionary)"
            )
        labels = load_dictionary(dictionary)
    except (OSError, ValueError) as exc:
        return {"passed": False, "release_ready": False, "issues": [*issues, str(exc)]}
    cases, annotations, reviews = (_read_rows(directory / name, issues) for name in BENCHMARK_FILES)
    structure = []
    for case in cases:
        errors = structure_errors(case, "case")
        if errors:
            structure.append(
                {"id": case.get("id") if isinstance(case, dict) else None, "errors": errors}
            )
    linking = audit_annotations(cases, annotations, reviews, labels)
    valid_cases = []
    for case in cases:
        if structure_errors(case, "case"):
            continue
        try:
            canonical_sql(case["sql"])
            valid_cases.append(case)
        except (ValueError, SqlglotError) as exc:
            issues.append(f"{case['id']}: invalid SQL: {exc}")
    splits = {
        name: _read_rows(path, issues)
        for name, path in split_paths(data_dir).items()
        if name in DEVELOPMENT_SPLITS
    }
    splits["test"] = valid_cases
    try:
        leakage = split_audit(splits)
    except (KeyError, TypeError, ValueError, SqlglotError) as exc:
        leakage = {"passed": False, "error": str(exc)}
    primary = Counter(c["primary_group"] for c in valid_cases)
    focus = Counter(
        c["property_focus"] for c in valid_cases if c["primary_group"] == "ambiguous_property"
    )
    if len(valid_cases) != 100 or len({canonical_sql(c["sql"]) for c in valid_cases}) != 100:
        blockers.append("requires 100 cases and 100 distinct canonical gold SQL queries")
    if dict(primary) != dict.fromkeys(GROUPS, 20):
        blockers.append("requires 20 cases in each primary group")
    if dict(focus) != PROPERTY_COUNTS:
        blockers.append("property focus must be direction=7, fact=7, address_role=6")
    if not linking["human_review_complete"]:
        blockers.append("independent human review is incomplete")
    annotation_by_id = {
        a["id"]: a for a in annotations if isinstance(a, dict) and isinstance(a.get("id"), str)
    }
    for case in valid_cases:
        group = case["primary_group"]
        start, end = case["window"]["start_date"], case["window"]["end_date"]
        if not "2026-05-31" <= start < end <= "2026-07-01":
            issues.append(f"{case['id']}: window must lie within the catalog UTC interval")
        if (group == "generic") != (case["subset"] == "generic"):
            issues.append(f"{case['id']}: subset differs from primary group")
        if group != "generic" and group not in case["specifics"]:
            issues.append(f"{case['id']}: primary group missing from specifics")
        if (group == "ambiguous_property") != (case["property_focus"] is not None):
            issues.append(f"{case['id']}: property_focus must apply to the property primary group")
        a = annotation_by_id.get(case["id"], {})
        if structure_errors(a, "annotation"):
            continue
        if "class_level" in case["specifics"] and not a["classes"]:
            issues.append(f"{case['id']}: class case requires a class annotation")
        if "class_level" in case["specifics"] and re.search(r"\bmajor\b", case["question"], re.I):
            issues.append(f"{case['id']}: undefined 'major' class scope is excluded from v2")
        if "multi_address" in case["specifics"] and not any(
            e["address_scope"] == "known_owner_addresses" and len(e["addresses"]) >= 2
            for e in a["entities"]
        ):
            issues.append(f"{case['id']}: multi-address case needs a complete owner address set")
        if "alias" in case["specifics"] and not any(
            e["owner"]
            and e["mention"]["text"].casefold() != e["owner"].casefold()
            and len(labels.phrases.get(normalize_phrase(e["mention"]["text"]), ())) == 1
            for e in a["entities"]
        ):
            issues.append(f"{case['id']}: alias case needs an unambiguous noncanonical alias")
        if case["property_focus"] and not a["properties"][case["property_focus"]]:
            issues.append(f"{case['id']}: missing annotation for property focus")
    profile = store_profile(con) if con is not None else manifest.get("store")
    if profile is not None and (
        not isinstance(profile.get("complete_snapshot"), bool)
        or not isinstance(profile.get("scope"), str)
        or not isinstance(profile.get("parquet_manifest_sha256"), str)
    ):
        issues.append(
            "store profile requires recorded scope, snapshot state and Parquet manifest hash"
        )
    if profile is None or not profile.get("complete_snapshot"):
        blockers.append(
            "full snapshot execution is required before freezing; sample is development only"
        )
    if profile and profile.get("labels_sha256") != sha256_file(dictionary / "entities.json"):
        issues.append("store labels differ from annotation dictionary")
    if manifest.get("store") is not None and manifest["store"] != profile:
        issues.append("store profile differs from the frozen manifest")
    gold = []
    if con is not None:
        for case in valid_cases:
            check = {"id": case["id"], "passed": True}
            try:
                result = execute(con, case["sql"])
                check.update(row_count=len(result.rows), empty=not result.rows)
                zero = len(result.rows) == 1 and all(v is None or v == 0 for v in result.rows[0])
                check["zero_aggregate"] = zero
                if (not result.rows or zero) and not (case.get("empty_reason") or "").strip():
                    raise ValueError("empty or zero/NULL result requires an explanation")
                a = annotation_by_id.get(case["id"], {})
                if "multi_address" in case["specifics"] and not structure_errors(a, "annotation"):
                    witnesses = []
                    for prop in a["properties"]["direction"]:
                        if not prop["target"].startswith("entity:"):
                            continue
                        index = int(prop["target"].split(":")[1])
                        if index >= len(a["entities"]):
                            continue
                        entity = a["entities"][index]
                        fact = a["properties"]["fact"]
                        if not entity["owner"] or fact not in {"transaction", "token_transfer"}:
                            continue
                        expected = {
                            "owners": [entity["owner"]],
                            "direction": prop["value"],
                            "fact": "transactions" if fact == "transaction" else "token_transfers",
                            "start_date": case["window"]["start_date"],
                            "end_date": case["window"]["end_date"],
                        }
                        witnesses.append(owner_support(con, expected))
                    check["multi_address_witnesses"] = witnesses
                    if not any(
                        w["active_addresses"] >= 2 and w["single_address_changes_answer"]
                        for w in witnesses
                    ):
                        raise ValueError("missing discriminating multi-address raw-table witness")
            except (ValueError, duckdb.Error, ExecutionError) as exc:
                check.update(passed=False, error=str(exc))
            gold.append(check)
    elif manifest.get("status") != "frozen":
        blockers.append("gold execution has not been checked")
    if manifest.get("status") == "frozen" and not manifest.get("frozen_at"):
        issues.append("frozen manifest requires a timestamp")
    passed = (
        not issues
        and not structure
        and linking["passed"]
        and leakage["passed"]
        and all(c["passed"] for c in gold)
    )
    return {
        "schema_version": 2,
        "passed": passed,
        "release_ready": passed and not blockers,
        "status": manifest.get("status"),
        "issues": issues,
        "release_blockers": blockers,
        "case_count": len(cases),
        "primary_counts": dict(primary),
        "property_counts": dict(focus),
        "structure": structure,
        "annotations": linking,
        "leakage": leakage,
        "store": profile,
        "gold": gold,
        "manifest_sha256": sha256_file(directory / "manifest.json"),
    }


def freeze_benchmark(
    directory: Path, data_dir: Path, dictionary: Path, con: duckdb.DuckDBPyConnection
) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text())
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    if manifest.get("status") != "draft":
        raise ValueError("benchmark is already frozen; create a new version instead of overwriting")
    report = audit_benchmark(directory, data_dir, dictionary, con)
    if not report["release_ready"]:
        raise ValueError(
            "benchmark is not release-ready: "
            + json.dumps(
                {
                    "issues": report["issues"],
                    "blockers": report.get("release_blockers", []),
                    "checks_passed": report["passed"],
                }
            )
        )
    manifest.update(status="frozen", frozen_at=datetime.now(UTC).isoformat(), store=report["store"])
    write_json(directory / "manifest.json", manifest)
    return manifest


def require_frozen(directory: Path, data_dir: Path, dictionary: Path) -> dict:
    """Prevent development commands from silently treating a draft as final test."""
    report = audit_benchmark(directory, data_dir, dictionary)
    if report.get("status") != "frozen" or not report.get("release_ready"):
        raise ValueError(
            "Final test v2 is not frozen and verified; use --split dev_eval. "
            + json.dumps(
                {"issues": report.get("issues"), "blockers": report.get("release_blockers")}
            )
        )
    return json.loads((directory / "manifest.json").read_text())

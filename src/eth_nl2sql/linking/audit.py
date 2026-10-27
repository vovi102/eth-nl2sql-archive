"""Offline dictionary checks and measured presence in a local store's raw tables."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pyarrow as pa

from eth_nl2sql.config import sha256_file
from eth_nl2sql.linking.dictionary import load_dictionary
from eth_nl2sql.linking.validation import read_dictionary
from eth_nl2sql.store.build import SNAPSHOT_END, SNAPSHOT_START
from eth_nl2sql.store.manifest import store_profile


def check_dictionary(directory: Path) -> dict:
    dictionary = load_dictionary(directory)
    rows, aliases, _ = read_dictionary(directory)
    owners = [t for t in dictionary.targets if t.kind == "owner"]
    operational = [t for t in owners if not t.is_token_owner]
    return {
        "passed": True,
        "files": {
            name: sha256_file(directory / name)
            for name in ("entities.json", "aliases.json", "concepts.json")
        },
        "addresses": len(rows),
        "owners": len(owners),
        "operational_owners": len(operational),
        "multi_address_owners": sum(len(t.addresses) > 1 for t in owners),
        "multi_address_operational_owners": sum(len(t.addresses) > 1 for t in operational),
        "aliases": len(aliases),
        "ambiguous_aliases": {
            phrase: values for phrase, values in aliases.items() if isinstance(values, list)
            and len(values) > 1
        },
        "categories": dict(sorted(Counter(r["category"] for r in rows).items())),
        "verified_dates": dict(sorted(Counter(r["verified_date"] for r in rows).items())),
    }


def dictionary_coverage(con: duckdb.DuckDBPyConnection, directory: Path) -> dict:
    """Count raw rows once per address/owner/category even when several roles match.

    The measured dictionary is registered independently of the store's loaded
    labels, so v2 can be profiled against a v1 store without changing the store.
    Presence includes zero-activity labels; metadata presence is reported apart
    from transaction/transfer activity. All activity uses the managed UTC window.
    """
    validation = check_dictionary(directory)
    rows, _, _ = read_dictionary(directory)
    addresses = {
        r["address"].lower(): {
            "address": r["address"].lower(), "owner": r["owner"], "category": r["category"],
            "address_role": r["address_role"],
        }
        for r in rows
    }
    owners = {
        r["owner"]: {"owner": r["owner"], "category": r["category"]} for r in rows
    }
    categories = {r["category"]: {"category": r["category"]} for r in rows}
    groups = {"addresses": addresses, "owners": owners, "categories": categories}
    totals = {}
    con.register("_dictionary_coverage_labels", pa.Table.from_pylist(list(addresses.values())))
    try:
        for table, columns in (
            ("transactions", ("from_address", "to_address")),
            ("token_transfers", ("from_address", "to_address", "token_address")),
        ):
            roles = [column.removesuffix("_address") for column in columns]
            mentions = ", ".join(
                f"('{role}', lower(raw.{col}))" for role, col in zip(roles, columns, strict=True)
            )
            counts = ", ".join(
                f"count(DISTINCT event_id) FILTER (WHERE role = '{role}') AS {role}_rows"
                for role in roles
            )
            bounds = [SNAPSHOT_START, SNAPSHOT_END]
            total = con.execute(
                f"SELECT count(*) FROM {table} WHERE block_timestamp >= ? AND block_timestamp < ?",
                bounds,
            ).fetchone()[0]
            result = con.execute(
                f"""WITH raw AS (
                    SELECT row_number() OVER () AS event_id, * FROM {table}
                    WHERE block_timestamp >= ? AND block_timestamp < ?
                ), matched AS (
                    SELECT raw.event_id, raw.block_timestamp, mention.role, labels.*
                    FROM raw CROSS JOIN LATERAL (VALUES {mentions}) AS mention(role, address)
                    JOIN _dictionary_coverage_labels labels ON labels.address = mention.address
                )
                SELECT CASE WHEN grouping(address) = 0 THEN 'addresses'
                            WHEN grouping(owner) = 0 THEN 'owners'
                            WHEN grouping(category) = 0 THEN 'categories'
                            ELSE 'summary' END AS level,
                       coalesce(address, owner, category) AS key,
                       count(DISTINCT event_id) AS any_rows, {counts},
                       min(block_timestamp), max(block_timestamp)
                FROM matched
                GROUP BY GROUPING SETS ((address), (owner), (category), ())""",
                bounds,
            ).fetchall()
            for level, key, any_rows, *rest in result:
                metrics = {f"{table}_any": any_rows}
                metrics.update({
                    f"{table}_{role}": n
                    for role, n in zip(roles, rest[:len(roles)], strict=True)
                })
                for field, stamp in zip(
                    ("first_seen", "last_seen"), rest[len(roles):], strict=True
                ):
                    metrics[f"{table}_{field}"] = stamp.isoformat() if stamp else None
                if level == "summary":
                    totals[table] = {
                        "rows": total, "matched_rows": any_rows,
                        "matched_fraction": any_rows / total if total else None,
                    }
                else:
                    groups[level][key].update(metrics)
            for values in groups.values():
                for entry in values.values():
                    for role in ["any", *roles]:
                        entry.setdefault(f"{table}_{role}", 0)
                    for field in ("first_seen", "last_seen"):
                        entry.setdefault(f"{table}_{field}", None)

        for name, table, column, condition, bounds in (
            ("contracts", "contracts", "address", "block_timestamp < ?", [SNAPSHOT_END]),
            ("token_metadata", "amended_tokens", "address", "TRUE", []),
            ("block_miner", "blocks", "miner", "timestamp >= ? AND timestamp < ?",
             [SNAPSHOT_START, SNAPSHOT_END]),
        ):
            observed = dict(con.execute(
                f"SELECT lower(raw.{column}), count(*) FROM {table} raw "
                f"JOIN _dictionary_coverage_labels labels ON lower(raw.{column}) = labels.address "
                f"WHERE {condition} GROUP BY 1",
                bounds,
            ).fetchall())
            for address, entry in addresses.items():
                entry[name] = observed.get(address, 0)
    finally:
        con.unregister("_dictionary_coverage_labels")

    by_owner = defaultdict(list)
    by_category = defaultdict(list)
    for entry in addresses.values():
        entry["activity_present"] = bool(entry["transactions_any"] or entry["token_transfers_any"])
        entry["present"] = entry["activity_present"] or any(
            entry[field] for field in ("contracts", "token_metadata", "block_miner")
        )
        by_owner[entry["owner"]].append(entry)
        by_category[entry["category"]].append(entry)
    for group, membership in ((owners, by_owner), (categories, by_category)):
        for key, entry in group.items():
            members = membership[key]
            entry.update({
                "addresses": len(members),
                "present_addresses": sum(m["present"] for m in members),
                "active_addresses": sum(m["activity_present"] for m in members),
            })
            entry["active_address_fraction"] = entry["active_addresses"] / entry["addresses"]
    operational = [v for v in owners.values() if v["category"] != "token_contract"]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "dictionary": validation,
        "store": store_profile(con),
        "loaded_labels_match": store_profile(con).get("labels_sha256") == validation["files"][
            "entities.json"
        ],
        "window": [SNAPSHOT_START.isoformat(), SNAPSHOT_END.isoformat()],
        "summary": {
            "present_addresses": sum(v["present"] for v in addresses.values()),
            "active_addresses": sum(v["activity_present"] for v in addresses.values()),
            "active_owners": sum(v["active_addresses"] > 0 for v in owners.values()),
            "active_operational_owners": sum(v["active_addresses"] > 0 for v in operational),
            "operational_owners_with_multiple_active_addresses": sum(
                v["active_addresses"] > 1 for v in operational
            ),
        },
        "tables": totals,
        **{name: [values[k] for k in sorted(values)] for name, values in groups.items()},
    }


def render_coverage(report: dict) -> str:
    summary, dictionary = report["summary"], report["dictionary"]
    lines = [
        "# T04 — Dictionary v2: hiện diện trong dữ liệu local", "",
        f"Đo lúc: {report['generated_at']}. Cửa sổ UTC: [{', '.join(report['window'])}).",
        f"Scope store: `{report['store']['scope']}`; "
        f"complete_snapshot: `{report['store']['complete_snapshot']}`.", "",
        f"Dictionary: {dictionary['addresses']:,} địa chỉ, {dictionary['operational_owners']} "
        f"owner ngoài token; {dictionary['multi_address_operational_owners']} owner nhiều địa chỉ.",
        f"Có hoạt động: {summary['active_addresses']:,} địa chỉ, "
        f"{summary['active_operational_owners']} owner ngoài token; "
        f"{summary['operational_owners_with_multiple_active_addresses']} owner có từ hai địa chỉ "
        "hoạt động trở lên.", "",
        "`any` đếm một dòng nguồn đúng một lần ở mỗi cấp địa chỉ/owner/nhóm, kể cả khi cả "
        "hai phía cùng khớp. Token transfer tính thêm vai trò token contract. "
        "Các vai trò from/to/token được đếm riêng và có thể chồng lấn.",
        "Hiện diện trong contracts/token metadata/block miner được ghi riêng trong JSON; "
        "không thay thế hoạt động giao dịch. Số 0 chỉ có nghĩa không quan sát thấy trong "
        "dữ liệu local; đây không phải coverage toàn mạng hay bằng chứng lịch sử "
        "về quyền sở hữu.", "",
        f"Nhãn đang nạp trong store khớp dictionary được đo: `{report['loaded_labels_match']}`.",
        "Báo cáo join dictionary trực tiếp với bảng raw, không phụ thuộc nhãn đang nạp.", "",
        "| Nhóm | Địa chỉ | Hoạt động | Giao dịch any | Token transfer any |",
        "|---|---:|---:|---:|---:|",
    ]
    for entry in report["categories"]:
        lines.append(
            f"| {entry['category']} | {entry['addresses']:,} | {entry['active_addresses']:,} "
            f"| {entry['transactions_any']:,} | {entry['token_transfers_any']:,} |"
        )
    lines += [
        "", "| Owner ngoài token | Địa chỉ | Hoạt động | Giao dịch any | Token transfer any |",
        "|---|---:|---:|---:|---:|",
    ]
    for entry in report["owners"]:
        if entry["category"] != "token_contract":
            lines.append(
                f"| {entry['owner']} | {entry['addresses']} | {entry['active_addresses']} "
                f"| {entry['transactions_any']:,} | {entry['token_transfers_any']:,} |"
            )
    return "\n".join(lines) + "\n"


def coverage_gate(report: dict, baseline: dict) -> dict:
    """Require a full v2 store with no activity loss against the sampled baseline.

    Zero-activity owners remain in the report. This gate does not invent a
    network-wide ownership coverage percentage or require every owner to be active.
    """
    checks = {
        "complete_snapshot": report["store"].get("complete_snapshot") is True,
        "loaded_labels_match": report["loaded_labels_match"],
        "same_dictionary": report["dictionary"]["files"] == baseline["dictionary"]["files"],
        "same_window": report["window"] == baseline["window"],
    }
    regressions = []
    for level, key in (("addresses", "address"), ("owners", "owner"), ("categories", "category")):
        current = {r[key]: r for r in report[level]}
        previous = {r[key]: r for r in baseline[level]}
        checks[f"same_{level}"] = set(current) == set(previous)
        for identity, old in previous.items():
            for metric in ("transactions_any", "token_transfers_any"):
                actual = current.get(identity, {}).get(metric, 0)
                if actual < old[metric]:
                    regressions.append(
                        {
                            "level": level,
                            "key": identity,
                            "metric": metric,
                            "minimum": old[metric],
                            "actual": actual,
                        }
                    )
    checks["no_activity_regressions"] = not regressions
    return {"passed": all(checks.values()), "checks": checks, "regressions": regressions}

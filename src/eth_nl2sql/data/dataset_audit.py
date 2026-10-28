"""Execute dataset golds and retain empty/zero answers and held-out checks."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from eth_nl2sql.config import read_jsonl, sha256_file
from eth_nl2sql.data.annotations import audit_annotations
from eth_nl2sql.data.entities import split_audit
from eth_nl2sql.data.splits import DEVELOPMENT_SPLITS
from eth_nl2sql.linking.dictionary import load_dictionary
from eth_nl2sql.linking.validation import read_dictionary
from eth_nl2sql.results import is_order_sensitive, row_digests
from eth_nl2sql.store.execute import ExecutionError, execute
from eth_nl2sql.store.manifest import store_profile
from eth_nl2sql.validation import ValidationError


def text_digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def owner_support(con: duckdb.DuckDBPyConnection, expected: dict) -> dict:
    """Independent raw-table oracle; also measure single-address ablations."""
    fact = expected["fact"]
    if fact not in {"transactions", "token_transfers"}:
        raise ValueError(f"unsupported support fact: {fact}")
    direction = expected["direction"]
    columns = {
        "from": ["from_address"],
        "to": ["to_address"],
        "either": ["from_address", "to_address"],
        "token": ["token_address"],
    }[direction]
    endpoint = " OR ".join(f"lower(f.{col}) = labels.address" for col in columns)
    identity = (
        "f.hash"
        if fact == "transactions"
        else ("(f.transaction_hash, f.log_index, f.block_number, f.block_hash)")
    )
    success = " AND f.receipt_status = 1" if expected.get("success_only") else ""
    source = f"""FROM {fact} AS f JOIN entity_labels_v1 AS labels ON ({endpoint})
        WHERE labels.owner = ? AND f.block_timestamp >= CAST(? AS TIMESTAMPTZ)
        AND f.block_timestamp < CAST(? AS TIMESTAMPTZ){success}"""
    params = [expected["owners"][0], expected["start_date"], expected["end_date"]]
    counts = con.execute(
        f"SELECT labels.address, COUNT(*) {source} GROUP BY labels.address ORDER BY labels.address",
        params,
    ).fetchall()
    total = con.execute(f"SELECT COUNT(DISTINCT {identity}) {source}", params).fetchone()[0]
    maximum = max((count for _, count in counts), default=0)
    return {
        "matching_events": total,
        "active_addresses": len(counts),
        "per_address": dict(counts),
        "max_single_address_events": maximum,
        "single_address_changes_answer": total > maximum,
    }


def relation_oracle(con: duckdb.DuckDBPyConnection, expected: dict) -> tuple[tuple, ...]:
    """Counts for class/pair/composite cases, independently of managed macros."""
    fact, direction = expected["fact"], expected["direction"]
    start, end = expected["start_date"], expected["end_date"]
    bounds = (
        "f.block_timestamp >= CAST(? AS TIMESTAMPTZ) AND f.block_timestamp < CAST(? AS TIMESTAMPTZ)"
    )
    if fact == "joined_transaction_token_transfer":
        sql = f"""SELECT COUNT(*) FROM token_transfers AS f
          JOIN transactions AS tx ON f.transaction_hash = tx.hash
            AND f.block_number = tx.block_number AND f.block_hash = tx.block_hash
          JOIN entity_labels_v1 AS sender ON lower(tx.from_address) = sender.address
          JOIN entity_labels_v1 AS recipient ON lower(f.to_address) = recipient.address
          WHERE {bounds} AND tx.block_timestamp >= CAST(? AS TIMESTAMPTZ)
            AND tx.block_timestamp < CAST(? AS TIMESTAMPTZ)
            AND sender.owner = ? AND recipient.owner = ?"""
        params = [start, end, start, end, *expected["owners"]]
    elif expected.get("category"):
        column = "from_address" if direction == "from" else "to_address"
        sql = f"""SELECT labels.owner, COUNT(*) AS event_count FROM {fact} AS f
          JOIN entity_labels_v1 AS labels ON lower(f.{column}) = labels.address
          WHERE {bounds} AND labels.category = ? GROUP BY labels.owner
          ORDER BY event_count DESC, labels.owner"""
        params = [start, end, expected["category"]]
    else:
        join = f"""FROM {fact} AS f
          JOIN entity_labels_v1 AS sender ON lower(f.from_address) = sender.address
          JOIN entity_labels_v1 AS recipient ON lower(f.to_address) = recipient.address"""
        if expected.get("from_category"):
            sql = f"""SELECT sender.owner, recipient.owner, COUNT(*) AS event_count {join}
              WHERE {bounds} AND sender.category = ? AND recipient.category = ?
              GROUP BY sender.owner, recipient.owner
              ORDER BY event_count DESC, sender.owner, recipient.owner"""
            params = [start, end, expected["from_category"], expected["to_category"]]
        else:
            predicate = "sender.owner = ? AND recipient.owner = ?"
            params = [start, end, *expected["owners"]]
            if direction == "bidirectional_pair":
                predicate = f"({predicate}) OR (sender.owner = ? AND recipient.owner = ?)"
                params += list(reversed(expected["owners"]))
            sql = f"SELECT COUNT(*) {join} WHERE {bounds} AND ({predicate})"
    return tuple(con.execute(sql, params).fetchall())


def _review_status(rows: list[dict], review: dict) -> dict:
    records = {row["id"]: row for row in review["cases"]}
    stale = [
        row["id"]
        for row in rows
        if row["id"] not in records
        or records[row["id"]]["question_sha256"] != text_digest(row["question"])
        or records[row["id"]]["sql_sha256"] != text_digest(row["sql"])
        or records[row["id"]].get("status") not in {"agent_reviewed", "human_reviewed"}
        or not records[row["id"]].get("note")
    ]
    extra = sorted(set(records) - {r["id"] for r in rows})
    return {
        "passed": not stale and not extra and len(records) == len(review["cases"]),
        "reviewer": review["reviewer"],
        "human_review": review["human_review"],
        "stale_or_missing_ids": stale,
        "extra_ids": extra,
    }


def audit_dataset(
    con: duckdb.DuckDBPyConnection,
    data_dir: Path,
    dictionary: Path,
    *,
    progress: Callable[[str], None] | None = None,
) -> dict:
    splits = {s: read_jsonl(data_dir / f"{s}.jsonl") for s in DEVELOPMENT_SPLITS}
    _, aliases, _ = read_dictionary(dictionary)
    profile = store_profile(con)
    labels_match = profile.get("labels_sha256") == sha256_file(dictionary / "entities.json")
    leakage = split_audit(splits)
    review = _review_status(
        splits["dev_eval"], json.loads((data_dir / "dev_eval-review.json").read_text())
    )
    linking_annotations = audit_annotations(
        splits["dev_eval"],
        read_jsonl(data_dir / "dev_eval-annotations.jsonl"),
        read_jsonl(data_dir / "dev_eval-annotation-reviews.jsonl"),
        load_dictionary(dictionary),
    )
    cache = {}
    checks = []
    for split, rows in splits.items():
        for row in rows:
            sql = row["sql"]
            if sql not in cache:
                if progress and len(cache) % 100 == 0:
                    progress(f"{split}: executing distinct SQL {len(cache) + 1}")
                try:
                    result = execute(con, sql)
                    digests = row_digests(result.rows, float_digits=12)
                    if not is_order_sensitive(sql):
                        digests = tuple(sorted(digests))
                    cache[sql] = {
                        "ok": True,
                        "row_count": len(result.rows),
                        "columns": result.columns,
                        "empty": not result.rows,
                        "zero_aggregate": len(result.rows) == 1
                        and all(v is None or v == 0 for v in result.rows[0]),
                        "rows_sha256": text_digest("\n".join(digests)),
                    }
                except (ExecutionError, ValidationError) as exc:
                    cache[sql] = {"ok": False, "error_code": exc.code, "error": str(exc)}
            check = {"id": row["id"], "split": split, "sql_sha256": text_digest(sql), **cache[sql]}
            if row.get("entity_expectations"):
                expectation = row["entity_expectations"]
                issues = []
                for alias, owner in expectation.get("aliases", {}).items():
                    if aliases.get(alias.casefold()) != owner:
                        issues.append(f"alias {alias!r} is not unambiguous for {owner}")
                if expectation.get("owners") and expectation.get("direction") in {
                    "from",
                    "to",
                    "either",
                    "token",
                }:
                    support = owner_support(con, expectation)
                    check["support"] = support
                    if support["active_addresses"] < expectation.get("minimum_active_addresses", 0):
                        issues.append(
                            "insufficient active addresses for this fact/direction/window"
                        )
                    if (
                        "multi_address" in row["specifics"]
                        and not support["single_address_changes_answer"]
                    ):
                        issues.append("a single-address answer is indistinguishable")
                    if check["ok"] and expectation.get("aggregate_count"):
                        oracle = ((support["matching_events"],),)
                        digest = text_digest("\n".join(row_digests(oracle)))
                        if check["rows_sha256"] != digest:
                            issues.append("gold count differs from independent raw-table oracle")
                else:
                    oracle = relation_oracle(con, expectation)
                    if expectation.get("expect_positive_count") and oracle == ((0,),):
                        issues.append("expected a positive count for this property witness")
                    digests = row_digests(oracle)
                    if not is_order_sensitive(sql):
                        digests = tuple(sorted(digests))
                    digest = text_digest("\n".join(digests))
                    check["oracle_rows_sha256"] = digest
                    if check["ok"] and check["rows_sha256"] != digest:
                        issues.append("gold differs from independent raw-table relation oracle")
                if check.get("empty") and not row.get("empty_reason"):
                    issues.append("unexpected empty entity result without explanation")
                check["semantic_issues"] = issues
                if row.get("empty_reason"):
                    check["empty_reason"] = row["empty_reason"]
            checks.append(check)
    summary = {}
    for split in splits:
        selected = [c for c in checks if c["split"] == split]
        summary[split] = {
            "rows": len(selected),
            "unique_sql": len({r["sql"] for r in splits[split]}),
            "execution_errors": [c["id"] for c in selected if not c["ok"]],
            "empty_result_ids": [c["id"] for c in selected if c.get("empty")],
            "zero_aggregate_ids": [c["id"] for c in selected if c.get("zero_aggregate")],
        }
    entity = [r for r in splits["dev_eval"] if r["subset"] == "entity"]
    specifics = Counter(s for row in entity for s in row["specifics"])
    passed = (
        labels_match
        and leakage["passed"]
        and review["passed"]
        and linking_annotations["passed"]
        and all(c["ok"] and not c.get("semantic_issues") for c in checks)
    )
    return {
        "version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "passed": passed,
        "store": profile,
        "loaded_labels_match": labels_match,
        "files": {f"{s}.jsonl": sha256_file(data_dir / f"{s}.jsonl") for s in splits},
        "review_sha256": sha256_file(data_dir / "dev_eval-review.json"),
        "templates_sha256": sha256_file(data_dir / "templates" / "entity_templates.json"),
        "dictionary_manifest_sha256": sha256_file(dictionary / "manifest.json"),
        "splits": summary,
        "dev_eval_subsets": dict(Counter(r["subset"] for r in splits["dev_eval"])),
        "specifics": dict(specifics),
        "semantic_review": review,
        "linking_annotations": linking_annotations,
        "annotation_files": {
            name: sha256_file(data_dir / name)
            for name in ("dev_eval-annotations.jsonl", "dev_eval-annotation-reviews.jsonl")
        },
        "multi_address_owners": sorted(
            {
                owner
                for r in entity
                if "multi_address" in r["specifics"]
                for owner in r["entity_expectations"]["owners"]
            }
        ),
        "leakage": leakage,
        "queries": checks,
    }


def render_audit(report: dict) -> str:
    lines = [
        "# T05 — Kiểm dataset trên DuckDB",
        "",
        f"Kết quả: **{'PASS' if report['passed'] else 'FAIL'}**. "
        f"Thời điểm UTC: {report['generated_at']}.",
        "",
        f"Scope: `{report['store'].get('scope')}`; "
        f"complete_snapshot: `{report['store'].get('complete_snapshot')}`.",
        "",
        "| Split | Câu | SQL phân biệt | Lỗi | Rỗng | Aggregate 0/NULL |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for split, s in report["splits"].items():
        lines.append(
            f"| {split} | {s['rows']} | {s['unique_sql']} | "
            f"{len(s['execution_errors'])} | {len(s['empty_result_ids'])} | "
            f"{len(s['zero_aggregate_ids'])} |"
        )
    lines += [
        "",
        f"Dev eval: {report['dev_eval_subsets']}. Nhãn có thể chồng lấn: {report['specifics']}.",
        f"Multi-address: {len(report['multi_address_owners'])} owner; "
        "mỗi ca được kiểm trực tiếp trên raw fact theo đúng chiều và cửa sổ.",
        "",
        "## Leakage",
        "",
        report["leakage"]["policy"],
        "",
        "| Cặp split | Trùng câu | Trùng SQL | Trùng family | Câu chung 12-gram |",
        "|---|---:|---:|---:|---:|",
    ]
    for pair, p in report["leakage"]["pairs"].items():
        lines.append(
            f"| {pair} | {len(p['normalized_question_overlap'])} | "
            f"{p['canonical_sql_overlap_count']} | {len(p['family_overlap'])} | "
            f"{len(p['ngram_12_overlap_ids'])} |"
        )
    lines += [
        "",
        "Train/dev dùng chung template nên có đoạn văn mẫu trùng; "
        "đây là cảnh báo được giữ trong báo cáo, không phải kiểm tra 12-gram đã sạch.",
        "",
        "## Kết quả rỗng của dev_eval",
        "",
    ]
    for check in report["queries"]:
        if check["split"] == "dev_eval" and check.get("empty"):
            lines.append(f"- `{check['id']}`: {check.get('empty_reason', 'Cần review.')}")
    if not report["splits"]["dev_eval"]["empty_result_ids"]:
        lines.append("Không có.")
    lines += [
        "",
        "Kết quả đếm 0 vẫn trả một dòng; danh sách zero_aggregate_ids ghi riêng trong JSON.",
        "",
        "## Review ngữ nghĩa",
        "",
        f"Reviewer: {report['semantic_review']['reviewer']}. "
        f"Human review: {report['semantic_review']['human_review']}.",
        "Mỗi câu dev_eval có ghi chú và hash câu hỏi/SQL trong `data/dev_eval-review.json`. "
        "Đổi câu hoặc SQL làm review hết hiệu lực.",
        "",
        (
            "Đây là kiểm gold trên snapshot đầy đủ local; parity BigQuery được kiểm riêng bằng v1."
            if report["store"].get("complete_snapshot")
            else "Đây là kiểm tra trên dữ liệu local lấy mẫu, chưa phải parity với BigQuery."
        ),
        "",
    ]
    return "\n".join(lines)

"""Read-only T09A sample audit and human-review packet; never invoke a model/linker.

Usage: .venv/bin/python scripts/audit_t09a.py
Requires the separately built data/store/t09-sample-v2.duckdb.
Writes reports only. It cannot approve reviews, alter golds, freeze or run T09B.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from sqlglot import exp

from eth_nl2sql.config import DATA_DIR, DICTIONARY_DIR, ROOT, read_jsonl, sha256_file, write_json
from eth_nl2sql.data.annotations import GROUPS, PROPERTY_COUNTS, text_digest
from eth_nl2sql.data.benchmark import audit_benchmark
from eth_nl2sql.data.entities import canonical_sql, normalize_question
from eth_nl2sql.data.leakage import leaked_ids
from eth_nl2sql.results import canonical_value, is_order_sensitive, row_digests, sql_signatures
from eth_nl2sql.store.build import connect
from eth_nl2sql.store.execute import ExecutionError, execute
from eth_nl2sql.store.manifest import store_profile
from eth_nl2sql.validation import parse_query

BENCHMARK = DATA_DIR / "benchmark/v2"


def summarize(result, sql, *, include_row_digests=True):
    digests = row_digests(result.rows, float_digits=12)
    ordered = is_order_sensitive(sql)
    sequence = digests if ordered else tuple(sorted(digests))
    summary = {
        "row_count": len(result.rows),
        "columns": list(result.columns),
        "types": list(result.types),
        "ordered": ordered,
        "answer_sha256": text_digest(json.dumps(sequence)),
        "elapsed_ms": round(result.elapsed_ms, 3),
        "empty": not result.rows,
        "zero_aggregate": len(result.rows) == 1
        and all(v is None or v == 0 for v in result.rows[0]),
        "preview_typed": [[canonical_value(v) for v in row] for row in result.rows[:5]],
    }
    if include_row_digests:
        summary["row_sha256"] = list(digests)
    return summary


def single_address_sql(sql, owner, address):
    """Restrict every use of one owner's endpoint set, including COUNTIF predicates."""
    tree = parse_query(sql).copy()
    replaced = 0
    for eq in list(tree.find_all(exp.EQ)):
        col, value = eq.this, eq.expression
        if not isinstance(col, exp.Column) or not isinstance(value, exp.Literal):
            continue
        if value.this != owner or col.name not in {"from_owner", "to_owner"}:
            continue
        col.set("this", exp.to_identifier(col.name.replace("_owner", "_address")))
        eq.set("expression", exp.Literal.string(address))
        replaced += 1
    if not replaced:
        raise ValueError("single-address diagnostic did not replace an owner endpoint predicate")
    return tree.sql(dialect="bigquery")


def multi_address_checks(con, cases, annotations, gold):
    checks = []
    # Full query ablations are performed for the 20 PRIMARY cases. The existing
    # benchmark audit separately records broad raw-table support for secondary labels.
    for case in cases:
        if case["primary_group"] != "multi_address":
            continue
        entity = annotations[case["id"]]["entities"][0]
        direction = annotations[case["id"]]["properties"]["direction"][0]["value"]
        raw = (
            "transactions"
            if annotations[case["id"]]["properties"]["fact"] == "transaction"
            else "token_transfers"
        )
        endpoint = {"from": "from_address", "to": "to_address"}.get(direction)
        predicate = (
            f"lower({endpoint}) IN (SELECT address FROM entity_labels_v1 WHERE owner=?)"
            if endpoint
            else "(lower(from_address) IN (SELECT address FROM entity_labels_v1 WHERE owner=?) "
            "OR lower(to_address) IN (SELECT address FROM entity_labels_v1 WHERE owner=?))"
        )
        params = [entity["owner"]] * (1 if endpoint else 2)
        # One raw scan lists addresses with any endpoint activity in the window.
        columns = [endpoint] if endpoint else ["from_address", "to_address"]
        active = set()
        for column in columns:
            rows = con.execute(
                f"SELECT DISTINCT lower({column}) FROM {raw} WHERE {predicate} "
                "AND block_timestamp >= '2026-06-01' AND block_timestamp < '2026-07-01'",
                params,
            ).fetchall()
            active.update(row[0] for row in rows if row[0] in entity["addresses"])
        inactive = sorted(set(entity["addresses"]) - active)
        tested = sorted(active) + inactive[:1]
        variants = []
        for address in tested:
            sql = single_address_sql(case["sql"], entity["owner"], address)
            result = summarize(execute(con, sql), sql)
            variants.append(
                {
                    "address": address,
                    "sql_sha256": text_digest(sql),
                    "row_count": result["row_count"],
                    "answer_sha256": result["answer_sha256"],
                    "differs_from_union": result["answer_sha256"]
                    != gold[case["id"]]["answer_sha256"],
                }
            )
        checks.append(
            {
                "id": case["id"],
                "owner": entity["owner"],
                "known_addresses": len(entity["addresses"]),
                "raw_active_addresses": len(active),
                "inactive_addresses": len(inactive),
                "tested": variants,
                "inactive_equivalence": "No inactive endpoint rows; one representative executed.",
                "union_differs_from_every_single_address": bool(variants)
                and all(v["differs_from_union"] for v in variants),
                "scope": "sample; exact gold-query predicates/projection/order/limit retained",
            }
        )
        print(f"multi {case['id']}: {len(active)} active endpoints checked", flush=True)
    return checks


def source_audit(cases):
    structures = {sql_signatures(c["sql"])[1] for c in cases}
    comparisons = {}
    for split in ("train", "dev", "dev_eval"):
        rows = read_jsonl(DATA_DIR / f"{split}.jsonl")
        old_structures = {sql_signatures(c["sql"])[1] for c in rows}
        shared = structures & old_structures
        comparisons[split] = {
            "literal_and_alias_masked_sql_overlap": len(shared),
            "test_ids_with_masked_sql_overlap": [
                c["id"] for c in cases if sql_signatures(c["sql"])[1] in shared
            ],
            "test_to_split_12gram_ids": leaked_ids(cases, [r["question"] for r in rows]),
            "split_to_test_12gram_ids": leaked_ids(rows, [r["question"] for r in cases]),
        }
    return {
        "unique_questions": len({normalize_question(c["question"]) for c in cases}),
        "distinct_canonical_sql": len({canonical_sql(c["sql"]) for c in cases}),
        "literal_and_alias_masked_sql_count": len(structures),
        "comparisons": comparisons,
        "limitation": "Masked SQL is a syntactic screen, not proof of intent or template holdout. "
        "All records are agent-authored; independent semantic/human review remains pending.",
    }


def review_packet(cases, annotations, reviews, notes, gold, properties, multi, report_hash):
    lines = [
        "# T09A — hồ sơ human review (DRAFT)",
        "",
        "Tác giả: `codex-t09a` (agent). **0/100 human review**; mọi trạng thái là `pending`.",
        "Người review đối chiếu câu hỏi, SQL và annotation; ghi reviewer, timestamp có timezone,",
        "ghi chú, status và bốn hash trong `reviews.jsonl`. Agent không điền xác nhận thay người.",
        "Sửa bất kỳ nội dung case/annotation nào phải cập nhật hash và review lại.",
        "",
        "Kiểm: ý hỏi, UTC/cutoff, fact/đơn vị đếm, chiều, token/endpoint, tập owner/class,",
        "join/fanout, NULL/zero, sắp xếp/tie/limit, witness và giải thích ca rỗng.",
        "Kết quả dưới đây chỉ là sample; T09B phải chạy lại toàn bộ trên full snapshot sau T06.",
        f"Sample report SHA-256: `{report_hash}`.",
        "",
    ]
    for case in cases:
        key = case["id"]
        result = gold[key]
        lines += [
            f"## {key} — {case['primary_group']}",
            "",
            case["question"],
            "",
            "Case metadata (cũng được gắn hash review):",
            "",
            "```json",
            json.dumps(
                {k: v for k, v in case.items() if k not in {"question", "sql"}},
                ensure_ascii=False,
                indent=2,
            ),
            "```",
            "",
            f"Intent: `{notes[key]['intent']}`. Property focus: `{case['property_focus']}`.",
            "",
            "```sql",
            case["sql"],
            "```",
            "",
            "Annotation trực tiếp:",
            "",
            "```json",
            json.dumps(annotations[key], ensure_ascii=False, indent=2),
            "```",
            "",
            f"Lý do tác giả: {notes[key]['author_rationale']}",
            "",
            f"Sample: {result.get('row_count')} rows; empty={result.get('empty')}; "
            f"zero/NULL aggregate={result.get('zero_aggregate')}; error={result.get('error')}.",
            "",
            f"Giải thích rỗng: {case['empty_reason'] or 'Không có kết quả rỗng được ghi nhận.'}",
            "",
            "Preview (giá trị có type tag):",
            "",
            "```json",
            json.dumps(result.get("preview_typed"), ensure_ascii=False, indent=2),
            "```",
            "",
        ]
        if key in properties:
            p = properties[key]
            lines += [
                f"Property contrast: phân biệt trên sample={p.get('discriminates_on_sample')}; "
                f"{p['rationale']}",
                "",
                "```sql",
                p["sql"],
                "```",
                "",
            ]
        if key in multi:
            m = multi[key]
            lines += [
                f"Multi-address: {m['raw_active_addresses']}/{m['known_addresses']} active; "
                "union khác mọi địa chỉ riêng="
                f"{m['union_differs_from_every_single_address']}.",
                "",
            ]
        lines += [
            "Review binding:",
            "",
            "```json",
            json.dumps(reviews[key], ensure_ascii=False, indent=2),
            "```",
            "",
            "Nhận xét của người review: ____________________",
            "",
            "Người review / thời điểm / quyết định: ____________________",
            "",
        ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=DATA_DIR / "store/t09-sample-v2.duckdb")
    parser.add_argument("--out", type=Path, default=ROOT / "reports/benchmark")
    args = parser.parse_args()
    if args.out.resolve().is_relative_to(BENCHMARK.resolve()):
        parser.error("reports must not overwrite benchmark inputs")
    manifest = json.loads((BENCHMARK / "manifest.json").read_text())
    if manifest["status"] != "draft":
        parser.error("T09A audit expects draft; frozen benchmarks require their release protocol")
    cases = read_jsonl(BENCHMARK / "test.jsonl")
    annotations = {r["id"]: r for r in read_jsonl(BENCHMARK / "annotations.jsonl")}
    reviews = {r["id"]: r for r in read_jsonl(BENCHMARK / "reviews.jsonl")}
    notes = {r["id"]: r for r in read_jsonl(BENCHMARK / "author-notes.jsonl")}
    contrasts = read_jsonl(BENCHMARK / "property-contrasts.jsonl")
    inputs = {str(p.relative_to(ROOT)): sha256_file(p) for p in BENCHMARK.iterdir() if p.is_file()}
    infrastructure = audit_benchmark(BENCHMARK, DATA_DIR, DICTIONARY_DIR)
    write_json(args.out / "structure.json", infrastructure)
    if (
        not infrastructure["passed"]
        or infrastructure["case_count"] != 100
        or infrastructure["primary_counts"] != dict.fromkeys(GROUPS, 20)
        or infrastructure["property_counts"] != PROPERTY_COUNTS
    ):
        raise SystemExit("Structure/annotation/hash/leakage audit failed; inspect structure.json")
    gold, properties = {}, []
    with connect(args.store) as con:
        con.execute("SET threads=2")
        profile = store_profile(con)
        if profile["complete_snapshot"]:
            parser.error(
                "Full-snapshot work belongs to T09B; T09A requires an explicitly sampled store"
            )
        if profile["labels_sha256"] != sha256_file(DICTIONARY_DIR / "entities.json"):
            parser.error("Sample store must use the pinned v2 dictionary")
        for case in cases:
            try:
                gold[case["id"]] = {
                    "id": case["id"],
                    "passed": True,
                    **summarize(execute(con, case["sql"]), case["sql"]),
                }
            except (ValueError, ExecutionError) as exc:
                gold[case["id"]] = {"id": case["id"], "passed": False, "error": str(exc)}
            print(f"gold {case['id']}: {gold[case['id']].get('row_count', 'ERROR')}", flush=True)
        for contrast in contrasts:
            check = dict(contrast)
            try:
                check["result"] = summarize(
                    execute(con, contrast["sql"]), contrast["sql"], include_row_digests=False
                )
                check["discriminates_on_sample"] = check["result"]["answer_sha256"] != gold[
                    contrast["id"]
                ].get("answer_sha256")
            except (ValueError, ExecutionError) as exc:
                check.update(error=str(exc), discriminates_on_sample=False)
            properties.append(check)
        multi = (
            multi_address_checks(con, cases, annotations, gold)
            if all(r["passed"] for r in gold.values())
            else []
        )
    report = {
        "task": "T09A",
        "status": "draft",
        "checked_at": datetime.now(UTC).isoformat(),
        "verification": "sample_execution_only; no BigQuery/full-snapshot equivalence claim",
        "store_path": str(args.store.relative_to(ROOT)),
        "store": profile,
        "inputs": inputs,
        "audit_script_sha256": sha256_file(Path(__file__)),
        "answer_comparison": "Typed hashes, float_digits=12; ORDER BY sequence, else multiset",
        "source_independence_screen": source_audit(cases),
        "gold": list(gold.values()),
        "property_witnesses": properties,
        "primary_multi_address_witnesses": multi,
        "secondary_counts": dict(Counter(s for c in cases for s in c["specifics"])),
        "difficulty_counts": dict(Counter(c["difficulty"] for c in cases)),
        "human_reviewed": infrastructure["annotations"]["human_reviewed"],
        "release_ready": False,
        "pending_t09b": [
            "T06 full snapshot and provenance/parity gates",
            "Rerun every gold and inspect empty/zero/NULL outcomes on full snapshot",
            "Discriminating raw and exact-query multi-address witnesses on full snapshot",
            "Property witnesses on full snapshot, including sample-nondiscriminating cases",
            "Independent human question/SQL/annotation review, content-bound hashes",
            "Recheck all release gates before any freeze",
        ],
    }
    report["execution_passed"] = all(g["passed"] for g in gold.values())
    report["unexplained_empty_ids"] = [
        c["id"]
        for c in cases
        if (gold[c["id"]].get("empty") or gold[c["id"]].get("zero_aggregate"))
        and not c["empty_reason"]
    ]
    report["t09a_checks_passed"] = (
        report["execution_passed"]
        and not report["unexplained_empty_ids"]
        and report["source_independence_screen"]["distinct_canonical_sql"] == 100
        and all(
            not comparison["literal_and_alias_masked_sql_overlap"]
            and not comparison["test_to_split_12gram_ids"]
            and not comparison["split_to_test_12gram_ids"]
            for comparison in report["source_independence_screen"]["comparisons"].values()
        )
        and len(properties) == 20
        and all("error" not in p for p in properties)
        and len(multi) == 20
        and all(
            m["raw_active_addresses"] >= 2 and m["union_differs_from_every_single_address"]
            for m in multi
        )
    )
    write_json(args.out / "sample.json", report)
    packet = review_packet(
        cases,
        annotations,
        reviews,
        notes,
        gold,
        {p["id"]: p for p in properties},
        {m["id"]: m for m in multi},
        sha256_file(args.out / "sample.json"),
    )
    (args.out / "human-review.md").write_text(packet + "\n")
    assert inputs == {
        str(p.relative_to(ROOT)): sha256_file(p) for p in BENCHMARK.iterdir() if p.is_file()
    }
    print(
        json.dumps(
            {
                "execution_passed": report["execution_passed"],
                "unexplained_empty_ids": report["unexplained_empty_ids"],
                "property_discriminating": sum(
                    p.get("discriminates_on_sample", False) for p in properties
                ),
                "multi_discriminating": sum(
                    m["union_differs_from_every_single_address"] for m in multi
                ),
            }
        )
    )
    if not report["t09a_checks_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

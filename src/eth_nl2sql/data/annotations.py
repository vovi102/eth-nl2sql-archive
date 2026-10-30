"""Versioned linking gold, with content-bound review independent of model output."""

from __future__ import annotations

import json
import re
from collections import Counter
from functools import cache

from jsonschema import Draft202012Validator, FormatChecker
from sqlglot import exp
from sqlglot.errors import SqlglotError
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import traverse_scope

from eth_nl2sql.artifacts import json_digest, text_digest
from eth_nl2sql.config import CATALOG_PATH, ROOT
from eth_nl2sql.linking.dictionary import Dictionary, normalize_phrase, owner_id
from eth_nl2sql.validation import MANAGED_RELATIONS, relation_name, validate_sql

SCHEMA_PATH = ROOT / "configs" / "benchmark.schema.json"
GROUPS = ("generic", "multi_address", "alias", "class_level", "ambiguous_property")
PROPERTY_COUNTS = {"direction": 7, "fact": 7, "address_role": 6}


def content_digest(value: dict) -> str:
    """JSON key order and whitespace do not invalidate an otherwise identical review."""
    return json_digest(value)


def annotation_digest(annotation: dict) -> str:
    return content_digest(annotation)


@cache
def _validator(kind: str) -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text())
    return Draft202012Validator(
        {"$ref": f"#/$defs/{kind}", "$defs": schema["$defs"]}, format_checker=FormatChecker()
    )


def structure_errors(value: object, kind: str) -> list[str]:
    return [
        f"{'.'.join(map(str, error.absolute_path)) or kind}: {error.message}"
        for error in _validator(kind).iter_errors(value)
    ]


@cache
def sql_schema(sql: str) -> dict:
    """Resolve physical column references, including CTEs, aliases and TVFs.

    TVFs are replaced by their catalog relation only in this analysis copy;
    the original SQL, window arguments and execution path are never modified.
    COUNT(*) needs a relation but contributes no column target.
    """
    tree = validate_sql(sql).copy()
    catalog = json.loads(CATALOG_PATH.read_text())["analytical_relations"]
    for table in tree.find_all(exp.Table):
        name = relation_name(table)
        if name in MANAGED_RELATIONS:
            table.set("this", exp.to_identifier(name.rsplit(".", 1)[-1]))
            table.set("db", exp.to_identifier("nl2sparql_analytics"))
            table.set("catalog", exp.to_identifier("nl2sparql-thesis"))
    schema = {
        "nl2sparql-thesis": {
            "nl2sparql_analytics": {
                name: dict.fromkeys(info["fields"], "UNKNOWN") for name, info in catalog.items()
            }
        }
    }
    tree = qualify(tree, dialect="bigquery", schema=schema, identify=False)
    relations, columns = set(), set()
    for scope in traverse_scope(tree):
        for source in scope.sources.values():
            if isinstance(source, exp.Table) and relation_name(source) in MANAGED_RELATIONS:
                relations.add(source.name)
        for column in scope.columns:
            source = scope.sources.get(column.table)
            if isinstance(source, exp.Table) and relation_name(source) in MANAGED_RELATIONS:
                columns.add((source.name, column.name))
    return {
        "relations": sorted(relations),
        "columns": [
            {"relation": relation, "column": column} for relation, column in sorted(columns)
        ],
    }


def _mention_errors(mention: dict, question: str) -> list[str]:
    start, end = mention["start"], mention["end"]
    if not 0 <= start < end <= len(question) or question[start:end] != mention["text"]:
        return ["mention span does not match the question (Python Unicode character offsets)"]
    return []


def validate_annotation(case: dict, annotation: dict, dictionary: Dictionary) -> list[str]:
    errors = structure_errors(annotation, "annotation")
    if errors:
        return errors
    if annotation["id"] != case["id"]:
        errors.append("annotation ID differs from case")
    for field in ("question", "sql"):
        if annotation[f"{field}_sha256"] != text_digest(case[field]):
            errors.append(f"stale {field} hash")
    try:
        expected = sql_schema(case["sql"])
        actual = annotation["schema"]
        if set(actual["relations"]) != set(expected["relations"]) or {
            (c["relation"], c["column"]) for c in actual["columns"]
        } != {(c["relation"], c["column"]) for c in expected["columns"]}:
            errors.append("schema targets differ from resolved gold SQL references")
    except (ValueError, SqlglotError) as exc:
        errors.append(f"invalid gold SQL schema: {exc}")
    for entity in annotation["entities"]:
        errors.extend(_mention_errors(entity["mention"], case["question"]))
        owner = dictionary.by_id.get(owner_id(entity["owner"])) if entity["owner"] else None
        addresses = set(entity["addresses"])
        if entity["owner"] is not None and owner is None:
            errors.append(f"unknown owner: {entity['owner']}")
        if entity["address_scope"] == "known_owner_addresses":
            if owner is None or addresses != set(owner.addresses):
                errors.append("owner address set differs from the frozen dictionary")
            if owner and owner.target_id not in dictionary.phrases.get(
                normalize_phrase(entity["mention"]["text"]), ()
            ):
                errors.append("mention does not name the annotated owner/alias")
        else:
            if len(addresses) != 1 or entity["mention"]["text"].lower() not in addresses:
                errors.append("explicit address must match one address mention")
            if owner and not addresses <= set(owner.addresses):
                errors.append("explicit address does not belong to its owner")
            if owner is None and any(
                address in dictionary.address_targets for address in addresses
            ):
                errors.append("known explicit address requires its annotated owner")
    for cls in annotation["classes"]:
        errors.extend(_mention_errors(cls["mention"], case["question"]))
        target = dictionary.by_id.get(f"concept:{cls['category']}")
        if target is None or cls["concept_class"] not in target.concept_classes:
            errors.append("unknown category/concept class")
            continue
        owners = {t.name for t in dictionary.owners_of_class(cls["concept_class"])}
        if set(cls["owners"]) != owners:
            errors.append("class members differ from the frozen dictionary")
        if target.target_id not in dictionary.phrases.get(
            normalize_phrase(cls["mention"]["text"]), ()
        ):
            errors.append("mention does not name the annotated class")
    properties = annotation["properties"]
    for kind in ("direction", "address_role"):
        targets = []
        for prop in properties[kind]:
            target_kind, index = prop["target"].split(":")
            values = annotation["entities" if target_kind == "entity" else "classes"]
            if int(index) >= len(values):
                errors.append(f"{kind} references a nonexistent target: {prop['target']}")
            targets.append(prop["target"])
        if len(targets) != len(set(targets)):
            errors.append(f"conflicting or repeated {kind} target")
    relations = set(annotation["schema"]["relations"])
    tx = bool(relations & {"transaction_facts", "labeled_transactions"})
    token = bool(relations & {"token_transfer_facts", "labeled_token_transfers"})
    expected_fact = (
        "transaction_token_transfer_join"
        if tx and token
        else "transaction"
        if tx
        else "token_transfer"
        if token
        else None
    )
    if properties["fact"] != expected_fact:
        errors.append("fact property differs from gold relations")
    return errors


def pending_review(case: dict, annotation: dict) -> dict:
    return {
        "schema_version": 2,
        "id": case["id"],
        "case_sha256": content_digest(case),
        "question_sha256": text_digest(case["question"]),
        "sql_sha256": text_digest(case["sql"]),
        "annotation_sha256": annotation_digest(annotation),
        "status": "pending",
        "reviewer": None,
        "reviewer_kind": None,
        "reviewed_at": None,
        "note": "Draft annotation; independent human review pending.",
    }


def validate_review(case: dict, annotation: dict, review: dict) -> list[str]:
    errors = structure_errors(review, "review")
    if errors:
        return errors
    if review["id"] != case["id"]:
        errors.append("review ID differs from case")
    if review["case_sha256"] != content_digest(case):
        errors.append("stale review case hash")
    for field in ("question", "sql"):
        if review[f"{field}_sha256"] != text_digest(case[field]):
            errors.append(f"stale review {field} hash")
    if review["annotation_sha256"] != annotation_digest(annotation):
        errors.append("stale review annotation hash")
    if review["status"] != "pending":
        if not all(
            isinstance(review[k], str) and review[k].strip()
            for k in ("reviewer", "reviewed_at", "note")
        ):
            errors.append("completed review requires reviewer, timestamp and note")
        kind = {"human_reviewed": "human", "agent_reviewed": "agent"}.get(review["status"])
        if kind and review["reviewer_kind"] != kind:
            errors.append("review status differs from reviewer kind")
        provenance = case.get("provenance")
        author = provenance.get("author") if isinstance(provenance, dict) else None
        if review["status"] == "human_reviewed" and review["reviewer"] == author:
            errors.append("human review must be independent of the author")
    return errors


def audit_annotations(
    cases: list[dict], annotations: list[dict], reviews: list[dict], dictionary: Dictionary
) -> dict:
    issues = []
    indexes = []
    for name, rows in (("cases", cases), ("annotations", annotations), ("reviews", reviews)):
        invalid = [
            i
            for i, row in enumerate(rows)
            if not isinstance(row, dict)
            or not isinstance(row.get("id"), str)
            or not row["id"].strip()
        ]
        if invalid:
            issues.append(f"{name}: invalid ID/object at rows {invalid}")
        valid = [row for row in rows if isinstance(row, dict) and isinstance(row.get("id"), str)]
        duplicates = sorted(k for k, n in Counter(r["id"] for r in valid).items() if n > 1)
        if duplicates:
            issues.append(f"{name}: duplicate IDs {duplicates}")
        indexes.append({row["id"]: row for row in valid})
    case_index, annotation_index, review_index = indexes
    for name, index in (("annotations", annotation_index), ("reviews", review_index)):
        if set(index) != set(case_index):
            issues.append(
                f"{name}: missing IDs {sorted(set(case_index) - set(index))}; "
                f"extra IDs {sorted(set(index) - set(case_index))}"
            )
    checks = []
    for key, case in case_index.items():
        annotation, review = annotation_index.get(key), review_index.get(key)
        errors = []
        if not all(isinstance(case.get(k), str) and case[k].strip() for k in ("question", "sql")):
            errors.append("case requires nonempty question and SQL")
        elif annotation is not None:
            errors.extend(validate_annotation(case, annotation, dictionary))
            if review is not None:
                errors.extend(validate_review(case, annotation, review))
        checks.append(
            {
                "id": key,
                "errors": errors,
                "review_status": review.get("status")
                if review and isinstance(review.get("status"), str)
                else "invalid",
            }
        )
    human = [c["id"] for c in checks if not c["errors"] and c["review_status"] == "human_reviewed"]
    return {
        "passed": not issues and all(not c["errors"] for c in checks),
        "issues": issues,
        "cases": checks,
        "human_reviewed": len(human),
        "human_review_complete": bool(cases) and len(human) == len(cases) and not issues,
        "review_counts": dict(Counter(c["review_status"] for c in checks)),
    }


def draft_development_annotations(cases: list[dict], dictionary: Dictionary) -> list[dict]:
    """Bootstrap legacy expectations into drafts. This never marks anything reviewed."""

    def mention(question: str, phrases: tuple[str, ...]) -> dict:
        for phrase in sorted(phrases, key=lambda p: (-len(p), p)):
            match = re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", question, re.IGNORECASE)
            if match:
                return {"text": match[0], "start": match.start(), "end": match.end()}
        raise ValueError(f"No matching mention for {phrases} in {question!r}")

    drafts = []
    for case in cases:
        expected = case.get("entity_expectations", {})
        entities, classes, directions, roles = [], [], [], []
        schema = sql_schema(case["sql"])
        direction = expected.get("direction")
        for i, owner in enumerate(expected.get("owners", [])):
            target = dictionary.by_id[owner_id(owner)]
            entities.append(
                {
                    "mention": mention(case["question"], target.aliases),
                    "owner": owner,
                    "addresses": list(target.addresses),
                    "address_scope": "known_owner_addresses",
                }
            )
            role = "token_contract" if direction == "token" else "endpoint"
            roles.append({"target": f"entity:{i}", "value": role})
            value = direction
            if direction in {"from_to", "tx_from_log_to"}:
                value = "from" if i == 0 else "to"
            elif direction == "bidirectional_pair":
                value = "either"
            if value in {"from", "to", "either"}:
                directions.append({"target": f"entity:{i}", "value": value})
        for key in ("category", "from_category", "to_category"):
            if key not in expected:
                continue
            target = dictionary.by_id[f"concept:{expected[key]}"]
            index = len(classes)
            cls = target.concept_classes[0]
            classes.append(
                {
                    "mention": mention(case["question"], target.aliases),
                    "category": target.name,
                    "concept_class": cls,
                    "owners": sorted(t.name for t in dictionary.owners_of_class(cls)),
                }
            )
            value = {"from_category": "from", "to_category": "to"}.get(key, direction)
            if value in {"from", "to", "either"}:
                directions.append({"target": f"class:{index}", "value": value})
            roles.append({"target": f"class:{index}", "value": "endpoint"})
        relations = set(schema["relations"])
        tx = bool(relations & {"transaction_facts", "labeled_transactions"})
        token = bool(relations & {"token_transfer_facts", "labeled_token_transfers"})
        fact = (
            "transaction_token_transfer_join"
            if tx and token
            else "transaction"
            if tx
            else "token_transfer"
            if token
            else None
        )
        drafts.append(
            {
                "schema_version": 2,
                "id": case["id"],
                "question_sha256": text_digest(case["question"]),
                "sql_sha256": text_digest(case["sql"]),
                "schema": schema,
                "entities": entities,
                "classes": classes,
                "properties": {"direction": directions, "fact": fact, "address_role": roles},
            }
        )
    return drafts

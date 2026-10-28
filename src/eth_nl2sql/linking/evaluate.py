"""Score saved question-only predictions against T07 annotations, never generated SQL."""

from __future__ import annotations

from collections import Counter

METRICS = (
    "relation_recall@3",
    "column_recall@6",
    "entity",
    "address_set",
    "multi_address_set",
    "class",
    "class_membership",
    "direction",
    "fact",
    "address_role",
)


def _mention(item: dict) -> tuple:
    mention = item["mention"]
    return mention["start"], mention["end"], mention["text"]


def _index(rows: list[dict], name: str) -> dict[str, dict]:
    result = {}
    for row in rows:
        if row["id"] in result:
            raise ValueError(f"Duplicate {name} ID: {row['id']}")
        result[row["id"]] = row
    return result


def _ratio(correct: int, total: int) -> dict:
    return {"correct": correct, "total": total, "rate": correct / total if total else None}


def _same_target(expected: dict, predicted: dict | None, kind: str) -> bool:
    if predicted is None or predicted.get("status") == "unresolved":
        return False
    if kind == "class":
        return all(expected[k] == predicted.get(k) for k in ("category", "concept_class"))
    if expected["owner"] != predicted.get("owner"):
        return False
    if expected["owner"] is not None and expected["address_scope"] != "explicit_address":
        return True
    return set(expected["addresses"]) == set(predicted.get("addresses", ()))


def _property_targets(value: dict, kind: str) -> dict[tuple, object]:
    result = {}
    for prop in value.get("properties", {}).get(kind, ()):
        category, index = prop["target"].split(":")
        targets = value.get("entities" if category == "entity" else "classes", ())
        if category not in {"entity", "class"} or not 0 <= int(index) < len(targets):
            raise ValueError(f"Invalid property target: {prop['target']}")
        key = (category, _mention(targets[int(index)]))
        if key in result:
            raise ValueError(f"Duplicate property target: {prop['target']}")
        result[key] = prop["value"]
    return result


def score_predictions(
    predictions: list[dict],
    annotations: list[dict],
    *,
    split: str = "dev_eval",
    human_review_complete: bool = False,
) -> dict:
    predicted = _index(predictions, "prediction")
    gold = _index(annotations, "annotation")
    extra = sorted(predicted.keys() - gold.keys())
    if extra:
        raise ValueError(f"Predictions contain unknown IDs: {extra}")
    totals = {metric: Counter() for metric in METRICS}
    details = []
    for key, expected in sorted(gold.items()):
        row = predicted.get(key, {})
        actual = row.get("linking", row)
        scores = {metric: Counter() for metric in METRICS}

        def add(metric: str, correct: int, total: int = 1, *, scores: dict = scores) -> None:
            scores[metric].update(correct=correct, total=total)

        schema = actual.get("schema", {})
        relations = set(expected["schema"]["relations"])
        columns = {(c["relation"], c["column"]) for c in expected["schema"]["columns"]}
        add(
            "relation_recall@3",
            len(relations & set(schema.get("relations", ())[:3])),
            len(relations),
        )
        add(
            "column_recall@6",
            len(columns & {(c["relation"], c["column"]) for c in schema.get("columns", ())[:6]}),
            len(columns),
        )
        matched = {}
        unmatched = {}
        for kind, field in (("entity", "entities"), ("class", "classes")):
            items = actual.get(field, ())
            index = {_mention(item): item for item in items}
            if len(index) != len(items):
                raise ValueError(f"Duplicate predicted {kind} mention in {key}")
            gold_mentions = {_mention(item) for item in expected[field]}
            unmatched[field] = sum(_mention(item) not in gold_mentions for item in items)
            for item in expected[field]:
                target = index.get(_mention(item))
                correct = _same_target(item, target, kind)
                matched[kind, _mention(item)] = correct
                add(kind, int(correct))
                if kind == "entity":
                    same_set = int(
                        correct and set(item["addresses"]) == set(target.get("addresses", ()))
                    )
                    add("address_set", same_set)
                    if item["address_scope"] == "known_owner_addresses" and len(
                        item["addresses"]
                    ) > 1:
                        add("multi_address_set", same_set)
                else:
                    add(
                        "class_membership",
                        int(correct and set(item["owners"]) == set(target.get("owners", ()))),
                    )
        unresolved = {}
        for kind in ("direction", "address_role"):
            actual_properties = _property_targets(actual, kind)
            expected_properties = _property_targets(expected, kind)
            unresolved[kind] = 0
            for target, value in expected_properties.items():
                resolved = actual_properties.get(target)
                unresolved[kind] += resolved is None
                add(kind, int(matched.get(target, False) and resolved == value))
        fact = expected["properties"]["fact"]
        if fact is not None:
            actual_fact = actual.get("properties", {}).get("fact")
            add("fact", int(actual_fact == fact))
            unresolved["fact"] = int(actual_fact is None)
        for metric, score in scores.items():
            totals[metric].update(score)
        details.append(
            {
                "id": key,
                "missing_prediction": key not in predicted,
                "metrics": {m: _ratio(s["correct"], s["total"]) for m, s in scores.items()},
                "unresolved_properties": unresolved,
                "unmatched_predictions": unmatched,
            }
        )
    development = split != "test" or not human_review_complete
    return {
        "split": split,
        "evaluation_scope": "development" if development else "final_test",
        "notice": "Development evaluation using draft annotations; independent human review "
        "is incomplete. These are not final benchmark results."
        if not human_review_complete
        else "Development evaluation."
        if development
        else "Frozen, human-reviewed final test.",
        "human_review_complete": human_review_complete,
        "cases": len(gold),
        "missing_prediction_ids": sorted(gold.keys() - predicted.keys()),
        "metrics": {m: _ratio(s["correct"], s["total"]) for m, s in totals.items()},
        "details": details,
    }

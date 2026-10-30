"""Prompt construction shared by B1/B2 (catalog in context) and B3 (compact schema).

Compared with luanvan, the catalog summary now shows each relation's fully
qualified name and call syntax; luanvan's summary listed only short relation
ids, which is why 99/100 zero-shot outputs there referenced unknown tables.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from eth_nl2sql.artifacts import json_digest
from eth_nl2sql.validation import PROJECT_DATASET

LABEL_COLUMNS = (
    "primary_label",
    "owner",
    "category",
    "concept_class",
    "address_role",
    "confidence",
)

_RULES = """QUERY RULES
- Return exactly one read-only GoogleSQL query and nothing else: no prose, comments or semicolon.
- Use only the managed relations above with their fully qualified names in backticks.
- Call parameterized relations with DATE literals, e.g.
  `{project}.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08').
- Date windows are half-open [start_date, end_date), at most 31 days, inside {start}..{end}.
- Name every output column explicitly; SELECT * is not allowed.
- Filter named entities and entity classes through entity_labels_v1 (owner, concept_class),
  never by guessing addresses."""


def qualified(relation_id: str) -> str:
    return f"`{PROJECT_DATASET}.{relation_id}`"


def relation_signature(relation_id: str, relation: Mapping) -> str:
    parameters = relation.get("parameters", {})
    if not parameters:
        return f"{qualified(relation_id)} (view)"
    args = ", ".join(f"{name} {kind}" for name, kind in parameters.items())
    return f"{qualified(relation_id)}({args})"


def _relation_lines(relation_id: str, relation: Mapping) -> list[str]:
    lines = [f"Relation {relation_signature(relation_id, relation)}"]
    fields = relation["fields"]
    if relation_id.startswith("labeled_"):
        base = (
            "transaction_facts" if relation_id == "labeled_transactions" else "token_transfer_facts"
        )
        prefixes = sorted({name.split("_", 1)[0] for name in fields if name.endswith("_owner")})
        lines.append(
            f"  - all fields of {base}, plus label columns "
            + ", ".join(f"{prefix}_{{{','.join(LABEL_COLUMNS)}}}" for prefix in prefixes)
        )
        return lines
    for name, field in fields.items():
        expression = field.get("expression")
        suffix = f"; semantics: {expression}" if isinstance(expression, str) else ""
        lines.append(f"  - {name}: {field['type']}{suffix}")
    return lines


def _join_line(join_id: str, join: Mapping) -> str:
    if join["kind"] == "equi_join":
        left, right = join["left_relation"], join["right_relation"]
        pairs = ", ".join(
            f"{left}.{c['left_field']} = {right}.{c['right_field']}" for c in join["conditions"]
        )
    else:
        left = ", ".join(
            f"{relation}.{field}"
            for relation, fields in sorted(join["left_relations"].items())
            for field in fields
        )
        pairs = f"{left} = {join['right_relation']}.{join['right_field']}"
    return f"- {join_id} ({join['join_type']}): {pairs}"


def catalog_summary(catalog: Mapping) -> str:
    """Deterministic schema context for prompts with the catalog in context."""
    window = catalog["evaluation_window"]
    lines = ["GOOGLESQL ANALYTICAL CATALOG (BigQuery)", "", "MANAGED RELATIONS"]
    for relation_id, relation in sorted(catalog["analytical_relations"].items()):
        lines.extend(_relation_lines(relation_id, relation))
    lines += ["", "APPROVED JOINS"]
    lines += [_join_line(join_id, join) for join_id, join in sorted(catalog["join_paths"].items())]
    adjustments = [
        f"- {item['semantic_id']}: {item.get('reason', 'adjusted semantics')}"
        for item in catalog.get("semantic_mappings", [])
        if item.get("status") == "semantic_adjustment"
    ]
    if adjustments:
        lines += ["", "SEMANTIC ADJUSTMENTS", *adjustments]
    policies = catalog.get("interpretation_policies", {})
    if policies:
        lines += ["", "INTERPRETATION POLICIES"]
        lines += [f"- {term}: {rule}" for term, rule in sorted(policies.items())]
    lines += [
        "",
        _RULES.format(project=PROJECT_DATASET, start=window["start_date"], end=window["end_date"]),
    ]
    return "\n".join(lines) + "\n"


def compact_schema(catalog: Mapping) -> str:
    """Relation signatures only, for the fine-tuned model that learned the schema."""
    return "\n".join(
        relation_signature(relation_id, relation)
        for relation_id, relation in sorted(catalog["analytical_relations"].items())
    )


SYSTEM_WITH_CATALOG = (
    "You write GoogleSQL for Ethereum analytics on BigQuery. Use only the catalog below.\n\n"
    "{catalog}"
)
SYSTEM_COMPACT = (
    "You write GoogleSQL for Ethereum analytics on BigQuery over these managed relations:\n"
    "{schema}\n"
    "Return exactly one read-only query with explicit output columns and nothing else."
)


def system_prompt(catalog: Mapping, *, compact: bool) -> str:
    if compact:
        return SYSTEM_COMPACT.format(schema=compact_schema(catalog))
    return SYSTEM_WITH_CATALOG.format(catalog=catalog_summary(catalog))


def build_messages(
    question: str,
    *,
    system: str,
    examples: Sequence[Mapping] = (),
    linking: str | None = None,
) -> list[dict]:
    """Chat messages: optional examples and linking context, then the question."""
    parts = []
    if examples:
        shots = "\n\n".join(f"Question: {ex['question']}\nSQL: {ex['sql']}" for ex in examples)
        parts.append(f"Examples:\n{shots}")
    if linking:
        parts.append(linking)
    parts.append(f"Question: {question}\nSQL:")
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n\n".join(parts)},
    ]


def messages_digest(messages: Sequence[Mapping]) -> str:
    return json_digest(list(messages))

"""Run the three linkers on a question and render the prompt's linking block."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from eth_nl2sql.linking.dictionary import Dictionary
from eth_nl2sql.linking.entity import EntityLinker
from eth_nl2sql.linking.resolver import Resolution, Resolver, fact_of
from eth_nl2sql.linking.schema import SchemaLinker
from eth_nl2sql.linking.variants import VARIANTS

TOP_RELATIONS = 3
TOP_FIELDS = 6


@dataclass(frozen=True)
class Linking:
    relations: tuple[str, ...]
    fields: tuple[str, ...]
    entities: tuple[Resolution, ...]
    fact: str | None = None
    variant: str = "full"

    def to_json(self) -> dict:
        entities, classes, directions, roles = [], [], [], []
        for item in self.entities:
            values = classes if item.kind == "class" else entities
            target = f"{'class' if item.kind == 'class' else 'entity'}:{len(values)}"
            value = {
                "mention": {"text": item.span, "start": item.start, "end": item.end},
            }
            if item.kind == "class":
                value.update(
                    category=item.name, concept_class=item.concept_class, owners=list(item.owners)
                )
            else:
                value.update(
                    owner=item.name,
                    addresses=list(item.addresses),
                    address_scope=item.address_scope,
                    kind=item.kind,
                    concept_class=item.concept_class,
                    is_token=item.is_token,
                    candidates=list(item.candidates),
                    status="unresolved" if item.kind == "ambiguous" else "resolved",
                )
            values.append(value)
            directions.append(
                {
                    "target": target,
                    "value": None if item.direction == "unspecified" else item.direction,
                }
            )
            roles.append({"target": target, "value": item.address_role})
        return {
            "schema_version": 2,
            "variant": self.variant,
            "schema": {
                "relations": list(self.relations),
                "columns": [
                    {"relation": field.rsplit(".", 1)[0], "column": field.rsplit(".", 1)[1]}
                    for field in self.fields
                ],
            },
            "entities": entities,
            "classes": classes,
            "properties": {"direction": directions, "fact": self.fact, "address_role": roles},
        }

    @classmethod
    def from_json(cls, value: dict) -> Linking:
        if value.get("schema_version") == 2:
            properties = value["properties"]
            directions = {p["target"]: p["value"] for p in properties["direction"]}
            roles = {p["target"]: p["value"] for p in properties["address_role"]}
            items = []
            for kind, key in (("entity", "entities"), ("class", "classes")):
                for i, item in enumerate(value[key]):
                    target = f"{kind}:{i}"
                    mention = item["mention"]
                    items.append(
                        Resolution(
                            mention["text"],
                            "class" if kind == "class" else item["kind"],
                            directions.get(target) or "unspecified",
                            item["category"] if kind == "class" else item["owner"],
                            item.get("concept_class"),
                            tuple(item.get("addresses", ())),
                            tuple(item.get("candidates", ())),
                            item.get("is_token", False),
                            mention["start"],
                            mention["end"],
                            item.get("address_scope"),
                            tuple(item.get("owners", ())),
                            roles.get(target),
                        )
                    )
            items.sort(key=lambda item: item.start)
            return cls(
                tuple(value["schema"]["relations"]),
                tuple(f"{c['relation']}.{c['column']}" for c in value["schema"]["columns"]),
                tuple(items),
                properties["fact"],
                value.get("variant", "full"),
            )
        entities = tuple(
            Resolution(
                **{**e, "addresses": tuple(e["addresses"]), "candidates": tuple(e["candidates"])}
            )
            for e in value["entities"]
        )
        return cls(tuple(value["relations"]), tuple(value["fields"]), entities)


class LinkingPipeline:
    def __init__(
        self,
        dictionary: Dictionary,
        schema: SchemaLinker,
        entity: EntityLinker,
        *,
        variant: str = "full",
    ) -> None:
        self.variant = variant
        self.options = VARIANTS[variant]
        self.schema = schema
        self.entity = (
            entity
            if self.options.aliases and self.options.approximate
            else EntityLinker(
                dictionary,
                entity.encoder,
                aliases=self.options.aliases,
                approximate=self.options.approximate,
            )
        )
        self.resolver = Resolver(dictionary)

    def link(self, question: str) -> Linking:
        relations, fields = self.schema.link(question, top_k=max(TOP_RELATIONS, TOP_FIELDS))
        matches = self.entity.link(question)
        entities = self.resolver.resolve(question, matches, fields)
        fact = fact_of(question, entities) if self.options.properties else None
        entities = [item for item in entities if self.options.classes or item.kind != "class"]
        if not self.options.multi_address:
            entities = [
                replace(item, addresses=item.addresses[:1], address_scope="representative_address")
                if item.address_scope == "known_owner_addresses"
                else item
                for item in entities
            ]
        if not self.options.properties:
            entities = [
                replace(item, direction="unspecified", address_role=None) for item in entities
            ]
        return Linking(
            tuple(m.element_id for m in relations[:TOP_RELATIONS]),
            tuple(m.element_id for m in fields[:TOP_FIELDS]),
            tuple(entities),
            fact,
            self.variant,
        )


def link_rows(pipeline: LinkingPipeline, cases: Sequence[Mapping]) -> list[dict]:
    """Prediction boundary: only IDs and question strings enter the linker."""
    return [
        {
            "id": case["id"],
            "question": case["question"],
            "question_sha256": hashlib.sha256(case["question"].encode()).hexdigest(),
            "linking": pipeline.link(case["question"]).to_json(),
        }
        for case in cases
    ]


def _direction_note(direction: str) -> str:
    return {
        "from": "as sender (from_address)",
        "to": "as recipient (to_address)",
        "either": "either endpoint (from_address OR to_address)",
        "unspecified": "direction unresolved",
    }[direction]


def _entity_line(entity: Resolution, *, properties: bool = True) -> str:
    mention = f'"{entity.span}"'
    direction = f", {_direction_note(entity.direction)}" if properties else ""
    role = f", address role: {entity.address_role or 'unresolved'}" if properties else ""
    if entity.kind == "address":
        field = "token_address" if entity.address_role == "token_contract" else "address"
        return f"- {mention}: raw {field} {entity.addresses[0]}{direction}{role}"
    if entity.kind == "ambiguous":
        return f"- {mention}: ambiguous, could be {' | '.join(entity.candidates)}"
    if entity.kind == "class":
        return (
            f"- {mention}: entity class, filter entity_labels_v1.concept_class = "
            f"'{entity.concept_class}', known members: {', '.join(entity.owners)}{direction}"
        )
    if entity.address_scope in {"explicit_address", "representative_address"}:
        field = "token_address" if entity.address_role == "token_contract" else "address"
        return (
            f"- {mention}: owner '{entity.name}', filter {field} IN "
            f"({', '.join(repr(a) for a in entity.addresses)}){direction}{role}"
        )
    if entity.address_role == "token_contract":
        return (
            f"- {mention}: token contract {entity.name}, filter token_address IN "
            f"({', '.join(repr(a) for a in entity.addresses)})"
        )
    count = len(entity.addresses)
    return (
        f"- {mention}: entity owner '{entity.name}' with {count} labeled address"
        f"{'es' if count != 1 else ''}, filter entity_labels_v1.owner = '{entity.name}'"
        f"{direction}{role}"
    )


def render(linking: Linking) -> str:
    lines = [
        "Linking hints (automatic, may be incomplete):",
        f"- likely relations: {', '.join(linking.relations)}",
        f"- likely columns: {', '.join(linking.fields)}",
    ]
    properties = VARIANTS[linking.variant].properties
    lines += [_entity_line(entity, properties=properties) for entity in linking.entities]
    if properties:
        lines.append(f"- fact: {linking.fact or 'unresolved'}")
    return "\n".join(lines)

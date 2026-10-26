"""Run the three linkers on a question and render the prompt's linking block."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from eth_nl2sql.linking.dictionary import Dictionary
from eth_nl2sql.linking.entity import EntityLinker
from eth_nl2sql.linking.resolver import Resolution, Resolver
from eth_nl2sql.linking.schema import SchemaLinker

TOP_RELATIONS = 3
TOP_FIELDS = 6


@dataclass(frozen=True)
class Linking:
    relations: tuple[str, ...]
    fields: tuple[str, ...]
    entities: tuple[Resolution, ...]

    def to_json(self) -> dict:
        return {
            "relations": list(self.relations),
            "fields": list(self.fields),
            "entities": [asdict(entity) for entity in self.entities],
        }

    @classmethod
    def from_json(cls, value: dict) -> Linking:
        entities = tuple(
            Resolution(
                **{**e, "addresses": tuple(e["addresses"]), "candidates": tuple(e["candidates"])}
            )
            for e in value["entities"]
        )
        return cls(tuple(value["relations"]), tuple(value["fields"]), entities)


class LinkingPipeline:
    def __init__(self, dictionary: Dictionary, schema: SchemaLinker, entity: EntityLinker) -> None:
        self.schema = schema
        self.entity = entity
        self.resolver = Resolver(dictionary)

    def link(self, question: str) -> Linking:
        relations, fields = self.schema.link(question, top_k=max(TOP_RELATIONS, TOP_FIELDS))
        matches = self.entity.link(question)
        entities = self.resolver.resolve(question, matches, fields)
        return Linking(
            tuple(m.element_id for m in relations[:TOP_RELATIONS]),
            tuple(m.element_id for m in fields[:TOP_FIELDS]),
            tuple(entities),
        )


def _direction_note(direction: str) -> str:
    return {
        "from": "as sender (from_address)",
        "to": "as recipient (to_address)",
        "unspecified": "direction not stated (from_address or to_address)",
    }[direction]


def _entity_line(entity: Resolution) -> str:
    mention = f'"{entity.span}"'
    if entity.kind == "address":
        return (
            f"- {mention}: raw address {entity.addresses[0]}, {_direction_note(entity.direction)}"
        )
    if entity.kind == "ambiguous":
        return f"- {mention}: ambiguous, could be {' | '.join(entity.candidates)}"
    if entity.kind == "class":
        return (
            f"- {mention}: entity class, filter entity_labels_v1.concept_class = "
            f"'{entity.concept_class}', {_direction_note(entity.direction)}"
        )
    if entity.is_token:
        return f"- {mention}: token contract {entity.name} at {', '.join(entity.addresses)}"
    count = len(entity.addresses)
    return (
        f"- {mention}: entity owner '{entity.name}' with {count} labeled address"
        f"{'es' if count != 1 else ''}, filter entity_labels_v1.owner = '{entity.name}', "
        f"{_direction_note(entity.direction)}"
    )


def render(linking: Linking) -> str:
    lines = [
        "Linking hints (automatic, may be incomplete):",
        f"- likely relations: {', '.join(linking.relations)}",
        f"- likely columns: {', '.join(linking.fields)}",
    ]
    lines += [_entity_line(entity) for entity in linking.entities]
    return "\n".join(lines)

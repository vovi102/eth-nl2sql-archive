"""Turn entity matches into typed constraints (ported from luanvan `linking/resolver/`).

The four blockchain-specific cases are handled here:
- multi-address entity: an owner target carries all of its labeled addresses;
- alias: the exact/fuzzy/embedding stage already mapped the alias to its owner;
- class-level: "any DEX", "exchanges" resolve to a concept class;
- ambiguous property: the flow direction (from/to) comes from cue words, then
  from the schema linker, and stays "unspecified" otherwise.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from eth_nl2sql.linking.dictionary import Dictionary
from eth_nl2sql.linking.entity import EntityMatch
from eth_nl2sql.linking.schema import SchemaMatch

_FROM_CUE_RE = re.compile(r"\b(?:from|sent\s+by|out\s+of|outflows?\s+of)\b", re.IGNORECASE)
_TO_CUE_RE = re.compile(r"\b(?:to|into|received\s+by|inflows?\s+(?:of|to))\b", re.IGNORECASE)
_CLASS_TRIGGER_RE = re.compile(r"\b(?:any|all|every|major)\s+$", re.IGNORECASE)


@dataclass(frozen=True)
class Resolution:
    span: str
    kind: str  # instance | class | address | ambiguous
    direction: str  # from | to | unspecified
    name: str | None  # owner name or concept key
    concept_class: str | None
    addresses: tuple[str, ...]
    candidates: tuple[str, ...]  # alternative names when ambiguous
    is_token: bool = False


def direction_of(question: str, start: int) -> str:
    """Read the flow direction from cue words in the 40 characters before a mention."""
    prefix = question[max(0, start - 40) : start]
    from_cues = list(_FROM_CUE_RE.finditer(prefix))
    to_cues = list(_TO_CUE_RE.finditer(prefix))
    if from_cues and to_cues:
        source, destination = from_cues[-1], to_cues[-1]
        earlier, later = sorted((source, destination), key=lambda cue: cue.start())
        if prefix[earlier.end() : later.start()].casefold().strip() in {"and", "or", "and/or", "/"}:
            return "unspecified"
        return "from" if source.start() > destination.start() else "to"
    if from_cues:
        return "from"
    if to_cues:
        return "to"
    return "unspecified"


def _schema_direction(fields: Sequence[SchemaMatch]) -> str:
    directions = {
        "from" if match.element_id.endswith(".from_address") else "to"
        for match in fields[:3]
        if match.element_id.endswith((".from_address", ".to_address"))
    }
    return directions.pop() if len(directions) == 1 else "unspecified"


class Resolver:
    def __init__(self, dictionary: Dictionary) -> None:
        self.dictionary = dictionary

    def resolve(
        self,
        question: str,
        matches: Sequence[EntityMatch],
        schema_fields: Sequence[SchemaMatch] = (),
    ) -> list[Resolution]:
        fallback = _schema_direction(schema_fields)
        resolved = []
        for match in matches:
            direction = direction_of(question, match.start)
            if direction == "unspecified":
                direction = fallback
            resolved.append(self._resolve(question, match, direction))
        return resolved

    def _resolve(self, question: str, match: EntityMatch, direction: str) -> Resolution:
        if match.target_id.startswith("address:"):
            address = match.target_id.removeprefix("address:")
            return Resolution(match.span, "address", direction, None, None, (address,), ())
        if match.ambiguous:
            targets = [self.dictionary.by_id[target_id] for target_id in match.target_ids]
            prefix = question[max(0, match.start - 20) : match.start]
            class_trigger = bool(
                _CLASS_TRIGGER_RE.search(prefix)
            ) or match.span.casefold().endswith("s")
            concepts = [target for target in targets if target.kind == "concept"]
            if class_trigger and len(concepts) == 1:
                return self._concept(match, concepts[0], direction)
            return Resolution(
                match.span,
                "ambiguous",
                direction,
                None,
                None,
                (),
                tuple(target.name for target in targets),
            )
        target = self.dictionary.by_id[match.target_id]
        if target.kind == "concept":
            return self._concept(match, target, direction)
        return Resolution(
            match.span,
            "instance",
            direction,
            target.name,
            target.concept_classes[0] if len(target.concept_classes) == 1 else None,
            target.addresses,
            (),
            target.is_token_owner,
        )

    @staticmethod
    def _concept(match: EntityMatch, target, direction: str) -> Resolution:
        return Resolution(
            match.span, "class", direction, target.name, target.concept_classes[0], (), ()
        )

"""Resolve question evidence into owner/class constraints and three typed properties.

Ranked schema candidates are never evidence for a property: absent or conflicting
language stays unresolved. Explicit addresses retain their literal scope.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, replace

from eth_nl2sql.linking.dictionary import Dictionary
from eth_nl2sql.linking.entity import EntityMatch
from eth_nl2sql.linking.schema import SchemaMatch

_FROM_CUE_RE = re.compile(r"\b(?:from|sent\s+by|out\s+of|outflows?\s+of)\b", re.IGNORECASE)
_TO_CUE_RE = re.compile(r"\b(?:to|into|received\s+by|inflows?\s+(?:of|to))\b", re.IGNORECASE)
_CLASS_TRIGGER_RE = re.compile(r"\b(?:any|all|every|major)\s+$", re.IGNORECASE)
_EITHER_RE = re.compile(r"\b(?:between|involv(?:e|es|ed|ing)|inflows?\s+and\s+outflows?)\b", re.I)
_TOKEN_FACT_RE = re.compile(
    r"\b(?:token\s+(?:transfer|event)|transfer\s+(?:event|log)|erc[- ]?(?:20|721|1155))s?\b",
    re.I,
)
_TX_RE = re.compile(r"\b(?:transactions?|eth|ether|native(?:\s+transfers?)?)\b", re.I)
_TX_ONLY_RE = re.compile(
    r"\b(?:gas|fees?|transaction\s+(?:sender|status)|receipt\s+status)\b", re.I
)


@dataclass(frozen=True)
class Resolution:
    span: str
    kind: str  # instance | class | address | ambiguous
    direction: str  # from | to | either | unspecified
    name: str | None  # owner name or concept key
    concept_class: str | None
    addresses: tuple[str, ...]
    candidates: tuple[str, ...]  # alternative names when ambiguous
    is_token: bool = False
    start: int = -1
    end: int = -1
    address_scope: str | None = None
    owners: tuple[str, ...] = ()
    address_role: str | None = None


def direction_of(question: str, start: int, end: int | None = None) -> str:
    """Read local prepositions and subject verbs, distinguishing either from unknown."""
    prefix = re.split(r"[.;?!]", question[:start])[-1]
    from_cues = list(_FROM_CUE_RE.finditer(prefix))
    to_cues = list(_TO_CUE_RE.finditer(prefix))
    if from_cues and to_cues:
        source, destination = from_cues[-1], to_cues[-1]
        earlier, later = sorted((source, destination), key=lambda cue: cue.start())
        if prefix[earlier.end() : later.start()].casefold().strip() in {"and", "or", "and/or", "/"}:
            return "either"
        return "from" if source.start() > destination.start() else "to"
    if from_cues:
        return "from"
    if to_cues:
        return "to"
    if _EITHER_RE.search(prefix):
        return "either"
    if end is not None:
        suffix = question[end:]
        role = re.match(
            r"\s*(?:(?:address|wallet|account|contract)s?\s+)?"
            r"(?:as\s+(?:(?:their|the|a)\s+)?|on\s+(?:the\s+)?)"
            r"(sender|recipient|sending\s+side|receiving\s+side|either\s+endpoint)"
            r"(?:,?\s+(?:and|or)\s+(sender|recipient))?",
            suffix,
            re.I,
        )
        if role:
            roles = {v.lower() for v in role.groups() if v}
            if "either endpoint" in roles or {"sender", "recipient"} <= roles:
                return "either"
            return "from" if roles & {"sender", "sending side"} else "to"
        subject = re.match(
            r"\s*(?:'s\s+)?(?:(?:did|has|have|had|was|were|is|are|both)\s+)*"
            r"(send|sent|sending|receive|received|receiving|outflows?|inflows?)\b"
            r"(?:\s+and\s+(send|sent|receive|received))?",
            suffix,
            re.I,
        )
        if subject:
            values = {
                "from" if verb.lower().startswith(("sen", "out")) else "to"
                for verb in subject.groups()
                if verb
            }
            return values.pop() if len(values) == 1 else "either"
    return "unspecified"


def fact_of(question: str, entities: Sequence[Resolution] = ()) -> str | None:
    question = question.replace("-", " ")
    token = bool(_TOKEN_FACT_RE.search(question)) or (
        bool(re.search(r"\btransfers?\b", question, re.I))
        and any(item.is_token and item.direction == "unspecified" for item in entities)
    )
    transaction = bool(_TX_RE.search(question))
    if token and (transaction or _TX_ONLY_RE.search(question)):
        if _TX_ONLY_RE.search(question) or re.search(
            r"\b(?:join|joined|emitted|emitting|containing)\b", question, re.I
        ):
            return "transaction_token_transfer_join"
        return None
    if token:
        return "token_transfer"
    return "transaction" if transaction else None


def address_role_of(question: str, item: Resolution, fact: str | None) -> str | None:
    if item.kind == "ambiguous":
        return None
    if item.direction != "unspecified":
        return "endpoint"
    prefix = question[max(0, item.start - 40) : item.start]
    suffix = question[item.end : item.end + 40]
    if re.search(r"\b(?:token\s+contract|token_address)\s*(?:is|=|named)?\s*$", prefix, re.I):
        return "token_contract"
    if item.is_token and fact in {"token_transfer", "transaction_token_transfer_join"}:
        if re.search(r"\b(?:transfers?|events?|logs?)\b", prefix + " " + suffix, re.I):
            return "token_contract"
    return None


class Resolver:
    def __init__(self, dictionary: Dictionary) -> None:
        self.dictionary = dictionary

    def resolve(
        self,
        question: str,
        matches: Sequence[EntityMatch],
        schema_fields: Sequence[SchemaMatch] = (),
    ) -> list[Resolution]:
        resolved = []
        for match in matches:
            direction = direction_of(question, match.start, match.end)
            item = self._resolve(question, match, direction)
            scope = "explicit_address" if match.stage == "address" else "known_owner_addresses"
            addresses = (match.span.lower(),) if match.stage == "address" else item.addresses
            resolved.append(
                replace(
                    item,
                    start=match.start,
                    end=match.end,
                    addresses=addresses,
                    address_scope=scope if item.kind in {"instance", "address"} else None,
                )
            )
        fact = fact_of(question, resolved)
        return [
            replace(item, address_role=address_role_of(question, item, fact)) for item in resolved
        ]

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

    def _concept(self, match: EntityMatch, target, direction: str) -> Resolution:
        return Resolution(
            match.span,
            "class",
            direction,
            target.name,
            target.concept_classes[0],
            (),
            (),
            owners=tuple(
                sorted(t.name for t in self.dictionary.owners_of_class(target.concept_classes[0]))
            ),
        )

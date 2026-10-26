"""Entity dictionary loading: owner targets (one entity, many addresses) and concept targets.

Ported from luanvan `linking/entity/documents.py`. A dictionary directory holds
`entities.json` (one row per address), `aliases.json` (phrase -> owner or an
explicit list of ambiguous owners) and `concepts.json` (class key -> aliases,
description, instances). V2 includes a checksum/provenance manifest.
"""

from __future__ import annotations

import unicodedata
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote


def normalize_phrase(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


@dataclass(frozen=True)
class Target:
    target_id: str
    kind: str  # "owner" or "concept"
    name: str  # owner name or concept key
    addresses: tuple[str, ...]
    aliases: tuple[str, ...]
    categories: tuple[str, ...]
    concept_classes: tuple[str, ...]
    document: str

    @property
    def is_token_owner(self) -> bool:
        return self.kind == "owner" and (
            "token_contract" in self.categories or "TokenContract" in self.concept_classes
        )


@dataclass(frozen=True)
class Dictionary:
    targets: tuple[Target, ...]
    by_id: Mapping[str, Target]
    phrases: Mapping[str, tuple[str, ...]]
    address_targets: Mapping[str, str]

    def owners_of_class(self, concept_class: str) -> tuple[Target, ...]:
        return tuple(
            target
            for target in self.targets
            if target.kind == "owner" and concept_class in target.concept_classes
        )


def owner_id(owner: str) -> str:
    return f"owner:{quote(owner, safe='')}"


def load_dictionary(directory: Path) -> Dictionary:
    from eth_nl2sql.linking.validation import read_dictionary

    entities, aliases, concepts = read_dictionary(directory)

    rows_by_owner: dict[str, list[dict]] = defaultdict(list)
    for row in entities:
        rows_by_owner[row["owner"]].append(row)
    phrase_targets: dict[str, set[str]] = defaultdict(set)
    extra_aliases: dict[str, set[str]] = defaultdict(set)
    for phrase, owners in aliases.items():
        for owner in [owners] if isinstance(owners, str) else owners:
            extra_aliases[owner].add(normalize_phrase(phrase))

    targets: list[Target] = []
    address_targets: dict[str, str] = {}
    for owner, rows in sorted(rows_by_owner.items()):
        target_id = owner_id(owner)
        labels = sorted({row["primary_label"] for row in rows})
        names = {
            normalize_phrase(owner),
            *(normalize_phrase(label) for label in labels),
            *(normalize_phrase(alias) for row in rows for alias in row["aliases"]),
            *extra_aliases[owner],
        }
        categories = tuple(sorted({row["category"] for row in rows}))
        classes = tuple(sorted({row["concept_class"] for row in rows}))
        addresses = tuple(sorted({row["address"].lower() for row in rows}))
        document = "\n".join(
            [
                f"Owner: {owner}",
                f"Primary labels: {' | '.join(labels)}",
                f"Aliases: {' | '.join(sorted(names))}",
                f"Categories: {' | '.join(categories)}",
                f"Concept classes: {' | '.join(classes)}",
                f"Address roles: {' | '.join(sorted({row['address_role'] for row in rows}))}",
            ]
        )
        targets.append(
            Target(
                target_id,
                "owner",
                owner,
                addresses,
                tuple(sorted(names)),
                categories,
                classes,
                document,
            )
        )
        for phrase in names:
            phrase_targets[phrase].add(target_id)
        for address in addresses:
            address_targets[address] = target_id

    for key, info in sorted(concepts.items()):
        target_id = f"concept:{key}"
        names = {normalize_phrase(key), *(normalize_phrase(alias) for alias in info["aliases"])}
        concept_class = info["ontology_class"].rsplit("/", 1)[-1].rsplit("#", 1)[-1]
        instances = sorted(info["instances"])
        document = "\n".join(
            [
                f"Concept: {key}",
                f"Description: {info['description']}",
                f"Aliases: {' | '.join(sorted(names))}",
                f"Concept class: {concept_class}",
                f"Known owner count: {len(instances)}",
                f"Known owner sample: {' | '.join(instances[:50])}",
            ]
        )
        targets.append(
            Target(
                target_id,
                "concept",
                key,
                (),
                tuple(sorted(names)),
                (key,),
                (concept_class,),
                document,
            )
        )
        for phrase in names:
            phrase_targets[phrase].add(target_id)

    ordered = tuple(sorted(targets, key=lambda target: target.target_id))
    return Dictionary(
        targets=ordered,
        by_id={target.target_id: target for target in ordered},
        phrases={phrase: tuple(sorted(ids)) for phrase, ids in sorted(phrase_targets.items())},
        address_targets=dict(sorted(address_targets.items())),
    )

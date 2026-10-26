"""Schema linking: hybrid lexical + embedding ranking of relations and fields.

Ported from luanvan `linking/schema/` (documents built from the catalog,
score = 0.65 * cosine + 0.35 * lexical overlap with synonym expansion).
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

SEMANTIC_WEIGHT = 0.65
LEXICAL_WEIGHT = 0.35

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_CAMEL_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_TEMPORAL_CUE_RE = re.compile(
    r"\b(?:january|february|march|april|may|june|july|august|september|october|"
    r"november|december|20\d{2}|daily|days?|before|during)\b"
)
_TEMPORAL_TERMS = ("timestamp", "date", "time", "when")


def _words(value: str) -> tuple[str, ...]:
    expanded = _CAMEL_RE.sub(" ", value.lstrip(":"))
    normalized = unicodedata.normalize("NFKC", expanded).casefold().replace("_", " ")
    return tuple(_TOKEN_RE.findall(normalized))


@dataclass(frozen=True)
class SchemaElement:
    element_id: str  # "relation" or "relation.field"
    kind: str  # relation | field
    document: str


@dataclass(frozen=True)
class SchemaMatch:
    element_id: str
    kind: str
    score: float


def _semantics_by_element(catalog: Mapping) -> dict[str, set[str]]:
    index: dict[str, set[str]] = defaultdict(set)
    for item in catalog.get("semantic_mappings", []):
        for target in item.get("targets", []):
            relation = target.get("relation")
            if not relation:
                continue
            element = f"{relation}.{target['field']}" if target.get("field") else relation
            index[element].add(item["semantic_id"])
    return index


def _synonym_terms(element_id: str, semantics: set[str], synonyms: Mapping) -> list[str]:
    tokens = set(_words(element_id))
    for semantic_id in semantics:
        tokens.update(_words(semantic_id))
    terms = set()
    for token in tokens:
        if token in synonyms:
            terms.add(token)
            terms.update(synonyms[token])
    return sorted(terms)


def build_elements(catalog: Mapping, synonyms: Mapping[str, Sequence[str]]) -> list[SchemaElement]:
    semantics = _semantics_by_element(catalog)
    elements = []
    for relation_id, relation in sorted(catalog["analytical_relations"].items()):
        relation_semantics = semantics.get(relation_id, set())
        elements.append(
            SchemaElement(
                relation_id,
                "relation",
                "\n".join(
                    [
                        f"Relation: {' '.join(_words(relation_id))}",
                        f"Kind: {relation['kind']}",
                        f"Sources: {' '.join(sorted(relation['sources']))}",
                        f"Parameters: {' '.join(relation.get('parameters', {}))}",
                        f"Semantics: {' '.join(sorted(relation_semantics))}",
                        "Synonyms: "
                        + " ".join(_synonym_terms(relation_id, relation_semantics, synonyms)),
                    ]
                ),
            )
        )
        for field_id, field in sorted(relation["fields"].items()):
            element_id = f"{relation_id}.{field_id}"
            field_semantics = semantics.get(element_id, set())
            lineage = " ".join(f"{item['source']}.{item['field']}" for item in field["lineage"])
            elements.append(
                SchemaElement(
                    element_id,
                    "field",
                    "\n".join(
                        [
                            f"Field: {' '.join(_words(element_id))}",
                            f"Relation: {' '.join(_words(relation_id))}",
                            f"Type: {field['type']}",
                            f"Lineage: {lineage}",
                            f"Expression: {field.get('expression', '')}",
                            f"Semantics: {' '.join(sorted(field_semantics))}",
                            "Synonyms: "
                            + " ".join(_synonym_terms(element_id, field_semantics, synonyms)),
                        ]
                    ),
                )
            )
    return elements


class SchemaLinker:
    def __init__(
        self,
        catalog: Mapping,
        synonyms: Mapping[str, Sequence[str]],
        encoder: object | None = None,
    ) -> None:
        self.elements = build_elements(catalog, synonyms)
        self.encoder = encoder
        self._documents = [set(_words(element.document)) for element in self.elements]
        self._groups = [
            (tuple(_words(canonical)), [tuple(_words(p)) for p in (canonical, *aliases)])
            for canonical, aliases in sorted(synonyms.items())
        ]
        self._matrix = None
        if encoder is not None:
            vectors = encoder.encode([e.document for e in self.elements], normalize_embeddings=True)
            self._matrix = np.asarray(vectors, dtype=np.float32)

    def _lexical(self, tokens: tuple[str, ...], document: set[str]) -> float:
        base = set(tokens)
        expanded = set(base)
        phrases = []
        for canonical, group in self._groups:
            hits = [p for p in group if p and _contains(tokens, p)]
            if hits:
                phrases.extend(hits)
                expanded.update(word for phrase in group for word in phrase)
                expanded.update(canonical)
        base_score = len(base & document) / len(base)
        expanded_score = len(expanded & document) / len(expanded)
        phrase_score = float(any(set(phrase) <= document for phrase in phrases))
        return min(1.0, 0.6 * base_score + 0.3 * expanded_score + 0.1 * phrase_score)

    def link(self, question: str, top_k: int = 5) -> tuple[list[SchemaMatch], list[SchemaMatch]]:
        """Return (top relations, top fields)."""
        normalized = " ".join(unicodedata.normalize("NFKC", question).casefold().split())
        tokens = tuple(_TOKEN_RE.findall(normalized))
        field_tokens = tokens
        if _TEMPORAL_CUE_RE.search(normalized):
            field_tokens = tuple(dict.fromkeys((*tokens, *_TEMPORAL_TERMS)))
        if self._matrix is not None:
            query = np.asarray(
                self.encoder.encode(normalized, normalize_embeddings=True), dtype=np.float32
            )
            semantic = self._matrix @ query
        else:
            semantic = np.zeros(len(self.elements), dtype=np.float32)
        relations, fields = [], []
        for element, document, cosine in zip(self.elements, self._documents, semantic, strict=True):
            lexical = self._lexical(
                tokens if element.kind == "relation" else field_tokens, document
            )
            match = SchemaMatch(
                element.element_id,
                element.kind,
                SEMANTIC_WEIGHT * float(cosine) + LEXICAL_WEIGHT * lexical,
            )
            (relations if element.kind == "relation" else fields).append(match)

        def ranked(items: list[SchemaMatch]) -> list[SchemaMatch]:
            return sorted(items, key=lambda m: (-m.score, m.element_id))[:top_k]

        return ranked(relations), ranked(fields)


def _contains(tokens: tuple[str, ...], phrase: tuple[str, ...]) -> bool:
    width = len(phrase)
    return any(tokens[i : i + width] == phrase for i in range(len(tokens) - width + 1))

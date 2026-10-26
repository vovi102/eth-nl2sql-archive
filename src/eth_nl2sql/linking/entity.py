"""Entity linking cascade: address -> exact alias -> fuzzy alias -> embedding.

Ported from luanvan `linking/entity/linker.py` with the same thresholds
(fuzzy >= 0.85, embedding >= 0.75, ambiguity margin 0.03) and the same guard
that a single lower-case word only links to a token owner when written in
capitals (so "bob" stays a word while "BOB" may be a ticker).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
from rapidfuzz import process
from rapidfuzz.fuzz import ratio

from eth_nl2sql.linking.dictionary import Dictionary

FUZZY_THRESHOLD = 0.85
EMBEDDING_THRESHOLD = 0.75
AMBIGUITY_MARGIN = 0.03
MAX_WINDOW_TOKENS = 5

_ADDRESS_RE = re.compile(r"(?<!\w)0x[0-9a-f]{40}(?!\w)", re.IGNORECASE)
_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)

# Snowball English stop list (snapshot vendored in luanvan) plus request verbs and modals.
FUNCTION_WORDS = frozenset(
    """
    i me my myself we our ours ourselves you your yours yourself yourselves he him his himself
    she her hers herself it its itself they them their theirs themselves what which who whom
    this that these those am is are was were be been being have has had having do does did
    doing would should could ought m re s ve d ll isn t aren wasn weren hasn haven hadn doesn
    don didn won wouldn shan shouldn can cannot couldn mustn let a an the and but if or because
    as until while of at by for with about against between into through during before after
    above below to from up down in out on off over under again further then once here there
    when where why how all any both each few more most other some such no nor not only own same
    so than too very please show list tell give get find provide display need may might must
    shall will
    """.split()
)


@dataclass(frozen=True)
class EntityMatch:
    span: str
    start: int
    end: int
    target_ids: tuple[str, ...]  # best first; more than one means ambiguous
    stage: str  # address | exact | fuzzy | embedding
    confidence: float

    @property
    def target_id(self) -> str:
        return self.target_ids[0]

    @property
    def ambiguous(self) -> bool:
        return len(self.target_ids) > 1


@dataclass(frozen=True)
class _Window:
    text: str
    start: int
    end: int
    tokens: int


def _lower(question: str) -> str:
    """Lower-case without changing string length, so offsets stay aligned."""
    return "".join(ch.lower() if len(ch.lower()) == 1 else ch for ch in question)


def _bounded(text: str, start: int, end: int) -> bool:
    return (start == 0 or not text[start - 1].isalnum()) and (
        end == len(text) or not text[end].isalnum()
    )


def _overlaps(start: int, end: int, matches: list[EntityMatch]) -> bool:
    return any(start < match.end and match.start < end for match in matches)


class EntityLinker:
    def __init__(self, dictionary: Dictionary, encoder: object | None = None) -> None:
        self.dictionary = dictionary
        self.encoder = encoder
        self._phrases = tuple(dictionary.phrases)
        self._token_owner_ids = frozenset(
            t.target_id for t in dictionary.targets if t.is_token_owner
        )
        self._target_matrix = None
        if encoder is not None:
            documents = [target.document for target in dictionary.targets]
            matrix = encoder.encode(documents, normalize_embeddings=True)
            self._target_matrix = np.asarray(matrix, dtype=np.float32)

    def link(self, question: str) -> list[EntityMatch]:
        text = _lower(question)
        selected = self._select(self._addresses(question) + self._exact(question, text))
        selected = self._select(selected + self._select(self._fuzzy(question, text, selected)))
        if self._target_matrix is not None:
            selected = self._select(
                selected + self._select(self._embedding(question, text, selected))
            )
        return sorted(selected, key=lambda match: match.start)

    def _needs_signal(self, phrase: str, target_ids: tuple[str, ...], span: str) -> bool:
        return (
            _TOKEN_RE.fullmatch(phrase) is not None
            and all(target_id in self._token_owner_ids for target_id in target_ids)
            and not span.isupper()
        )

    def _token_needs_name(self, target_ids: tuple[str, ...], span: str) -> bool:
        """Token names are proper nouns: approximate matches need a capital letter."""
        return all(t in self._token_owner_ids for t in target_ids) and not any(
            ch.isupper() for ch in span
        )

    def _addresses(self, question: str) -> list[EntityMatch]:
        matches = []
        for found in _ADDRESS_RE.finditer(question):
            address = found.group().lower()
            target_id = self.dictionary.address_targets.get(address, f"address:{address}")
            matches.append(
                EntityMatch(found.group(), found.start(), found.end(), (target_id,), "address", 1.0)
            )
        return matches

    def _exact(self, question: str, text: str) -> list[EntityMatch]:
        matches = []
        for phrase, target_ids in self.dictionary.phrases.items():
            start = text.find(phrase)
            while start >= 0:
                end = start + len(phrase)
                span = question[start:end]
                if _bounded(text, start, end):
                    exact_owner = tuple(
                        target_id
                        for target_id in target_ids
                        if self.dictionary.by_id[target_id].name == span
                    )
                    ordered = exact_owner + tuple(t for t in target_ids if t not in exact_owner)
                    if exact_owner or not self._needs_signal(phrase, target_ids, span):
                        matches.append(EntityMatch(span, start, end, ordered[:3], "exact", 1.0))
                start = text.find(phrase, start + 1)
        return matches

    def _windows(self, text: str, covered: list[EntityMatch]) -> list[_Window]:
        tokens = list(_TOKEN_RE.finditer(text))
        windows = []
        for first_index in range(len(tokens)):
            for size in range(1, min(MAX_WINDOW_TOKENS, len(tokens) - first_index) + 1):
                first, last = tokens[first_index], tokens[first_index + size - 1]
                if _overlaps(first.start(), last.end(), covered):
                    continue
                window = text[first.start() : last.end()]
                words = _TOKEN_RE.findall(window)
                if not any(ch.isalpha() for word in words for ch in word):
                    continue
                if all(word in FUNCTION_WORDS for word in words):
                    continue
                windows.append(_Window(window, first.start(), last.end(), size))
        return windows

    def _ranked(
        self, scores: dict[str, float], cutoff: float
    ) -> tuple[tuple[str, ...], float] | None:
        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        if not ranked or ranked[0][1] < cutoff:
            return None
        best = ranked[0][1]
        accepted = [target_id for target_id, score in ranked if best - score < AMBIGUITY_MARGIN]
        return tuple(accepted[:3]), best

    def _fuzzy(self, question: str, text: str, covered: list[EntityMatch]) -> list[EntityMatch]:
        matches = []
        for window in self._windows(text, covered):
            words = _TOKEN_RE.findall(window.text)
            scores: dict[str, float] = {}
            for phrase, raw, _ in process.extract(
                window.text,
                self._phrases,
                scorer=ratio,
                score_cutoff=FUZZY_THRESHOLD * 100,
                limit=None,
            ):
                phrase_words = _TOKEN_RE.findall(phrase)
                if (words[0] in FUNCTION_WORDS and words[0] != phrase_words[0]) or (
                    words[-1] in FUNCTION_WORDS and words[-1] != phrase_words[-1]
                ):
                    continue
                target_ids = self.dictionary.phrases[phrase]
                span = question[window.start : window.end]
                if window.tokens == 1 and self._needs_signal(phrase, target_ids, span):
                    continue
                for target_id in target_ids:
                    scores[target_id] = max(scores.get(target_id, 0.0), raw / 100.0)
            ranked = self._ranked(scores, FUZZY_THRESHOLD)
            span = question[window.start : window.end]
            if ranked and not self._token_needs_name(ranked[0], span):
                ids, confidence = ranked
                matches.append(
                    EntityMatch(span, window.start, window.end, ids, "fuzzy", confidence)
                )
        return matches

    def _embedding(self, question: str, text: str, covered: list[EntityMatch]) -> list[EntityMatch]:
        windows = self._windows(text, covered)
        if not windows:
            return []
        vectors = np.asarray(
            self.encoder.encode([w.text for w in windows], normalize_embeddings=True),
            dtype=np.float32,
        )
        matches = []
        for window, row in zip(windows, vectors @ self._target_matrix.T, strict=True):
            scores = {
                target.target_id: min(1.0, float(score))
                for target, score in zip(self.dictionary.targets, row, strict=True)
                if score >= EMBEDDING_THRESHOLD
            }
            ranked = self._ranked(scores, EMBEDDING_THRESHOLD)
            if not ranked:
                continue
            ids, confidence = ranked
            span = question[window.start : window.end]
            if self._token_needs_name(ids, span):
                continue
            if (
                window.tokens == 1
                and not span.isupper()
                and all(i in self._token_owner_ids for i in ids)
            ):
                continue
            matches.append(
                EntityMatch(span, window.start, window.end, ids, "embedding", confidence)
            )
        return matches

    @staticmethod
    def _select(candidates: list[EntityMatch]) -> list[EntityMatch]:
        """Keep non-overlapping matches: addresses first, then longer spans, then earlier."""
        ordered = sorted(
            candidates,
            key=lambda m: (
                0 if m.stage == "address" else 1,
                -(m.end - m.start),
                m.start,
                m.target_id,
            ),
        )
        selected: list[EntityMatch] = []
        for match in ordered:
            if not _overlaps(match.start, match.end, selected):
                selected.append(match)
        return selected

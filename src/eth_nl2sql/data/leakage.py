"""Train/test leakage checks and family-level splits (ported from luanvan `assembly.py`).

A training question leaks if its normalized text equals a held-out question or
if it shares any 12-token n-gram with one. Splits hash the semantic family id,
so all phrasings of one SQL land on the same side.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence

from eth_nl2sql.generation.retrieval import normalize_question

NGRAM_SIZE = 12


def _ngrams(question: str, size: int) -> set[tuple[str, ...]]:
    tokens = normalize_question(question).split()
    return {tuple(tokens[i : i + size]) for i in range(len(tokens) - size + 1)}


def leaked_ids(
    training: Sequence[Mapping], held_out_questions: Iterable[str], *, size: int = NGRAM_SIZE
) -> list[str]:
    """Return ids of training records that overlap a held-out question."""
    held_out = list(held_out_questions)
    exact = {normalize_question(question) for question in held_out}
    grams = set().union(*(_ngrams(question, size) for question in held_out)) if held_out else set()
    return sorted(
        record["id"]
        for record in training
        if normalize_question(record["question"]) in exact
        or _ngrams(record["question"], size) & grams
    )


def family_split(family_id: str, *, seed: int = 42, development_percent: int = 10) -> str:
    bucket = int(hashlib.sha256(f"{seed}:{family_id}".encode()).hexdigest()[:8], 16) % 100
    return "development" if bucket < development_percent else "train"

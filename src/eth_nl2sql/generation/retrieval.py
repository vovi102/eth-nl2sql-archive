"""Few-shot example retrieval (B2) and the shared sentence encoder."""

from __future__ import annotations

import unicodedata
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import numpy as np

from eth_nl2sql.artifacts import read_jsonl


def cached_retriever(
    path: Path,
    cases: Sequence[Mapping],
    train: Sequence[Mapping],
    *,
    k: int = 5,
) -> Callable[[Mapping], list[Mapping]]:
    """Reuse an exact training-example selection after checking IDs and leakage."""
    rows = read_jsonl(path)
    selected = {row["id"]: row["example_ids"] for row in rows}
    if len(selected) != len(rows) or set(selected) != {c["id"] for c in cases}:
        raise ValueError("Example cache must cover exactly the split IDs, without duplicates")
    train_index = {row["id"]: row for row in train}
    examples = {}
    for case in cases:
        ids = selected[case["id"]]
        if len(ids) != k or len(set(ids)) != k or not set(ids) <= train_index.keys():
            raise ValueError("Example cache needs five distinct training IDs per question")
        shots = [train_index[key] for key in ids]
        if any(
            (case.get("family_id") is not None and shot.get("family_id") == case["family_id"])
            or normalize_question(shot["question"]) == normalize_question(case["question"])
            for shot in shots
        ):
            raise ValueError("Example cache leaks the question or its family")
        examples[case["id"]] = shots
    return lambda case: examples[case["id"]]


def example_retriever(
    train: Sequence[Mapping],
    settings: Mapping,
    *,
    encoder=None,
    k: int | None = None,
) -> FewShotRetriever:
    return FewShotRetriever(
        train,
        encoder if encoder is not None else load_encoder(settings),
        k=settings["retrieval"]["examples"] if k is None else k,
    )


def load_encoder(config: Mapping):
    """Load the pinned MiniLM encoder (requires the `embed` extra)."""
    from sentence_transformers import SentenceTransformer

    encoder = config["models"]["encoder"]
    return SentenceTransformer(encoder["repo_id"], revision=encoder["revision"], device="cpu")


def normalize_question(question: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", question).casefold().split())


class FewShotRetriever:
    """Top-k training examples by cosine similarity, ties broken by record id."""

    def __init__(self, records: Sequence[Mapping], encoder, *, k: int = 5) -> None:
        self.records = list(records)
        self.encoder = encoder
        self.k = k
        self._normalized = [normalize_question(r["question"]) for r in self.records]
        vectors = encoder.encode([r["question"] for r in self.records], normalize_embeddings=True)
        self._matrix = np.asarray(vectors, dtype=np.float32)

    def __call__(self, case: Mapping) -> list[Mapping]:
        return self.retrieve(case["question"], exclude_family=case.get("family_id"))

    def retrieve(self, question: str, *, exclude_family: str | None = None) -> list[Mapping]:
        """Exclude the question's own semantic family and identical questions."""
        query = np.asarray(
            self.encoder.encode([question], normalize_embeddings=True), dtype=np.float32
        )[0]
        scores = self._matrix @ query
        target = normalize_question(question)
        ranked = sorted(
            range(len(self.records)), key=lambda i: (-float(scores[i]), self.records[i]["id"])
        )
        chosen = []
        for index in ranked:
            record = self.records[index]
            if record.get("family_id") == exclude_family or self._normalized[index] == target:
                continue
            chosen.append(record)
            if len(chosen) == self.k:
                break
        return chosen

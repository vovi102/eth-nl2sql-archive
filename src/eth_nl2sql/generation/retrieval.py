"""Few-shot example retrieval (B2) and the shared sentence encoder."""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence

import numpy as np


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

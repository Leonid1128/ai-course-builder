from __future__ import annotations

import math
import re
from typing import Any
from uuid import UUID

from apps.common.interfaces import EmbeddingClientProtocol, VectorStoreProtocol
from apps.uploads.models import MaterialEmbedding

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norm_l = math.sqrt(sum(a * a for a in left))
    norm_r = math.sqrt(sum(b * b for b in right))
    if norm_l == 0.0 or norm_r == 0.0:
        return 0.0
    return dot / (norm_l * norm_r)


def lexical_score(query: str, text: str) -> float:
    query_tokens = set(_TOKEN_RE.findall(query.lower()))
    if not query_tokens:
        return 0.0
    text_tokens = set(_TOKEN_RE.findall(text.lower()))
    return len(query_tokens & text_tokens) / len(query_tokens)


class DjangoVectorStore(VectorStoreProtocol):
    """Course-scoped RAG over `MaterialEmbedding`. Falls back to lexical ranking."""

    def __init__(self, embedding_client: EmbeddingClientProtocol | None = None) -> None:
        self._embeddings = embedding_client

    def similarity_search(
        self,
        query: str,
        *,
        course_id: UUID | str,
        k: int = 5,
    ) -> list[dict[str, Any]]:
        chunks = list(
            MaterialEmbedding.objects.filter(
                material__course_id=course_id,
                material__embedding_status=True,
            ).select_related("material")
        )
        if not chunks:
            return []

        scored: list[tuple[float, MaterialEmbedding]]
        query_vector = self._embed_query(query)
        if query_vector is not None:
            scored = []
            for chunk in chunks:
                vector = chunk.embedding_vector or []
                if vector:
                    scored.append((cosine_similarity(query_vector, vector), chunk))
                else:
                    scored.append((lexical_score(query, chunk.chunk_text), chunk))
        else:
            scored = [(lexical_score(query, chunk.chunk_text), chunk) for chunk in chunks]

        scored.sort(key=lambda item: item[0], reverse=True)
        results: list[dict[str, Any]] = []
        for score, chunk in scored[:k]:
            if score <= 0:
                continue
            results.append(
                {
                    "text": chunk.chunk_text,
                    "score": score,
                    "metadata": {
                        **(chunk.chunk_metadata or {}),
                        "filename": chunk.material.filename,
                        "material_id": str(chunk.material.id),
                    },
                }
            )
        return results

    def _embed_query(self, query: str) -> list[float] | None:
        if self._embeddings is None:
            return None
        try:
            vectors = self._embeddings.embed([query])
        except Exception:
            return None
        return vectors[0] if vectors else None


# Backwards-compatible name used by older imports/tests.
class PGVectorStore(DjangoVectorStore):
    def __init__(self, connection_string: str | None = None, embedding_function: object = None) -> None:
        del connection_string, embedding_function
        super().__init__(embedding_client=None)

"""SemanticSearchEngine - Embedding-based semantic search (R5)."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class Embedding:
    """A vector embedding."""

    vector: list[float] = field(default_factory=list)
    content_hash: str = ""
    message_id: str = ""
    dimension: int = 0

    def to_list(self) -> list[float]:
        """Convert to list."""
        return self.vector

    @classmethod
    def from_list(cls, data: list[float]) -> Embedding:
        """Create from list."""
        return cls(vector=data, dimension=len(data))


class SemanticSearchEngine:
    """Semantic search engine using local embeddings (R5).

    Provides meaning-based search using cosine similarity
    between embedding vectors.
    """

    # Constraints (R5)
    MIN_QUERY_LENGTH = 2
    MIN_SIMILARITY = 0.7
    MAX_RESULTS = 50
    SEARCH_TIMEOUT_MS = 5000  # 5 seconds (R5)

    def __init__(self, dimension: int = 768):
        """Initialize the semantic search engine.

        Args:
            dimension: Embedding vector dimension.
        """
        self.dimension = dimension
        self._embeddings: dict[str, Embedding] = {}  # content_hash -> embedding
        self._message_embeddings: dict[str, str] = {}  # message_id -> content_hash
        self._query_index: dict[str, list[str]] = {}  # query_term -> message_ids

    def compute_cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            vec_a: First vector.
            vec_b: Second vector.

        Returns:
            Cosine similarity score (0.0 to 1.0).
        """
        if not vec_a or not vec_b:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        mag_a = math.sqrt(sum(a * a for a in vec_a))
        mag_b = math.sqrt(sum(b * b for b in vec_b))

        if mag_a == 0 or mag_b == 0:
            return 0.0

        return dot_product / (mag_a * mag_b)

    def add_embedding(
        self,
        message_id: str,
        vector: list[float],
        content_hash: str = "",
    ) -> bool:
        """Add an embedding for a message.

        Args:
            message_id: The message ID.
            vector: The embedding vector.
            content_hash: Content hash for deduplication.

        Returns:
            True if added.
        """
        if not vector:
            return False

        if len(vector) != self.dimension:
            # Pad or truncate to match dimension
            if len(vector) < self.dimension:
                vector = vector + [0.0] * (self.dimension - len(vector))
            else:
                vector = vector[:self.dimension]

        embedding = Embedding(
            vector=vector,
            content_hash=content_hash or f"emb_{message_id}",
            message_id=message_id,
            dimension=len(vector),
        )

        self._embeddings[embedding.content_hash] = embedding
        self._message_embeddings[message_id] = embedding.content_hash

        return True

    def search(
        self,
        query_vector: list[float],
        min_similarity: float | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Search for semantically similar messages.

        Args:
            query_vector: Query embedding vector.
            min_similarity: Minimum cosine similarity (default: 0.7).
            limit: Maximum results.

        Returns:
            List of search results with similarity scores.
        """
        if min_similarity is None:
            min_similarity = self.MIN_SIMILARITY

        results = []

        for content_hash, embedding in self._embeddings.items():
            similarity = self.compute_cosine_similarity(query_vector, embedding.vector)

            if similarity >= min_similarity:
                results.append({
                    "message_id": embedding.message_id,
                    "content_hash": content_hash,
                    "similarity": similarity,
                    "dimension": embedding.dimension,
                })

        # Sort by similarity (descending)
        results.sort(key=lambda r: r["similarity"], reverse=True)

        return results[:limit]

    def search_by_text(
        self,
        query_text: str,
        text_to_embedding: dict[str, list[float]],
        min_similarity: float | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Search by text using pre-computed embeddings.

        Args:
            query_text: Query text.
            text_to_embedding: Mapping of text to embedding vectors.
            min_similarity: Minimum similarity threshold.
            limit: Maximum results.

        Returns:
            List of search results.
        """
        if len(query_text.strip()) < self.MIN_QUERY_LENGTH:
            return []

        # Get query embedding
        query_vec = text_to_embedding.get(query_text)
        if not query_vec:
            return []

        return self.search(query_vec, min_similarity, limit)

    def get_embedding(self, message_id: str) -> Embedding | None:
        """Get embedding for a message.

        Args:
            message_id: The message ID.

        Returns:
            The Embedding or None.
        """
        content_hash = self._message_embeddings.get(message_id)
        if content_hash:
            return self._embeddings.get(content_hash)
        return None

    def get_or_create_embedding(
        self,
        message_id: str,
        content_hash: str = "",
    ) -> Embedding:
        """Get existing or create new embedding.

        Args:
            message_id: The message ID.
            content_hash: Content hash.

        Returns:
            The Embedding.
        """
        existing = self.get_embedding(message_id)
        if existing:
            return existing

        new_embedding = Embedding(
            vector=[0.0] * self.dimension,
            content_hash=content_hash or f"emb_{message_id}",
            message_id=message_id,
            dimension=self.dimension,
        )

        self._embedments[new_embedding.content_hash] = new_embedding
        self._message_embeddings[message_id] = new_embedding.content_hash

        return new_embedding

    def has_embedding(self, message_id: str) -> bool:
        """Check if a message has an embedding.

        Args:
            message_id: The message ID.

        Returns:
            True if embedding exists.
        """
        return message_id in self._message_embeddings

    def remove_embedding(self, message_id: str) -> bool:
        """Remove an embedding.

        Args:
            message_id: The message ID.

        Returns:
            True if removed.
        """
        content_hash = self._message_embeddings.pop(message_id, None)
        if content_hash and content_hash in self._embeddings:
            del self._embeddings[content_hash]
            return True
        return False

    def get_embedding_count(self) -> int:
        """Get total embedding count.

        Returns:
            Number of embeddings.
        """
        return len(self._embeddings)

    def incremental_update(
        self,
        new_embeddings: dict[str, list[float]],
    ) -> int:
        """Incrementally update embeddings without reprocessing all.

        Args:
            new_embeddings: Mapping of message_id to vector.

        Returns:
            Number of embeddings added.
        """
        added = 0
        for message_id, vector in new_embeddings.items():
            if not self.has_embedding(message_id):
                self.add_embedding(message_id, vector)
                added += 1
        return added

    def to_dict(self) -> dict[str, Any]:
        """Serialize engine state."""
        return {
            "dimension": self.dimension,
            "embedding_count": len(self._embeddings),
            "message_embedding_count": len(self._message_embeddings),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"SemanticSearchEngine(dimension={self.dimension}, "
            f"embeddings={len(self._embeddings)})"
        )

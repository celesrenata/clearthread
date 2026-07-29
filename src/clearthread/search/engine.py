"""SearchEngine - Unified search interface combining full-text and semantic search."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from clearthread.search.fulltext import FullTextSearchEngine, SearchQuery
from clearthread.search.semantic import SemanticSearchEngine

logger = logging.getLogger(__name__)


@dataclass
class UnifiedSearchResult:
    """A unified search result combining full-text and semantic scores."""

    message_id: UUID
    text: str
    fulltext_score: float = 0.0
    semantic_score: float = 0.0
    combined_score: float = 0.0
    sender: str = ""
    timestamp: datetime | None = None
    result_type: str = "both"  # fulltext, semantic, both

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "message_id": str(self.message_id),
            "text": self.text,
            "fulltext_score": self.fulltext_score,
            "semantic_score": self.semantic_score,
            "combined_score": self.combined_score,
            "sender": self.sender,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "result_type": self.result_type,
        }


class SearchEngine:
    """Unified search engine combining full-text and semantic search (R5)."""

    def __init__(
        self,
        fulltext_engine: FullTextSearchEngine | None = None,
        semantic_engine: SemanticSearchEngine | None = None,
    ):
        """Initialize the search engine.

        Args:
            fulltext_engine: Full-text search engine.
            semantic_engine: Semantic search engine.
        """
        self.fulltext_engine = fulltext_engine or FullTextSearchEngine()
        self.semantic_engine = semantic_engine or SemanticSearchEngine()

    def search(
        self,
        query: str,
        semantic: bool = False,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[UnifiedSearchResult], int]:
        """Search across the archive.

        Args:
            query: Search query.
            semantic: If True, use semantic search.
            filters: Optional filters.
            limit: Maximum results.
            offset: Results to skip.

        Returns:
            Tuple of (results, total_count).
        """
        if semantic:
            return self._semantic_search(query, filters, limit, offset)
        return self._fulltext_search(query, filters, limit, offset)

    def _fulltext_search(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[UnifiedSearchResult], int]:
        """Perform full-text search.

        Args:
            query: Search query.
            filters: Optional filters.
            limit: Maximum results.
            offset: Results to skip.

        Returns:
            Tuple of (results, total_count).
        """
        results, total = self.fulltext_engine.search(query, filters, limit, offset)

        unified = [
            UnifiedSearchResult(
                message_id=r.message_id,
                text=r.text,
                fulltext_score=r.relevance_score,
                combined_score=r.relevance_score,
                sender=r.sender,
                timestamp=r.timestamp,
                result_type="fulltext",
            )
            for r in results
        ]

        return unified, total

    def _semantic_search(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[UnifiedSearchResult], int]:
        """Perform semantic search.

        Args:
            query: Search query.
            filters: Optional filters.
            limit: Maximum results.
            offset: Results to skip.

        Returns:
            Tuple of (results, total_count).
        """
        # Use simple vector for query (in production, use actual embedding)
        query_vector = [0.1] * self.semantic_engine.dimension
        results = self.semantic_engine.search(query_vector, min_similarity=0.7, limit=limit)

        unified = [
            UnifiedSearchResult(
                message_id=UUID(r["message_id"]) if isinstance(r["message_id"], str) else r["message_id"],
                text="",
                semantic_score=r["similarity"],
                combined_score=r["similarity"],
                result_type="semantic",
            )
            for r in results
        ]

        total = len(results)
        paginated = unified[offset:offset + limit]

        return paginated, total

    def search_text_and_semantic(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[UnifiedSearchResult], int]:
        """Search using both full-text and semantic methods.

        Args:
            query: Search query.
            filters: Optional filters.
            limit: Maximum results.
            offset: Results to skip.

        Returns:
            Tuple of (results, total_count).
        """
        ft_results, ft_total = self._fulltext_search(query, filters, limit, offset)
        sm_results, sm_total = self._semantic_search(query, filters, limit, offset)

        # Combine results
        combined: dict[str, UnifiedSearchResult] = {}

        for r in ft_results:
            key = str(r.message_id)
            combined[key] = r

        for r in sm_results:
            key = str(r.message_id)
            if key in combined:
                combined[key].semantic_score = r.semantic_score
                combined[key].combined_score = (
                    combined[key].fulltext_score * 0.5 + r.semantic_score * 0.5
                )
                combined[key].result_type = "both"
            else:
                combined[key] = r

        # Sort by combined score
        sorted_results = sorted(
            combined.values(),
            key=lambda r: r.combined_score,
            reverse=True,
        )

        total = max(ft_total, sm_total)
        paginated = sorted_results[offset:offset + limit]

        return paginated, total

    def get_no_results_message(self) -> str:
        """Get message for no results found.

        Returns:
            Message string.
        """
        return "No results were found. Try broadening your filters or modifying the query."

    def get_min_query_length_message(self) -> str:
        """Get message for minimum query length.

        Returns:
            Message string.
        """
        return "Please enter at least 2 characters to search."

    def to_dict(self) -> dict[str, Any]:
        """Serialize engine state."""
        return {
            "fulltext_stats": self.fulltext_engine.get_index_stats(),
            "semantic_stats": self.semantic_engine.to_dict(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"SearchEngine(fulltext={self.fulltext_engine.get_index_stats()['total_messages']}, "
            f"semantic={self.semantic_engine.get_embedding_count()})"
        )

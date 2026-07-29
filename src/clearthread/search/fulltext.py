"""FullTextSearchEngine - Full-text search with TF/recency ranking (R5)."""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result."""

    message_id: UUID
    text: str
    relevance_score: float = 0.0
    sender: str = ""
    timestamp: datetime | None = None
    context_before: list[str] = field(default_factory=list)
    context_after: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "message_id": str(self.message_id),
            "text": self.text,
            "relevance_score": self.relevance_score,
            "sender": self.sender,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "context_before": self.context_before,
            "context_after": self.context_after,
        }


@dataclass
class SearchQuery:
    """A search query with filters."""

    query_text: str = ""
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None
    participant_id: UUID | None = None
    conversation_id: UUID | None = None
    attachment_present: bool | None = None
    user_authored_only: bool | None = None
    episode_type: str | None = None
    annotation_present: bool | None = None
    finding_association: str | None = None
    pagination_page: int = 0
    page_size: int = 50

    @property
    def min_query_length(self) -> int:
        """Minimum query length (R5)."""
        return 2

    @property
    def has_valid_query(self) -> bool:
        """Check if query meets minimum length."""
        return len(self.query_text.strip()) >= self.min_query_length


class FullTextSearchEngine:
    """Full-text search engine (R5).

    Provides exact text matching with relevance scoring based on
    term frequency and recency.
    """

    # Constraints (R5)
    MAX_SAVED_QUERIES = 100
    MAX_QUERY_LENGTH = 1000
    FIRST_PAGE_RESULTS = 50
    SEARCH_TIMEOUT_MS = 2000  # 2 seconds (R5)

    def __init__(self):
        """Initialize the full-text search engine."""
        self._index: dict[str, list[str]] = {}  # term -> message_ids
        self._messages: dict[str, dict[str, Any]] = {}  # message_id -> message_data
        self._saved_queries: dict[str, dict[str, Any]] = {}  # query_name -> query_data
        self._term_frequencies: dict[str, dict[str, int]] = {}  # term -> {message_id: freq}

    def index_message(self, message_id: str, text: str, metadata: dict[str, Any] | None = None) -> bool:
        """Index a message for full-text search.

        Args:
            message_id: The message ID.
            text: The message text.
            metadata: Optional message metadata.

        Returns:
            True if indexed.
        """
        if not text or len(text.strip()) < 2:
            return False

        self._messages[message_id] = {
            "text": text,
            "metadata": metadata or {},
        }

        # Tokenize text
        tokens = self._tokenize(text)

        # Update index
        for token in tokens:
            if token not in self._index:
                self._index[token] = []
            if message_id not in self._index[token]:
                self._index[token].append(message_id)

            # Update term frequency
            if token not in self._term_frequencies:
                self._term_frequencies[token] = {}
            self._term_frequencies[token][message_id] = (
                self._term_frequencies[token].get(message_id, 0) + 1
            )

        return True

    def search(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SearchResult], int]:
        """Search for messages matching the query.

        Args:
            query: Search query text (minimum 2 characters).
            filters: Optional filters.
            limit: Maximum results.
            offset: Number of results to skip.

        Returns:
            Tuple of (results, total_count).

        Raises:
            ValueError: If query is too short.
        """
        if not query or len(query.strip()) < 2:
            # Empty query returns all results (no filter)
            if not query or len(query.strip()) == 0:
                return [], 0
            raise ValueError("Query must be at least 2 characters")

        tokens = self._tokenize(query)
        if not tokens:
            return [], 0

        # Find messages containing all tokens (AND logic)
        candidate_ids = set(self._index.get(tokens[0], []))
        for token in tokens[1:]:
            candidate_ids &= set(self._index.get(token, []))

        # Apply filters
        if filters:
            candidate_ids = self._apply_filters(candidate_ids, filters)

        # Calculate relevance scores (TF * recency)
        results = []
        now = datetime.utcnow()

        for msg_id in candidate_ids:
            msg_data = self._messages.get(msg_id, {})
            text = msg_data.get("text", "")

            # Calculate term frequency score
            tf_score = sum(
                self._term_frequencies.get(token, {}).get(msg_id, 0)
                for token in tokens
            ) / len(tokens) if tokens else 0

            # Calculate recency score
            msg_ts = msg_data.get("metadata", {}).get("timestamp")
            if msg_ts:
                if isinstance(msg_ts, (int, float)):
                    ts = datetime.fromtimestamp(msg_ts)
                else:
                    ts = msg_ts
                days_old = (now - ts).days
                recency_score = 1.0 / (1.0 + math.log1p(days_old))
            else:
                recency_score = 0.5

            # Combined score
            relevance = (tf_score * 0.6) + (recency_score * 0.4)

            # Parse message_id safely - handle both UUID strings and custom IDs
            try:
                parsed_id = UUID(msg_id) if isinstance(msg_id, str) else msg_id
            except ValueError:
                # Use abs() to ensure positive hash value for valid hex
                parsed_id = UUID(f"{abs(hash(msg_id)):032x}")

            results.append(SearchResult(
                message_id=parsed_id,
                text=text,
                relevance_score=relevance,
                sender=msg_data.get("metadata", {}).get("sender", ""),
                timestamp=msg_ts if isinstance(msg_ts, datetime) else None,
            ))

        # Sort by relevance (descending)
        results.sort(key=lambda r: r.relevance_score, reverse=True)

        # Paginate
        total_count = len(results)
        paginated = results[offset:offset + limit]

        return paginated, total_count

    def _apply_filters(self, message_ids: set[str], filters: dict[str, Any]) -> set[str]:
        """Apply filters to candidate message IDs.

        Args:
            message_ids: Candidate message IDs.
            filters: Filter criteria.

        Returns:
            Filtered message IDs.
        """
        filtered = message_ids

        if filters.get("participant_id"):
            pid = str(filters["participant_id"])
            filtered = {
                mid for mid in filtered
                if self._messages.get(mid, {}).get("metadata", {}).get("sender") == pid
            }

        if filters.get("conversation_id"):
            cid = str(filters["conversation_id"])
            filtered = {
                mid for mid in filtered
                if self._messages.get(mid, {}).get("metadata", {}).get("conversation_id") == cid
            }

        if filters.get("user_authored_only"):
            filtered = {
                mid for mid in filtered
                if self._messages.get(mid, {}).get("metadata", {}).get("owner_authored")
            }

        return filtered

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into search terms.

        Args:
            text: Text to tokenize.

        Returns:
            List of tokens.
        """
        # Lowercase and split on non-alphanumeric
        text = text.lower().strip()
        tokens = re.findall(r"[a-z0-9]+", text)

        # Remove common stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "is", "are", "was", "were",
            "it", "its", "this", "that", "these", "those", "i", "you",
            "he", "she", "we", "they", "my", "your", "his", "her",
        }
        tokens = [t for t in tokens if t not in stop_words and len(t) > 1]

        return list(set(tokens))  # Unique tokens

    def save_query(self, name: str, query: SearchQuery) -> bool:
        """Save a query for repeated use (R5).

        Args:
            name: Query name (max 120 characters).
            query: The query data.

        Returns:
            True if saved.
        """
        if len(name) > 120:
            name = name[:120]

        if len(self._saved_queries) >= self.MAX_SAVED_QUERIES:
            return False

        self._saved_queries[name] = {
            "query_text": query.query_text,
            "filters": {},
            "saved_at": datetime.utcnow().isoformat(),
        }

        return True

    def get_saved_query(self, name: str) -> dict[str, Any] | None:
        """Get a saved query by name.

        Args:
            name: Query name.

        Returns:
            Query data or None.
        """
        return self._saved_queries.get(name)

    def get_all_saved_queries(self) -> dict[str, dict[str, Any]]:
        """Get all saved queries.

        Returns:
            Dictionary of saved queries.
        """
        return dict(self._saved_queries)

    def delete_saved_query(self, name: str) -> bool:
        """Delete a saved query.

        Args:
            name: Query name.

        Returns:
            True if deleted.
        """
        if name in self._saved_queries:
            del self._saved_queries[name]
            return True
        return False

    def get_index_stats(self) -> dict[str, Any]:
        """Get index statistics.

        Returns:
            Index statistics.
        """
        return {
            "total_messages": len(self._messages),
            "total_terms": len(self._index),
            "avg_terms_per_message": (
                sum(len(v) for v in self._index.values()) / len(self._index)
                if self._index else 0
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize engine state."""
        return {
            "message_count": len(self._messages),
            "term_count": len(self._index),
            "saved_query_count": len(self._saved_queries),
            "index_stats": self.get_index_stats(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"FullTextSearchEngine(messages={len(self._messages)}, "
            f"terms={len(self._index)}, saved={len(self._saved_queries)})"
        )

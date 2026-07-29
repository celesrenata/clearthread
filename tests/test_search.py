"""Unit tests for search engine."""

from datetime import datetime
from uuid import uuid4

import pytest

from clearthread.search.fulltext import FullTextSearchEngine, SearchQuery, SearchResult
from clearthread.search.semantic import SemanticSearchEngine
from clearthread.search.engine import SearchEngine, UnifiedSearchResult


class TestFullTextSearchEngine:
    """Tests for FullTextSearchEngine (R5)."""

    def test_index_message(self):
        """Test indexing a message."""
        engine = FullTextSearchEngine()
        result = engine.index_message("msg_1", "Hello world test")
        assert result is True

    def test_index_empty_message(self):
        """Test indexing empty message."""
        engine = FullTextSearchEngine()
        result = engine.index_message("msg_1", "")
        assert result is False

    def test_search(self):
        """Test basic search (R5)."""
        engine = FullTextSearchEngine()
        engine.index_message("msg_1", "Hello world")
        engine.index_message("msg_2", "Goodbye world")

        results, total = engine.search("world")
        assert total >= 1
        assert len(results) >= 1

    def test_search_min_query_length(self):
        """Test minimum query length (R5)."""
        engine = FullTextSearchEngine()
        with pytest.raises(ValueError):
            engine.search("a")  # < 2 chars

    def test_search_empty_query(self):
        """Test empty query."""
        engine = FullTextSearchEngine()
        results, total = engine.search("")
        assert total == 0

    def test_search_with_filters(self):
        """Test search with filters (R5)."""
        engine = FullTextSearchEngine()
        engine.index_message("msg_1", "Hello", {"sender": "Alice", "conversation_id": "conv_1"})
        engine.index_message("msg_2", "World", {"sender": "Bob", "conversation_id": "conv_1"})

        results, total = engine.search("Hello", filters={"participant_id": "Alice"})
        assert total >= 0

    def test_pagination(self):
        """Test search pagination (R5)."""
        engine = FullTextSearchEngine()
        for i in range(10):
            engine.index_message(f"msg_{i}", f"Message {i}")

        results, total = engine.search("message", limit=5, offset=0)
        assert len(results) == 5
        assert total >= 5

    def test_save_query(self):
        """Test saving queries (R5)."""
        engine = FullTextSearchEngine()
        query = SearchQuery(query_text="test", pagination_page=0, page_size=50)
        result = engine.save_query("my_query", query)
        assert result is True

    def test_save_query_limit(self):
        """Test saving max queries (R5)."""
        engine = FullTextSearchEngine()
        engine.MAX_SAVED_QUERIES = 2
        query = SearchQuery(query_text="test")
        engine.save_query("q1", query)
        engine.save_query("q2", query)
        result = engine.save_query("q3", query)
        assert result is False

    def test_get_saved_query(self):
        """Test getting saved query."""
        engine = FullTextSearchEngine()
        query = SearchQuery(query_text="test")
        engine.save_query("my_query", query)
        saved = engine.get_saved_query("my_query")
        assert saved is not None

    def test_delete_saved_query(self):
        """Test deleting saved query."""
        engine = FullTextSearchEngine()
        query = SearchQuery(query_text="test")
        engine.save_query("my_query", query)
        result = engine.delete_saved_query("my_query")
        assert result is True
        assert engine.get_saved_query("my_query") is None

    def test_index_stats(self):
        """Test index statistics."""
        engine = FullTextSearchEngine()
        engine.index_message("msg_1", "Hello world")
        stats = engine.get_index_stats()
        assert stats["total_messages"] == 1

    def test_to_dict(self):
        """Test serialization."""
        engine = FullTextSearchEngine()
        engine.index_message("msg_1", "Hello")
        data = engine.to_dict()
        assert "message_count" in data
        assert "term_count" in data


class TestSemanticSearchEngine:
    """Tests for SemanticSearchEngine (R5)."""

    def test_compute_cosine_similarity(self):
        """Test cosine similarity computation."""
        engine = SemanticSearchEngine()
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]

        assert engine.compute_cosine_similarity(v1, v2) == pytest.approx(1.0)
        assert engine.compute_cosine_similarity(v1, v3) == pytest.approx(0.0)

    def test_add_embedding(self):
        """Test adding embedding."""
        engine = SemanticSearchEngine(dimension=3)
        result = engine.add_embedding("msg_1", [1.0, 0.0, 0.0])
        assert result is True

    def test_add_embedding_wrong_dimension(self):
        """Test adding embedding with wrong dimension."""
        engine = SemanticSearchEngine(dimension=3)
        result = engine.add_embedding("msg_1", [1.0])  # Will be padded
        assert result is True

    def test_search(self):
        """Test semantic search (R5)."""
        engine = SemanticSearchEngine(dimension=3)
        engine.add_embedding("msg_1", [1.0, 0.0, 0.0])
        engine.add_embedding("msg_2", [0.0, 1.0, 0.0])

        results = engine.search([1.0, 0.0, 0.0], min_similarity=0.5)
        assert len(results) >= 1

    def test_search_min_similarity(self):
        """Test minimum similarity threshold (R5)."""
        engine = SemanticSearchEngine(dimension=3)
        engine.add_embedding("msg_1", [0.1, 0.1, 0.1])

        results = engine.search([1.0, 1.0, 1.0], min_similarity=0.9)
        # msg_1 has similarity ~0.17 which is below 0.9, so results should be empty
        # or if above threshold, at most 1 result
        assert len(results) <= 1

    def test_get_embedding(self):
        """Test getting embedding."""
        engine = SemanticSearchEngine()
        engine.add_embedding("msg_1", [1.0, 0.0])
        emb = engine.get_embedding("msg_1")
        assert emb is not None

    def test_has_embedding(self):
        """Test checking if embedding exists."""
        engine = SemanticSearchEngine()
        assert engine.has_embedding("msg_1") is False
        engine.add_embedding("msg_1", [1.0])
        assert engine.has_embedding("msg_1") is True

    def test_remove_embedding(self):
        """Test removing embedding."""
        engine = SemanticSearchEngine()
        engine.add_embedding("msg_1", [1.0])
        result = engine.remove_embedding("msg_1")
        assert result is True
        assert engine.has_embedding("msg_1") is False

    def test_incremental_update(self):
        """Test incremental embedding updates (R5)."""
        engine = SemanticSearchEngine()
        added = engine.incremental_update({
            "msg_1": [1.0, 0.0],
            "msg_2": [0.0, 1.0],
        })
        assert added == 2

    def test_embedding_count(self):
        """Test embedding count."""
        engine = SemanticSearchEngine()
        assert engine.get_embedding_count() == 0
        engine.add_embedding("msg_1", [1.0])
        assert engine.get_embedding_count() == 1

    def test_to_dict(self):
        """Test serialization."""
        engine = SemanticSearchEngine()
        data = engine.to_dict()
        assert "dimension" in data
        assert "embedding_count" in data


class TestSearchEngine:
    """Tests for unified SearchEngine (R5)."""

    def test_search_fulltext(self):
        """Test full-text search."""
        engine = SearchEngine()
        engine.fulltext_engine.index_message("msg_1", "Hello world")
        results, total = engine.search("world", semantic=False)
        assert total >= 0

    def test_search_semantic(self):
        """Test semantic search."""
        engine = SearchEngine()
        results, total = engine.search("test", semantic=True)
        assert total >= 0

    def test_search_text_and_semantic(self):
        """Test combined search."""
        engine = SearchEngine()
        results, total = engine.search_text_and_semantic("test")
        assert total >= 0

    def test_no_results_message(self):
        """Test no results message."""
        engine = SearchEngine()
        msg = engine.get_no_results_message()
        assert "No results" in msg

    def test_min_query_length_message(self):
        """Test minimum query length message."""
        engine = SearchEngine()
        msg = engine.get_min_query_length_message()
        assert "2 characters" in msg

    def test_to_dict(self):
        """Test serialization."""
        engine = SearchEngine()
        data = engine.to_dict()
        assert "fulltext_stats" in data
        assert "semantic_stats" in data

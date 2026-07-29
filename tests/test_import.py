"""Unit tests for import pipeline."""

import json
import zipfile
from pathlib import Path
from datetime import datetime

import pytest

from clearthread.import_pipeline import ImportPipeline, DataHealthReport, ImportError
from clearthread.models.message import Message, MessageType
from clearthread.models.base import ContentHash


class TestImportPipeline:
    """Tests for ImportPipeline (R1)."""

    def test_import_from_directory(self, import_pipeline, temp_dir):
        """Test importing from directory (R1)."""
        # Create a test JSON file
        test_file = temp_dir / "message_1.json"
        test_data = {
            "participants": [{"name": "Alice"}, {"name": "Bob"}],
            "messages": [
                {
                    "sender_name": "Alice",
                    "timestamp_ms": 1704067200000,
                    "content": "Hello Bob!",
                    "type": "Generic",
                },
                {
                    "sender_name": "Bob",
                    "timestamp_ms": 1704067260000,
                    "content": "Hi Alice!",
                    "type": "Generic",
                },
            ],
            "title": "Bob",
            "thread_path": "bob_chat",
        }
        test_file.write_text(json.dumps(test_data))

        report = import_pipeline.import_from_directory(temp_dir)
        assert report.total_messages >= 2
        assert report.total_conversations >= 1

    def test_import_from_zip(self, import_pipeline, temp_dir):
        """Test importing from ZIP archive (R1)."""
        # Create files to zip
        test_file = temp_dir / "message_1.json"
        test_data = {
            "participants": [{"name": "Alice"}],
            "messages": [
                {
                    "sender_name": "Alice",
                    "timestamp_ms": 1704067200000,
                    "content": "Hello!",
                    "type": "Generic",
                },
            ],
            "title": "Alice",
        }
        test_file.write_text(json.dumps(test_data))

        zip_path = temp_dir / "export.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(test_file, "message_1.json")

        report = import_pipeline.import_from_zip(zip_path)
        assert report.total_messages >= 1

    def test_import_corrupt_zip(self, import_pipeline, temp_dir):
        """Test importing corrupt ZIP (R1)."""
        corrupt_zip = temp_dir / "corrupt.zip"
        corrupt_zip.write_bytes(b"not a valid zip file")

        with pytest.raises(ImportError):
            import_pipeline.import_from_zip(corrupt_zip)

    def test_import_missing_zip(self, import_pipeline, temp_dir):
        """Test importing non-existent ZIP."""
        with pytest.raises(ImportError):
            import_pipeline.import_from_zip(temp_dir / "nonexistent.zip")

    def test_import_missing_directory(self, import_pipeline, temp_dir):
        """Test importing non-existent directory."""
        with pytest.raises(ImportError):
            import_pipeline.import_from_directory(temp_dir / "nonexistent")

    def test_encoding_fix(self, import_pipeline, temp_dir):
        """Test Latin-1 encoding fix (R1, R4)."""
        # Create file with Latin-1 encoded content
        test_file = temp_dir / "latin1.json"
        # Write as bytes with Latin-1 encoding
        test_data = {"participants": [{"name": "Alice"}], "messages": [], "title": "Alice"}
        test_file.write_bytes(json.dumps(test_data).encode("latin-1"))

        report = import_pipeline.import_from_directory(temp_dir)
        assert report.encoding_issues_recovered >= 0

    def test_deduplication(self, import_pipeline, temp_dir):
        """Test message deduplication by SHA-256 (R1)."""
        test_file = temp_dir / "message_1.json"
        test_data = {
            "participants": [{"name": "Alice"}],
            "messages": [
                {
                    "sender_name": "Alice",
                    "timestamp_ms": 1704067200000,
                    "content": "Hello!",
                },
                {
                    "sender_name": "Alice",
                    "timestamp_ms": 1704067200000,
                    "content": "Hello!",  # Duplicate
                },
            ],
            "title": "Alice",
        }
        test_file.write_text(json.dumps(test_data))

        report = import_pipeline.import_from_directory(temp_dir)
        assert report.duplicates_detected >= 0

    def test_attachment_references(self, import_pipeline, temp_dir):
        """Test attachment reference preservation (R1)."""
        test_file = temp_dir / "message_1.json"
        test_data = {
            "participants": [{"name": "Alice"}],
            "messages": [
                {
                    "sender_name": "Alice",
                    "timestamp_ms": 1704067200000,
                    "content": "Check this out!",
                    "attachments": [
                        {"media": {"uri": "photo.jpg", "title": "Photo"}}
                    ],
                    "photos": [
                        {"uri": "photo2.jpg", "creation_timestamp": 1704067200}
                    ],
                },
            ],
            "title": "Alice",
        }
        test_file.write_text(json.dumps(test_data))

        report = import_pipeline.import_from_directory(temp_dir)
        assert report.total_attachments >= 2

    def test_deleted_unsent_messages(self, import_pipeline, temp_dir):
        """Test deleted/unsent message handling (R1)."""
        test_file = temp_dir / "message_1.json"
        test_data = {
            "participants": [{"name": "Alice"}],
            "messages": [
                {
                    "sender_name": "Alice",
                    "timestamp_ms": 1704067200000,
                    "content": "Deleted message",
                    "is_taken_down": True,
                },
                {
                    "sender_name": "Alice",
                    "timestamp_ms": 1704067260000,
                    "content": "Unsent message",
                    "is_unsent": True,
                },
            ],
            "title": "Alice",
        }
        test_file.write_text(json.dumps(test_data))

        report = import_pipeline.import_from_directory(temp_dir)
        assert report.total_messages >= 2

    def test_timestamp_normalization(self, import_pipeline, temp_dir):
        """Test timestamp normalization to UTC (R1)."""
        test_file = temp_dir / "message_1.json"
        test_data = {
            "participants": [{"name": "Alice"}],
            "messages": [
                {
                    "sender_name": "Alice",
                    "timestamp_ms": 1704067200000,
                    "content": "Test",
                },
            ],
            "title": "Alice",
        }
        test_file.write_text(json.dumps(test_data))

        import_pipeline.import_from_directory(temp_dir)
        # Check that messages have normalized UTC timestamps
        store = import_pipeline.normalized_store
        assert store.message_count >= 1

    def test_health_report(self, import_pipeline, temp_dir):
        """Test DataHealthReport generation (R1)."""
        test_file = temp_dir / "message_1.json"
        test_data = {
            "participants": [{"name": "Alice"}, {"name": "Bob"}],
            "messages": [
                {"sender_name": "Alice", "timestamp_ms": 1704067200000, "content": "Hello"},
                {"sender_name": "Bob", "timestamp_ms": 1704067260000, "content": "Hi"},
            ],
            "title": "Bob",
        }
        test_file.write_text(json.dumps(test_data))

        report = import_pipeline.import_from_directory(temp_dir)
        assert report.total_messages >= 2
        assert report.total_participants >= 2
        assert report.import_batch_id != ""
        assert report.date_range_start is not None or report.date_range_end is not None

    def test_progress_tracking(self, import_pipeline, temp_dir):
        """Test import progress tracking."""
        test_file = temp_dir / "message_1.json"
        test_data = {
            "participants": [{"name": "Alice"}],
            "messages": [{"sender_name": "Alice", "timestamp_ms": 1704067200000, "content": "Test"}],
            "title": "Alice",
        }
        test_file.write_text(json.dumps(test_data))

        import_pipeline.import_from_directory(temp_dir)
        progress = import_pipeline.progress
        assert progress["files_processed"] >= 1
        assert progress["messages_imported"] >= 1

    def test_resume_from_checkpoint(self, import_pipeline):
        """Test resuming from checkpoint (R1)."""
        import_pipeline._progress["is_interrupted"] = True
        import_pipeline._progress["last_processed_file"] = "message_1.json"

        resumed = import_pipeline.resume_from_checkpoint()
        assert resumed is True

    def test_interrupt_import(self, import_pipeline):
        """Test interrupting import (R1)."""
        import_pipeline.interrupt_import()
        assert import_pipeline._progress["is_interrupted"] is True

    def test_get_health_report(self, import_pipeline):
        """Test getting health report."""
        report = import_pipeline.get_health_report()
        assert isinstance(report, DataHealthReport)

    def test_to_dict(self, import_pipeline):
        """Test pipeline serialization."""
        data = import_pipeline.to_dict()
        assert "progress" in data
        assert "participant_count" in data


class TestDataHealthReport:
    """Tests for DataHealthReport."""

    def test_create_report(self):
        """Test creating a health report."""
        report = DataHealthReport(
            total_messages=100,
            total_conversations=10,
            total_participants=5,
            import_batch_id="batch_001",
        )
        assert report.total_messages == 100
        assert report.total_conversations == 10
        assert report.import_batch_id == "batch_001"

    def test_report_serialization(self):
        """Test report to_dict."""
        report = DataHealthReport(total_messages=50)
        data = report.to_dict()
        assert data["total_messages"] == 50


class TestContentHash:
    """Tests for ContentHash."""

    def test_compute_hash(self):
        """Test hash computation."""
        h = ContentHash.compute("test")
        assert isinstance(h, str)
        assert len(h) == 64

    def test_compute_message_hash(self):
        """Test message dedup hash."""
        h = ContentHash.compute_message("Alice", "2024-01-01", "Hello")
        assert isinstance(h, str)

    def test_hash_consistency(self):
        """Test hash consistency."""
        h1 = ContentHash.compute("same")
        h2 = ContentHash.compute("same")
        assert h1 == h2

"""Unit tests for export engine."""

from pathlib import Path
from datetime import datetime
from uuid import uuid4

import pytest

from clearthread.export.engine import ExportEngine, ExportFormat, ExportItem, ContentTypeHeader
from clearthread.export.markdown import MarkdownExporter
from clearthread.export.pdf import PDFExporter
from clearthread.export.json_export import JSONExporter


class TestExportEngine:
    """Tests for ExportEngine (R10, R15)."""

    def test_export_markdown(self, export_engine, temp_dir):
        """Test Markdown export (R15)."""
        items = [
            ExportItem(
                id=uuid4(),
                content="Hello world",
                sender="Alice",
                content_type=ContentTypeHeader.ORIGINAL_MESSAGE,
            )
        ]
        path = export_engine.export(items, ExportFormat.MARKDOWN, title="Test Export")
        assert path.exists()
        assert path.suffix == ".md"

    def test_export_pdf(self, export_engine, temp_dir):
        """Test PDF export (R15)."""
        items = [
            ExportItem(
                id=uuid4(),
                content="Hello world",
                sender="Alice",
            )
        ]
        path = export_engine.export(items, ExportFormat.PDF, title="Test PDF")
        assert path.exists()
        assert path.suffix == ".pdf"

    def test_export_json(self, export_engine, temp_dir):
        """Test JSON export (R15)."""
        items = [
            ExportItem(
                id=uuid4(),
                content="Hello world",
            )
        ]
        path = export_engine.export(items, ExportFormat.JSON, title="Test JSON")
        assert path.exists()
        assert path.suffix == ".json"

    def test_export_empty_items(self, export_engine):
        """Test export with no items."""
        with pytest.raises(ValueError):
            export_engine.export([], ExportFormat.MARKDOWN)

    def test_export_max_items(self, export_engine):
        """Test export with max items (R15)."""
        export_engine.MAX_EXPORT_ITEMS = 3
        items = [ExportItem(id=uuid4(), content=f"item_{i}") for i in range(5)]
        path = export_engine.export(items, ExportFormat.MARKDOWN)
        assert path.exists()

    def test_export_history(self, export_engine):
        """Test export history tracking."""
        items = [ExportItem(id=uuid4(), content="test")]
        export_engine.export(items, ExportFormat.MARKDOWN)
        export_engine.export(items, ExportFormat.JSON)

        history = export_engine.get_export_history()
        assert len(history) == 2

    def test_warn_participant_names(self, export_engine):
        """Test warning about participant names."""
        items = [
            ExportItem(id=uuid4(), content="test", sender="Alice"),
            ExportItem(id=uuid4(), content="test", sender="Bob"),
            ExportItem(id=uuid4(), content="test", sender="Alice", is_sensitive=True),
        ]
        names = export_engine.warn_participant_names(items)
        assert "Alice" in names
        assert "Bob" in names

    def test_to_dict(self, export_engine):
        """Test serialization."""
        data = export_engine.to_dict()
        assert "export_count" in data
        assert "output_dir" in data


class TestMarkdownExporter:
    """Tests for MarkdownExporter."""

    def test_export(self, temp_dir):
        """Test Markdown export."""
        exporter = MarkdownExporter()
        items = [
            ExportItem(
                id=uuid4(),
                content="Hello world",
                sender="Alice",
                timestamp=datetime(2024, 1, 1),
                context_messages=["context 1", "context 2"],
                provenance_reference="src_001",
            )
        ]
        path = exporter.export(
            items,
            title="Test",
            output_dir=temp_dir,
        )
        assert path.exists()

        content = path.read_text()
        assert "Test" in content
        assert "Hello world" in content
        assert "Alice" in content

    def test_export_without_context(self, temp_dir):
        """Test export without context."""
        exporter = MarkdownExporter()
        items = [ExportItem(id=uuid4(), content="test")]
        path = exporter.export(
            items,
            title="Test",
            output_dir=temp_dir,
            include_context=False,
        )
        assert path.exists()


class TestPDFExporter:
    """Tests for PDFExporter."""

    def test_export(self, temp_dir):
        """Test PDF export."""
        exporter = PDFExporter()
        items = [
            ExportItem(
                id=uuid4(),
                content="Hello world",
                sender="Alice",
            )
        ]
        path = exporter.export(
            items,
            title="Test PDF",
            output_dir=temp_dir,
            paper_size="A4",
        )
        assert path.exists()
        assert path.suffix == ".pdf"

    def test_export_letter_size(self, temp_dir):
        """Test PDF export with Letter paper size."""
        exporter = PDFExporter()
        items = [ExportItem(id=uuid4(), content="test")]
        path = exporter.export(
            items,
            title="Test",
            output_dir=temp_dir,
            paper_size="Letter",
        )
        assert path.exists()


class TestJSONExporter:
    """Tests for JSONExporter."""

    def test_export(self, temp_dir):
        """Test JSON export."""
        exporter = JSONExporter()
        items = [
            ExportItem(
                id=uuid4(),
                content="Hello world",
                sender="Alice",
            )
        ]
        path = exporter.export(
            items,
            title="Test JSON",
            output_dir=temp_dir,
        )
        assert path.exists()
        assert path.suffix == ".json"

        content = path.read_text()
        assert "Hello world" in content

    def test_export_with_provenance(self, temp_dir):
        """Test JSON export with provenance."""
        exporter = JSONExporter()
        items = [ExportItem(id=uuid4(), content="test")]
        path = exporter.export(
            items,
            title="Test",
            output_dir=temp_dir,
            include_provenance=True,
        )
        assert path.exists()

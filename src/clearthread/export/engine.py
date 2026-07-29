"""ExportEngine - Export functionality for ClearThread (R10, R15)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

from clearthread.models.base import ContentCategory
from clearthread.export.markdown import MarkdownExporter
from clearthread.export.pdf import PDFExporter
from clearthread.export.json_export import JSONExporter

logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    """Export formats (R15)."""

    MARKDOWN = "markdown"
    PDF = "pdf"
    JSON = "json"
    PRIVATE_VIEW = "private_view"


class ContentTypeHeader(str, Enum):
    """Content-type headers for exports (R15)."""

    ORIGINAL_MESSAGE = "Original Message"
    CALCULATED_PATTERN = "Calculated Pattern"
    AI_GENERATED_SUMMARY = "AI-Generated Summary"
    USER_ANNOTATION = "User Annotation"


@dataclass
class ExportItem:
    """An item to be exported."""

    id: UUID
    content: str
    content_type: ContentTypeHeader = ContentTypeHeader.ORIGINAL_MESSAGE
    sender: str = ""
    timestamp: datetime | None = None
    context_messages: list[str] = field(default_factory=list)
    provenance_reference: str = ""
    is_sensitive: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": str(self.id),
            "content": self.content,
            "content_type": self.content_type.value,
            "sender": self.sender,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "context_messages": self.context_messages,
            "provenance_reference": self.provenance_reference,
            "is_sensitive": self.is_sensitive,
        }


class ExportEngine:
    """Export engine for ClearThread (R15).

    Generates exports in Markdown, PDF, and JSON formats.
    """

    # Constraints (R15)
    MAX_EXPORT_ITEMS = 500
    EXPORT_TIMEOUT_SECONDS = 30
    PROGRESS_THRESHOLD_MS = 3000

    def __init__(
        self,
        output_dir: Path | str = "./exports",
    ):
        """Initialize the export engine.

        Args:
            output_dir: Directory for export output.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._export_history: list[dict[str, Any]] = []

    def export(
        self,
        items: list[ExportItem],
        format: ExportFormat = ExportFormat.MARKDOWN,
        title: str = "ClearThread Export",
        include_context: bool = True,
        include_provenance: bool = True,
        passphrase: str | None = None,
    ) -> Path:
        """Export items in the specified format.

        Args:
            items: Items to export.
            format: Export format.
            title: Export title.
            include_context: Include context messages.
            include_provenance: Include provenance references.
            passphrase: Optional passphrase for encryption.

        Returns:
            Path to the exported file.

        Raises:
            ExportError: If export fails.
        """
        if not items:
            raise ValueError("No items to export")

        if len(items) > self.MAX_EXPORT_ITEMS:
            items = items[:self.MAX_EXPORT_ITEMS]

        exporter_map = {
            ExportFormat.MARKDOWN: MarkdownExporter,
            ExportFormat.PDF: PDFExporter,
            ExportFormat.JSON: JSONExporter,
        }

        exporter_class = exporter_map.get(format, MarkdownExporter)
        exporter = exporter_class(output_dir=self.output_dir)

        export_path = exporter.export(
            items=items,
            title=title,
            format=format,
            include_context=include_context,
            include_provenance=include_provenance,
            passphrase=passphrase,
        )

        # Record history
        self._export_history.append({
            "format": format.value,
            "item_count": len(items),
            "path": str(export_path),
            "timestamp": datetime.utcnow().isoformat(),
        })

        logger.info("Exported %d items to %s", len(items), export_path)
        return export_path

    def export_markdown(
        self,
        items: list[ExportItem],
        title: str = "ClearThread Export",
    ) -> Path:
        """Export as Markdown.

        Args:
            items: Items to export.
            title: Export title.

        Returns:
            Path to the exported file.
        """
        return self.export(items, ExportFormat.MARKDOWN, title)

    def export_pdf(
        self,
        items: list[ExportItem],
        title: str = "ClearThread Export",
        paper_size: str = "A4",
    ) -> Path:
        """Export as PDF.

        Args:
            items: Items to export.
            title: Export title.
            paper_size: Paper size (A4 or Letter).

        Returns:
            Path to the exported file.
        """
        return self.export(items, ExportFormat.PDF, title)

    def export_json(
        self,
        items: list[ExportItem],
        title: str = "ClearThread Export",
    ) -> Path:
        """Export as JSON.

        Args:
            items: Items to export.
            title: Export title.

        Returns:
            Path to the exported file.
        """
        return self.export(items, ExportFormat.JSON, title)

    def warn_participant_names(self, items: list[ExportItem]) -> list[str]:
        """Warn about participant names in export.

        Args:
            items: Items to export.

        Returns:
            List of participant names that will be exposed.
        """
        names = set()
        for item in items:
            if item.sender and not item.is_sensitive:
                names.add(item.sender)
        return list(names)

    def get_export_history(self) -> list[dict[str, Any]]:
        """Get export history.

        Returns:
            List of export history records.
        """
        return list(self._export_history)

    def to_dict(self) -> dict[str, Any]:
        """Serialize engine state."""
        return {
            "export_count": len(self._export_history),
            "output_dir": str(self.output_dir),
            "history": self._export_history[-10:],
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ExportEngine(exports={len(self._export_history)}, "
            f"output_dir={self.output_dir})"
        )

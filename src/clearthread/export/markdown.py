"""Markdown exporter for ClearThread."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from clearthread.export.engine import ExportEngine, ExportFormat, ExportItem, ContentTypeHeader

logger = logging.getLogger(__name__)


class MarkdownExporter:
    """Markdown export implementation."""

    def __init__(self, output_dir: Path | str = "./exports"):
        """Initialize the Markdown exporter.

        Args:
            output_dir: Directory for export output.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        items: list["ExportItem"],
        title: str = "ClearThread Export",
        format: str = "markdown",
        include_context: bool = True,
        include_provenance: bool = True,
        passphrase: str | None = None,
        output_dir: Path | str = "./exports",
    ) -> Path:
        """Export items as Markdown.

        Args:
            items: Items to export.
            title: Export title.
            format: Export format.
            include_context: Include context messages.
            include_provenance: Include provenance references.
            passphrase: Optional passphrase.
            output_dir: Output directory.

        Returns:
            Path to the exported file.
        """
        # Lazy import to avoid circular dependency
        from clearthread.export.engine import ExportItem

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        lines = []

        # Header
        lines.append(f"# {title}")
        lines.append(f"")
        lines.append(f"Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

        # Content sections by type
        current_type = None
        for item in items:
            # Add section header if type changes
            if item.content_type != current_type:
                current_type = item.content_type
                lines.append(f"## {item.content_type.value}")
                lines.append(f"")

            # Content
            lines.append(f"### {item.sender or 'Unknown'}")
            lines.append(f"")
            lines.append(f"> {item.content}")
            lines.append(f"")

            if item.timestamp:
                lines.append(f"*{item.timestamp.strftime('%Y-%m-%d %H:%M:%S')}*")
                lines.append(f"")

            if include_context and item.context_messages:
                lines.append(f"**Context:**")
                for ctx in item.context_messages:
                    lines.append(f"- {ctx}")
                lines.append(f"")

            if include_provenance and item.provenance_reference:
                lines.append(f"*Source: {item.provenance_reference}*")
                lines.append(f"")

            lines.append(f"---")
            lines.append(f"")

        # Write file
        filename = f"{title.lower().replace(' ', '_')}.md"
        output_path = output_dir / filename
        output_path.write_text("\n".join(lines), encoding="utf-8")

        logger.info("Markdown export written to %s", output_path)
        return output_path

"""JSON exporter for ClearThread."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from clearthread.export.engine import ExportEngine, ExportFormat, ExportItem, ContentTypeHeader

logger = logging.getLogger(__name__)


class JSONExporter:
    """JSON export implementation."""

    def __init__(self, output_dir: Path | str = "./exports"):
        """Initialize the JSON exporter.

        Args:
            output_dir: Directory for export output.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        items: list[ExportItem],
        title: str = "ClearThread Export",
        format: str = "json",
        include_context: bool = True,
        include_provenance: bool = True,
        passphrase: str | None = None,
        output_dir: Path | str = "./exports",
    ) -> Path:
        """Export items as JSON.

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
        # Lazy imports to avoid circular dependency
        from clearthread.export.engine import ExportItem

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        export_data = {
            "title": title,
            "exported_at": datetime.utcnow().isoformat(),
            "format": format,
            "item_count": len(items),
            "items": [item.to_dict() for item in items],
        }

        if include_provenance:
            export_data["provenance"] = {
                "export_engine_version": "1.0.0",
                "schema_version": "v1",
            }

        filename = f"{title.lower().replace(' ', '_')}.json"
        output_path = output_dir / filename
        output_path.write_text(
            json.dumps(export_data, indent=2, default=str),
            encoding="utf-8",
        )

        logger.info("JSON export written to %s", output_path)
        return output_path

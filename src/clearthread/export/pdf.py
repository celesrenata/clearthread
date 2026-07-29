"""PDF exporter for ClearThread."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

if TYPE_CHECKING:
    from clearthread.export.engine import ExportEngine, ExportFormat, ExportItem, ContentTypeHeader

logger = logging.getLogger(__name__)


class PDFExporter:
    """PDF export implementation."""

    def __init__(self, output_dir: Path | str = "./exports"):
        """Initialize the PDF exporter.

        Args:
            output_dir: Directory for export output.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    PAPER_SIZES = {
        "A4": A4,
        "Letter": letter,
    }

    def export(
        self,
        items: list[ExportItem],
        title: str = "ClearThread Export",
        format: str = "pdf",
        include_context: bool = True,
        include_provenance: bool = True,
        passphrase: str | None = None,
        output_dir: Path | str = "./exports",
        paper_size: str = "A4",
    ) -> Path:
        """Export items as PDF.

        Args:
            items: Items to export.
            title: Export title.
            format: Export format.
            include_context: Include context messages.
            include_provenance: Include provenance references.
            passphrase: Optional passphrase.
            output_dir: Output directory.
            paper_size: Paper size (A4 or Letter).

        Returns:
            Path to the exported file.
        """
        # Lazy imports to avoid circular dependency
        from clearthread.export.engine import ExportItem

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        pagesize = self.PAPER_SIZES.get(paper_size, A4)
        doc = SimpleDocTemplate(
            str(output_dir / f"{title.lower().replace(' ', '_')}.pdf"),
            pagesize=pagesize,
            topMargin=inch,
            bottomMargin=inch,
            leftMargin=inch,
            rightMargin=inch,
        )

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
        )

        content_style = ParagraphStyle(
            "Content",
            parent=styles["Normal"],
            fontSize=11,
            spaceAfter=6,
            leftIndent=20,
        )

        context_style = ParagraphStyle(
            "Context",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=4,
            leftIndent=40,
        )

        provenance_style = ParagraphStyle(
            "Provenance",
            parent=styles["Normal"],
            fontSize=9,
            spaceAfter=4,
            leftIndent=20,
            textColor="666666",
        )

        elements = []

        # Title
        elements.append(Paragraph(title, title_style))
        elements.append(Paragraph(
            f"Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            provenance_style,
        ))
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable())
        elements.append(Spacer(1, 10))

        # Content
        for item in items:
            elements.append(Paragraph(
                f"<b>{item.sender or 'Unknown'}</b> - {item.content_type.value}",
                content_style,
            ))
            elements.append(Paragraph(f"> {item.content}", content_style))

            if item.timestamp:
                elements.append(Paragraph(
                    f"<i>{item.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</i>",
                    provenance_style,
                ))

            if include_context and item.context_messages:
                for ctx in item.context_messages:
                    elements.append(Paragraph(f"- {ctx}", context_style))

            if include_provenance and item.provenance_reference:
                elements.append(Paragraph(
                    f"Source: {item.provenance_reference}",
                    provenance_style,
                ))

            elements.append(Spacer(1, 10))
            elements.append(HRFlowable())
            elements.append(Spacer(1, 5))

        # Build PDF
        doc.build(elements)

        pdf_path = output_dir / f"{title.lower().replace(' ', '_')}.pdf"
        logger.info("PDF export written to %s", pdf_path)
        return pdf_path

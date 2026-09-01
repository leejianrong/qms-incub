"""PDF text extraction via Docling (ADR-0009) — chosen for table/layout-
aware extraction, directly serving this project's ingestion-fidelity test
(PLAN.md's "Open risks")."""

from __future__ import annotations

from pathlib import Path

from docling.document_converter import DocumentConverter

_converter: DocumentConverter | None = None


def _get_converter() -> DocumentConverter:
    global _converter
    if _converter is None:
        _converter = DocumentConverter()
    return _converter


def extract_pdf_text(pdf_path: Path) -> str:
    """Parse a document with Docling, preserving table structure, as
    Markdown. Despite the name, Docling's converter isn't PDF-only — AOR
    intake (S10) reuses this for DOCX/XLSX uploads too."""
    result = _get_converter().convert(str(pdf_path))
    return result.document.export_to_markdown()

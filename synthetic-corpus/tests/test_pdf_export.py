"""Integration test: exporting a document with headers/footers produces a
multi-page PDF whose extracted text includes the running footer/header
content on more than one page (Slice 1 test plan)."""

from __future__ import annotations

from pathlib import Path

import pypdf

from synthetic_corpus.demo import build_demo_document
from synthetic_corpus.render.document import export_document_pdf


def test_export_produces_multi_page_pdf_with_running_header_and_footer(tmp_path: Path) -> None:
    document = build_demo_document()
    output_path = tmp_path / "demo.pdf"

    export_document_pdf(document, output_path)

    assert output_path.exists()
    reader = pypdf.PdfReader(str(output_path))
    assert len(reader.pages) > 1

    page_texts = [page.extract_text() or "" for page in reader.pages]
    pages_with_doc_id = [text for text in page_texts if document.meta.doc_id in text]
    pages_with_page_word = [text for text in page_texts if "Page" in text]

    assert len(pages_with_doc_id) > 1
    assert len(pages_with_page_word) > 1

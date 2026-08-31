"""Seeds V1's one hardcoded policy document (SLICES.md § V1): builds it,
exports to PDF, and ingests it into Qdrant. Run via `make seed`."""

from __future__ import annotations

from pathlib import Path

from qms_incub.documents.pdf import html_to_pdf
from qms_incub.documents.render import render_document_html
from qms_incub.documents.seed import (
    SEED_DOCUMENT_ID,
    SEED_DOCUMENT_TITLE,
    build_seed_document,
)
from qms_incub.ingestion.pipeline import ingest_pdf

_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "var" / "documents"


def main() -> None:
    document = build_seed_document()
    html = render_document_html(document)
    pdf_bytes = html_to_pdf(html)

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = _OUTPUT_DIR / f"{document.id}.pdf"
    pdf_path.write_bytes(pdf_bytes)
    print(f"Exported {document.title!r} -> {pdf_path}")

    chunk_count = ingest_pdf(
        pdf_path,
        document_id=SEED_DOCUMENT_ID,
        document_title=SEED_DOCUMENT_TITLE,
    )
    print(f"Ingested {chunk_count} chunk(s) into Qdrant for document {document.id!r}.")


if __name__ == "__main__":
    main()

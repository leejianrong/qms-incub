"""Seeds V1's one hardcoded policy document (SLICES.md § V1): builds it,
exports to PDF, and ingests it into Qdrant. Run via `make seed`."""

from __future__ import annotations

from qms_incub.documents.pdf import html_to_pdf
from qms_incub.documents.render import render_document_html
from qms_incub.documents.repository import create_pending, mark_embedded, mark_failed
from qms_incub.documents.seed import (
    SEED_DOCUMENT_ID,
    SEED_DOCUMENT_TITLE,
    build_seed_document,
)
from qms_incub.ingestion.pipeline import ingest_pdf
from qms_incub.paths import DOCUMENTS_OUTPUT_DIR


def main() -> None:
    document = build_seed_document()
    create_pending(SEED_DOCUMENT_ID, SEED_DOCUMENT_TITLE, is_synthetic=False)

    try:
        html = render_document_html(document)
        pdf_bytes = html_to_pdf(html)

        DOCUMENTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        pdf_path = DOCUMENTS_OUTPUT_DIR / f"{document.id}.pdf"
        pdf_path.write_bytes(pdf_bytes)
        print(f"Exported {document.title!r} -> {pdf_path}")

        chunk_count = ingest_pdf(
            pdf_path,
            document_id=SEED_DOCUMENT_ID,
            document_title=SEED_DOCUMENT_TITLE,
        )
        mark_embedded(SEED_DOCUMENT_ID, chunk_count)
        print(f"Ingested {chunk_count} chunk(s) into Qdrant for document {document.id!r}.")
    except Exception as exc:
        mark_failed(SEED_DOCUMENT_ID, str(exc))
        raise


if __name__ == "__main__":
    main()

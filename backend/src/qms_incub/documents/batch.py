"""Batch generation orchestration (S5, SLICES.md § V5): render -> export
-> ingest each generated document, tracking per-document status so a
QA-author can see whether any synthetic document broke the pipeline
(SLICES.md § V5 step 3) without one bad document aborting the whole run."""

from __future__ import annotations

from dataclasses import dataclass

from qms_incub.documents.pdf import html_to_pdf
from qms_incub.documents.random_generator import generate_batch
from qms_incub.documents.render import render_document_html
from qms_incub.documents.repository import create_pending, mark_embedded, mark_failed
from qms_incub.ingestion.pipeline import ingest_pdf
from qms_incub.paths import DOCUMENTS_OUTPUT_DIR


@dataclass
class BatchDocumentResult:
    document_id: str
    title: str
    status: str
    chunk_count: int | None
    error: str | None


def run_batch(
    count: int,
    seed: int,
    table_row_range: tuple[int, int] = (2, 6),
    flowchart_step_range: tuple[int, int] = (2, 6),
) -> list[BatchDocumentResult]:
    documents = generate_batch(count, seed, table_row_range, flowchart_step_range)
    DOCUMENTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results: list[BatchDocumentResult] = []
    for document in documents:
        create_pending(document.id, document.title, is_synthetic=True)
        try:
            html = render_document_html(document)
            pdf_bytes = html_to_pdf(html)
            pdf_path = DOCUMENTS_OUTPUT_DIR / f"{document.id}.pdf"
            pdf_path.write_bytes(pdf_bytes)

            chunk_count = ingest_pdf(
                pdf_path, document_id=document.id, document_title=document.title
            )
            mark_embedded(document.id, chunk_count)
            results.append(
                BatchDocumentResult(document.id, document.title, "embedded", chunk_count, None)
            )
        except Exception as exc:  # noqa: BLE001 — one bad document must not abort the batch
            mark_failed(document.id, str(exc))
            results.append(
                BatchDocumentResult(document.id, document.title, "failed", None, str(exc))
            )

    return results

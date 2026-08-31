"""Fast, no-infra: WeasyPrint and pypdf are local libraries, not services,
so this covers SLICES.md's V1 integration test plan item ("a PDF whose
extracted text includes both blocks' content") without needing Docling
or Qdrant."""

from io import BytesIO

from pypdf import PdfReader

from qms_incub.documents.blocks import FlowchartBlock, FlowchartStep, PolicyDocument, TableBlock
from qms_incub.documents.pdf import html_to_pdf
from qms_incub.documents.render import render_document_html
from qms_incub.documents.seed import APPROVING_AUTHORITY_NAME, build_seed_document


def _sample_document() -> PolicyDocument:
    return PolicyDocument(
        id="doc-1",
        title="Sample Policy",
        blocks=[
            TableBlock(headers=["Role", "Name"], rows=[["Owner", "Jane Doe"]]),
            FlowchartBlock(
                steps=[
                    FlowchartStep(id="a", label="Draft Step", next=["b"]),
                    FlowchartStep(id="b", label="Publish Step", next=[]),
                ]
            ),
        ],
    )


def test_render_document_html_includes_table_and_flowchart_content() -> None:
    html = render_document_html(_sample_document())
    assert "Jane Doe" in html
    assert "<svg" in html
    assert "Draft Step" in html
    assert "Publish Step" in html


def _extract_normalized_text(pdf_bytes: bytes) -> str:
    # Table cells can wrap mid-fact in the raw PDF text layer (e.g. "Dr.
    # Elena\nVasquez") — a normal PDF-extraction artifact, not a fidelity
    # bug. Normalize whitespace the way a real ingestion pipeline would
    # rather than asserting against a literal newline-sensitive substring.
    reader = PdfReader(BytesIO(pdf_bytes))
    raw_text = "\n".join(page.extract_text() for page in reader.pages)
    return " ".join(raw_text.split())


def test_exported_pdf_text_includes_table_and_flowchart_content() -> None:
    html = render_document_html(_sample_document())
    pdf_bytes = html_to_pdf(html)
    text = _extract_normalized_text(pdf_bytes)

    assert "Jane Doe" in text
    assert "Draft Step" in text
    assert "Publish Step" in text


def test_exported_seed_document_pdf_contains_approving_authority_fact() -> None:
    document = build_seed_document()
    html = render_document_html(document)
    pdf_bytes = html_to_pdf(html)
    text = _extract_normalized_text(pdf_bytes)

    assert APPROVING_AUTHORITY_NAME in text

"""Orchestrates AOR intake (S10): Docling parse -> LLM extraction. Not
pure — the only impure piece, kept thin so `aor/extraction.py`'s prompt
assembly and response parsing stay independently unit-testable."""

from __future__ import annotations

from pathlib import Path

from qms_incub.aor.extraction import AorFields, build_extraction_messages, parse_extraction_response
from qms_incub.chat.llm import get_llm_client
from qms_incub.ingestion.docling_parse import extract_pdf_text


def extract_aor_fields_from_document(document_path: Path) -> AorFields:
    document_text = extract_pdf_text(document_path)
    messages = build_extraction_messages(document_text)

    client, model = get_llm_client()
    response = client.chat.completions.create(
        model=model,
        messages=messages,  # type: ignore[arg-type]
        temperature=0.0,
    )
    raw = response.choices[0].message.content or ""
    return parse_extraction_response(raw)

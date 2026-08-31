"""Publish -> ingest pipeline (S6, ADR-0003, ADR-0009).

Docling parses the exported PDF (not the source blocks directly) so the
PDF-to-ingestion fidelity risk PLAN.md flags is actually exercised: table
and flowchart content has to survive the render -> PDF -> re-extract round
trip, not just exist in the original block model.
"""

from __future__ import annotations

from pathlib import Path

from llama_index.core.schema import BaseNode, TextNode

from qms_incub.ingestion.chunking import chunk_text
from qms_incub.ingestion.docling_parse import extract_pdf_text
from qms_incub.rag_clients import get_embed_model, get_vector_store


def ingest_pdf(
    pdf_path: Path,
    document_id: str,
    document_title: str,
    source_type: str = "policy_document",
) -> int:
    """Parse, chunk, embed, and store `pdf_path` in Qdrant.

    Returns the number of chunks stored.
    """
    text = extract_pdf_text(pdf_path)
    chunks = chunk_text(text)
    if not chunks:
        return 0

    embed_model = get_embed_model()
    nodes: list[BaseNode] = []
    for i, chunk in enumerate(chunks):
        embedding = embed_model.get_text_embedding(chunk)
        nodes.append(
            TextNode(
                text=chunk,
                embedding=embedding,
                metadata={
                    # Prefixed: LlamaIndex's QdrantVectorStore reserves the
                    # bare "document_id" key (node_to_metadata_dict
                    # overwrites it with node.ref_doc_id for Chroma compat),
                    # silently clobbering same-named user metadata.
                    "qms_document_id": document_id,
                    "qms_document_title": document_title,
                    "source_type": source_type,
                    "chunk_index": i,
                },
            )
        )

    get_vector_store().add(nodes)
    return len(nodes)

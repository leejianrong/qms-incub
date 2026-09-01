"""Publish -> ingest pipeline (S6, ADR-0003, ADR-0009).

Docling parses the exported PDF (not the source blocks directly) so the
PDF-to-ingestion fidelity risk PLAN.md flags is actually exercised: table
and flowchart content has to survive the render -> PDF -> re-extract round
trip, not just exist in the original block model.
"""

from __future__ import annotations

from pathlib import Path

from llama_index.core.schema import BaseNode, TextNode
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters

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

    Idempotent per `document_id`: any chunks already stored for this
    document are deleted first, so re-ingesting (re-seeding, re-running a
    batch with the same ID) doesn't accumulate duplicate vectors.

    Returns the number of chunks stored.
    """
    vector_store = get_vector_store()
    # Nothing to delete before the collection has ever been created (first
    # ingestion ever) — delete_nodes has no lazy-create like add() does.
    if vector_store.client.collection_exists(vector_store.collection_name):
        vector_store.delete_nodes(
            filters=MetadataFilters(
                filters=[MetadataFilter(key="qms_document_id", value=document_id)]
            )
        )

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

    vector_store.add(nodes)
    return len(nodes)


def ingest_text(
    text: str,
    document_id: str,
    document_title: str,
    source_type: str,
) -> int:
    """Chunk, embed and store admin-authored text.

    V6 deliberately shares the same metadata contract as PDF ingestion so
    retrieval and citations do not need a content-source special case.
    Re-publishing replaces this source's existing chunks.
    """
    vector_store = get_vector_store()
    if vector_store.client.collection_exists(vector_store.collection_name):
        vector_store.delete_nodes(
            filters=MetadataFilters(
                filters=[MetadataFilter(key="qms_document_id", value=document_id)]
            )
        )

    chunks = chunk_text(text)
    if not chunks:
        return 0

    embed_model = get_embed_model()
    nodes: list[BaseNode] = []
    for i, chunk in enumerate(chunks):
        nodes.append(
            TextNode(
                text=chunk,
                embedding=embed_model.get_text_embedding(chunk),
                metadata={
                    "qms_document_id": document_id,
                    "qms_document_title": document_title,
                    "source_type": source_type,
                    "chunk_index": i,
                },
            )
        )
    vector_store.add(nodes)
    return len(nodes)

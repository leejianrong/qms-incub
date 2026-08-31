"""Vector retrieval over the ingested corpus (S8, ADR-0003)."""

from __future__ import annotations

from dataclasses import dataclass

from llama_index.core.vector_stores.types import VectorStoreQuery

from qms_incub.rag_clients import get_embed_model, get_vector_store


@dataclass
class RetrievedChunk:
    text: str
    document_id: str
    document_title: str
    source_type: str
    score: float


def retrieve_top_k(query: str, k: int = 4) -> list[RetrievedChunk]:
    embed_model = get_embed_model()
    query_embedding = embed_model.get_query_embedding(query)

    result = get_vector_store().query(
        VectorStoreQuery(query_embedding=query_embedding, similarity_top_k=k)
    )

    chunks: list[RetrievedChunk] = []
    nodes = result.nodes or []
    similarities = result.similarities or [0.0] * len(nodes)
    for node, score in zip(nodes, similarities):
        meta = node.metadata or {}
        chunks.append(
            RetrievedChunk(
                text=node.get_content(),
                document_id=meta.get("qms_document_id", "unknown"),
                document_title=meta.get("qms_document_title", "unknown"),
                source_type=meta.get("source_type", "unknown"),
                score=score,
            )
        )
    return chunks

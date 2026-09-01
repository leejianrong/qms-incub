"""Retrieval over the ingested corpus (S8, ADR-0003).

BM25 sparse lexical retrieval against the Qdrant collection, then an
optional rerank pass (``chat/rerank.py``) before returning the top-k.

Dense and hybrid retrieval were removed from this path: with the reranker
on, the candidate set it sees — and therefore the final ranking — came
out the same whichever way candidates were fetched, so BM25 alone is the
cheapest option. The collection is still ingested with dense vectors
present, so restoring a dense/hybrid query mode later needs no re-ingest.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from llama_index.core.vector_stores.types import VectorStoreQuery, VectorStoreQueryMode
from qdrant_client import models

from qms_incub.chat.rerank import get_reranker
from qms_incub.config import settings
from qms_incub.rag_clients import get_vector_store


@dataclass
class RetrievedChunk:
    text: str
    document_id: str
    document_title: str
    source_type: str
    score: float
    chunk_id: str = "unknown"
    # 0-based position of this chunk within its document. Stable across
    # re-ingestion of the same PDF (unlike chunk_id / document_id); used by
    # the retrieval eval harness for chunk-level scoring.
    chunk_index: int = -1


def _candidates(query: str, k: int) -> list[RetrievedChunk]:
    result = get_vector_store().query(
        VectorStoreQuery(
            query_str=query,
            sparse_top_k=k,
            mode=VectorStoreQueryMode.SPARSE,
        )
    )

    nodes = result.nodes or []
    similarities = result.similarities or [0.0] * len(nodes)
    chunks: list[RetrievedChunk] = []
    for node, score in zip(nodes, similarities):
        meta = node.metadata or {}
        try:
            chunk_index = int(meta.get("chunk_index", -1))
        except (TypeError, ValueError):
            chunk_index = -1
        chunks.append(
            RetrievedChunk(
                text=node.get_content(),
                document_id=meta.get("qms_document_id", "unknown"),
                document_title=meta.get("qms_document_title", "unknown"),
                source_type=meta.get("source_type", "unknown"),
                score=score or 0.0,
                chunk_id=str(node.node_id),
                chunk_index=chunk_index,
            )
        )
    return chunks


def fetch_document(document_id: str, *, score: float = 0.0) -> RetrievedChunk | None:
    """Return an entire document as one context block: every chunk stored
    for ``document_id``, concatenated in ``chunk_index`` order.

    Used by the chat flow to hand the LLM whole policies rather than only
    the passages that matched the query. Returns ``None`` if the document
    has no chunks in the store.
    """
    store = get_vector_store()
    points, _ = store.client.scroll(
        collection_name=store.collection_name,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="qms_document_id",
                    match=models.MatchValue(value=document_id),
                )
            ]
        ),
        limit=10_000,
        with_payload=True,
        with_vectors=False,
    )
    if not points:
        return None

    rows: list[tuple[int, str]] = []
    meta: dict[str, Any] = {}
    for p in points:
        payload = p.payload or {}
        meta = meta or payload
        try:
            text = json.loads(payload.get("_node_content", "{}")).get("text", "")
        except (TypeError, ValueError):
            text = ""
        try:
            idx = int(payload.get("chunk_index", 0))
        except (TypeError, ValueError):
            idx = 0
        rows.append((idx, text))
    rows.sort(key=lambda r: r[0])

    return RetrievedChunk(
        text="\n\n".join(text for _, text in rows if text),
        document_id=document_id,
        document_title=meta.get("qms_document_title", "unknown"),
        source_type=meta.get("source_type", "unknown"),
        score=score,
        chunk_id="full-document",
        chunk_index=-1,
    )


def retrieve(
    query: str,
    k: int = 4,
    *,
    rerank: bool = True,
    candidate_k: int | None = None,
) -> list[RetrievedChunk]:
    """Retrieve the top-k chunks for ``query`` via BM25, optionally reranked.

    When ``rerank`` is true, ``candidate_k`` chunks (default
    ``settings.retrieval_candidate_k``, never fewer than ``k``) are fetched
    and handed to the reranker, which returns the final ``k``.
    """
    fetch_k = max(candidate_k or settings.retrieval_candidate_k, k) if rerank else k
    candidates = _candidates(query, fetch_k)

    if rerank:
        candidates = get_reranker().rerank(query, candidates, top_n=k)
    return candidates[:k]

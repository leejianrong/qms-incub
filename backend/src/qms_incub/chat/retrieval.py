"""Retrieval over the ingested corpus (S8, ADR-0003) — the concrete,
Qdrant/LlamaIndex-backed implementation of `rag.ports.RetrievalPort`
(`LlamaIndexRetrieval`, at the bottom of this module). Callers outside this
module should go through `rag.factory.get_retrieval_port()` rather than
importing `retrieve`/`fetch_document` directly.

``RETRIEVAL_MODE`` picks the candidate-fetching strategy — ``"bm25"``
(sparse lexical, the default) or ``"vector"`` (dense embedding
similarity) — then an optional rerank pass (``chat/rerank.py``) narrows
to the requested top-k. Both query the same Qdrant collection: ingestion
writes a dense vector and a BM25 sparse vector for every chunk, so
switching modes needs no re-ingest. A fused hybrid mode (both signals
combined into one ranking, rather than picking one or the other) is
deferred — issue #53.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from llama_index.core.vector_stores.types import VectorStoreQuery, VectorStoreQueryMode
from qdrant_client import models

from qms_incub.chat.rerank import get_reranker
from qms_incub.config import settings
from qms_incub.rag.ports import RetrievedChunk as RetrievedChunk
from qms_incub.rag_clients import get_embed_model, get_vector_store


def _nodes_to_chunks(
    nodes: Sequence[Any], similarities: list[float] | None
) -> list[RetrievedChunk]:
    similarities = similarities or [0.0] * len(nodes)
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


def _bm25_candidates(query: str, k: int) -> list[RetrievedChunk]:
    result = get_vector_store().query(
        VectorStoreQuery(
            query_str=query,
            sparse_top_k=k,
            mode=VectorStoreQueryMode.SPARSE,
        )
    )
    return _nodes_to_chunks(result.nodes or [], result.similarities)


def _vector_candidates(query: str, k: int) -> list[RetrievedChunk]:
    query_embedding = get_embed_model().get_query_embedding(query)
    result = get_vector_store().query(
        VectorStoreQuery(query_embedding=query_embedding, similarity_top_k=k)
    )
    return _nodes_to_chunks(result.nodes or [], result.similarities)


def _candidates(query: str, k: int) -> list[RetrievedChunk]:
    if settings.retrieval_mode == "vector":
        return _vector_candidates(query, k)
    return _bm25_candidates(query, k)


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
    """Retrieve the top-k chunks for ``query`` via ``settings.retrieval_mode``
    (``"bm25"`` or ``"vector"``), optionally reranked.

    When ``rerank`` is true, ``candidate_k`` chunks (default
    ``settings.retrieval_candidate_k``, never fewer than ``k``) are fetched
    and handed to the reranker, which returns the final ``k``.
    """
    fetch_k = max(candidate_k or settings.retrieval_candidate_k, k) if rerank else k
    candidates = _candidates(query, fetch_k)

    if rerank:
        candidates = get_reranker().rerank(query, candidates, top_n=k)
    return candidates[:k]


class LlamaIndexRetrieval:
    """`rag.ports.RetrievalPort` implementation backed by this module's
    functions — the only implementation today. Returned by
    `rag.factory.get_retrieval_port()`."""

    def retrieve(
        self,
        query: str,
        k: int = 4,
        *,
        rerank: bool = True,
        candidate_k: int | None = None,
    ) -> list[RetrievedChunk]:
        return retrieve(query, k, rerank=rerank, candidate_k=candidate_k)

    def fetch_document(
        self, document_id: str, *, score: float = 0.0
    ) -> RetrievedChunk | None:
        return fetch_document(document_id, score=score)

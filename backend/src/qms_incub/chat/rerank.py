"""Cross-encoder reranking of retrieval candidates (Q19).

The retriever (dense or BM25) returns a wide, cheap candidate set; the
reranker reorders it with a stronger relevance model and hands back the
top-n. The model is undecided, so this is deliberately thin:

- ``ZenMuxReranker`` — ZenMux's hosted ``POST /rerank`` (DashScope/Qwen
  shape): request ``{model, input: {query, documents}, parameters:
  {top_n, return_documents}}``; response ``{output: {results: [{index,
  relevance_score}, ...]}}``. A flat top-level ``results`` is tolerated
  too, in case the envelope differs.
- ``NoOpReranker`` — passthrough, preserving retriever order.

Auth reuses ``settings.zenmux_api_key`` — the shared key #30 distributed
for the Q39 window — so there's one ZenMux key, not one per feature. With
no key set (e.g. after the window closes) this degrades to the no-op with
a warning, so local dev keeps working without extra setup.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

import httpx

from qms_incub.config import settings

if TYPE_CHECKING:
    from qms_incub.chat.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


class Reranker(Protocol):
    def rerank(
        self, query: str, chunks: list[RetrievedChunk], top_n: int
    ) -> list[RetrievedChunk]: ...


class NoOpReranker:
    """Keeps the retriever's own ordering, just truncating to top_n."""

    def rerank(
        self, query: str, chunks: list[RetrievedChunk], top_n: int
    ) -> list[RetrievedChunk]:
        return chunks[:top_n]


class ZenMuxReranker:
    """ZenMux's hosted ``POST /rerank`` (DashScope/Qwen request+response
    shape). See the module docstring for the JSON contract."""

    def __init__(self, *, api_key: str, url: str, model: str, timeout_s: float) -> None:
        self._url = url
        self._model = model
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._timeout_s = timeout_s

    def rerank(
        self, query: str, chunks: list[RetrievedChunk], top_n: int
    ) -> list[RetrievedChunk]:
        if not chunks:
            return []

        payload = {
            "model": self._model,
            "input": {
                "query": query,
                "documents": [c.text for c in chunks],
            },
            # We map results back to chunks by index, so no need to have
            # the documents echoed in the response.
            "parameters": {"top_n": top_n, "return_documents": False},
        }
        response = httpx.post(
            self._url, json=payload, headers=self._headers, timeout=self._timeout_s
        )
        response.raise_for_status()
        body = response.json()
        # DashScope-style: results nested under "output". Tolerate a flat
        # top-level "results" too, in case ZenMux's envelope differs.
        results = (body.get("output") or body).get("results", [])

        reranked: list[RetrievedChunk] = []
        for item in results:
            chunk = chunks[int(item["index"])]
            chunk.score = float(item.get("relevance_score", chunk.score))
            reranked.append(chunk)
        # If the API returned nothing usable, fall back to retriever order
        # rather than silently dropping every candidate.
        return (reranked or list(chunks))[:top_n]


_reranker: Reranker | None = None


def get_reranker() -> Reranker:
    """Process-wide reranker, built once from settings."""
    global _reranker
    if _reranker is None:
        _reranker = _build_reranker()
    return _reranker


def _build_reranker() -> Reranker:
    provider = settings.reranker_provider
    if provider == "none":
        return NoOpReranker()
    if provider == "zenmux":
        if not settings.zenmux_api_key:
            logger.warning(
                "RERANKER_PROVIDER=zenmux but ZENMUX_API_KEY is unset — "
                "reranking disabled (candidates kept in retriever order)."
            )
            return NoOpReranker()
        return ZenMuxReranker(
            api_key=settings.zenmux_api_key,
            url=settings.zenmux_rerank_url,
            model=settings.reranker_model,
            timeout_s=settings.reranker_timeout_s,
        )
    raise ValueError(f"unknown reranker provider: {provider!r}")

"""Reranking of retrieval candidates (Q19).

The retriever (BM25) returns a wide, cheap candidate set; the reranker
reorders it with a stronger relevance signal and hands back the top-n.
Three providers, chosen by ``settings.reranker_provider``:

- ``ZenMuxReranker`` — ZenMux's hosted ``POST /rerank`` (DashScope/Qwen
  shape): request ``{model, input: {query, documents}, parameters:
  {top_n, return_documents}}``; response ``{output: {results: [{index,
  relevance_score}, ...]}}``. A flat top-level ``results`` is tolerated
  too, in case the envelope differs. Cheap and fast — no LLM tokens spent
  — but ZenMux-only.
- ``LLMPromptReranker`` — asks whichever provider ``LLM_PROVIDER`` is
  already set to (ollama/openrouter/zenmux, via ``chat/llm.get_llm_client``)
  to rank the candidates. Costs LLM tokens and a round trip, but works
  with any of the three providers already wired for chat — no separate
  rerank API needed for ollama/openrouter.
- ``NoOpReranker`` — passthrough, preserving retriever order. The default:
  no reranker provider should be assumed configured.

Both real rerankers degrade to the no-op with a warning if their
provider's credentials aren't set (e.g. ZENMUX_API_KEY unset, or
LLM_PROVIDER pointing at a provider missing its key), so local dev keeps
working without extra setup.
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Protocol

import httpx

from qms_incub.config import settings

if TYPE_CHECKING:
    from openai import OpenAI

    from qms_incub.chat.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

# Cap per-chunk text in the rerank prompt so a wide candidate_k doesn't
# blow up the prompt size, especially against smaller local Ollama models.
_LLM_RERANK_CHUNK_CHARS = 500


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


class LLMPromptReranker:
    """Ranks candidates by prompting the already-configured chat LLM
    (whichever provider ``LLM_PROVIDER`` names) instead of a dedicated
    rerank API. Works with ollama/openrouter/zenmux alike."""

    def __init__(self, *, client: OpenAI, model: str) -> None:
        self._client = client
        self._model = model

    def rerank(
        self, query: str, chunks: list[RetrievedChunk], top_n: int
    ) -> list[RetrievedChunk]:
        if not chunks:
            return []

        listing = "\n".join(
            f"[{i}] {c.text[:_LLM_RERANK_CHUNK_CHARS]}" for i, c in enumerate(chunks)
        )
        prompt = (
            "Rank the following numbered passages by relevance to the query, "
            "most relevant first. Respond with ONLY a JSON array of the "
            f"passage numbers, e.g. [2, 0, 1]. Return at most {top_n} numbers.\n\n"
            f"Query: {query}\n\nPassages:\n{listing}"
        )
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            content = response.choices[0].message.content or ""
            order = self._parse_order(content, len(chunks))
        except Exception:
            logger.warning("LLM reranker call failed — keeping retriever order.", exc_info=True)
            return chunks[:top_n]

        if not order:
            return chunks[:top_n]
        reranked = [chunks[i] for i in order if 0 <= i < len(chunks)]
        # Fill any remainder (model returned fewer than top_n, or skipped
        # some indices) with the untouched retriever order, deduplicated.
        seen = set(order)
        reranked.extend(c for i, c in enumerate(chunks) if i not in seen)
        return reranked[:top_n]

    @staticmethod
    def _parse_order(content: str, n: int) -> list[int]:
        match = re.search(r"\[[\d,\s]*\]", content)
        if not match:
            return []
        try:
            indices = json.loads(match.group(0))
        except (json.JSONDecodeError, ValueError):
            return []
        seen: set[int] = set()
        order: list[int] = []
        for idx in indices:
            if isinstance(idx, int) and 0 <= idx < n and idx not in seen:
                seen.add(idx)
                order.append(idx)
        return order


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
    if provider == "llm":
        from qms_incub.chat.llm import get_llm_client

        try:
            client, model = get_llm_client()
        except RuntimeError as exc:
            logger.warning(
                "RERANKER_PROVIDER=llm but the configured LLM_PROVIDER isn't "
                "usable (%s) — reranking disabled (candidates kept in "
                "retriever order).",
                exc,
            )
            return NoOpReranker()
        return LLMPromptReranker(client=client, model=model)
    raise ValueError(f"unknown reranker provider: {provider!r}")

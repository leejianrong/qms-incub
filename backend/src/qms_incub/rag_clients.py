"""Shared, lazily-initialized clients for the embedding model and vector
store (ADR-0009), used by both ingestion (S6) and retrieval (S8).

Dense embeddings are provider-swappable (Q36, same pattern as `chat/llm.py`'s
`LLM_PROVIDER`): ``EMBEDDING_PROVIDER=local`` (default) runs a HuggingFace
sentence-embedding model in-process, no API key, offline-capable — but it
needs a machine that can actually run the model. `BAAI/bge-small-en-v1.5`
(the default) is a ~33M-parameter model built for CPU inference and is fast
enough there for this project's scale; it does not need a GPU. A much larger
local embedding model would, so if `EMBEDDING_MODEL` is ever changed to one,
revisit this. ``openrouter`` / ``zenmux`` instead call a hosted
OpenAI-compatible ``/embeddings`` endpoint — useful for a machine you'd
rather not run any local model on at all — at the cost of a network round
trip per chunk (ingestion) and per query (retrieval), and losing offline
capability. Ingestion and retrieval must use the same provider+model at all
times: they write/query the same Qdrant collection, and switching providers
changes the vector's dimensionality, so it is not a hot-swap like
`RETRIEVAL_MODE` — the collection needs re-ingesting after a provider change.

The vector store is hybrid regardless of embedding provider: LlamaIndex also
writes (on ingest) and queries a sparse BM25 vector per chunk via a local
fastembed model, so no API key and no separate sparse client is needed here.
"""

from __future__ import annotations

from typing import Protocol

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from openai import OpenAI
from qdrant_client import QdrantClient

from qms_incub.config import settings


class EmbeddingModel(Protocol):
    """The only two methods ingestion (`get_text_embedding`) and retrieval
    (`get_query_embedding`) actually call — small enough that the hosted
    backends below don't need to be full `llama_index` embedding classes."""

    def get_text_embedding(self, text: str) -> list[float]: ...

    def get_query_embedding(self, query: str) -> list[float]: ...


class _OpenAICompatibleEmbedding:
    """Embeds via an OpenAI-compatible ``POST /embeddings`` (OpenRouter or
    ZenMux). Both expose the same request/response shape as OpenAI's own
    embeddings API, so one class serves either. There's no separate
    instruction-prefixed query mode here like some local models use — text
    and query embedding are the same call."""

    def __init__(self, *, client: OpenAI, model: str) -> None:
        self._client = client
        self._model = model

    def _embed(self, text: str) -> list[float]:
        response = self._client.embeddings.create(model=self._model, input=text)
        return response.data[0].embedding

    def get_text_embedding(self, text: str) -> list[float]:
        return self._embed(text)

    def get_query_embedding(self, query: str) -> list[float]:
        return self._embed(query)


_embed_model: EmbeddingModel | None = None
_vector_store: QdrantVectorStore | None = None


def get_embed_model() -> EmbeddingModel:
    global _embed_model
    if _embed_model is None:
        _embed_model = _build_embed_model()
    return _embed_model


def _build_embed_model() -> EmbeddingModel:
    provider = settings.embedding_provider
    if provider == "openrouter":
        if not settings.openrouter_api_key:
            raise RuntimeError(
                "EMBEDDING_PROVIDER=openrouter but OPENROUTER_API_KEY is unset "
                "— set it in backend/.env."
            )
        client = OpenAI(
            api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url
        )
        return _OpenAICompatibleEmbedding(
            client=client, model=settings.openrouter_embedding_model
        )
    if provider == "zenmux":
        if not settings.zenmux_api_key:
            raise RuntimeError(
                "EMBEDDING_PROVIDER=zenmux but ZENMUX_API_KEY is unset — set it "
                "in backend/.env."
            )
        client = OpenAI(
            api_key=settings.zenmux_api_key, base_url=settings.zenmux_base_url
        )
        return _OpenAICompatibleEmbedding(
            client=client, model=settings.zenmux_embedding_model
        )
    return HuggingFaceEmbedding(model_name=settings.embedding_model)


def get_vector_store() -> QdrantVectorStore:
    """Hybrid Qdrant store shared by ingestion and retrieval.

    `enable_hybrid=True` makes `.add()` store a fastembed sparse vector
    alongside each dense vector, and lets `.query()` run SPARSE / HYBRID
    modes. The collection must be (re)ingested under this setting — points
    written dense-only have no sparse vector to match.
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = QdrantVectorStore(
            client=QdrantClient(url=settings.qdrant_url),
            collection_name=settings.qdrant_collection,
            enable_hybrid=True,
            fastembed_sparse_model=settings.sparse_embedding_model,
        )
    return _vector_store

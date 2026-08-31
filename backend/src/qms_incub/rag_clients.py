"""Shared, lazily-initialized clients for the embedding model and vector
store (ADR-0009), used by both ingestion (S6) and retrieval (S8)."""

from __future__ import annotations

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from qms_incub.config import settings

_embed_model: HuggingFaceEmbedding | None = None
_vector_store: QdrantVectorStore | None = None


def get_embed_model() -> HuggingFaceEmbedding:
    global _embed_model
    if _embed_model is None:
        _embed_model = HuggingFaceEmbedding(model_name=settings.embedding_model)
    return _embed_model


def get_vector_store() -> QdrantVectorStore:
    global _vector_store
    if _vector_store is None:
        client = QdrantClient(url=settings.qdrant_url)
        _vector_store = QdrantVectorStore(
            client=client,
            collection_name=settings.qdrant_collection,
        )
    return _vector_store

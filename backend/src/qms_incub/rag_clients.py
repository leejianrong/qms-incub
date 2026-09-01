"""Shared, lazily-initialized clients for the embedding model and vector
store (ADR-0009), used by both ingestion (S6) and retrieval (S8).

Dense embeddings run through a local HuggingFace model (Q36). The vector
store is hybrid: LlamaIndex also writes (on ingest) and queries a sparse
BM25 vector per chunk via a local fastembed model, so no API key and no
separate sparse client is needed here.
"""

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

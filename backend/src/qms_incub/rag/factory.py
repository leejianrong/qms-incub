"""Resolves the RAG ports (`ports.py`) to a concrete implementation.

Today there's exactly one: Docling + LlamaIndex + Qdrant, the same code
`ingestion/pipeline.py` and `chat/retrieval.py` always had. Not cached —
each call is a cheap wrapper construction; the expensive state (the
embedding model, the vector store client) is already lazily cached in
`rag_clients.py`. A second implementation, if one is ever written, plugs
in here behind a setting, the same way `LLM_PROVIDER`/`RERANKER_PROVIDER`
pick an implementation in `chat/llm.py`/`chat/rerank.py`.
"""

from __future__ import annotations

from qms_incub.chat.retrieval import LlamaIndexRetrieval
from qms_incub.ingestion.pipeline import DoclingLlamaIndexIngestion
from qms_incub.rag.ports import IngestionPort, RetrievalPort


def get_ingestion_port() -> IngestionPort:
    return DoclingLlamaIndexIngestion()


def get_retrieval_port() -> RetrievalPort:
    return LlamaIndexRetrieval()

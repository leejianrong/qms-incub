"""The RAG layer's boundary: the two things the rest of the app (HTTP
routers, `chat/service.py`'s compliance-state grounding, the eval harness)
depend on, instead of reaching into `ingestion/pipeline.py`,
`chat/retrieval.py`, or `rag_clients.py` directly.

Swapping the RAG implementation later means writing a new class that
satisfies these two Protocols and pointing `rag/factory.py` at it — no
caller changes. `chat/service.py`'s compliance-state grounding (V8) is
deliberately not part of either port: it's project-specific business data
read straight from Postgres, not something a generic RAG implementation
should know exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


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


class IngestionPort(Protocol):
    """Get a document's content into the corpus."""

    def ingest_pdf(
        self,
        pdf_path: Path,
        document_id: str,
        document_title: str,
        source_type: str = "policy_document",
    ) -> int: ...

    def ingest_text(
        self, text: str, document_id: str, document_title: str, source_type: str
    ) -> int: ...


class RetrievalPort(Protocol):
    """Query the corpus for a chat request, the debug `/retrieve` endpoint,
    or an eval run."""

    def retrieve(
        self,
        query: str,
        k: int = 4,
        *,
        rerank: bool = True,
        candidate_k: int | None = None,
    ) -> list[RetrievedChunk]: ...

    def fetch_document(
        self, document_id: str, *, score: float = 0.0
    ) -> RetrievedChunk | None: ...

"""`PolicyDocumentRow` — one row per uploaded document, tracking its
progress through the ingestion pipeline (S6). Not a document content
model: the backend never stores or composes document content itself, only
what Docling/LlamaIndex derive from an uploaded PDF."""

from __future__ import annotations

import datetime
from typing import Literal

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from qms_incub.db import Base

IngestionStatus = Literal["pending", "embedded", "failed"]


class PolicyDocumentRow(Base):
    __tablename__ = "policy_documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    chunk_count: Mapped[int | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

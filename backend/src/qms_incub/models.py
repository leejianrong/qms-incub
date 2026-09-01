"""`PolicyDocumentRow` — one row per uploaded document, tracking its
progress through the ingestion pipeline (S6). Not a document content
model: the backend never stores or composes document content itself, only
what Docling/LlamaIndex derive from an uploaded PDF."""

from __future__ import annotations

import datetime
import uuid
from typing import Literal

from sqlalchemy import DateTime, String, Text, func
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


def _uuid() -> str:
    return str(uuid.uuid4())


class BlogPost(Base):
    """Admin-authored, plain-text corpus content (V6)."""

    __tablename__ = "blog_posts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    published_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    chunk_count: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FAQEntry(Base):
    """Admin-authored question and answer pair for the RAG corpus (V6)."""

    __tablename__ = "faq_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    question: Mapped[str] = mapped_column(Text, nullable=False, default="")
    answer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    published_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    chunk_count: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

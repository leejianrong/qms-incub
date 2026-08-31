"""Minimal `PolicyDocument` persistence (V5) — just enough for the
ingestion-status dashboard (SLICES.md § V5 step 3). Not the full
`PolicyDocument` shape from PLAN.md's Implementation decisions (no
`Block` rows, no Draft/Published lifecycle, no org-scoping column yet) —
that lands with the rest of the data model in V2/V4/ADR-0004."""

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
    origin: Mapped[str] = mapped_column(String, nullable=False, default="generated")
    is_synthetic: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    chunk_count: Mapped[int | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

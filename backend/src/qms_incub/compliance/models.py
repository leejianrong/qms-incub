"""Compliance data model (ADR-0008, V2). `ComplianceStandard` -> `Clause`
-> `Requirement` is user-authored, QA-author-maintained content — no
hardcoded regulatory schema. A `Project`'s wizard answers produce a risk
tier (S1); todo generation (S2) creates one `TodoItem` per `Requirement`
tagged for that tier, each traceable back to its Requirement, Clause, and
Standard."""

from __future__ import annotations

import datetime
import uuid
from typing import Literal

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from qms_incub.db import Base

RiskTier = Literal["low", "medium", "high"]
TodoStatus = Literal["pending", "complied"]
ApprovalState = Literal["not_required", "not_started", "submitted", "approved", "returned"]


def _uuid() -> str:
    return str(uuid.uuid4())


class ComplianceStandard(Base):
    __tablename__ = "compliance_standards"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Clause(Base):
    __tablename__ = "clauses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    standard_id: Mapped[str] = mapped_column(
        String, ForeignKey("compliance_standards.id"), nullable=False
    )
    ordering: Mapped[int] = mapped_column(nullable=False, default=0)
    text: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    clause_id: Mapped[str] = mapped_column(String, ForeignKey("clauses.id"), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    # e.g. ["medium", "high"] — which wizard-derived risk tiers this
    # Requirement generates a TodoItem for (ADR-0008).
    risk_tiers: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Project(Base):
    """`risk_tier` starts null: a Project is created from just a name
    (wizard step 1, alongside an optional AOR upload, S10), then
    classified — which sets `risk_tier` and generates TodoItems — once
    the 3-question wizard (S1/S2) is submitted (wizard step 2)."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    risk_tier: Mapped[str | None] = mapped_column(String, nullable=True)
    # AOR intake (S10, Q40): extraction of an uploaded document's own
    # content, never entered into the Qdrant corpus (ADR-0012).
    aor_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    aor_extracted_fields: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TodoItem(Base):
    """`approval_state`/`approval_authority`/`sla_target` are assigned at
    generation time (S2, `classify_project`); self-attestation (S3) sets
    `approval_state` to `approved` and stamps `decided_at` in the same
    transaction as the Complied status flip. Schema-only — no reviewer
    role or gate exists yet (Q42, additive to ADR-0002)."""

    __tablename__ = "todo_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    requirement_id: Mapped[str] = mapped_column(
        String, ForeignKey("requirements.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    approval_state: Mapped[str] = mapped_column(String, nullable=False, default="not_started")
    approval_authority: Mapped[str] = mapped_column(String, nullable=False, default="QA Office")
    sla_target: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decided_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Artifact(Base):
    """Proof of compliance uploaded against a `TodoItem` (S3). Uploading
    one is self-attestation, not a reviewed submission — it flips the
    TodoItem straight to Complied (ADR-0002), no reviewer gate."""

    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    todo_item_id: Mapped[str] = mapped_column(String, ForeignKey("todo_items.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

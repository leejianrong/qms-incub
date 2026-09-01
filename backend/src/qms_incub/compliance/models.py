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

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from qms_incub.db import Base

RiskTier = Literal["low", "medium", "high"]
TodoStatus = Literal["pending", "complied"]


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
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    risk_tier: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TodoItem(Base):
    __tablename__ = "todo_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    requirement_id: Mapped[str] = mapped_column(
        String, ForeignKey("requirements.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

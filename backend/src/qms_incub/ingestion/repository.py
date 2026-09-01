"""CRUD for `PolicyDocumentRow` — ingestion-status tracking for uploaded
documents (S6). Every document the backend knows about arrived via the
upload endpoint; there is no generated/imported distinction to track."""

from __future__ import annotations

from dataclasses import dataclass

from qms_incub.db import get_session
from qms_incub.models import PolicyDocumentRow


@dataclass
class DocumentStatus:
    id: str
    title: str
    status: str
    chunk_count: int | None
    error: str | None


def create_pending(document_id: str, title: str) -> None:
    # merge, not add: re-uploading the same document_id must reset status
    # to pending rather than fail on a duplicate primary key.
    with get_session() as session:
        session.merge(
            PolicyDocumentRow(
                id=document_id,
                title=title,
                status="pending",
                chunk_count=None,
                error=None,
            )
        )


def mark_embedded(document_id: str, chunk_count: int) -> None:
    with get_session() as session:
        row = session.get(PolicyDocumentRow, document_id)
        if row is not None:
            row.status = "embedded"
            row.chunk_count = chunk_count


def mark_failed(document_id: str, error: str) -> None:
    with get_session() as session:
        row = session.get(PolicyDocumentRow, document_id)
        if row is not None:
            row.status = "failed"
            row.error = error


def delete_by_id(document_id: str) -> None:
    with get_session() as session:
        row = session.get(PolicyDocumentRow, document_id)
        if row is not None:
            session.delete(row)


def list_all() -> list[DocumentStatus]:
    with get_session() as session:
        rows = session.query(PolicyDocumentRow).order_by(PolicyDocumentRow.created_at.desc()).all()
        return [
            DocumentStatus(
                id=row.id,
                title=row.title,
                status=row.status,
                chunk_count=row.chunk_count,
                error=row.error,
            )
            for row in rows
        ]

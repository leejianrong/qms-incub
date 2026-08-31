"""SQLAlchemy engine/session (V5 — the first slice to touch the data
model). Scoped deliberately to just what V5's ingestion-status dashboard
needs; the full data model (Project/TodoItem/Standard/Clause/Requirement,
ADR-0008) lands in V2."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from qms_incub.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

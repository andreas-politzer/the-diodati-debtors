"""SQLAlchemy engine and session factory.

Phase 0 scope: connection plumbing only. No models are queried here,
and this module must never be imported by anything under ui/ directly —
only services/ and state/ may use it, per the architecture contract in
Implementation Specification.md.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import settings

engine = create_engine(
    settings.sqlalchemy_database_uri,
    pool_pre_ping=True,
    echo=settings.debug,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional scope for a single unit of work.

    Usage:
        with get_session() as session:
            session.add(some_model)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

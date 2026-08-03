"""Shared pytest fixtures.

Tests run against an isolated in-memory SQLite database, never the
real development MySQL instance — this keeps the Service Contract's
"no session passed in" rule intact while still making services
testable: `db.session.SessionLocal` is monkeypatched to point at this
test engine for the duration of each test that requests the `db`
fixture, so services need no test-specific code path.

Works because the ORM layer uses only portable SQLAlchemy types — no
MySQL-specific constructs.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import diodati_debtors.db.session as db_session
import diodati_debtors.models  # noqa: F401 - registers all models on Base.metadata
from diodati_debtors.db.base import Base


@pytest.fixture()
def test_engine():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture()
def db(test_engine, monkeypatch):
    """Point db.session.SessionLocal at the isolated test engine for
    the duration of a single test.
    """
    test_session_local = sessionmaker(
        bind=test_engine, autoflush=False, autocommit=False, future=True
    )
    monkeypatch.setattr(db_session, "SessionLocal", test_session_local)
    yield test_session_local

@pytest.fixture(autouse=True)
def mock_gemini_generate_text(monkeypatch):
    """Prevents real Gemini API calls during tests — book_service.
    create_book now always computes an embedding (02.08. fix), which
    internally calls generate_text (fallback description) AND
    embed_text (the actual vector) when no summary exists. Without
    this mock, every test using create_book (63+ call sites) makes
    real, slow API calls. Tests that specifically need to control
    generate_text/embed_text's return value can still override this
    mock locally via their own monkeypatch.setattr call.
    """
    import diodati_debtors.services.book_service as book_service_module

    def fake_generate_text(prompt: str) -> str:
        return "A book, for testing purposes."

    def fake_embed_text(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        return [0.1] * 768

    monkeypatch.setattr(book_service_module, "generate_text", fake_generate_text)
    monkeypatch.setattr(book_service_module, "embed_text", fake_embed_text)
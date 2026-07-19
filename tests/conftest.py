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
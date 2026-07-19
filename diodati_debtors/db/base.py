"""Declarative base for all SQLAlchemy models.

Architecture rule: SQLAlchemy models plus Alembic migrations are the
schema source of truth. No second, hand-maintained DDL file exists
alongside this. Every model in models/ must inherit from `Base` defined
here, nowhere else.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base class for all ORM models."""


__all__ = ["Base"]
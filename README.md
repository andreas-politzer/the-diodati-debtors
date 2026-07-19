# The Diodati Debtors

A small community library app for a book club: members catalogue their
own books, lend and borrow within the group, post recommendations, and
see a trust score reflecting on-time returns.

Working title references the Villa Diodati (summer of 1816 — Byron,
Mary Shelley, Polidori) and doubles as a pun: "Debtors" are the members
who haven't returned a book yet.

## Status

Phase 0 (bootstrap) complete. No feature logic yet — see
`Implementation Specification.md` in the project vault for the full
phased plan and current gate.

## Stack

- [Reflex](https://reflex.dev) — Python-only frontend/backend, compiles to React
- MySQL (via Docker) + SQLAlchemy + Alembic
- Design tokens per the project's design contract (see vault)

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in local DB credentials
reflex run
```

## Architecture

- `core/` — framework-agnostic configuration
- `db/` — SQLAlchemy engine, session, declarative base (schema source of
  truth via SQLAlchemy models + Alembic migrations — no separate
  hand-maintained schema.sql)
- `models/` — SQLAlchemy entities only
- `services/` — business logic, no Reflex import
- `state/` — the only layer bridging Reflex UI and services
- `ui/` — presentation only, imports state, never services or models directly

## Testing

```bash
ruff check .
pytest
```

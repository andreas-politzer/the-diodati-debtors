# The Diodati Debtors

A small community library app for a book club: members catalogue their
own books, lend and borrow within the group, post recommendations, and
see a trust score reflecting on-time returns.

Working title references the Villa Diodati (summer of 1816 — Byron,
Mary Shelley, Polidori) and doubles as a pun: "Debtors" are the members
who haven't returned a book yet.

## Status

**Working and tested:**
- Full auth flow: registration, login, session cookie
- Personal library CRUD: add a book, view details, lend, return —
  backed by real services and a MySQL database, no mock data
- 22 passing unit tests across `auth_service`, `book_service`,
  `loan_service`, isolated against an in-memory SQLite test database
- Design system (custom typography, flat/no-shadow visual language,
  documented design contract) applied throughout

**In progress right now:**
- Multi-club architecture: a user can found or join several book
  clubs (Kicktipp-style — pick a club after login, not baked into the
  account). Domain model in place (`Group` with a founder, member
  roles, `JoinRequest`/`LoanRequest` as distinct entities from
  `Membership`/`Loan`), group-scoped dashboard and request/approval
  workflow (replacing instant lending with an owner-approved request,
  closer to how lending actually works between people) being wired up
  next.

**Deliberately deferred, documented as concepts, not yet built:**
- Open Library ISBN lookup for auto-filling book metadata
- Reservations ("notify me when this book is returned")
- Lending to non-registered contacts (neighbours, family)
- Trust score, AI-assisted reminder emails, a semantic book-recommendation agent

See `Implementation Specification.md` and `Domain Model v2.md` in the
project vault for the full phased plan and current architectural
decisions.

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
alembic upgrade head
reflex run
```

To populate demo data (requires `DIODATI_DEBUG=true` in `.env`):

```bash
python scripts/seed_demo.py
```

Then visit `http://localhost:3000/`.

## Architecture

- `core/` — framework-agnostic configuration, exceptions, time/normalization policy, password hashing
- `db/` — SQLAlchemy engine, session, declarative base (schema source of
  truth via SQLAlchemy models + Alembic migrations — no separate
  hand-maintained schema.sql)
- `models/` — SQLAlchemy entities only, no business logic
- `services/` — business logic, no Reflex import, organized by bounded
  context (`auth_service`, `user_service`, `book_service`, `loan_service`, ...)
- `state/` — the only layer bridging Reflex UI and services
- `ui/` — presentation only, imports state, never services or models directly

Layering is a hard constraint, not a convention: services never import
Reflex, state never touches the ORM directly, and business rules
(e.g. "a book can't have two active loans") live exclusively in the
service layer.

## Testing

```bash
ruff check .
pytest tests/unit/ -v
```
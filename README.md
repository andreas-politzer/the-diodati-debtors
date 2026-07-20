# The Diodati Debtors

A small community library app for a book club: members catalogue their
own books, lend and borrow within the group, post recommendations, and
see a trust score reflecting on-time returns.

Working title references the Villa Diodati (summer of 1816 — Byron,
Mary Shelley, Polidori) and doubles as a pun: "Debtors" are the members
who haven't returned a book yet.

## Status

**Working and tested (45 passing unit tests):**
- Full auth flow: registration, login, session cookie
- Multi-club membership: found a club (founder invariant enforced),
  browse and request to join other clubs, founder approves/declines —
  a user can belong to several clubs (Kicktipp-style, pick one after
  login) or use the app with zero clubs at all
- Personal Library (always available, no club required) and Common
  Library (all books visible to a selected club's members) as tabs on
  one dashboard — same list component, different data source
- Book CRUD: add a book (title required, everything else optional,
  including a free-text location field), view details with full loan
  history
- Loan-request/approval workflow at the service layer: a borrower
  requests a book, the owner approves or declines — replaces instant
  lending (closer to how borrowing actually works between people).
  Service layer complete with tests; not yet wired into the UI (still
  using the older instant "Lend to" picker on screen for now)
- Design system (custom typography, flat/no-shadow visual language,
  documented design contract) applied throughout

**In progress right now:**
- Wiring the loan-request workflow into State/UI (replacing the
  instant "Lend to" dropdown)
- An "Organize" inbox — where a club founder can see and act on
  pending club-join requests, and a book owner can see and act on
  pending loan requests, in one place

**Deliberately deferred, documented as concepts, not yet built:**
- Open Library ISBN lookup for auto-filling book metadata
- Reservations ("notify me when this book is returned")
- Lending to non-registered contacts (neighbours, family)
- A "Members" view per club — browse fellow members' personal libraries
- Trust score (reliability) and a separate book-condition/care signal,
  AI-assisted reminder emails, a semantic book-recommendation agent

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
  context (`auth_service`, `user_service`, `book_service`,
  `loan_service`, `group_service`, ...)
- `state/` — the only layer bridging Reflex UI and services, itself
  split by bounded context (`AuthState`, `GroupState`, `LibraryState`)
- `ui/` — presentation only, imports state, never services or models directly

Layering is a hard constraint, not a convention: services never import
Reflex, state never touches the ORM directly, and business rules
(e.g. "a book can't have two active loans", "a group's founder always
holds the FOUNDER role") live exclusively in the service layer.

## Testing

```bash
ruff check .
pytest tests/unit/ -v
```
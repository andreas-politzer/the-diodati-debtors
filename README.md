# The Diodati Debtors

A small community library app for a book club: members catalogue their
own books, lend and borrow within the group, post recommendations, and
see a trust score reflecting on-time returns.

Working title references the Villa Diodati (summer of 1816 — Byron,
Mary Shelley, Polidori) and doubles as a pun: "Debtors" are the members
who haven't returned a book yet.

## Status

**Working and tested (48 passing unit tests):**
- Full auth flow: registration, login, session cookie
- Multi-club membership: found a club (founder invariant enforced),
  browse and request to join other clubs, founder approves/declines,
  edit a club's description (founder-only, collapsible "About" when
  browsing) — a user can belong to several clubs or use the app with
  zero clubs at all
- Personal Library (always available, no club required) and Common
  Club Library (all books visible to a selected club's members) as
  tabs on one dashboard, with a club switcher directly on the Common
  tab (no page navigation needed to change which club you're viewing)
  — proper empty states for every combination (no books yet, no club
  selected, club has no books)
- Members page: every member of every club you belong to, grouped by
  club, with a read-only view into each member's personal library
  (reusing the exact same book-row component as the dashboard)
- Book CRUD: add a book (title required, everything else — author,
  ISBN, location — optional), view full details and loan history
- Lending via a request/approval workflow, not instant lending: a
  borrower requests a book, the owner approves or declines — closer to
  how borrowing actually works between people. Same pattern for club
  membership (join requests, founder approves/declines)
- A unified "Organize" inbox: pending club-join requests (for clubs you
  founded) and pending loan requests (for books you own) in one place
- Design system (custom typography, flat/no-shadow visual language,
  documented design contract) applied throughout

**Deliberately deferred, documented as concepts, not yet built:**
- Open Library ISBN lookup for auto-filling book metadata
- Reservations ("notify me when this book is returned")
- Lending to non-registered contacts (neighbours, family)
- Editing/deleting your own books after adding them
- A predefined genre field, trust score, book-condition signal,
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

Then visit `http://localhost:3000/`. All demo users share the password
`seeddemo123` (see the script's printed output for their emails and
what club/role each one has).

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
  split by bounded context (`AuthState`, `GroupState`, `LibraryState`,
  `OrganizeState`)
- `ui/` — presentation only, imports state, never services or models
  directly; shared components (e.g. `book_row`) are reused across
  pages rather than duplicated

Layering is a hard constraint, not a convention: services never import
Reflex, state never touches the ORM directly, and business rules
(e.g. "a book can't have two active loans", "a group's founder always
holds the FOUNDER role") live exclusively in the service layer.

## Testing

```bash
ruff check .
pytest tests/unit/ -v
```
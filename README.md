# The Diodati Debtors

A small community library app for a book club: members catalogue their
own books, lend and borrow within the group, post recommendations, and
see a trust score reflecting on-time returns.

Working title references the Villa Diodati (summer of 1816 — Byron,
Mary Shelley, Polidori) and doubles as a pun: "Debtors" are the members
who haven't returned a book yet.

## Status

**Working and tested (59 passing unit tests):**
- Full auth flow: registration, login, session cookie
- Multi-club membership: found a club (founder invariant enforced),
  browse and request to join other clubs, founder approves/declines,
  edit a club's description (founder-only, collapsible "About" when
  browsing) — a user can belong to several clubs or use the app with
  zero clubs at all
- Personal Library (always available, no club required) and Common
  Club Library (all books visible to a selected club's members) as
  tabs on one dashboard, with a club switcher directly on the Common
  tab, and empty states for every combination
- Members page: every member of every club you belong to, grouped by
  club, with a read-only view into each member's personal library
- Full book CRUD: add, edit, delete (owner-only, delete blocked by any
  loan history or pending request), view full details and loan history
- **Open Library ISBN lookup**: enter an ISBN (10 or 13 digit, with or
  without hyphens/spaces) on the Add/Edit Book form, click "Look up",
  title and author autofill from Open Library's Books API — never
  overwrites a field the API didn't actually return data for
- Lending via a request/approval workflow, not instant lending: a
  borrower requests a book, the owner approves or declines. Same
  pattern for club membership (join requests, founder approves/declines)
- A unified "Organize" inbox: pending club-join requests and pending
  loan requests in one place
- Design system (custom typography, flat/no-shadow visual language,
  documented design contract) applied throughout

**Deliberately deferred, documented as concepts, not yet built:**
- Title search with multiple results to choose from (needs Open
  Library's Search API, a different endpoint/response shape than the
  ISBN lookup above — a separate piece of work, not an extension of it)
- Posts/feed, reviews (star-or-icon rating + free text per book)
- Reservations ("notify me when this book is returned")
- Lending to non-registered contacts (neighbours, family)
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
  `loan_service`, `group_service`, ...); `services/external/` holds
  thin API clients (Open Library) with no business logic of their own
- `state/` — the only layer bridging Reflex UI and services, itself
  split by bounded context (`AuthState`, `GroupState`, `LibraryState`,
  `OrganizeState`)
- `ui/` — presentation only, imports state, never services or models
  directly; shared components (`book_row`, `book_form`,
  `book_action_bar`) are reused across pages rather than duplicated

Layering is a hard constraint, not a convention: services never import
Reflex, state never touches the ORM directly, and business rules live
exclusively in the service layer.

## Testing

```bash
ruff check .
pytest tests/unit/ -v
```
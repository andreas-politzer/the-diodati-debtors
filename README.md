# The Diodati Debtors

A community library application for book clubs where members catalogue
their own books, lend them to one another, discuss what they're
reading, and build a shared library without giving up personal
ownership.

Built as a learning project during a Data Science & AI bootcamp, The
Diodati Debtors gradually evolved into a fully layered web application
with a strong emphasis on clean architecture, testability, and
domain-driven design principles.

The working title references the Villa Diodati (summer of 1816 —
Byron, Mary Shelley, and Polidori) and doubles as a pun: the
"Debtors" are the members who haven't returned a borrowed book yet.

🔗 **Live demo:** https://the-diodati-debtors-production.up.railway.app/

## Design Principles

This project intentionally favors clean architecture over rapid
feature growth.

Business logic lives entirely in framework-independent services, the
UI remains presentation-only, and every feature is implemented
vertically—from database migration to tests, service layer, state, and
UI—before the next feature begins.

The goal is not only to build a useful application, but also to
demonstrate maintainable software architecture in a real-world Python
project.

## Status

### Implemented (87 passing unit tests)

- Full auth flow: registration, login, session cookie
- Multi-club membership: found a club, browse/join others, founder
  approval, editable club descriptions — works with zero clubs too
- Personal Library, Common Club Library (with an in-dashboard club
  switcher), and My Borrowed Books (currently borrowed + history, with
  overdue/due-soon indicators) as three dashboard tabs
- Members page: every member of every club you belong to, with a
  read-only view into each member's personal library
- Full book CRUD: add, edit, delete (owner-only, blocked by loan
  history), Open Library ISBN lookup and title search with cover
  previews
- Lending via a request/approval workflow (not instant), with a
  unified "Organize" inbox for pending club-join and loan requests
- Communication: Club Feed (posts + threaded comments), built on a
  single Post entity that also supports a Global Board and per-book
  Discussions as different projections of the same data — no separate
  tables per context
- Legal basics: Imprint and Privacy Policy pages
- Design system (custom typography, flat/no-shadow visual language,
  documented design contract) applied throughout
- Deployed and live on Railway (EU West), tested by real external
  users beyond the development session

### Planned

- Global Board and Book Discussions UI (same Post entity as the Club
  Feed — the service layer already supports all three; only the UI is
  missing)
- Reviews (rating + free text per book, using a custom Diodati motif
  instead of traditional star ratings)
- A "My Lent Out Books" dashboard tab (mirror of My Borrowed Books —
  which books I own are currently out, and to whom)
- Search and filtering across books (genre, author, availability)
- Book synopsis/preview on the detail page, sourced from Open Library
- Reservations and lending to non-registered contacts
- Trust score, book-condition tracking, and AI-assisted reminders
- **The Diodati Matchmaker** — a proactive, embeddings-based
  recommendation agent that surfaces newly available books to members
  whose reading history suggests they would enjoy them. Development is
  intentionally staged, beginning with a simple rule-based version
  before introducing embeddings.

See the project documentation (`Implementation Specification.md`,
`Domain Model v2.md`, `Communication Domain Model.md`, and
`AI Matchmaker Vision.md`) for the complete roadmap and architectural
decisions.

## Stack

- [Reflex](https://reflex.dev) — Python-only frontend/backend,
  compiled to React
- MySQL (via Docker) + SQLAlchemy + Alembic
- Design tokens based on the project's design contract
- Hosted on [Railway](https://railway.com)

## Local Setup

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

All demo users share the password `seeddemo123` (see the script output
for email addresses, clubs, and assigned roles).

## Architecture

- `core/` — framework-agnostic configuration, exceptions,
  normalization/time policy, password hashing
- `db/` — SQLAlchemy engine, sessions, declarative base (schema source
  of truth via SQLAlchemy models + Alembic migrations)
- `models/` — SQLAlchemy entities only; no business logic
- `services/` — business logic only, organized by bounded context
  (`auth_service`, `user_service`, `book_service`,
  `loan_service`, `group_service`, `post_service`,
  `comment_service`, ...)
- `state/` — the only layer connecting Reflex UI and services, split
  by bounded context (`AuthState`, `GroupState`, `LibraryState`,
  `OrganizeState`, `PostState`)
- `ui/` — presentation only; imports state, never services or models
  directly; reusable components shared across pages

Layering is a hard constraint.

Services never import Reflex.

State never touches the ORM directly.

Business rules live exclusively inside the service layer.

Services return domain objects and foreign-key IDs rather than
presentation-ready display names. UI-specific enrichment belongs to
the State layer, keeping the separation of responsibilities consistent
across every feature (books, loans, posts, comments, and future
modules).

## Testing

```bash
ruff check .
pytest tests/unit/ -v
```
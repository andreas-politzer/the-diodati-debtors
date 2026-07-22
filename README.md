# The Diodati Debtors

A community library application for book clubs where members catalogue
their own books, lend and borrow within the group, discuss what they're
reading, write reviews, and build a shared library without giving up
personal ownership.

Originally started as a learning project during a Data Science & AI
bootcamp, The Diodati Debtors gradually evolved into a fully layered
web application with a strong emphasis on clean architecture,
testability, and domain-driven design.

The working title references the Villa Diodati (summer of 1816 —
Byron, Mary Shelley, and Polidori) and doubles as a pun: the
"Debtors" are the members who haven't returned a borrowed book yet.

🔗 **Live demo:** https://the-diodati-debtors-production.up.railway.app/

---

## Status

### Working and tested (104 passing unit tests)

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
- Lending via a request/approval workflow, with a unified "Organize"
  inbox for pending club-join and loan requests
- **Communication:** Club Feed and Global Board (posts + threaded
  comments), built on a single Post entity that also supports per-book
  Discussions as a third projection of the same data — with a
  collapsible Community Guidelines panel above every composer
- **Reviews:** owner/borrower-only, one editable review per person per
  book, rated with a recurring owl motif instead of traditional stars
- **Synopsis pipeline:** a book summary can be written manually,
  imported from Open Library (best effort — upstream availability
  varies), or generated with Google Gemini. Every synopsis is clearly
  labelled by source, editable, and removable by the book's owner
- Legal basics: Imprint and Privacy Policy pages, transparently
  documenting every third-party service used (Open Library, Google
  Gemini, Railway)
- Design system (custom typography, flat/no-shadow visual language,
  documented design contract) applied throughout
- **Deployed and live** on Railway (EU West, Amsterdam), tested by real
  external users beyond the development session

### Deliberately deferred (documented concepts, not yet implemented)

- A "My Lent Out Books" dashboard tab (mirror of My Borrowed Books)
- Reservations and lending to non-registered contacts
- Deeper Open Library integration (Work API for more reliable
  descriptions)
- A broader platform vision (public profiles, member discovery,
  private messaging) — intentionally postponed to keep the project
  focused on book clubs rather than becoming a general-purpose social
  network
- Trust score, book-condition tracking, and **The Diodati Matchmaker**
  — a semantic recommendation agent that gradually evolves from
  rule-based recommendations to embedding-powered suggestions

See the project documentation (`Implementation Specification.md`,
`Domain Model v2.md`, `Communication Domain Model.md`,
`Platform Vision.md`, and `AI Matchmaker Vision.md`) for the complete
roadmap and architectural decisions.

---

## Design Philosophy

Although originally built as a learning project, the application
intentionally follows a strict layered architecture.

Business logic lives entirely in framework-independent services,
Reflex remains a presentation layer, and every feature is implemented
vertically—from database migration through tests, service layer,
state, and UI—before the next feature begins.

The objective is not only to build a useful application, but also to
demonstrate maintainable software architecture in a real-world Python
project.

---

## Stack

- [Reflex](https://reflex.dev) — Python-only frontend/backend,
  compiled to React
- MySQL (via Docker) + SQLAlchemy + Alembic
- Open Library for book metadata, covers, and available descriptions
- Google Gemini for AI-generated book summaries
- Design tokens based on the project's design contract
- Hosted on Railway (EU West)

---

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in local DB credentials and API keys
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

---

## Architecture

- `core/` — framework-agnostic configuration, exceptions,
  normalization/time policy, password hashing
- `db/` — SQLAlchemy engine, sessions, declarative base (schema source
  of truth via SQLAlchemy models and Alembic migrations)
- `models/` — SQLAlchemy entities only; no business logic
- `services/` — business logic organized by bounded context
  (`auth_service`, `user_service`, `book_service`,
  `loan_service`, `group_service`, `post_service`,
  `comment_service`, `review_service`, ...)

  External integrations live in `services/external/` as thin API
  clients (Open Library, Google Gemini, future providers). They contain
  no business logic and are responsible only for communicating with
  third-party services.

- `state/` — the only layer connecting Reflex UI and services, split
  by bounded context (`AuthState`, `GroupState`, `LibraryState`,
  `OrganizeState`, `PostState`, `ReviewState`)
- `ui/` — presentation only; imports state, never services or models
  directly; reusable components shared across pages

Layering is a hard constraint.

Services never import Reflex.

State never touches the ORM directly.

Business rules live exclusively inside the service layer.

Services return domain objects and foreign-key IDs rather than
presentation-ready display names. UI-specific enrichment belongs to
the State layer, keeping the separation of responsibilities consistent
across every feature.

---

## Testing

Current test suite:

- **104 passing unit tests**
- Service-layer and domain-rule focused
- Fast execution suitable for continuous development

Run locally:

```bash
ruff check .
pytest tests/unit/ -v
```
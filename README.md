# The Diodati Debtors

A community library application for book clubs where members catalogue
their own books, lend and borrow within the group, discuss what
they're reading, write reviews, and build a shared library without
giving up personal ownership.

Originally started as a learning project during a Data Science & AI
bootcamp, The Diodati Debtors gradually evolved into a fully layered
web application with a strong emphasis on clean architecture,
testability, and domain-driven design.

The working title references the Villa Diodati (summer of 1816 —
Byron, Mary Shelley, and Polidori) and doubles as a pun: the "Debtors"
are the members who haven't returned a borrowed book yet.

🔗 **Live demo:** https://the-diodati-debtors-production.up.railway.app/

## Status

**Working and tested (181 passing unit tests)**

- Full auth flow: registration, login, session cookie
- Multi-club membership: found a club, browse/join others, founder
  approval, editable club descriptions — works with zero clubs too
- Personal Library, Common Club Library (with an in-dashboard club
  switcher), My Borrowed Books, and My Lent-Out Books as four dashboard
  tabs — each shows only what's currently relevant, with full history
  (borrow history, lent-out history grouped by book) on dedicated pages
- Search, genre/availability filters, and sorting across Personal/Common
  Library, plus sorting for Borrowed/Lent-Out books
- **Bulk Import**: upload an existing library as CSV, XLSX, or ODS —
  automatic column detection (synonym-based, no AI needed), duplicate
  detection (against existing books and within the same file),
  progressive disclosure (one-click confirmation when detection is
  confident, a manual mapping table otherwise), and a per-row error
  report — verified against real, deliberately messy spreadsheets
  (Goodreads-style exports, invalid ISBNs, missing fields)
- **My Bookmates**: Club Members and personal Contacts side by side —
  Contacts are private, non-registered borrowers (a grandmother, a
  neighbour) who never touch the app themselves; the owner lends and
  manages the loan directly. Same Trust Signals, same Loan model, no
  duplicated logic — "a Contact is just a mate who isn't a club member
  yet"
- Full book CRUD: add, edit, delete (owner-only, blocked by loan
  history), Open Library ISBN lookup and title search with cover
  previews
- Lending via a request/approval workflow with a real dialog: the
  requester can propose a custom loan period and leave a note (e.g.
  "I'm on vacation for 3 weeks"), the owner can approve or decline with
  a reply message. "Mark returned" also opens a dialog to optionally
  rate the book's condition
- **Organize**: "What needs my attention?" — pending club-join and loan
  requests, split from **Your Requests** (what you've sent, pending vs.
  a collapsible history) — keeps the page from becoming a scroll
  monster as history grows
- **Trust signals**: Reliability and Book Care, two independent
  qualitative signals (never numerical scores, never rankings),
  computed on demand from loan facts, shown in the loan-request dialog
  and on member/contact profiles
- **Community**: Club Feed, Global Board, and per-book Discussions (one
  shared Post entity, different projections), Reviews (owner/borrower-
  only, owl rating instead of stars), and a three-source Synopsis
  pipeline (manual, Open Library, Google Gemini)
- **Ask the Librarian**: semantic, natural-language book search over
  the club's own collection, powered by Gemini text embeddings and
  cosine similarity — with a built-in discretion principle (a match
  outside the requester's visible scope is never revealed by title or
  owner, only hinted at by club name). When nothing matches locally,
  the librarian — voiced in character as Lord Byron, who was actually
  present at Villa Diodati in 1816 — suggests up to three real books
  from the wider world, enriched with genuine cover art via Open
  Library
- A redesigned landing page: a real 1835 Villa Diodati engraving, the
  project's origin story, and a philosophy statement — an invitation
  rather than an immediate login wall
- Legal basics: Imprint and Privacy Policy pages, transparent about
  every third-party service used
- Design system (custom typography, flat/no-shadow visual language,
  documented design contract) applied throughout
- Deployed and live on Railway (EU West, Amsterdam), tested by real
  external users beyond the development session

**Deliberately deferred (documented concepts, not yet implemented)**

- Tags for books, bulk import from existing spreadsheets/exports
- Reservations
- Deeper Open Library integration (Work API for more reliable
  descriptions)
- A broader platform vision (public profiles, member discovery,
  private messaging) — intentionally postponed to keep the project
  focused on book clubs rather than becoming a general-purpose social
  network
- A horizontal navigation redesign (currently a vertical link list)

See the project documentation (`Implementation Specification.md`,
`Domain Model v2.md`, `Communication Domain Model.md`,
`Platform Vision.md`, `Ask the Librarian Vision.md`,
`Bulk Import Domain Model.md`) for the complete roadmap and
architectural decisions.

## Design Philosophy

Although originally built as a learning project, the application
intentionally follows a strict layered architecture.

Business logic lives entirely in framework-independent services,
Reflex remains a presentation layer, and every feature is implemented
vertically — from database migration through tests, service layer,
state, and UI — before the next feature begins.

The objective is not only to build a useful application, but also to
demonstrate maintainable software architecture in a real-world Python
project.

## Stack

- [Reflex](https://reflex.dev) — Python-only frontend/backend, compiled to React
- MySQL (via Docker) + SQLAlchemy + Alembic
- [Open Library](https://openlibrary.org) for book metadata, covers, and available descriptions
- [Google Gemini](https://ai.google.dev) for AI-generated book summaries and text embeddings
- Design tokens based on the project's design contract
- Hosted on [Railway](https://railway.com) (EU West)

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

## Architecture

- `core/` — framework-agnostic configuration, exceptions, normalization/time policy, password hashing
- `db/` — SQLAlchemy engine, sessions, declarative base (schema source of truth via SQLAlchemy models and Alembic migrations)
- `models/` — SQLAlchemy entities only; no business logic
- `services/` — business logic organized by bounded context (`auth_service`, `user_service`, `book_service`, `loan_service`, `group_service`, `contact_service`, `post_service`, `comment_service`, `review_service`, `trust_service`, `librarian_service`, ...)
- External integrations live in `services/external/` as thin API clients (Open Library, Google Gemini). They contain no business logic and are responsible only for communicating with third-party services.
- `state/` — the only layer connecting Reflex UI and services, split by bounded context (`AuthState`, `GroupState`, `LibraryState`, `BookDetailState`, `MemberLibraryState`, `LoanActivityState`, `OrganizeState`, `PostState`, `ReviewState`, `ContactState`, `LibrarianState`), 
- `ui/` — presentation only; imports state, never services or models directly; reusable components shared across pages

Layering is a hard constraint.

Services never import Reflex.

State never touches the ORM directly.

Business rules live exclusively inside the service layer.

Services return domain objects and foreign-key IDs rather than
presentation-ready display names. UI-specific enrichment belongs to
the State layer, keeping the separation of responsibilities consistent
across every feature. Trust signals and book embeddings both follow
the same "store facts, calculate/derive state" principle — nothing is
ever stored pre-computed as the source of truth, and a failure to
refresh a derived artefact (an embedding, a search index) never
breaks the core operation that triggered it.

A Loan's borrower is either a registered User or a personal Contact —
never both, never neither, enforced in the service layer, never as a
database constraint.

## Testing

Current test suite:

- 155 passing unit tests
- Service-layer and domain-rule focused
- Fast execution suitable for continuous development

Run locally:

```bash
ruff check .
pytest tests/unit/ -v
```
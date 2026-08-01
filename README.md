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

**Working and tested (223 passing unit tests)**

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
  detection (against existing books and within the same file, plus
  robust encoding/delimiter handling verified against real, messy
  spreadsheets — Goodreads-style exports, invalid ISBNs, Windows line
  endings), progressive disclosure, and a per-row error report
- **My Bookmates**: Club Members and personal Contacts side by side —
  Contacts are private, non-registered borrowers (a grandmother, a
  neighbour) who never touch the app themselves; the owner lends and
  manages the loan directly
- Full book CRUD: add, edit, delete (owner-only, blocked by loan
  history), Open Library ISBN lookup and title search with cover
  previews, per-book **Borrowing Visibility** (club only / public
  enquiries allowed / not available for borrowing)
- Lending via a request/approval workflow with a real dialog: the
  requester can propose a custom loan period and leave a note, the
  owner can approve or decline with a reply message. "Mark returned"
  also opens a dialog to optionally rate the book's condition
- **Organize**: "What needs my attention?" — pending club-join and loan
  requests, split from **Your Requests**, with prominent, dismissible
  notification banners for decided requests (read-tracked, not just a
  quiet status line)
- **Trust signals**: Reliability and Book Care, two independent
  qualitative signals, computed on demand from loan facts
- **Community**: Club Feed, Global Board, and per-book Discussions,
  Reviews (owl rating instead of stars), and a three-source Synopsis
  pipeline (manual, Open Library, Google Gemini)
- **Personal Profile** (optional, on top of the mandatory account):
  display name, location, bio, favourite genre, a single shared
  visibility level (private / club members only / public), and a
  miniature-portrait-style initials avatar. Visible to fellow club
  members on their Member Detail page when not private
- **Public Borrowing Inquiry**: a book-bound conversation with a user
  outside your clubs, only when the book owner has explicitly allowed
  public enquiries and their profile isn't private — the Librarian
  mediates books, never people
- **Club-Internal Messaging**: free-form conversation between members
  of the same club (no book required) — the shared club membership
  itself is the context that keeps this from becoming a general
  messenger
- **Ask the Librarian**: semantic, natural-language book search over
  the club's own collection (Gemini embeddings + cosine similarity),
  with a discretion principle for matches outside the requester's
  visibility. For everything else, a fast-path/slow-path external
  fallback: short, unambiguous queries go straight to Google Books;
  longer or knowledge-style questions are answered by Gemini and every
  candidate book is hard-verified (title + author) against Google
  Books before ever being shown — the librarian, voiced as Lord Byron,
  never presents a book that hasn't been confirmed to exist, in
  structured results or in his own prose
- A redesigned landing page: a real 1835 Villa Diodati engraving, the
  project's origin story, and a philosophy statement
- Legal basics: Imprint and Privacy Policy pages
- Design system (custom typography, flat/no-shadow visual language)
  applied throughout
- Deployed and live on Railway (EU West, Amsterdam), tested by real
  external users beyond the development session

**Deliberately deferred (documented concepts, not yet implemented)**

- Tags for books
- Reservations
- Deeper Open Library integration (Work API for more reliable
  descriptions)
- Communication page listing of Personal Conversations (Public
  Borrowing Inquiries + Club Conversations), unread-message badges,
  message buttons on Member Detail, Librarian "Send borrowing request"
  button — the remaining wiring for the Personal Messages feature,
  whose full domain model and backend (services, data model) are
  already complete
- A horizontal navigation redesign (currently a vertical link list)

See the project documentation (`Implementation Specification.md`,
`Domain Model v2.md`, `Communication Domain Model.md`,
`Personal Messages Domain Model.md`, `Ask the Librarian Vision.md`,
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
- [Google Books](https://developers.google.com/books) for external book verification (Ask the Librarian's fallback)
- [Google Gemini](https://ai.google.dev) for AI-generated book summaries, text embeddings, and the Librarian's natural-language reasoning
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
- `services/` — business logic organized by bounded context (`auth_service`, `user_service`, `book_service`, `loan_service`, `group_service`, `contact_service`, `post_service`, `comment_service`, `review_service`, `trust_service`, `librarian_service`, `profile_service`, `borrowing_inquiry_service`, `club_conversation_service`, ...)
- External integrations live in `services/external/` as thin API clients (Open Library, Google Books, Google Gemini). They contain no business logic and are responsible only for communicating with third-party services.
- `state/` — the only layer connecting Reflex UI and services, split by bounded context (`AuthState`, `GroupState`, `LibraryState`, `BookDetailState`, `MemberLibraryState`, `LoanActivityState`, `OrganizeState`, `PostState`, `ReviewState`, `ContactState`, `LibrarianState`, `ProfileState`)
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
database constraint. Similarly, communication between two users always
belongs to a specific bibliothekarisch process (a Borrowing Inquiry or
a Club Conversation) rather than existing as a standalone, general-
purpose "conversation" concept — deliberately avoiding the on-ramp to
an unbounded messaging feature.

## Testing

Current test suite:

- 223 passing unit tests
- Service-layer and domain-rule focused
- Fast execution suitable for continuous development

Run locally:

```bash
ruff check .
pytest tests/unit/ -v
```
# The Diodati Debtors

A community library application for book clubs.

Members catalogue their personal libraries, lend books through an
approval workflow, discover what other members own, and build a shared
club library without giving up ownership of their books.

The name references the Villa Diodati (summer of 1816 — Byron, Mary
Shelley and Polidori) while also serving as a small joke: the
"Debtors" are the members who still owe someone a book.

---

## Status

**Working and tested (63 passing unit tests):**

### Authentication & Membership

- User registration, login and session management
- Multi-club membership
- Create clubs (founder invariant enforced)
- Browse public clubs
- Request to join clubs
- Founder approval / decline workflow
- Founder-only editing of club descriptions

### Library Management

- Personal Library (available even without belonging to a club)
- Common Club Library for the currently selected club
- Full book CRUD
- Owner-only editing and deletion
- Delete protection when books have loan history or pending requests
- Detailed book page including loan history

### Open Library Integration

Two independent metadata workflows:

**ISBN Lookup**

- Supports ISBN-10 and ISBN-13
- Accepts hyphens and spaces
- Automatic normalization
- Fetches metadata from the Open Library Books API
- Only updates fields for which metadata actually exists

**Title Search**

- Search Open Library by title
- Multiple candidate editions
- Cover previews via the Open Library Covers API
- User explicitly chooses an edition
- Selected metadata populates the existing BookForm
- Never guesses the intended edition automatically

### Lending Workflow

- Borrow requests instead of instant lending
- Owner approval / decline
- Return workflow
- Loan history
- Request validation and race-condition protection

### Organization

- Unified "Organize" inbox
- Pending club join requests
- Pending loan requests

### Community

- Members grouped by club
- Read-only view into every member's personal library

### Design

- Shared design system
- Flat visual language
- Typography system
- Reusable UI components
- Documented design contract

---

## Planned Features

The current architecture was intentionally designed so the following
features can be added without structural changes:

- Reviews and recommendations
- Reservations ("notify me when available")
- Lending to non-registered contacts
- Genre support
- Book condition
- Trust score
- AI-assisted reminder generation
- Semantic recommendation agent

See the project documentation inside the Vault for the phased roadmap.

---

## Technology Stack

- Reflex
- Python
- SQLAlchemy
- Alembic
- MySQL (Docker)
- Open Library Books API
- Open Library Search API
- Open Library Covers API

---

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env

alembic upgrade head

reflex run
```

Populate demo data:

```bash
python scripts/seed_demo.py
```

Open:

```
http://localhost:3000
```

All demo users share the password `seeddemo123`. Run the seed script
to see the printed list of emails and each user's club/role.

---

## Architecture

The project follows strict layered architecture.

```
UI
↓

State

↓

Services

↓

External Clients / Database
```

### ui/

Presentation only.

Never imports services or ORM models directly.

### state/

The bridge between Reflex and the business layer.

Contains no business rules.

### services/

Framework-independent business logic.

Business rules live exclusively here.

### services/external/

Thin HTTP clients for external APIs (Open Library).

No business logic.

### models/

SQLAlchemy entities only.

### db/

Database configuration, engine, sessions and migrations.

---

## Architectural Principles

- No hardcoded business rules
- Strict separation of UI and business logic
- Small, reusable components
- Framework-independent service layer
- One responsibility per module
- Shared components instead of duplicated pages
- Tests accompany new functionality

Layering is enforced, not merely encouraged.

---

## Testing

```bash
ruff check .

pytest tests/unit/ -v
```



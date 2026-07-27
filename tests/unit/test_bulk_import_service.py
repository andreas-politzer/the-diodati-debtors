"""Tests for bulk_import_service's Column Detector — pure mapping
logic, no file I/O, no database.
"""

from __future__ import annotations

from diodati_debtors.services import bulk_import_service

from diodati_debtors.services import book_service


def test_detects_exact_title_match_as_high_confidence():
    mapping = bulk_import_service.detect_column_mapping(["Title", "Author", "ISBN"])

    assert mapping["title"].header == "Title"
    assert mapping["title"].confidence == "high"


def test_detects_german_synonyms():
    mapping = bulk_import_service.detect_column_mapping(["Buchtitel", "Autor", "ISBN-13"])

    assert mapping["title"].header == "Buchtitel"
    assert mapping["author"].header == "Autor"
    assert mapping["isbn"].header == "ISBN-13"


def test_case_and_whitespace_insensitive():
    mapping = bulk_import_service.detect_column_mapping(["  TITLE  ", "AUTHOR"])

    assert mapping["title"].confidence == "high"
    assert mapping["author"].confidence == "high"


def test_low_confidence_for_partial_match():
    mapping = bulk_import_service.detect_column_mapping(["Book Title (English)"])

    assert mapping["title"].header == "Book Title (English)"
    assert mapping["title"].confidence == "low"


def test_column_order_does_not_matter():
    mapping = bulk_import_service.detect_column_mapping(["ISBN", "Author", "Title"])

    assert mapping["title"].header == "Title"
    assert mapping["author"].header == "Author"
    assert mapping["isbn"].header == "ISBN"


def test_unrecognized_column_returns_none():
    mapping = bulk_import_service.detect_column_mapping(["Random Column", "Another One"])

    assert mapping["title"] is None
    assert mapping["author"] is None
    assert mapping["isbn"] is None


def test_extra_unrelated_columns_are_ignored():
    mapping = bulk_import_service.detect_column_mapping(
        ["Title", "Author", "Purchase Date", "Shelf Location"]
    )

    assert mapping["title"].header == "Title"
    assert mapping["author"].header == "Author"
    assert mapping["isbn"] is None


def test_is_high_confidence_mapping_true_when_title_exact():
    mapping = bulk_import_service.detect_column_mapping(["Title"])

    assert bulk_import_service.is_high_confidence_mapping(mapping) is True


def test_is_high_confidence_mapping_false_when_title_low_confidence():
    mapping = bulk_import_service.detect_column_mapping(["Book Title Thing"])

    assert bulk_import_service.is_high_confidence_mapping(mapping) is False


def test_is_high_confidence_mapping_false_when_no_title_found():
    mapping = bulk_import_service.detect_column_mapping(["Random"])

    assert bulk_import_service.is_high_confidence_mapping(mapping) is False

def _make_user(db, email: str) -> int:
    from diodati_debtors.models.user import User

    with db() as session:
        user = User(email=email, password_hash="x", display_name="User")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def test_find_duplicates_matches_by_isbn(db):
    owner_id = _make_user(db, "owner_import1@example.com")
    book_service.create_book(owner_id=owner_id, title="Frankenstein", isbn="9780141439471")

    mapping = bulk_import_service.detect_column_mapping(["Title", "ISBN"])
    rows = [{"Title": "Frankenstein or The Modern Prometheus", "ISBN": "9780141439471"}]

    candidates = bulk_import_service.find_duplicates(owner_id, rows, mapping)

    assert len(candidates) == 1
    assert candidates[0].match_reason == "isbn"


def test_find_duplicates_matches_by_title_and_author_without_isbn(db):
    owner_id = _make_user(db, "owner_import2@example.com")
    book_service.create_book(owner_id=owner_id, title="Dracula", author="Bram Stoker")

    mapping = bulk_import_service.detect_column_mapping(["Title", "Author"])
    rows = [{"Title": "Dracula", "Author": "Bram Stoker"}]

    candidates = bulk_import_service.find_duplicates(owner_id, rows, mapping)

    assert len(candidates) == 1
    assert candidates[0].match_reason == "title_author"


def test_find_duplicates_ignores_non_matching_rows(db):
    owner_id = _make_user(db, "owner_import3@example.com")
    book_service.create_book(owner_id=owner_id, title="Dracula", author="Bram Stoker")

    mapping = bulk_import_service.detect_column_mapping(["Title", "Author"])
    rows = [{"Title": "The Vampyre", "Author": "John Polidori"}]

    candidates = bulk_import_service.find_duplicates(owner_id, rows, mapping)

    assert candidates == []


def test_find_duplicates_never_matches_across_different_owners(db):
    owner_id = _make_user(db, "owner_import4@example.com")
    other_owner_id = _make_user(db, "owner_import5@example.com")
    book_service.create_book(owner_id=other_owner_id, title="Dracula", author="Bram Stoker")

    mapping = bulk_import_service.detect_column_mapping(["Title", "Author"])
    rows = [{"Title": "Dracula", "Author": "Bram Stoker"}]

    candidates = bulk_import_service.find_duplicates(owner_id, rows, mapping)

    assert candidates == []


def test_find_duplicates_returns_empty_when_no_title_column_detected(db):
    owner_id = _make_user(db, "owner_import6@example.com")

    mapping = bulk_import_service.detect_column_mapping(["Random Column"])
    rows = [{"Random Column": "something"}]

    candidates = bulk_import_service.find_duplicates(owner_id, rows, mapping)

    assert candidates == []


def test_find_duplicates_returns_empty_for_owner_with_no_books(db):
    owner_id = _make_user(db, "owner_import7@example.com")

    mapping = bulk_import_service.detect_column_mapping(["Title"])
    rows = [{"Title": "Anything"}]

    candidates = bulk_import_service.find_duplicates(owner_id, rows, mapping)

    assert candidates == []

def test_import_books_creates_books_from_rows(db):
    owner_id = _make_user(db, "owner_import8@example.com")
    mapping = bulk_import_service.detect_column_mapping(["Title", "Author", "ISBN"])
    rows = [
        {"Title": "Frankenstein", "Author": "Mary Shelley", "ISBN": "9780141439471"},
        {"Title": "Dracula", "Author": "Bram Stoker", "ISBN": ""},
    ]

    report = bulk_import_service.import_books(owner_id, rows, mapping, skip_row_indices=set())

    assert report.total_rows == 2
    assert report.imported_count == 2
    assert report.skipped == []


def test_import_books_skips_rows_missing_title(db):
    owner_id = _make_user(db, "owner_import9@example.com")
    mapping = bulk_import_service.detect_column_mapping(["Title", "Author"])
    rows = [
        {"Title": "", "Author": "Nobody"},
        {"Title": "Real Book", "Author": "Real Author"},
    ]

    report = bulk_import_service.import_books(owner_id, rows, mapping, skip_row_indices=set())

    assert report.imported_count == 1
    assert len(report.skipped) == 1
    assert report.skipped[0].reason == "missing_title"


def test_import_books_skips_rows_marked_as_duplicates(db):
    owner_id = _make_user(db, "owner_import10@example.com")
    mapping = bulk_import_service.detect_column_mapping(["Title"])
    rows = [{"Title": "Book A"}, {"Title": "Book B"}]

    report = bulk_import_service.import_books(owner_id, rows, mapping, skip_row_indices={0})

    assert report.imported_count == 1
    assert len(report.skipped) == 1
    assert report.skipped[0].reason == "duplicate_skipped"
    assert report.skipped[0].row_index == 0


def test_import_books_never_aborts_on_individual_row_failure(db, monkeypatch):
    owner_id = _make_user(db, "owner_import11@example.com")
    mapping = bulk_import_service.detect_column_mapping(["Title"])
    rows = [{"Title": "Good Book"}, {"Title": "Bad Book"}, {"Title": "Another Good Book"}]

    original_create_book = bulk_import_service.create_book

    def flaky_create_book(**kwargs):
        if kwargs.get("title") == "Bad Book":
            raise ValueError("simulated failure")
        return original_create_book(**kwargs)

    monkeypatch.setattr(bulk_import_service, "create_book", flaky_create_book)

    report = bulk_import_service.import_books(owner_id, rows, mapping, skip_row_indices=set())

    assert report.imported_count == 2
    assert len(report.skipped) == 1
    assert report.skipped[0].reason == "creation_failed"


def test_import_books_generates_ai_summaries_when_requested(db, monkeypatch):
    owner_id = _make_user(db, "owner_import12@example.com")
    mapping = bulk_import_service.detect_column_mapping(["Title"])
    rows = [{"Title": "Some Book"}]

    called_with = {}

    def fake_generate_summary(book_id, owner_id):
        called_with["book_id"] = book_id
        called_with["owner_id"] = owner_id

    monkeypatch.setattr(bulk_import_service, "generate_summary_with_ai", fake_generate_summary)

    bulk_import_service.import_books(
        owner_id, rows, mapping, skip_row_indices=set(), generate_ai_summaries=True
    )

    assert called_with.get("owner_id") == owner_id


def test_import_books_summary_failure_does_not_break_import(db, monkeypatch):
    owner_id = _make_user(db, "owner_import13@example.com")
    mapping = bulk_import_service.detect_column_mapping(["Title"])
    rows = [{"Title": "Some Book"}]

    def failing_generate_summary(book_id, owner_id):
        raise ValueError("simulated Gemini outage")

    monkeypatch.setattr(bulk_import_service, "generate_summary_with_ai", failing_generate_summary)

    report = bulk_import_service.import_books(
        owner_id, rows, mapping, skip_row_indices=set(), generate_ai_summaries=True
    )

    assert report.imported_count == 1  # book creation itself still succeeded

def test_bulk_import_service_has_no_reflex_dependency():
    with open(bulk_import_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source
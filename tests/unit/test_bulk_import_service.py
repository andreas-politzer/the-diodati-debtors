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


def test_bulk_import_service_has_no_reflex_dependency():
    with open(bulk_import_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source
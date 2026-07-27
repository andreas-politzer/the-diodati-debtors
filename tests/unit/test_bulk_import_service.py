"""Tests for bulk_import_service's Column Detector — pure mapping
logic, no file I/O, no database.
"""

from __future__ import annotations

from diodati_debtors.services import bulk_import_service


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


def test_bulk_import_service_has_no_reflex_dependency():
    with open(bulk_import_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source
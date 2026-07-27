"""Bulk Import state — the adapter between Reflex UI and
bulk_import_service. Separate bounded context, own state class.

Rows are stored as a dedicated dataclass (values: list[str], same
order as headers) rather than list[dict[str, str]] — Reflex Vars with
nested dict types have caused issues elsewhere in this project; a flat
list inside a dataclass is the safer, already-proven shape (see
LentOutHistoryGroup.periods for precedent).
"""

from __future__ import annotations
from ..core.exceptions import DiodatiError
from dataclasses import dataclass

import reflex as rx

from ..services import bulk_import_service
from .auth_state import AuthState

_UNUSED = "— Unused —"


@dataclass
class ImportRow:
    values: list[str]


@dataclass
class DuplicateChoice:
    row_index: int
    row_title: str
    existing_book_title: str
    match_reason: str
    import_anyway: bool = False


class BulkImportState(rx.State):
    uploaded_filename: str = ""
    headers: list[str] = []
    rows: list[ImportRow] = []

    is_high_confidence: bool = False
    detected_title_header: str = ""
    detected_author_header: str = ""
    detected_isbn_header: str = ""

    selected_title_header: str = ""
    selected_author_header: str = ""
    selected_isbn_header: str = ""

    error_message: str = ""
    info_message: str = ""

    reviewing: bool = False
    duplicate_choices: list[DuplicateChoice] = []
    generate_ai_summaries: bool = False
    report_total: int = 0
    report_imported: int = 0
    report_skipped_count: int = 0

    report_imported_titles: list[str] = []
    report_skipped_titles: list[str] = []

    def _rows_as_dicts(self) -> list[dict[str, str]]:
        """Bridges the Var-safe ImportRow shape back to the plain
        dict[str, str] shape that bulk_import_service functions expect
        — a transient conversion, never itself stored as a State var.
        """
        return [dict(zip(self.headers, row.values)) for row in self.rows]

    async def handle_upload(self, files: list[rx.UploadFile]):
        self.error_message = ""
        self.info_message = ""
        if not files:
            return

        uploaded = files[0]
        content = await uploaded.read()
        filename = uploaded.filename.lstrip("/")

        try:
            headers, raw_rows = bulk_import_service.parse_uploaded_file(filename, content)
        except ValueError as e:
            self.error_message = str(e)
            return

        self.uploaded_filename = filename
        self.headers = headers
        self.rows = [ImportRow(values=[row.get(h, "") for h in headers]) for row in raw_rows]

        mapping = bulk_import_service.detect_column_mapping(headers)
        self.is_high_confidence = bulk_import_service.is_high_confidence_mapping(mapping)

        title_match = mapping.get("title")
        author_match = mapping.get("author")
        isbn_match = mapping.get("isbn")

        self.detected_title_header = title_match.header if title_match else ""
        self.detected_author_header = author_match.header if author_match else ""
        self.detected_isbn_header = isbn_match.header if isbn_match else ""

        self.selected_title_header = self.detected_title_header
        self.selected_author_header = self.detected_author_header or _UNUSED
        self.selected_isbn_header = self.detected_isbn_header or _UNUSED

    def set_selected_title_header(self, value: str):
        self.selected_title_header = value

    def set_selected_author_header(self, value: str):
        self.selected_author_header = value

    def set_selected_isbn_header(self, value: str):
        self.selected_isbn_header = value

    @rx.var
    def header_options(self) -> list[str]:
        return [_UNUSED] + self.headers
    
    def toggle_ai_summaries(self, value: bool):
        self.generate_ai_summaries = value

    def toggle_duplicate_import_anyway(self, row_index: int):
        for choice in self.duplicate_choices:
            if choice.row_index == row_index:
                choice.import_anyway = not choice.import_anyway
        self.duplicate_choices = list(self.duplicate_choices)

    async def confirm_mapping(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in to import books."
            return

        mapping = self._build_mapping()
        rows_as_dicts = self._rows_as_dicts()

        try:
            candidates = bulk_import_service.find_duplicates(
                int(auth_state.current_user_id), rows_as_dicts, mapping
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return

        self.duplicate_choices = [
            DuplicateChoice(
                row_index=c.row_index,
                row_title=c.row_title,
                existing_book_title=c.existing_book_title,
                match_reason=c.match_reason,
                import_anyway=False,
            )
            for c in candidates
        ]
        self.reviewing = True

    def _build_mapping(self):
        from ..services.bulk_import_service import ColumnMatch

        mapping = {}
        if self.selected_title_header and self.selected_title_header != _UNUSED:
            mapping["title"] = ColumnMatch(field="title", header=self.selected_title_header, confidence="high")
        if self.selected_author_header and self.selected_author_header != _UNUSED:
            mapping["author"] = ColumnMatch(field="author", header=self.selected_author_header, confidence="high")
        if self.selected_isbn_header and self.selected_isbn_header != _UNUSED:
            mapping["isbn"] = ColumnMatch(field="isbn", header=self.selected_isbn_header, confidence="high")
        return mapping
    
    def start_new_import(self):
        self.uploaded_filename = ""
        self.headers = []
        self.rows = []
        self.reviewing = False
        self.duplicate_choices = []
        self.report_total = 0
        self.report_imported = 0
        self.report_skipped_count = 0
        self.report_imported_titles = []
        self.report_skipped_titles = []

    async def run_import(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.error_message = "You must be logged in to import books."
            return

        mapping = self._build_mapping()
        rows_as_dicts = self._rows_as_dicts()
        skip_indices = {c.row_index for c in self.duplicate_choices if not c.import_anyway}

        report = bulk_import_service.import_books(
            int(auth_state.current_user_id),
            rows_as_dicts,
            mapping,
            skip_row_indices=skip_indices,
            generate_ai_summaries=self.generate_ai_summaries,
        )

        self.report_total = report.total_rows
        self.report_imported = report.imported_count
        self.report_skipped_count = len(report.skipped)

        imported_titles = []
        for index, row in enumerate(rows_as_dicts):
            if index not in skip_indices and index not in {s.row_index for s in report.skipped}:
                title_header = mapping["title"].header if mapping.get("title") else None
                if title_header:
                    imported_titles.append(row.get(title_header, "").strip())
        self.report_imported_titles = imported_titles
        self.report_skipped_titles = [
            f"{rows_as_dicts[s.row_index].get(mapping['title'].header, '(unknown)') if mapping.get('title') else '(unknown)'} — {s.reason.replace('_', ' ')}"
            for s in report.skipped
        ]

        self.reviewing = False
        self.uploaded_filename = ""
        self.headers = []
        self.rows = []
        self.duplicate_choices = []


__all__ = ["BulkImportState", "ImportRow", "DuplicateChoice"]
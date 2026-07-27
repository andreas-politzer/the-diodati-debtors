"""Import Books — the Bulk Import UI, right column of a future
"Add/Import Books" two-column layout (left: existing manual/ISBN/title
tools, right: this). Currently its own page; will be merged into
add_book.py once both halves are stable.

Header image: Ackermann's "Repository of Arts" — interior of James
Lackington's "Temple of the Muses" bookshop, London, early 19th
century. Lackington was one of the era's most influential booksellers
and, as Lackington, Allen & Co., published the first edition of
Frankenstein (1818) — a direct historical link, not just a themed
illustration.
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.bulk_import_state import BulkImportState


def import_books() -> rx.Component:
    return shell(
        page_title("Import Books"),
        rx.image(src="/images/temple-of-muses.jpg", width="100%", margin_bottom="0.5rem"),
        meta_text(
            "The Temple of the Muses, James Lackington's London bookshop — "
            "once the largest in the world, known for its vast, "
            "systematically catalogued stock. Lackington's firm later "
            "published the first edition of Frankenstein (1818)."
        ),
        divider(),
        body_text(
            "Upload a CSV, XLSX, or ODS file from your existing library "
            "spreadsheet — we'll figure out which columns are which."
        ),
        rx.upload(
            rx.vstack(
                primary_button("Select a file", type="button"),
                body_text("or drag and drop it here"),
            ),
            id="bulk_import_upload",
            border=f"1px dashed {Color.text_soft}",
            padding="2rem",
            border_radius="4px",
        ),
        rx.cond(
            rx.selected_files("bulk_import_upload").length() > 0,
            meta_text(f"Selected: {rx.selected_files('bulk_import_upload')}"),
        ),
        primary_button(
            "Upload",
            on_click=BulkImportState.handle_upload(rx.upload_files(upload_id="bulk_import_upload")),
            type="button",
        ),
        rx.cond(
            BulkImportState.error_message != "",
            rx.text(
                BulkImportState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.cond(
            BulkImportState.uploaded_filename != "",
            rx.fragment(
                divider(),
                meta_text(f"File: {BulkImportState.uploaded_filename} ({BulkImportState.rows.length()} rows)"),
                rx.cond(
                    BulkImportState.is_high_confidence,
                    rx.vstack(
                        body_text(
                            f"Detected: Title → \"{BulkImportState.detected_title_header}\", "
                            f"Author → \"{BulkImportState.detected_author_header}\", "
                            f"ISBN → \"{BulkImportState.detected_isbn_header}\". Looks right?"
                        ),
                        rx.hstack(
                            primary_button("Yes, continue", on_click=BulkImportState.confirm_mapping, type="button"),
                            primary_button("No, adjust mapping", on_click=BulkImportState.show_detailed_mapping, type="button"),
                            primary_button("Cancel", on_click=BulkImportState.cancel_upload, type="button"),
                            spacing="2",
                        ),
                    ),
                    rx.vstack(
                        body_text("Please confirm which column is which:"),
                        rx.hstack(
                            meta_text("Title"),
                            rx.select(
                                BulkImportState.header_options,
                                value=BulkImportState.selected_title_header,
                                on_change=BulkImportState.set_selected_title_header,
                            ),
                        ),
                        rx.hstack(
                            meta_text("Author"),
                            rx.select(
                                BulkImportState.header_options,
                                value=BulkImportState.selected_author_header,
                                on_change=BulkImportState.set_selected_author_header,
                            ),
                        ),
                        rx.hstack(
                            meta_text("ISBN"),
                            rx.select(
                                BulkImportState.header_options,
                                value=BulkImportState.selected_isbn_header,
                                on_change=BulkImportState.set_selected_isbn_header,
                            ),
                        ),
                        primary_button(
                            "Confirm mapping",
                            on_click=BulkImportState.confirm_mapping,
                            type="button",
                            margin_top="0.5rem",
                        ),
                        primary_button(
                            "Cancel",
                            on_click=BulkImportState.cancel_upload,
                            type="button",
                            margin_top="0.5rem",
                        ),
                        spacing="2",
                    ),
                ),
            ),
        ),
        rx.cond(
            BulkImportState.reviewing,
            rx.fragment(
                divider(),
                page_title("Review", font_size="1.3rem"),
                rx.cond(
                    BulkImportState.duplicate_choices.length() > 0,
                    rx.vstack(
                        body_text("These look like books you might already have:"),
                        rx.foreach(
                            BulkImportState.duplicate_choices,
                            lambda choice: rx.hstack(
                                meta_text(f"{choice.row_title} (matches: {choice.existing_book_title})"),
                                rx.checkbox(
                                    "Import anyway",
                                    checked=choice.import_anyway,
                                    on_change=lambda _: BulkImportState.toggle_duplicate_import_anyway(choice.row_index),
                                ),
                                spacing="2",
                            ),
                        ),
                        spacing="2",
                    ),
                    body_text("No duplicates detected."),
                ),
                rx.checkbox(
                    "Also generate AI summaries for imported books (may take longer)",
                    checked=BulkImportState.generate_ai_summaries,
                    on_change=BulkImportState.toggle_ai_summaries,
                    margin_top="1rem",
                ),
                primary_button(
                    "Start Import", on_click=BulkImportState.run_import, type="button", margin_top="1rem"
                ),
            ),
        ),
        rx.cond(
            BulkImportState.report_total > 0,
            rx.fragment(
                divider(),
                page_title("Import complete", font_size="1.3rem"),
                rx.cond(
                    BulkImportState.report_imported_titles.length() > 0,
                    rx.cond(
                        BulkImportState.report_imported_titles.length() <= 20,
                        rx.vstack(
                            body_text(f"Added ({BulkImportState.report_imported}):"),
                            rx.foreach(BulkImportState.report_imported_titles, meta_text),
                            spacing="1",
                        ),
                        body_text(f"Added {BulkImportState.report_imported} books."),
                    ),
                ),
                rx.cond(
                    BulkImportState.report_skipped_titles.length() > 0,
                    rx.cond(
                        BulkImportState.report_skipped_titles.length() <= 20,
                        rx.vstack(
                            body_text(f"Skipped ({BulkImportState.report_skipped_count}):"),
                            rx.foreach(BulkImportState.report_skipped_titles, meta_text),
                            spacing="1",
                            margin_top="1rem",
                        ),
                        body_text(f"Skipped {BulkImportState.report_skipped_count} rows."),
                    ),
                ),
                primary_button(
                    "Import another file",
                    on_click=BulkImportState.start_new_import,
                    type="button",
                    margin_top="1rem",
                ),
            ),
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="56rem",
    )


__all__ = ["import_books"]
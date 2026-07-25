"""Lend to a Contact — the complete lending workflow for personal,
non-registered borrowers (Domain Model, "External Contacts"). Contact
management lives on this same page (reachable from the lending flow,
not a separate top-nav item, per the domain decision).
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.contact_state import ContactState, ContactView
from ...state.library_state import LibraryState


def _contact_card(contact: ContactView) -> rx.Component:
    return card(
        rx.cond(
            ContactState.pending_edit_contact_id == contact.id,
            rx.form(
                rx.vstack(
                    rx.input(
                        placeholder="Name", name="name",
                        value=ContactState.edit_name, on_change=ContactState.set_edit_name,
                    ),
                    rx.input(
                        placeholder="Phone", name="phone",
                        value=ContactState.edit_phone, on_change=ContactState.set_edit_phone,
                    ),
                    rx.input(
                        placeholder="Email", name="email",
                        value=ContactState.edit_email, on_change=ContactState.set_edit_email,
                    ),
                    rx.input(
                        placeholder="Address", name="address",
                        value=ContactState.edit_address, on_change=ContactState.set_edit_address,
                    ),
                    rx.text_area(
                        placeholder="Notes...", name="notes", rows="4",
                        value=ContactState.edit_notes, on_change=ContactState.set_edit_notes,
                    ),
                    rx.hstack(
                        primary_button("Save", on_click=ContactState.submit_edit_contact, type="button"),
                        primary_button("Cancel", on_click=ContactState.cancel_edit_contact, type="button"),
                        spacing="2",
                    ),
                    spacing="2",
                ),
            ),
            rx.fragment(
                page_title(contact.name),
                rx.cond(contact.phone, meta_text(f"Phone: {contact.phone}")),
                rx.cond(contact.email, meta_text(f"Email: {contact.email}")),
                rx.cond(contact.address, meta_text(f"Address: {contact.address}")),
                rx.cond(contact.notes, body_text(contact.notes)),
                meta_text(f"Reliability: {contact.reliability}"),
                meta_text(f"Book Care: {contact.book_care}"),
                primary_button(
                    "Edit", on_click=lambda: ContactState.start_edit_contact(contact), type="button"
                ),
            ),
        ),
        margin_bottom="1rem",
    )


def lend_to_contact() -> rx.Component:
    return shell(
        page_title("Lend to a Contact"),
        rx.cond(
            ContactState.error_message != "",
            rx.text(
                ContactState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.cond(
            ContactState.info_message != "",
            meta_text(ContactState.info_message),
        ),
        rx.form(
            rx.vstack(
                rx.select(LibraryState.lendable_book_options, name="book_id", placeholder="Which book?"),
                rx.select(
                    ContactState.contact_options,
                    name="contact_id",
                    placeholder="Lend to whom?",
                ),
                primary_button("Lend it out", type="submit"),
                spacing="3",
            ),
            on_submit=ContactState.submit_lend_to_contact,
        ),
        divider(),
        page_title("Add a new contact"),
        rx.form(
            rx.vstack(
                rx.input(placeholder="Name", name="name", required=True),
                rx.input(placeholder="Phone (optional)", name="phone"),
                rx.input(placeholder="Email (optional)", name="email"),
                rx.input(placeholder="Address (optional)", name="address"),
                rx.text_area(placeholder="Notes (optional)", name="notes", rows="4"),
                primary_button("Add contact", type="submit"),
                spacing="3",
            ),
            on_submit=ContactState.create_contact,
            reset_on_submit=True,
        ),
        divider(),
        page_title("Your contacts"),
        rx.cond(
            ContactState.contacts.length() > 0,
            rx.foreach(ContactState.contacts, _contact_card),
            body_text("You haven't added any contacts yet."),
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="40rem",
    )


__all__ = ["lend_to_contact"]
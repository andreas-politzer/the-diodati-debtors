"""Contact state — the adapter between Reflex UI and contact_service/
trust_service (contact variant). Separate from LibraryState/GroupState
per the bounded-context discipline; Contacts are a private, club-
independent concept (see Domain Model, "External Contacts").
"""

from __future__ import annotations

from dataclasses import dataclass

import reflex as rx
import datetime as dt

from ..core.exceptions import DiodatiError
from ..services import contact_service, trust_service
from .auth_state import AuthState


@dataclass
class ContactView:
    id: int
    name: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    notes: str | None = None
    reliability: str = ""
    book_care: str = ""


class ContactState(rx.State):
    contacts: list[ContactView] = []
    error_message: str = ""
    info_message: str = ""

    pending_edit_contact_id: int = 0  # 0 == nothing being edited
    edit_name: str = ""
    edit_phone: str = ""
    edit_email: str = ""
    edit_address: str = ""
    edit_notes: str = ""

    async def load_contacts(self):
        self.error_message = ""
        auth_state = await self.get_state(AuthState)
        if not auth_state.is_logged_in:
            self.contacts = []
            return
        try:
            results = contact_service.list_contacts_for_owner(
                int(auth_state.current_user_id)
            )
        except DiodatiError as e:
            self.error_message = str(e)
            return

        views: list[ContactView] = []
        for c in results:
            signals = trust_service.get_trust_signals_for_contact(c.id)
            views.append(
                ContactView(
                    id=c.id,
                    name=c.name,
                    phone=c.phone,
                    email=c.email,
                    address=c.address,
                    notes=c.notes,
                    reliability=signals.reliability,
                    book_care=signals.book_care,
                )
            )
        self.contacts = views

    async def create_contact(self, form_data: dict):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        try:
            contact_service.create_contact(
                owner_id=int(auth_state.current_user_id),
                name=form_data.get("name", ""),
                phone=form_data.get("phone", ""),
                email=form_data.get("email", ""),
                address=form_data.get("address", ""),
                notes=form_data.get("notes", ""),
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.info_message = "Contact added."
            await self.load_contacts()

    def start_edit_contact(self, contact: ContactView):
        self.pending_edit_contact_id = contact.id
        self.edit_name = contact.name
        self.edit_phone = contact.phone or ""
        self.edit_email = contact.email or ""
        self.edit_address = contact.address or ""
        self.edit_notes = contact.notes or ""

    def cancel_edit_contact(self):
        self.pending_edit_contact_id = 0

    def set_edit_name(self, value: str):
        self.edit_name = value

    def set_edit_phone(self, value: str):
        self.edit_phone = value

    def set_edit_email(self, value: str):
        self.edit_email = value

    def set_edit_address(self, value: str):
        self.edit_address = value

    def set_edit_notes(self, value: str):
        self.edit_notes = value

    @rx.var
    def contact_options(self) -> list[str]:
        return [f"{c.id}: {c.name}" for c in self.contacts]

    async def submit_edit_contact(self):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)
        try:
            contact_service.update_contact(
                self.pending_edit_contact_id,
                owner_id=int(auth_state.current_user_id),
                name=self.edit_name,
                phone=self.edit_phone,
                email=self.edit_email,
                address=self.edit_address,
                notes=self.edit_notes,
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.info_message = "Contact updated."
            self.pending_edit_contact_id = 0
            await self.load_contacts()

    async def submit_lend_to_contact(self, form_data: dict):
        self.error_message = ""
        self.info_message = ""
        auth_state = await self.get_state(AuthState)

        try:
            book_id = int(form_data.get("book_id", "").split(":", 1)[0].strip())
            contact_id = int(form_data.get("contact_id", "").split(":", 1)[0].strip())
        except (ValueError, IndexError, AttributeError):
            self.error_message = "Select a book and a contact first."
            return

        try:
            from ..services import loan_service

            loan_service.lend_to_contact(
                book_id=book_id,
                owner_id=int(auth_state.current_user_id),
                contact_id=contact_id,
                due_date=dt.date.today() + dt.timedelta(days=14),
            )
        except DiodatiError as e:
            self.error_message = str(e)
        else:
            self.info_message = "Lent out successfully."


__all__ = ["ContactState", "ContactView"]
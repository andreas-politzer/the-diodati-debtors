"""My Bookmates — Club Members and Contacts side by side (Andy's
architecture law: "People are people, mates are mates. A contact is
just a mate who isn't a club member yet." Unified at the navigation/
mental-model level only — group_service and contact_service remain
completely separate underneath, per Struktur.md.

Club invitations live here too (per the 04.08. UX decision, project
vault) — inviting someone is a relationship between people, not a
separate technical feature, and a dedicated Club Detail page would
violate "one page, one question."
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ...state.club_invitation_state import ClubInvitationState, InvitableGroupOption, PendingInvitationView
from ...state.contact_state import ContactState, ContactView
from ...state.group_state import ClubMembersView, GroupState, MemberEntry


def _member_link(member: MemberEntry) -> rx.Component:
    return rx.cond(
        member.is_current_user,
        rx.hstack(
            rx.text("☞", font_size="1.5rem", line_height="1"),
            body_text("You"),
            meta_text(member.role),
            spacing="2",
            align="center",
            margin_bottom="0.5rem",
        ),
        rx.link(
            rx.hstack(
                rx.text("☞", font_size="1.5rem", line_height="1"),
                body_text(member.display_name),
                meta_text(member.role),
                spacing="2",
                align="center",
            ),
            href=f"/members/{member.user_id}",
            display="block",
            margin_bottom="0.5rem",
        ),
    )


def _club_section(club: ClubMembersView) -> rx.Component:
    return card(
        page_title(club.group_name),
        rx.foreach(club.members, _member_link),
        margin_bottom="1rem",
    )


def _contact_summary(contact: ContactView) -> rx.Component:
    return card(
        body_text(contact.name),
        meta_text(f"Reliability: {contact.reliability}"),
        meta_text(f"Book Care: {contact.book_care}"),
        margin_bottom="1rem",
    )


def _pending_invitation_card(invitation: PendingInvitationView) -> rx.Component:
    return card(
        body_text(invitation.group_name),
        meta_text(invitation.invited_email),
        meta_text("Pending"),
        margin_bottom="0.5rem",
    )

def members() -> rx.Component:
    return shell(
        page_title("My Bookmates"),
        rx.image(src="/images/lord-byron-sepia2.jpg", width="520px", margin_top="0.5rem", margin_bottom="0.5rem"),
        meta_text("Polidori, Mary Shelley, and Byron — the original bookmates, Villa Diodati, 1816."),
        rx.box(height="1.5rem"),
        rx.hstack(
            rx.vstack(
                page_title("Club Members"),
                rx.cond(
                    GroupState.has_groups,
                    rx.foreach(GroupState.club_members, _club_section),
                    rx.fragment(
                        body_text("You're not a member of any club yet."),
                        rx.link("☞ Go to your clubs", href="/clubs", margin_top="0.5rem", display="block"),
                    ),
                ),
                spacing="2",
                width="50%",
            ),
            rx.vstack(
                page_title("Contacts"),
                rx.cond(
                    ContactState.contacts.length() > 0,
                    rx.foreach(ContactState.contacts, _contact_summary),
                    body_text("You haven't added any contacts yet."),
                ),
                rx.link("☞ Manage contacts", href="/lend-to-contact", margin_top="0.5rem", display="block"),
                spacing="2",
                width="50%",
            ),
            spacing="4",
            align="start",
        ),
        divider(),
        rx.cond(
            GroupState.has_groups,
            rx.vstack(
                page_title("Pending Invitations"),
                rx.cond(
                    ClubInvitationState.pending_invitations.length() > 0,
                    rx.foreach(ClubInvitationState.pending_invitations, _pending_invitation_card),
                    body_text("No pending invitations."),
                ),
                rx.cond(
                    ClubInvitationState.error_message != "",
                    meta_text(ClubInvitationState.error_message),
                ),
                rx.cond(
                    ClubInvitationState.info_message != "",
                    meta_text(ClubInvitationState.info_message),
                ),
                page_title("Invite Someone", font_size="1.2rem", margin_top="1rem"),
                rx.form(
                    rx.vstack(
                        rx.input(
                            placeholder="Email address",
                            value=ClubInvitationState.invite_email_draft,
                            on_change=ClubInvitationState.set_invite_email_draft,
                        ),
                        rx.select(
                            ClubInvitationState.invitable_group_names,
                            placeholder="Choose a club",
                            on_change=ClubInvitationState.set_invite_group_name_draft,
                        ),
                        primary_button("Send Invitation", type="submit"),
                        spacing="3",
                    ),
                    on_submit=ClubInvitationState.send_invitation,
                ),
                spacing="3",
                width="100%",
                margin_top="1rem",
            ),
        ),
        divider(),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="48rem",
    )


__all__ = ["members"]
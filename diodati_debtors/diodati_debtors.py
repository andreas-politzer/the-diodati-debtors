"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from .ui.theme import global_style, stylesheets
from .ui.pages.style_preview import style_preview
from .ui.pages.landing import landing
from .ui.pages.login import login
from .ui.pages.register import register
from .ui.pages.clubs import clubs
from .ui.pages.dashboard import dashboard
from .ui.pages.book_detail import book_detail
from .ui.pages.add_book import add_book
from .ui.pages.organize import organize
from .ui.pages.members import members
from .ui.pages.member_detail import member_detail
from .ui.pages.edit_book import edit_book
from .ui.pages.imprint import imprint
from .ui.pages.privacy import privacy
from .ui.pages.club_feed import club_feed
from .ui.pages.global_board import global_board
from .ui.pages.reviews import reviews
from .ui.pages.synopsis import synopsis
from .ui.pages.book_discussion import book_discussion
from .ui.pages.communication import communication
from .ui.pages.club_conversation_detail import club_conversation_detail
from .ui.pages.lent_out_books import lent_out_books
from .ui.pages.lend_to_contact import lend_to_contact
from .ui.pages.manual import manual
from .ui.pages.librarian import librarian
from .ui.pages.import_books import import_books
from .ui.pages.profile import profile
from .ui.pages.personal_messages import personal_messages
from .ui.pages.borrowing_inquiry_detail import borrowing_inquiry_detail
from .state.borrowing_inquiry_detail_state import BorrowingInquiryDetailState
from .state.club_conversation_detail_state import ClubConversationDetailState
from .state.communication_state import CommunicationState
from .state.personal_messages_state import PersonalMessagesState
from .state.profile_state import ProfileState
from .state.bulk_import_state import BulkImportState
from .state.librarian_state import LibrarianState
from .state.review_state import ReviewState
from .state.post_state import PostState
from .state.auth_state import AuthState
from .state.group_state import GroupState
from .state.library_state import LibraryState
from .state.organize_state import OrganizeState
from .state.contact_state import ContactState
from .state.book_detail_state import BookDetailState
from .state.member_library_state import MemberLibraryState
from .state.loan_activity_state import LoanActivityState


class State(rx.State):
    """The app state."""


app = rx.App(
    style=global_style(),
    stylesheets=stylesheets(),
)
app.add_page(
    landing,
    route="/",
    title="The Diodati Debtors | Community Library for Book Clubs",
    description=(
        "A community library application for book clubs. "
        "Catalogue your books, lend and borrow within your club, "
        "and keep track of shared libraries."
    ),
    meta=[
        {
            "property": "og:title",
            "content": "The Diodati Debtors | Community Library for Book Clubs",
        },
        {
            "property": "og:description",
            "content": (
                "A community library application for book clubs. "
                "Catalogue your books, lend and borrow within your club, "
                "and keep track of shared libraries."
            ),
        },
        {
            "property": "og:type",
            "content": "website",
        },
    ],
)
app.add_page(style_preview, route="/style-preview")
app.add_page(login, route="/login", on_load=AuthState.redirect_if_logged_in)
app.add_page(register, route="/register", on_load=AuthState.redirect_if_logged_in)
app.add_page(
    imprint,
    route="/imprint",
    title="Imprint | The Diodati Debtors",
    description="Legal notice and provider information for The Diodati Debtors.",
)

app.add_page(
    privacy,
    route="/privacy",
    title="Privacy Policy | The Diodati Debtors",
    description=(
        "Information about how The Diodati Debtors processes and protects personal data."
    ),
)
app.add_page(
    clubs,
    route="/clubs",
    on_load=[AuthState.check_auth, GroupState.load_all],
)
app.add_page(
    dashboard,
    route="/dashboard",
    on_load=[
        AuthState.check_auth,
        GroupState.load_my_groups,
        LibraryState.load_all,
        LoanActivityState.load_borrowed_books,
        LoanActivityState.load_lent_out_books,
        OrganizeState.load_pending_count,
        CommunicationState.load_hub,
    ],
)
app.add_page(
    global_board,
    route="/board",
    on_load=[AuthState.check_auth, PostState.load_board],
)
app.add_page(
    book_detail,
    route="/book/[book_id]",
    on_load=[AuthState.check_auth, BookDetailState.load_book_detail],
)
app.add_page(
    add_book,
    route="/add-book",
    on_load=[AuthState.check_auth, BookDetailState.reset_form_fields],
)
app.add_page(
    organize,
    route="/organize",
    on_load=[AuthState.check_auth, OrganizeState.load_all],
)
app.add_page(
    member_detail,
    route="/members/[member_id]",
    on_load=[AuthState.check_auth, MemberLibraryState.load_member_library],
)
app.add_page(
    edit_book,
    route="/book/[book_id]/edit",
    on_load=[AuthState.check_auth, BookDetailState.load_book_detail],
)
app.add_page(
    club_feed,
    route="/club-feed",
    on_load=[AuthState.check_auth, PostState.load_club_feed],
)
app.add_page(
    reviews,
    route="/book/[book_id]/reviews",
    on_load=[AuthState.check_auth, ReviewState.load_reviews],
)
app.add_page(
    synopsis,
    route="/book/[book_id]/synopsis",
    on_load=[AuthState.check_auth, BookDetailState.load_book_detail],
)
app.add_page(
    book_discussion,
    route="/book/[book_id]/discussion",
    on_load=[AuthState.check_auth, PostState.load_book_discussion],
)
app.add_page(
    communication,
    route="/communication",
    on_load=[AuthState.check_auth, CommunicationState.load_hub],
)
app.add_page(
    personal_messages,
    route="/personal-messages",
    on_load=[AuthState.check_auth, PersonalMessagesState.load_entries],
)
app.add_page(
    club_conversation_detail,
    route="/club-conversation/[conversation_id]",
    on_load=[AuthState.check_auth, ClubConversationDetailState.load_conversation],
)
app.add_page(
    borrowing_inquiry_detail,
    route="/borrowing-inquiry/[inquiry_id]",
    on_load=[AuthState.check_auth, BorrowingInquiryDetailState.load_inquiry],
)
app.add_page(
    lent_out_books,
    route="/lent-out-history",
    on_load=[AuthState.check_auth, LoanActivityState.load_lent_out_history],
)
app.add_page(
    lend_to_contact,
    route="/lend-to-contact",
    on_load=[AuthState.check_auth, ContactState.load_contacts, LibraryState.load_lendable_book_options],
)
app.add_page(
    members,
    route="/members",
    on_load=[AuthState.check_auth, GroupState.load_my_groups, GroupState.load_members_overview, ContactState.load_contacts],
)
app.add_page(
    manual, route="/manual"
)
app.add_page(
    librarian, route="/librarian", on_load=AuthState.check_auth
)
app.add_page(
    import_books, route="/import-books", on_load=AuthState.check_auth
)
app.add_page(
    profile,
    route="/profile",
    on_load=[AuthState.check_auth, ProfileState.load_profile],
)
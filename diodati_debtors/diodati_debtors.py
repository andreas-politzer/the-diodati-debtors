"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from .ui.theme import global_style, stylesheets
from .ui.pages.style_preview import style_preview
from .ui.pages.landing import landing
from .ui.pages.dashboard import dashboard
from .ui.pages.book_detail import book_detail
from .state.library_state import LibraryState
from .ui.pages.add_book import add_book


class State(rx.State):
    """The app state."""


app = rx.App(
    style=global_style(),
    stylesheets=stylesheets(),
)
app.add_page(landing, route="/")
app.add_page(style_preview, route="/style-preview")
app.add_page(dashboard, route="/dashboard", on_load=LibraryState.load_all)
app.add_page(book_detail, route="/book/[book_id]", on_load=LibraryState.load_book_detail)
app.add_page(add_book, route="/add-book", on_load=LibraryState.load_users)
"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from rxconfig import config
from .ui.theme import global_style, stylesheets
from .ui.pages.style_preview import style_preview
from .ui.pages.dashboard import dashboard
from .state.library_state import LibraryState
from .ui.pages.book_detail import book_detail


class State(rx.State):
    """The app state."""


def index() -> rx.Component:
    # Welcome Page (Index)
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("Welcome to Reflex!", size="9"),
            rx.text(
                "Get started by editing ",
                rx.code(f"{config.app_name}/{config.app_name}.py"),
                size="5",
            ),
            rx.link(
                rx.button("Check out our docs!"),
                href="https://reflex.dev/docs/getting-started/introduction/",
                is_external=True,
            ),
            spacing="5",
            justify="center",
            min_height="85vh",
        ),
    )


app = rx.App(
    style=global_style(),
    stylesheets=stylesheets(),
)
app.add_page(index)
app.add_page(style_preview, route="/style-preview")
app.add_page(dashboard, route="/dashboard", on_load=LibraryState.load_all)
app.add_page(book_detail, route="/book/[book_id]", on_load=LibraryState.load_book_detail)

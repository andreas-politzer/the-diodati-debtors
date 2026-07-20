"""Club selection/creation page.

Bootstrap case (Domain Model v2, project vault): a user with zero
clubs must be able to found the first one — there's no "empty system"
deadlock. Users with existing clubs pick one to make active; everyone
can also browse all clubs and request to join one they're not in yet.
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.group_state import GroupState


def _my_group_row(group: dict) -> rx.Component:
    return card(
        page_title(group["name"]),
        primary_button(
            "Enter this club", on_click=lambda: GroupState.select_group(group["id"])
        ),
        margin_bottom="1rem",
    )


def _available_group_row(group: dict) -> rx.Component:
    return card(
        page_title(group["name"]),
        primary_button(
            "Request to join",
            on_click=lambda: GroupState.send_join_request(group["id"]),
        ),
        margin_bottom="1rem",
    )


def clubs() -> rx.Component:
    return shell(
        page_title("Your clubs"),
        rx.cond(
            GroupState.error_message != "",
            rx.text(
                GroupState.error_message,
                font_family=Font.system,
                font_size=Type.meta,
                color=Color.warning,
            ),
        ),
        rx.cond(
            GroupState.info_message != "",
            meta_text(GroupState.info_message),
        ),
        rx.cond(
            GroupState.has_groups,
            rx.fragment(
                rx.foreach(GroupState.my_groups, _my_group_row),
            ),
            body_text(
                "You're not a member of any club yet. Found the first one, "
                "or browse existing clubs below to request joining."
            ),
        ),
        divider(),
        page_title("Found a new club"),
        rx.form(
            rx.hstack(
                rx.input(placeholder="Club name", name="name", required=True),
                primary_button("Found club", type="submit"),
                spacing="3",
            ),
            on_submit=GroupState.create_group,
            reset_on_submit=True,
        ),
        divider(),
        page_title("Browse clubs"),
        rx.foreach(GroupState.available_groups, _available_group_row),
        max_width="40rem",
    )


__all__ = ["clubs"]
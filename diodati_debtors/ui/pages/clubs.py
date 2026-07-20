"""Clubs page — "How do I discover, join, or create clubs?"

Founding, browsing/joining, and editing a club's description all live
here. Editing is restricted to the founder at the service layer
(NotAuthorizedError if not).

Descriptions can be long (a proper "about us"), so: a multi-line
text_area for editing, and a collapsible <details>/<summary> element
for browsing — no Reflex state needed for the expand/collapse, it's
native HTML behaviour.
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.card import card
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Color, Font, Type
from ...state.group_state import GroupState


def _available_group_row(group: dict) -> rx.Component:
    return card(
        page_title(group["name"]),
        rx.cond(
            group["description"],
            rx.el.details(
                rx.el.summary(
                    "☞ About this club",
                    font_family=Font.system,
                    font_size=Type.meta,
                    cursor="pointer",
                ),
                body_text(group["description"], margin_top="0.5rem"),
            ),
        ),
        primary_button(
            "Request to join",
            on_click=lambda: GroupState.send_join_request(group["id"]),
            margin_top="0.5rem",
        ),
        margin_bottom="1rem",
    )


def clubs() -> rx.Component:
    return shell(
        page_title("Clubs"),
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
        rx.cond(
            GroupState.current_group_id != "",
            rx.fragment(
                page_title("Edit current club's description"),
                meta_text(GroupState.current_group_name),
                rx.form(
                    rx.vstack(
                        rx.text_area(
                            placeholder="Tell people about your club — what you read, why you started it...",
                            name="description",
                            rows="5",
                            width="100%",
                            font_family=Font.body,
                            font_size=Type.body,
                        ),
                        primary_button("Save", type="submit"),
                        spacing="3",
                    ),
                    on_submit=GroupState.update_description,
                ),
                divider(),
            ),
        ),
        page_title("Browse clubs"),
        rx.cond(
            GroupState.available_groups.length() > 0,
            rx.foreach(GroupState.available_groups, _available_group_row),
            body_text("No other clubs to join right now."),
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="40rem",
    )


__all__ = ["clubs"]
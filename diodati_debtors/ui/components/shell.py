"""Reusable page shell.

Every page composes its content inside `shell(...)`. This is the only
place that wires up the Google Fonts preconnect/stylesheet links, so
individual pages never need to think about font loading.

top_right is optional — pages that need something in the top-right
corner (e.g. a Log out link) pass a component; pages that don't
(Landing, Imprint, ...) are unaffected, since it defaults to nothing.
"""

from __future__ import annotations

import reflex as rx

from ..tokens import Border, Color, Font, Space


def shell(
    *children: rx.Component,
    max_width: str = "40rem",
    top_right: rx.Component | None = None,
) -> rx.Component:
    top_right_box = (
        rx.box(top_right, position="absolute", top=Space.md, right=Space.md)
        if top_right is not None
        else rx.fragment()
    )
    support_button = rx.link(
        rx.box(
            "☞ Support",
            background_color=Color.accent,
            color=Color.text,
            font_family=Font.system,
            font_size="0.8rem",
            padding_x=Space.md,
            padding_y=Space.sm,
            border=Border.hairline,
            cursor="pointer",
        ),
        href="https://liberapay.com/andreas_politzer/donate",
        is_external=True,
    )
    return rx.fragment(
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            cross_origin="",
        ),
        rx.box(
            top_right_box,
            rx.box(
                *children,
                max_width=max_width,
                width="100%",
                margin_x="auto",
                padding=Space.lg,
            ),
            rx.box(support_button, position="fixed", bottom=Space.md, right=Space.md, z_index="10"),
            rx.box(
                rx.hstack(
                    rx.link(
                        "Imprint",
                        href="/imprint",
                        font_family=Font.system,
                        font_size="0.7rem",
                        color=Color.text_soft,
                    ),
                    rx.link(
                        "Privacy",
                        href="/privacy",
                        font_family=Font.system,
                        font_size="0.7rem",
                        color=Color.text_soft,
                    ),
                    rx.link(
                        "Manual",
                        href="/manual",
                        font_family=Font.system,
                        font_size="0.7rem",
                        color=Color.text_soft,
                    ),
                    spacing="3",
                    justify="center",
                ),
                width="100%",
                padding_y=Space.md,
            ),
            background_color=Color.background,
            min_height="100vh",
            width="100%",
            position="relative",
        ),
    )


def divider() -> rx.Component:
    """A single hairline divider — the app's only separation device,
    used instead of spacing-via-shadow or nested card borders.
    """
    return rx.box(
        width="100%",
        border_bottom=Border.hairline,
        margin_y=Space.md,
    )


__all__ = ["shell", "divider"]
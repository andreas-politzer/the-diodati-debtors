"""Reusable page shell.

Every page composes its content inside `shell(...)`. This is the only
place that wires up the Google Fonts preconnect/stylesheet links, so
individual pages never need to think about font loading.

Phase 1 scope: layout skeleton only. No navigation logic, no auth
state, no feed/book content — those arrive with the vertical slice in
a later phase.
"""

from __future__ import annotations

import reflex as rx

from ..tokens import Border, Color, Space


def shell(*children: rx.Component, max_width: str = "40rem") -> rx.Component:
    """Wrap page content in the app's consistent outer frame.

    Args:
        children: page content components.
        max_width: content column width; pages needing a wider layout
            (e.g. a book grid) can override this per call.
    """
    return rx.fragment(
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            cross_origin="",
        ),
        rx.box(
            rx.box(
                *children,
                max_width=max_width,
                width="100%",
                margin_x="auto",
                padding=Space.lg,
            ),
            background_color=Color.background,
            min_height="100vh",
            width="100%",
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

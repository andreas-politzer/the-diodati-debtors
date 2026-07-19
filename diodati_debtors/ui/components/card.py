"""Card primitive.

Design Contract rule: cards separate from the background via a hairline
border only — never a drop shadow. Surface colour is a hair lighter
than the page background, which is the only depth cue this design
system uses.
"""

from __future__ import annotations

import reflex as rx

from ..tokens import Border, Color, Radius, Space


def card(*children: rx.Component, **props) -> rx.Component:
    """Generic flat container for grouped content (a book entry, a
    feed post, a form section).
    """
    return rx.box(
        *children,
        background_color=Color.surface,
        border=Border.hairline,
        border_radius=Radius.max,
        padding=Space.md,
        box_shadow="none",
        **props,
    )


__all__ = ["card"]

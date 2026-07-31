"""Miniature-portrait-style avatar — an oval (not a circle), evoking
18th/19th-century portrait miniatures, with the user's initials set
in Lancelot. Initials are computed server-side (in State, via
@rx.var), not here — this component just renders whatever string
it's given.
"""

from __future__ import annotations

import reflex as rx

from ..tokens import Color, Font


def avatar(initials: str, size: str = "36px") -> rx.Component:
    return rx.box(
        rx.text(
            initials,
            font_family=Font.avatar,
            font_size="0.9rem",
            color=Color.background,
        ),
        width=size,
        height="46px",
        border_radius="50%",
        background_color=Color.text,
        display="flex",
        align_items="center",
        justify_content="center",
    )


__all__ = ["avatar"]
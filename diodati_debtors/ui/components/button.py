"""Button primitive.

Design Contract rule: flat, square-ish (max 2px radius). Both buttons
share the same resting appearance (off-black background, cream text) —
the distinction is in the hover colour: primary inverts to Gruenspan,
warning inverts to Ochsenblut. No shadows, no gradients, no size
variants beyond what's needed here in Phase 1.
"""

from __future__ import annotations

import reflex as rx

from ..tokens import Border, Color, Font, Radius, Space, Type


def primary_button(text: str, **props) -> rx.Component:
    """The app's single button style for primary actions
    (e.g. "Lend", "Return", "Submit").
    """
    return rx.button(
        text,
        background_color=Color.text,
        color=Color.accent_contrast,
        font_family=Font.system,
        font_size=Type.meta,
        font_weight="600",
        letter_spacing="0.02em",
        border=Border.hairline,
        border_radius=Radius.max,
        padding_x=Space.md,
        padding_y=Space.sm,
        box_shadow="none",
        cursor="pointer",
        _hover={
            "background_color": Color.accent,
            "color": Color.accent_contrast,
        },
        **props,
    )


def warning_button(text: str, **props) -> rx.Component:
    """Reserved for genuinely destructive or debt-related actions only
    (e.g. "Mark Overdue"). Same resting appearance as `primary_button`
    — the warning only reveals itself on hover, via Ochsenblut, per
    the Design Contract's rule that Ochsenblut is warning-only, never
    decorative in a resting state.
    """
    return rx.button(
        text,
        background_color=Color.text,
        color=Color.accent_contrast,
        font_family=Font.system,
        font_size=Type.meta,
        font_weight="600",
        letter_spacing="0.02em",
        border=Border.hairline,
        border_radius=Radius.max,
        padding_x=Space.md,
        padding_y=Space.sm,
        box_shadow="none",
        cursor="pointer",
        _hover={
            "background_color": Color.warning,
            "color": Color.accent_contrast,
        },
        **props,
    )


__all__ = ["primary_button", "warning_button"]
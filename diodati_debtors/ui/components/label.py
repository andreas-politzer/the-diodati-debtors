"""Label / meta-text primitive.

Design Contract rule: timestamps, nav labels, and other system chrome
use Inter, deliberately breaking the historical body/display faces at
exactly this point — the app should feel modern at the system layer
and considered/period-appropriate at the reading layer.

Also provides the display-numeral primitive intended for things like
the trust-score figure — large Bodoni, used sparingly per the Design
Contract (no gauges, no stars, no progress bars).
"""

from __future__ import annotations

import reflex as rx

from ..tokens import Color, Font, Type


def meta_text(text: str, **props) -> rx.Component:
    """Small system-level text: timestamps, nav labels, field hints."""
    return rx.text(
        text,
        font_family=Font.system,
        font_size=Type.meta,
        color=Color.text_soft,
        **props,
    )


def body_text(text: str, **props) -> rx.Component:
    """Default reading text: feed posts, book descriptions, names."""
    return rx.text(
        text,
        font_family=Font.body,
        font_size=Type.body,
        line_height=Type.line_height_body,
        color=Color.text,
        **props,
    )


def display_numeral(value: str, **props) -> rx.Component:
    """Large Bodoni numeral — reserved for the trust-score figure or
    similarly weighty single values. Never use for body headings; use
    `page_title` for those.
    """
    return rx.text(
        value,
        font_family=Font.display,
        font_size=Type.display_lg,
        font_weight="700",
        letter_spacing=Type.tracking_display,
        line_height=Type.line_height_tight,
        color=Color.text,
        **props,
    )


def page_title(text: str, **props) -> rx.Component:
    """Page-level heading (e.g. "The Library", "The Feed")."""
    return rx.heading(
        text,
        font_family=Font.display,
        font_size=Type.display_sm,
        letter_spacing=Type.tracking_display,
        color=Color.text,
        **props,
    )


__all__ = ["meta_text", "body_text", "display_numeral", "page_title"]

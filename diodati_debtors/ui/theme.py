"""Global styling entry point for Reflex.

Wires the design tokens (ui/tokens.py) into Reflex's `global_style`
mechanism, applied via `rx.App(style=...)`. The Radix theme itself is
configured directly in rxconfig.py's RadixThemesPlugin — passing
`theme=` to rx.App() was deprecated in Reflex 0.9.0.

Phase 1 scope only: no page-specific styling lives here.
"""

from __future__ import annotations

import reflex as rx

from .tokens import Color, Font, Type


def global_style() -> dict:
    """Base style dict applied once via `rx.App(style=...)`.

    Every component-level style override in ui/components/ should be
    additive to this, never contradict it.
    """
    return {
        "background_color": Color.background,
        "color": Color.text,
        "font_family": Font.body,
        "font_size": Type.body,
        "line_height": Type.line_height_body,

        rx.heading: {
            "font_family": Font.display,
            "letter_spacing": Type.tracking_display,
            "font_weight": "700",
            "color": Color.text,
        },

        rx.link: {
            "color": Color.text,
            "text_decoration": "none",
            "_hover": {
                "color": Color.accent,
            },
        },

        # Explicit placeholder colour — the browser default (light
        # grey) was nearly invisible against our Pergament-Creme
        # background, which looked like empty inputs with no
        # placeholder at all rather than a styling choice.
        "::placeholder": {
            "color": Color.text_soft,
            "opacity": "1",
            "font_family": Font.system,
        },

        ".diodati-meta": {
            "font_family": Font.system,
            "font_size": Type.meta,
            "color": Color.text_soft,
        },

        "box_shadow": "none",
    }


def stylesheets() -> list[str]:
    """External stylesheets to load (Google Fonts)."""
    return [Font.google_fonts_href]


__all__ = ["global_style", "stylesheets"]
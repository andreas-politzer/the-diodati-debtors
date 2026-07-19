"""Global styling entry point for Reflex.

Wires the design tokens (ui/tokens.py) into Reflex's two theming
mechanisms:

1. `radix_theme()` — passed to `rx.App(theme=...)`, controls the
   underlying Radix Themes primitives (appearance, accent, radius).
2. `global_style()` — passed to `rx.App(style=...)`, sets base styles
   for raw HTML-level components (body font, headings, links) so we
   don't have to repeat them on every component instance.

Phase 1 scope only: no page-specific styling lives here.
"""

from __future__ import annotations

import reflex as rx

from .tokens import Border, Color, Font, Radius, Type


def radix_theme() -> rx.Component:
    """Radix Themes base configuration.

    Kept intentionally minimal — our palette is fully custom (not one
    of Radix's named accent scales), so most of the actual visual
    identity lives in `global_style()` below, not here. This call
    mainly disables Radix defaults that would fight our flat,
    shadow-free design (e.g. default radius, default light/dark accent
    ramps).
    """
    return rx.theme(
        appearance="light",
        has_background=True,
        radius="none",
        scaling="100%",
    )


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

        # Headings default to the display face — component primitives
        # (Card titles, page titles) opt into this automatically.
        rx.heading: {
            "font_family": Font.display,
            "letter_spacing": Type.tracking_display,
            "font_weight": "700",
            "color": Color.text,
        },

        # Links styled flat, no underline-on-default, accent on hover —
        # matches the button hover-inversion rule from the Design Contract.
        rx.link: {
            "color": Color.text,
            "text_decoration": "none",
            "_hover": {
                "color": Color.accent,
            },
        },

        # System-level chrome: anything explicitly tagged as "meta" text
        # (timestamps, nav labels) should use Inter, never the body serif.
        ".diodati-meta": {
            "font_family": Font.system,
            "font_size": Type.meta,
            "color": Color.text_soft,
        },

        # Global replacement for shadows: everything separates via
        # hairline borders instead. Any component that still emits a
        # default browser/Radix shadow gets it stripped here.
        "box_shadow": "none",
    }


def stylesheets() -> list[str]:
    """External stylesheets to load (Google Fonts)."""
    return [Font.google_fonts_href]


__all__ = ["radix_theme", "global_style", "stylesheets"]

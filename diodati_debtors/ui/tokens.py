"""Design tokens for The Diodati Debtors.

Single source of truth for the visual language, translated from the
finalised Design Contract (see Design.md in the project vault). No
component may hardcode a raw hex value, font name, or spacing number —
everything references these constants, so a future palette or
typography change happens in exactly one place.

Phase 1 scope: tokens, typography, spacing, borders, shell + primitives.
No Goya/Easter-egg assets, no drop-caps, no conditional quill behaviour,
no cover filters — deferred until the first full vertical slice works
end-to-end (see Implementation Specification.md, Decorative-Assets-Gate).
"""

from __future__ import annotations


class Color:
    """Flat colour palette. Exactly one accent per semantic role."""

    background = "#F2EFE9"  # Pergament-Creme
    surface = "#FAF8F5"  # Karten/Container
    text = "#1A1918"  # Warmes Off-Black, primary text
    text_soft = "#23211F"  # Off-Black, secondary use
    border = "#DCD8D0"  # 1px dividers, replaces drop-shadows entirely

    accent = "#3A6053"  # Gruenspan — primary interactive accent
    accent_contrast = "#FAF8F5"  # Text/icon colour on top of accent

    warning = "#6B2727"  # Ochsenblut — warnings / overdue / debt only


class Font:
    """Three-role type system. See Design Contract for the reasoning:
    Bodoni only at display size, Baskerville for reading, Inter for
    neutral system chrome (timestamps, nav, button labels).
    """

    display = "'Bodoni Moda', serif"
    body = "'Libre Baskerville', 'EB Garamond', serif"
    system = "'Inter', sans-serif"

    # Google Fonts stylesheet URL, wired into the app via head_components
    # in the shell (see ui/components/shell.py). Weights kept minimal —
    # this is a flat, restrained system, not a decorative one.
    google_fonts_href = (
        "https://fonts.googleapis.com/css2"
        "?family=Bodoni+Moda:wght@500;700"
        "&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400"
        "&family=Inter:wght@400;500;600"
        "&display=swap"
    )


class Type:
    """Type scale. Display sizes are intentionally large and sparse —
    Bodoni's stroke contrast degrades at small sizes, so it must never
    be used below `display_sm`.
    """

    display_lg = "4rem"  # trust-score numerals, hero titles
    display_sm = "2rem"  # page titles ("The Feed", "The Library")
    body = "1rem"
    body_sm = "0.875rem"
    meta = "0.75rem"  # timestamps, nav labels, button text

    line_height_body = "1.6"
    line_height_tight = "1.2"

    tracking_display = "0.04em"


class Space:
    """Spacing scale, used for padding/margin/gap everywhere."""

    xs = "0.25rem"
    sm = "0.5rem"
    md = "1rem"
    lg = "1.5rem"
    xl = "2.5rem"
    xxl = "4rem"


class Radius:
    """Flat design: radius is essentially off. Never exceed `max`."""

    none = "0px"
    max = "2px"


class Border:
    """All border styles used in the app. No component constructs a
    border string inline — everything references a named token here,
    so `Border` stays the single source of truth for every border,
    including semantic ones like warnings.
    """

    hairline = f"1px solid {Color.border}"
    warning = f"1px solid {Color.warning}"


__all__ = ["Color", "Font", "Type", "Space", "Radius", "Border"]

"""Communication hub — links to the two book-independent Post
projections (Club Feed, Global Board). Book Discussion is
deliberately NOT here — it only makes sense attached to a specific
book, so it stays linked from the Book Detail page instead.

Header image: a real manuscript page from Frankenstein (Mary Shelley,
MS. Abinger c. 56), via the Shelley-Godwin Archive under CC BY-NC-SA
2.0 — a one-off page header, not a recurring decorative motif (see the
Villa Diodati landing-page image for the same precedent).
"""

from __future__ import annotations

import reflex as rx

from ..components.label import meta_text, page_title
from ..components.shell import shell


def communication() -> rx.Component:
    return shell(
        page_title("Communication", margin_bottom="1rem"),
        
        rx.link("☞ Club Feed", href="/club-feed", margin_top="1rem", margin_bottom="0.5rem", display="block"),
        rx.link("☞ Global Board", href="/board", margin_bottom="0.5rem", display="block"),
        rx.image(src="/images/frankenstein_manuscript.png", width="100%", margin_bottom="0.5rem"),
        meta_text(
            'Shelley, M. W. "Frankenstein, Volume I", in The Shelley-Godwin '
            "Archive, MS. Abinger c. 56, 4r. CC BY-NC-SA 2.0."
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="32rem",
    )


__all__ = ["communication"]
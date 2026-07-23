"""Landing page — public, no login required.

Hero image is a real 1835 engraving (Meyer's Universum, Bd. 2,
Bibliographisches Institut, Hildburghausen) depicting Villa Diodati —
authentic period imagery, not an AI-generated pastiche. Given a
caption and prominent placement, unlike the recurring in-app
Easter-egg motifs (owl, quill, zoomorphs), which stay small and rare.

Deliberately no Blackletter/Gothic fonts — Bodoni Moda carries the
literary weight here, consistent with the rest of the design system.
Buttons appear only after the story/overview, inviting rather than
demanding authentication immediately.
"""

from __future__ import annotations

import reflex as rx

from ..components.button import primary_button
from ..components.label import body_text, meta_text, page_title
from ..components.shell import divider, shell
from ..tokens import Font, Type


def landing() -> rx.Component:
    return shell(
        page_title("The Diodati Debtors"),
        body_text("A quiet place where books travel from one reader to the next."),
        rx.image(src="/images/villa-diodati.jpg", width="100%", margin_y="1rem"),
        meta_text("Villa Diodati, Lake Geneva — engraving from Meyer's Universum, 1835."),
        divider(),
        body_text(
            "In the summer of 1816, Lord Byron, Mary Shelley, Percy Shelley "
            "and John Polidori gathered at Villa Diodati on Lake Geneva. "
            "Their conversations inspired stories that would shape Gothic "
            "literature for generations."
        ),
        body_text(
            "The Diodati Debtors borrows its name from that house — and "
            "from every reader who has ever forgotten to return a "
            "borrowed book."
        ),
        divider(),
        page_title("What is The Diodati Debtors?"),
        body_text(
            "Build a shared community library without giving up ownership "
            "of your books."
        ),
        body_text("• Catalogue your personal library."),
        body_text("• Lend and borrow within trusted book clubs."),
        body_text("• Discuss, review and discover books together."),
        divider(),
        rx.link(primary_button("Enter Library"), href="/login"),
        rx.link(
            "☞ Create an account",
            href="/register",
            margin_top="0.5rem",
            margin_bottom="1.5rem",
            display="block",
        ),
        divider(),
        meta_text("No advertisements."),
        meta_text("No engagement algorithms."),
        meta_text("No follower counts."),
        meta_text("Just readers and books."),
        max_width="60rem",
    )


__all__ = ["landing"]
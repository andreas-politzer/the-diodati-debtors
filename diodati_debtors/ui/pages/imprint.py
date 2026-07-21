"""Imprint (Impressum) — required under German TMG § 5 for any
publicly reachable service, even a small demo project once it's
actively promoted (e.g. via LinkedIn), not just purely private use.

Andy: fill in your actual name/address/contact below before relying
on this page — placeholders are marked clearly.
"""

from __future__ import annotations

import reflex as rx

from ..components.label import body_text, page_title
from ..components.shell import shell


def imprint() -> rx.Component:
    return shell(
        page_title("Imprint"),
        body_text("Information according to § 5 TMG (German Telemedia Act):"),
        body_text("Andreas Politzer"),
        body_text("Martinistraße 16"),
        body_text("20251, Hamburg"),
        body_text("Germany"),
        body_text("Email: andreas.politzer@ik.me"),
        body_text(
            "This is a private, non-commercial software project developed as part of a Data Science & AI bootcamp. "
            "It is operated solely for educational and demonstration purposes and is not conducted as a commercial business."
        ),
        rx.hstack(
            rx.link(
                "GitHub",
                href="https://github.com/andreas-politzer/the-diodati-debtors",
                is_external=True,
            ),
            rx.link(
                "LinkedIn",
                href="https://www.linkedin.com/in/andreas-politzer/",
                is_external=True,
            ),
            spacing="3",
            margin_top="1rem",
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="32rem",
    )


__all__ = ["imprint"]
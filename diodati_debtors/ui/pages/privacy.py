"""Privacy Policy (Datenschutzerklärung) — covers what personal data
this app stores, why, where, and user rights under the GDPR. Written
for a small demo/student project — not a substitute for proper legal
review if this ever becomes a real, larger-scale service.
"""

from __future__ import annotations

import reflex as rx

from ..components.label import body_text, page_title
from ..components.shell import divider, shell


def privacy() -> rx.Component:
    return shell(
        page_title("Privacy Policy"),
        body_text(
            "This page explains what personal data The Diodati Debtors "
            "collects, why, and your rights regarding it."
        ),
        divider(),
        page_title("What we store"),
        body_text(
            "Email address, a securely hashed password (never the "
            "plain-text password itself), your chosen display name, and "
            "the books/loans/club memberships you create while using "
            "the app."
        ),
        divider(),
        page_title("Why we store it"),
        body_text(
            "This data is necessary to provide the core service: "
            "identifying your account, showing your library, and "
            "managing lending between members. There is no advertising "
            "and no data is sold or shared for marketing purposes."
        ),
        divider(),
        page_title("Where it's hosted"),
        body_text(
            "The application and its database are hosted on Railway "
            "(railway.com), in the EU West (Amsterdam, Netherlands) "
            "region."
        ),
        divider(),
        page_title("Third-party services"),
        body_text(
            "When you use the ISBN lookup or title search features, the "
            "ISBN or search text you enter is sent to the Open Library "
            "API (openlibrary.org, operated by the Internet Archive) to "
            "retrieve book metadata. No account or personal data is "
            "sent as part of these requests."
        ),
        divider(),
        page_title("Cookies"),
        body_text(
            "We use strictly functional cookies only — to keep you "
            "logged in and remember which club you're currently "
            "viewing. No tracking or advertising cookies are used."
        ),
        divider(),
        page_title("Your rights"),
        body_text(
            "Under the GDPR, you can request access to, correction of, "
            "or deletion of your personal data at any time. Contact us "
            "using the email address on the Imprint page."
        ),
        rx.link("☞ Back to library", href="/dashboard", margin_top="1rem", display="block"),
        max_width="32rem",
    )


__all__ = ["privacy"]
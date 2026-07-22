"""Privacy Policy (Datenschutzerklärung) — covers what personal data
this app stores, why, where, and user rights under the GDPR. Written
for a small educational/demo project. It is not legal advice and should
be reviewed before operating a larger public service.
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
            "collects, why it is processed, and your rights under the "
            "General Data Protection Regulation (GDPR)."
        ),
        divider(),
        page_title("What we store"),
        body_text(
            "We store your email address, a securely hashed password "
            "(never your plain-text password), your chosen display "
            "name, and any content you voluntarily create while using "
            "the application, such as books, loans, club memberships, "
            "and other library-related data."
        ),
        divider(),
        page_title("Why we store it"),
        body_text(
            "This information is processed solely to provide the "
            "functionality of the application, including user "
            "authentication, personal libraries, club membership, and "
            "book lending between members. We do not display "
            "advertising and we do not sell or share personal data for "
            "marketing purposes."
        ),
        divider(),
        page_title("Legal basis"),
        body_text(
            "Personal data is processed under Article 6(1)(b) GDPR, as "
            "it is necessary to provide the user account and lending "
            "functionality requested by the user."
        ),
        divider(),
        page_title("Where it's hosted"),
        body_text(
            "The application is hosted on Railway. The production "
            "database is hosted in Railway's EU West region "
            "(Amsterdam, Netherlands)."
        ),
        divider(),
        page_title("Third-party services"),
        body_text(
            "When you use the ISBN lookup or title search features, "
            "only the ISBN or search query you enter is transmitted to "
            "the Open Library API (operated by the Internet Archive) "
            "to retrieve book metadata. No user account information, "
            "authentication data, or personal profile information is "
            "included in these requests. Requests to Open Library are "
            "subject to Open Library's own privacy practices."
        ),
        body_text(
            "When you use the AI-generated summary feature, the book's "
            "title and author are sent to Google's Gemini API to "
            "generate a short synopsis. No account or personal data is "
            "sent as part of these requests. This feature is optional "
            "and only triggered when a book's owner explicitly requests it."
        ),
        divider(),
        page_title("Cookies"),
        body_text(
            "We use only technically necessary cookies. They are used "
            "to keep you signed in and remember which club you are "
            "currently viewing. No tracking or advertising cookies are "
            "used."
        ),
        divider(),
        page_title("Your rights"),
        body_text(
            "Under the GDPR, you have the right to request access to, "
            "correction of, or deletion of your personal data. If you "
            "would like your account or associated data to be deleted, "
            "please contact us using the email address provided on the "
            "Imprint page."
        ),
        rx.link(
            "☞ Back to library",
            href="/dashboard",
            margin_top="1rem",
            display="block",
        ),
        max_width="32rem",
    )


__all__ = ["privacy"]
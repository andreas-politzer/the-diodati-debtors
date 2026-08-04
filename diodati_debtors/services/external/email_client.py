"""Thin HTTP client for Brevo's transactional email API. No business
logic here, per the Service Contract — just sending a single email,
given a recipient, subject, and body.
"""

from __future__ import annotations

import requests

from ...core.config import settings

_TIMEOUT_SECONDS = 10
_BASE_URL = "https://api.brevo.com/v3/smtp/email"


def send_email(to_email: str, subject: str, html_body: str) -> None:
    """Sends a single transactional email via Brevo.

    Raises requests.RequestException on network/HTTP failure — not
    translated into a domain exception here, per the Service Contract
    (infrastructure failures stay infrastructure failures).
    """
    response = requests.post(
        _BASE_URL,
        headers={
            "api-key": settings.brevo_api_key,
            "Content-Type": "application/json",
        },
        json={
            "sender": {"email": settings.email_sender_address, "name": "The Diodati Debtors"},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_body,
        },
        timeout=(3.0, _TIMEOUT_SECONDS),
    )
    response.raise_for_status()


__all__ = ["send_email"]
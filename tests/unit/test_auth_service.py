"""Tests for auth_service: registration, login, email normalization,
password validation, and the deliberately generic invalid-credentials
behavior (never reveals whether an email exists).
"""

from __future__ import annotations

import pytest

from diodati_debtors.core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidRegistrationDataError,
)
from diodati_debtors.services import auth_service


def test_register_succeeds(db):
    result = auth_service.register(
        email="Reader@Example.com", password="hunter22", display_name="Liane"
    )

    assert result.email == "reader@example.com"  # normalized: lowercase
    assert result.display_name == "Liane"


def test_register_rejects_duplicate_email(db):
    auth_service.register(email="dup@example.com", password="hunter22", display_name="A")

    with pytest.raises(EmailAlreadyRegisteredError):
        auth_service.register(email="dup@example.com", password="hunter22", display_name="B")


def test_register_treats_email_case_as_duplicate(db):
    auth_service.register(email="case@example.com", password="hunter22", display_name="A")

    with pytest.raises(EmailAlreadyRegisteredError):
        auth_service.register(email="CASE@EXAMPLE.COM", password="hunter22", display_name="B")


def test_register_rejects_blank_display_name(db):
    with pytest.raises(InvalidRegistrationDataError):
        auth_service.register(email="blank@example.com", password="hunter22", display_name="   ")


def test_register_rejects_short_password(db):
    with pytest.raises(InvalidRegistrationDataError):
        auth_service.register(email="short@example.com", password="abc", display_name="A")


def test_register_rejects_invalid_email(db):
    with pytest.raises(InvalidRegistrationDataError):
        auth_service.register(email="not-an-email", password="hunter22", display_name="A")


def test_login_succeeds_with_correct_credentials(db):
    auth_service.register(email="login@example.com", password="correcthorse", display_name="A")

    result = auth_service.login(email="login@example.com", password="correcthorse")

    assert result.email == "login@example.com"


def test_login_rejects_wrong_password(db):
    auth_service.register(email="wrongpw@example.com", password="correcthorse", display_name="A")

    with pytest.raises(InvalidCredentialsError):
        auth_service.login(email="wrongpw@example.com", password="incorrecthorse")


def test_login_rejects_unknown_email(db):
    with pytest.raises(InvalidCredentialsError):
        auth_service.login(email="doesnotexist@example.com", password="whatever1")


def test_auth_service_has_no_reflex_dependency():
    """Static source check, per the Architecture Contract."""
    with open(auth_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source
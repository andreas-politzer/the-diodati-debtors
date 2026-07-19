"""Domain-specific exceptions raised by the service layer.

Per the Service Contract (Implementation Specification.md), the
service layer is the only layer allowed to enforce business rules. When
a rule is violated, a service raises one of these rather than returning
an ambiguous boolean or None — callers (state/) catch these explicitly
and translate them into user-facing messages. Services never catch a
broad `Exception` to swallow a business-rule violation.

These exceptions are part of the public service API. Once introduced,
never replace them with a generic ValueError, RuntimeError, or plain
Exception in future services. Infrastructure failures (database,
network, etc.) are never represented as domain exceptions — they
propagate as their own natural exception types.
"""

from __future__ import annotations


class DiodatiError(Exception):
    """Base class for all domain-specific errors in this application."""


class NotFoundError(DiodatiError):
    """Raised when a requested entity does not exist."""


class BusinessRuleViolation(DiodatiError):
    """Raised when an operation would violate a documented business rule."""


class BookAlreadyOnLoanError(BusinessRuleViolation):
    """Raised when attempting to lend a book that already has an
    active loan (return_date IS NULL).
    """


class InvalidLoanDatesError(BusinessRuleViolation):
    """Raised when due_date < loan_date, or return_date < loan_date."""


class LoanAlreadyReturnedError(BusinessRuleViolation):
    """Raised when attempting to return a loan that already has a
    return_date — loan history is immutable, not silently overwritable.
    """


__all__ = [
    "DiodatiError",
    "NotFoundError",
    "BusinessRuleViolation",
    "BookAlreadyOnLoanError",
    "InvalidLoanDatesError",
    "LoanAlreadyReturnedError",
]
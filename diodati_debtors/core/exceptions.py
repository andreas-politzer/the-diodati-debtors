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


class InvalidBookDataError(BusinessRuleViolation):
    """Raised when book data fails a business-level validation rule
    (e.g. a blank title) — distinct from a database NOT NULL failure.
    """


class InvalidRegistrationDataError(BusinessRuleViolation):
    """Raised when registration data fails validation (blank fields,
    invalid email format, password too short).
    """


class EmailAlreadyRegisteredError(BusinessRuleViolation):
    """Raised when attempting to register with an email already in use."""


class InvalidCredentialsError(BusinessRuleViolation):
    """Raised on login failure. Deliberately generic — never reveals
    whether the email exists or the password was wrong, to avoid
    leaking account existence.
    """


class InvalidGroupDataError(BusinessRuleViolation):
    """Raised when group data fails validation (e.g. a blank name)."""


class AlreadyGroupMemberError(BusinessRuleViolation):
    """Raised when a user who is already a member requests to join
    the same group again.
    """


class DuplicateJoinRequestError(BusinessRuleViolation):
    """Raised when a user already has a pending JoinRequest for a
    group and submits another one.
    """


class RequestNotPendingError(BusinessRuleViolation):
    """Raised when attempting to approve/decline a JoinRequest or
    LoanRequest that is not in PENDING status — approved/declined
    requests are immutable history, not re-reviewable.
    """

class NotAuthorizedError(BusinessRuleViolation):
    """Raised when a user attempts an action requiring a group role
    they don't have — e.g. approving a JoinRequest without being that
    group's founder/admin.
    """

class CannotRequestOwnBookError(BusinessRuleViolation):
    """Raised when a user attempts to request their own book."""


class DuplicateLoanRequestError(BusinessRuleViolation):
    """Raised when the same user already has a pending LoanRequest for
    the same book.
    """

class BookHasLoanHistoryError(BusinessRuleViolation):
    """Raised when attempting to delete a book that has any loan
    record (active or historical). Loan has no cascade from Book
    (immutable history principle) — deleting would orphan those rows.
    """


class BookHasPendingLoanRequestError(BusinessRuleViolation):
    """Raised when attempting to delete a book that has a pending
    loan request — the request should be declined/cancelled first.
    """

class IsbnNotFoundError(BusinessRuleViolation):
    """Raised when an ISBN has no matching record in Open Library.
    Network/timeout failures are NOT wrapped here — they propagate as
    their own natural exception (e.g. requests.RequestException), per
    the Service Contract's rule that infrastructure failures are never
    represented as domain exceptions.
    """

class InvalidSearchQueryError(BusinessRuleViolation):
    """Raised when a title search query is blank. An empty results
    list (genuinely no matches found) is NOT an exception — that's a
    normal, displayable outcome, not a business-rule violation.
    """

class InvalidPostDataError(BusinessRuleViolation):
    """Raised when post/comment content is blank."""


class NotAuthorizedToPostError(BusinessRuleViolation):
    """Raised when a user attempts to post somewhere they can't see —
    a club feed they're not a member of, or a book they can't view.
    """


__all__ = [
    "DiodatiError",
    "NotFoundError",
    "BusinessRuleViolation",
    "BookAlreadyOnLoanError",
    "InvalidLoanDatesError",
    "LoanAlreadyReturnedError",
    "InvalidBookDataError",
    "InvalidRegistrationDataError",
    "EmailAlreadyRegisteredError",
    "InvalidCredentialsError",
    "InvalidGroupDataError",
    "AlreadyGroupMemberError",
    "DuplicateJoinRequestError",
    "RequestNotPendingError",
    "NotAuthorizedError",
    "CannotRequestOwnBookError",
    "DuplicateLoanRequestError",
    "BookHasLoanHistoryError",
    "BookHasPendingLoanRequestError",
    "IsbnNotFoundError",
    "InvalidSearchQueryError",
    "InvalidPostDataError",
    "NotAuthorizedToPostError",
]
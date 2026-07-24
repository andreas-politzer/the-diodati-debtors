"""Trust service — Reliability and Book Care, two independent
qualitative signals (see Trust Signals Domain Design, project vault).

Nothing here is ever stored — scores are always computed on demand
from facts already in the database (Loan.due_date, return_date,
condition_rating), per the project's "store facts, calculate state"
principle (same as Book.is_on_loan).

Never expose numerical values to the UI — only the category strings.
No traffic-light colors, no rankings, no leaderboards.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy import select

from ..db.session import get_session
from ..models.enums import ConditionRating
from ..models.loan import Loan

_RELIABILITY_POINTS_ON_TIME = 100
_RELIABILITY_POINTS_1_TO_3_DAYS = 80
_RELIABILITY_POINTS_4_TO_7_DAYS = 50
_RELIABILITY_POINTS_OVER_7_DAYS = 20

_BOOK_CARE_POINTS = {
    ConditionRating.BETTER_THAN_BEFORE: 100,
    ConditionRating.SAME_CONDITION: 100,
    ConditionRating.SLIGHTLY_WORSE: 50,
    ConditionRating.SIGNIFICANTLY_WORSE: 10,
}

_CATEGORY_THRESHOLDS = [
    (90, "Excellent"),
    (70, "Good"),
    (50, "Fair"),
]
_CATEGORY_BELOW_THRESHOLD = "Needs Improvement"


@dataclass(frozen=True)
class TrustSignals:
    reliability: str
    book_care: str

    def to_dict(self) -> dict:
        return asdict(self)


def _category_for_score(score: float) -> str:
    for threshold, label in _CATEGORY_THRESHOLDS:
        if score >= threshold:
            return label
    return _CATEGORY_BELOW_THRESHOLD


def _reliability_points(loan: Loan) -> int:
    days_late = (loan.return_date - loan.due_date).days
    if days_late <= 0:
        return _RELIABILITY_POINTS_ON_TIME
    if days_late <= 3:
        return _RELIABILITY_POINTS_1_TO_3_DAYS
    if days_late <= 7:
        return _RELIABILITY_POINTS_4_TO_7_DAYS
    return _RELIABILITY_POINTS_OVER_7_DAYS


def get_trust_signals(user_id: int) -> TrustSignals:
    """Compute both signals for a user as a borrower. Cold-start cases
    ("New Member", "Not Yet Rated") never imply poor behaviour.
    """
    with get_session() as session:
        completed_loans = session.scalars(
            select(Loan).where(
                Loan.borrower_id == user_id, Loan.return_date.is_not(None)
            )
        ).all()

        if not completed_loans:
            reliability = "New Member"
        else:
            points = [_reliability_points(loan) for loan in completed_loans]
            reliability = _category_for_score(sum(points) / len(points))

        rated_loans = [loan for loan in completed_loans if loan.condition_rating is not None]
        if not rated_loans:
            book_care = "Not Yet Rated"
        else:
            points = [_BOOK_CARE_POINTS[loan.condition_rating] for loan in rated_loans]
            book_care = _category_for_score(sum(points) / len(points))

        return TrustSignals(reliability=reliability, book_care=book_care)


__all__ = ["TrustSignals", "get_trust_signals"]
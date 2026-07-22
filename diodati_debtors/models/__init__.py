"""SQLAlchemy models. Importing them here ensures every model is
registered on Base.metadata before Alembic's autogenerate inspects it.
"""

from .user import User
from .group import Group, GroupMembership
from .join_request import JoinRequest
from .book import Book
from .loan import Loan
from .loan_request import LoanRequest
from .post import Post
from .comment import Comment
from .review import Review

__all__ = [
    "User",
    "Group",
    "GroupMembership",
    "JoinRequest",
    "Book",
    "Loan",
    "LoanRequest",
    "Post",
    "Comment",
    "Review",
]
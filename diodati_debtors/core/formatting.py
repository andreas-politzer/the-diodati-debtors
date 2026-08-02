"""Shared, human-readable formatting helpers — used across State
classes to avoid duplicating date/time display logic (same principle
as compute_initials in ui/components/avatar.py).
"""

from __future__ import annotations

import datetime as dt


def format_datetime_human(value: dt.datetime) -> str:
    """e.g. 'July 22, 2026, 7:47 AM' — no seconds, no raw ISO format,
    reads like a normal sentence, not a machine timestamp. Uses
    strip() on the hour instead of platform-specific %-I/%#I format
    codes, since those differ between Linux/Mac and Windows."""
    date_part = value.strftime("%B %d, %Y")
    hour_12 = value.strftime("%I").lstrip("0") or "0"
    minute = value.strftime("%M")
    am_pm = value.strftime("%p")
    return f"{date_part}, {hour_12}:{minute} {am_pm}"


__all__ = ["format_datetime_human"]
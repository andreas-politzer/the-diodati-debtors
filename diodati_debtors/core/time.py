"""Project-wide time policy.

All stored timestamps are generated at the application layer (not the
database server) and stored as naive datetimes representing UTC.
Relying on server_default=func.now() would depend on the MySQL server's
configured timezone, which can differ across environments (local
Docker vs. a later production host) — this avoids that entirely.

Localizing a timestamp for display is a UI-layer concern and must
never happen in models or services.

`today()` exists so services never call `datetime.date.today()`
directly — tests can monkeypatch this single function to inject a
deterministic date, instead of patching the standard library.
"""

from __future__ import annotations

import datetime as dt


def utcnow() -> dt.datetime:
    """Current time as a naive datetime representing UTC."""
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


def today() -> dt.date:
    """Current date, per the application's UTC time policy."""
    return utcnow().date()
"""Central application configuration.

Architecture rule (Implementation Specification, Phase 0):
all environment-specific values come from configuration; no demo IDs,
names, credentials, or policy thresholds in application code.

This module reads exclusively from environment variables (optionally
loaded from a local .env file that is NOT committed to git — see
.gitignore). Every value has a safe, non-secret local-dev default;
nothing here is a production credential.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - optional dependency
    # python-dotenv is not a hard requirement; if it's not installed,
    # we simply rely on variables already present in the environment.
    pass


def _get_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Immutable application settings, resolved once at import time."""

    # -- Database -----------------------------------------------------
    db_host: str = os.environ.get("DIODATI_DB_HOST", "localhost")
    db_port: int = int(os.environ.get("DIODATI_DB_PORT", "3306"))
    db_name: str = os.environ.get("DIODATI_DB_NAME", "diodati_debtors")
    db_user: str = os.environ.get("DIODATI_DB_USER", "diodati")
    db_password: str = os.environ.get("DIODATI_DB_PASSWORD", "")

    # -- App behaviour --------------------------------------------------
    debug: bool = _get_bool("DIODATI_DEBUG", True)

    # -- External services (Phase 0: read only, not yet wired up) -----
    open_library_base_url: str = os.environ.get(
        "OPEN_LIBRARY_BASE_URL", "https://openlibrary.org"
    )
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")

    @property
    def sqlalchemy_database_uri(self) -> str:
        """Assemble the PyMySQL connection string from discrete parts.

        Kept as a computed property rather than a single hardcoded
        connection string so that no credential fragment ever needs to
        be pasted into code — only into environment variables / a local
        .env file, which is excluded from version control.
        """
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()

"""Cron entry point: compute embeddings for every book that doesn't
have one yet. Per the 07.08. architecture decision (project vault):
embeddings are search infrastructure, maintained periodically via a
Railway Cron Job — not synchronously during book writes. Safe to
re-run repeatedly (idempotent).
"""

from __future__ import annotations

from diodati_debtors.services import librarian_maintenance_service


def main() -> None:
    report = librarian_maintenance_service.backfill_missing_embeddings()
    print(
        f"Embedding backfill complete: {report.succeeded}/{report.total_checked} "
        f"succeeded, {report.failed} failed."
    )


if __name__ == "__main__":
    main()
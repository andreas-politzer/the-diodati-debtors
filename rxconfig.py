"""Reflex configuration for The Diodati Debtors.

Phase 0 scope only: bootstrap-level settings. No feature flags, no
demo/environment values hardcoded here — those come from core/config.py.
"""

import reflex as rx

config = rx.Config(
    app_name="diodati_debtors",
    plugins=[
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(
                appearance="light",
                has_background=True,
                radius="none",
                scaling="100%",
            )
        ),
    ],
    disable_plugins=[rx.plugins.SitemapPlugin],
)
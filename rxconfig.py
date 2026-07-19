"""Reflex configuration for The Diodati Debtors.

Phase 0 scope only: bootstrap-level settings. No feature flags, no
demo/environment values hardcoded here — those come from core/config.py.
"""

import reflex as rx

# NOTE (verify before commit): Reflex made Radix Themes an explicit opt-in
# plugin starting in 0.9.0 (previously implicit, which raised a
# DeprecationWarning). The exact plugin class name has moved between
# releases. Confirm the correct name against your installed version with:
#
#   python -c "import reflex as rx; print([p for p in dir(rx.plugins) if 'Radix' in p or 'Theme' in p])"
#
# and adjust the import below accordingly before relying on this file.
try:
    _radix_plugin = rx.plugins.RadixThemesPlugin()
except AttributeError as exc:  # pragma: no cover - environment-dependent
    raise RuntimeError(
        "rx.plugins.RadixThemesPlugin not found on this Reflex version. "
        "Run the verification command in the comment above and update "
        "rxconfig.py with the correct plugin class name."
    ) from exc

config = rx.Config(
    app_name="diodati_debtors",
    plugins=[
        _radix_plugin,
    ],
)

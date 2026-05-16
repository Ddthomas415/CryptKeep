from __future__ import annotations
"""
DEPRECATED — this module is in a transitional service family scheduled for
removal on 2026-07-01. See docs/ARCHITECTURE.md for the migration plan.
Import from the canonical path instead.
"""
import warnings as _warnings
_warnings.warn(
    f"{{__name__}} is deprecated and will be removed 2026-07-01. "
    "Use 'services/execution/startup_guard.py' instead. See docs/ARCHITECTURE.md.",
    DeprecationWarning,
    stacklevel=2,
)


import os

from storage.position_state_sqlite import PositionStateSQLite


class StartupGuardError(RuntimeError):
    pass


def require_known_flat_or_override(*, venue: str, symbol: str) -> None:
    row = PositionStateSQLite().get(venue=venue, symbol=symbol)
    if row is None:
        if os.getenv("CBP_STARTUP_CONFIRM_FLAT", "").strip().lower() == "true":
            return
        raise StartupGuardError("unknown_position_state")

    qty = float((row.get("qty") if isinstance(row, dict) else getattr(row, "qty", 0.0)) or 0.0)
    if qty != 0.0 and os.getenv("CBP_STARTUP_ALLOW_OPEN_POSITION", "").strip().lower() != "true":
        raise StartupGuardError("open_position_requires_override")

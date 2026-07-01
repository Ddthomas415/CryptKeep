"""Deprecated compatibility wrapper for the canonical strategy runner.

Use ``services.execution.strategy_runner`` for runtime execution. This module
re-exports the canonical runner only to preserve existing external imports until
the 2026-08-01 transitional-family deadline.
"""
from __future__ import annotations

from services.execution import strategy_runner as _canonical


for _name in dir(_canonical):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_canonical, _name)

__all__ = [_name for _name in dir(_canonical) if not _name.startswith("__")]

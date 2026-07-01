"""Deprecated strategy-runner compatibility package.

Use ``services.strategies`` for strategy implementations and the canonical
runtime scripts for execution wiring. This package remains only as a temporary
compatibility surface until the 2026-08-01 transitional-family deadline.
"""
from __future__ import annotations

import warnings


warnings.warn(
    "services.strategy_runner is deprecated and will be removed after 2026-08-01; "
    "use services.strategies and canonical runtime scripts instead.",
    DeprecationWarning,
    stacklevel=2,
)

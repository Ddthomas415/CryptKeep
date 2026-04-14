"""
DEPRECATED — this module is in a transitional service family scheduled for
removal on 2026-07-01. See docs/ARCHITECTURE.md for the migration plan.
Import from the canonical path instead.
"""
import warnings as _warnings
_warnings.warn(
    f"{{__name__}} is deprecated and will be removed 2026-07-01. "
    "Use 'services/market_data/ws_ticker_feed.py' instead. See docs/ARCHITECTURE.md.",
    DeprecationWarning,
    stacklevel=2,
)

from services.market_data.ws_ticker_feed import *

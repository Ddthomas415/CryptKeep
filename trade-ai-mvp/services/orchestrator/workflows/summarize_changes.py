from __future__ import annotations

from typing import Any


def summarize_changes(asset: str, market_delta_pct: float, doc_count: int) -> str:
    direction = "up" if market_delta_pct >= 0 else "down"
    return (
        f"{asset} moved {direction} {abs(market_delta_pct):.2f}% with "
        f"{doc_count} relevant context documents in scope."
    )

from __future__ import annotations

from typing import Any

from shared.clients.exchange_client import fetch_coinbase_snapshot


async def get_snapshot(symbol: str) -> dict[str, Any]:
    return await fetch_coinbase_snapshot(symbol)

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import httpx

@dataclass(frozen=True)
class DepthSnapshot:
    last_update_id: int
    bids: List[Tuple[float, float]]  # (price, qty)
    asks: List[Tuple[float, float]]  # (price, qty)

async def fetch_depth_snapshot(symbol: str, limit: int = 1000, timeout: float = 10.0) -> DepthSnapshot:
    sym = symbol.upper().replace("-", "").replace("_", "")
    url = "https://api.binance.com/api/v3/depth"
    params = {"symbol": sym, "limit": int(limit)}
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    last_id = int(data["lastUpdateId"])
    bids = [(float(p), float(q)) for p, q in data.get("bids", [])]
    asks = [(float(p), float(q)) for p, q in data.get("asks", [])]
    return DepthSnapshot(last_update_id=last_id, bids=bids, asks=asks)

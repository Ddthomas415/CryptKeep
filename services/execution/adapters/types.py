from __future__ import annotations

from typing import Any, Dict, Optional, TypedDict, Literal

Side = Literal["buy", "sell"]

class OrderRequest(TypedDict, total=False):
    # minimal shape used across executor codepaths
    symbol: str
    side: Side
    type: str                 # "market"/"limit"/etc.
    amount: float
    price: Optional[float]
    params: Dict[str, Any]

class OrderResponse(TypedDict, total=False):
    id: str
    status: str
    filled: float
    remaining: float
    cost: float
    price: float
    average: float
    info: Any

__all__ = ["Side", "OrderRequest", "OrderResponse"]

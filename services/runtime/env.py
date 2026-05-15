from __future__ import annotations

import os
from typing import List

def env_venue(default: str = "coinbase") -> str:
    return str(os.environ.get("CBP_VENUE") or default).lower().strip()

def env_symbols(default: List[str] | None = None) -> List[str]:
    if default is None:
        default = ["BTC/USD"]
    raw = (os.environ.get("CBP_SYMBOLS") or "").strip()
    if not raw:
        return list(default)
    return [x.strip() for x in raw.split(",") if x.strip()]

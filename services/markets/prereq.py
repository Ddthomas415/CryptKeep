from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from services.markets.cache_sqlite import any_fresh, default_exec_db

@dataclass(frozen=True)
class MarketRulesPrereq:
    ok: bool
    ttl_s: float
    message: str
    meta: Dict[str, Any]

def check_market_rules_prereq(exec_db: Optional[str] = None, ttl_s: float = 6 * 3600.0) -> MarketRulesPrereq:
    db = exec_db or default_exec_db()
    try:
        ok = bool(any_fresh(db, float(ttl_s)))
        if ok:
            return MarketRulesPrereq(True, float(ttl_s), "OK", {"exec_db": db})
        return MarketRulesPrereq(False, float(ttl_s), "MARKET_RULES_CACHE_STALE_OR_EMPTY", {"exec_db": db, "hint": "Run scripts/refresh_market_rules.py"})
    except Exception as e:
        return MarketRulesPrereq(False, float(ttl_s), "EXCEPTION", {"exec_db": db, "error": f"{type(e).__name__}: {e}"})

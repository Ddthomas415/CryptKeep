from __future__ import annotations
from services.markets.symbols import env_symbol
import os
import time
import uuid
from services.admin.config_editor import load_user_yaml
from services.market_data.symbol_router import normalize_venue, normalize_symbol
from storage.intent_queue_sqlite import IntentQueueSQLite
from storage.signal_reliability_sqlite import SignalReliabilitySQLite

def _cfg() -> dict:
    cfg = load_user_yaml()
    r = cfg.get("signals") if isinstance(cfg.get("signals"), dict) else {}
    return {
        "auto_route_to_paper": bool(r.get("auto_route_to_paper", False)),
        "allowed_sources": r.get("allowed_sources") if isinstance(r.get("allowed_sources"), list) else [],
        "allowed_authors": r.get("allowed_authors") if isinstance(r.get("allowed_authors"), list) else [],
        "allowed_symbols": r.get("allowed_symbols") if isinstance(r.get("allowed_symbols"), list) else [],
        "default_venue": normalize_venue(str(os.environ.get("CBP_VENUE") or r.get("default_venue") or "coinbase")),
        "default_qty": float(r.get("default_qty", 0.001) or 0.001),
        "order_type": str(r.get("order_type", "market") or "market").lower().strip(),
    }

def _allowed(val: str, allowed_list: list[str]) -> bool:
    if not allowed_list:
        return True
    return val in set(str(x) for x in allowed_list)

def route_signal_to_paper_intent(sig: dict) -> dict:
    """
    Creates a paper intent from a signal, only if config allows and allowlists pass.
    """
    cfg = _cfg()
    if not cfg["auto_route_to_paper"]:
        return {"ok": False, "reason": "signals.auto_route_to_paper_disabled"}
    source = str(sig.get("source") or "")
    author = str(sig.get("author") or "")
    symbol = normalize_symbol(str(sig.get("symbol") or ""))
    action = str(sig.get("action") or "").lower().strip()
    if action not in ("buy","sell"):
        return {"ok": False, "reason": "signal_action_not_tradeable", "action": action}
    if not _allowed(source, cfg["allowed_sources"]):
        return {"ok": False, "reason": "source_not_allowed", "source": source}
    if not _allowed(author, cfg["allowed_authors"]):
        return {"ok": False, "reason": "author_not_allowed", "author": author}
    if cfg["allowed_symbols"] and symbol not in set(normalize_symbol(str(s)) for s in cfg["allowed_symbols"]):
        return {"ok": False, "reason": "symbol_not_allowed", "symbol": symbol}
    venue = normalize_venue(str(sig.get("venue_hint") or cfg["default_venue"]))
    qty = float(sig.get("qty") or cfg["default_qty"])
    intent_id = str(uuid.uuid4())
    it = {
        "intent_id": intent_id,
        "ts": str(int(time.time())),
        "source": "signal_inbox",
        "venue": venue,
        "symbol": symbol,
        "side": action,
        "order_type": cfg["order_type"],
        "qty": qty,
        "limit_price": None,
        "status": "queued",
        "last_error": None,
    }
    db = IntentQueueSQLite()
    db.upsert_intent(it)
    return {"ok": True, "intent_id": intent_id, "intent": it}

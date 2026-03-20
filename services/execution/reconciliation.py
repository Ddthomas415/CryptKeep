from __future__ import annotations

from services.market_data.symbol_router import normalize_venue, normalize_symbol
from services.market_data.symbol_utils import split_symbol
from services.security.credentials_loader import load_exchange_credentials
from services.security.exchange_factory import make_exchange
from storage.position_state_sqlite import PositionStateSQLite


def _safe_float(x) -> float:
    try:
        return float(x or 0.0)
    except Exception:
        return 0.0


def reconcile_spot_position(*, venue: str, symbol: str) -> dict:
    v = normalize_venue(venue)
    sym = normalize_symbol(symbol)
    base, quote = split_symbol(sym)
    ex = None
    try:
        creds = load_exchange_credentials(v)
        if not creds.get("apiKey") or not creds.get("secret"):
            return {
                "ok": False,
                "error": "missing_credentials",
                "venue": v,
                "symbol": sym,
                "source": str(creds.get("source") or "unknown"),
                "api_env": creds.get("api_env"),
                "secret_env": creds.get("secret_env"),
            }
        ex = make_exchange(
            v,
            {
                "apiKey": creds["apiKey"],
                "secret": creds["secret"],
                "password": creds.get("password"),
            },
            enable_rate_limit=True,
        )
        bal = ex.fetch_balance()
        total_map = bal.get("total") if isinstance(bal.get("total"), dict) else {}
        free_map = bal.get("free") if isinstance(bal.get("free"), dict) else {}
        used_map = bal.get("used") if isinstance(bal.get("used"), dict) else {}
        base_total = None
        if base in total_map:
            base_total = _safe_float(total_map.get(base))
        else:
            cur = bal.get(base)
            if isinstance(cur, dict):
                base_total = _safe_float(cur.get("total"))
        if base_total is None:
            base_total = _safe_float(free_map.get(base)) + _safe_float(used_map.get(base))
        status = "open" if base_total > 0 else "flat"
        PositionStateSQLite().upsert(
            venue=v, symbol=sym, base=base, quote=quote,
            qty=float(base_total),
            status=status,
            note="reconciled_from_balance",
            raw={"base_total": float(base_total)},
        )
        return {"ok": True, "venue": v, "symbol": sym, "base": base, "qty": float(base_total), "status": status}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}:{e}", "venue": v, "symbol": sym}
    finally:
        try:
            if ex is not None and hasattr(ex, "close"):
                ex.close()
        except Exception:
            pass


def reconcile_once(*, venue: str, symbol: str) -> dict:
    """Compatibility alias for legacy callers."""
    return reconcile_spot_position(venue=venue, symbol=symbol)

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.security.credentials_loader import load_exchange_credentials
from services.security.exchange_factory import make_exchange


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

# Only read-only probes (safe)
PROBES: dict[str, dict] = {
    "fetch_balance": {"label": "fetchBalance (read)", "fn": lambda ex: ex.fetch_balance()},
    "fetch_open_orders": {"label": "fetchOpenOrders (read)", "fn": lambda ex: ex.fetch_open_orders()},
    "fetch_my_trades": {"label": "fetchMyTrades (read)", "fn": lambda ex: ex.fetch_my_trades()},
    "fetch_closed_orders": {"label": "fetchClosedOrders (read)", "fn": lambda ex: ex.fetch_closed_orders()},
    "fetch_deposits": {"label": "fetchDeposits (read)", "fn": lambda ex: ex.fetch_deposits()},
    "fetch_withdrawals": {"label": "fetchWithdrawals (read)", "fn": lambda ex: ex.fetch_withdrawals()},
}

DEFAULT_PROBES = ["fetch_balance", "fetch_open_orders", "fetch_my_trades"]

def list_probes() -> list[dict]:
    out = []
    for k, v in PROBES.items():
        out.append({"key": k, "label": v.get("label")})
    return out

def _close_exchange(ex: Any) -> None:
    try:
        if hasattr(ex, "close"):
            ex.close()
    except Exception:
        pass

def exchange_has_flags(exchange_id: str, creds: dict) -> dict:
    ex = make_exchange(exchange_id, creds)
    try:
        has = getattr(ex, "has", None)
        return dict(has) if isinstance(has, dict) else {}
    finally:
        _close_exchange(ex)

def run_probe(exchange_id: str, probe_key: str) -> dict:
    ex_id = str(exchange_id).lower().strip()
    key = str(probe_key).lower().strip()

    if key not in PROBES:
        return {"ok": False, "exchange": ex_id, "probe": key, "reason": "unknown_probe", "ts": _now()}

    creds = load_exchange_credentials(ex_id)
    if not creds.get("apiKey") or not creds.get("secret"):
        return {
            "ok": False,
            "exchange": ex_id,
            "probe": key,
            "reason": "missing_credentials",
            "source": str(creds.get("source") or "unknown"),
            "ts": _now(),
        }

    ex = make_exchange(ex_id, creds)
    try:
        fn = PROBES[key]["fn"]
        res = fn(ex)

        # Return compact summaries only
        summary = {"type": type(res).__name__}
        if isinstance(res, dict):
            # common balance summary
            if "total" in res and isinstance(res["total"], dict):
                summary["total_asset_count"] = len(res["total"].keys())
        if isinstance(res, list):
            summary["list_count"] = len(res)

        return {"ok": True, "exchange": ex_id, "probe": key, "ts": _now(), "summary": summary}
    except Exception as e:
        return {"ok": False, "exchange": ex_id, "probe": key, "ts": _now(), "reason": type(e).__name__, "error": str(e)[:700]}
    finally:
        _close_exchange(ex)

def run_probes(exchange_id: str, probe_keys: list[str]) -> dict:
    out = {"exchange": str(exchange_id).lower().strip(), "ts": _now(), "results": []}
    for k in probe_keys or []:
        out["results"].append(run_probe(exchange_id, k))
    out["ok"] = all(bool(r.get("ok")) for r in out["results"]) if out["results"] else False
    return out

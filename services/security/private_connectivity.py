from __future__ import annotations

from datetime import datetime, timezone

from services.security.credentials_loader import load_exchange_credentials
from services.security.exchange_factory import make_exchange


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def test_private_connectivity(exchange: str) -> dict:
    ex = str(exchange).lower().strip()
    creds = load_exchange_credentials(ex)
    if not creds.get("apiKey") or not creds.get("secret"):
        return {
            "ok": False,
            "exchange": ex,
            "reason": "missing_credentials",
            "source": str(creds.get("source") or "unknown"),
            "ts": _now(),
        }

    client = None
    try:
        client = make_exchange(ex, creds)
        # Low-risk call (read-only)
        bal = client.fetch_balance()
        # Don't dump full balances (can be huge); return a compact summary
        totals = bal.get("total") if isinstance(bal, dict) else None
        count_assets = len(totals.keys()) if isinstance(totals, dict) else None
        return {"ok": True, "exchange": ex, "ts": _now(), "balance_total_asset_count": count_assets}
    except Exception as e:
        return {"ok": False, "exchange": ex, "ts": _now(), "reason": f"{type(e).__name__}", "error": str(e)[:600]}
    finally:
        try:
            if client is not None and hasattr(client, "close"):
                client.close()
        except Exception:
            pass

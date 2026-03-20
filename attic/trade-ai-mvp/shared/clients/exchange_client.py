from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

try:
    import httpx
except Exception:  # pragma: no cover - optional in minimal local env
    httpx = None


def _normalize_symbol(symbol: str) -> str:
    raw = str(symbol).upper().replace("/", "-")
    if "-" not in raw:
        return f"{raw}-USD"
    return raw


def _fallback_snapshot(symbol: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    seeded = {
        "SOL-USD": ("145.20", "145.10", "145.30"),
        "BTC-USD": ("84250.12", "84249.90", "84250.20"),
        "ETH-USD": ("4380.50", "4380.20", "4380.80"),
    }
    last, bid, ask = seeded.get(_normalize_symbol(symbol), ("100.00", "99.90", "100.10"))
    spread = f"{(float(ask) - float(bid)):.2f}"
    return {
        "symbol": _normalize_symbol(symbol),
        "exchange": "coinbase",
        "last_price": last,
        "bid": bid,
        "ask": ask,
        "spread": spread,
        "timestamp": now.isoformat(),
        "raw": {"source": "fallback"},
    }


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _snapshot_from_exchange_payload(pair: str, data: dict[str, Any]) -> dict[str, Any]:
    bid = str(data.get("bid") or "0")
    ask = str(data.get("ask") or "0")
    last = str(data.get("price") or data.get("last") or "0")
    bid_f = _safe_float(bid)
    ask_f = _safe_float(ask)
    spread = f"{(ask_f - bid_f):.8f}" if bid_f and ask_f else "0"
    return {
        "symbol": pair,
        "exchange": "coinbase",
        "last_price": last,
        "bid": bid,
        "ask": ask,
        "spread": spread,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw": {"provider": "coinbase_exchange", "payload": data},
    }


def _snapshot_from_spot_payload(pair: str, data: dict[str, Any]) -> dict[str, Any] | None:
    amount = (
        data.get("data", {}).get("amount")
        if isinstance(data, dict)
        else None
    )
    price = _safe_float(amount)
    if price <= 0:
        return None
    # Spot endpoint does not provide bid/ask; derive a conservative synthetic spread.
    bid = price * 0.9995
    ask = price * 1.0005
    spread = ask - bid
    return {
        "symbol": pair,
        "exchange": "coinbase",
        "last_price": f"{price:.8f}",
        "bid": f"{bid:.8f}",
        "ask": f"{ask:.8f}",
        "spread": f"{spread:.8f}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw": {"provider": "coinbase_spot", "payload": data},
    }


async def fetch_coinbase_snapshot(symbol: str, timeout: float = 8.0, retries: int = 2) -> dict[str, Any]:
    pair = _normalize_symbol(symbol)
    ticker_url = f"https://api.exchange.coinbase.com/products/{pair}/ticker"
    spot_url = f"https://api.coinbase.com/v2/prices/{pair}/spot"

    last_error: str | None = None
    if httpx is None:
        out = _fallback_snapshot(pair)
        out["raw"]["error"] = "httpx_missing"
        return out
    for _ in range(retries + 1):
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                headers={"User-Agent": "trade-ai-mvp/0.1 (+research-copilot)"},
            ) as client:
                ticker_resp = await client.get(ticker_url)
                ticker_resp.raise_for_status()
                ticker_data = ticker_resp.json()
                snap = _snapshot_from_exchange_payload(pair, ticker_data)
                if _safe_float(snap["last_price"]) > 0:
                    return snap
        except Exception as exc:
            last_error = str(exc)

        # Secondary fallback to Coinbase spot API for last traded price.
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                headers={"User-Agent": "trade-ai-mvp/0.1 (+research-copilot)"},
            ) as client:
                spot_resp = await client.get(spot_url)
                spot_resp.raise_for_status()
                spot_data = spot_resp.json()
                snap = _snapshot_from_spot_payload(pair, spot_data)
                if snap:
                    return snap
        except Exception as exc:
            last_error = str(exc)

    out = _fallback_snapshot(pair)
    out["raw"]["error"] = last_error or "coinbase_fetch_failed"
    return out

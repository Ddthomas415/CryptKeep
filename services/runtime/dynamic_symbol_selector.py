from __future__ import annotations

from typing import Any

from dashboard.services.symbol_scanner import run_symbol_scan


DEFAULT_EXCLUDES = {
    "USDT/USD",
    "USDC/USD",
    "DAI/USD",
    "PYUSD/USD",
    "EURC/USD",
}


def _safe(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _is_tradeable_symbol(symbol: str) -> bool:
    s = str(symbol or "").upper().strip()
    if not s or s in DEFAULT_EXCLUDES:
        return False
    if "/" not in s:
        return False
    base, quote = s.split("/", 1)
    if quote not in {"USD", "USDC"}:
        return False
    if len(base) < 2:
        return False
    return True


def select_symbols(
    *,
    venue: str = "coinbase",
    top_n: int = 10,
    min_hot_score: float = 25.0,
    min_change_pct: float = 2.5,
    min_volume_24h: float = 100000.0,
) -> dict[str, Any]:
    """
    Pull the scanner's market-wide results and return a ranked list of
    symbols suitable for execution.

    Returns:
        {
            "ok": True,
            "source": "coinbase_movers",
            "selected": ["BTC/USD", ...],
            "rows": [...],
            "scanned": 773,
            "ts": "...",
        }
    """
    scan = run_symbol_scan(venue=venue, symbols=[])
    if not scan.get("ok"):
        return {
            "ok": False,
            "selected": [],
            "rows": [],
            "errors": scan.get("errors", []),
            "source": scan.get("source"),
            "scanned": scan.get("scanned", 0),
            "ts": scan.get("ts"),
        }

    rows = list(scan.get("hot") or scan.get("momentum") or [])
    filtered: list[dict[str, Any]] = []

    for row in rows:
        symbol = str(row.get("symbol") or "")
        hot_score = _safe(row.get("hot_score"), 0.0)
        change_pct = _safe(row.get("change_pct"), 0.0)
        volume_24h = _safe(row.get("volume_24h"), 0.0)

        if not _is_tradeable_symbol(symbol):
            continue
        if hot_score < min_hot_score:
            continue
        if change_pct < min_change_pct:
            continue
        if volume_24h < min_volume_24h:
            continue

        filtered.append({
            "symbol": symbol,
            "hot_score": round(hot_score, 2),
            "change_pct": round(change_pct, 2),
            "volume_24h": round(volume_24h, 2),
            "volatility_pct": round(_safe(row.get("volatility_pct"), 0.0), 2),
            "rsi": row.get("rsi"),
            "signal": row.get("signal"),
        })

    filtered.sort(
        key=lambda r: (r["hot_score"], r["change_pct"], r["volume_24h"]),
        reverse=True,
    )

    selected = [r["symbol"] for r in filtered[:top_n]]

    return {
        "ok": True,
        "source": scan.get("source"),
        "selected": selected,
        "rows": filtered[:top_n],
        "scanned": scan.get("scanned", 0),
        "ts": scan.get("ts"),
        "errors": scan.get("errors", []),
    }


if __name__ == "__main__":
    result = select_symbols()
    print({
        "ok": result.get("ok"),
        "selected": result.get("selected"),
        "count": len(result.get("selected") or []),
        "source": result.get("source"),
        "scanned": result.get("scanned"),
        "errors": len(result.get("errors") or []),
    })

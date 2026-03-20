from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import json
from typing import Any

from services.market_data.symbol_router import map_symbol, normalize_symbol, normalize_venue
from services.security.binance_guard import require_binance_allowed
from services.strategies.presets import apply_preset
from services.strategies.strategy_registry import compute_signal

_PRESET_BY_STRATEGY = {
    "ema_cross": "ema_cross_default",
    "breakout_donchian": "breakout_default",
    "mean_reversion_rsi": "mean_reversion_default",
}


def _csv_items(text: str) -> list[str]:
    return [str(item).strip() for item in str(text or "").split(",") if str(item).strip()]


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _market_volume(market: dict[str, Any]) -> float:
    info = market.get("info") if isinstance(market.get("info"), dict) else {}
    for key in ("quoteVolume", "quote_volume", "baseVolume", "base_volume", "volume", "vol"):
        if key in market:
            return _as_float(market.get(key))
        if key in info:
            return _as_float(info.get(key))
    return 0.0


def _select_symbols(
    markets: dict[str, dict[str, Any]],
    *,
    quotes: list[str],
    max_symbols: int,
    explicit_symbols: list[str] | None = None,
) -> list[str]:
    if explicit_symbols:
        seen: set[str] = set()
        out: list[str] = []
        for item in explicit_symbols:
            sym = normalize_symbol(item)
            if sym and sym not in seen:
                out.append(sym)
                seen.add(sym)
        return out

    wanted_quotes = {str(item or "").strip().upper() for item in quotes if str(item or "").strip()}
    rows: list[tuple[float, str]] = []
    for raw_symbol, raw_market in (markets or {}).items():
        market = raw_market if isinstance(raw_market, dict) else {}
        symbol = normalize_symbol(str(market.get("symbol") or raw_symbol or ""))
        if "/" not in symbol:
            continue
        base, quote = symbol.split("/", 1)
        if wanted_quotes and quote.upper() not in wanted_quotes:
            continue
        if market.get("active") is False:
            continue
        if market.get("spot") is False:
            continue
        market_type = str(market.get("type") or "").strip().lower()
        if market_type and market_type != "spot":
            continue
        if not base or not quote:
            continue
        rows.append((_market_volume(market), symbol))
    rows.sort(key=lambda item: (-item[0], item[1]))
    return [symbol for _, symbol in rows[: max(1, int(max_symbols or 1))]]


def _strategy_cfg(strategy: str) -> dict[str, Any]:
    name = str(strategy or "").strip()
    preset = _PRESET_BY_STRATEGY.get(name)
    if not preset:
        raise KeyError(f"unsupported_strategy:{name}")
    return apply_preset({}, preset)


def _make_public_exchange(venue: str):
    import ccxt  # type: ignore

    venue_id = normalize_venue(venue)
    require_binance_allowed(venue_id)
    klass = getattr(ccxt, venue_id)
    return klass({"enableRateLimit": True})


def _candidate_rank(item: dict[str, Any]) -> tuple[float, float, float, str, str]:
    ind = item.get("ind") if isinstance(item.get("ind"), dict) else {}
    return (
        _as_float(ind.get("volume_ratio")),
        _as_float(ind.get("avg_range_pct")),
        _as_float(ind.get("trend_efficiency")),
        str(item.get("symbol") or ""),
        str(item.get("timeframe") or ""),
    )


def scan_candidates(
    *,
    venue: str,
    quotes: list[str],
    strategies: list[str],
    timeframes: list[str],
    action: str,
    max_symbols: int,
    limit: int,
    symbols: list[str] | None = None,
    exchange: Any | None = None,
) -> dict[str, Any]:
    venue_id = normalize_venue(venue)
    requested_action = str(action or "buy").strip().lower() or "buy"
    ex = exchange or _make_public_exchange(venue_id)
    errors: list[dict[str, str]] = []
    candidates: list[dict[str, Any]] = []

    try:
        markets = ex.load_markets() or {}
        selected = _select_symbols(
            markets,
            quotes=quotes,
            max_symbols=max_symbols,
            explicit_symbols=list(symbols or []),
        )
        for symbol in selected:
            mapped_symbol = map_symbol(venue_id, symbol)
            for timeframe in timeframes:
                try:
                    ohlcv = ex.fetch_ohlcv(mapped_symbol, timeframe=str(timeframe), limit=int(limit))
                except Exception as exc:
                    errors.append(
                        {
                            "symbol": symbol,
                            "mapped_symbol": mapped_symbol,
                            "timeframe": str(timeframe),
                            "reason": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    continue
                if not isinstance(ohlcv, list) or not ohlcv:
                    continue
                for strategy in strategies:
                    try:
                        sig = compute_signal(cfg=_strategy_cfg(strategy), symbol=symbol, ohlcv=ohlcv)
                    except Exception as exc:
                        errors.append(
                            {
                                "symbol": symbol,
                                "mapped_symbol": mapped_symbol,
                                "strategy": str(strategy),
                                "timeframe": str(timeframe),
                                "reason": f"{type(exc).__name__}: {exc}",
                            }
                        )
                        continue
                    item = {
                        "strategy": str(strategy),
                        "symbol": symbol,
                        "mapped_symbol": mapped_symbol,
                        "venue": venue_id,
                        "timeframe": str(timeframe),
                        "candles": int(len(ohlcv)),
                        "action": str(sig.get("action") or "hold"),
                        "reason": str(sig.get("reason") or ""),
                        "ind": sig.get("ind") if isinstance(sig.get("ind"), dict) else {},
                    }
                    if item["action"] == requested_action:
                        candidates.append(item)
        candidates.sort(key=_candidate_rank, reverse=True)
        return {
            "ok": True,
            "venue": venue_id,
            "quotes": list(quotes),
            "strategies": list(strategies),
            "timeframes": list(timeframes),
            "requested_action": requested_action,
            "scanned_symbols": len(selected),
            "candidates": candidates,
            "errors": errors,
        }
    finally:
        close = getattr(ex, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan public markets for actionable strategy signals.")
    ap.add_argument("--venue", default="coinbase", help="Exchange venue id")
    ap.add_argument("--quotes", default="USD", help="Comma-separated quote currencies to scan")
    ap.add_argument("--strategies", default="breakout_donchian,ema_cross", help="Comma-separated canonical strategy ids")
    ap.add_argument("--timeframes", default="1m,5m,15m", help="Comma-separated CCXT timeframes to scan")
    ap.add_argument("--action", default="buy", help="Action to return, usually buy or sell")
    ap.add_argument("--max-symbols", type=int, default=60, help="Maximum number of discovered symbols to scan")
    ap.add_argument("--limit", type=int, default=120, help="OHLCV candles to fetch per symbol/timeframe")
    ap.add_argument("--symbols", default="", help="Optional comma-separated explicit symbols to scan")
    ap.add_argument("--top", type=int, default=20, help="Maximum number of candidates to print")
    args = ap.parse_args()

    out = scan_candidates(
        venue=str(args.venue or "coinbase"),
        quotes=[str(item).upper() for item in _csv_items(args.quotes or "USD")],
        strategies=_csv_items(args.strategies or "breakout_donchian,ema_cross"),
        timeframes=_csv_items(args.timeframes or "1m,5m,15m"),
        action=str(args.action or "buy"),
        max_symbols=int(args.max_symbols or 60),
        limit=int(args.limit or 120),
        symbols=_csv_items(args.symbols or ""),
    )
    out["candidates"] = list(out.get("candidates") or [])[: max(1, int(args.top or 20))]
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

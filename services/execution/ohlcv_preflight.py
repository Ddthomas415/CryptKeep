"""Read-only public-OHLCV reachability preflight.

Run this before a governed Stage 0 / paper session to distinguish a market-data
source problem from a strategy result. The probe mirrors the strategy runner's
public-OHLCV fetch path but never writes snapshots, evidence, or state.
"""
from __future__ import annotations

from typing import Any


def _timeframe_from_source(signal_source: str) -> str | None:
    source = str(signal_source or "").strip().lower()
    if source.startswith("public_ohlcv_"):
        timeframe = source.removeprefix("public_ohlcv_").strip()
        return timeframe or None
    return None


def _config_error(reason: str, *, venue: str, symbol: str, signal_source: str, probe_limit: int | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "invalid_preflight_config",
        "reason": reason,
        "venue": str(venue or ""),
        "symbol": str(symbol or ""),
        "signal_source": str(signal_source or ""),
        "timeframe": None,
        "probe_limit": probe_limit,
        "row_count": 0,
        "error": None,
    }


def check_ohlcv_reachable(
    *,
    venue: str,
    symbol: str,
    signal_source: str,
    probe_limit: int = 5,
) -> dict[str, Any]:
    """Probe whether a config can fetch public OHLCV.

    Exit-code policy for callers:
    - ``ok`` -> success / exit 0.
    - ``ohlcv_source_unreachable`` -> network/source problem / exit 2.
    - all other non-ok statuses -> config or empty-source problem / exit 1.
    """
    venue_s = str(venue or "").strip()
    symbol_s = str(symbol or "").strip()
    signal_source_s = str(signal_source or "").strip()
    try:
        limit_i = int(probe_limit)
    except Exception:
        limit_i = 0

    if not venue_s:
        return _config_error("missing venue", venue=venue_s, symbol=symbol_s, signal_source=signal_source_s, probe_limit=limit_i)
    if not symbol_s:
        return _config_error("missing symbol", venue=venue_s, symbol=symbol_s, signal_source=signal_source_s, probe_limit=limit_i)
    if limit_i <= 0:
        return _config_error("probe_limit must be positive", venue=venue_s, symbol=symbol_s, signal_source=signal_source_s, probe_limit=limit_i)

    timeframe = _timeframe_from_source(signal_source_s)
    result: dict[str, Any] = {
        "ok": False,
        "status": "ohlcv_source_unreachable",
        "reason": "",
        "venue": venue_s,
        "symbol": symbol_s,
        "signal_source": signal_source_s,
        "timeframe": timeframe,
        "probe_limit": limit_i,
        "row_count": 0,
        "error": None,
    }
    if not timeframe:
        result.update(
            status="not_public_ohlcv_source",
            reason=f"signal_source={signal_source_s!r} is not a public_ohlcv_* source",
        )
        return result

    ex = None
    try:
        from services.market_data.symbol_router import map_symbol, normalize_symbol
        from services.security.exchange_factory import make_exchange

        try:
            ex = make_exchange(venue_s, {"apiKey": None, "secret": None}, enable_rate_limit=True)
        except AttributeError as exc:
            result.update(
                status="invalid_preflight_config",
                reason="unknown venue",
                error=f"{type(exc).__name__}: {exc}",
            )
            return result
        mapped_symbol = map_symbol(venue_s, normalize_symbol(symbol_s))
        rows = ex.fetch_ohlcv(mapped_symbol, timeframe=timeframe, limit=limit_i)
        clean_rows = [row for row in list(rows or []) if isinstance(row, (list, tuple)) and len(row) >= 6]
        result["row_count"] = len(clean_rows)
        if clean_rows:
            result.update(ok=True, status="ok", reason="public_ohlcv_reachable")
        else:
            result.update(status="ohlcv_source_empty", reason="fetch returned no usable rows")
    except Exception as exc:
        result.update(
            status="ohlcv_source_unreachable",
            reason="public ohlcv fetch failed",
            error=f"{type(exc).__name__}: {exc}",
        )
    finally:
        try:
            if ex is not None and hasattr(ex, "close"):
                ex.close()
        except Exception:
            pass
    return result


def check_config_ohlcv_reachable(cfg: dict[str, Any], *, probe_limit: int = 5) -> dict[str, Any]:
    """Convenience wrapper for strategy-runner-style config dictionaries."""
    return check_ohlcv_reachable(
        venue=str(cfg.get("venue") or ""),
        symbol=str(cfg.get("symbol") or ""),
        signal_source=str(cfg.get("signal_source") or ""),
        probe_limit=probe_limit,
    )

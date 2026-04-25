from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

from dashboard.services.intelligence import build_opportunity_snapshot
from services.admin.config_editor import CONFIG_PATH, load_user_yaml, save_user_yaml
from services.execution.live_arming import set_live_enabled
from services.setup.config_manager import DEFAULT_CFG, deep_merge

REPO_ROOT = Path(__file__).resolve().parents[2]
API_BASE_URL = os.environ.get("CK_API_BASE_URL", "http://localhost:8000").rstrip("/")
PHASE1_ORCHESTRATOR_URL = os.environ.get("CK_PHASE1_ORCHESTRATOR_URL", "http://localhost:8002").rstrip("/")
PHASE1_SERVICE_TOKEN = (
    os.environ.get("CK_PHASE1_SERVICE_TOKEN")
    or os.environ.get("SERVICE_TOKEN")
    or ""
).strip()
API_TIMEOUT_SECONDS = float(os.environ.get("CK_API_TIMEOUT_SECONDS", "0.6"))



from dashboard.services.views._shared_shared import (
    _extract_close_series,
    _normalize_asset_symbol,
)
from dashboard.services.views._shared_http import (
    _fetch_envelope,
)


def _view_data():
    from dashboard.services import view_data

    return view_data

def _repo_default_watchlist_assets() -> list[str]:
    fallback_assets = ["BTC", "ETH"]
    path = REPO_ROOT / "config" / "trading.yaml"
    if not path.exists():
        return fallback_assets
    try:
        raw_cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return fallback_assets
    if not isinstance(raw_cfg, dict):
        return fallback_assets
    raw_symbols = raw_cfg.get("symbols") if isinstance(raw_cfg.get("symbols"), list) else []
    resolved: list[str] = []
    for item in raw_symbols:
        asset = _normalize_asset_symbol(item)
        if asset and asset not in resolved:
            resolved.append(asset)
    return resolved or fallback_assets


def _default_watchlist_rows() -> list[dict[str, Any]]:
    templates: dict[str, dict[str, Any]] = {
        "BTC": {"price": 84250.12, "change_24h_pct": 2.4, "signal": "watch"},
        "ETH": {"price": 4421.34, "change_24h_pct": 1.3, "signal": "monitor"},
        "SOL": {"price": 187.42, "change_24h_pct": 6.9, "signal": "research"},
    }
    rows: list[dict[str, Any]] = []
    for asset in _repo_default_watchlist_assets():
        template = dict(templates.get(asset, {"price": 0.0, "change_24h_pct": 0.0, "signal": "watch"}))
        template["asset"] = asset
        rows.append(template)
    return rows


def _derive_market_bias(change_24h_pct: float) -> str:
    if change_24h_pct >= 2.0:
        return "bullish"
    if change_24h_pct <= -2.0:
        return "defensive"
    return "balanced"


def _build_price_series(last_price: float, change_24h_pct: float) -> list[float]:
    price = max(float(last_price or 0.0), 0.01)
    pct = float(change_24h_pct or 0.0)
    open_price = price / (1.0 + (pct / 100.0)) if abs(pct) < 95.0 else price
    anchors = (0.22, 0.37, 0.31, 0.55, 0.71, 0.88, 0.81, 1.0)

    series: list[float] = []
    for idx, anchor in enumerate(anchors, start=1):
        blend = idx / len(anchors)
        drift = open_price + ((price - open_price) * blend)
        swing = price * 0.012 * (anchor - 0.5)
        if pct < 0:
            swing *= -1
        series.append(round(max(drift + swing, 0.01), 2))

    series[-1] = round(price, 2)
    return series


def _to_price(value: Any) -> float:
    try:
        price = round(float(value), 2)
    except (TypeError, ValueError):
        return 0.0
    return price if price > 0 else 0.0


def _snapshot_spread(bid: float, ask: float, provided: Any = None) -> float:
    spread = _to_price(provided)
    if spread > 0:
        return spread
    if bid > 0 and ask > 0 and ask >= bid:
        return round(ask - bid, 2)
    return 0.0


def _canonical_market_symbol(asset: str, venue: str) -> str:
    asset_symbol = str(asset or "").strip().upper()
    normalized_venue = str(venue or "coinbase").strip().lower()
    quote = "USD" if normalized_venue in {"coinbase", "kraken"} else "USDT"
    return f"{asset_symbol}/{quote}"


def _normalize_market_snapshot(asset: str, venue: str, payload: dict[str, Any], *, source: str) -> dict[str, Any]:
    bid = _to_price(payload.get("bid"))
    ask = _to_price(payload.get("ask"))
    last_price = _to_price(payload.get("last_price") or payload.get("price") or payload.get("last"))
    if last_price <= 0:
        last_price = _to_price((payload.get("quote") or {}).get("last")) if isinstance(payload.get("quote"), dict) else 0.0
    if last_price <= 0 and bid > 0 and ask > 0:
        last_price = round((bid + ask) / 2.0, 2)

    return {
        "asset": str(asset or "").strip().upper(),
        "exchange": str(payload.get("exchange") or payload.get("venue") or venue or "coinbase").strip().lower(),
        "last_price": last_price,
        "bid": bid,
        "ask": ask,
        "spread": _snapshot_spread(bid, ask, payload.get("spread")),
        "volume_24h": _to_price(payload.get("volume_24h") or payload.get("quote_vol")),
        "timestamp": str(payload.get("timestamp") or payload.get("ts") or payload.get("ts_ms") or ""),
        "source": source,
    }


def _load_local_market_snapshot(venue: str, symbol: str, *, asset: str) -> dict[str, Any] | None:
    try:
        from services.ws.last_price_provider import get_last_price
    except Exception:
        get_last_price = None

    if callable(get_last_price):
        try:
            quote = get_last_price(venue=venue, symbol=symbol, allow_stale=True)
        except Exception:
            quote = None
        if isinstance(quote, dict) and bool(quote.get("ok")):
            ws_payload: dict[str, Any] = {
                "venue": venue,
                "price": quote.get("price"),
                "timestamp": quote.get("age_ms"),
            }
            if isinstance(quote.get("quote"), dict):
                ws_payload.update(quote["quote"])
            snapshot = _normalize_market_snapshot(asset, venue, ws_payload, source="local_ws")
            if snapshot["last_price"] > 0:
                return snapshot

    try:
        from services.os.app_paths import data_dir, runtime_dir
        from storage.market_data_store_sqlite import SQLiteMarketDataStore
    except Exception:
        return None

    candidate_paths = [
        runtime_dir() / "market_data.sqlite",
        runtime_dir() / "market_ws.sqlite",
        data_dir() / "market_data.sqlite",
    ]
    seen_paths: set[str] = set()
    for path in candidate_paths:
        key = str(path)
        if key in seen_paths:
            continue
        seen_paths.add(key)
        try:
            rows = SQLiteMarketDataStore(path=path).get_latest_sync()
        except Exception:
            continue
        if not isinstance(rows, list):
            continue
        match = next(
            (
                row
                for row in rows
                if isinstance(row, dict)
                and str(row.get("venue") or row.get("exchange") or "").strip().lower() == venue
                and str(row.get("symbol") or "").strip().upper() == symbol.upper()
            ),
            None,
        )
        if isinstance(match, dict):
            snapshot = _normalize_market_snapshot(asset, venue, match, source="local_store")
            if snapshot["last_price"] > 0:
                return snapshot
    return None


def _get_market_snapshot(asset: str, *, exchange: str = "coinbase") -> dict[str, Any] | None:
    asset_symbol = str(asset or "").strip().upper()
    venue = str(exchange or "coinbase").strip().lower() or "coinbase"
    vd = _view_data()

    envelope = vd._fetch_envelope(f"/api/v1/market/{asset_symbol}/snapshot?exchange={venue}")
    if isinstance(envelope, dict) and envelope.get("status") == "success" and isinstance(envelope.get("data"), dict):
        snapshot = _normalize_market_snapshot(asset_symbol, venue, envelope["data"], source="api")
        if snapshot["last_price"] > 0:
            return snapshot

    local_symbol = _canonical_market_symbol(asset_symbol, venue)
    return vd._load_local_market_snapshot(venue, local_symbol, asset=asset_symbol)


def _load_local_ohlcv(venue: str, symbol: str, *, timeframe: str = "1h", limit: int = 24) -> list[list]:
    try:
        from services.market_data.ohlcv_fetcher import load_ohlcv
    except Exception:
        return []

    try:
        rows = load_ohlcv(venue, symbol, timeframe=timeframe, limit=limit)
    except Exception:
        return []
    return rows if isinstance(rows, list) else []


def _load_local_portfolio_snapshot(prices: dict[str, float]) -> dict[str, Any] | None:
    normalized_prices = {
        _normalize_asset_symbol(symbol): float(price or 0.0)
        for symbol, price in (prices or {}).items()
        if _normalize_asset_symbol(symbol)
    }

    try:
        from services.analytics.portfolio_mtm import build_portfolio_mtm
        from services.paper_trader.paper_state import PaperState  # canonical
    except Exception:
        build_portfolio_mtm = None
        PaperState = None

    local_positions: list[dict[str, Any]] = []
    cash_quote = 0.0
    realized_pnl = 0.0

    if callable(PaperState) and callable(build_portfolio_mtm):
        try:
            paper_state = PaperState()
            snapshot = paper_state.snapshot(limit=200)
        except Exception:
            snapshot = {}
        rows = snapshot.get("positions") if isinstance(snapshot.get("positions"), list) else []
        local_positions = [
            {
                "symbol": str(item.get("symbol") or ""),
                "qty": float(item.get("qty") or 0.0),
                "avg_price": float(item.get("avg_price") or 0.0),
                "realized_pnl": float(item.get("realized_pnl") or 0.0),
                "updated_ts": str(item.get("updated_ts") or ""),
                "venue": "paper",
            }
            for item in rows
            if isinstance(item, dict) and str(item.get("symbol") or "").strip()
        ]
        cash_quote = float(snapshot.get("cash_quote") or 0.0)
        realized_pnl = float(snapshot.get("realized_pnl") or 0.0)

    if not local_positions:
        try:
            from storage.pnl_store_sqlite import PnLStoreSQLite
        except Exception:
            PnLStoreSQLite = None
        if callable(PnLStoreSQLite) and callable(build_portfolio_mtm):
            try:
                pnl_store = PnLStoreSQLite()
                local_positions = [
                    {
                        "symbol": str(item.get("symbol") or ""),
                        "qty": float(item.get("qty") or 0.0),
                        "avg_price": float(item.get("avg_price") or 0.0),
                        "realized_pnl": 0.0,
                        "updated_ts": str(item.get("updated_ts") or ""),
                        "venue": str(item.get("venue") or "paper"),
                    }
                    for item in pnl_store.positions()
                    if isinstance(item, dict) and str(item.get("symbol") or "").strip()
                ]
                realized_pnl = float((pnl_store.get_today_realized() or {}).get("realized_pnl") or 0.0)
            except Exception:
                local_positions = []

    if not local_positions or not callable(build_portfolio_mtm):
        return None

    mtm = build_portfolio_mtm(
        cash_quote=cash_quote,
        positions=local_positions,
        prices=normalized_prices,
        realized_pnl=realized_pnl,
    )
    mtm_positions = mtm.get("positions") if isinstance(mtm.get("positions"), list) else []
    by_symbol = {str(item.get("symbol") or ""): item for item in local_positions if isinstance(item, dict)}
    enriched_positions: list[dict[str, Any]] = []
    for row in mtm_positions:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("symbol") or "")
        source_row = by_symbol.get(symbol, {})
        qty = float(row.get("qty") or 0.0)
        asset = _normalize_asset_symbol(symbol)
        enriched_positions.append(
            {
                "asset": asset or symbol,
                "symbol": symbol,
                "venue": str(source_row.get("venue") or "paper"),
                "side": "long" if qty >= 0 else "short",
                "size": abs(qty),
                "entry": float(row.get("avg_price") or source_row.get("avg_price") or 0.0),
                "mark": float(row.get("mark_price") or source_row.get("avg_price") or 0.0),
                "pnl": float(row.get("unrealized_pnl") or 0.0),
                "updated_ts": str(source_row.get("updated_ts") or ""),
            }
        )

    equity_quote = float(mtm.get("equity_quote") or 0.0)
    market_value = abs(float(mtm.get("market_value") or 0.0))
    return {
        "portfolio": {
            "total_value": equity_quote,
            "cash": float(mtm.get("cash_quote") or 0.0),
            "unrealized_pnl": float(mtm.get("unrealized_pnl") or 0.0),
            "realized_pnl_24h": float(mtm.get("realized_pnl") or 0.0),
            "exposure_used_pct": round((market_value / equity_quote) * 100.0, 1) if equity_quote > 0 else 0.0,
            "leverage": 1.0,
        },
        "positions": enriched_positions,
        "source": "local_portfolio",
    }


def _get_market_price_series(
    asset: str,
    last_price: float,
    change_24h_pct: float,
    *,
    exchange: str = "coinbase",
    interval: str = "1h",
    limit: int = 24,
) -> list[float]:
    asset_symbol = str(asset or "").strip().upper()
    venue = str(exchange or "coinbase").strip().lower() or "coinbase"
    candle_limit = max(int(limit or 24), 2)
    vd = _view_data()

    envelope = vd._fetch_envelope(
        f"/api/v1/market/{asset_symbol}/candles?exchange={venue}&interval={interval}&limit={candle_limit}"
    )
    if isinstance(envelope, dict) and envelope.get("status") == "success":
        data = envelope.get("data")
        candles = data.get("candles") if isinstance(data, dict) else None
        candle_series = _extract_close_series(candles)
        if candle_series:
            return candle_series

    quote = "USD" if venue in {"coinbase", "kraken"} else "USDT"
    local_symbol = f"{asset_symbol}/{quote}"
    local_series = _extract_close_series(
        vd._load_local_ohlcv(venue, local_symbol, timeframe=interval, limit=candle_limit)
    )
    if local_series:
        return local_series

    return _build_price_series(last_price, change_24h_pct)


def _build_watchlist_preview(summary: dict[str, Any], *, limit: int = 5) -> list[dict[str, Any]]:
    watchlist = summary.get("watchlist") if isinstance(summary.get("watchlist"), list) else []
    ranked_rows: list[tuple[float, int, dict[str, Any]]] = []

    for index, item in enumerate(watchlist):
        if not isinstance(item, dict):
            continue

        asset = str(item.get("asset") or "").strip().upper()
        if not asset:
            continue

        try:
            change_24h_pct = round(float(item.get("change_24h_pct") or 0.0), 2)
        except (TypeError, ValueError):
            change_24h_pct = 0.0

        row: dict[str, Any] = {
            "asset": asset,
            "price": _to_price(item.get("price")),
            "change_24h_pct": change_24h_pct,
            "signal": str(item.get("signal") or "watch"),
        }

        snapshot_source = str(item.get("snapshot_source") or "").strip()
        if snapshot_source:
            row["source"] = snapshot_source

        ranked_rows.append((abs(change_24h_pct), index, row))

    ranked_rows.sort(key=lambda entry: (-entry[0], entry[1]))
    return [row for _, _, row in ranked_rows[:limit]]



def _load_automation_operations_snapshot() -> dict[str, Any]:
    try:
        from dashboard.services.operator import get_operations_snapshot
    except Exception:
        return {}

    try:
        payload = get_operations_snapshot()
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


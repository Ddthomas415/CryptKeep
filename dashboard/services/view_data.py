from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

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


def _default_dashboard_summary() -> dict[str, Any]:
    return {
        "mode": "research_only",
        "execution_enabled": False,
        "approval_required": True,
        "risk_status": "safe",
        "kill_switch": False,
        "portfolio": {
            "total_value": 124850.0,
            "cash": 48120.0,
            "unrealized_pnl": 2145.0,
            "realized_pnl_24h": 812.0,
            "exposure_used_pct": 18.4,
            "leverage": 1.0,
        },
        "watchlist": [
            {"asset": "BTC", "price": 84250.12, "change_24h_pct": 2.4, "signal": "watch"},
            {"asset": "ETH", "price": 4421.34, "change_24h_pct": 1.3, "signal": "monitor"},
            {"asset": "SOL", "price": 187.42, "change_24h_pct": 6.9, "signal": "research"},
        ],
    }


def _default_recommendations() -> list[dict[str, Any]]:
    return [
        {
            "asset": "SOL",
            "signal": "buy",
            "confidence": 0.78,
            "summary": "Momentum + catalyst alignment",
            "evidence": "spot volume, ecosystem releases",
            "status": "pending_review",
        },
        {
            "asset": "BTC",
            "signal": "hold",
            "confidence": 0.66,
            "summary": "Range breakout not confirmed",
            "evidence": "weak continuation volume",
            "status": "watch",
        },
    ]


def _default_activity() -> list[str]:
    return [
        "Generated explanation for SOL",
        "Health check passed",
        "Listing logs refreshed",
        "Paper trade blocked by risk policy",
    ]


def _default_positions() -> list[dict[str, Any]]:
    return [
        {"asset": "BTC", "side": "long", "size": 0.12, "entry": 80120.0, "mark": 84250.12, "pnl": 495.6},
        {"asset": "SOL", "side": "long", "size": 45.0, "entry": 173.4, "mark": 187.42, "pnl": 630.9},
    ]


def _default_recent_fills() -> list[dict[str, Any]]:
    return [
        {"ts": "2026-03-11T12:20:00Z", "asset": "BTC", "side": "buy", "qty": 0.01, "price": 83500.0},
        {"ts": "2026-03-11T11:05:00Z", "asset": "ETH", "side": "sell", "qty": 0.3, "price": 4390.0},
    ]


def _default_settings_payload() -> dict[str, Any]:
    default_providers = {
        "coingecko": {
            "enabled": True,
            "api_key": "",
            "status": "ready",
            "role": "Crypto breadth",
            "last_sync": "Starter dataset",
        },
        "twelve_data": {
            "enabled": False,
            "api_key": "",
            "status": "optional",
            "role": "Cross-asset prices",
            "last_sync": "Configure key",
        },
        "alpha_vantage": {
            "enabled": False,
            "api_key": "",
            "status": "optional",
            "role": "Alternate cross-asset feed",
            "last_sync": "Configure key",
        },
        "trading_economics": {
            "enabled": False,
            "api_key": "",
            "status": "optional",
            "role": "Macro calendar",
            "last_sync": "Configure key",
        },
        "fred": {
            "enabled": True,
            "api_key": "",
            "status": "ready",
            "role": "Economic releases",
            "last_sync": "Public API",
        },
        "sec_filings": {
            "enabled": True,
            "api_key": "",
            "status": "ready",
            "role": "Filings and company facts",
            "last_sync": "Public API",
        },
        "smtp": {
            "enabled": False,
            "api_key": "",
            "status": "local",
            "role": "Email delivery",
            "last_sync": "Configure host",
        },
    }
    return {
        "general": {
            "timezone": "America/New_York",
            "default_currency": "USD",
            "startup_page": "/dashboard",
            "default_mode": "research_only",
            "watchlist_defaults": ["BTC", "ETH", "SOL"],
        },
        "notifications": {
            "email": False,
            "email_enabled": False,
            "email_address": "",
            "delivery_mode": "instant",
            "daily_digest_enabled": True,
            "weekly_digest_enabled": True,
            "confidence_threshold": 0.72,
            "opportunity_threshold": 0.7,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "06:00",
            "telegram": True,
            "discord": False,
            "webhook": False,
            "price_alerts": True,
            "news_alerts": True,
            "catalyst_alerts": True,
            "risk_alerts": True,
            "approval_requests": True,
            "categories": {
                "top_opportunities": True,
                "paper_trade_opened": True,
                "paper_trade_closed": True,
                "macro_events": True,
                "provider_failures": True,
                "daily_summary": True,
                "weekly_summary": True,
            },
        },
        "ai": {
            "explanation_length": "normal",
            "tone": "balanced",
            "show_evidence": True,
            "show_confidence": True,
            "include_archives": True,
            "include_onchain": True,
            "include_social": False,
            "allow_hypotheses": True,
            "evidence_verbosity": "standard",
            "provider_assisted_explanations": True,
            "autopilot_explanation_depth": "standard",
            "away_summary_mode": "prioritized",
        },
        "autopilot": {
            "autopilot_enabled": False,
            "scout_mode_enabled": True,
            "paper_trading_enabled": True,
            "learning_enabled": False,
            "scan_interval_minutes": 15,
            "candidate_limit": 12,
            "confidence_threshold": 0.72,
            "alert_threshold": 0.8,
            "default_market_universe": "core_watchlist",
            "enabled_asset_classes": ["crypto"],
            "exclusion_list": [],
            "digest_frequency": "daily",
        },
        "providers": default_providers,
        "paper_trading": {
            "enabled": True,
            "fee_bps": 7.0,
            "slippage_bps": 2.0,
            "approval_required": True,
            "max_position_size_usd": 5000.0,
            "max_daily_loss_pct": 2.0,
        },
        "security": {
            "session_timeout_minutes": 60,
            "secret_masking": True,
            "audit_export_allowed": True,
            "auth_scope": "local_private_only",
            "remote_access_requires_mfa": True,
            "outer_access_control": "",
        },
    }


def _default_explain_payload(asset: str = "SOL", question: str | None = None) -> dict[str, Any]:
    asset_symbol = str(asset or "SOL").strip().upper() or "SOL"
    resolved_question = question or f"Why is {asset_symbol} moving?"
    templates: dict[str, dict[str, Any]] = {
        "SOL": {
            "current_cause": "SOL is rising alongside increased spot volume and fresh ecosystem headlines.",
            "past_precedent": "Similar moves previously followed ecosystem upgrade narratives.",
            "future_catalyst": "A scheduled governance milestone may still matter.",
            "confidence": 0.78,
            "risk_note": "Research only. Execution disabled.",
            "execution_disabled": True,
            "evidence": [
                {
                    "id": "ev1",
                    "type": "market",
                    "source": "coinbase",
                    "timestamp": "2026-03-11T12:55:00Z",
                    "summary": "Volume expansion over the last hour.",
                    "relevance": 0.92,
                }
            ],
        },
        "BTC": {
            "current_cause": "BTC is firming as spot demand absorbs intraday pullbacks and range highs come back into view.",
            "past_precedent": "Comparable breakouts often held when U.S. session liquidity strengthened into the close.",
            "future_catalyst": "Macro prints later this week could decide whether continuation volume stays intact.",
            "confidence": 0.72,
            "risk_note": "Research only. Execution disabled.",
            "execution_disabled": True,
            "evidence": [
                {
                    "id": "ev_btc_1",
                    "type": "market",
                    "source": "coinbase",
                    "timestamp": "2026-03-11T12:45:00Z",
                    "summary": "Price held above intraday support while spot liquidity stayed firm.",
                    "relevance": 0.87,
                }
            ],
        },
        "ETH": {
            "current_cause": "ETH is trading with steadier follow-through as traders reprice upgrade narratives without a full momentum breakout.",
            "past_precedent": "Past pre-upgrade phases often rotated between compression and brief expansion before trend confirmation.",
            "future_catalyst": "Protocol milestone timing remains the next obvious catalyst for a larger directional move.",
            "confidence": 0.68,
            "risk_note": "Research only. Execution disabled.",
            "execution_disabled": True,
            "evidence": [
                {
                    "id": "ev_eth_1",
                    "type": "news",
                    "source": "newsapi",
                    "timestamp": "2026-03-11T11:20:00Z",
                    "summary": "Upgrade commentary is supporting interest, but conviction remains moderate.",
                    "relevance": 0.81,
                }
            ],
        },
    }
    selected = dict(templates.get(asset_symbol, templates["SOL"]))
    if asset_symbol not in templates:
        selected.update(
            {
                "current_cause": f"{asset_symbol} is moving with watchlist momentum and refreshed market attention.",
                "past_precedent": f"Prior {asset_symbol} expansions tended to follow liquidity improvement and renewed narrative flow.",
                "future_catalyst": f"The next catalyst for {asset_symbol} is whether follow-through volume confirms the move.",
                "confidence": 0.64,
                "evidence": [
                    {
                        "id": f"ev_{asset_symbol.lower()}_1",
                        "type": "market",
                        "source": "watchlist",
                        "timestamp": None,
                        "summary": f"{asset_symbol} is being tracked in the active market watchlist.",
                        "relevance": 0.75,
                    }
                ],
            }
        )

    return {
        "asset": asset_symbol,
        "question": resolved_question,
        "current_cause": str(selected.get("current_cause") or ""),
        "past_precedent": str(selected.get("past_precedent") or ""),
        "future_catalyst": str(selected.get("future_catalyst") or ""),
        "confidence": float(selected.get("confidence") or 0.0),
        "risk_note": selected.get("risk_note"),
        "execution_disabled": bool(selected.get("execution_disabled", True)),
        "evidence": list(selected.get("evidence") or []),
        "assistant_status": {
            "provider": "dashboard_fallback",
            "model": None,
            "fallback": True,
            "message": "Static asset-aware dashboard fallback used because no valid explain response was available.",
        },
    }


def _derive_market_bias(change_24h_pct: float) -> str:
    if change_24h_pct >= 2.0:
        return "bullish"
    if change_24h_pct <= -2.0:
        return "defensive"
    return "balanced"


def _derive_volume_trend(change_24h_pct: float) -> str:
    magnitude = abs(change_24h_pct)
    if magnitude >= 5.0:
        return "high"
    if magnitude >= 2.0:
        return "elevated"
    return "steady"


def _normalize_asset_symbol(value: Any) -> str:
    symbol = str(value or "").strip().upper()
    if not symbol:
        return ""
    if "/" in symbol:
        return symbol.split("/", 1)[0]
    if "-" in symbol:
        return symbol.split("-", 1)[0]
    for suffix in ("USDT", "USDC", "USD", "PERP"):
        if symbol.endswith(suffix) and len(symbol) > len(suffix):
            return symbol[: -len(suffix)]
    return symbol


def _normalize_signal_action(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    mapping = {
        "long": "buy",
        "short": "sell",
        "flat": "hold",
    }
    resolved = mapping.get(normalized, normalized)
    return resolved if resolved in {"buy", "sell", "hold", "watch", "research", "monitor"} else "hold"


def _normalize_signal_status(value: Any, *, action: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"pending_review", "pending review"}:
        return "pending_review"
    if normalized in {"approved", "accepted", "routed", "executed"}:
        return "approved"
    if normalized in {"rejected", "blocked", "dropped"}:
        return "rejected"
    if normalized in {"expired", "stale"}:
        return "expired"
    if normalized in {"watch", "monitor"}:
        return normalized
    if normalized in {"new", "queued", "received", "pending", "review", "reviewed", "normalized", "ingested", "scored"}:
        return "pending_review" if action in {"buy", "sell"} else "monitor"
    return "pending_review" if action in {"buy", "sell"} else "watch"


def _normalize_order_status(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"cancelled"}:
        return "canceled"
    if normalized in {"blocked", "dropped"}:
        return "rejected"
    if normalized in {"error"}:
        return "failed"
    return normalized


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


def _extract_close_series(rows: Any) -> list[float]:
    if not isinstance(rows, list):
        return []

    series: list[float] = []
    for row in rows:
        close_value: Any | None = None
        if isinstance(row, dict):
            close_value = row.get("close")
        elif isinstance(row, (list, tuple)) and len(row) >= 5:
            close_value = row[4]

        try:
            close_price = round(float(close_value), 2)
        except (TypeError, ValueError):
            continue

        if close_price > 0:
            series.append(close_price)
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

    envelope = _fetch_envelope(f"/api/v1/market/{asset_symbol}/snapshot?exchange={venue}")
    if isinstance(envelope, dict) and envelope.get("status") == "success" and isinstance(envelope.get("data"), dict):
        snapshot = _normalize_market_snapshot(asset_symbol, venue, envelope["data"], source="api")
        if snapshot["last_price"] > 0:
            return snapshot

    local_symbol = _canonical_market_symbol(asset_symbol, venue)
    return _load_local_market_snapshot(venue, local_symbol, asset=asset_symbol)


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
        from services.paper.paper_state import PaperState
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


def _load_local_recent_fills(limit: int = 20) -> list[dict[str, Any]]:
    normalized_limit = max(1, int(limit or 20))

    try:
        from storage.pnl_store_sqlite import PnLStoreSQLite
    except Exception:
        PnLStoreSQLite = None

    if callable(PnLStoreSQLite):
        try:
            fills = PnLStoreSQLite().last_fills(limit=normalized_limit)
        except Exception:
            fills = []
        if fills:
            return [
                {
                    "ts": str(item.get("ts") or ""),
                    "asset": _normalize_asset_symbol(item.get("symbol")),
                    "side": str(item.get("side") or ""),
                    "qty": float(item.get("qty") or 0.0),
                    "price": float(item.get("price") or 0.0),
                    "venue": str(item.get("venue") or ""),
                }
                for item in fills
                if isinstance(item, dict) and _normalize_asset_symbol(item.get("symbol"))
            ]

    try:
        from storage.live_trading_sqlite import LiveTradingSQLite
    except Exception:
        LiveTradingSQLite = None

    if callable(LiveTradingSQLite):
        try:
            fills = LiveTradingSQLite().list_fills(limit=normalized_limit)
        except Exception:
            fills = []
        if fills:
            return [
                {
                    "ts": str(item.get("ts") or ""),
                    "asset": _normalize_asset_symbol(item.get("symbol")),
                    "side": str(item.get("side") or ""),
                    "qty": float(item.get("qty") or 0.0),
                    "price": float(item.get("price") or 0.0),
                    "venue": str(item.get("venue") or ""),
                }
                for item in fills
                if isinstance(item, dict) and _normalize_asset_symbol(item.get("symbol"))
            ]

    try:
        from storage.execution_audit_reader import list_fills
    except Exception:
        list_fills = None

    if callable(list_fills):
        try:
            fills = list_fills(limit=normalized_limit)
        except Exception:
            fills = []
        if fills:
            return [
                {
                    "ts": str(item.get("ts") or item.get("ts_iso") or ""),
                    "asset": _normalize_asset_symbol(item.get("symbol")),
                    "side": str(item.get("side") or ""),
                    "qty": float(item.get("qty") or 0.0),
                    "price": float(item.get("price") or 0.0),
                    "venue": str(item.get("venue") or ""),
                }
                for item in fills
                if isinstance(item, dict) and _normalize_asset_symbol(item.get("symbol"))
            ]

    return []


def _load_local_pending_approvals(limit: int = 20) -> list[dict[str, Any]]:
    normalized_limit = max(1, int(limit or 20))
    allowed_statuses = {"queued", "pending", "pending_review", "review", "held", "new"}
    pending_rows: list[dict[str, Any]] = []

    def _collect(rows: Any, *, mode: str) -> None:
        if not isinstance(rows, list):
            return
        for item in rows:
            if not isinstance(item, dict):
                continue

            status = str(item.get("status") or "").strip().lower()
            if status not in allowed_statuses:
                continue

            asset = _normalize_asset_symbol(item.get("symbol") or item.get("asset"))
            if not asset:
                continue

            try:
                qty = float(item.get("qty") or 0.0)
            except (TypeError, ValueError):
                qty = 0.0

            try:
                limit_price = float(item.get("limit_price") or 0.0)
            except (TypeError, ValueError):
                limit_price = 0.0

            pending_rows.append(
                {
                    "id": str(item.get("intent_id") or item.get("id") or ""),
                    "asset": asset,
                    "side": str(item.get("side") or "hold").strip().lower(),
                    "qty": qty,
                    "risk_size_pct": float(item.get("risk_size_pct") or 0.0),
                    "venue": str(item.get("venue") or mode),
                    "mode": mode,
                    "order_type": str(item.get("order_type") or "market").strip().lower(),
                    "limit_price": limit_price if limit_price > 0 else None,
                    "status": status,
                    "created_ts": str(item.get("created_ts") or item.get("ts") or ""),
                    "source": str(item.get("source") or ""),
                }
            )

    try:
        from storage.intent_queue_sqlite import IntentQueueSQLite
    except Exception:
        IntentQueueSQLite = None

    if callable(IntentQueueSQLite):
        try:
            _collect(IntentQueueSQLite().list_intents(limit=normalized_limit, status=None), mode="paper")
        except Exception:
            pass

    try:
        from storage.live_intent_queue_sqlite import LiveIntentQueueSQLite
    except Exception:
        LiveIntentQueueSQLite = None

    if callable(LiveIntentQueueSQLite):
        try:
            _collect(LiveIntentQueueSQLite().list_intents(limit=normalized_limit, status=None), mode="live")
        except Exception:
            pass

    pending_rows.sort(key=lambda row: str(row.get("created_ts") or ""), reverse=True)
    return pending_rows[:normalized_limit]


def _load_local_open_orders(limit: int = 20) -> list[dict[str, Any]]:
    normalized_limit = max(1, int(limit or 20))
    allowed_statuses = {"new", "open", "submitted", "accepted", "working", "partially_filled"}
    open_rows: list[dict[str, Any]] = []

    def _collect(rows: Any, *, mode: str, source: str) -> None:
        if not isinstance(rows, list):
            return
        for item in rows:
            if not isinstance(item, dict):
                continue

            status = _normalize_order_status(item.get("status"))
            if status not in allowed_statuses:
                continue

            asset = _normalize_asset_symbol(item.get("symbol") or item.get("asset"))
            if not asset:
                continue

            try:
                qty = float(item.get("qty") or 0.0)
            except (TypeError, ValueError):
                qty = 0.0

            try:
                limit_price = float(item.get("limit_price") or 0.0)
            except (TypeError, ValueError):
                limit_price = 0.0

            open_rows.append(
                {
                    "id": str(
                        item.get("client_order_id")
                        or item.get("order_id")
                        or item.get("exchange_order_id")
                        or item.get("id")
                        or ""
                    ),
                    "asset": asset,
                    "side": str(item.get("side") or "hold").strip().lower(),
                    "qty": qty,
                    "venue": str(item.get("venue") or mode),
                    "mode": mode,
                    "order_type": str(item.get("order_type") or "market").strip().lower(),
                    "limit_price": limit_price if limit_price > 0 else None,
                    "status": status,
                    "created_ts": str(
                        item.get("created_ts")
                        or item.get("ts")
                        or item.get("ts_iso")
                        or item.get("submitted_ts")
                        or ""
                    ),
                    "exchange_order_id": str(item.get("exchange_order_id") or ""),
                    "source": source,
                }
            )

    try:
        from storage.live_trading_sqlite import LiveTradingSQLite
    except Exception:
        LiveTradingSQLite = None

    if callable(LiveTradingSQLite):
        try:
            _collect(LiveTradingSQLite().list_orders(limit=normalized_limit), mode="live", source="live_orders")
        except Exception:
            pass

    try:
        from storage.paper_trading_sqlite import PaperTradingSQLite
    except Exception:
        PaperTradingSQLite = None

    if callable(PaperTradingSQLite):
        try:
            _collect(PaperTradingSQLite().list_orders(limit=normalized_limit, status=None), mode="paper", source="paper_orders")
        except Exception:
            pass

    try:
        from storage.execution_audit_reader import list_orders
    except Exception:
        list_orders = None

    if callable(list_orders):
        try:
            _collect(list_orders(limit=normalized_limit), mode="audit", source="execution_audit")
        except Exception:
            pass

    open_rows.sort(key=lambda row: str(row.get("created_ts") or ""), reverse=True)
    return open_rows[:normalized_limit]


def _load_local_failed_orders(limit: int = 20) -> list[dict[str, Any]]:
    normalized_limit = max(1, int(limit or 20))
    allowed_statuses = {"rejected", "canceled", "failed"}
    failed_rows: list[dict[str, Any]] = []

    def _collect(rows: Any, *, mode: str, source: str) -> None:
        if not isinstance(rows, list):
            return
        for item in rows:
            if not isinstance(item, dict):
                continue

            status = _normalize_order_status(item.get("status"))
            if status not in allowed_statuses:
                continue

            asset = _normalize_asset_symbol(item.get("symbol") or item.get("asset"))
            if not asset:
                continue

            try:
                qty = float(item.get("qty") or item.get("amount") or 0.0)
            except (TypeError, ValueError):
                qty = 0.0

            try:
                limit_price = float(item.get("limit_price") or item.get("price") or 0.0)
            except (TypeError, ValueError):
                limit_price = 0.0

            failed_rows.append(
                {
                    "id": str(
                        item.get("client_order_id")
                        or item.get("order_id")
                        or item.get("intent_id")
                        or item.get("exchange_order_id")
                        or item.get("id")
                        or ""
                    ),
                    "asset": asset,
                    "side": str(item.get("side") or "hold").strip().lower(),
                    "qty": qty,
                    "venue": str(item.get("venue") or mode),
                    "mode": mode,
                    "order_type": str(item.get("order_type") or "market").strip().lower(),
                    "limit_price": limit_price if limit_price > 0 else None,
                    "status": status,
                    "created_ts": str(
                        item.get("updated_ts")
                        or item.get("created_ts")
                        or item.get("ts")
                        or item.get("ts_iso")
                        or item.get("submitted_ts")
                        or ""
                    ),
                    "exchange_order_id": str(item.get("exchange_order_id") or item.get("linked_order_id") or ""),
                    "reason": str(
                        item.get("last_error")
                        or item.get("reject_reason")
                        or item.get("error")
                        or ""
                    ),
                    "source": source,
                }
            )

    try:
        from storage.live_trading_sqlite import LiveTradingSQLite
    except Exception:
        LiveTradingSQLite = None

    if callable(LiveTradingSQLite):
        try:
            _collect(LiveTradingSQLite().list_orders(limit=normalized_limit), mode="live", source="live_orders")
        except Exception:
            pass

    try:
        from storage.paper_trading_sqlite import PaperTradingSQLite
    except Exception:
        PaperTradingSQLite = None

    if callable(PaperTradingSQLite):
        try:
            _collect(PaperTradingSQLite().list_orders(limit=normalized_limit, status=None), mode="paper", source="paper_orders")
        except Exception:
            pass

    try:
        from storage.live_intent_queue_sqlite import LiveIntentQueueSQLite
    except Exception:
        LiveIntentQueueSQLite = None

    if callable(LiveIntentQueueSQLite):
        try:
            _collect(LiveIntentQueueSQLite().list_intents(limit=normalized_limit, status=None), mode="live", source="live_intents")
        except Exception:
            pass

    try:
        from storage.intent_queue_sqlite import IntentQueueSQLite
    except Exception:
        IntentQueueSQLite = None

    if callable(IntentQueueSQLite):
        try:
            _collect(IntentQueueSQLite().list_intents(limit=normalized_limit, status=None), mode="paper", source="paper_intents")
        except Exception:
            pass

    try:
        from storage.execution_audit_reader import list_orders
    except Exception:
        list_orders = None

    if callable(list_orders):
        try:
            _collect(list_orders(limit=normalized_limit), mode="audit", source="execution_audit")
        except Exception:
            pass

    failed_rows.sort(key=lambda row: str(row.get("created_ts") or ""), reverse=True)
    return failed_rows[:normalized_limit]


def _dedupe_recommendation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        asset = str(row.get("asset") or "").strip().upper()
        if not asset or asset in seen:
            continue
        seen.add(asset)
        deduped.append(row)
    return deduped


def _load_current_regime() -> str:
    try:
        from storage.ops_signal_store_sqlite import OpsSignalStoreSQLite
    except Exception:
        OpsSignalStoreSQLite = None

    if callable(OpsSignalStoreSQLite):
        try:
            payload = OpsSignalStoreSQLite().latest_risk_gate()
        except Exception:
            payload = None
        if isinstance(payload, dict):
            regime = str(payload.get("regime") or "").strip()
            if regime:
                return regime
    return ""


def _load_signal_reliability(asset: str) -> dict[str, Any] | None:
    normalized_asset = _normalize_asset_symbol(asset)
    if not normalized_asset:
        return None

    try:
        from storage.signal_reliability_sqlite import SignalReliabilitySQLite
    except Exception:
        SignalReliabilitySQLite = None

    if not callable(SignalReliabilitySQLite):
        return None

    try:
        rows = SignalReliabilitySQLite().list(limit=100)
    except Exception:
        return None

    for row in rows:
        if not isinstance(row, dict):
            continue
        if _normalize_asset_symbol(row.get("symbol")) == normalized_asset:
            return row
    return None


def _enrich_signal_row(
    item: dict[str, Any] | None,
    *,
    market_row: dict[str, Any] | None = None,
    current_regime: str = "",
    risk_status: str = "",
) -> dict[str, Any]:
    payload = dict(item) if isinstance(item, dict) else {}
    asset = str(payload.get("asset") or "").strip().upper()
    intelligence = build_opportunity_snapshot(
        signal_row=payload,
        market_row=market_row if isinstance(market_row, dict) else {},
        reliability=_load_signal_reliability(asset),
        summary={"risk_status": risk_status, "current_regime": current_regime},
    )
    payload.update(
        {
            "regime": str(intelligence.get("regime") or ""),
            "regime_fit": float(intelligence.get("regime_fit") or 0.0),
            "tradeability": float(intelligence.get("tradeability") or 0.0),
            "setup_quality": float(intelligence.get("setup_quality") or 0.0),
            "expected_return": float(intelligence.get("expected_return") or 0.0),
            "risk_penalty": float(intelligence.get("risk_penalty") or 0.0),
            "opportunity_score": float(intelligence.get("opportunity_score") or 0.0),
            "category": str(intelligence.get("category") or ""),
        }
    )
    return payload


def _load_local_recommendations(limit: int = 20) -> list[dict[str, Any]]:
    normalized_limit = max(1, int(limit or 20))

    try:
        from storage.signal_inbox_sqlite import SignalInboxSQLite
    except Exception:
        SignalInboxSQLite = None

    if callable(SignalInboxSQLite):
        try:
            inbox_rows = SignalInboxSQLite().list_signals(limit=normalized_limit)
        except Exception:
            inbox_rows = []
        if inbox_rows:
            mapped = []
            for item in inbox_rows:
                if not isinstance(item, dict):
                    continue
                asset = _normalize_asset_symbol(item.get("symbol"))
                action = _normalize_signal_action(item.get("action"))
                if not asset:
                    continue
                note = str(item.get("notes") or "").strip()
                source = str(item.get("source") or "").strip()
                author = str(item.get("author") or "").strip()
                mapped.append(
                    {
                        "id": str(item.get("signal_id") or f"inbox_{asset.lower()}"),
                        "asset": asset,
                        "signal": action,
                        "confidence": float(item.get("confidence") or 0.0),
                        "summary": note or f"Signal inbox update from {author or source or 'local source'}.",
                        "evidence": source or author or "signal_inbox",
                        "status": _normalize_signal_status(item.get("status"), action=action),
                    }
                )
            deduped = _dedupe_recommendation_rows(mapped)
            if deduped:
                return deduped

    try:
        from storage.evidence_signals_sqlite import EvidenceSignalsSQLite
    except Exception:
        EvidenceSignalsSQLite = None

    if callable(EvidenceSignalsSQLite):
        try:
            evidence_rows = EvidenceSignalsSQLite().recent_signals(limit=normalized_limit)
        except Exception:
            evidence_rows = []
        if evidence_rows:
            mapped = []
            for item in evidence_rows:
                if not isinstance(item, dict):
                    continue
                asset = _normalize_asset_symbol(item.get("symbol"))
                action = _normalize_signal_action(item.get("side"))
                if not asset:
                    continue
                note = str(item.get("notes") or "").strip()
                source_id = str(item.get("source_id") or "").strip()
                mapped.append(
                    {
                        "id": str(item.get("signal_id") or f"evidence_{asset.lower()}"),
                        "asset": asset,
                        "signal": action,
                        "confidence": float(item.get("confidence") or 0.0),
                        "summary": note or f"Evidence signal from {source_id or 'local evidence store'}.",
                        "evidence": source_id or "evidence_signals",
                        "status": _normalize_signal_status(item.get("status"), action=action),
                    }
                )
            deduped = _dedupe_recommendation_rows(mapped)
            if deduped:
                return deduped

    return []


def _apply_local_execution_state_to_recommendations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized_rows = [dict(row) for row in rows if isinstance(row, dict)]
    if not normalized_rows:
        return []

    asset_count = len(normalized_rows)
    pending_rows = _load_local_pending_approvals(limit=max(20, asset_count * 4))
    fill_rows = _load_local_recent_fills(limit=max(20, asset_count * 4))

    latest_pending_by_asset: dict[str, dict[str, Any]] = {}
    for row in pending_rows:
        if not isinstance(row, dict):
            continue
        asset = _normalize_asset_symbol(row.get("asset"))
        if asset and asset not in latest_pending_by_asset:
            latest_pending_by_asset[asset] = row

    latest_fill_by_asset: dict[str, dict[str, Any]] = {}
    for row in fill_rows:
        if not isinstance(row, dict):
            continue
        asset = _normalize_asset_symbol(row.get("asset"))
        if asset and asset not in latest_fill_by_asset:
            latest_fill_by_asset[asset] = row

    enriched_rows: list[dict[str, Any]] = []
    for row in normalized_rows:
        asset = _normalize_asset_symbol(row.get("asset"))
        enriched = dict(row)
        pending = latest_pending_by_asset.get(asset)
        latest_fill = latest_fill_by_asset.get(asset)

        if isinstance(latest_fill, dict):
            side = str(latest_fill.get("side") or "").strip().lower()
            qty = float(latest_fill.get("qty") or 0.0)
            price = float(latest_fill.get("price") or 0.0)
            venue = str(latest_fill.get("venue") or "").strip()
            enriched["status"] = "executed"
            enriched["execution_state"] = f"{side.upper()} {qty:g} @ {price:,.2f}" if qty and price else "Filled"
            if venue:
                enriched["execution_state"] = f"{enriched['execution_state']} · {venue}"
        elif isinstance(pending, dict):
            mode = str(pending.get("mode") or "").strip()
            venue = str(pending.get("venue") or "").strip()
            order_type = str(pending.get("order_type") or "").strip()
            enriched["status"] = "queued"
            parts = [part for part in (mode.upper() if mode else "", venue, order_type) if part]
            enriched["execution_state"] = " · ".join(parts) or "Queued"

        enriched_rows.append(enriched)

    return enriched_rows


def _resolve_execution_db_path() -> str:
    cfg = deep_merge(DEFAULT_CFG, load_user_yaml() or {})
    execution_cfg = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {}
    return str(execution_cfg.get("db_path") or DEFAULT_CFG["execution"]["db_path"]).strip()


def _load_local_recent_activity(limit: int = 6) -> list[str]:
    normalized_limit = max(1, int(limit or 6))

    def _dedupe_lines(lines: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for raw in lines:
            line = str(raw or "").strip()
            if not line or line in seen:
                continue
            seen.add(line)
            out.append(line)
            if len(out) >= normalized_limit:
                break
        return out

    try:
        from storage.ops_event_store_sqlite import OpsEventStore
    except Exception:
        OpsEventStore = None

    if callable(OpsEventStore):
        try:
            rows = OpsEventStore(exec_db=_resolve_execution_db_path()).list_recent(limit=normalized_limit)
        except Exception:
            rows = []
        if rows:
            ops_lines = [
                str(item.get("message") or item.get("event_type") or "").strip()
                for item in rows
                if isinstance(item, dict)
            ]
            deduped_ops = _dedupe_lines(ops_lines)
            if deduped_ops:
                return deduped_ops

    try:
        from services.execution.intent_audit import recent_intent_events
    except Exception:
        recent_intent_events = None

    if callable(recent_intent_events):
        try:
            rows = recent_intent_events(limit=normalized_limit)
        except Exception:
            rows = []
        if rows:
            intent_lines: list[str] = []
            for item in rows:
                if not isinstance(item, dict):
                    continue
                payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
                event = str(payload.get("event") or "").strip().replace("_", " ")
                status = str(payload.get("status") or item.get("status") or "").strip()
                asset = _normalize_asset_symbol(item.get("symbol"))
                parts = [part for part in (event.title() if event else "", asset, status) if part]
                line = " · ".join(parts) or str(item.get("summary") or "").strip()
                if line:
                    intent_lines.append(line)
            deduped_intents = _dedupe_lines(intent_lines)
            if deduped_intents:
                return deduped_intents

    try:
        from storage.decision_audit_store_sqlite import DecisionAuditStoreSQLite
    except Exception:
        DecisionAuditStoreSQLite = None

    if callable(DecisionAuditStoreSQLite):
        try:
            rows = DecisionAuditStoreSQLite().last_decisions(limit=normalized_limit)
        except Exception:
            rows = []
        if rows:
            decision_lines: list[str] = []
            for item in rows:
                if not isinstance(item, dict):
                    continue
                asset = _normalize_asset_symbol(item.get("symbol"))
                side = _normalize_signal_action(item.get("side")).upper()
                safety_reason = str(item.get("safety_reason") or "").strip()
                price = float(item.get("price") or 0.0)
                line = f"Decision {side or 'HOLD'} {asset}".strip()
                if price > 0:
                    line = f"{line} @ {price:,.2f}"
                if safety_reason:
                    line = f"{line} ({safety_reason})"
                decision_lines.append(line)
            deduped_decisions = _dedupe_lines(decision_lines)
            if deduped_decisions:
                return deduped_decisions

    return []


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

    envelope = _fetch_envelope(
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
        _load_local_ohlcv(venue, local_symbol, timeframe=interval, limit=candle_limit)
    )
    if local_series:
        return local_series

    return _build_price_series(last_price, change_24h_pct)


def _asset_priority(signal: str) -> int:
    normalized = str(signal or "").strip().lower()
    order = {
        "buy": 0,
        "research": 0,
        "monitor": 1,
        "hold": 1,
        "watch": 2,
    }
    return order.get(normalized, 3)


def _explain_mentions_foreign_asset(payload: dict[str, Any], asset_symbol: str) -> bool:
    text = " ".join(
        str(payload.get(key) or "")
        for key in ("current_cause", "past_precedent", "future_catalyst")
    ).upper()
    known_assets = {"BTC", "ETH", "SOL"}
    return any(symbol in text for symbol in known_assets if symbol != asset_symbol)


def _read_mock_envelope(filename: str) -> dict[str, Any] | None:
    path = REPO_ROOT / "crypto-trading-ai" / "shared" / "mock-data" / filename
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _request_envelope_from_base(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    url = f"{base_url}{path}"
    body: bytes | None = None
    headers = {
        "Accept": "application/json",
        "User-Agent": "CryptKeepDashboard/1.0",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if base_url.rstrip("/") == PHASE1_ORCHESTRATOR_URL and PHASE1_SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {PHASE1_SERVICE_TOKEN}"
    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (TimeoutError, OSError, ValueError, urllib.error.URLError):
        return None


def _request_envelope(path: str, *, method: str = "GET", payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    return _request_envelope_from_base(API_BASE_URL, path, method=method, payload=payload)


def _fetch_envelope(path: str) -> dict[str, Any] | None:
    return _request_envelope(path, method="GET")


def _load_local_kill_switch_state() -> bool | None:
    try:
        from services.admin.kill_switch import KILL_PATH, get_state
    except Exception:
        return None

    if not Path(KILL_PATH).exists():
        return None

    try:
        payload = get_state()
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return bool(payload.get("armed", True))


def _load_local_system_guard_state() -> dict[str, Any] | None:
    try:
        from services.admin.system_guard import GUARD_PATH, get_state
    except Exception:
        return None

    if not Path(GUARD_PATH).exists():
        return None

    try:
        payload = get_state(fail_closed=True)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    state = str(payload.get("state") or "").strip().upper()
    if not state:
        return None
    return {**payload, "state": state}


def _load_local_connections_summary() -> dict[str, Any] | None:
    health_rows: list[dict[str, Any]] = []
    ws_rows: list[dict[str, Any]] = []

    try:
        from services.admin.health import list_health
    except Exception:
        list_health = None

    if callable(list_health):
        try:
            raw_health = list_health()
        except Exception:
            raw_health = []
        health_rows = [item for item in raw_health if isinstance(item, dict)]

    try:
        from storage.ws_status_sqlite import WSStatusSQLite
    except Exception:
        WSStatusSQLite = None

    if callable(WSStatusSQLite):
        try:
            raw_ws = WSStatusSQLite().recent_events(limit=200)
        except Exception:
            raw_ws = []
        ws_rows = [item for item in raw_ws if isinstance(item, dict)]

    if not health_rows and not ws_rows:
        return None

    running_statuses = {"RUNNING", "OK", "HEALTHY", "STARTING"}
    failed_statuses = {"ERROR", "FAILED", "UNHEALTHY", "DEGRADED", "STOPPED"}

    provider_states: dict[str, str] = {}
    last_sync = ""
    for item in health_rows:
        service = str(item.get("service") or "").strip()
        status = str(item.get("status") or "").strip().upper()
        ts = str(item.get("ts") or "").strip()
        if service:
            provider_states[service] = status
        if ts and ts > last_sync:
            last_sync = ts

    latest_ws_by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for item in ws_rows:
        exchange = str(item.get("exchange") or "").strip().lower()
        symbol = str(item.get("symbol") or "").strip().upper()
        if not exchange or not symbol:
            continue
        latest_ws_by_pair.setdefault((exchange, symbol), item)
        ts = str(item.get("updated_ts") or "").strip()
        if ts and ts > last_sync:
            last_sync = ts

    exchange_states: dict[str, list[str]] = {}
    for item in latest_ws_by_pair.values():
        exchange = str(item.get("exchange") or "").strip().lower()
        status = str(item.get("status") or "").strip().lower()
        if exchange:
            exchange_states.setdefault(exchange, []).append(status)

    connected_exchanges = sum(1 for states in exchange_states.values() if any(state == "ok" for state in states))
    failed_exchanges = sum(1 for states in exchange_states.values() if states and all(state == "error" for state in states))
    connected_providers = sum(1 for status in provider_states.values() if status in running_statuses)
    failed_providers = sum(1 for status in provider_states.values() if status in failed_statuses)

    return {
        "connected_exchanges": int(connected_exchanges),
        "connected_providers": int(connected_providers if provider_states else connected_exchanges),
        "failed": int(failed_providers if provider_states else failed_exchanges),
        "last_sync": last_sync or None,
    }


def _apply_local_summary_overrides(summary: dict[str, Any]) -> dict[str, Any]:
    merged = dict(summary or {})
    portfolio = merged.get("portfolio") if isinstance(merged.get("portfolio"), dict) else {}
    watchlist = merged.get("watchlist") if isinstance(merged.get("watchlist"), list) else []

    watch_prices = {
        str(item.get("asset") or ""): float(item.get("price") or 0.0)
        for item in watchlist
        if isinstance(item, dict) and str(item.get("asset") or "").strip()
    }
    local_snapshot = _load_local_portfolio_snapshot(watch_prices)
    if isinstance(local_snapshot, dict):
        local_portfolio = local_snapshot.get("portfolio") if isinstance(local_snapshot.get("portfolio"), dict) else {}
        if local_portfolio:
            merged["portfolio"] = {**portfolio, **local_portfolio}

    normalized_watchlist: list[dict[str, Any]] = [
        dict(item)
        for item in watchlist
        if isinstance(item, dict) and str(item.get("asset") or "").strip()
    ]
    if not normalized_watchlist:
        settings = get_settings_view()
        general = settings.get("general") if isinstance(settings.get("general"), dict) else {}
        configured_assets = [
            _normalize_asset_symbol(item)
            for item in (general.get("watchlist_defaults") if isinstance(general.get("watchlist_defaults"), list) else [])
        ]
        configured_assets = [asset for asset in configured_assets if asset]
        default_rows = {
            str(item.get("asset") or "").strip().upper(): dict(item)
            for item in _default_dashboard_summary()["watchlist"]
            if isinstance(item, dict) and str(item.get("asset") or "").strip()
        }
        normalized_watchlist = [
            dict(default_rows.get(asset) or {"asset": asset, "price": 0.0, "change_24h_pct": 0.0, "signal": "watch"})
            for asset in configured_assets
        ]

    if normalized_watchlist:
        updated_watchlist: list[dict[str, Any]] = []
        for item in normalized_watchlist:
            asset = _normalize_asset_symbol(item.get("asset"))
            if not asset:
                continue
            row = dict(item)
            row["asset"] = asset
            snapshot = _get_market_snapshot(asset) or {}
            if float(snapshot.get("last_price") or 0.0) > 0:
                row["price"] = float(snapshot["last_price"])
            if snapshot:
                row["exchange"] = str(snapshot.get("exchange") or row.get("exchange") or "coinbase")
                row["snapshot_source"] = str(snapshot.get("source") or row.get("snapshot_source") or "watchlist")
                if float(snapshot.get("volume_24h") or 0.0) > 0:
                    row["volume_24h"] = float(snapshot["volume_24h"])
            updated_watchlist.append(row)
        if updated_watchlist:
            merged["watchlist"] = updated_watchlist

    raw_cfg = load_user_yaml()
    if isinstance(raw_cfg, dict) and raw_cfg:
        raw_execution = raw_cfg.get("execution") if isinstance(raw_cfg.get("execution"), dict) else {}
        raw_dashboard_ui = raw_cfg.get("dashboard_ui") if isinstance(raw_cfg.get("dashboard_ui"), dict) else {}
        raw_automation = raw_dashboard_ui.get("automation") if isinstance(raw_dashboard_ui.get("automation"), dict) else {}

        if "default_mode" in raw_automation:
            merged["mode"] = str(raw_automation.get("default_mode") or merged.get("mode") or "research_only")
        if "enabled" in raw_automation:
            merged["execution_enabled"] = bool(raw_automation.get("enabled"))
        elif raw_execution.get("live_enabled") is True:
            merged["execution_enabled"] = True
        if "approval_required_for_live" in raw_automation:
            merged["approval_required"] = bool(raw_automation.get("approval_required_for_live"))

    local_kill_switch = _load_local_kill_switch_state()
    if local_kill_switch is not None:
        merged["kill_switch"] = local_kill_switch

    connections_payload = merged.get("connections") if isinstance(merged.get("connections"), dict) else {}
    local_connections = _load_local_connections_summary()
    if isinstance(local_connections, dict):
        merged["connections"] = {**connections_payload, **local_connections}

    portfolio_payload = merged.get("portfolio") if isinstance(merged.get("portfolio"), dict) else {}
    risk_overlay = _load_local_risk_overlay(
        portfolio_total_value=float(portfolio_payload.get("total_value") or 0.0)
    )
    if isinstance(risk_overlay, dict):
        risk_status = str(risk_overlay.get("risk_status") or "").strip()
        if risk_status:
            merged["risk_status"] = risk_status
        if isinstance(risk_overlay.get("active_warnings"), list):
            merged["active_warnings"] = list(risk_overlay.get("active_warnings") or [])
        if risk_overlay.get("blocked_trades_count") is not None:
            merged["blocked_trades_count"] = int(risk_overlay.get("blocked_trades_count") or 0)

        portfolio_updates: dict[str, Any] = {}
        exposure_used_pct = float(risk_overlay.get("exposure_used_pct") or 0.0)
        leverage = float(risk_overlay.get("leverage") or 0.0)
        drawdown_today_pct = float(risk_overlay.get("drawdown_today_pct") or 0.0)
        drawdown_week_pct = float(risk_overlay.get("drawdown_week_pct") or 0.0)
        if exposure_used_pct > 0.0:
            portfolio_updates["exposure_used_pct"] = exposure_used_pct
        if leverage > 0.0:
            portfolio_updates["leverage"] = leverage
        if drawdown_today_pct > 0.0:
            merged["drawdown_today_pct"] = drawdown_today_pct
        if drawdown_week_pct > 0.0:
            merged["drawdown_week_pct"] = drawdown_week_pct
        if portfolio_updates:
            merged["portfolio"] = {**portfolio_payload, **portfolio_updates}

    local_system_guard = _load_local_system_guard_state()
    if isinstance(local_system_guard, dict):
        state = str(local_system_guard.get("state") or "").strip().upper()
        if state:
            merged["system_guard_state"] = state.lower()
            warnings = merged.get("active_warnings") if isinstance(merged.get("active_warnings"), list) else []
            updated_warnings = [str(item) for item in warnings if str(item).strip()]
            if state == "HALTING":
                merged["risk_status"] = "caution"
                updated_warnings.append("system_guard_halting")
            elif state == "HALTED":
                merged["risk_status"] = "danger"
                updated_warnings.append("system_guard_halted")
            if updated_warnings:
                deduped: list[str] = []
                seen: set[str] = set()
                for item in updated_warnings:
                    if item in seen:
                        continue
                    seen.add(item)
                    deduped.append(item)
                merged["active_warnings"] = deduped

    return merged


def get_dashboard_summary() -> dict[str, Any]:
    envelope = _fetch_envelope("/api/v1/dashboard/summary")
    if isinstance(envelope, dict) and envelope.get("status") == "success" and isinstance(envelope.get("data"), dict):
        return _apply_local_summary_overrides(dict(envelope["data"]))

    mock = _read_mock_envelope("dashboard.json")
    if isinstance(mock, dict) and isinstance(mock.get("data"), dict):
        return _apply_local_summary_overrides(dict(mock["data"]))
    return _apply_local_summary_overrides(_default_dashboard_summary())


def _gate_state_to_risk_status(gate_state: Any, *, kill_switch_on: bool = False) -> str:
    if kill_switch_on:
        return "danger"
    normalized = str(gate_state or "").strip().upper()
    if normalized == "ALLOW_TRADING":
        return "safe"
    if normalized == "ALLOW_ONLY_REDUCTIONS":
        return "caution"
    if normalized in {"HALT_NEW_POSITIONS", "FULL_STOP"}:
        return "danger"
    return "safe"


def _load_local_risk_overlay(*, portfolio_total_value: float = 0.0) -> dict[str, Any] | None:
    raw_signal: dict[str, Any] | None = None
    risk_gate: dict[str, Any] | None = None
    blocked_rows: list[dict[str, Any]] = []

    try:
        from storage.ops_signal_store_sqlite import OpsSignalStoreSQLite
    except Exception:
        OpsSignalStoreSQLite = None

    if callable(OpsSignalStoreSQLite):
        try:
            store = OpsSignalStoreSQLite()
            raw_signal = store.latest_raw_signal()
            risk_gate = store.latest_risk_gate()
        except Exception:
            raw_signal = None
            risk_gate = None

    try:
        from storage.risk_blocks_store_sqlite import RiskBlocksStoreSQLite
    except Exception:
        RiskBlocksStoreSQLite = None

    if callable(RiskBlocksStoreSQLite):
        try:
            blocked_rows = RiskBlocksStoreSQLite().last_n(limit=20)
        except Exception:
            blocked_rows = []

    if not isinstance(raw_signal, dict) and not isinstance(risk_gate, dict) and not blocked_rows:
        return None

    kill_switch_on = bool(_load_local_kill_switch_state())
    exposure_usd = float((raw_signal or {}).get("exposure_usd") or 0.0)
    leverage = float((raw_signal or {}).get("leverage") or 0.0)
    drawdown_pct = float((raw_signal or {}).get("drawdown_pct") or 0.0)
    exposure_used_pct = 0.0
    if portfolio_total_value > 0.0 and exposure_usd > 0.0:
        exposure_used_pct = round((exposure_usd / portfolio_total_value) * 100.0, 2)

    warnings: list[str] = []
    for item in ((risk_gate or {}).get("hazards") or []):
        text = str(item or "").strip()
        if text:
            warnings.append(text)
    for item in ((risk_gate or {}).get("reasons") or []):
        text = str(item or "").strip()
        if text:
            warnings.append(text)
    for item in blocked_rows:
        if not isinstance(item, dict):
            continue
        gate = str(item.get("gate") or "").strip()
        reason = str(item.get("reason") or "").strip()
        text = gate or reason
        if text:
            warnings.append(text)
    if kill_switch_on:
        warnings.append("kill_switch_armed")

    deduped_warnings: list[str] = []
    seen_warnings: set[str] = set()
    for item in warnings:
        if item in seen_warnings:
            continue
        seen_warnings.add(item)
        deduped_warnings.append(item)

    return {
        "risk_status": _gate_state_to_risk_status((risk_gate or {}).get("gate_state"), kill_switch_on=kill_switch_on),
        "blocked_trades_count": len(blocked_rows),
        "active_warnings": deduped_warnings,
        "drawdown_today_pct": round(drawdown_pct, 2),
        "drawdown_week_pct": round(drawdown_pct, 2),
        "exposure_used_pct": exposure_used_pct,
        "leverage": round(leverage, 2),
    }


def get_research_explain(asset: str, question: str | None = None) -> dict[str, Any]:
    asset_symbol = str(asset or "").strip().upper() or "SOL"
    resolved_question = question or f"Why is {asset_symbol} moving?"
    fallback = _default_explain_payload(asset_symbol, resolved_question)

    def _normalize_explain(
        envelope: dict[str, Any] | None,
        *,
        default_provider: str,
        default_fallback: bool,
    ) -> dict[str, Any] | None:
        if isinstance(envelope, dict) and isinstance(envelope.get("data"), dict):
            data = dict(envelope["data"])
        elif isinstance(envelope, dict):
            data = dict(envelope)
        else:
            return None

        if not any(key in data for key in ("current_cause", "past_precedent", "future_catalyst")):
            return None
        if _explain_mentions_foreign_asset(data, asset_symbol):
            return None

        data["asset"] = asset_symbol
        data["question"] = resolved_question
        assistant_status = data.get("assistant_status") if isinstance(data.get("assistant_status"), dict) else {}
        assistant_message = str(assistant_status.get("message") or "").strip()
        data["assistant_status"] = {
            "provider": str(assistant_status.get("provider") or default_provider),
            "model": assistant_status.get("model"),
            "fallback": bool(assistant_status.get("fallback")) if "fallback" in assistant_status else default_fallback,
            "message": assistant_message or None,
        }
        return data

    primary_envelope = _request_envelope(
        "/api/v1/research/explain",
        method="POST",
        payload={"asset": asset_symbol, "question": resolved_question},
    )
    primary = _normalize_explain(
        primary_envelope,
        default_provider="backend_api",
        default_fallback=False,
    )
    if primary is not None:
        return primary

    phase1 = _normalize_explain(
        _request_envelope_from_base(
            PHASE1_ORCHESTRATOR_URL,
            "/v1/explain",
            method="POST",
            payload={"asset": asset_symbol, "question": resolved_question, "lookback_minutes": 60},
        ),
        default_provider="phase1_copilot",
        default_fallback=False,
    )
    if phase1 is not None:
        return phase1

    mock = _read_mock_envelope("explain-sol.json")
    if asset_symbol == "SOL" and isinstance(mock, dict) and isinstance(mock.get("data"), dict):
        data = dict(mock["data"])
        data["asset"] = asset_symbol
        data["question"] = resolved_question
        data["assistant_status"] = {
            "provider": "dashboard_fallback",
            "model": None,
            "fallback": True,
            "message": "Static asset-aware dashboard fallback used because no valid explain response was available.",
        }
        return data

    return fallback


def get_markets_view(selected_asset: str | None = None) -> dict[str, Any]:
    summary = get_dashboard_summary()
    recommendations = get_recommendations()
    current_regime = _load_current_regime() or str(summary.get("risk_status") or "")
    risk_status = str(summary.get("risk_status") or "")

    recommendation_map: dict[str, dict[str, Any]] = {}
    for item in recommendations:
        if not isinstance(item, dict):
            continue
        asset = str(item.get("asset") or "").strip().upper()
        if asset and asset not in recommendation_map:
            recommendation_map[asset] = item

    raw_watchlist = summary.get("watchlist") if isinstance(summary.get("watchlist"), list) else []
    if not raw_watchlist:
        raw_watchlist = _default_dashboard_summary()["watchlist"]

    watchlist: list[dict[str, Any]] = []
    for item in raw_watchlist:
        if not isinstance(item, dict):
            continue
        asset = str(item.get("asset") or "").strip().upper()
        if not asset:
            continue
        recommendation = recommendation_map.get(asset, {})
        change_24h_pct = float(item.get("change_24h_pct") or 0.0)
        watchlist.append(
            _enrich_signal_row(
                {
                    "asset": asset,
                    "price": float(item.get("price") or 0.0),
                    "change_24h_pct": change_24h_pct,
                    "signal": str(item.get("signal") or recommendation.get("signal") or "watch"),
                    "confidence": float(recommendation.get("confidence") or 0.0),
                    "status": str(recommendation.get("status") or "monitor"),
                    "volume_trend": str(item.get("volume_trend") or _derive_volume_trend(change_24h_pct)),
                    "execution_state": str(recommendation.get("execution_state") or ""),
                    "evidence": str(recommendation.get("evidence") or ""),
                    "summary": str(recommendation.get("summary") or ""),
                },
                market_row=item,
                current_regime=current_regime,
                risk_status=risk_status,
            )
        )

    if not watchlist:
        watchlist = list(_default_dashboard_summary()["watchlist"])

    requested_asset = str(selected_asset or "").strip().upper()
    if requested_asset:
        selected_row = next((row for row in watchlist if str(row.get("asset")) == requested_asset), watchlist[0])
    else:
        selected_row = min(
            enumerate(watchlist),
            key=lambda item: (_asset_priority(str(item[1].get("signal") or "")), item[0]),
        )[1]

    asset = str(selected_row.get("asset") or "")
    watchlist_price = float(selected_row.get("price") or 0.0)
    change_24h_pct = float(selected_row.get("change_24h_pct") or 0.0)
    explain = get_research_explain(asset, question=f"Why is {asset} moving?")
    snapshot = _get_market_snapshot(asset) or {}
    price = float(snapshot.get("last_price") or watchlist_price or 0.0)
    bid = float(snapshot.get("bid") or 0.0)
    ask = float(snapshot.get("ask") or 0.0)
    spread = float(snapshot.get("spread") or 0.0)
    exchange = str(snapshot.get("exchange") or "coinbase")
    snapshot_timestamp = str(snapshot.get("timestamp") or "")
    snapshot_source = str(snapshot.get("source") or "watchlist")
    volume_24h = float(snapshot.get("volume_24h") or 0.0)

    related_signals = [
        _enrich_signal_row(
            {
                "asset": str(item.get("asset") or ""),
                "signal": str(item.get("signal") or "hold"),
                "confidence": float(item.get("confidence") or 0.0),
                "summary": str(item.get("summary") or ""),
                "status": str(item.get("status") or "pending"),
                "execution_state": str(item.get("execution_state") or ""),
                "evidence": str(item.get("evidence") or ""),
                "price": watchlist_price,
                "change_24h_pct": change_24h_pct,
            },
            market_row={
                **(selected_row if isinstance(selected_row, dict) else {}),
                **(snapshot if isinstance(snapshot, dict) else {}),
                "price": price,
                "change_24h_pct": change_24h_pct,
                "volume_24h": volume_24h,
                "spread": spread,
            },
            current_regime=current_regime,
            risk_status=risk_status,
        )
        for item in recommendations
        if isinstance(item, dict) and str(item.get("asset") or "").strip().upper() == asset
    ]
    if not related_signals:
        related_signals = [
            _enrich_signal_row(
                {
                "asset": asset,
                "signal": str(selected_row.get("signal") or "watch"),
                "confidence": float(selected_row.get("confidence") or 0.0),
                "summary": "No direct recommendation is available. Keep this asset in monitored research mode.",
                "status": str(selected_row.get("status") or "monitor"),
                "execution_state": str(selected_row.get("execution_state") or ""),
                "price": watchlist_price,
                "change_24h_pct": change_24h_pct,
                },
                market_row={
                    **(selected_row if isinstance(selected_row, dict) else {}),
                    **(snapshot if isinstance(snapshot, dict) else {}),
                    "price": price,
                    "change_24h_pct": change_24h_pct,
                    "volume_24h": volume_24h,
                    "spread": spread,
                },
                current_regime=current_regime,
                risk_status=risk_status,
            )
        ]

    lead_signal = recommendation_map.get(asset, {})
    current_cause = str(explain.get("current_cause") or "").strip()
    past_precedent = str(explain.get("past_precedent") or "").strip()
    future_catalyst = str(explain.get("future_catalyst") or "").strip()

    thesis = current_cause or str(lead_signal.get("summary") or "").strip()
    if not thesis:
        bias = _derive_market_bias(change_24h_pct)
        thesis = f"{asset} remains {bias} with {selected_row.get('volume_trend')} activity and watchlist support."

    evidence = str(lead_signal.get("evidence") or "").strip()
    raw_evidence = explain.get("evidence") if isinstance(explain.get("evidence"), list) else []
    evidence_items = [
        {
            "type": str(item.get("type") or ""),
            "source": str(item.get("source") or ""),
            "summary": str(item.get("summary") or ""),
            "timestamp": str(item.get("timestamp") or ""),
            "relevance": float(item.get("relevance") or 0.0),
        }
        for item in raw_evidence
        if isinstance(item, dict)
    ]
    if not evidence and evidence_items:
        evidence = str(evidence_items[0].get("summary") or "")
    if not evidence:
        evidence = f"24h change {change_24h_pct:+.1f}% with {selected_row.get('volume_trend')} participation."
    if not evidence_items:
        evidence_items = [
            {
                "type": "market",
                "source": "watchlist",
                "summary": evidence,
                "timestamp": "",
                "relevance": 0.7,
            }
        ]

    catalysts = [
        current_cause or thesis,
        past_precedent or f"Volume trend is {selected_row.get('volume_trend')}.",
        future_catalyst or f"Nearest support is ${price * 0.985:,.2f} and resistance is ${price * 1.015:,.2f}.",
        str(explain.get("risk_note") or f"Current workflow state is {str(selected_row.get('status') or 'monitor').replace('_', ' ')}."),
    ]

    detail = {
        "asset": asset,
        "price": price,
        "change_24h_pct": change_24h_pct,
        "signal": str(selected_row.get("signal") or "watch"),
        "confidence": float(explain.get("confidence") or lead_signal.get("confidence") or selected_row.get("confidence") or 0.0),
        "status": str(lead_signal.get("status") or selected_row.get("status") or "monitor"),
        "execution_state": str(lead_signal.get("execution_state") or ""),
        "market_bias": _derive_market_bias(change_24h_pct),
        "volume_trend": str(selected_row.get("volume_trend") or "steady"),
        "support": round(price * 0.985, 2),
        "resistance": round(price * 1.015, 2),
        "exchange": exchange,
        "bid": bid,
        "ask": ask,
        "spread": spread,
        "volume_24h": volume_24h,
        "snapshot_timestamp": snapshot_timestamp,
        "snapshot_source": snapshot_source,
        "thesis": thesis,
        "question": str(explain.get("question") or f"Why is {asset} moving?"),
        "current_cause": current_cause or thesis,
        "past_precedent": past_precedent,
        "future_catalyst": future_catalyst,
        "risk_note": str(explain.get("risk_note") or ""),
        "execution_disabled": bool(explain.get("execution_disabled", True)),
        "evidence": evidence,
        "evidence_items": evidence_items,
        "price_series": _get_market_price_series(asset, price, change_24h_pct),
        "catalysts": catalysts,
        "related_signals": related_signals,
    }
    detail = _enrich_signal_row(
        detail,
        market_row={
            **(snapshot if isinstance(snapshot, dict) else {}),
            "price": price,
            "change_24h_pct": change_24h_pct,
            "volume_24h": volume_24h,
            "spread": spread,
        },
        current_regime=current_regime,
        risk_status=risk_status,
    )

    return {
        "selected_asset": asset,
        "watchlist": watchlist,
        "detail": detail,
    }


def _apply_local_settings_overrides(settings_payload: dict[str, Any]) -> dict[str, Any]:
    merged = {
        section: dict(value) if isinstance(value, dict) else {}
        for section, value in (settings_payload or {}).items()
    }
    raw_cfg = load_user_yaml()
    if not isinstance(raw_cfg, dict):
        return merged

    dashboard_ui = raw_cfg.get("dashboard_ui") if isinstance(raw_cfg.get("dashboard_ui"), dict) else {}
    local_settings = dashboard_ui.get("settings") if isinstance(dashboard_ui.get("settings"), dict) else {}
    automation_ui = dashboard_ui.get("automation") if isinstance(dashboard_ui.get("automation"), dict) else {}
    execution_cfg = raw_cfg.get("execution") if isinstance(raw_cfg.get("execution"), dict) else {}
    risk_cfg = raw_cfg.get("risk") if isinstance(raw_cfg.get("risk"), dict) else {}

    for section in ("general", "notifications", "ai", "autopilot", "providers", "paper_trading", "security"):
        local_section = local_settings.get(section) if isinstance(local_settings.get(section), dict) else {}
        if local_section:
            merged[section] = deep_merge(
                merged.get(section) if isinstance(merged.get(section), dict) else {},
                local_section,
            )

    general = merged.get("general") if isinstance(merged.get("general"), dict) else {}
    if "default_mode" not in general and str(automation_ui.get("default_mode") or "").strip():
        general["default_mode"] = str(automation_ui.get("default_mode") or "research_only")

    local_general = local_settings.get("general") if isinstance(local_settings.get("general"), dict) else {}
    raw_symbols = raw_cfg.get("symbols") if isinstance(raw_cfg.get("symbols"), list) else []
    normalized_symbols = [_normalize_asset_symbol(item) for item in raw_symbols]
    normalized_symbols = [item for item in normalized_symbols if item]
    if normalized_symbols and "watchlist_defaults" not in local_general:
        general["watchlist_defaults"] = normalized_symbols

    merged["general"] = general
    notifications = merged.get("notifications") if isinstance(merged.get("notifications"), dict) else {}
    categories = notifications.get("categories") if isinstance(notifications.get("categories"), dict) else {}
    notifications["email_enabled"] = bool(notifications.get("email_enabled", notifications.get("email")))
    notifications["categories"] = categories
    merged["notifications"] = notifications

    ai = merged.get("ai") if isinstance(merged.get("ai"), dict) else {}
    if not str(ai.get("evidence_verbosity") or "").strip():
        ai["evidence_verbosity"] = "standard"
    if not str(ai.get("autopilot_explanation_depth") or "").strip():
        ai["autopilot_explanation_depth"] = "standard"
    if not str(ai.get("away_summary_mode") or "").strip():
        ai["away_summary_mode"] = "prioritized"
    merged["ai"] = ai

    autopilot = merged.get("autopilot") if isinstance(merged.get("autopilot"), dict) else {}
    if "enabled" in automation_ui:
        autopilot["autopilot_enabled"] = bool(automation_ui.get("enabled"))
    if "approval_required_for_live" in automation_ui:
        autopilot["approval_required"] = bool(automation_ui.get("approval_required_for_live"))
    merged["autopilot"] = autopilot

    paper_trading = merged.get("paper_trading") if isinstance(merged.get("paper_trading"), dict) else {}
    paper_trading["enabled"] = bool(
        paper_trading.get("enabled", str(execution_cfg.get("executor_mode") or "paper").strip().lower() == "paper")
    )
    paper_trading["fee_bps"] = float(paper_trading.get("fee_bps") or execution_cfg.get("paper_fee_bps") or 7.0)
    paper_trading["slippage_bps"] = float(
        paper_trading.get("slippage_bps") or execution_cfg.get("paper_slippage_bps") or 2.0
    )
    paper_trading["approval_required"] = bool(
        paper_trading.get("approval_required", automation_ui.get("approval_required_for_live", True))
    )
    paper_trading["max_position_size_usd"] = float(
        paper_trading.get("max_position_size_usd") or risk_cfg.get("max_position_notional_per_symbol") or 5000.0
    )
    max_daily_loss_quote = float(risk_cfg.get("max_daily_loss_quote") or 0.0)
    if float(paper_trading.get("max_daily_loss_pct") or 0.0) <= 0 and max_daily_loss_quote > 0:
        total_value = float(general.get("portfolio_value_hint") or 0.0)
        if total_value > 0:
            paper_trading["max_daily_loss_pct"] = round((max_daily_loss_quote / total_value) * 100, 2)
    merged["paper_trading"] = paper_trading
    return merged


def get_settings_view() -> dict[str, Any]:
    envelope = _fetch_envelope("/api/v1/settings")
    if isinstance(envelope, dict) and envelope.get("status") == "success" and isinstance(envelope.get("data"), dict):
        return _apply_local_settings_overrides(deep_merge(_default_settings_payload(), dict(envelope["data"])))

    mock = _read_mock_envelope("settings.json")
    if isinstance(mock, dict) and isinstance(mock.get("data"), dict):
        return _apply_local_settings_overrides(deep_merge(_default_settings_payload(), dict(mock["data"])))
    return _apply_local_settings_overrides(_default_settings_payload())


def update_settings_view(payload: dict[str, Any]) -> dict[str, Any]:
    cfg = deep_merge(DEFAULT_CFG, load_user_yaml() or {})
    dashboard_ui = cfg.get("dashboard_ui") if isinstance(cfg.get("dashboard_ui"), dict) else {}
    settings_overlay = dashboard_ui.get("settings") if isinstance(dashboard_ui.get("settings"), dict) else {}

    for section in ("general", "notifications", "ai", "autopilot", "providers", "paper_trading", "security"):
        if isinstance(payload.get(section), dict):
            base_section = settings_overlay.get(section) if isinstance(settings_overlay.get(section), dict) else {}
            settings_overlay[section] = deep_merge(base_section, dict(payload[section]))

    automation_ui = dashboard_ui.get("automation") if isinstance(dashboard_ui.get("automation"), dict) else {}
    general_payload = payload.get("general") if isinstance(payload.get("general"), dict) else {}
    if "default_mode" in general_payload:
        automation_ui["default_mode"] = str(general_payload.get("default_mode") or "research_only")
    autopilot_payload = payload.get("autopilot") if isinstance(payload.get("autopilot"), dict) else {}
    if "autopilot_enabled" in autopilot_payload:
        automation_ui["enabled"] = bool(autopilot_payload.get("autopilot_enabled"))
    if "paper_trading_enabled" in autopilot_payload:
        automation_ui["paper_trading_enabled"] = bool(autopilot_payload.get("paper_trading_enabled"))
    if "digest_frequency" in autopilot_payload:
        automation_ui["digest_frequency"] = str(autopilot_payload.get("digest_frequency") or "daily")

    paper_payload = payload.get("paper_trading") if isinstance(payload.get("paper_trading"), dict) else {}
    execution_cfg = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {}
    if "fee_bps" in paper_payload:
        execution_cfg["paper_fee_bps"] = float(paper_payload.get("fee_bps") or 0.0)
    if "slippage_bps" in paper_payload:
        execution_cfg["paper_slippage_bps"] = float(paper_payload.get("slippage_bps") or 0.0)
    if "enabled" in paper_payload:
        execution_cfg["executor_mode"] = "paper" if bool(paper_payload.get("enabled")) else execution_cfg.get("executor_mode") or "paper"
    cfg["execution"] = execution_cfg

    risk_cfg = cfg.get("risk") if isinstance(cfg.get("risk"), dict) else {}
    if "max_position_size_usd" in paper_payload:
        risk_cfg["max_position_notional_per_symbol"] = float(paper_payload.get("max_position_size_usd") or 0.0)
    cfg["risk"] = risk_cfg

    dashboard_ui["automation"] = automation_ui
    dashboard_ui["settings"] = settings_overlay
    cfg["dashboard_ui"] = dashboard_ui

    saved, local_message = save_user_yaml(cfg, dry_run=False)
    if not saved:
        return {"ok": False, "message": str(local_message or "Local settings save failed.")}

    envelope = _request_envelope("/api/v1/settings", method="PUT", payload=payload)
    if isinstance(envelope, dict) and envelope.get("status") == "success" and isinstance(envelope.get("data"), dict):
        return {
            "ok": True,
            "data": dict(envelope["data"]),
            "message": "Settings saved locally and synced to the local API.",
        }

    error = envelope.get("error") if isinstance(envelope, dict) else None
    message = "Settings saved locally; API sync skipped."
    if isinstance(error, dict) and str(error.get("message") or "").strip():
        message = f"Settings saved locally; API sync skipped: {str(error['message'])}"
    return {"ok": True, "data": payload, "message": message}


def get_recommendations() -> list[dict[str, Any]]:
    local_rows = _load_local_recommendations(limit=20)
    if local_rows:
        return _apply_local_execution_state_to_recommendations(local_rows)

    envelope = _fetch_envelope("/api/v1/trading/recommendations")
    if isinstance(envelope, dict) and envelope.get("status") == "success":
        data = envelope.get("data")
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            mapped: list[dict[str, Any]] = []
            for item in data["items"]:
                if not isinstance(item, dict):
                    continue
                mapped.append(
                    {
                        "asset": str(item.get("asset") or ""),
                        "signal": str(item.get("side") or "hold"),
                        "confidence": float(item.get("confidence") or 0.0),
                        "summary": str(item.get("strategy") or ""),
                        "evidence": str(item.get("target_logic") or ""),
                        "status": str(item.get("status") or "pending"),
                    }
                )
            if mapped:
                return _apply_local_execution_state_to_recommendations(mapped)
    return _apply_local_execution_state_to_recommendations(_default_recommendations())


def get_signals_view(selected_asset: str | None = None) -> dict[str, Any]:
    recommendations = get_recommendations()
    summary = get_dashboard_summary()
    current_regime = _load_current_regime() or str(summary.get("risk_status") or "")
    watchlist = summary.get("watchlist") if isinstance(summary.get("watchlist"), list) else []

    market_rows: dict[str, dict[str, Any]] = {}
    for item in watchlist:
        if not isinstance(item, dict):
            continue
        asset = str(item.get("asset") or "").strip().upper()
        if asset:
            market_rows[asset] = item

    signals: list[dict[str, Any]] = []
    for item in recommendations:
        if not isinstance(item, dict):
            continue
        asset = str(item.get("asset") or "").strip().upper()
        market = market_rows.get(asset, {})
        signals.append(
            _enrich_signal_row(
                {
                    "asset": asset,
                    "signal": str(item.get("signal") or "hold"),
                    "confidence": float(item.get("confidence") or 0.0),
                    "summary": str(item.get("summary") or ""),
                    "status": str(item.get("status") or "pending"),
                    "execution_state": str(item.get("execution_state") or ""),
                    "evidence": str(item.get("evidence") or ""),
                    "price": float(market.get("price") or 0.0),
                    "change_24h_pct": float(market.get("change_24h_pct") or 0.0),
                },
                market_row=market,
                current_regime=current_regime,
                risk_status=str(summary.get("risk_status") or ""),
            )
        )

    if not signals:
        markets_view = get_markets_view(selected_asset=selected_asset)
        detail = markets_view.get("detail") if isinstance(markets_view.get("detail"), dict) else {}
        fallback_asset = str(detail.get("asset") or selected_asset or "SOL")
        signals = [
            {
                "asset": fallback_asset,
                "signal": str(detail.get("signal") or "watch"),
                "confidence": float(detail.get("confidence") or 0.0),
                "summary": str(detail.get("current_cause") or detail.get("thesis") or ""),
                "status": str(detail.get("status") or "monitor"),
                "execution_state": str(detail.get("execution_state") or ""),
                "evidence": str(detail.get("evidence") or ""),
                "price": float(detail.get("price") or 0.0),
                "change_24h_pct": float(detail.get("change_24h_pct") or 0.0),
                "regime": str(detail.get("regime") or current_regime or ""),
                "regime_fit": float(detail.get("regime_fit") or 0.0),
                "tradeability": float(detail.get("tradeability") or 0.0),
                "setup_quality": float(detail.get("setup_quality") or 0.0),
                "expected_return": float(detail.get("expected_return") or 0.0),
                "risk_penalty": float(detail.get("risk_penalty") or 0.0),
                "opportunity_score": float(detail.get("opportunity_score") or 0.0),
                "category": str(detail.get("category") or ""),
            }
        ]
        return {
            "selected_asset": fallback_asset,
            "signals": signals,
            "detail": detail,
        }

    requested_asset = str(selected_asset or "").strip().upper()
    if requested_asset and any(row["asset"] == requested_asset for row in signals):
        resolved_asset = requested_asset
    else:
        resolved_asset = max(
            signals,
            key=lambda row: (
                str(row.get("status") or "") == "pending_review",
                str(row.get("signal") or "") in {"buy", "research"},
                float(row.get("confidence") or 0.0),
            ),
        )["asset"]

    markets_view = get_markets_view(selected_asset=resolved_asset)
    detail = dict(markets_view.get("detail")) if isinstance(markets_view.get("detail"), dict) else {}
    selected_signal = next((row for row in signals if str(row.get("asset") or "") == resolved_asset), {})
    if detail and isinstance(selected_signal, dict):
        detail.update(
            {
                "regime": str(selected_signal.get("regime") or ""),
                "regime_fit": float(selected_signal.get("regime_fit") or 0.0),
                "tradeability": float(selected_signal.get("tradeability") or 0.0),
                "setup_quality": float(selected_signal.get("setup_quality") or 0.0),
                "expected_return": float(selected_signal.get("expected_return") or 0.0),
                "risk_penalty": float(selected_signal.get("risk_penalty") or 0.0),
                "opportunity_score": float(selected_signal.get("opportunity_score") or 0.0),
                "category": str(selected_signal.get("category") or ""),
            }
        )

    return {
        "selected_asset": resolved_asset,
        "signals": signals,
        "detail": detail,
    }


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


def get_overview_view(selected_asset: str | None = None) -> dict[str, Any]:
    summary = get_dashboard_summary()
    recent_activity = get_recent_activity()
    signals_view = get_signals_view(selected_asset=selected_asset)
    signals = signals_view.get("signals") if isinstance(signals_view.get("signals"), list) else []
    detail = signals_view.get("detail") if isinstance(signals_view.get("detail"), dict) else {}

    signal_rows = [
        {
            "asset": str(item.get("asset") or ""),
            "signal": str(item.get("signal") or ""),
            "confidence": float(item.get("confidence") or 0.0),
            "status": str(item.get("status") or ""),
            "execution_state": str(item.get("execution_state") or ""),
            "thesis": str(item.get("summary") or ""),
            "regime": str(item.get("regime") or ""),
            "category": str(item.get("category") or ""),
            "opportunity_score": float(item.get("opportunity_score") or 0.0),
        }
        for item in signals[:6]
        if isinstance(item, dict)
    ]

    return {
        "summary": summary,
        "recent_activity": recent_activity,
        "watchlist_preview": _build_watchlist_preview(summary),
        "signals": signal_rows,
        "selected_asset": str(signals_view.get("selected_asset") or detail.get("asset") or ""),
        "detail": detail,
    }


def get_recent_activity() -> list[str]:
    local_rows = _load_local_recent_activity(limit=6)
    if local_rows:
        return local_rows

    envelope = _fetch_envelope("/api/v1/audit/events")
    if isinstance(envelope, dict) and envelope.get("status") == "success":
        data = envelope.get("data")
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            out = []
            for item in data["items"][:6]:
                if not isinstance(item, dict):
                    continue
                details = str(item.get("details") or "").strip()
                action = str(item.get("action") or "").strip()
                line = details or action
                if line:
                    out.append(line)
            if out:
                return out
    return _default_activity()


def get_portfolio_view() -> dict[str, Any]:
    summary = get_dashboard_summary()
    portfolio = summary.get("portfolio") if isinstance(summary.get("portfolio"), dict) else {}
    watchlist = summary.get("watchlist") if isinstance(summary.get("watchlist"), list) else []

    watch_prices = {
        str(item.get("asset") or ""): float(item.get("price") or 0.0)
        for item in watchlist
        if isinstance(item, dict) and str(item.get("asset") or "").strip()
    }

    local_snapshot = _load_local_portfolio_snapshot(watch_prices)
    if isinstance(local_snapshot, dict):
        local_portfolio = local_snapshot.get("portfolio") if isinstance(local_snapshot.get("portfolio"), dict) else {}
        local_positions = (
            local_snapshot.get("positions") if isinstance(local_snapshot.get("positions"), list) else []
        )
        if local_portfolio and local_positions:
            merged_portfolio = {**portfolio, **local_portfolio}
            return {
                "currency": "USD",
                "portfolio": merged_portfolio,
                "positions": local_positions,
            }

    positions = _default_positions()
    enriched_positions: list[dict[str, Any]] = []
    for row in positions:
        asset = str(row.get("asset") or "")
        size = float(row.get("size") or 0.0)
        entry = float(row.get("entry") or 0.0)
        mark = float(watch_prices.get(asset) or row.get("mark") or 0.0)
        pnl = round((mark - entry) * size, 2) if size and entry and mark else float(row.get("pnl") or 0.0)
        enriched_positions.append(
            {
                "asset": asset,
                "side": str(row.get("side") or "long"),
                "size": size,
                "entry": entry,
                "mark": mark,
                "pnl": pnl,
            }
        )

    return {
        "currency": "USD",
        "portfolio": portfolio,
        "positions": enriched_positions,
    }


def get_trades_view() -> dict[str, Any]:
    summary = get_dashboard_summary()
    pending_approvals = _load_local_pending_approvals(limit=20)
    if not pending_approvals:
        recommendations = get_recommendations()
        pending_approvals = [
            {
                "id": str(item.get("id") or f"rec_{index + 1}"),
                "asset": str(item.get("asset") or ""),
                "side": str(item.get("signal") or "hold"),
                "risk_size_pct": float(item.get("risk_size_pct") or 0.0),
                "status": str(item.get("status") or "pending_review"),
            }
            for index, item in enumerate(recommendations)
            if str(item.get("status") or "").strip() in {"pending_review", "pending", "watch"}
        ]
    if not pending_approvals:
        pending_approvals = [
            {"id": "rec_1", "asset": "SOL", "side": "buy", "risk_size_pct": 1.5, "status": "pending_review"}
        ]

    recent_fills = _load_local_recent_fills(limit=20)
    if not recent_fills:
        recent_fills = _default_recent_fills()

    open_orders = _load_local_open_orders(limit=20)
    failed_orders = _load_local_failed_orders(limit=20)

    return {
        "approval_required": bool(summary.get("approval_required", True)),
        "pending_approvals": pending_approvals,
        "open_orders": open_orders,
        "failed_orders": failed_orders,
        "recent_fills": recent_fills,
    }


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


def get_automation_view() -> dict[str, Any]:
    summary = get_dashboard_summary()
    settings = get_settings_view()
    general = settings.get("general") if isinstance(settings.get("general"), dict) else {}
    runtime_cfg = deep_merge(DEFAULT_CFG, load_user_yaml())
    runtime_execution = runtime_cfg.get("execution") if isinstance(runtime_cfg.get("execution"), dict) else {}
    runtime_signals = runtime_cfg.get("signals") if isinstance(runtime_cfg.get("signals"), dict) else {}
    dashboard_ui = runtime_cfg.get("dashboard_ui") if isinstance(runtime_cfg.get("dashboard_ui"), dict) else {}
    automation_ui = dashboard_ui.get("automation") if isinstance(dashboard_ui.get("automation"), dict) else {}

    default_mode = str(
        automation_ui.get("default_mode") or general.get("default_mode") or summary.get("mode") or "research_only"
    )
    execution_enabled = bool(
        automation_ui.get("enabled", summary.get("execution_enabled", False))
    )
    approval_required = bool(
        automation_ui.get("approval_required_for_live", summary.get("approval_required", True))
    )
    executor_mode = str(runtime_execution.get("executor_mode") or "paper").lower().strip()
    live_enabled = bool(runtime_execution.get("live_enabled", False))

    return {
        "execution_enabled": execution_enabled,
        "dry_run_mode": bool(
            automation_ui.get("dry_run_mode", not execution_enabled if "dry_run_mode" not in automation_ui else True)
        ),
        "default_mode": default_mode,
        "schedule": str(automation_ui.get("schedule") or "manual"),
        "marketplace_routing": str(
            automation_ui.get(
                "marketplace_routing",
                "paper only" if bool(runtime_signals.get("auto_route_to_paper", False)) else "disabled",
            )
        ),
        "approval_required_for_live": approval_required,
        "config_path": str(CONFIG_PATH.resolve()),
        "executor_mode": executor_mode,
        "live_enabled": live_enabled,
        "executor_poll_sec": float(runtime_execution.get("executor_poll_sec") or DEFAULT_CFG["execution"]["executor_poll_sec"]),
        "executor_max_per_cycle": int(
            runtime_execution.get("executor_max_per_cycle") or DEFAULT_CFG["execution"]["executor_max_per_cycle"]
        ),
        "paper_fee_bps": float(runtime_execution.get("paper_fee_bps") or DEFAULT_CFG["execution"]["paper_fee_bps"]),
        "paper_slippage_bps": float(
            runtime_execution.get("paper_slippage_bps") or DEFAULT_CFG["execution"]["paper_slippage_bps"]
        ),
        "require_keys_for_live": bool(
            runtime_execution.get("require_keys_for_live", DEFAULT_CFG["execution"]["require_keys_for_live"])
        ),
        "default_venue": str(runtime_signals.get("default_venue") or "coinbase"),
        "default_qty": float(runtime_signals.get("default_qty") or 0.001),
        "order_type": str(runtime_signals.get("order_type") or "market").lower().strip(),
        "operations_snapshot": _load_automation_operations_snapshot(),
    }


def update_automation_view(payload: dict[str, Any]) -> dict[str, Any]:
    enable_automation = bool(payload.get("execution_enabled", False))
    dry_run_mode = bool(payload.get("dry_run_mode", True))
    default_mode = str(payload.get("default_mode") or "research_only")
    schedule = str(payload.get("schedule") or "manual")
    marketplace_routing = str(payload.get("marketplace_routing") or "disabled")
    approval_required_for_live = bool(payload.get("approval_required_for_live", True))
    executor_poll_sec = float(payload.get("executor_poll_sec") or DEFAULT_CFG["execution"]["executor_poll_sec"])
    executor_max_per_cycle = int(
        payload.get("executor_max_per_cycle") or DEFAULT_CFG["execution"]["executor_max_per_cycle"]
    )
    paper_fee_bps = float(payload.get("paper_fee_bps") or DEFAULT_CFG["execution"]["paper_fee_bps"])
    paper_slippage_bps = float(payload.get("paper_slippage_bps") or DEFAULT_CFG["execution"]["paper_slippage_bps"])
    require_keys_for_live = bool(
        payload.get("require_keys_for_live", DEFAULT_CFG["execution"]["require_keys_for_live"])
    )
    default_venue = str(payload.get("default_venue") or "coinbase").strip().lower()
    default_qty = float(payload.get("default_qty") or 0.001)
    order_type = str(payload.get("order_type") or "market").strip().lower()

    cfg = deep_merge(DEFAULT_CFG, load_user_yaml())
    dashboard_ui = cfg.get("dashboard_ui") if isinstance(cfg.get("dashboard_ui"), dict) else {}
    automation_ui = dashboard_ui.get("automation") if isinstance(dashboard_ui.get("automation"), dict) else {}
    signals = cfg.get("signals") if isinstance(cfg.get("signals"), dict) else {}
    paper_execution = cfg.get("paper_execution") if isinstance(cfg.get("paper_execution"), dict) else {}
    execution = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {}

    runtime_live_enabled = bool(enable_automation and default_mode == "live_auto" and not dry_run_mode)
    executor_mode = "live" if enable_automation and default_mode in {"live_approval", "live_auto"} and not dry_run_mode else "paper"

    cfg = set_live_enabled(cfg, runtime_live_enabled)
    execution = cfg.get("execution") if isinstance(cfg.get("execution"), dict) else execution
    execution["executor_mode"] = executor_mode
    execution["executor_poll_sec"] = executor_poll_sec
    execution["executor_max_per_cycle"] = executor_max_per_cycle
    execution["paper_fee_bps"] = paper_fee_bps
    execution["paper_slippage_bps"] = paper_slippage_bps
    execution["require_keys_for_live"] = require_keys_for_live
    cfg["execution"] = execution

    paper_execution["enabled"] = bool(enable_automation and executor_mode == "paper")
    cfg["paper_execution"] = paper_execution

    signals["auto_route_to_paper"] = marketplace_routing == "paper only"
    signals["default_venue"] = default_venue
    signals["default_qty"] = default_qty
    signals["order_type"] = order_type
    cfg["signals"] = signals

    automation_ui.update(
        {
            "enabled": enable_automation,
            "dry_run_mode": dry_run_mode,
            "default_mode": default_mode,
            "schedule": schedule,
            "marketplace_routing": marketplace_routing,
            "approval_required_for_live": approval_required_for_live,
        }
    )
    dashboard_ui["automation"] = automation_ui
    cfg["dashboard_ui"] = dashboard_ui

    saved, message = save_user_yaml(cfg, dry_run=False)
    settings_result = update_settings_view({"general": {"default_mode": default_mode}})

    if saved and bool(settings_result.get("ok")):
        return {
            "ok": True,
            "message": "Automation settings saved.",
            "config_path": str(CONFIG_PATH.resolve()),
        }
    if saved:
        return {
            "ok": True,
            "message": f"Runtime automation settings saved. Settings API sync skipped: {settings_result.get('message')}",
            "config_path": str(CONFIG_PATH.resolve()),
        }
    return {"ok": False, "message": message}

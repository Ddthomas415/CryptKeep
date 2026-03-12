from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from services.admin.config_editor import CONFIG_PATH, load_user_yaml, save_user_yaml
from services.execution.live_arming import set_live_enabled
from services.setup.config_manager import DEFAULT_CFG, deep_merge

REPO_ROOT = Path(__file__).resolve().parents[2]
API_BASE_URL = os.environ.get("CK_API_BASE_URL", "http://localhost:8000").rstrip("/")
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
            "telegram": True,
            "discord": False,
            "webhook": False,
            "price_alerts": True,
            "news_alerts": True,
            "catalyst_alerts": True,
            "risk_alerts": True,
            "approval_requests": True,
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
        },
        "security": {
            "session_timeout_minutes": 60,
            "secret_masking": True,
            "audit_export_allowed": True,
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


def _request_envelope(path: str, *, method: str = "GET", payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    url = f"{API_BASE_URL}{path}"
    body: bytes | None = None
    headers = {
        "Accept": "application/json",
        "User-Agent": "CryptKeepDashboard/1.0",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
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


def _fetch_envelope(path: str) -> dict[str, Any] | None:
    return _request_envelope(path, method="GET")


def get_dashboard_summary() -> dict[str, Any]:
    envelope = _fetch_envelope("/api/v1/dashboard/summary")
    if isinstance(envelope, dict) and envelope.get("status") == "success" and isinstance(envelope.get("data"), dict):
        return dict(envelope["data"])

    mock = _read_mock_envelope("dashboard.json")
    if isinstance(mock, dict) and isinstance(mock.get("data"), dict):
        return dict(mock["data"])
    return _default_dashboard_summary()


def get_research_explain(asset: str, question: str | None = None) -> dict[str, Any]:
    asset_symbol = str(asset or "").strip().upper() or "SOL"
    resolved_question = question or f"Why is {asset_symbol} moving?"
    fallback = _default_explain_payload(asset_symbol, resolved_question)

    envelope = _request_envelope(
        "/api/v1/research/explain",
        method="POST",
        payload={"asset": asset_symbol, "question": resolved_question},
    )
    if isinstance(envelope, dict) and envelope.get("status") == "success" and isinstance(envelope.get("data"), dict):
        data = dict(envelope["data"])
        if not _explain_mentions_foreign_asset(data, asset_symbol):
            data["asset"] = asset_symbol
            data["question"] = resolved_question
            return data
        return fallback

    mock = _read_mock_envelope("explain-sol.json")
    if asset_symbol == "SOL" and isinstance(mock, dict) and isinstance(mock.get("data"), dict):
        data = dict(mock["data"])
        data["asset"] = asset_symbol
        data["question"] = resolved_question
        return data

    return fallback


def get_markets_view(selected_asset: str | None = None) -> dict[str, Any]:
    summary = get_dashboard_summary()
    recommendations = get_recommendations()

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
            {
                "asset": asset,
                "price": float(item.get("price") or 0.0),
                "change_24h_pct": change_24h_pct,
                "signal": str(item.get("signal") or recommendation.get("signal") or "watch"),
                "confidence": float(recommendation.get("confidence") or 0.0),
                "status": str(recommendation.get("status") or "monitor"),
                "volume_trend": str(item.get("volume_trend") or _derive_volume_trend(change_24h_pct)),
            }
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
    price = float(selected_row.get("price") or 0.0)
    change_24h_pct = float(selected_row.get("change_24h_pct") or 0.0)
    explain = get_research_explain(asset, question=f"Why is {asset} moving?")

    related_signals = [
        {
            "asset": str(item.get("asset") or ""),
            "signal": str(item.get("signal") or "hold"),
            "confidence": float(item.get("confidence") or 0.0),
            "summary": str(item.get("summary") or ""),
            "status": str(item.get("status") or "pending"),
        }
        for item in recommendations
        if isinstance(item, dict) and str(item.get("asset") or "").strip().upper() == asset
    ]
    if not related_signals:
        related_signals = [
            {
                "asset": asset,
                "signal": str(selected_row.get("signal") or "watch"),
                "confidence": float(selected_row.get("confidence") or 0.0),
                "summary": "No direct recommendation is available. Keep this asset in monitored research mode.",
                "status": str(selected_row.get("status") or "monitor"),
            }
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
        "market_bias": _derive_market_bias(change_24h_pct),
        "volume_trend": str(selected_row.get("volume_trend") or "steady"),
        "support": round(price * 0.985, 2),
        "resistance": round(price * 1.015, 2),
        "thesis": thesis,
        "question": str(explain.get("question") or f"Why is {asset} moving?"),
        "current_cause": current_cause or thesis,
        "past_precedent": past_precedent,
        "future_catalyst": future_catalyst,
        "risk_note": str(explain.get("risk_note") or ""),
        "execution_disabled": bool(explain.get("execution_disabled", True)),
        "evidence": evidence,
        "evidence_items": evidence_items,
        "price_series": _build_price_series(price, change_24h_pct),
        "catalysts": catalysts,
        "related_signals": related_signals,
    }

    return {
        "selected_asset": asset,
        "watchlist": watchlist,
        "detail": detail,
    }


def get_settings_view() -> dict[str, Any]:
    envelope = _fetch_envelope("/api/v1/settings")
    if isinstance(envelope, dict) and envelope.get("status") == "success" and isinstance(envelope.get("data"), dict):
        return dict(envelope["data"])

    mock = _read_mock_envelope("settings.json")
    if isinstance(mock, dict) and isinstance(mock.get("data"), dict):
        return dict(mock["data"])
    return _default_settings_payload()


def update_settings_view(payload: dict[str, Any]) -> dict[str, Any]:
    envelope = _request_envelope("/api/v1/settings", method="PUT", payload=payload)
    if isinstance(envelope, dict) and envelope.get("status") == "success" and isinstance(envelope.get("data"), dict):
        return {"ok": True, "data": dict(envelope["data"])}

    error = envelope.get("error") if isinstance(envelope, dict) else None
    message = "Settings API unavailable."
    if isinstance(error, dict) and str(error.get("message") or "").strip():
        message = str(error["message"])
    return {"ok": False, "message": message}


def get_recommendations() -> list[dict[str, Any]]:
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
                return mapped
    return _default_recommendations()


def get_signals_view(selected_asset: str | None = None) -> dict[str, Any]:
    recommendations = get_recommendations()
    summary = get_dashboard_summary()
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
            {
                "asset": asset,
                "signal": str(item.get("signal") or "hold"),
                "confidence": float(item.get("confidence") or 0.0),
                "summary": str(item.get("summary") or ""),
                "status": str(item.get("status") or "pending"),
                "evidence": str(item.get("evidence") or ""),
                "price": float(market.get("price") or 0.0),
                "change_24h_pct": float(market.get("change_24h_pct") or 0.0),
            }
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
                "evidence": str(detail.get("evidence") or ""),
                "price": float(detail.get("price") or 0.0),
                "change_24h_pct": float(detail.get("change_24h_pct") or 0.0),
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
    detail = markets_view.get("detail") if isinstance(markets_view.get("detail"), dict) else {}

    return {
        "selected_asset": resolved_asset,
        "signals": signals,
        "detail": detail,
    }


def get_recent_activity() -> list[str]:
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

    return {
        "approval_required": bool(summary.get("approval_required", True)),
        "pending_approvals": pending_approvals,
        "recent_fills": _default_recent_fills(),
    }


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

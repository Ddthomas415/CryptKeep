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
    }


def update_automation_view(payload: dict[str, Any]) -> dict[str, Any]:
    enable_automation = bool(payload.get("execution_enabled", False))
    dry_run_mode = bool(payload.get("dry_run_mode", True))
    default_mode = str(payload.get("default_mode") or "research_only")
    schedule = str(payload.get("schedule") or "manual")
    marketplace_routing = str(payload.get("marketplace_routing") or "disabled")
    approval_required_for_live = bool(payload.get("approval_required_for_live", True))

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
    cfg["execution"] = execution

    paper_execution["enabled"] = bool(enable_automation and executor_mode == "paper")
    cfg["paper_execution"] = paper_execution

    signals["auto_route_to_paper"] = marketplace_routing == "paper only"
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

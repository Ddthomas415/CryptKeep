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
    _normalize_asset_symbol,
)
from dashboard.services.views._shared_market import (
    _default_watchlist_rows,
    _get_market_snapshot,
    _load_local_portfolio_snapshot,
)

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
        "watchlist": _default_watchlist_rows(),
    }


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




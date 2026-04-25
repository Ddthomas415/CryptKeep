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


def _view_data():
    from dashboard.services import view_data

    return view_data
from dashboard.services.views._shared_market import (
    _repo_default_watchlist_assets,
)
from dashboard.services.views._shared_shared import (
    _normalize_asset_symbol,
)

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
            "watchlist_defaults": _repo_default_watchlist_assets(),
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


def _apply_local_settings_overrides(settings_payload: dict[str, Any]) -> dict[str, Any]:
    merged = {
        section: dict(value) if isinstance(value, dict) else {}
        for section, value in (settings_payload or {}).items()
    }
    raw_cfg = _view_data().load_user_yaml()
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



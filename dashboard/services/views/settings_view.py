from __future__ import annotations
from typing import Any
from services.setup.config_manager import DEFAULT_CFG, deep_merge
from services.admin.config_editor import CONFIG_PATH, load_user_yaml, save_user_yaml

# settings_view.py — auto-split from view_data.py
from services.execution.live_arming import set_live_enabled
from dashboard.services.views._shared import (  # noqa: F401
    _apply_local_settings_overrides,
    _default_settings_payload,
    _fetch_envelope,
    _load_automation_operations_snapshot,
    _read_mock_envelope,
    _request_envelope,
)

def _view_data():
    from dashboard.services import view_data

    return view_data

def get_settings_view() -> dict[str, Any]:
    vd = _view_data()
    envelope = vd._fetch_envelope("/api/v1/settings")
    if isinstance(envelope, dict) and envelope.get("status") == "success" and isinstance(envelope.get("data"), dict):
        return vd._apply_local_settings_overrides(deep_merge(vd._default_settings_payload(), dict(envelope["data"])))

    mock = vd._read_mock_envelope("settings.json")
    if isinstance(mock, dict) and isinstance(mock.get("data"), dict):
        return vd._apply_local_settings_overrides(deep_merge(vd._default_settings_payload(), dict(mock["data"])))
    return vd._apply_local_settings_overrides(vd._default_settings_payload())



def update_settings_view(payload: dict[str, Any]) -> dict[str, Any]:
    vd = _view_data()
    cfg = deep_merge(DEFAULT_CFG, vd.load_user_yaml() or {})
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

    saved, local_message = vd.save_user_yaml(cfg, dry_run=False)
    if not saved:
        return {"ok": False, "message": str(local_message or "Local settings save failed.")}

    envelope = vd._request_envelope("/api/v1/settings", method="PUT", payload=payload)
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



def get_automation_view() -> dict[str, Any]:
    vd = _view_data()
    summary = vd.get_dashboard_summary()
    settings = vd.get_settings_view()
    general = settings.get("general") if isinstance(settings.get("general"), dict) else {}
    runtime_cfg = deep_merge(DEFAULT_CFG, vd.load_user_yaml())
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
        "config_path": str(vd.CONFIG_PATH.resolve()),
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
        "operations_snapshot": vd._load_automation_operations_snapshot(),
    }



def update_automation_view(payload: dict[str, Any]) -> dict[str, Any]:
    vd = _view_data()
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

    cfg = deep_merge(DEFAULT_CFG, vd.load_user_yaml())
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

    saved, message = vd.save_user_yaml(cfg, dry_run=False)
    settings_result = vd.update_settings_view({"general": {"default_mode": default_mode}})

    if saved and bool(settings_result.get("ok")):
        return {
            "ok": True,
            "message": "Automation settings saved.",
            "config_path": str(vd.CONFIG_PATH.resolve()),
        }
    if saved:
        return {
            "ok": True,
            "message": f"Runtime automation settings saved. Settings API sync skipped: {settings_result.get('message')}",
            "config_path": str(vd.CONFIG_PATH.resolve()),
        }
    return {"ok": False, "message": message}

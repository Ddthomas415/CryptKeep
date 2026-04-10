from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from services.bot.process_manager import start_process, stop_process, read_status, ProcStatus
from services.config_loader import load_runtime_trading_config
from services.execution.live_arming import is_live_enabled

@dataclass(frozen=True)
class StartDecision:
    ok: bool
    mode: str
    status: str   # OK / WARN / BLOCK
    reasons: List[str]
    note: str

def _load_cfg(path: str = "config/trading.yaml") -> Dict[str, Any]:
    return load_runtime_trading_config(path)

def _risk_check(cfg: Dict[str, Any]) -> Tuple[bool, List[str]]:
    r = cfg.get("risk") or {}
    live_risk = r.get("live") if isinstance(r.get("live"), dict) else {}
    if not bool(r.get("enabled", True)):
        return True, ["risk_disabled"]
    reasons = []

    def _pos(x):
        try:
            return float(x) > 0
        except Exception:
            return False

    max_order_notional = live_risk.get("max_notional_per_trade_usd", r.get("max_order_notional_usd", 0))
    max_position_notional = live_risk.get(
        "max_position_notional_usd",
        r.get("max_position_notional_usd", r.get("max_position_notional", 0)),
    )
    mdl = live_risk.get("max_daily_loss_usd", r.get("max_daily_loss_usd", None))

    if not _pos(max_order_notional):
        reasons.append("risk.max_order_notional_usd_missing_or_nonpositive")
    if not _pos(max_position_notional):
        reasons.append("risk.max_position_notional_usd_missing_or_nonpositive")
    # daily loss can be null (disabled), but if set must be >0
    if mdl is not None and not _pos(mdl):
        reasons.append("risk.max_daily_loss_usd_nonpositive")
    return (len([x for x in reasons if x.endswith("missing_or_nonpositive")]) == 0), reasons

def _ui_gate(cfg: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
    # Uses Phase 5 ui gate if present
    try:
        from services.diagnostics.ui_live_gate import evaluate_live_ui_gate
        g = evaluate_live_ui_gate(cfg)
        return bool(g.ok), str(g.status), list(g.reasons)
    except Exception:
        # If UI gate missing, fail closed for live
        return False, "BLOCK", ["ui_gate_missing_or_error"]

def decide_start(mode: str, cfg: Optional[Dict[str, Any]] = None) -> StartDecision:
    cfg = cfg or _load_cfg()
    mode = str(mode).lower().strip()

    if mode not in ("paper", "live"):
        return StartDecision(False, mode, "BLOCK", ["invalid_mode"], "Mode must be paper or live")

    # Live: enforce gates and explicit confirmations
    if mode == "live":
        live = cfg.get("live") or {}
        sandbox = bool(live.get("sandbox", True))
        if not is_live_enabled(cfg):
            return StartDecision(False, mode, "BLOCK", ["execution.live_enabled is false"], "Enable execution.live_enabled before starting live mode")

        ok_gate, gate_status, gate_reasons = _ui_gate(cfg)
        if not ok_gate:
            return StartDecision(False, mode, "BLOCK", gate_reasons, "Blocked by feed/ws/collector gate")

        ok_risk, risk_reasons = _risk_check(cfg)
        if not ok_risk:
            return StartDecision(False, mode, "BLOCK", risk_reasons, "Blocked by risk config")

        # Real live (sandbox false) requires explicit environment confirmation
        if not sandbox:
            if os.environ.get("ENABLE_LIVE_TRADING", "").upper() != "YES":
                return StartDecision(False, mode, "BLOCK", ["ENABLE_LIVE_TRADING!=YES"], "Set ENABLE_LIVE_TRADING=YES to allow real live")
            if os.environ.get("CONFIRM_LIVE", "").upper() != "YES":
                return StartDecision(False, mode, "BLOCK", ["CONFIRM_LIVE!=YES"], "Set CONFIRM_LIVE=YES to confirm real live")

        # sandbox live is allowed with gate OK; still requires keys set in environment
        return StartDecision(True, mode, gate_status, [], "Live start allowed")

    # Paper: allowed always (no live keys required)
    return StartDecision(True, mode, "OK", [], "Paper start allowed")

def start(mode: str) -> Tuple[StartDecision, ProcStatus]:
    cfg = _load_cfg()
    decision = decide_start(mode, cfg)

    if not decision.ok:
        return decision, read_status()

    # launch module
    module = "services.bot.cli_paper" if mode == "paper" else "services.bot.cli_live"
    st = start_process(mode=mode, module=module)
    return decision, st

def stop() -> ProcStatus:
    return stop_process()

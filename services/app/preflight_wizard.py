from __future__ import annotations
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Dict

from services.os.app_paths import runtime_dir, data_dir, ensure_dirs
from services.os.ports import can_bind as _port_can_bind, resolve_preferred_port
from services.admin.config_editor import load_user_yaml
from services.admin.first_run_wizard import (
    guided_setup_state,
    guided_setup_apply_state,
    guided_setup_apply_preset,
)


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _port_open(host: str, port: int, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except Exception:
        return False


def _in_venv() -> bool:
    try:
        return getattr(sys, "base_prefix", sys.prefix) != sys.prefix
    except Exception:
        return False


def _import_ok(mod: str) -> tuple[bool, str | None]:
    try:
        __import__(mod)
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _cfg() -> dict:
    cfg = load_user_yaml()
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}
    venues = pf.get("venues") if isinstance(pf.get("venues"), list) else ["coinbase", "gateio"]
    symbols = pf.get("symbols") if isinstance(pf.get("symbols"), list) else ["BTC/USD"]
    return {"venues": venues, "symbols": symbols}


def _config_valid() -> tuple[bool, str | None]:
    try:
        from services.admin.config_editor import validate_user_yaml
        ok, errors, _warnings = validate_user_yaml(load_user_yaml())
        if ok:
            return True, None
        return False, str(errors)
    except Exception:
        return True, None


def _market_checks(venues: list[str], symbols: list[str]) -> list[dict]:
    rows = []
    try:
        from services.market_data.symbol_router import normalize_venue, normalize_symbol
        from services.risk.market_quality_guard import check as mq_check

        for v in venues:
            nv = normalize_venue(str(v))
            for s in symbols:
                ns = normalize_symbol(str(s))
                r = mq_check(nv, ns)
                rows.append({"venue": nv, "symbol": ns, **r})

    except Exception as e:
        rows.append({"ok": False, "reason": f"market_check_failed:{type(e).__name__}:{e}"})

    return rows


def _db_presence() -> dict:
    d = data_dir()
    return {
        "intent_queue": str(d / "intent_queue.sqlite"),
        "paper_trading": str(d / "paper_trading.sqlite"),
        "trade_journal": str(d / "trade_journal.sqlite"),
        "live_intent_queue": str(d / "live_intent_queue.sqlite"),
        "live_trading": str(d / "live_trading.sqlite"),
        "exists": {
            "intent_queue": (d / "intent_queue.sqlite").exists(),
            "paper_trading": (d / "paper_trading.sqlite").exists(),
            "trade_journal": (d / "trade_journal.sqlite").exists(),
            "live_intent_queue": (d / "live_intent_queue.sqlite").exists(),
            "live_trading": (d / "live_trading.sqlite").exists(),
        }
    }


def _supervisor_state() -> dict:
    p = runtime_dir() / "supervisor" / "pids.json"
    return {"pids_path": str(p), "pids": _read_json(p) if p.exists() else None}


def _live_arming_state() -> dict:
    try:
        from services.execution.live_arming import live_enabled_and_armed
        armed, reason = live_enabled_and_armed()
        return {"armed": bool(armed), "reason": reason, "CBP_LIVE_ARMED": os.getenv("CBP_LIVE_ARMED", "")}
    except Exception as e:
        return {"armed": False, "reason": f"live_arming_unavailable:{type(e).__name__}:{e}"}


def run_preflight() -> dict:
    ensure_dirs()

    py_ok = sys.version_info >= (3, 10)
    venv = _in_venv()

    deps = {}
    for m in ("streamlit", "pandas", "ccxt"):
        ok, err = _import_ok(m)
        deps[m] = {"ok": ok, "error": err}

    cfg_ok, cfg_err = _config_valid()
    cfg = _cfg()

    host = "127.0.0.1"
    port = 8501
    resolution = resolve_preferred_port(
        host,
        port,
        max_offset=int(os.environ.get("CBP_PORT_SEARCH_LIMIT", "50") or "50"),
    )
    port_free = bool(resolution.requested_available)
    port_open = _port_open(host, port)
    port_ok = _port_can_bind(host, int(resolution.resolved_port))

    mk = _market_checks(cfg["venues"], cfg["symbols"])

    # ── LENIENT readiness check ────────────────────────────────────────────────
    # Ready if at least one venue/symbol pair is OK
    market_ok = any(bool(r.get("ok")) for r in mk if isinstance(r, dict) and r.get("ok") is not None)

    db = _db_presence()
    sup = _supervisor_state()
    live = _live_arming_state()

    problems: List[str] = []
    if not py_ok:
        problems.append("python_version<3.10")
    if not cfg_ok:
        problems.append("config_invalid")
    if not deps["streamlit"]["ok"]:
        problems.append("missing_streamlit")
    if not deps["pandas"]["ok"]:
        problems.append("missing_pandas")
    if not deps["ccxt"]["ok"]:
        problems.append("missing_ccxt")
    if not port_ok:
        problems.append("ui_port_unavailable")
    if not market_ok:
        problems.append("market_data_not_ready")

    ready = len(problems) == 0

    return {
        "ts": _now(),
        "ready": ready,
        "problems": problems,
        "python": {"ok": py_ok, "version": sys.version},
        "venv": {"in_venv": venv, "sys_prefix": sys.prefix},
        "deps": deps,
        "config": {"ok": cfg_ok, "error": cfg_err, "preflight": cfg},
        "port_8501": {
            "ok": port_ok,
            "free": port_free,
            "open": port_open,
            "requested_port": int(resolution.requested_port),
            "resolved_port": int(resolution.resolved_port),
            "auto_switched": bool(resolution.auto_switched),
        },
        "market_quality": mk,
        "db_presence": db,
        "supervisor": sup,
        "live_arming": live,
    }

def wizard_guided_setup_state() -> dict:
    return guided_setup_state()


def wizard_guided_setup_apply_state(patch: dict | None = None) -> dict:
    return guided_setup_apply_state(patch)


def wizard_guided_setup_apply_preset(preset: str) -> dict:
    return guided_setup_apply_preset(preset)

def wizard_guided_setup_apply_preset_state(preset: str) -> dict:
    guided_setup_apply_preset(preset)
    return guided_setup_state()

def wizard_guided_setup_page_data() -> dict:
    state = wizard_guided_setup_state()
    return {
        "summary": state.get("summary", {}),
        "preflight": state.get("preflight", {}),
        "status": state.get("status", {}),
    }

def render_guided_setup_panel(ui) -> dict:
    action = ui.get("action")
    if action == "apply_preset":
        state = wizard_guided_setup_apply_preset_state(str(ui.get("preset", "safe_paper")))
    elif action == "apply_patch":
        state = wizard_guided_setup_apply_state(ui.get("patch"))
    elif action == "refresh":
        state = wizard_guided_setup_page_data()
    else:
        state = wizard_guided_setup_page_data()

    summary = state.get("summary", {}) or {}
    preflight = state.get("preflight", {}) or {}
    status = state.get("status", {}) or {}

    ui["summary"] = summary
    ui["preflight"] = preflight
    ui["status"] = status
    ui["last_action"] = action or "load"

    return state

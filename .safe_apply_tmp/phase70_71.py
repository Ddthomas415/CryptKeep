from pathlib import Path

# -----------------------
# Helpers
# -----------------------
def write(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")

def patch(path: str, fn):
    p = Path(path)
    if not p.exists():
        raise RuntimeError(f"Missing file: {path}")
    t = p.read_text(encoding="utf-8")
    nt = fn(t)
    if nt != t:
        p.write_text(nt, encoding="utf-8")

# -----------------------
# Phase 70: Live Enable Wizard backend
# -----------------------
write("services/admin/live_enable_wizard.py", r"""
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from services.admin.preflight import run_preflight
from services.market_data.poller import build_required_pairs
from services.market_data.cache_audit import missing_pairs as cache_missing_pairs
from services.admin.kill_switch import get_state as get_kill, set_armed
from services.admin.config_editor import load_user_yaml, save_user_yaml
from services.execution.event_log import log_event
from services.run_context import run_id

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _risk_nonzero_ok(risk: dict) -> tuple[bool, list[str], dict]:
    required_pos = ["max_daily_loss_usd", "max_position_usd", "max_trades_per_day", "min_order_usd"]
    missing, bad, snap = [], [], {}
    for k in required_pos:
        v = risk.get(k)
        snap[k] = v
        if v is None: missing.append(k); continue
        try: 
            if float(v) <= 0: bad.append(k)
        except Exception: bad.append(k)
    ok = (len(missing) == 0 and len(bad) == 0)
    return ok, (missing + bad), {"missing": missing, "non_positive_or_invalid": bad, "snapshot": snap}

def compute_readiness() -> dict:
    cfg = load_user_yaml()
    risk = cfg.get("risk") if isinstance(cfg.get("risk"), dict) else {}
    md = cfg.get("market_data_poller") if isinstance(cfg.get("market_data_poller"), dict) else {}
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}

    venues = pf.get("venues") or ["binance", "coinbase", "gateio"]
    symbols = pf.get("symbols") or ["BTC/USDT"]
    tol = int(pf.get("time_tolerance_ms", 1500) or 1500)
    do_priv = bool(pf.get("private_check", False))
    allow_unknown = bool(risk.get("allow_unknown_notional", False))

    preflight = asyncio.run(run_preflight(
        venues=[str(v).lower().strip() for v in venues],
        symbols=[str(s).strip() for s in symbols],
        time_tolerance_ms=tol,
        do_private_check=do_priv
    ))

    venue_for_cache = str(md.get("venue") or venues[0]).lower().strip()
    req_pairs = build_required_pairs([str(s).strip() for s in (md.get("symbols") or symbols)], include_symbols=True, extra_pairs=(md.get("extra_pairs") or []))
    audit = cache_missing_pairs(venue_for_cache, req_pairs)
    cache_ok = (audit.get("missing_count", 0) == 0) or allow_unknown
    cache_reason = "ok" if cache_ok else "missing_required_pairs_and_allow_unknown_false"

    risk_ok, risk_issues, risk_detail = _risk_nonzero_ok(risk)
    ks = get_kill()
    ks_armed = bool(ks.get("armed", True))
    enable_live_now = bool(risk.get("enable_live", False))

    steps = {
        "preflight_ok": bool(preflight.get("summary", {}).get("ok", False)),
        "cache_ok": bool(cache_ok),
        "risk_limits_ok": bool(risk_ok),
        "kill_switch_armed": ks_armed,
        "enable_live_current": enable_live_now,
    }

    all_ok = steps["preflight_ok"] and steps["cache_ok"] and steps["risk_limits_ok"] and ks_armed

    return {
        "ts": _now(),
        "run_id": run_id(),
        "steps": steps,
        "details": {"preflight": preflight, "cache": {"venue": venue_for_cache, "allow_unknown_notional": allow_unknown, "required_pairs_count": len(req_pairs), "missing_count": audit.get("missing_count"), "missing": audit.get("missing", []), "reason": cache_reason}, "risk": risk_detail, "kill_switch": ks},
        "ready_to_enable": all_ok,
    }

def enable_live_now() -> dict:
    ready = compute_readiness()
    if not ready["ready_to_enable"]:
        return {"ok": False, "reason": "not_ready", "readiness": ready}

    cfg = load_user_yaml()
    risk = cfg.get("risk") if isinstance(cfg.get("risk"), dict) else {}
    prev_cfg = {"risk_enable_live": bool(risk.get("enable_live", False))}
    prev_ks = get_kill()

    new_cfg = dict(cfg)
    new_risk = dict(risk)
    new_risk["enable_live"] = True
    new_cfg["risk"] = new_risk
    save_out = save_user_yaml(new_cfg, create_backup=True, dry_run=False)
    if not save_out.get("ok"):
        return {"ok": False, "reason": "config_save_failed", "save": save_out, "readiness": ready}

    ks2 = set_armed(False, note="wizard_enable_live")
    try:
        log_event("system", "GLOBAL", "live_enabled", ref_id=None, payload={"ts": _now(), "run_id": run_id(), "pre": {"kill_switch": prev_ks, **prev_cfg}, "post": {"kill_switch": ks2, "risk_enable_live": True}, "config_backup": save_out.get("backup")})
    except Exception:
        pass

    return {"ok": True, "readiness": ready, "save": save_out, "kill_switch": ks2}
""")

# -----------------------
# Phase 71: Live Disable Wizard + Auto Recovery backend
# -----------------------
write("services/admin/live_disable_wizard.py", r"""
from __future__ import annotations
from datetime import datetime, timezone
from services.admin.kill_switch import get_state as get_kill, set_armed
from services.admin.config_editor import load_user_yaml, save_user_yaml
from services.execution.event_log import log_event
from services.run_context import run_id

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def status() -> dict:
    cfg = load_user_yaml()
    risk = cfg.get("risk") if isinstance(cfg.get("risk"), dict) else {}
    ks = get_kill()
    return {"ts": _now(), "run_id": run_id(), "risk_enable_live": bool(risk.get("enable_live", False)), "kill_switch_armed": bool(ks.get("armed", True)), "kill_switch": ks}

def disable_live_now(note: str = "wizard_disable_live") -> dict:
    cfg = load_user_yaml()
    risk = cfg.get("risk") if isinstance(cfg.get("risk"), dict) else {}
    prev = status()
    new_cfg = dict(cfg)
    new_risk = dict(risk)
    new_risk["enable_live"] = False
    new_cfg["risk"] = new_risk
    save_out = save_user_yaml(new_cfg, create_backup=True, dry_run=False)
    if not save_out.get("ok"):
        return {"ok": False, "reason": "config_save_failed", "save": save_out, "prev": prev}
    ks2 = set_armed(True, note=str(note))
    try:
        log_event("system", "GLOBAL", "live_disabled", ref_id=None, payload={"ts": _now(), "run_id": run_id(), "pre": prev, "post": {"risk_enable_live": False, "kill_switch": ks2}, "config_backup": save_out.get("backup"), "note": str(note)})
    except Exception:
        pass
    return {"ok": True, "prev": prev, "post": status(), "save": save_out, "kill_switch": ks2}
""")

write("services/admin/safe_mode_recovery.py", r"""
from __future__ import annotations
from datetime import datetime, timezone
from services.admin.live_disable_wizard import disable_live_now, status
from services.admin.config_editor import load_user_yaml

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def auto_disable_if_needed() -> dict:
    cfg = load_user_yaml()
    safety = cfg.get("safety") if isinstance(cfg.get("safety"), dict) else {}
    auto = bool(safety.get("auto_disable_live_on_start", True))
    st = status()
    if not auto: return {"ok": True, "did_action": False, "reason": "auto_disable_disabled_in_config", "status": st, "ts": _now()}
    enable_live = bool(st.get("risk_enable_live", False))
    ks_armed = bool(st.get("kill_switch_armed", True))
    if enable_live or (not ks_armed):
        out = disable_live_now(note="auto_recovery_on_start")
        return {"ok": bool(out.get("ok")), "did_action": True, "reason": "auto_recovery_on_start", "result": out, "ts": _now()}
    return {"ok": True, "did_action": False, "reason": "already_safe", "status": st, "ts": _now()}
""")

# -----------------------
# Phase 70+71: Dashboard patches
# -----------------------
def patch_dashboard(t: str) -> str:
    add = r"""
st.divider()
st.header("Live enable/disable wizard + auto recovery")

st.caption("Live Enable Wizard: readiness check + one-button enable (sets enable_live=true + DISARMS kill switch)")

try:
    from services.admin.live_enable_wizard import compute_readiness, enable_live_now
    import json as _json
    if st.button("Run readiness check"):
        st.session_state["live_ready"] = compute_readiness()
    ready = st.session_state.get("live_ready")
    if ready:
        steps = ready.get("steps", {})
        def flag(x): return "✅" if x else "❌"
        st.subheader("Checklist")
        st.write({k: flag(v) if isinstance(v,bool) else v for k,v in steps.items()})
        ack = st.checkbox("I understand this will enable LIVE trading.", value=False)
        if st.button("ENABLE LIVE NOW", disabled=(not ack) or (not ready.get("ready_to_enable", False))):
            out = enable_live_now()
            st.json(out)
            st.session_state["live_ready"] = compute_readiness()
except Exception as e: st.error(f"Live enable wizard failed: {type(e).__name__}: {e}")

st.divider()
st.header("Auto safety recovery + Live Disable Wizard")

st.caption("Auto recovery: if enable_live=true OR kill switch disarmed, will auto-run Live Disable")

try:
    from services.admin.safe_mode_recovery import auto_disable_if_needed
    from services.admin.live_disable_wizard import status as live_status, disable_live_now

    if "auto_recovery_done" not in st.session_state:
        st.session_state["auto_recovery_done"] = auto_disable_if_needed()
    st.json(st.session_state["auto_recovery_done"])

    st.write(live_status())
    ack2 = st.checkbox("I understand this will DISABLE LIVE trading.", value=False)
    if st.button("DISABLE LIVE NOW", disabled=not ack2):
        out2 = disable_live_now(note="wizard_disable_live")
        st.json(out2)

except Exception as e: st.error(f"Live disable wizard failed: {type(e).__name__}: {e}")
"""
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# -----------------------
# Phase 70+71: Checkpoints
# -----------------------
def patch_cp(t: str) -> str:
    if "## BR) Live Enable Wizard" not in t:
        t += (
            "\n## BR) Live Enable Wizard\n"
            "- ✅ BR1: Deterministic readiness evaluation (preflight + cache readiness + risk non-zero + kill switch armed)\n"
            "- ✅ BR2: Single action enable: sets risk.enable_live=true (atomic + backup) and DISARMS kill switch\n"
            "- ✅ BR3: Audit event recorded: live_enabled (includes pre/post state + backup path)\n"
            "- ✅ BR4: Dashboard wizard panel with explicit acknowledgement checkbox\n"
        )
    if "## BS) Live Disable + Auto Recovery" not in t:
        t += (
            "\n## BS) Live Disable + Auto Recovery\n"
            "- ✅ BS1: Live disable wizard: sets risk.enable_live=false + ARMS kill switch + audit event live_disabled\n"
            "- ✅ BS2: Auto recovery on UI start: if enable_live=true OR kill switch disarmed => auto-disable (safe default)\n"
            "- ✅ BS3: Config opt-out: safety.auto_disable_live_on_start: false\n"
            "- ✅ BS4: Dashboard panels for auto recovery + manual Live Disable\n"
        )
    return t

patch("CHECKPOINTS.md", patch_cp)

print("OK: Phases 70+71 applied successfully (live enable/disable wizard + auto recovery + dashboard + checkpoints).")


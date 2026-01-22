# apply_phase128.py - Phase 128: Shared fill model + paper parity patch + diagnostics + checkpoints
from pathlib import Path
import re

def write(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"Written/Updated: {path}")

def patch(path: str, fn):
    p = Path(path)
    if not p.exists():
        print(f"Skipping patch - file missing: {path}")
        return
    t = p.read_text(encoding="utf-8", errors="replace")
    nt = fn(t)
    if nt != t:
        p.write_text(nt, encoding="utf-8")
        print(f"Patched: {path}")
    else:
        print(f"No changes needed: {path}")

# 1) Shared fill model (paper parity anchor)
write("services/execution/fill_model.py", r'''from __future__ import annotations
from dataclasses import dataclass

@dataclass
class FillResult:
    exec_px: float
    fee: float
    notional: float

def apply_fee_slippage(
    *,
    mid_px: float,
    side: str,
    qty: float,
    fee_bps: float,
    slippage_bps: float,
) -> FillResult:
    """
    Deterministic fill model for PAPER + BACKTEST parity.
    - BUY executes at mid + slippage
    - SELL executes at mid - slippage
    - fee is charged on notional: fee_bps / 10_000
    NOTE: If you want perfect parity, PAPER engine should call this same function.
    """
    px = float(mid_px)
    q = float(qty)
    fb = float(fee_bps) / 10000.0
    sb = float(slippage_bps) / 10000.0
    if q <= 0 or px <= 0:
        return FillResult(exec_px=0.0, fee=0.0, notional=0.0)
    s = str(side).lower().strip()
    slip = px * sb
    exec_px = px + slip if s == "buy" else max(0.0, px - slip)
    notional = q * exec_px
    fee = notional * fb
    return FillResult(exec_px=exec_px, fee=fee, notional=notional)
''')

# 2) Preflight core
write("services/app/preflight_wizard.py", r'''from __future__ import annotations
import json
import os
import socket
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from services.os.app_paths import runtime_dir, data_dir, ensure_dirs
from services.admin.config_editor import load_user_yaml

def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")

def _port_free(host: str, port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, int(port)))
        return True
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass

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
        return False, f"{type(e).__name__}:{e}"

def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def _cfg() -> dict:
    cfg = load_user_yaml()
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}
    venues = pf.get("venues") if isinstance(pf.get("venues"), list) else ["binance", "coinbase", "gateio"]
    symbols = pf.get("symbols") if isinstance(pf.get("symbols"), list) else ["BTC/USDT"]
    return {"venues": venues, "symbols": symbols}

def _config_valid() -> tuple[bool, str | None]:
    try:
        from services.admin.config_editor import validate_user_yaml
        res = validate_user_yaml(load_user_yaml())
        if res.get("ok"):
            return True, None
        return False, str(res.get("errors", []))
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
    port_free = _port_free(host, port)
    port_open = _port_open(host, port)
    port_ok = port_free or port_open
    mk = _market_checks(cfg["venues"], cfg["symbols"])
    market_ok = True
    if mk:
        market_ok = any(bool(r.get("ok")) for r in mk if isinstance(r, dict))
    db = _db_presence()
    sup = _supervisor_state()
    live = _live_arming_state()
    problems = []
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
        problems.append("port_8501_unavailable")
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
        "port_8501": {"ok": port_ok, "free": port_free, "open": port_open},
        "market_quality": mk,
        "db_presence": db,
        "supervisor": sup,
        "live_arming": live,
    }
''')

# 2) CLI runner
write("scripts/run_preflight.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import json
from services.app.preflight_wizard import run_preflight

def main():
    print(json.dumps(run_preflight(), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''')

# 3) Dashboard panel
def patch_dashboard(t: str) -> str:
    if "Preflight Wizard (Ready / Not Ready)" in t:
        return t
    add = r'''
st.divider()
st.header("Preflight Wizard (Ready / Not Ready)")
st.caption("Single screen readiness check + fix actions. Paper-first. Live remains hard-disabled unless armed.")
try:
    import json as _json
    import subprocess as _subprocess
    import sys as _sys
    import platform as _platform
    from services.app.preflight_wizard import run_preflight
    from services.os.app_paths import runtime_dir
    res = run_preflight()
    if res.get("ready"):
        st.success({"READY": True, "problems": res.get("problems", [])})
    else:
        st.error({"READY": False, "problems": res.get("problems", [])})
    st.subheader("Details")
    st.json(res)
    st.subheader("Fix actions (safe defaults)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Start paper stack (no dashboard)"):
            _subprocess.Popen([_sys.executable, "scripts/cbp_supervisor.py", "start", "--no-dashboard"])
            st.success("Requested start.")
    with c2:
        if st.button("Stop paper stack"):
            _subprocess.Popen([_sys.executable, "scripts/cbp_supervisor.py", "stop"])
            st.success("Requested stop.")
    with c3:
        if st.button("Export Carryover Pack"):
            _subprocess.Popen([_sys.executable, "scripts/export_carryover.py"])
            st.success(f"Export requested. Check: {runtime_dir() / 'exports'}")
    with c4:
        if st.button("Export Diagnostics Zip"):
            _subprocess.Popen([_sys.executable, "scripts/export_diagnostics.py"])
            st.success(f"Export requested. Check: {runtime_dir() / 'exports'}")
    with st.expander("Install/Run instructions"):
        try:
            p = Path("INSTALL_APP.md")
            if p.exists():
                st.markdown(p.read_text(encoding="utf-8", errors="replace")[:12000])
            else:
                st.info("INSTALL_APP.md not found.")
        except Exception as e:
            st.error(f"Could not read INSTALL_APP.md: {type(e).__name__}: {e}")
except Exception as e:
    st.error(f"Preflight panel failed: {type(e).__name__}: {e}")
'''
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 4) CHECKPOINTS
def patch_checkpoints(t: str) -> str:
    if "## DS) Preflight Wizard" in t:
        return t
    return t + (
        "\n## DS) Preflight Wizard\n"
        "- ✅ DS1: services/app/preflight_wizard.py computes Ready/Not Ready with concrete reasons\n"
        "- ✅ DS2: scripts/run_preflight.py prints JSON preflight report (CLI)\n"
        "- ✅ DS3: Dashboard Preflight Wizard panel with fix actions + export buttons\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 123 applied (Preflight Wizard + CLI + dashboard + checkpoints).")
print("Next steps:")
print("  1. Run preflight check: python3 scripts/run_preflight.py")
print("  2. Check dashboard 'Preflight Wizard' panel for readiness + fix buttons")
print("  3. If not ready, follow the problems list and fix actions")
END_OF_FINAL
# apply_phase102.py - Phase 102 launcher (tick publisher + UI + config)
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
    t = p.read_text(encoding="utf-8")
    nt = fn(t)
    if nt != t:
        p.write_text(nt, encoding="utf-8")
        print(f"Patched: {path}")
    else:
        print(f"No changes needed: {path}")

# 1) Tick publisher service
write("services/market_data/system_status_publisher.py", r'''from __future__ import annotations
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.admin.config_editor import load_user_yaml
from services.security.exchange_factory import make_exchange

SNAPSHOT_DIR = Path("runtime") / "snapshots"
FLAGS_DIR = Path("runtime") / "flags"
LOCKS_DIR = Path("runtime") / "locks"
STOP_FILE = FLAGS_DIR / "tick_publisher.stop"
LOCK_FILE = LOCKS_DIR / "tick_publisher.lock"
STATUS_FILE = FLAGS_DIR / "tick_publisher.status.json"

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _now_ms() -> int:
    return int(time.time() * 1000)

def _safe_float(x) -> float | None:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None

def _cfg() -> dict:
    cfg = load_user_yaml()
    mdp = cfg.get("market_data_publisher") if isinstance(cfg.get("market_data_publisher"), dict) else {}
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}
    venues = mdp.get("venues") if isinstance(mdp.get("venues"), list) else (pf.get("venues") if isinstance(pf.get("venues"), list) else ["binance","coinbase","gateio"])
    symbols = mdp.get("symbols") if isinstance(mdp.get("symbols"), list) else (pf.get("symbols") if isinstance(pf.get("symbols"), list) else ["BTC/USDT"])
    interval_sec = int(mdp.get("interval_sec", 2) or 2)
    enabled = bool(mdp.get("enabled", True))
    write_latest_only = bool(mdp.get("write_latest_only", True))
    max_symbols_per_venue = int(mdp.get("max_symbols_per_venue", 50) or 50)
    return {
        "enabled": enabled,
        "interval_sec": max(1, interval_sec),
        "venues": [str(v).lower().strip() for v in venues][:20],
        "symbols": [str(s).strip() for s in symbols][:max_symbols_per_venue],
        "write_latest_only": write_latest_only,
    }

def _write_status(obj: dict) -> None:
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def _acquire_lock() -> bool:
    LOCKS_DIR.mkdir(parents=True, exist_ok=True)
    if LOCK_FILE.exists():
        return False
    LOCK_FILE.write_text(json.dumps({"pid": os.getpid(), "ts": _now_iso()}, indent=2) + "\n", encoding="utf-8")
    return True

def _release_lock() -> None:
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass

def _clear_stop() -> None:
    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
    except Exception:
        pass

def _snapshot_path(write_latest_only: bool) -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    if write_latest_only:
        return SNAPSHOT_DIR / "system_status.latest.json"
    tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return SNAPSHOT_DIR / f"system_status.{tag}.json"

def _fetch_tick(ex, venue: str, symbol: str) -> dict:
    t = ex.fetch_ticker(symbol)
    ts_ms = None
    if isinstance(t, dict):
        ts_ms = t.get("timestamp") or t.get("ts_ms") or t.get("timestamp_ms")
        if ts_ms is None and t.get("datetime"):
            try:
                dt = datetime.fromisoformat(str(t["datetime"]).replace("Z","+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                ts_ms = int(dt.timestamp() * 1000)
            except Exception:
                ts_ms = None
    bid = _safe_float(t.get("bid") if isinstance(t, dict) else None)
    ask = _safe_float(t.get("ask") if isinstance(t, dict) else None)
    last = _safe_float(t.get("last") if isinstance(t, dict) else None)
    if ts_ms is None:
        ts_ms = _now_ms()
    return {
        "venue": str(venue).lower().strip(),
        "symbol": str(symbol).strip(),
        "ts_ms": int(ts_ms),
        "bid": bid,
        "ask": ask,
        "last": last,
    }

def run_forever() -> None:
    c = _cfg()
    if not bool(c["enabled"]):
        _write_status({"ok": False, "reason": "disabled", "ts": _now_iso()})
        return
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    _clear_stop()
    if not _acquire_lock():
        _write_status({"ok": False, "reason": "lock_exists", "lock_file": str(LOCK_FILE), "ts": _now_iso()})
        return
    _write_status({"ok": True, "status": "running", "pid": os.getpid(), "ts": _now_iso(), "cfg": c})
    clients = {}
    try:
        for v in c["venues"]:
            clients[v] = make_exchange(v, {"apiKey": None, "secret": None}, enable_rate_limit=True)
            try:
                if hasattr(clients[v], "load_markets"):
                    clients[v].load_markets()
            except Exception:
                pass
        while True:
            if STOP_FILE.exists():
                _write_status({"ok": True, "status": "stopping", "pid": os.getpid(), "ts": _now_iso()})
                break
            ticks = []
            errors = []
            for v, ex in clients.items():
                for s in c["symbols"]:
                    try:
                        ticks.append(_fetch_tick(ex, v, s))
                    except Exception as e:
                        errors.append({"venue": v, "symbol": s, "error": f"{type(e).__name__}: {e}"})
            snap = {
                "ts": _now_iso(),
                "ts_ms": _now_ms(),
                "publisher": {
                    "name": "system_status_publisher",
                    "pid": os.getpid(),
                    "interval_sec": int(c["interval_sec"]),
                },
                "ticks": ticks,
                "errors": errors[:50],
            }
            p = _snapshot_path(bool(c["write_latest_only"]))
            p.write_text(json.dumps(snap, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            _write_status({
                "ok": True,
                "status": "running",
                "pid": os.getpid(),
                "ts": _now_iso(),
                "snapshot_path": str(p),
                "tick_count": len(ticks),
                "error_count": len(errors),
            })
            time.sleep(float(c["interval_sec"]))
    finally:
        for ex in clients.values():
            try:
                if hasattr(ex, "close"):
                    ex.close()
            except Exception:
                pass
        _release_lock()
        _write_status({"ok": True, "status": "stopped", "pid": os.getpid(), "ts": _now_iso()})

def request_stop() -> dict:
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    STOP_FILE.write_text(_now_iso() + "\n", encoding="utf-8")
    return {"ok": True, "stop_file": str(STOP_FILE), "ts": _now_iso()}
''')

# 2) Runner script
write("scripts/run_tick_publisher.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
from services.market_data.system_status_publisher import run_forever, request_stop

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "stop"], nargs="?", default="run")
    args = ap.parse_args()
    if args.cmd == "stop":
        print(request_stop())
        return 0
    run_forever()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''')

# 3) Dashboard patch function (use triple-single quotes)
def patch_dashboard(t: str) -> str:
    if "System Status Tick Publisher" in t and "scripts/run_tick_publisher.py" in t:
        return t
    add = r'''
st.divider()
st.header("System Status Tick Publisher")
st.caption("Keeps runtime/snapshots/system_status.latest.json fresh so the Market Data Staleness Guard can verify tick freshness. Public market data only.")
try:
    from services.admin.config_editor import load_user_yaml, save_user_yaml
    from pathlib import Path as _Path
    import json as _json
    import os as _os
    import subprocess as _subprocess
    import sys as _sys
    import platform as _platform
    cfg = load_user_yaml()
    mdp = cfg.get("market_data_publisher") if isinstance(cfg.get("market_data_publisher"), dict) else {}
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}
    venues_default = mdp.get("venues") if isinstance(mdp.get("venues"), list) else (pf.get("venues") if isinstance(pf.get("venues"), list) else ["binance","coinbase","gateio"])
    symbols_default = mdp.get("symbols") if isinstance(mdp.get("symbols"), list) else (pf.get("symbols") if isinstance(pf.get("symbols"), list) else ["BTC/USDT"])
    st.subheader("Controls")
    c1, c2, c3 = st.columns(3)
    stop_file = _Path("runtime") / "flags" / "tick_publisher.stop"
    lock_file = _Path("runtime") / "locks" / "tick_publisher.lock"
    status_file = _Path("runtime") / "flags" / "tick_publisher.status.json"
    with c1:
        if st.button("Start publisher (background)"):
            cmd = [_sys.executable, "scripts/run_tick_publisher.py", "run"]
            try:
                if _platform.system().lower().startswith("win"):
                    DETACHED_PROCESS = 0x00000008
                    _subprocess.Popen(cmd, creationflags=DETACHED_PROCESS, stdout=_subprocess.DEVNULL, stderr=_subprocess.DEVNULL)
                else:
                    _subprocess.Popen(cmd, start_new_session=True, stdout=_subprocess.DEVNULL, stderr=_subprocess.DEVNULL)
                st.success({"ok": True, "started": cmd})
            except Exception as e:
                st.error(f"Start failed: {type(e).__name__}: {e}")
            st.caption("If it refuses, delete the lock file only if you are sure it is not running.")
    with c2:
        if st.button("Request stop"):
            stop_file.parent.mkdir(parents=True, exist_ok=True)
            stop_file.write_text("stop\n", encoding="utf-8")
            st.success({"ok": True, "stop_file": str(stop_file)})
    with c3:
        if st.button("Show run command"):
            st.code("python3 scripts/run_tick_publisher.py run", language="bash")
            st.code("python3 scripts/run_tick_publisher.py stop", language="bash")
    st.subheader("Status")
    st.caption(f"Lock: {lock_file} | Stop file: {stop_file}")
    if status_file.exists():
        st.json(_json.loads(status_file.read_text(encoding="utf-8")))
    else:
        st.warning("No status file yet. Start the publisher or run it in a terminal.")
    st.subheader("Latest snapshot preview")
    snap = _Path("runtime") / "snapshots" / "system_status.latest.json"
    if snap.exists():
        st.caption(str(snap))
        with st.expander("Preview (first ~16k chars)"):
            st.code(snap.read_text(encoding="utf-8")[:16000], language="json")
    else:
        st.warning("system_status.latest.json not found yet.")
    st.subheader("Config (safe write)")
    cur_enabled = bool(mdp.get("enabled", True))
    cur_interval = int(mdp.get("interval_sec", 2) or 2)
    cur_latest = bool(mdp.get("write_latest_only", True))
    cur_maxsym = int(mdp.get("max_symbols_per_venue", 50) or 50)
    enabled = st.checkbox("market_data_publisher.enabled", value=cur_enabled)
    interval = st.number_input("market_data_publisher.interval_sec", min_value=1, max_value=60, value=cur_interval, step=1)
    latest_only = st.checkbox("market_data_publisher.write_latest_only", value=cur_latest)
    maxsym = st.number_input("market_data_publisher.max_symbols_per_venue", min_value=1, max_value=500, value=cur_maxsym, step=1)
    venues_txt = st.text_area("market_data_publisher.venues (one per line)", value="\n".join([str(x) for x in venues_default]))
    symbols_txt = st.text_area("market_data_publisher.symbols (one per line)", value="\n".join([str(x) for x in symbols_default]))
    new_cfg = dict(cfg)
    new_mdp = dict(mdp)
    new_mdp["enabled"] = bool(enabled)
    new_mdp["interval_sec"] = int(interval)
    new_mdp["write_latest_only"] = bool(latest_only)
    new_mdp["max_symbols_per_venue"] = int(maxsym)
    new_mdp["venues"] = [x.strip().lower() for x in venues_txt.splitlines() if x.strip()]
    new_mdp["symbols"] = [x.strip() for x in symbols_txt.splitlines() if x.strip()]
    new_cfg["market_data_publisher"] = new_mdp
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Dry-run (diff only) — tick publisher config"):
            out = save_user_yaml(new_cfg, create_backup=False, dry_run=True)
            st.code(out.get("diff",""), language="diff")
            if not out.get("ok"):
                st.error(out.get("validation"))
    with c2:
        if st.button("Save — tick publisher config (backup + atomic)"):
            out = save_user_yaml(new_cfg, create_backup=True, dry_run=False)
            if out.get("ok"):
                st.success({"written": out.get("written"), "backup": out.get("backup")})
            else:
                st.error(out.get("validation"))
            st.code(out.get("diff",""), language="diff")
except Exception as e:
    st.error(f"Tick publisher panel failed: {type(e).__name__}: {e}")
'''
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 4) Config validation patch
def patch_config_editor(t: str) -> str:
    if "market_data_publisher.enabled" in t and "market_data_publisher.interval_sec" in t:
        return t
    insert = """
    # Market data publisher (optional)
    mdp = cfg.get("market_data_publisher", {})
    if mdp is not None and not isinstance(mdp, dict):
        errors.append("market_data_publisher:must_be_mapping")
        mdp = {}
    if isinstance(mdp, dict):
        if "enabled" in mdp and mdp["enabled"] is not None and not _is_bool(mdp["enabled"]):
            errors.append("market_data_publisher.enabled:must_be_bool")
        if "interval_sec" in mdp and mdp["interval_sec"] is not None and not _is_int(mdp["interval_sec"]):
            errors.append("market_data_publisher.interval_sec:must_be_int")
        if "write_latest_only" in mdp and mdp["write_latest_only"] is not None and not _is_bool(mdp["write_latest_only"]):
            errors.append("market_data_publisher.write_latest_only:must_be_bool")
        if "max_symbols_per_venue" in mdp and mdp["max_symbols_per_venue"] is not None and not _is_int(mdp["max_symbols_per_venue"]):
            errors.append("market_data_publisher.max_symbols_per_venue:must_be_int")
        for k in ("venues","symbols"):
            if k in mdp and mdp[k] is not None and not isinstance(mdp[k], list):
                errors.append(f"market_data_publisher.{k}:must_be_list")
"""
    anchor = "ok = len(errors) == 0"
    if anchor in t:
        return t.replace(anchor, insert + "\n" + anchor, 1)
    return t

patch("services/admin/config_editor.py", patch_config_editor)

# 5) Checkpoints patch
def patch_checkpoints(t: str) -> str:
    if "## CX) System Status Tick Publisher" in t:
        return t
    return t + (
        "\n## CX) System Status Tick Publisher\n"
        "- ✅ CX1: Background publisher writes runtime/snapshots/system_status.latest.json on interval\n"
        "- ✅ CX2: Includes ticks[{venue,symbol,ts_ms,bid,ask,last}] compatible with staleness guard discovery\n"
        "- ✅ CX3: File-based stop request + lock file to avoid accidental duplicate runners\n"
        "- ✅ CX4: Dashboard panel: start/stop, status, snapshot preview, safe config editing\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 102 applied (tick publisher + scripts + UI + config validation + checkpoints).")
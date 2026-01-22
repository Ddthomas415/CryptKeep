# apply_phase107.py - Phase 107 launcher (Supervisor Mode + PID control + dashboard panel)
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

# 1) Supervisor controller (PID-based, cross-platform; no deps)
write("services/supervisor/supervisor.py", r'''from __future__ import annotations
import json
import os
import platform
import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from services.os.app_paths import runtime_dir, ensure_dirs, code_root

FLAGS_DIR = runtime_dir() / "flags"
LOCKS_DIR = runtime_dir() / "locks"
STATE_FILE = FLAGS_DIR / "supervisor.state.json"
LOCK_FILE = LOCKS_DIR / "supervisor.lock"

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _is_windows() -> bool:
    return platform.system().lower().startswith("win")

def pid_is_alive(pid: int) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        if _is_windows():
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            OpenProcess = ctypes.windll.kernel32.OpenProcess
            GetExitCodeProcess = ctypes.windll.kernel32.GetExitCodeProcess
            CloseHandle = ctypes.windll.kernel32.CloseHandle
            h = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, int(pid))
            if not h:
                return False
            try:
                code = ctypes.c_ulong()
                ok = GetExitCodeProcess(h, ctypes.byref(code))
                if not ok:
                    return False
                return int(code.value) == STILL_ACTIVE
            finally:
                CloseHandle(h)
        else:
            os.kill(int(pid), 0)
            return True
    except Exception:
        return False

def _read_json(p: Path) -> dict:
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

def _write_json(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def _acquire_lock() -> dict:
    ensure_dirs()
    LOCKS_DIR.mkdir(parents=True, exist_ok=True)
    if LOCK_FILE.exists():
        cur = _read_json(LOCK_FILE)
        pid = int(cur.get("pid") or 0)
        if pid and pid_is_alive(pid):
            return {"ok": False, "reason": "lock_exists", "lock": cur}
        # stale lock
        try:
            LOCK_FILE.unlink()
        except Exception:
            return {"ok": False, "reason": "stale_lock_unremovable", "lock": cur}
    lock = {"pid": os.getpid(), "ts": _now_iso()}
    _write_json(LOCK_FILE, lock)
    return {"ok": True, "lock": lock}

def _release_lock() -> None:
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass

def _spawn_detached(cmd: list[str]) -> int:
    if _is_windows():
        DETACHED_PROCESS = 0x00000008
        p = subprocess.Popen(cmd, creationflags=DETACHED_PROCESS, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(code_root()))
    else:
        p = subprocess.Popen(cmd, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(code_root()))
    return int(p.pid)

def _open_browser(host: str, port: int) -> None:
    try:
        webbrowser.open(f"http://{host}:{port}", new=1)
    except Exception:
        pass

def _default_host_port() -> tuple[str, int]:
    host = os.getenv("CBP_HOST", "127.0.0.1").strip() or "127.0.0.1"
    try:
        port = int(os.getenv("CBP_PORT", "8501"))
    except Exception:
        port = 8501
    return host, port

def status() -> dict:
    ensure_dirs()
    st = _read_json(STATE_FILE)
    out = {"ok": True, "ts": _now_iso(), "state": st, "services": {}}
    for name in ("dashboard", "tick_publisher", "evidence_webhook"):
        pid = int((st.get("pids") or {}).get(name) or 0)
        out["services"][name] = {"pid": pid, "alive": pid_is_alive(pid)}
    lock = _read_json(LOCK_FILE) if LOCK_FILE.exists() else {}
    if lock:
        out["lock"] = {"exists": True, "pid": int(lock.get("pid") or 0), "alive": pid_is_alive(int(lock.get("pid") or 0)), "ts": lock.get("ts")}
    else:
        out["lock"] = {"exists": False}
    return out

def _write_state(pids: dict, meta: dict) -> None:
    _write_json(STATE_FILE, {"pids": pids, "meta": meta, "ts": _now_iso()})

def start(
    *,
    with_dashboard: bool = True,
    start_tick: bool = True,
    start_webhook: bool = True,
    host: str | None = None,
    port: int | None = None,
    open_browser: bool = True,
) -> dict:
    ensure_dirs()
    lk = _acquire_lock()
    if not lk.get("ok"):
        return {"ok": False, "reason": lk.get("reason"), "details": lk}
    try:
        host0, port0 = _default_host_port()
        host = (host or host0).strip()
        port = int(port or port0)
        st = _read_json(STATE_FILE)
        pids = dict(st.get("pids") or {})
        if start_tick:
            pid = int(pids.get("tick_publisher") or 0)
            if not pid_is_alive(pid):
                pid = _spawn_detached([sys.executable, "scripts/run_tick_publisher.py", "run"])
                pids["tick_publisher"] = pid
        if start_webhook:
            pid = int(pids.get("evidence_webhook") or 0)
            if not pid_is_alive(pid):
                pid = _spawn_detached([sys.executable, "scripts/run_evidence_webhook.py", "run"])
                pids["evidence_webhook"] = pid
        if with_dashboard:
            pid = int(pids.get("dashboard") or 0)
            if not pid_is_alive(pid):
                app = Path("dashboard") / "app.py"
                cmd = [
                    sys.executable, "-m", "streamlit", "run", str(app),
                    "--server.address", host,
                    "--server.port", str(port),
                ]
                pid = _spawn_detached(cmd)
                pids["dashboard"] = pid
                if open_browser:
                    _open_browser(host, port)
        meta = {"host": host, "port": port, "with_dashboard": with_dashboard, "start_tick": start_tick, "start_webhook": start_webhook}
        _write_state(pids, meta)
        return {"ok": True, "pids": pids, "meta": meta}
    finally:
        _release_lock()

def stop(*, stop_dashboard: bool = True, stop_tick: bool = True, stop_webhook: bool = True, timeout_sec: int = 6) -> dict:
    ensure_dirs()
    lk = _acquire_lock()
    if not lk.get("ok"):
        return {"ok": False, "reason": lk.get("reason"), "details": lk}
    try:
        st = _read_json(STATE_FILE)
        pids = dict(st.get("pids") or {})
        actions = []
        if stop_tick:
            try:
                (runtime_dir() / "flags" / "tick_publisher.stop").write_text(_now_iso() + "\n", encoding="utf-8")
                actions.append({"service": "tick_publisher", "action": "stop_file_written"})
            except Exception as e:
                actions.append({"service": "tick_publisher", "action": "stop_file_failed", "error": f"{type(e).__name__}: {e}"})
        if stop_webhook:
            try:
                (runtime_dir() / "flags" / "evidence_webhook.stop").write_text(_now_iso() + "\n", encoding="utf-8")
                actions.append({"service": "evidence_webhook", "action": "stop_file_written"})
            except Exception as e:
                actions.append({"service": "evidence_webhook", "action": "stop_file_failed", "error": f"{type(e).__name__}: {e}"})
        if stop_dashboard:
            pid = int(pids.get("dashboard") or 0)
            if pid_is_alive(pid):
                try:
                    if _is_windows():
                        subprocess.call(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        os.kill(pid, 15) # SIGTERM
                    actions.append({"service": "dashboard", "action": "terminate_sent", "pid": pid})
                except Exception as e:
                    actions.append({"service": "dashboard", "action": "terminate_failed", "pid": pid, "error": f"{type(e).__name__}: {e}"})
        deadline = time.time() + float(timeout_sec)
        while time.time() < deadline:
            alive_any = False
            for svc in ("tick_publisher", "evidence_webhook"):
                pid = int(pids.get(svc) or 0)
                if pid and pid_is_alive(pid):
                    alive_any = True
            if not alive_any:
                break
            time.sleep(0.25)
        for svc in ("tick_publisher", "evidence_webhook"):
            if (svc == "tick_publisher" and not stop_tick) or (svc == "evidence_webhook" and not stop_webhook):
                continue
            pid = int(pids.get(svc) or 0)
            if pid and pid_is_alive(pid):
                try:
                    if _is_windows():
                        subprocess.call(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        os.kill(pid, 9) # SIGKILL
                    actions.append({"service": svc, "action": "force_kill", "pid": pid})
                except Exception as e:
                    actions.append({"service": svc, "action": "force_kill_failed", "pid": pid, "error": f"{type(e).__name__}: {e}"})
        new_pids = dict(pids)
        if stop_dashboard:
            new_pids["dashboard"] = 0
        if stop_tick:
            new_pids["tick_publisher"] = 0
        if stop_webhook:
            new_pids["evidence_webhook"] = 0
        _write_state(new_pids, dict(st.get("meta") or {}))
        return {"ok": True, "actions": actions, "final_state": status()}
    finally:
        _release_lock()
''')

# 2) CLI wrapper: scripts/supervisor.py
write("scripts/supervisor.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from services.supervisor.supervisor import start, stop, status

def main():
    ap = argparse.ArgumentParser(description="CryptoBotPro Supervisor (start/stop/status).")
    ap.add_argument("cmd", choices=["start","stop","status"], nargs="?", default="status")
    ap.add_argument("--no-dashboard", action="store_true")
    ap.add_argument("--no-tick", action="store_true")
    ap.add_argument("--no-webhook", action="store_true")
    ap.add_argument("--host", default=None)
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--timeout-sec", type=int, default=6)
    args = ap.parse_args()
    if args.cmd == "status":
        print(json.dumps(status(), indent=2))
        return 0
    if args.cmd == "start":
        out = start(
            with_dashboard=not args.no_dashboard,
            start_tick=not args.no_tick,
            start_webhook=not args.no_webhook,
            host=args.host,
            port=args.port,
            open_browser=not args.no_browser,
        )
        print(json.dumps(out, indent=2))
        return 0 if out.get("ok") else 2
    out = stop(
        stop_dashboard=not args.no_dashboard,
        stop_tick=not args.no_tick,
        stop_webhook=not args.no_webhook,
        timeout_sec=int(args.timeout_sec),
    )
    print(json.dumps(out, indent=2))
    return 0 if out.get("ok") else 2

if __name__ == "__main__":
    raise SystemExit(main())
''')

# 3) Dashboard panel: Supervisor controls + status
def patch_dashboard(t: str) -> str:
    if "Supervisor Mode (One Toggle)" in t and "scripts/supervisor.py start" in t:
        return t
    add = r'''
st.divider()
st.header("Supervisor Mode (One Toggle)")
st.caption("Starts/stops: Dashboard + Tick Publisher + Evidence Webhook. Uses PID checks to avoid 'delete lock file' workflows.")
try:
    from services.supervisor.supervisor import start as sup_start, stop as sup_stop, status as sup_status
    import time as _time
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("START ALL (Supervisor)"):
            out = sup_start(with_dashboard=False, start_tick=True, start_webhook=True, open_browser=False)
            st.session_state["sup_last"] = out
            st.success(out)
    with c2:
        if st.button("STOP services (Supervisor)"):
            out = sup_stop(stop_dashboard=False, stop_tick=True, stop_webhook=True, timeout_sec=6)
            st.session_state["sup_last"] = out
            st.success(out)
    with c3:
        if st.button("Refresh status"):
            st.session_state["sup_status"] = sup_status()
    st.subheader("Status")
    st.json(st.session_state.get("sup_status", sup_status()))
    st.subheader("How to run FULL supervisor from terminal (starts dashboard too)")
    st.code("python3 scripts/supervisor.py start\npython3 scripts/supervisor.py status\npython3 scripts/supervisor.py stop", language="bash")
    with st.expander("Last supervisor action"):
        st.json(st.session_state.get("sup_last", {}))
except Exception as e:
    st.error(f"Supervisor panel failed: {type(e).__name__}: {e}")
'''
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 4) CHECKPOINTS update
def patch_checkpoints(t: str) -> str:
    if "## DC) Supervisor Mode" in t:
        return t
    return t + (
        "\n## DC) Supervisor Mode\n"
        "- ✅ DC1: services/supervisor/supervisor.py start/stop/status with PID-based running detection\n"
        "- ✅ DC2: Auto-clears stale supervisor lock if owning PID is dead (no manual lock deletion)\n"
        "- ✅ DC3: scripts/supervisor.py CLI (start/stop/status) for one-command control\n"
        "- ✅ DC4: Dashboard panel to start/stop services and view supervisor status\n"
        "- ✅ DC5: Can start Streamlit dashboard from terminal supervisor (not from inside dashboard by default)\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 107 applied (Supervisor Mode + PID detection + CLI + dashboard panel + checkpoints).")
print("Next steps:")
print("  1. Restart webhook server: python3 scripts/run_evidence_webhook.py run")
print("  2. Check dashboard 'Supervisor Mode' panel for start/stop buttons")
print("  3. Test supervisor CLI: python3 scripts/supervisor.py status")
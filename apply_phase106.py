# apply_phase106.py - Phase 106 launcher (webhook graceful stop + dashboard stop panel)
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

# 1) Patch evidence webhook server to support stop-file graceful shutdown + lock + status
def patch_webhook_server(t: str) -> str:
    if "evidence_webhook.stop" in t and "request_stop()" in t and "LOCK_FILE" in t and "handle_request" in t:
        return t
    if "from services.os.app_paths import runtime_dir, ensure_dirs" not in t:
        t = t.replace(
            "from http.server import BaseHTTPRequestHandler, HTTPServer\n",
            "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
            "from services.os.app_paths import runtime_dir, ensure_dirs\n",
            1
        )
    if "STOP_FILE" not in t:
        insert = """
FLAGS_DIR = runtime_dir() / "flags"
LOCKS_DIR = runtime_dir() / "locks"
STOP_FILE = FLAGS_DIR / "evidence_webhook.stop"
LOCK_FILE = LOCKS_DIR / "evidence_webhook.lock"
STATUS_FILE = FLAGS_DIR / "evidence_webhook.status.json"

def _write_status(obj: dict) -> None:
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\\n", encoding="utf-8")

def _acquire_lock() -> bool:
    LOCKS_DIR.mkdir(parents=True, exist_ok=True)
    if LOCK_FILE.exists():
        return False
    LOCK_FILE.write_text(json.dumps({"pid": os.getpid(), "ts": int(time.time())}, indent=2) + "\\n", encoding="utf-8")
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
"""
        t = t.replace("def _compute_sig(secret: str, ts: str, body: bytes) -> str:\n", insert + "\n\ndef _compute_sig(secret: str, ts: str, body: bytes) -> str:\n", 1)
    if "def run():" in t:
        t = re.sub(
            r"def run\(\):\n(?:.|\n)*?if __name__ == \"__main__\":\n\s*run\(\)\n",
            """def run():
    ensure_dirs()
    cfg = _cfg()
    _bind_guard(cfg)
    if not cfg.get("enabled", True):
        _write_status({"ok": False, "reason": "webhook_disabled"})
        return
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    _clear_stop()
    if not _acquire_lock():
        _write_status({"ok": False, "reason": "lock_exists", "lock_file": str(LOCK_FILE)})
        return
    host = cfg["host"]
    port = int(cfg["port"])
    httpd = HTTPServer((host, port), Handler)
    httpd.timeout = 1.0  # allow periodic stop-file checks
    _write_status({"ok": True, "status": "running", "host": host, "port": port, "hmac_required": bool(cfg["require_hmac"])})
    print(f"[evidence_webhook] listening on http://{host}:{port}/evidence (hmac_required={cfg['require_hmac']})")
    try:
        while True:
            if STOP_FILE.exists():
                _write_status({"ok": True, "status": "stopping", "host": host, "port": port})
                break
            httpd.handle_request()
    finally:
        try:
            httpd.server_close()
        except Exception:
            pass
        _release_lock()
        _write_status({"ok": True, "status": "stopped", "host": host, "port": port})

def request_stop() -> dict:
    ensure_dirs()
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    STOP_FILE.write_text(str(int(time.time())) + "\\n", encoding="utf-8")
    return {"ok": True, "stop_file": str(STOP_FILE)}

if __name__ == "__main__":
    run()
""",
            t,
            flags=re.M | re.S
        )
    if "import os" not in t:
        t = t.replace("import hmac\n", "import hmac\nimport os\n", 1)
    if "import time" not in t:
        t = t.replace("import hashlib\n", "import hashlib\nimport time\n", 1)
    return t

patch("services/evidence/webhook_server.py", patch_webhook_server)

# 2) Add run/stop script for evidence webhook
write("scripts/run_evidence_webhook.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
from services.evidence.webhook_server import run, request_stop

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run","stop"], nargs="?", default="run")
    args = ap.parse_args()
    if args.cmd == "stop":
        print(request_stop())
        return 0
    run()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''')

# 3) Dashboard: add stop-services panel
def patch_dashboard(t: str) -> str:
    if "Service Controls (Stop Without Killing the App)" in t and "scripts/run_evidence_webhook.py stop" in t:
        return t
    add = r'''
st.divider()
st.header("Service Controls (Stop Without Killing the App)")
st.caption("Graceful stop uses stop-files. This is safer than killing processes when running as a packaged desktop app.")
try:
    from pathlib import Path as _Path
    import json as _json
    import time as _time
    # Tick publisher files
    tick_stop = _Path("runtime") / "flags" / "tick_publisher.stop"
    tick_status = _Path("runtime") / "flags" / "tick_publisher.status.json"
    tick_lock = _Path("runtime") / "locks" / "tick_publisher.lock"
    # Evidence webhook files
    wh_stop = _Path("runtime") / "flags" / "evidence_webhook.stop"
    wh_status = _Path("runtime") / "flags" / "evidence_webhook.status.json"
    wh_lock = _Path("runtime") / "locks" / "evidence_webhook.lock"
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Request STOP: Tick Publisher"):
            tick_stop.parent.mkdir(parents=True, exist_ok=True)
            tick_stop.write_text(str(int(_time.time())) + "\n", encoding="utf-8")
            st.success({"ok": True, "stop_file": str(tick_stop)})
    with c2:
        if st.button("Request STOP: Evidence Webhook"):
            wh_stop.parent.mkdir(parents=True, exist_ok=True)
            wh_stop.write_text(str(int(_time.time())) + "\n", encoding="utf-8")
            st.success({"ok": True, "stop_file": str(wh_stop)})
    with c3:
        if st.button("Show stop commands"):
            st.code("python3 scripts/run_tick_publisher.py stop\npython3 scripts/run_evidence_webhook.py stop", language="bash")
    st.subheader("Status snapshots")
    cc1, cc2 = st.columns(2)
    with cc1:
        st.caption(f"Tick lock: {tick_lock}")
        if tick_status.exists():
            st.json(_json.loads(tick_status.read_text(encoding='utf-8')))
        else:
            st.info("No tick publisher status file yet.")
    with cc2:
        st.caption(f"Webhook lock: {wh_lock}")
        if wh_status.exists():
            st.json(_json.loads(wh_status.read_text(encoding='utf-8')))
        else:
            st.info("No webhook status file yet.")
except Exception as e:
    st.error(f"Service controls panel failed: {type(e).__name__}: {e}")
'''
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 4) CHECKPOINTS update
def patch_checkpoints(t: str) -> str:
    if "## DB) Graceful Stop for Services" in t:
        return t
    return t + (
        "\n## DB) Graceful Stop for Services\n"
        "- ✅ DB1: Evidence webhook supports stop-file shutdown (runtime/flags/evidence_webhook.stop)\n"
        "- ✅ DB2: Evidence webhook uses lock + status files (runtime/locks/evidence_webhook.lock, runtime/flags/evidence_webhook.status.json)\n"
        "- ✅ DB3: scripts/run_evidence_webhook.py supports run/stop commands\n"
        "- ✅ DB4: Dashboard includes Service Controls panel to request stop for webhook + tick publisher\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 106 applied (webhook graceful stop + dashboard stop panel + script + checkpoints).")
print("Next steps:")
print("  1. Restart webhook server: python3 scripts/run_evidence_webhook.py run")
print("  2. Check dashboard 'Service Controls' panel for stop buttons")
print("  3. Test stop: python3 scripts/run_evidence_webhook.py stop")
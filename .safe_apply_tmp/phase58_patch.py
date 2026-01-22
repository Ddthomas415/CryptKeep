
from pathlib import Path
import re

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

# 1) Health writer/reader (single source of truth)
write("services/admin/health.py", r"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.run_context import run_id

HEALTH_DIR = Path("runtime") / "health"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _health_path(service_name: str) -> Path:
    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    return HEALTH_DIR / f"{service_name}.json"

def set_health(service_name: str, status: str, pid: int | None = None, details: dict | None = None) -> None:
    """
    Writes runtime/health/<service>.json
    Status must be one of: RUNNING, STOPPING, STOPPED
    """
    s = str(status).upper().strip()
    if s not in ("RUNNING", "STOPPING", "STOPPED"):
        s = "RUNNING"

    payload = {
        "service": str(service_name),
        "status": s,
        "pid": int(pid) if pid is not None else None,
        "run_id": str(run_id()),
        "ts": _now(),
        "details": details or {},
    }
    try:
        _health_path(service_name).write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass

def read_health(service_name: str) -> dict | None:
    p = _health_path(service_name)
    try:
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def list_health() -> List[dict]:
    out: List[dict] = []
    try:
        if not HEALTH_DIR.exists():
            return out
        for f in sorted(HEALTH_DIR.glob("*.json")):
            try:
                out.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                continue
    except Exception:
        return out
    return out
""")

# 2) Patch service_manager to write health state on start/stop
def patch_service_manager(t: str) -> str:
    # import
    if "from services.admin.health import set_health" not in t:
        # place after imports (best-effort)
        m = re.search(r"(^import .+\n|^from .+ import .+\n)+", t, flags=re.M)
        ins = "from services.admin.health import set_health\n"
        if m:
            t = t[:m.end()] + ins + t[m.end():]
        else:
            t = ins + t

    # augment _write_pid: after writing, set RUNNING
    if "_write_pid(" in t and "set_health(service_name, \"RUNNING\"" not in t:
        t = t.replace(
            "def _write_pid(service_name: str, pid: int) -> None:\n    try:\n        _pid_path(service_name).write_text(str(int(pid)) + \"\\n\", encoding=\"utf-8\")\n    except Exception:\n        pass\n",
            "def _write_pid(service_name: str, pid: int) -> None:\n"
            "    try:\n"
            "        _pid_path(service_name).write_text(str(int(pid)) + \"\\n\", encoding=\"utf-8\")\n"
            "    except Exception:\n"
            "        pass\n"
            "    try:\n"
            "        set_health(service_name, \"RUNNING\", pid=int(pid), details={\"source\": \"service_manager\"})\n"
            "    except Exception:\n"
            "        pass\n"
        )

    # augment _clear_pid: after unlink, set STOPPED
    if "def _clear_pid(" in t and "set_health(service_name, \"STOPPED\"" not in t:
        t = t.replace(
            "def _clear_pid(service_name: str) -> None:\n    try:\n        p = _pid_path(service_name)\n        if p.exists():\n            p.unlink()\n    except Exception:\n        pass\n",
            "def _clear_pid(service_name: str) -> None:\n"
            "    try:\n"
            "        p = _pid_path(service_name)\n"
            "        if p.exists():\n"
            "            p.unlink()\n"
            "    except Exception:\n"
            "        pass\n"
            "    try:\n"
            "        set_health(service_name, \"STOPPED\", pid=None, details={\"source\": \"service_manager\"})\n"
            "    except Exception:\n"
            "        pass\n"
        )

    # insert STOPPING at start of stop_service(name)
    if re.search(r"def stop_service\(", t) and "set_health(name, \"STOPPING\"" not in t:
        t = re.sub(
            r"(def stop_service\([^\)]*\):\n)(\s+)",
            r"\1\2try:\n\2    set_health(name, \"STOPPING\", pid=None, details={\"source\": \"service_manager\"})\n\2except Exception:\n\2    pass\n\n\2",
            t,
            count=1
        )

    # stop_all: write STOPPING for each known service name before stop
    if re.search(r"def stop_all\(", t) and "set_health(n, \"STOPPING\"" not in t:
        t = re.sub(
            r"(def stop_all\([^\)]*\):\n)(\s+)",
            r"\1\2try:\n\2    # best-effort: mark stop requested\n\2    for n in known_service_names():\n\2        try:\n\2            set_health(n, \"STOPPING\", pid=None, details={\"source\": \"service_manager.stop_all\"})\n\2        except Exception:\n\2            pass\n\2except Exception:\n\2    pass\n\n\2",
            t,
            count=1
        )

    return t

patch("desktop/service_manager.py", patch_service_manager)

# 3) Patch PID-scoped service controls to set health during stop/cleanup
def patch_service_controls(t: str) -> str:
    if "from services.admin.health import set_health" not in t:
        t = t.replace(
            "from pathlib import Path\nfrom typing import Dict, List, Tuple\n",
            "from pathlib import Path\nfrom typing import Dict, List, Tuple\nfrom services.admin.health import set_health\n"
        )

    if "set_health(name, \"STOPPING\"" not in t:
        t = t.replace(
            "        # SIGTERM\n        try:\n            os.kill(pid, signal.SIGTERM)\n",
            "        # mark STOPPING\n        try:\n            set_health(name, \"STOPPING\", pid=int(pid), details={\"source\": \"dashboard_stop_all\"})\n        except Exception:\n            pass\n\n        # SIGTERM\n        try:\n            os.kill(pid, signal.SIGTERM)\n"
        )

    if "set_health(name, \"STOPPED\"" not in t:
        t = t.replace(
            "            stopped.append({\"service\": name, \"pid\": pid})\n            continue\n",
            "            try:\n                set_health(name, \"STOPPED\", pid=None, details={\"source\": \"dashboard_stop_all\"})\n            except Exception:\n                pass\n            stopped.append({\"service\": name, \"pid\": pid})\n            continue\n"
        )
        t = t.replace(
            "            stopped.append({\"service\": name, \"pid\": pid})\n        else:\n            still_alive.append({\"service\": name, \"pid\": pid, \"file\": str(pf)})\n",
            "            try:\n                set_health(name, \"STOPPED\", pid=None, details={\"source\": \"dashboard_stop_all\"})\n            except Exception:\n                pass\n            stopped.append({\"service\": name, \"pid\": pid})\n        else:\n            try:\n                set_health(name, \"RUNNING\", pid=int(pid), details={\"source\": \"dashboard_stop_all\", \"note\": \"still_alive\"})\n            except Exception:\n                pass\n            still_alive.append({\"service\": name, \"pid\": pid, \"file\": str(pf)})\n"
        )

    # cleanup stale pid files => mark STOPPED
    if "clean_stale_pid_files" in t and "set_health" in t and "dashboard_pid_cleanup" not in t:
        t = t.replace(
            "                pf.unlink()\n                removed.append({\"service\": pf.stem, \"pid\": pid, \"file\": str(pf)})\n",
            "                pf.unlink()\n                try:\n                    set_health(pf.stem, \"STOPPED\", pid=None, details={\"source\": \"dashboard_pid_cleanup\"})\n                except Exception:\n                    pass\n                removed.append({\"service\": pf.stem, \"pid\": pid, \"file\": str(pf)})\n"
        )
        t = t.replace(
            "                pf.unlink()\n                removed.append({\"service\": pf.stem, \"pid\": None, \"file\": str(pf)})\n",
            "                pf.unlink()\n                try:\n                    set_health(pf.stem, \"STOPPED\", pid=None, details={\"source\": \"dashboard_pid_cleanup\"})\n                except Exception:\n                    pass\n                removed.append({\"service\": pf.stem, \"pid\": None, \"file\": str(pf)})\n"
        )

    return t

patch("services/admin/service_controls.py", patch_service_controls)

# 4) Dashboard: Health panel
def patch_dashboard(t: str) -> str:
    if "Service health (handshake)" in t:
        return t
    add = r"""
st.divider()
st.header("Service health (handshake)")

st.caption("Reads runtime/health/*.json. Status is written by service_manager and dashboard stop actions: RUNNING / STOPPING / STOPPED.")

try:
    from services.admin.health import list_health
    rows = list_health()
    st.dataframe(rows, use_container_width=True, height=260)
except Exception as e:
    st.error(f"Health panel failed: {type(e).__name__}: {e}")
"""
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 5) CHECKPOINTS
def patch_cp(t: str) -> str:
    if "## BF) Safe Shutdown Handshake" in t:
        return t
    return t + (
        "\n## BF) Safe Shutdown Handshake\n"
        "- ✅ BF1: runtime/health/<service>.json writer/reader (RUNNING/STOPPING/STOPPED)\n"
        "- ✅ BF2: service_manager stamps health on start/stop/stop_all\n"
        "- ✅ BF3: Dashboard stop/cleanup actions update health states\n"
        "- ✅ BF4: Dashboard health panel displays handshake state\n"
    )

patch("CHECKPOINTS.md", patch_cp)

print("OK: Phase 58 applied (health handshake files + wiring + dashboard + checkpoints).")
PY


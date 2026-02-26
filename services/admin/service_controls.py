from __future__ import annotations

import os
import re
import signal
import time

from services.logging.app_logger import get_logger

logger = get_logger("service_controls")


def stop_service_from_pidfile(service_name: str, grace_sec: float = 4.0) -> dict:
    attempted, stopped, still_alive, errors = [], [], [], []

    from services.admin.health import set_health
    from services.admin.watchdog import PID_DIR, _pid_alive

    def _safe_service_name(name):
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))

    def _known_services():
        return ["market_data_poller", "live_trader_multi", "live_trader_fleet"]

    if not _safe_service_name(service_name):
        return {"ok": False, "error": "unsafe_service_name"}

    known = _known_services()
    if known and service_name not in known:
        return {"ok": False, "error": "unknown_service_name"}

    pf = PID_DIR / f"{service_name}.pid"
    if not pf.exists():
        return {"ok": True, "note": "pid_file_missing", "service": service_name}

    try:
        pid = int(pf.read_text())
    except Exception:
        try:
            pf.unlink()
        except Exception:
            logger.exception("service_controls: failed to remove invalid pid file path=%s", pf)
        return {"ok": False, "error": "invalid_pid_file", "service": service_name}

    attempted.append({"service": service_name, "pid": pid, "file": str(pf)})

    # mark STOPPING
    try:
        set_health(service_name, "STOPPING", pid=pid, details={"source": "dashboard_restart"})
    except Exception:
        logger.exception("service_controls: failed to mark STOPPING service=%s pid=%s", service_name, pid)

    # SIGTERM
    try: os.kill(pid, signal.SIGTERM)
    except Exception as e:
        errors.append({"service": service_name, "pid": pid, "error": f"term_failed: {type(e).__name__}: {e}"})
        return {"ok": False, "attempted": attempted, "stopped": stopped, "still_alive": still_alive, "errors": errors}

    t0 = time.time()
    while time.time() - t0 < float(grace_sec):
        if not _pid_alive(pid): break
        time.sleep(0.15)

    if not _pid_alive(pid):
        try:
            pf.unlink()
        except Exception:
            logger.exception("service_controls: failed to remove pid file path=%s", pf)
        try:
            set_health(service_name, "STOPPED", pid=None, details={"source": "dashboard_restart"})
        except Exception:
            logger.exception("service_controls: failed to mark STOPPED service=%s", service_name)
        stopped.append({"service": service_name, "pid": pid})
        return {"ok": True, "attempted": attempted, "stopped": stopped, "still_alive": still_alive, "errors": errors}

    # SIGKILL fallback
    try: os.kill(pid, getattr(signal, "SIGKILL", signal.SIGTERM))
    except Exception as e: errors.append({"service": service_name, "pid": pid, "error": f"kill_failed: {type(e).__name__}: {e}"})

    t1 = time.time()
    while time.time() - t1 < 1.5:
        if not _pid_alive(pid): break
        time.sleep(0.15)

    if not _pid_alive(pid):
        try:
            pf.unlink()
        except Exception:
            logger.exception("service_controls: failed to remove pid file after hard stop path=%s", pf)
        try:
            set_health(service_name, "STOPPED", pid=None, details={"source": "dashboard_restart"})
        except Exception:
            logger.exception("service_controls: failed to mark STOPPED after hard stop service=%s", service_name)
        stopped.append({"service": service_name, "pid": pid})
        return {"ok": True, "attempted": attempted, "stopped": stopped, "still_alive": still_alive, "errors": errors}

    try:
        set_health(service_name, "RUNNING", pid=pid, details={"source": "dashboard_restart", "note": "still_alive"})
    except Exception:
        logger.exception("service_controls: failed to restore RUNNING status service=%s pid=%s", service_name, pid)
    still_alive.append({"service": service_name, "pid": pid, "file": str(pf)})
    return {"ok": False, "attempted": attempted, "stopped": stopped, "still_alive": still_alive, "errors": errors}

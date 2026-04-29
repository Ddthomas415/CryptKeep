from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

from services.os.app_paths import data_dir
from services.admin.config_editor import load_user_yaml
from services.logging.app_logger import get_logger
from services.process.bot_runtime_truth import (
    canonical_bot_status as bot_status,
    read_heartbeat,
    stop_bot,
)
from services.process.crash_snapshot import write_crash_snapshot

WD_PATH = data_dir() / "watchdog_last.json"
logger = get_logger("watchdog")

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _persist(obj: dict) -> None:
    try:
        WD_PATH.parent.mkdir(parents=True, exist_ok=True)
        WD_PATH.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str)[:2_000_000], encoding="utf-8")
    except Exception:
        logger.exception("watchdog: persist failed")

def read_last() -> dict:
    try:
        if not WD_PATH.exists():
            return {}
        return json.loads(WD_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _kill_switch_on(reason: str):
    try:
        from services.admin.kill_switch import set_armed

        payload = set_armed(True, note=reason)
        return {"ok": True, "kill_switch": payload}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}:{e}"}


def _system_guard_halting(reason: str):
    try:
        from services.admin.system_guard import set_state

        payload = set_state("HALTING", writer="watchdog", reason=reason)
        return {"ok": True, "system_guard": payload}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}:{e}"}

def _cfg() -> dict:
    cfg = load_user_yaml()
    wd = cfg.get("watchdog") if isinstance(cfg.get("watchdog"), dict) else {}
    wd.setdefault("enabled", True)
    wd.setdefault("stale_after_sec", 120)
    wd.setdefault("auto_stop_on_stale", False)      # safest default: do NOT kill process automatically
    wd.setdefault("stop_hard", True)                # if auto_stop_on_stale=True, hard kill allowed after soft timeout (stop_bot handles soft->hard)
    wd.setdefault("write_crash_snapshot_on_stale", True)
    return wd

def run_watchdog_once() -> dict:
    wd = _cfg()
    if not bool(wd.get("enabled", True)):
        out = {"ok": True, "skipped": True, "reason": "disabled", "ts": _iso_now()}
        _persist(out)
        return out

    st = bot_status()
    hb = read_heartbeat()
    now = time.time()

    out: dict[str, Any] = {
        "ok": True,
        "ts": _iso_now(),
        "bot_running": bool(st.get("running")),
        "pid": st.get("pid"),
        "heartbeat": hb,
        "stale_after_sec": float(wd.get("stale_after_sec", 120) or 120),
        "actions": [],
        "triggered": False,
    }

    if not st.get("running"):
        out["note"] = "bot_not_running"
        _persist(out)
        return out

    ts_epoch = hb.get("ts_epoch")
    if ts_epoch is None:
        # No heartbeat while bot claims running -> treat as stale
        age = None
        stale = True
    else:
        try:
            age = float(now - float(ts_epoch))
            stale = age >= float(out["stale_after_sec"])
        except Exception:
            age = None
            stale = True

    out["heartbeat_age_sec"] = age
    out["heartbeat_stale"] = bool(stale)

    if not stale:
        _persist(out)
        return out

    out["triggered"] = True

    # 1) crash snapshot
    if bool(wd.get("write_crash_snapshot_on_stale", True)):
        try:
            cs = write_crash_snapshot(
                reason="watchdog_heartbeat_stale",
                pid=(int(st.get("pid")) if st.get("pid") else None),
                proc_state=(st.get("state") or {}),
                extra={"heartbeat_age_sec": age, "stale_after_sec": out["stale_after_sec"]},
            )
            out["actions"].append({"action": "write_crash_snapshot", "result": cs})
        except Exception as e:
            logger.exception("watchdog: crash snapshot failed")
            out["actions"].append({"action": "write_crash_snapshot", "ok": False, "error": f"{type(e).__name__}:{e}"})

    # 2) system guard HALTING (always)
    sg = _system_guard_halting("watchdog:heartbeat_stale")
    out["actions"].append({"action": "system_guard_halting", "result": sg})

    # 3) kill switch ON (always)
    ks = _kill_switch_on("watchdog:heartbeat_stale")
    out["actions"].append({"action": "kill_switch_on", "result": ks})

    # 4) optional stop
    if bool(wd.get("auto_stop_on_stale", False)):
        try:
            res = stop_bot(hard=bool(wd.get("stop_hard", True)))
            out["actions"].append({"action": "stop_bot", "result": res})
        except Exception as e:
            logger.exception("watchdog: stop_bot failed")
            out["actions"].append({"action": "stop_bot", "ok": False, "error": f"{type(e).__name__}:{e}"})

    _persist(out)
    return out

def run_watchdog_loop(*, interval_sec: int = 15) -> None:
    interval_sec = int(interval_sec)
    if interval_sec <= 0:
        interval_sec = 15
    while True:
        try:
            run_watchdog_once()
        except Exception:
            logger.exception("watchdog: loop iteration failed")
        time.sleep(interval_sec)

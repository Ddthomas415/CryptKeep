from __future__ import annotations

from pathlib import Path
import argparse
import json
import os
import signal
import subprocess
import sys
import time

# CBP_BOOTSTRAP_SYS_PATH
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.os.app_paths import data_dir, ensure_dirs, state_root
from services.logging.app_logger import get_logger

REPO = Path(__file__).resolve().parents[1]
PROC_PATH = data_dir() / "bot_process.json"
LOG_PATH = data_dir() / "logs" / "bot.log"
logger = get_logger("bot_ctl")


def _emit(obj) -> None:
    sys.stdout.write(json.dumps(obj))
    sys.stdout.write("\n")


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _load_state() -> dict:
    if not PROC_PATH.exists():
        return {}
    try:
        return json.loads(PROC_PATH.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("bot_ctl: failed to parse process state path=%s", PROC_PATH)
        return {}


def _save_state(state: dict) -> None:
    PROC_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROC_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _clear_state() -> None:
    try:
        PROC_PATH.unlink(missing_ok=True)
    except Exception:
        logger.exception("bot_ctl: failed to clear process state path=%s", PROC_PATH)


def cmd_status(_args) -> int:
    st = _load_state()
    pid = st.get("pid")
    running = bool(pid) and isinstance(pid, int) and _pid_alive(pid)

    if pid and not running:
        _clear_state()
        st = {}
        pid = None

    _emit(
        {
            "ok": True,
            "running": running,
            "pid": pid,
            "state": st,
            "log_path": str(LOG_PATH),
            "proc_path": str(PROC_PATH),
        }
    )
    return 0


def cmd_start(args) -> int:
    st = _load_state()
    pid = st.get("pid")
    if isinstance(pid, int) and pid and _pid_alive(pid):
        _emit({"ok": True, "started": False, "running": True, "pid": pid, "msg": "already running"})
        return 0

    ensure_dirs()
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.touch(exist_ok=True)

    cmd = [sys.executable, "-u", "scripts/run_bot_safe.py", "--venue", args.venue, "--symbols", args.symbols]
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["CBP_VENUE"] = args.venue  # make venue visible to anything using env
    env["CBP_SYMBOLS"] = args.symbols  # propagate CLI symbols
    env.setdefault("CBP_STATE_DIR", str(state_root()))

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        p = subprocess.Popen(cmd, cwd=str(REPO), stdout=f, stderr=subprocess.STDOUT, env=env)

    state = {
        "pid": p.pid,
        "cmd": cmd,
        "venue": args.venue,
        "symbols": [s for s in args.symbols.split(",") if s],
        "started_ts_epoch": time.time(),
        "started_ts_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "force": bool(getattr(args, "force", False)),
    }
    _save_state(state)

    _emit({"ok": True, "started": True, "pid": p.pid, "log_path": str(LOG_PATH), "proc_path": str(PROC_PATH)})
    return 0


def cmd_stop(args) -> int:
    st = _load_state()
    pid = st.get("pid")

    if not isinstance(pid, int) or not pid:
        _emit({"ok": True, "stopped": True, "reason": "no_pid"})
        return 0

    if not _pid_alive(pid):
        _clear_state()
        _emit({"ok": True, "stopped": True, "reason": "not_running_stale_pid"})
        return 0

    sig = signal.SIGKILL if args.hard else signal.SIGTERM
    try:
        os.kill(pid, sig)
    except Exception as e:
        _emit({"ok": False, "stopped": False, "pid": pid, "error": str(e)})
        return 1

    # best-effort cleanup
    _clear_state()
    _emit({"ok": True, "stopped": True, "pid": pid, "hard": bool(args.hard)})
    return 0


def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--venue", required=True)
    common.add_argument("--symbols", required=True, help="Comma list")

    ap = argparse.ArgumentParser(prog="bot_ctl.py")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")

    p_start = sub.add_parser("start", parents=[common])
    p_start.add_argument("--force", action="store_true", help="Start even if preflight fails (unsafe)")

    p_stop = sub.add_parser("stop")
    p_stop.add_argument("--hard", action="store_true", help="Hard stop (kill)")

    p_stop_all = sub.add_parser("stop_all")
    p_stop_all.add_argument("--hard", action="store_true", help="Hard stop (kill)")

    args = ap.parse_args()

    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "start":
        return cmd_start(args)
    if args.cmd in ("stop", "stop_all"):
        return cmd_stop(args)

    _emit({"ok": False, "error": f"unknown cmd {args.cmd}"})
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

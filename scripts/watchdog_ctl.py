from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import os
import re

from services.os.app_paths import ensure_dirs, runtime_dir
from services.process.watchdog_process import clear_stale, start_watchdog, status, stop_watchdog


def _clear_stale_runtime_locks(*, hard: bool = False) -> dict:
    ensure_dirs()
    locks = runtime_dir() / "locks"
    removed: list[str] = []
    if not locks.exists():
        return {"ok": True, "removed": removed, "hard": hard}

    for lock_file in locks.glob("*.lock"):
        if hard:
            try:
                lock_file.unlink()
                removed.append(lock_file.name)
            except Exception:
                continue
            continue

        pid: int | None = None
        try:
            text = lock_file.read_text(encoding="utf-8", errors="replace")
            match = re.search(r"\b(\d{2,10})\b", text)
            pid = int(match.group(1)) if match else None
        except Exception:
            pid = None

        alive = False
        if pid:
            try:
                os.kill(pid, 0)
                alive = True
            except Exception:
                alive = False

        if not alive:
            try:
                lock_file.unlink()
                removed.append(lock_file.name)
            except Exception:
                continue

    return {"ok": True, "removed": removed, "hard": hard}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "start", "stop", "clear_stale"])
    ap.add_argument("--interval", type=int, default=15)
    ap.add_argument("--hard", action="store_true")
    args = ap.parse_args()

    if args.cmd == "status":
        payload = status()
        print(payload)
        return 0 if bool(payload.get("ok")) else 2

    if args.cmd == "start":
        payload = start_watchdog(interval_sec=int(args.interval))
        print(payload)
        return 0 if bool(payload.get("ok")) else 2

    if args.cmd == "stop":
        payload = stop_watchdog(hard=bool(args.hard))
        print(payload)
        return 0 if bool(payload.get("ok")) else 2

    if args.cmd == "clear_stale":
        watchdog_payload = clear_stale()
        lock_payload = _clear_stale_runtime_locks(hard=bool(args.hard))
        payload = {
            "ok": bool(watchdog_payload.get("ok")) and bool(lock_payload.get("ok")),
            "watchdog": watchdog_payload,
            "locks": lock_payload,
        }
        print(payload)
        return 0 if bool(payload.get("ok")) else 2

    return 2


if __name__ == "__main__":
    raise SystemExit(main())

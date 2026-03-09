from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

_REPO = add_repo_root_to_syspath(Path(__file__).resolve().parent)


import time
import traceback
import runpy
from services.os import app_paths


def _log_path() -> Path:
    path = app_paths.runtime_dir() / "logs" / "intent_reconciler.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def _append(path: Path, text: str):
    with path.open("a", encoding="utf-8") as f:
        f.write(text)

def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    _append(_log_path(), f"[{ts}] {msg}\n")

def _prereqs_ok() -> tuple[bool, str]:
    cfg = _REPO / "config" / "trading.yaml"
    if not cfg.exists():
        return False, "missing config/trading.yaml"
    return True, "ok"

def main() -> int:
    ok, why = _prereqs_ok()
    if not ok:
        log("intent_reconciler starting in IDLE mode: " + why)
        try:
            while True:
                time.sleep(2.0)
        except KeyboardInterrupt:
            log("intent_reconciler stopped (KeyboardInterrupt)")
            return 0

    log("intent_reconciler wrapper launching real module: scripts.run_intent_reconciler")

    try:
        # Execute the existing real script module as __main__
        runpy.run_module("scripts.run_intent_reconciler", run_name="__main__")
        return 0
    except KeyboardInterrupt:
        log("intent_reconciler stopped (KeyboardInterrupt)")
        return 0
    except Exception as e:
        log("intent_reconciler crashed: " + repr(e))
        log(traceback.format_exc())
        # Fail closed: keep alive (so supervisor can stop it) unless you prefer exit.
        # We keep it alive to avoid restart thrash.
        try:
            log("intent_reconciler entering SAFE-IDLE after crash")
            while True:
                time.sleep(2.0)
        except KeyboardInterrupt:
            log("intent_reconciler stopped (KeyboardInterrupt)")
            return 0

if __name__ == "__main__":
    raise SystemExit(main())

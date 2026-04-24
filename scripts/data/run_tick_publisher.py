from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

_REPO = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import json
import time
import traceback
from services.os.app_paths import data_dir, runtime_dir, ensure_dirs
from services.config_loader import runtime_trading_config_available

def _log_path() -> Path:
    ensure_dirs()
    path = runtime_dir() / "logs" / "tick_publisher.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

# append-friendly helper (py<3.12 compatible)
def _append(path: Path, text: str):
    with path.open("a", encoding="utf-8") as f:
        f.write(text)

def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    _append(_log_path(), f"[{ts}] {msg}\n")

def main() -> int:
    try:
        # Prereqs we can check without forcing API calls
        rules_db = data_dir() / "execution.sqlite"

        missing = []
        if not runtime_trading_config_available():
            missing.append("runtime trading config missing")
        if not rules_db.exists():
            # not fatal; just means no market rules cached yet
            missing.append(".cbp_state/data/execution.sqlite missing (ok for fresh install)")

        if missing:
            log("tick_publisher starting in IDLE mode: " + "; ".join(missing))
        else:
            log("tick_publisher starting (prereqs present)")

        # Try to run the real publisher if available
        try:
            from services.market_data.system_status_publisher import run_tick_publisher  # type: ignore
        except Exception:
            run_tick_publisher = None

        if callable(run_tick_publisher):
            log("tick_publisher using services.market_data.system_status_publisher.run_tick_publisher")
            run_tick_publisher()
            return 0

        # Fallback: idle loop that keeps process alive (so supervisor tooling works)
        log("tick_publisher fallback idle loop (no run_tick_publisher available)")
        while True:
            time.sleep(2.0)

    except KeyboardInterrupt:
        log("tick_publisher stopped (KeyboardInterrupt)")
        return 0
    except Exception as e:
        log("tick_publisher crashed: " + repr(e))
        log(traceback.format_exc())
        return 2

if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import time
from pathlib import Path
import yaml

def main() -> int:
    cfg = {}
    try:
        cfg = yaml.safe_load(Path("config/trading.yaml").read_text(encoding="utf-8", errors="replace")) or {}
    except Exception:
        cfg = {}

    mode = str(cfg.get("mode") or "paper").lower()
    live_enabled = bool((cfg.get("live") or {}).get("enabled", False))

    print(f"[bot_runner] starting. mode={mode} live.enabled={live_enabled}")

    # === Temporary Terminal Patch ===
    tick = 0
    try:
        while True:
            tick += 1
            print(f"[bot_runner] tick {tick}: {'simulated trade' if mode=='paper' else 'live trade stub'}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("[bot_runner] stopped by user")
    # === End Patch ===

    return 0

if __name__ == "__main__":
    raise SystemExit(main())

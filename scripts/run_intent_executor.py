from __future__ import annotations

import time
from services.admin.config_editor import load_user_yaml
from services.execution.intent_executor import execute_one, reconcile_open

def main():
    cfg = load_user_yaml()
    ex = cfg.get("execution", {}) if isinstance(cfg.get("execution"), dict) else {}
    venue = ex.get("venue", "binance")
    mode = ex.get("mode", "paper")
    symbol = ex.get("symbol", None)
    interval = int(ex.get("loop_interval_sec", 2) or 2)
    reconcile_every = int(ex.get("reconcile_every_sec", 30) or 30)

    last_recon = 0.0
    while True:
        execute_one(cfg, venue=str(venue), mode=str(mode))
        now = time.time()
        if now - last_recon >= reconcile_every:
            reconcile_open(cfg, venue=str(venue), mode=str(mode), symbol=(str(symbol) if symbol else None), limit=400)
            last_recon = now
        time.sleep(max(1, interval))

if __name__ == "__main__":
    main()

from __future__ import annotations

import traceback
import yaml

from services.execution import live_trader_loop


def main() -> int:
    try:
        cfg = yaml.safe_load(open("config/trading.yaml", "r", encoding="utf-8").read()) or {}
    except Exception:
        cfg = {}

    try:
        if hasattr(live_trader_loop, "main") and callable(getattr(live_trader_loop, "main")):
            return int(live_trader_loop.main())
        if hasattr(live_trader_loop, "run_forever_live") and callable(getattr(live_trader_loop, "run_forever_live")):
            live_trader_loop.run_forever_live()
            return 0
        if hasattr(live_trader_loop, "run_live") and callable(getattr(live_trader_loop, "run_live")):
            return int(live_trader_loop.run_live(cfg))
        raise RuntimeError("services.execution.live_trader_loop found but no main()/run_forever_live()/run_live(cfg) entrypoint")
    except Exception as e:
        print(f"[cli_live] ERROR: {type(e).__name__}: {e}")
        print(traceback.format_exc(limit=3))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())

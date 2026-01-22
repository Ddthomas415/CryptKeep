from __future__ import annotations

import traceback
import yaml

def main() -> int:
    try:
        cfg = yaml.safe_load(open("config/trading.yaml", "r", encoding="utf-8").read()) or {}
    except Exception:
        cfg = {}

    # Prefer existing live runner if present
    try:
        from services.bot import live_runner  # type: ignore
        # If live_runner exposes a main(), call it; else just return error.
        if hasattr(live_runner, "main") and callable(getattr(live_runner, "main")):
            return int(live_runner.main())  # type: ignore
        # If it exposes run_live(cfg), call it.
        if hasattr(live_runner, "run_live") and callable(getattr(live_runner, "run_live")):
            return int(live_runner.run_live(cfg))  # type: ignore
        raise RuntimeError("services.bot.live_runner found but no main()/run_live(cfg) entrypoint")
    except Exception as e:
        print(f"[cli_live] ERROR: {type(e).__name__}: {e}")
        print(traceback.format_exc(limit=3))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())

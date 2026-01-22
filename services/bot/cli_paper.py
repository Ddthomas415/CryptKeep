from __future__ import annotations

import traceback
import yaml

def main() -> int:
    try:
        cfg = yaml.safe_load(open("config/trading.yaml", "r", encoding="utf-8").read()) or {}
    except Exception:
        cfg = {}

    # Prefer existing paper runner if present
    try:
        from services.bot import paper_runner  # type: ignore
        if hasattr(paper_runner, "main") and callable(getattr(paper_runner, "main")):
            return int(paper_runner.main())  # type: ignore
        if hasattr(paper_runner, "run_paper") and callable(getattr(paper_runner, "run_paper")):
            return int(paper_runner.run_paper(cfg))  # type: ignore
        raise RuntimeError("services.bot.paper_runner found but no main()/run_paper(cfg) entrypoint")
    except Exception as e:
        print(f"[cli_paper] ERROR: {type(e).__name__}: {e}")
        print(traceback.format_exc(limit=3))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())

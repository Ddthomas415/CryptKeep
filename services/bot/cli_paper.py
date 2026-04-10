from __future__ import annotations

import traceback

from services.config_loader import load_runtime_trading_config
from services.execution import paper_runner


def main() -> int:
    cfg = load_runtime_trading_config()

    try:
        if hasattr(paper_runner, "main") and callable(getattr(paper_runner, "main")):
            return int(paper_runner.main())
        if hasattr(paper_runner, "run_forever") and callable(getattr(paper_runner, "run_forever")):
            paper_runner.run_forever()
            return 0
        if hasattr(paper_runner, "run_paper") and callable(getattr(paper_runner, "run_paper")):
            return int(paper_runner.run_paper(cfg))
        raise RuntimeError("services.execution.paper_runner found but no main()/run_forever()/run_paper(cfg) entrypoint")
    except Exception as e:
        print(f"[cli_paper] ERROR: {type(e).__name__}: {e}")
        print(traceback.format_exc(limit=3))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())

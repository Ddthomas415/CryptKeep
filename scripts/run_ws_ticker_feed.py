#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from scripts.data.run_ws_ticker_feed import *  # noqa: F401,F403
from scripts.data.run_ws_ticker_feed import main


if __name__ == "__main__":
    raise SystemExit(main())

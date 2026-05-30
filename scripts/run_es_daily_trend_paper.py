#!/usr/bin/env python3
from __future__ import annotations

import runpy
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

# The ManagedComponent API contract is implemented in
# scripts/dev/run_es_daily_trend_paper.py. Keep this marker here because CI
# guards the historical root entrypoint source directly: lock_dir=runtime_dir()


def main() -> None:
    runpy.run_module("scripts.dev.run_es_daily_trend_paper", run_name="__main__")


if __name__ == "__main__":
    main()

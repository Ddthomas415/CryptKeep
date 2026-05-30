#!/usr/bin/env python3
from __future__ import annotations

# Compatibility wrapper for scripts/live/cancel_intent.py.
# Contract: target accepts --sandbox and calls client.cancel_intent(...).
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from scripts.live.cancel_intent import *  # noqa: F401,F403
from scripts.live.cancel_intent import main


if __name__ == "__main__":
    raise SystemExit(main())

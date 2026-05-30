#!/usr/bin/env python3
from __future__ import annotations

# Compatibility wrapper for scripts/dev/reconcile_order_dedupe.py.
# Contract: target accepts --sandbox, calls client.fetch_open_orders(...),
# and calls client.fetch_order(...) without submitting orders.
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from scripts.dev.reconcile_order_dedupe import *  # noqa: F401,F403
from scripts.dev.reconcile_order_dedupe import main


if __name__ == "__main__":
    raise SystemExit(main())

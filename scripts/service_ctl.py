#!/usr/bin/env python3
from __future__ import annotations

# Compatibility path for the canonical service control CLI.
# from services.desktop.simple_service_manager import (
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from scripts.compat.service_ctl import *  # noqa: F401,F403
from scripts.compat.service_ctl import main


if __name__ == "__main__":
    raise SystemExit(main())

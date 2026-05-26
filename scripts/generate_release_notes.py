#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from scripts.release.generate_release_notes import *  # noqa: F401,F403
from scripts.release.generate_release_notes import main


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Repo installer entrypoint.

Run from repo root:
    python3 scripts/install.py
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def _repo_root(start_dir: Path) -> Path:
    """Walk upward until we find the repo root (pyproject + services + install.py)."""
    for p in [start_dir] + list(start_dir.parents):
        if (p / "pyproject.toml").exists() and (p / "services").is_dir() and (p / "install.py").exists():
            return p
    # fallback: scripts/.. (repo root)
    return start_dir.parent


def main() -> int:
    # Avoid Path.resolve() on Python 3.13; use os.path.realpath(str) instead.
    this_file = Path(os.path.realpath(__file__))
    scripts_dir = this_file.parent

    root = _repo_root(scripts_dir)

    # Safety: if root/install.py accidentally points to THIS wrapper, force root to scripts/..
    target_install = os.path.realpath(str(root / "install.py"))
    if target_install == os.path.realpath(str(this_file)):
        root = scripts_dir.parent
        target_install = os.path.realpath(str(root / "install.py"))

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    runpy.run_path(target_install, run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

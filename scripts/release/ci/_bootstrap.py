from __future__ import annotations

import sys
from pathlib import Path


def repo_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(10):
        if (cur / "pyproject.toml").exists() or ((cur / "install.py").exists() and (cur / "services").exists()):
            return cur
        cur = cur.parent
    return start.resolve()


def add_repo_root_to_syspath(start: Path) -> Path:
    root = repo_root(start)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root

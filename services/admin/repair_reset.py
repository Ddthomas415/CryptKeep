from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from services.os.app_paths import ensure_dirs, runtime_dir


def _remove_if_exists(path: Path, *, dry_run: bool) -> bool:
    if not path.exists():
        return False
    if not dry_run:
        try:
            if path.is_file():
                path.unlink()
            else:
                return False
        except Exception:
            return False
    return True


def reset_runtime_state(*, include_locks: bool = False, dry_run: bool = False) -> Dict[str, Any]:
    ensure_dirs()
    root = runtime_dir()
    flags = root / "flags"
    locks = root / "locks"
    snapshots = root / "snapshots"

    removed: list[str] = []
    scanned: list[str] = []

    for d in (flags, snapshots):
        if d.exists():
            for p in d.glob("*"):
                scanned.append(str(p))
                if _remove_if_exists(p, dry_run=dry_run):
                    removed.append(str(p))

    if include_locks and locks.exists():
        for p in locks.glob("*"):
            scanned.append(str(p))
            if _remove_if_exists(p, dry_run=dry_run):
                removed.append(str(p))

    return {
        "ok": True,
        "dry_run": bool(dry_run),
        "include_locks": bool(include_locks),
        "scanned": len(scanned),
        "removed": len(removed),
        "removed_paths": removed,
    }

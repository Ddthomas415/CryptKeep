from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from services.os.app_paths import data_dir, ensure_dirs, runtime_dir


def _timestamp_suffix() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _log_dirs() -> list[Path]:
    ensure_dirs()
    return [runtime_dir() / "logs", data_dir() / "logs"]


def _prune_rotated(log_file: Path, *, max_keep: int) -> list[str]:
    if max_keep <= 0:
        return []
    deleted: list[str] = []
    rotated = sorted(log_file.parent.glob(f"{log_file.name}.*"))
    overflow = max(0, len(rotated) - int(max_keep))
    for p in rotated[:overflow]:
        try:
            p.unlink()
            deleted.append(str(p))
        except Exception:
            continue
    return deleted


def rotate_logs(*, max_bytes: int = 5_000_000, max_keep: int = 5) -> dict:
    rotated: list[str] = []
    deleted: list[str] = []
    skipped: list[str] = []

    for log_dir in _log_dirs():
        if not log_dir.exists():
            continue
        for log_file in sorted(log_dir.glob("*.log")):
            try:
                size = int(log_file.stat().st_size)
            except Exception:
                skipped.append(str(log_file))
                continue

            if size <= int(max_bytes):
                deleted.extend(_prune_rotated(log_file, max_keep=int(max_keep)))
                continue

            target = log_file.with_name(f"{log_file.name}.{_timestamp_suffix()}")
            try:
                os.replace(log_file, target)
                log_file.touch(exist_ok=True)
                rotated.append(str(target))
            except Exception:
                skipped.append(str(log_file))
                continue

            deleted.extend(_prune_rotated(log_file, max_keep=int(max_keep)))

    return {
        "ok": True,
        "rotated": rotated,
        "deleted": deleted,
        "skipped": skipped,
        "max_bytes": int(max_bytes),
        "max_keep": int(max_keep),
    }

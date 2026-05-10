"""
services/os/file_utils.py
Shared file I/O utilities — safe atomic writes for all runtime state.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def _sibling_temp_path(path: Path) -> tuple[int, Path]:
    fd, raw_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    return fd, Path(raw_path)


def atomic_write(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    """Write *text* to *path* atomically using a sibling temp file + os.replace().

    Guarantees that readers never observe a partially-written file.
    Works on all POSIX systems and on Windows (Python 3.3+).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = _sibling_temp_path(path)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as handle:
            handle.write(text)
        os.replace(tmp, path)
    except Exception:
        # Best-effort cleanup of temp file on failure
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Byte-level variant of atomic_write."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = _sibling_temp_path(path)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        raise

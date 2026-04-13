"""
services/os/file_utils.py
Shared file I/O utilities — safe atomic writes for all runtime state.
"""
from __future__ import annotations

import os
from pathlib import Path


def atomic_write(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    """Write *text* to *path* atomically using a sibling temp file + os.replace().

    Guarantees that readers never observe a partially-written file.
    Works on all POSIX systems and on Windows (Python 3.3+).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(text, encoding=encoding)
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
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        raise

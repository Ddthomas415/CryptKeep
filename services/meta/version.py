from __future__ import annotations

from pathlib import Path

def get_version() -> str:
    p = Path(__file__).resolve().parents[2] / "VERSION"
    try:
        return p.read_text(encoding="utf-8").strip()
    except Exception:
        return "0.0.0"

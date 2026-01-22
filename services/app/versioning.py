from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]

def current_version() -> str:
    try:
        v = (_repo_root() / "VERSION").read_text(encoding="utf-8").strip()
        return v or "0.0.0"
    except Exception:
        return "0.0.0"

def build_meta() -> dict:
    return {
        "version": current_version(),
        "build_ts_utc": datetime.now(timezone.utc).isoformat(),
    }

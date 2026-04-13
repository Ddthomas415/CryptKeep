from __future__ import annotations

import json
from typing import Any

from services.os.app_paths import runtime_dir


def _path():
    outdir = runtime_dir() / "candidates"
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir / "latest_candidates.json"


def write_candidates(rows: list[dict[str, Any]]) -> str:
    p = _path()
    p.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return str(p)


def load_latest_candidates() -> list[dict[str, Any]]:
    p = _path()
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []

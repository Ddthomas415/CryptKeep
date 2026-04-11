from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

STORE_DIR = Path(".cbp_state/runtime/outcomes")
STORE_FILE = STORE_DIR / "strategy_outcomes.jsonl"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def log_strategy_outcome(row: dict[str, Any]) -> dict[str, Any]:
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": _now(),
        **dict(row or {}),
    }
    with STORE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")
    return {"ok": True, "path": str(STORE_FILE), "row": payload}

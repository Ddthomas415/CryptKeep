from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from services.os.app_paths import runtime_dir


def outcomes_file() -> Path:
    """The outcome log of the current state directory.

    Resolved on each call from CBP_STATE_DIR (default <repo>/.cbp_state). It
    used to be a path relative to the working directory, so every paper
    campaign started from the repo root wrote one shared file whatever its
    own state directory was, and a process started elsewhere wrote and read
    a different file.
    """
    return runtime_dir() / "outcomes" / "strategy_outcomes.jsonl"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def log_strategy_outcome(row: dict[str, Any]) -> dict[str, Any]:
    store_file = outcomes_file()
    store_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": _now(),
        **dict(row or {}),
    }
    with store_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")
    return {"ok": True, "path": str(store_file), "row": payload}

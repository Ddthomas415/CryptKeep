from __future__ import annotations
import json
import time
from services.os.app_paths import runtime_dir

LATEST_SNAPSHOT = runtime_dir() / "snapshots" / "system_status.latest.json"

def is_snapshot_fresh(max_age_sec: float = 5.0) -> tuple[bool, str | None]:
    if not LATEST_SNAPSHOT.exists():
        return False, "snapshot_missing"
    try:
        data = json.loads(LATEST_SNAPSHOT.read_text(encoding="utf-8"))
        ts_ms = int(data.get("ts_ms") or 0)
        if ts_ms == 0:
            return False, "no_ts_ms"
        age = (time.time() * 1000 - ts_ms) / 1000
        if age > max_age_sec:
            return False, f"stale:{age:.1f}s"
        return True, None
    except Exception as e:
        return False, f"parse_error:{type(e).__name__}"

from datetime import datetime, timezone
from pathlib import Path
import json

KILL_PATH = Path("runtime") / "kill_switch.json"

def _now():
    return datetime.now(timezone.utc).isoformat()

def ensure_default():
    if not KILL_PATH.exists():
        KILL_PATH.parent.mkdir(parents=True, exist_ok=True)
        KILL_PATH.write_text(json.dumps({"armed": True, "ts": _now(), "note": "default"}, indent=2) + "\n")
    return get_state()

def get_state():
    try:
        ensure_default()
        return json.loads(KILL_PATH.read_text())
    except:
        return {"armed": True, "ts": _now(), "note": "fallback"}

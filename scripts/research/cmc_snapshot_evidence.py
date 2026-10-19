"""Read-only v3 snapshot envelopes; content hashes are not source authentication."""
import hashlib
import json
from datetime import datetime, timezone


def load_snapshot(path):
    raw = path.read_bytes()
    item = json.loads(raw)
    if not isinstance(item, dict) or item.get("schema_version") != 3:
        raise ValueError("explicit v3 schema required; original snapshots remain preserved")
    if item.get("artifact_type") != "research_only_forward_log_v3" or item.get("places_orders") is not False:
        raise ValueError("invalid research envelope")
    timestamp = item.get("snapshot_utc")
    if not isinstance(timestamp, str):
        raise ValueError("text snapshot timestamp required")
    time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if time.utcoffset() is None:
        raise ValueError("aware snapshot timestamp required")
    for field in ("trending_hidden_boost", "tracked_coinbase"):
        if not isinstance(item.get(field), list):
            raise ValueError("list field required: " + field)
    if not isinstance(item.get("majors_coinbase"), dict):
        raise ValueError("benchmark quote envelope required")
    return {"file": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
            "snapshot_utc": time.astimezone(timezone.utc), "data": item,
            "source_authentication": "UNVERIFIED", "scoring_authorized": False}

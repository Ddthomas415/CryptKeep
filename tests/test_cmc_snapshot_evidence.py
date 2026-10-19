import hashlib
import json

import pytest

from scripts.research.cmc_snapshot_evidence import load_snapshot


def record():
    return {"schema_version": 3, "artifact_type": "research_only_forward_log_v3",
            "places_orders": False, "snapshot_utc": "2026-10-09T05:00:00Z",
            "trending_hidden_boost": [], "tracked_coinbase": [], "majors_coinbase": {}}


def test_read_only_hash_evidence(tmp_path):
    path = tmp_path / "snapshot.json"; raw = json.dumps(record()).encode(); path.write_bytes(raw)
    result = load_snapshot(path)
    assert result["sha256"] == hashlib.sha256(raw).hexdigest()
    assert path.read_bytes() == raw
    assert result["scoring_authorized"] is False


@pytest.mark.parametrize("key,value", [("schema_version", 2), ("places_orders", True),
    ("snapshot_utc", "2026-10-09T05:00:00"), ("tracked_coinbase", {}),
    ("majors_coinbase", []), ("artifact_type", "actual_trades"),
    ("snapshot_utc", None), ("snapshot_utc", 123)])
def test_invalid_envelopes_refused(tmp_path, key, value):
    data = record(); data[key] = value
    path = tmp_path / "snapshot.json"; path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        load_snapshot(path)

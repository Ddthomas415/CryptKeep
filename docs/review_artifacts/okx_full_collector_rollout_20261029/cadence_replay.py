"""Offline reproduction only; no original database or transport access."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from services.analytics.edge_cadence import check_edge_cadence
from services.analytics.okx_funding_journal import _stored_pair


def main():
    saved = ROOT / "docs/review_artifacts/okx_funding_pilot_20261029/20261029T182056Z_5544cd086ad64e1f8787f2e44546edc3/READBACK.json"
    raw = json.loads(saved.read_bytes())["raw"]
    entry = raw["observations"][0]
    record = entry["observation"]
    policy = _stored_pair(record, entry["observation_key"])
    capture = record["captured_at"]
    with tempfile.TemporaryDirectory(prefix="edge-cadence-replay-") as tmp:
        database = Path(tmp) / "synthetic.sqlite"
        def scoped_sql(event, args):
            if event == "sqlite3.connect" and str(args[0]) not in {
                str(database), f"file:{database}?mode=ro"
            }:
                raise AssertionError("non_disposable_database_forbidden")
        sys.addaudithook(scoped_sql)
        with sqlite3.connect(database) as conn:
            conn.execute("CREATE TABLE raw_funding_observations(source TEXT, observation_key TEXT, capture_ts TEXT, payload_json TEXT)")
            conn.execute("INSERT INTO raw_funding_observations VALUES(?,?,?,?)", (
                raw["source"], entry["observation_key"], capture, json.dumps(record)))
            for table in ("open_interest_snapshots", "basis_snapshots"):
                conn.execute(f"CREATE TABLE {table}(snapshot_id TEXT, capture_ts TEXT, source TEXT)")
                conn.execute(f"INSERT INTO {table} VALUES(?,?,?)", ("synthetic", capture, raw["source"]))
            conn.commit()
        before = hashlib.sha256(database.read_bytes()).hexdigest()
        result = check_edge_cadence(store_path=str(database), now=datetime.fromisoformat(capture))
        assert result["missing"] == ["funding"] and not result["ok"]
        assert result["stale"] == [] and "store_error" not in result
        assert policy["strategy_eligible"] is False and policy["execution_authority"] is False
        assert hashlib.sha256(database.read_bytes()).hexdigest() == before
    out = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "input_sha256": hashlib.sha256(saved.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256((ROOT / "services/analytics/edge_cadence.py").read_bytes()).hexdigest(),
        "valid_saved_pair": True, "reference_time": capture,
        "result": result, "database_byte_preserved": True,
        "diagnosis": "legacy_only_cadence_ignores_valid_raw_pair",
        "scope": "offline disposable replay, not a current runtime check",
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

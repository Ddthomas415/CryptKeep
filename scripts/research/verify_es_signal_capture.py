"""Read-only verification of recorded ES signals, not a promotion gate."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.strategies.signal_input_capture import replay_es_inputs


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp_requires_timezone")
    return parsed


def verify(state: Path, *, since: datetime, until: datetime) -> dict:
    if not state.is_dir():
        raise ValueError("state_directory_missing")
    if since.tzinfo is None or until.tzinfo is None or until <= since:
        raise ValueError("invalid_observation_window")
    selected = 0
    checked = 0
    problems = []
    for path in sorted((state / "data" / "evidence" / "es_daily_trend_v1").glob("signal_*.jsonl")):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                observed = timestamp(record["timestamp"])
                if not since <= observed < until:
                    continue
                selected += 1
                if record.get("record_type") != "signal":
                    raise ValueError("unexpected_record_type")
                if record.get("signal_input_capture_status") != "captured":
                    raise ValueError("capture_missing_or_failed")
                digest = record.get("signal_input_sha256", "")
                if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                    raise ValueError("invalid_capture_hash")
                artifact = state / "data" / "signal_inputs" / f"{digest}.json"
                if artifact.is_symlink():
                    raise ValueError("symlink_capture_refused")
                replay = replay_es_inputs(artifact, expected_sha256=digest)
                payload = json.loads(artifact.read_text())
                for field, key in [("ohlcv_symbol", "symbol"), ("ohlcv_venue", "venue"),
                                   ("ohlcv_timeframe", "timeframe"), ("market_data_source", "source")]:
                    if field not in record or record[field] != payload[key]:
                        raise ValueError(f"provenance_mismatch:{field}")
                for field, key in [("signal_direction", "signal"), ("regime_flag", "regime"),
                                   ("entry_allowed", "entry_allowed"), ("sma_200", "sma_200"),
                                   ("atr_ratio", "atr_ratio")]:
                    if field not in record or key not in replay:
                        raise ValueError(f"missing_comparison_field:{field}")
                    actual, expected = record[field], replay[key]
                    if type(actual) in (int, float) and type(expected) in (int, float):
                        equal = math.isfinite(actual) and math.isfinite(expected) and math.isclose(
                            actual, expected, rel_tol=1e-12, abs_tol=1e-12)
                    else:
                        equal = type(actual) is type(expected) and actual == expected
                    if not equal:
                        raise ValueError(f"replay_mismatch:{field}")
                checked += 1
            except Exception as exc:
                reason = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
                problems.append({"file": path.name, "line": number, "reason": reason})
    status = "failed" if problems else "passed" if selected else "no_records"
    return {"status": status, "scope": "recorded_signals_only_not_session_coverage",
            "read_only": True, "selected": selected, "verified": checked, "problems": problems}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--since", required=True, type=timestamp)
    parser.add_argument("--until", required=True, type=timestamp)
    args = parser.parse_args()
    try:
        result = verify(args.state_dir, since=args.since, until=args.until)
    except Exception as exc:
        result = {"status": "failed", "read_only": True, "error_type": type(exc).__name__}
    print(json.dumps(result, indent=2))
    return {"passed": 0, "failed": 1, "no_records": 2}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_make_json(target: str) -> dict:
    out = subprocess.check_output(["make", target], cwd=str(ROOT), text=True)
    return json.loads(out)


def _to_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def test_make_json_runtime_temporal_consistency_matrix_smoke():
    targets = [
        "check-alignment-list-json",
        "check-alignment-json-fast",
        "validate-json-quick",
        "validate-json-fast",
        "pre-release-sanity-json-quick",
        "pre-release-sanity-json-fast",
    ]
    for target in targets:
        payload = _run_make_json(target)
        started = payload.get("started_at")
        finished = payload.get("finished_at")
        duration = payload.get("duration_seconds")
        assert isinstance(started, str) and started, target
        assert isinstance(finished, str) and finished, target
        assert isinstance(duration, (int, float)), target
        assert duration >= 0, target
        dt_start = _to_dt(started)
        dt_finish = _to_dt(finished)
        assert dt_finish >= dt_start, target
        assert duration < 3600, target

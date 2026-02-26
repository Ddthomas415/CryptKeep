from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_make_json(target: str) -> dict:
    out = subprocess.check_output(["make", target], cwd=str(ROOT), text=True)
    return json.loads(out)


def test_make_json_targets_matrix_smoke():
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
        assert payload.get("schema_version") == 1, target
        assert isinstance(payload.get("ok"), bool), target

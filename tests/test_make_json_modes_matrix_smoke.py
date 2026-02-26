from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_make_json(target: str) -> dict:
    out = subprocess.check_output(["make", target], cwd=str(ROOT), text=True)
    return json.loads(out)


def test_make_json_modes_matrix_smoke():
    expected = {
        "check-alignment-list-json": "list-tests",
        "check-alignment-json-fast": "full_skip_guards",
        "validate-json-quick": "quick",
        "validate-json-fast": "full",
        "pre-release-sanity-json-quick": "quick",
        "pre-release-sanity-json-fast": "custom",
    }
    for target, mode in expected.items():
        payload = _run_make_json(target)
        assert payload.get("schema_version") == 1, target
        assert payload.get("mode") == mode, target

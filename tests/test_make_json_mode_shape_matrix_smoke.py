from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_make_json(target: str) -> dict:
    out = subprocess.check_output(["make", target], cwd=str(ROOT), text=True)
    return json.loads(out)


def test_make_json_mode_shape_matrix_smoke():
    cases = [
        ("check-alignment-list-json", "list-tests"),
        ("check-alignment-json-fast", "full_skip_guards"),
        ("validate-json-quick", "quick"),
        ("validate-json-fast", "full"),
        ("pre-release-sanity-json-quick", "quick"),
        ("pre-release-sanity-json-fast", "custom"),
    ]
    for target, mode in cases:
        payload = _run_make_json(target)
        assert payload.get("schema_version") == 1, target
        assert payload.get("mode") == mode, target

        if target.startswith("check-alignment"):
            assert "guard_tests" in payload, target
            assert "steps" not in payload, target
        elif target.startswith("validate"):
            steps = payload.get("steps") or []
            assert isinstance(steps, list), target
            assert len(steps) in {2, 3}, target
            assert steps[0].get("label") == "check_repo_alignment", target
        else:
            steps = payload.get("steps") or []
            assert isinstance(steps, list), target
            assert len(steps) == 6, target
            assert steps[0].get("label") == "alignment_gate", target

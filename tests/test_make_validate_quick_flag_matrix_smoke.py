from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_make_json(target: str, env: dict | None = None) -> dict:
    out = subprocess.check_output(["make", target], cwd=str(ROOT), env=env, text=True)
    return json.loads(out)


def test_make_validate_quick_flag_matrix_smoke():
    p_quick = _run_make_json("validate-json-quick")
    assert p_quick.get("schema_version") == 1
    assert p_quick.get("mode") == "quick"
    assert p_quick.get("quick") is True

    p_fast = _run_make_json("validate-json-fast")
    assert p_fast.get("schema_version") == 1
    assert p_fast.get("mode") == "full"
    assert p_fast.get("quick") is False

    p_full = _run_make_json("validate-json", env={**os.environ, "CBP_VALIDATE_SKIP_PYTEST": "1"})
    assert p_full.get("schema_version") == 1
    assert p_full.get("mode") == "full"
    assert p_full.get("quick") is False

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_make_json(target: str, env: dict | None = None) -> dict:
    out = subprocess.check_output(["make", target], cwd=str(ROOT), env=env, text=True)
    return json.loads(out)


def test_make_json_top_level_contract_matrix_smoke():
    required = {"schema_version", "mode", "ok", "started_at", "finished_at", "duration_seconds"}
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
        assert required.issubset(set(payload.keys())), target
        assert payload.get("schema_version") == 1, target

    # `validate-json` is included separately with skip env to avoid recursive pytest in tests.
    p_validate_full = _run_make_json("validate-json", env={**os.environ, "CBP_VALIDATE_SKIP_PYTEST": "1"})
    assert required.issubset(set(p_validate_full.keys()))
    assert p_validate_full.get("schema_version") == 1

    # `quick` must exist for validate payloads and be absent for non-validate payloads.
    for t in ("validate-json-quick", "validate-json-fast"):
        p = _run_make_json(t)
        assert isinstance(p.get("quick"), bool), t
    assert isinstance(p_validate_full.get("quick"), bool)

    for t in ("check-alignment-list-json", "check-alignment-json-fast", "pre-release-sanity-json-quick", "pre-release-sanity-json-fast"):
        p = _run_make_json(t)
        assert "quick" not in p, t

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_json(cmd: list[str], env: dict | None = None) -> dict:
    out = subprocess.check_output(cmd, cwd=str(ROOT), env=env, text=True)
    return json.loads(out)


def test_json_script_top_level_contract_matrix_smoke():
    required = {"schema_version", "mode", "ok", "started_at", "finished_at", "duration_seconds"}

    cases = [
        (
            [sys.executable, str(ROOT / "scripts" / "check_repo_alignment.py"), "--list-tests", "--json"],
            None,
            False,
        ),
        (
            [sys.executable, str(ROOT / "scripts" / "check_repo_alignment.py"), "--json"],
            {**os.environ, "CBP_ALIGNMENT_SKIP_GUARDS": "1"},
            False,
        ),
        (
            [sys.executable, str(ROOT / "scripts" / "validate.py"), "--quick", "--json"],
            None,
            True,
        ),
        (
            [sys.executable, str(ROOT / "scripts" / "validate.py"), "--json"],
            {**os.environ, "CBP_VALIDATE_SKIP_PYTEST": "1"},
            True,
        ),
        (
            [
                sys.executable,
                str(ROOT / "scripts" / "pre_release_sanity.py"),
                "--json",
                "--skip-ruff",
                "--skip-mypy",
                "--skip-pytest",
                "--skip-config",
                "--skip-imports",
            ],
            None,
            False,
        ),
        (
            [sys.executable, str(ROOT / "scripts" / "pre_release_sanity.py"), "--json", "--skip-ruff", "--skip-mypy"],
            {**os.environ, "CBP_PRE_RELEASE_SKIP_PYTEST": "1"},
            False,
        ),
    ]

    for cmd, env, expects_quick in cases:
        payload = _run_json(cmd, env=env)
        assert required.issubset(set(payload.keys()))
        assert payload.get("schema_version") == 1
        if expects_quick:
            assert isinstance(payload.get("quick"), bool)
        else:
            assert "quick" not in payload

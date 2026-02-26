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


def test_json_runtime_mode_matrix_smoke():
    cases = [
        (
            [sys.executable, str(ROOT / "scripts" / "check_repo_alignment.py"), "--list-tests", "--json"],
            None,
            "list-tests",
        ),
        (
            [sys.executable, str(ROOT / "scripts" / "check_repo_alignment.py"), "--json"],
            {**os.environ, "CBP_ALIGNMENT_SKIP_GUARDS": "1"},
            "full_skip_guards",
        ),
        (
            [sys.executable, str(ROOT / "scripts" / "validate.py"), "--quick", "--json"],
            None,
            "quick",
        ),
        (
            [sys.executable, str(ROOT / "scripts" / "validate.py"), "--json"],
            {**os.environ, "CBP_VALIDATE_SKIP_PYTEST": "1"},
            "full",
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
            "quick",
        ),
        (
            [
                sys.executable,
                str(ROOT / "scripts" / "pre_release_sanity.py"),
                "--json",
                "--skip-ruff",
                "--skip-mypy",
            ],
            {**os.environ, "CBP_PRE_RELEASE_SKIP_PYTEST": "1"},
            "custom",
        ),
    ]
    for cmd, env, expected_mode in cases:
        payload = _run_json(cmd, env=env)
        assert payload.get("schema_version") == 1
        assert payload.get("mode") == expected_mode

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


def _assert_runtime_fields(payload: dict) -> None:
    started = payload.get("started_at")
    finished = payload.get("finished_at")
    duration = payload.get("duration_seconds")
    assert isinstance(started, str) and started
    assert isinstance(finished, str) and finished
    assert "T" in started and "T" in finished
    assert isinstance(duration, (int, float))
    assert duration >= 0


def test_json_runtime_metadata_smoke():
    p_align = _run_json([sys.executable, str(ROOT / "scripts" / "check_repo_alignment.py"), "--json"], env={**os.environ, "CBP_ALIGNMENT_SKIP_GUARDS": "1"})
    _assert_runtime_fields(p_align)

    p_validate = _run_json([sys.executable, str(ROOT / "scripts" / "validate.py"), "--json"], env={**os.environ, "CBP_VALIDATE_SKIP_PYTEST": "1"})
    _assert_runtime_fields(p_validate)

    p_pre = _run_json(
        [sys.executable, str(ROOT / "scripts" / "pre_release_sanity.py"), "--json", "--skip-ruff", "--skip-mypy"],
        env={**os.environ, "CBP_PRE_RELEASE_SKIP_PYTEST": "1"},
    )
    _assert_runtime_fields(p_pre)

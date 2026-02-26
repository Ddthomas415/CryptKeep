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


def test_json_runtime_steps_contract_smoke():
    p_align = _run_json(
        [sys.executable, str(ROOT / "scripts" / "check_repo_alignment.py"), "--json"],
        env={**os.environ, "CBP_ALIGNMENT_SKIP_GUARDS": "1"},
    )
    assert (p_align.get("repo_doctor") or {}).get("rc") == 0
    assert (p_align.get("guard_tests") or {}).get("rc") == 0

    p_validate = _run_json(
        [sys.executable, str(ROOT / "scripts" / "validate.py"), "--json"],
        env={**os.environ, "CBP_VALIDATE_SKIP_PYTEST": "1"},
    )
    s_validate = p_validate.get("steps") or []
    assert isinstance(s_validate, list) and len(s_validate) == 3
    assert s_validate[0].get("label") == "check_repo_alignment"
    assert s_validate[-1].get("label") == "pytest"

    p_pre = _run_json(
        [sys.executable, str(ROOT / "scripts" / "pre_release_sanity.py"), "--json", "--skip-ruff", "--skip-mypy"],
        env={**os.environ, "CBP_PRE_RELEASE_SKIP_PYTEST": "1"},
    )
    s_pre = p_pre.get("steps") or []
    assert isinstance(s_pre, list) and len(s_pre) == 6
    assert s_pre[0].get("label") == "alignment_gate"
    assert s_pre[-1].get("label") == "pytest"

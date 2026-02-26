from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_check_repo_alignment_guard_list_contract():
    txt = (ROOT / "scripts" / "check_repo_alignment.py").read_text(encoding="utf-8", errors="replace")
    assert "GUARD_TESTS = [" in txt
    required = [
        "tests/test_repo_doctor_strict.py",
        "tests/test_bootstrap_helper_adoption.py",
        "tests/test_no_duplicate_script_bootstrap.py",
        "tests/test_no_legacy_state_paths.py",
        "tests/test_validation_wiring.py",
        "tests/test_makefile_wiring.py",
        "tests/test_readme_alignment_wiring.py",
        "tests/test_repo_alignment_workflow_doc.py",
        "tests/test_pre_release_sanity_doc_wiring.py",
        "tests/test_check_repo_alignment_contract.py",
    ]
    for item in required:
        assert txt.count(item) == 1, item
    assert "--list-tests" in txt
    assert "--json" in txt

    out = subprocess.check_output(
        [sys.executable, str(ROOT / "scripts" / "check_repo_alignment.py"), "--list-tests"],
        cwd=str(ROOT),
        text=True,
    )
    listed = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("tests/")]
    assert listed == required

    out_json_list = subprocess.check_output(
        [sys.executable, str(ROOT / "scripts" / "check_repo_alignment.py"), "--list-tests", "--json"],
        cwd=str(ROOT),
        text=True,
    )
    payload_list = json.loads(out_json_list)
    assert payload_list.get("schema_version") == 1
    assert payload_list.get("mode") == "list-tests"
    assert payload_list.get("ok") is True
    assert isinstance(payload_list.get("started_at"), str) and payload_list.get("started_at")
    assert isinstance(payload_list.get("finished_at"), str) and payload_list.get("finished_at")
    assert isinstance(payload_list.get("duration_seconds"), (int, float))
    assert payload_list.get("duration_seconds") >= 0
    assert payload_list.get("guard_tests") == required

    out_json = subprocess.check_output(
        [sys.executable, str(ROOT / "scripts" / "check_repo_alignment.py"), "--json"],
        cwd=str(ROOT),
        env={**os.environ, "CBP_ALIGNMENT_SKIP_GUARDS": "1"},
        text=True,
    )
    payload = json.loads(out_json)
    assert payload.get("schema_version") == 1
    assert payload.get("mode") == "full_skip_guards"
    assert payload.get("ok") is True
    assert isinstance(payload.get("started_at"), str) and payload.get("started_at")
    assert isinstance(payload.get("finished_at"), str) and payload.get("finished_at")
    assert isinstance(payload.get("duration_seconds"), (int, float))
    assert payload.get("duration_seconds") >= 0
    assert (payload.get("repo_doctor") or {}).get("rc") == 0
    assert (payload.get("guard_tests") or {}).get("rc") == 0
    assert (payload.get("guard_tests") or {}).get("count") == len(required)
    assert (payload.get("guard_tests") or {}).get("skipped") is True
    assert payload.get("tests") == required
    assert isinstance(payload.get("tests"), list) and len(payload.get("tests")) > 0
    assert (payload.get("guard_tests") or {}).get("count") == len(payload.get("tests") or [])

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def test_validate_runs_alignment_gate_and_preflight_check():
    txt = _read("scripts/validate.py")
    assert "scripts/check_repo_alignment.py" in txt
    assert "scripts/preflight_check.py" in txt
    assert "--quick" in txt
    assert "--json" in txt
    assert "tests/test_repo_doctor_strict.py" in txt
    assert "tests/test_bootstrap_helper_adoption.py" in txt
    assert "tests/test_no_duplicate_script_bootstrap.py" in txt
    assert "tests/test_no_legacy_state_paths.py" in txt
    assert "SCHEMA_VERSION = 1" in txt
    assert "\"quick\" if args.quick else \"full\"" in txt
    assert "CBP_VALIDATE_SKIP_PYTEST" in txt
    assert "\"mode\"" in txt
    assert "started_at" in txt
    assert "finished_at" in txt
    assert "duration_seconds" in txt


def test_pre_release_sanity_runs_alignment_gate():
    txt = _read("scripts/pre_release_sanity.py")
    assert "def run_alignment_gate()" in txt
    assert "scripts/check_repo_alignment.py" in txt
    assert "--json" in txt
    assert "SCHEMA_VERSION = 1" in txt
    assert "\"quick\" if all(skip_flags) else (\"full\" if not any(skip_flags) else \"custom\")" in txt
    assert "CBP_PRE_RELEASE_SKIP_PYTEST" in txt
    assert "\"mode\"" in txt
    assert "started_at" in txt
    assert "finished_at" in txt
    assert "duration_seconds" in txt


def test_check_repo_alignment_wiring_contract():
    txt = _read("scripts/check_repo_alignment.py")
    assert "tools/repo_doctor.py" in txt
    assert "--strict" in txt
    assert "--json" in txt
    assert "tests/test_repo_doctor_strict.py" in txt
    assert "tests/test_bootstrap_helper_adoption.py" in txt
    assert "tests/test_no_duplicate_script_bootstrap.py" in txt
    assert "tests/test_no_legacy_state_paths.py" in txt
    assert "tests/test_makefile_wiring.py" in txt
    assert "tests/test_readme_alignment_wiring.py" in txt
    assert "tests/test_repo_alignment_workflow_doc.py" in txt
    assert "tests/test_pre_release_sanity_doc_wiring.py" in txt
    assert "tests/test_check_repo_alignment_contract.py" in txt
    assert "SCHEMA_VERSION = 1" in txt
    assert "\"mode\"" in txt
    assert "started_at" in txt
    assert "finished_at" in txt
    assert "duration_seconds" in txt

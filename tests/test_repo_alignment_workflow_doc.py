from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_repo_alignment_workflow_doc_has_canonical_commands():
    txt = (ROOT / "docs" / "REPO_ALIGNMENT_WORKFLOW.md").read_text(encoding="utf-8", errors="replace")
    assert "python scripts/check_repo_alignment.py" in txt
    assert "python scripts/check_repo_alignment.py --list-tests" in txt
    assert "python scripts/check_repo_alignment.py --json" in txt
    assert "CBP_ALIGNMENT_SKIP_GUARDS=1 python scripts/check_repo_alignment.py --json" in txt
    assert "python scripts/validate.py --quick --json" in txt
    assert "CBP_VALIDATE_SKIP_PYTEST=1 python scripts/validate.py --json" in txt
    assert "pytest` step as skipped" in txt
    assert "schema_version" in txt
    assert "mode" in txt
    assert "full_skip_guards" in txt
    assert "list-tests" in txt
    assert "quick" in txt
    assert "custom" in txt
    assert "started_at" in txt
    assert "finished_at" in txt
    assert "duration_seconds" in txt
    assert "python scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy --skip-pytest --skip-config --skip-imports" in txt
    assert "CBP_PRE_RELEASE_SKIP_PYTEST=1 python scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy" in txt
    assert "GUARD_TESTS" in txt
    assert "inspect with `--list-tests`" in txt
    assert "python scripts/validate.py --quick" in txt
    assert "python scripts/validate.py" in txt
    assert "make check-alignment" in txt
    assert "make alignment" in txt
    assert "make check-alignment-list" in txt
    assert "make check-alignment-list-json" in txt
    assert "make check-alignment-json" in txt
    assert "make check-alignment-json-fast" in txt
    assert "make validate-quick" in txt
    assert "make validate-json-quick" in txt
    assert "make validate-json-fast" in txt
    assert "make validate-json" in txt
    assert "make validate" in txt
    assert "make pre-release-sanity" in txt
    assert "make pre-release-sanity-quick" in txt
    assert "make pre-release-sanity-json-quick" in txt
    assert "make pre-release-sanity-json-fast" in txt

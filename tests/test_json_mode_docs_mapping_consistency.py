from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_json_mode_docs_mapping_consistency():
    wf = (ROOT / "docs" / "REPO_ALIGNMENT_WORKFLOW.md").read_text(encoding="utf-8", errors="replace")

    # Alignment modes
    assert "mode` values: `full` (default) or `full_skip_guards`" in wf
    assert "CBP_ALIGNMENT_SKIP_GUARDS=1 python scripts/check_repo_alignment.py --json" in wf
    assert "mode` value: `list-tests`." in wf
    assert "python scripts/check_repo_alignment.py --list-tests --json" in wf

    # Validate modes
    assert "python scripts/validate.py --quick --json" in wf
    assert "mode` values: `quick` or `full`." in wf
    assert "CBP_VALIDATE_SKIP_PYTEST=1 python scripts/validate.py --json" in wf

    # Pre-release modes
    assert "mode` values: `quick`, `full`, or `custom`" in wf
    assert "python scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy --skip-pytest --skip-config --skip-imports" in wf
    assert "CBP_PRE_RELEASE_SKIP_PYTEST=1 python scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy" in wf

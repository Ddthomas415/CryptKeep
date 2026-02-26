from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_makefile_has_alignment_targets():
    txt = (ROOT / "Makefile").read_text(encoding="utf-8", errors="replace")
    assert "doctor-strict:" in txt
    assert "alignment: check-alignment" in txt
    assert "check-alignment:" in txt
    assert "check-alignment-list:" in txt
    assert "check-alignment-list-json:" in txt
    assert "check-alignment-json:" in txt
    assert "check-alignment-json-fast:" in txt
    assert "validate-quick:" in txt
    assert "validate-json-quick:" in txt
    assert "validate-json-fast:" in txt
    assert "validate-json:" in txt
    assert "validate:" in txt
    assert "pre-release-sanity:" in txt
    assert "pre-release-sanity-quick:" in txt
    assert "pre-release-sanity-json-quick:" in txt
    assert "pre-release-sanity-json-fast:" in txt
    assert "test:" in txt
    assert "scripts/check_repo_alignment.py" in txt
    assert "scripts/check_repo_alignment.py --list-tests" in txt
    assert "scripts/check_repo_alignment.py --list-tests --json" in txt
    assert "scripts/check_repo_alignment.py --json" in txt
    assert "CBP_ALIGNMENT_SKIP_GUARDS=1" in txt
    assert "scripts/validate.py --quick --json" in txt
    assert "CBP_VALIDATE_SKIP_PYTEST=1" in txt
    assert "scripts/validate.py --json" in txt
    assert "scripts/validate.py --quick" in txt
    assert "scripts/pre_release_sanity.py" in txt
    assert "scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy --skip-pytest --skip-config --skip-imports" in txt
    assert "CBP_PRE_RELEASE_SKIP_PYTEST=1" in txt
    assert "scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy" in txt

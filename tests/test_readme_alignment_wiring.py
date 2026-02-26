from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_has_alignment_commands():
    txt = (ROOT / "README.md").read_text(encoding="utf-8", errors="replace")
    assert "## Repo Alignment Commands" in txt
    assert "make check-alignment" in txt
    assert "make check-alignment-list" in txt
    assert "make check-alignment-list-json" in txt
    assert "make check-alignment-json" in txt
    assert "make validate-quick" in txt
    assert "make validate-json-quick" in txt
    assert "make validate-json-fast" in txt
    assert "make validate-json" in txt
    assert "make validate" in txt
    assert "make pre-release-sanity" in txt
    assert "make pre-release-sanity-quick" in txt
    assert "make pre-release-sanity-json-quick" in txt
    assert "make pre-release-sanity-json-fast" in txt
    assert "CBP_ALIGNMENT_SKIP_GUARDS=1 python scripts/check_repo_alignment.py --json" in txt
    assert "CBP_VALIDATE_SKIP_PYTEST=1 python scripts/validate.py --json" in txt
    assert "CBP_PRE_RELEASE_SKIP_PYTEST=1 python scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy" in txt

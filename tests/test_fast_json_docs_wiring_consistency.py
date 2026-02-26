from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def test_fast_json_docs_wiring_consistency():
    mk = _read("Makefile")
    rd = _read("README.md")
    wf = _read("docs/REPO_ALIGNMENT_WORKFLOW.md")

    # Makefile targets exist and are env-gated as intended.
    assert "validate-json-fast:" in mk
    assert "CBP_VALIDATE_SKIP_PYTEST=1" in mk
    assert "pre-release-sanity-json-fast:" in mk
    assert "CBP_PRE_RELEASE_SKIP_PYTEST=1" in mk

    # README advertises both fast commands explicitly.
    assert "CBP_ALIGNMENT_SKIP_GUARDS=1 python scripts/check_repo_alignment.py --json" in rd
    assert "make validate-json-fast" in rd
    assert "CBP_VALIDATE_SKIP_PYTEST=1 python scripts/validate.py --json" in rd
    assert "make pre-release-sanity-json-fast" in rd
    assert "CBP_PRE_RELEASE_SKIP_PYTEST=1 python scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy" in rd

    # Workflow doc includes both direct commands and make targets.
    assert "CBP_VALIDATE_SKIP_PYTEST=1 python scripts/validate.py --json" in wf
    assert "make validate-json-fast" in wf
    assert "CBP_PRE_RELEASE_SKIP_PYTEST=1 python scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy" in wf
    assert "make pre-release-sanity-json-fast" in wf

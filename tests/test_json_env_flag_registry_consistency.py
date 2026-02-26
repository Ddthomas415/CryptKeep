from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def test_json_env_flag_registry_consistency():
    scripts = {
        "scripts/check_repo_alignment.py": "CBP_ALIGNMENT_SKIP_GUARDS",
        "scripts/validate.py": "CBP_VALIDATE_SKIP_PYTEST",
        "scripts/pre_release_sanity.py": "CBP_PRE_RELEASE_SKIP_PYTEST",
    }
    for path, flag in scripts.items():
        txt = _read(path)
        assert flag in txt, path

    mk = _read("Makefile")
    assert "CBP_ALIGNMENT_SKIP_GUARDS=1" in mk
    assert "CBP_VALIDATE_SKIP_PYTEST=1" in mk
    assert "CBP_PRE_RELEASE_SKIP_PYTEST=1" in mk

    rd = _read("README.md")
    assert "CBP_ALIGNMENT_SKIP_GUARDS=1 python scripts/check_repo_alignment.py --json" in rd
    assert "CBP_VALIDATE_SKIP_PYTEST=1 python scripts/validate.py --json" in rd
    assert "CBP_PRE_RELEASE_SKIP_PYTEST=1 python scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy" in rd

    wf = _read("docs/REPO_ALIGNMENT_WORKFLOW.md")
    assert "CBP_ALIGNMENT_SKIP_GUARDS=1 python scripts/check_repo_alignment.py --json" in wf
    assert "CBP_VALIDATE_SKIP_PYTEST=1 python scripts/validate.py --json" in wf
    assert "CBP_PRE_RELEASE_SKIP_PYTEST=1 python scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy" in wf

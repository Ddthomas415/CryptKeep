from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def test_json_script_command_registry_docs_consistency():
    rd = _read("README.md")
    wf = _read("docs/REPO_ALIGNMENT_WORKFLOW.md")

    # Canonical direct command registry for JSON surfaces.
    commands = [
        "python scripts/check_repo_alignment.py --list-tests --json",
        "python scripts/check_repo_alignment.py --json",
        "CBP_ALIGNMENT_SKIP_GUARDS=1 python scripts/check_repo_alignment.py --json",
        "python scripts/validate.py --quick --json",
        "python scripts/validate.py --json",
        "CBP_VALIDATE_SKIP_PYTEST=1 python scripts/validate.py --json",
        "python scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy --skip-pytest --skip-config --skip-imports",
        "CBP_PRE_RELEASE_SKIP_PYTEST=1 python scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy",
    ]

    # Workflow doc should be the full registry source for operator commands.
    for cmd in commands:
        assert cmd in wf, cmd

    # README intentionally contains fast-path direct commands for quick operator access.
    for cmd in [
        "CBP_ALIGNMENT_SKIP_GUARDS=1 python scripts/check_repo_alignment.py --json",
        "CBP_VALIDATE_SKIP_PYTEST=1 python scripts/validate.py --json",
        "CBP_PRE_RELEASE_SKIP_PYTEST=1 python scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy",
    ]:
        assert cmd in rd, cmd

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_make_json_target_command_contract():
    txt = (ROOT / "Makefile").read_text(encoding="utf-8", errors="replace")

    expected_snippets = [
        "check-alignment-list-json:",
        "@$(PYTHON) scripts/check_repo_alignment.py --list-tests --json",
        "check-alignment-json:",
        "@$(PYTHON) scripts/check_repo_alignment.py --json",
        "check-alignment-json-fast:",
        "@CBP_ALIGNMENT_SKIP_GUARDS=1 $(PYTHON) scripts/check_repo_alignment.py --json",
        "validate-json-quick:",
        "@$(PYTHON) scripts/validate.py --quick --json",
        "validate-json-fast:",
        "@CBP_VALIDATE_SKIP_PYTEST=1 $(PYTHON) scripts/validate.py --json",
        "validate-json:",
        "@$(PYTHON) scripts/validate.py --json",
        "pre-release-sanity-json-quick:",
        "@$(PYTHON) scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy --skip-pytest --skip-config --skip-imports",
        "pre-release-sanity-json-fast:",
        "@CBP_PRE_RELEASE_SKIP_PYTEST=1 $(PYTHON) scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy",
    ]

    for snippet in expected_snippets:
        assert snippet in txt, snippet

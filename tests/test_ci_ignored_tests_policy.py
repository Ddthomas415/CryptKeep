from __future__ import annotations

from pathlib import Path


IGNORED_TESTS = (
    "tests/test_symbol_scanner.py",
    "tests/test_dashboard_view_data.py",
    "tests/test_dashboard_page_runtime.py",
    "tests/test_dashboard_home_digest.py",
)


def test_optional_ignored_tests_workflow_is_manual_only() -> None:
    workflow = Path(".github/workflows/ci-ignored-tests.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "pull_request:" not in workflow
    assert "push:" not in workflow
    assert "make test-ci-ignored" in workflow


def test_ignored_test_slice_documented_in_make_policy_and_ci() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")
    policy = Path("docs/CI_IGNORED_TEST_POLICY.md").read_text(encoding="utf-8")
    ci = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    for test_path in IGNORED_TESTS:
        assert test_path in makefile
        assert test_path in policy
        assert f"--ignore={test_path}" in ci

from __future__ import annotations

from pathlib import Path


def test_required_governance_files_exist_and_are_nonempty() -> None:
    required = [
        Path("AGENTS.md"),
        Path("runtime_prompt.md"),
        Path("handoff_template.md"),
        Path("conformance_tests.md"),
    ]

    for path in required:
        assert path.exists(), f"missing required governance file: {path}"
        text = path.read_text(encoding="utf-8").strip()
        assert text, f"required governance file is empty: {path}"


def test_runtime_prompt_and_conformance_docs_have_expected_headings() -> None:
    runtime_prompt = Path("runtime_prompt.md").read_text(encoding="utf-8")
    conformance = Path("conformance_tests.md").read_text(encoding="utf-8")

    assert "# Runtime Prompt" in runtime_prompt
    assert "Use this short prompt for normal execution work in this repo" in runtime_prompt
    assert "# Conformance Tests" in conformance
    assert "Use targeted verification first." in conformance

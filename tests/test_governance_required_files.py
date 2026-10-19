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


def test_runtime_prompt_and_conformance_docs_have_expected_anchors() -> None:
    runtime_prompt = Path("runtime_prompt.md").read_text(encoding="utf-8")
    conformance = Path("conformance_tests.md").read_text(encoding="utf-8")

    assert "# Objective-Driven Working Protocol" in runtime_prompt
    assert "READY_FOR_INDEPENDENT_REVIEW" in runtime_prompt
    assert "the implementing thread cannot independently approve itself" in runtime_prompt
    assert "Do not passively wait" in runtime_prompt
    assert "Do not reopen completed issues" in runtime_prompt
    for obsolete in ("less progress over more progress", "Allowed normal output format only:",
                     "no further implementation until review result is available"):
        assert obsolete not in runtime_prompt
    pointer = Path("docs/.internal/runtime_prompt.md").read_text(encoding="utf-8")
    assert "../../runtime_prompt.md" in pointer
    assert "ROLE: AUTONOMOUS_HARDENING" not in pointer
    assert "# Conformance Tests" in conformance
    assert "Use targeted verification first." in conformance


def test_planning_documents_do_not_restart_historical_work() -> None:
    def normalized(path):
        return " ".join(Path(path).read_text(encoding="utf-8").split())

    for path in ("docs/HANDOFF.md", "docs/CHAT_HANDOFF.md"):
        assert "HISTORICAL / SUPERSEDED" in normalized(path)
    assert "Historical Operating Snapshots" in normalized("REMAINING_TASKS.md")
    assert "Historical snapshot only." in normalized("docs/ROADMAP_TRACKING_CHECKLIST.md")
    expansion = normalized("docs/research/strategy_expansion_roadmap.md")
    assert "do not rebuild them from this roadmap" in expansion
    assert "If only one next build starts now" not in expansion
    alignment = normalized("docs/REPO_ALIGNMENT_WORKFLOW.md")
    assert "Unrelated layout/documentation drift does not block independent work" in alignment
    assert "Required release and CI checks remain required and must not be bypassed" in alignment

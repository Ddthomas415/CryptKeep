from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_ENTRY_RE = re.compile(r"^- ✅ Phase (\d+):")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:")
BACKTICK_RE = re.compile(r"`([^`]+)`")
RECENT_WINDOW_SIZE = 12

ACTION_VERBS = ("added", "hardened", "fixed", "cleaned")
VALIDATION_VERBS = ("validated", "hardened", "fixed", "cleaned")


def _recent_phase_checklist_lines() -> list[tuple[int, str, str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()

    entries_by_phase: dict[int, list[str]] = {}
    ordered_verifications: list[int] = []

    for line in lines:
        entry_match = PHASE_ENTRY_RE.match(line)
        if entry_match:
            phase = int(entry_match.group(1))
            entries_by_phase.setdefault(phase, []).append(line)
            continue

        verification_match = PHASE_VERIFICATION_RE.match(line)
        if verification_match:
            ordered_verifications.append(int(verification_match.group(1)))

    assert ordered_verifications, "No phase verification lines found in CHECKPOINTS.md"

    recent_phases = ordered_verifications[-RECENT_WINDOW_SIZE:]
    out: list[tuple[int, str, str]] = []

    for phase in recent_phases:
        entries = entries_by_phase.get(phase, [])
        assert len(entries) >= 2, f"Phase {phase} must have at least two checklist lines"
        out.append((phase, entries[-2], entries[-1]))

    return out


def _has_repo_path_reference(line: str) -> bool:
    for token in BACKTICK_RE.findall(line):
        if any(ch in token for ch in "*?[]"):
            continue
        if (token.startswith("tests/") and token.endswith(".py")) or (
            token.startswith("scripts/") and token.endswith(".py")
        ) or (token.startswith("docs/") and token.endswith(".md")):
            return True
    return False


def test_recent_first_checklist_lines_include_action_and_path() -> None:
    for phase, first_line, _ in _recent_phase_checklist_lines():
        normalized = first_line.lower()
        assert any(verb in normalized for verb in ACTION_VERBS), (
            f"Phase {phase} first checklist line should include an action verb"
        )
        assert _has_repo_path_reference(first_line), (
            f"Phase {phase} first checklist line should include a backticked repo path"
        )



def test_recent_second_checklist_lines_include_validation_verb() -> None:
    for phase, _, second_line in _recent_phase_checklist_lines():
        normalized = second_line.lower()
        assert any(verb in normalized for verb in VALIDATION_VERBS), (
            f"Phase {phase} second checklist line should include a validation-style verb"
        )

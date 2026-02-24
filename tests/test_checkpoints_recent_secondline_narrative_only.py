from __future__ import annotations

import re
import pathlib


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_ENTRY_RE = re.compile(r"^- ✅ Phase (\d+):")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:")
BACKTICK_RE = re.compile(r"`([^`]+)`")
RECENT_WINDOW_SIZE = 12


def _recent_second_lines() -> list[tuple[int, str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()

    entries_by_phase: dict[int, list[str]] = {}
    verification_order: list[int] = []

    for line in lines:
        if m := PHASE_ENTRY_RE.match(line):
            phase = int(m.group(1))
            entries_by_phase.setdefault(phase, []).append(line)
            continue
        if m := PHASE_VERIFICATION_RE.match(line):
            verification_order.append(int(m.group(1)))

    assert verification_order, "No phase verification lines found in CHECKPOINTS.md"

    out: list[tuple[int, str]] = []
    for phase in verification_order[-RECENT_WINDOW_SIZE:]:
        entries = entries_by_phase.get(phase, [])
        assert len(entries) >= 2, f"Phase {phase} must have at least two checklist lines"
        out.append((phase, entries[-1]))
    return out


def test_recent_second_lines_have_no_concrete_test_artifact_path() -> None:
    for phase, line in _recent_second_lines():
        concrete_test_paths = [
            token
            for token in BACKTICK_RE.findall(line)
            if token.startswith("tests/")
            and token.endswith(".py")
            and not any(ch in token for ch in "*?[]")
        ]
        assert not concrete_test_paths, (
            f"Phase {phase} second checklist line should not carry concrete test artifact paths"
        )



def test_recent_second_lines_keep_validation_verb() -> None:
    verbs = ("validated", "hardened", "fixed", "cleaned")
    for phase, line in _recent_second_lines():
        assert any(verb in line.lower() for verb in verbs), (
            f"Phase {phase} second checklist line should keep validation-style wording"
        )

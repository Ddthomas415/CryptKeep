from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_WITH_COUNT_RE = re.compile(
    r"^- ✅ Phase (\d+) verification:.*full pytest pass \(`(\d+) passed`\)"
)
RECENT_WINDOW_SIZE = 12


def _verification_counts() -> list[tuple[int, int]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    vals: list[tuple[int, int]] = []

    for line in lines:
        match = PHASE_VERIFICATION_WITH_COUNT_RE.match(line)
        if match:
            vals.append((int(match.group(1)), int(match.group(2))))

    assert vals, "No verification lines with full pytest count found"
    return vals


def test_recent_full_pytest_counts_are_positive() -> None:
    recent = _verification_counts()[-RECENT_WINDOW_SIZE:]
    for phase, count in recent:
        assert count > 0, f"Phase {phase} must report a positive passed-count"



def test_recent_full_pytest_counts_are_nondecreasing() -> None:
    recent = _verification_counts()[-RECENT_WINDOW_SIZE:]
    for idx in range(1, len(recent)):
        prev_phase, prev_count = recent[idx - 1]
        phase, count = recent[idx]
        assert count >= prev_count, (
            f"Phase {phase} passed-count ({count}) must be >= phase {prev_phase} ({prev_count})"
        )

from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:(.*)$")
BACKTICK_RE = re.compile(r"`([^`]+)`")
RECENT_WINDOW_SIZE = 12


def _recent_counts() -> list[tuple[int, int, int]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    rows: list[tuple[int, int, int]] = []

    for line in lines:
        match = PHASE_VERIFICATION_RE.match(line)
        if not match:
            continue

        phase = int(match.group(1))
        segments = [seg.strip() for seg in match.group(2).strip().split(",")]
        if len(segments) != 3:
            continue

        focused_payloads = BACKTICK_RE.findall(segments[0])
        full_payloads = BACKTICK_RE.findall(segments[2])
        if not focused_payloads or not full_payloads:
            continue

        fm = re.fullmatch(r"(\d+) passed", focused_payloads[-1])
        xm = re.fullmatch(r"(\d+) passed", full_payloads[-1])
        if not fm or not xm:
            continue

        focused = int(fm.group(1))
        full = int(xm.group(1))
        rows.append((phase, focused, full))

    assert rows, "No recent focused/full counts found"
    return rows[-RECENT_WINDOW_SIZE:]


def test_recent_full_minus_focused_gap_is_nonnegative() -> None:
    for phase, focused, full in _recent_counts():
        assert full - focused >= 0, (
            f"Phase {phase} full-focused gap should be nonnegative"
        )



def test_recent_full_minus_focused_gap_has_bounded_downside() -> None:
    recent = _recent_counts()
    gaps = [(phase, full - focused) for phase, focused, full in recent]

    for idx in range(1, len(gaps)):
        prev_phase, prev_gap = gaps[idx - 1]
        phase, gap = gaps[idx]
        delta = gap - prev_gap
        assert -1 <= delta <= 3, (
            f"Phase {phase} full-focused gap delta ({delta}) should be bounded in [-1, 3] "
            f"from phase {prev_phase} gap ({prev_gap})"
        )

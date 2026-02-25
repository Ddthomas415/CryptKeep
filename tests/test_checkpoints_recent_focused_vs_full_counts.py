from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:(.*)$")
BACKTICK_RE = re.compile(r"`([^`]+)`")
RECENT_WINDOW_SIZE = 12


def _recent_count_pairs() -> list[tuple[int, int, int]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    out: list[tuple[int, int, int]] = []

    for line in lines:
        match = PHASE_VERIFICATION_RE.match(line)
        if not match:
            continue

        phase = int(match.group(1))
        segments = [segment.strip() for segment in match.group(2).strip().split(",")]
        if len(segments) != 3:
            continue

        p1 = BACKTICK_RE.findall(segments[0])
        p3 = BACKTICK_RE.findall(segments[2])
        if not p1 or not p3:
            continue

        m1 = re.fullmatch(r"(\d+) passed", p1[-1])
        m3 = re.fullmatch(r"(\d+) passed", p3[-1])
        if not m1 or not m3:
            continue

        focused_count = int(m1.group(1))
        full_count = int(m3.group(1))
        out.append((phase, focused_count, full_count))

    assert out, "No focused/full passed-count pairs found in recent verifications"
    return out[-RECENT_WINDOW_SIZE:]


def test_recent_full_counts_cover_focused_counts() -> None:
    for phase, focused_count, full_count in _recent_count_pairs():
        assert full_count >= focused_count, (
            f"Phase {phase} full passed-count ({full_count}) must be >= focused count ({focused_count})"
        )



def test_recent_count_pairs_are_positive() -> None:
    for phase, focused_count, full_count in _recent_count_pairs():
        assert focused_count > 0, f"Phase {phase} focused passed-count must be positive"
        assert full_count > 0, f"Phase {phase} full passed-count must be positive"

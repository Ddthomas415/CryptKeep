from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:(.*)$")
BACKTICK_RE = re.compile(r"`([^`]+)`")
RECENT_WINDOW_SIZE = 12


def _recent_full_counts() -> list[tuple[int, int]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    rows: list[tuple[int, int]] = []

    for line in lines:
        if not (m := PHASE_VERIFICATION_RE.match(line)):
            continue
        phase = int(m.group(1))
        segments = [seg.strip() for seg in m.group(2).strip().split(",")]
        if len(segments) != 3:
            continue
        payloads = BACKTICK_RE.findall(segments[2])
        if not payloads:
            continue
        if not (c := re.fullmatch(r"(\d+) passed", payloads[-1])):
            continue
        rows.append((phase, int(c.group(1))))

    assert rows, "No full pytest pass counts found"
    return rows[-RECENT_WINDOW_SIZE:]


def test_recent_full_counts_advance_with_bounded_positive_delta() -> None:
    recent = _recent_full_counts()
    for idx in range(1, len(recent)):
        prev_phase, prev_count = recent[idx - 1]
        phase, count = recent[idx]
        delta = count - prev_count
        assert 1 <= delta <= 3, (
            f"Phase {phase} full count delta ({delta}) should be bounded in [1, 3] "
            f"from phase {prev_phase} ({prev_count})"
        )

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
        match = PHASE_VERIFICATION_RE.match(line)
        if not match:
            continue

        phase = int(match.group(1))
        segments = [seg.strip() for seg in match.group(2).strip().split(",")]
        if len(segments) != 3:
            continue

        payloads = BACKTICK_RE.findall(segments[2])
        if not payloads:
            continue

        m = re.fullmatch(r"(\d+) passed", payloads[-1])
        if not m:
            continue

        rows.append((phase, int(m.group(1))))

    assert rows, "No full pytest pass counts found in verification lines"
    return rows[-RECENT_WINDOW_SIZE:]


def test_recent_full_counts_are_strictly_increasing() -> None:
    recent = _recent_full_counts()
    for idx in range(1, len(recent)):
        prev_phase, prev_count = recent[idx - 1]
        phase, count = recent[idx]
        assert count > prev_count, (
            f"Phase {phase} full passed-count ({count}) should be > "
            f"phase {prev_phase} ({prev_count})"
        )



def test_recent_full_counts_are_positive() -> None:
    for phase, count in _recent_full_counts():
        assert count > 0, f"Phase {phase} full passed-count must be positive"

from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:(.*)$")
BACKTICK_PAYLOAD_RE = re.compile(r"`([^`]+)`")
RECENT_WINDOW_SIZE = 12


def _recent_focused_counts() -> list[tuple[int, int]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    vals: list[tuple[int, int]] = []

    for line in lines:
        match = PHASE_VERIFICATION_RE.match(line)
        if not match:
            continue

        phase = int(match.group(1))
        segments = [segment.strip() for segment in match.group(2).strip().split(",")]
        if len(segments) != 3:
            continue

        payloads = BACKTICK_PAYLOAD_RE.findall(segments[0])
        if not payloads:
            continue

        focused_payload = payloads[-1]
        if not focused_payload.endswith(" passed"):
            continue

        count = int(focused_payload.split()[0])
        vals.append((phase, count))

    assert vals, "No focused passed-count payloads found in verification lines"
    return vals[-RECENT_WINDOW_SIZE:]


def test_recent_focused_passed_counts_are_positive() -> None:
    for phase, count in _recent_focused_counts():
        assert count > 0, f"Phase {phase} focused passed-count must be positive"



def test_recent_focused_passed_counts_are_bounded_nondecreasing() -> None:
    recent = _recent_focused_counts()
    for idx in range(1, len(recent)):
        prev_phase, prev_count = recent[idx - 1]
        phase, count = recent[idx]
        delta = count - prev_count
        assert 0 <= delta <= 3, (
            f"Phase {phase} focused passed-count delta ({delta}) should be bounded in [0, 3] "
            f"from phase {prev_phase} ({prev_count})"
        )

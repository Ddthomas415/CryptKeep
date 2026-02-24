from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:(.*)$")
RECENT_WINDOW_SIZE = 12


def _recent_segments() -> list[tuple[int, str, str, str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    rows: list[tuple[int, str, str, str]] = []

    for line in lines:
        if not (m := PHASE_VERIFICATION_RE.match(line)):
            continue
        phase = int(m.group(1))
        segments = [segment.strip().lower() for segment in m.group(2).strip().split(",")]
        if len(segments) != 3:
            continue
        rows.append((phase, segments[0], segments[1], segments[2]))

    assert rows, "No phase verification lines found in CHECKPOINTS.md"
    return rows[-RECENT_WINDOW_SIZE:]


def test_recent_focused_segment_excludes_crosscheck_and_full_markers() -> None:
    for phase, focused, _, _ in _recent_segments():
        assert "cross-check" not in focused, (
            f"Phase {phase} focused segment should not contain cross-check marker"
        )
        assert "full pytest" not in focused, (
            f"Phase {phase} focused segment should not contain full pytest marker"
        )


def test_recent_crosscheck_segment_excludes_focused_and_full_markers() -> None:
    for phase, _, crosscheck, _ in _recent_segments():
        assert "full pytest" not in crosscheck, (
            f"Phase {phase} cross-check segment should not contain full pytest marker"
        )


def test_recent_full_segment_excludes_focused_and_crosscheck_markers() -> None:
    for phase, _, _, full in _recent_segments():
        assert "focused" not in full, (
            f"Phase {phase} full segment should not contain focused marker"
        )
        assert "cross-check" not in full, (
            f"Phase {phase} full segment should not contain cross-check marker"
        )

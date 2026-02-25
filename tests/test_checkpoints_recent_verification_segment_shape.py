from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:(.*)$")
RECENT_WINDOW_SIZE = 12


def _recent_verification_bodies() -> list[tuple[int, str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    out: list[tuple[int, str]] = []

    for line in lines:
        match = PHASE_VERIFICATION_RE.match(line)
        if match:
            out.append((int(match.group(1)), match.group(2).strip()))

    assert out, "No phase verification lines found in CHECKPOINTS.md"
    return out[-RECENT_WINDOW_SIZE:]


def test_recent_verification_lines_have_three_comma_separated_segments() -> None:
    for phase, body in _recent_verification_bodies():
        segments = [s.strip() for s in body.split(",")]
        assert len(segments) == 3, (
            f"Phase {phase} verification should have exactly three comma-separated segments"
        )



def test_recent_verification_segments_include_required_markers() -> None:
    for phase, body in _recent_verification_bodies():
        segments = [s.strip().lower() for s in body.split(",")]
        assert "focused" in segments[0], (
            f"Phase {phase} segment 1 should contain focused-test marker"
        )
        assert "cross-check" in segments[1] and "pass" in segments[1], (
            f"Phase {phase} segment 2 should contain cross-check pass marker"
        )
        assert "full pytest pass" in segments[2], (
            f"Phase {phase} segment 3 should contain full pytest pass marker"
        )

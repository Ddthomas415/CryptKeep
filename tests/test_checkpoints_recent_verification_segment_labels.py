from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:(.*)$")
RECENT_WINDOW_SIZE = 12


def _recent_segments() -> list[tuple[int, list[str]]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    out: list[tuple[int, list[str]]] = []

    for line in lines:
        match = PHASE_VERIFICATION_RE.match(line)
        if not match:
            continue
        phase = int(match.group(1))
        segs = [seg.strip().lower() for seg in match.group(2).strip().split(",")]
        out.append((phase, segs))

    assert out, "No phase verification lines found in CHECKPOINTS.md"
    return out[-RECENT_WINDOW_SIZE:]


def test_recent_verification_segment_markers_and_pass_semantics() -> None:
    for phase, segs in _recent_segments():
        assert len(segs) == 3, f"Phase {phase} verification should have three segments"
        assert "focused" in segs[0] and "pass" in segs[0], (
            f"Phase {phase} segment 1 should contain focused pass semantics"
        )
        assert "cross-check" in segs[1] and "pass" in segs[1], (
            f"Phase {phase} segment 2 should contain cross-check pass semantics"
        )
        assert segs[2].startswith("full pytest pass"), (
            f"Phase {phase} segment 3 should start with 'full pytest pass'"
        )

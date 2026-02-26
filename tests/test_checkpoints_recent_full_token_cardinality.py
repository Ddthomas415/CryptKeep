from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:(.*)$")
RECENT_WINDOW_SIZE = 12


def _recent_full_segments() -> list[tuple[int, str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    rows: list[tuple[int, str]] = []

    for line in lines:
        match = PHASE_VERIFICATION_RE.match(line)
        if not match:
            continue

        phase = int(match.group(1))
        segments = [segment.strip().lower() for segment in match.group(2).strip().split(",")]
        if len(segments) != 3:
            continue

        rows.append((phase, segments[2]))

    assert rows, "No phase verification lines found in CHECKPOINTS.md"
    return rows[-RECENT_WINDOW_SIZE:]


def test_recent_full_segment_has_single_full_pytest_token() -> None:
    for phase, segment in _recent_full_segments():
        assert segment.count("full pytest") == 1, (
            f"Phase {phase} full segment should contain exactly one 'full pytest' token"
        )



def test_recent_full_segment_has_pass_semantics() -> None:
    for phase, segment in _recent_full_segments():
        assert "pass" in segment, (
            f"Phase {phase} full segment should contain pass semantics"
        )

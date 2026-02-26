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
        if not (m := PHASE_VERIFICATION_RE.match(line)):
            continue
        phase = int(m.group(1))
        segs = [seg.strip().lower() for seg in m.group(2).strip().split(",")]
        if len(segs) != 3:
            continue
        rows.append((phase, segs[2]))

    assert rows, "No phase verification lines found in CHECKPOINTS.md"
    return rows[-RECENT_WINDOW_SIZE:]


def test_recent_full_segment_has_single_full_pytest_token() -> None:
    for phase, seg in _recent_full_segments():
        assert seg.count("full pytest") == 1, (
            f"Phase {phase} full segment should contain exactly one 'full pytest' token"
        )


def test_recent_full_segment_has_single_pass_token() -> None:
    for phase, seg in _recent_full_segments():
        pass_words = re.findall(r"\bpass\b", seg)
        assert len(pass_words) == 1, (
            f"Phase {phase} full segment should contain exactly one 'pass' token"
        )

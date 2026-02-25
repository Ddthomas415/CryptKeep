from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:(.*)$")
RECENT_WINDOW_SIZE = 12


def _recent_verification_bodies() -> list[tuple[int, str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    rows: list[tuple[int, str]] = []
    for line in lines:
        if m := PHASE_VERIFICATION_RE.match(line):
            rows.append((int(m.group(1)), m.group(2).strip()))
    assert rows, "No phase verification lines found in CHECKPOINTS.md"
    return rows[-RECENT_WINDOW_SIZE:]


def test_recent_verification_lines_use_canonical_delimiter_spacing() -> None:
    for phase, body in _recent_verification_bodies():
        assert body.count(", ") == 2, (
            f"Phase {phase} verification should use exactly two ', ' delimiters"
        )
        assert body.count(",") == 2, (
            f"Phase {phase} verification should contain exactly two commas"
        )



def test_recent_verification_lines_split_cleanly_into_three_segments() -> None:
    for phase, body in _recent_verification_bodies():
        segments = body.split(", ")
        assert len(segments) == 3, (
            f"Phase {phase} verification should split into three segments via ', '"
        )
        assert all(segment.strip() == segment for segment in segments), (
            f"Phase {phase} verification segments should not have edge whitespace"
        )

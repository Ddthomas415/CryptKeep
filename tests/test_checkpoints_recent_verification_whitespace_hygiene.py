from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification: (.+)$")
RECENT_WINDOW_SIZE = 12


def _recent_verification_bodies() -> list[tuple[int, str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    rows: list[tuple[int, str]] = []

    for line in lines:
        if m := PHASE_VERIFICATION_RE.match(line):
            rows.append((int(m.group(1)), m.group(2)))

    assert rows, "No phase verification lines found in CHECKPOINTS.md"
    return rows[-RECENT_WINDOW_SIZE:]


def test_recent_verification_bodies_have_no_double_spaces() -> None:
    for phase, body in _recent_verification_bodies():
        assert "  " not in body, (
            f"Phase {phase} verification body should not contain double spaces"
        )



def test_recent_verification_bodies_have_no_tab_characters() -> None:
    for phase, body in _recent_verification_bodies():
        assert "\t" not in body, (
            f"Phase {phase} verification body should not contain tab characters"
        )

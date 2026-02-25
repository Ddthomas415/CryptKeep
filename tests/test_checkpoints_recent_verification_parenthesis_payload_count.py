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


def test_recent_verification_has_three_parenthesized_payload_groups() -> None:
    for phase, body in _recent_verification_bodies():
        assert body.count("(") == 3, (
            f"Phase {phase} verification should contain exactly three '(' payload groups"
        )
        assert body.count(")") == 3, (
            f"Phase {phase} verification should contain exactly three ')' payload groups"
        )

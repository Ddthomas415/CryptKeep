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
            rows.append((int(m.group(1)), m.group(2).lower()))
    assert rows, "No phase verification lines found in CHECKPOINTS.md"
    return rows[-RECENT_WINDOW_SIZE:]


def test_recent_verification_marker_order_is_strict() -> None:
    for phase, body in _recent_verification_bodies():
        i_focused = body.find("focused")
        i_cross = body.find("cross-check")
        i_full = body.find("full pytest")

        assert i_focused != -1, f"Phase {phase} missing focused marker"
        assert i_cross != -1, f"Phase {phase} missing cross-check marker"
        assert i_full != -1, f"Phase {phase} missing full pytest marker"
        assert i_focused < i_cross < i_full, (
            f"Phase {phase} marker order should be focused < cross-check < full pytest"
        )

from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:")
RECENT_WINDOW_SIZE = 12


def _recent_verifications() -> list[tuple[int, str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    vals: list[tuple[int, str]] = []
    for line in lines:
        match = PHASE_VERIFICATION_RE.match(line)
        if match:
            vals.append((int(match.group(1)), line))
    assert vals, "No phase verification lines found in CHECKPOINTS.md"
    return vals[-RECENT_WINDOW_SIZE:]


def test_recent_verifications_include_crosscheck_marker() -> None:
    for phase, line in _recent_verifications():
        normalized = line.lower()
        assert "cross-check" in normalized and "pass" in normalized, (
            f"Phase {phase} verification should include a cross-check pass marker"
        )

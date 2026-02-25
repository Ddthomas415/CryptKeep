from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:")
RECENT_WINDOW_SIZE = 12


def _recent_verification_lines() -> list[tuple[int, str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    pairs: list[tuple[int, str]] = []

    for line in lines:
        match = PHASE_VERIFICATION_RE.match(line)
        if match:
            pairs.append((int(match.group(1)), line))

    assert pairs, "No phase verification lines found in CHECKPOINTS.md"
    return pairs[-RECENT_WINDOW_SIZE:]


def test_recent_verifications_include_focused_result_marker() -> None:
    for phase, line in _recent_verification_lines():
        assert "focused" in line.lower(), (
            f"Phase {phase} verification should include focused test result marker"
        )



def test_recent_verifications_include_full_pytest_marker() -> None:
    for phase, line in _recent_verification_lines():
        assert "full pytest pass" in line.lower(), (
            f"Phase {phase} verification should include full pytest marker"
        )
        assert re.search(r"\(\s*`?\d+ passed`?\s*\)", line) is not None, (
            f"Phase {phase} verification should include explicit passed-count segment"
        )

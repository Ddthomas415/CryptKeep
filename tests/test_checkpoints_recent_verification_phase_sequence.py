from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:")
RECENT_WINDOW_SIZE = 12


def _recent_verification_phase_ids() -> list[int]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    ids = [
        int(match.group(1))
        for line in lines
        if (match := PHASE_VERIFICATION_RE.match(line))
    ]
    assert ids, "No phase verification lines found in CHECKPOINTS.md"
    return ids[-RECENT_WINDOW_SIZE:]


def test_recent_verification_phase_ids_are_strictly_increasing() -> None:
    recent = _recent_verification_phase_ids()
    assert recent == sorted(set(recent)), (
        "Recent verification phase IDs must be unique and strictly increasing"
    )



def test_recent_verification_phase_ids_are_contiguous() -> None:
    recent = _recent_verification_phase_ids()
    assert recent == list(range(recent[0], recent[-1] + 1)), (
        "Recent verification phase IDs must be contiguous"
    )

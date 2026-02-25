from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:")
RECENT_WINDOW_SIZE = 12


def _recent_verification_ids() -> list[int]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    ids = [
        int(m.group(1))
        for line in lines
        if (m := PHASE_VERIFICATION_RE.match(line))
    ]
    assert ids, "No phase verification lines found in CHECKPOINTS.md"
    return ids[-RECENT_WINDOW_SIZE:]


def test_recent_verification_ids_advance_by_one() -> None:
    ids = _recent_verification_ids()
    for idx in range(1, len(ids)):
        prev_phase = ids[idx - 1]
        phase = ids[idx]
        assert phase - prev_phase == 1, (
            f"Phase {phase} should follow phase {prev_phase} with delta=1"
        )

from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_ENTRY_RE = re.compile(r"^- ✅ Phase (\d+):")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:")


def test_tail_block_has_latest_phase_triplet() -> None:
    lines = [line for line in CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines() if line]
    assert len(lines) >= 3, "CHECKPOINTS.md must have at least three non-empty lines"

    tail = lines[-3:]
    first_match = PHASE_ENTRY_RE.match(tail[0])
    second_match = PHASE_ENTRY_RE.match(tail[1])
    verification_match = PHASE_VERIFICATION_RE.match(tail[2])

    assert first_match is not None, "Tail line 1 must be a phase checklist line"
    assert second_match is not None, "Tail line 2 must be a phase checklist line"
    assert verification_match is not None, "Tail line 3 must be a phase verification line"

    p1 = int(first_match.group(1))
    p2 = int(second_match.group(1))
    pv = int(verification_match.group(1))

    assert p1 == p2 == pv, "Tail triplet must refer to one latest phase ID"



def test_no_newer_phase_exists_before_tail_latest() -> None:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()

    phase_ids: list[int] = []
    for line in lines:
        entry_match = PHASE_ENTRY_RE.match(line)
        if entry_match:
            phase_ids.append(int(entry_match.group(1)))
            continue

        verification_match = PHASE_VERIFICATION_RE.match(line)
        if verification_match:
            phase_ids.append(int(verification_match.group(1)))

    assert phase_ids, "No phase IDs found in CHECKPOINTS.md"

    latest_seen = max(phase_ids)
    tail_line = [line for line in lines if line][-1]
    tail_match = PHASE_VERIFICATION_RE.match(tail_line)
    assert tail_match is not None, "Last non-empty line must be a phase verification line"

    tail_phase = int(tail_match.group(1))
    assert tail_phase == latest_seen, "Tail phase must be the latest phase ID in file"

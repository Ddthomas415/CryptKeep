from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_ENTRY_RE = re.compile(r"^- ✅ Phase (\d+):")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:")
RECENT_WINDOW_SIZE = 12


def _collect_line_positions() -> tuple[dict[int, list[int]], dict[int, list[int]], list[int]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()

    entry_positions: dict[int, list[int]] = {}
    verification_positions: dict[int, list[int]] = {}
    phase_order: list[int] = []

    for idx, line in enumerate(lines):
        entry_match = PHASE_ENTRY_RE.match(line)
        if entry_match:
            phase = int(entry_match.group(1))
            entry_positions.setdefault(phase, []).append(idx)
            if phase not in phase_order:
                phase_order.append(phase)
            continue

        verification_match = PHASE_VERIFICATION_RE.match(line)
        if verification_match:
            phase = int(verification_match.group(1))
            verification_positions.setdefault(phase, []).append(idx)

    return entry_positions, verification_positions, phase_order


def test_recent_phase_blocks_are_contiguous_triplets() -> None:
    entry_positions, verification_positions, phase_order = _collect_line_positions()
    assert phase_order, "No phase entries found in CHECKPOINTS.md"

    recent_phases = phase_order[-RECENT_WINDOW_SIZE:]
    for phase in recent_phases:
        entries = entry_positions.get(phase, [])
        verifications = verification_positions.get(phase, [])

        assert len(entries) == 2, f"Phase {phase} must have two checklist lines"
        assert len(verifications) == 1, f"Phase {phase} must have one verification line"

        i0, i1 = entries
        iv = verifications[0]

        assert i1 == i0 + 1, f"Phase {phase} checklist lines must be adjacent"
        assert iv == i1 + 1, f"Phase {phase} verification must immediately follow checklist lines"



def test_recent_phase_triplets_are_in_phase_order() -> None:
    entry_positions, verification_positions, phase_order = _collect_line_positions()
    recent_phases = phase_order[-RECENT_WINDOW_SIZE:]

    triplet_starts = []
    for phase in recent_phases:
        entries = entry_positions[phase]
        verification = verification_positions[phase][0]
        triplet_starts.append((phase, entries[0], entries[1], verification))

    for idx in range(1, len(triplet_starts)):
        prev_phase, _, _, prev_ver = triplet_starts[idx - 1]
        phase, e0, _, _ = triplet_starts[idx]
        assert e0 > prev_ver, (
            f"Phase {phase} triplet must start after phase {prev_phase} triplet ends"
        )

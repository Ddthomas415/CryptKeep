from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_ENTRY_RE = re.compile(r"^- ✅ Phase (\d+):")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:")
RECENT_WINDOW_SIZE = 12


def _collect_positions() -> tuple[dict[int, list[int]], dict[int, int], list[int]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()

    entry_positions: dict[int, list[int]] = {}
    verification_positions: dict[int, int] = {}
    phase_seen_order: list[int] = []

    for idx, line in enumerate(lines):
        entry_match = PHASE_ENTRY_RE.match(line)
        if entry_match:
            phase = int(entry_match.group(1))
            entry_positions.setdefault(phase, []).append(idx)
            if phase not in phase_seen_order:
                phase_seen_order.append(phase)
            continue

        verification_match = PHASE_VERIFICATION_RE.match(line)
        if verification_match:
            verification_positions[int(verification_match.group(1))] = idx

    return entry_positions, verification_positions, phase_seen_order


def test_recent_phase_blocks_have_two_entries_and_one_verification() -> None:
    entry_positions, verification_positions, phase_seen_order = _collect_positions()
    assert phase_seen_order, "No phase entries found in CHECKPOINTS.md"

    recent_phases = phase_seen_order[-RECENT_WINDOW_SIZE:]
    for phase in recent_phases:
        assert len(entry_positions.get(phase, [])) == 2, (
            f"Phase {phase} must have exactly two checklist lines"
        )
        assert phase in verification_positions, (
            f"Phase {phase} must have a verification line"
        )



def test_recent_phase_block_order_is_entries_then_verification() -> None:
    entry_positions, verification_positions, phase_seen_order = _collect_positions()
    recent_phases = phase_seen_order[-RECENT_WINDOW_SIZE:]

    for phase in recent_phases:
        entries = entry_positions[phase]
        verification = verification_positions[phase]
        assert entries[0] < entries[1] < verification, (
            f"Phase {phase} block order must be entry, entry, verification"
        )

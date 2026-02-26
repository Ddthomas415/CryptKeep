from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_ENTRY_RE = re.compile(r"^- ✅ Phase (\d+):")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:")
RECENT_WINDOW_SIZE = 12


def _phase_maps() -> tuple[dict[int, int], list[int]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()

    entry_counts: dict[int, int] = {}
    verification_order: list[int] = []

    for line in lines:
        entry_match = PHASE_ENTRY_RE.match(line)
        if entry_match:
            phase = int(entry_match.group(1))
            entry_counts[phase] = entry_counts.get(phase, 0) + 1
            continue

        verification_match = PHASE_VERIFICATION_RE.match(line)
        if verification_match:
            verification_order.append(int(verification_match.group(1)))

    assert verification_order, "No phase verification lines found in CHECKPOINTS.md"
    return entry_counts, verification_order


def test_recent_entry_and_verification_phase_sets_match() -> None:
    entry_counts, verification_order = _phase_maps()

    recent_verification_ids = verification_order[-RECENT_WINDOW_SIZE:]
    recent_verification_set = set(recent_verification_ids)
    recent_entry_set = {
        phase for phase in entry_counts if phase in recent_verification_set
    }

    assert recent_entry_set == recent_verification_set, (
        "Recent phase IDs must match between checklist entries and verification lines"
    )



def test_recent_phases_keep_expected_entry_count() -> None:
    entry_counts, verification_order = _phase_maps()

    for phase in verification_order[-RECENT_WINDOW_SIZE:]:
        assert entry_counts.get(phase, 0) >= 2, (
            f"Phase {phase} should have at least two checklist entry lines"
        )

from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_ENTRY_RE = re.compile(r"^- ✅ Phase (\d+):")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:")
RECENT_WINDOW_SIZE = 12


def _parse_counts() -> tuple[dict[int, int], dict[int, int], dict[int, int]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()

    entry_counts: dict[int, int] = {}
    verification_counts: dict[int, int] = {}
    last_entry_index: dict[int, int] = {}

    for idx, line in enumerate(lines):
        entry_match = PHASE_ENTRY_RE.match(line)
        if entry_match:
            phase = int(entry_match.group(1))
            entry_counts[phase] = entry_counts.get(phase, 0) + 1
            last_entry_index[phase] = idx
            continue

        verification_match = PHASE_VERIFICATION_RE.match(line)
        if verification_match:
            phase = int(verification_match.group(1))
            verification_counts[phase] = verification_counts.get(phase, 0) + 1

    return entry_counts, verification_counts, last_entry_index


def test_latest_phase_id_has_verification() -> None:
    entry_counts, verification_counts, _ = _parse_counts()
    assert entry_counts, "No phase entries found in CHECKPOINTS.md"

    latest_phase = max(entry_counts)
    assert latest_phase in verification_counts, (
        "Latest phase entry must include a verification line"
    )



def test_recent_phase_ids_are_contiguous_in_canonical_timeline() -> None:
    entry_counts, _, last_entry_index = _parse_counts()

    canonical_timeline = [
        phase for phase, _ in sorted(last_entry_index.items(), key=lambda item: item[1])
    ]
    assert canonical_timeline, "No canonical phase timeline found"

    recent = canonical_timeline[-RECENT_WINDOW_SIZE:]
    assert recent == list(range(recent[0], recent[-1] + 1)), (
        "Recent canonical phases must be contiguous"
    )



def test_recent_phase_line_shape_is_stable() -> None:
    entry_counts, verification_counts, _ = _parse_counts()
    latest_phase = max(entry_counts)

    start = max(min(entry_counts), latest_phase - RECENT_WINDOW_SIZE + 1)
    recent_phases = list(range(start, latest_phase + 1))

    for phase in recent_phases:
        assert entry_counts.get(phase, 0) == 2, (
            f"Phase {phase} must keep two checklist lines"
        )
        assert verification_counts.get(phase, 0) == 1, (
            f"Phase {phase} must keep one verification line"
        )

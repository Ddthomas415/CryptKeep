from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_ENTRY_RE = re.compile(r"^- ✅ Phase (\d+):")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:")
REQUIRED_VERIFICATION_FROM_PHASE = 95


def _collect_phase_lines() -> tuple[list[tuple[int, int]], list[tuple[int, int]], list[str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    entries: list[tuple[int, int]] = []
    verifications: list[tuple[int, int]] = []

    for idx, line in enumerate(lines):
        entry_match = PHASE_ENTRY_RE.match(line)
        if entry_match:
            entries.append((int(entry_match.group(1)), idx))
            continue

        verification_match = PHASE_VERIFICATION_RE.match(line)
        if verification_match:
            verifications.append((int(verification_match.group(1)), idx))

    return entries, verifications, lines


def _last_occurrence_map(pairs: list[tuple[int, int]]) -> dict[int, int]:
    out: dict[int, int] = {}
    for phase, idx in pairs:
        out[phase] = idx
    return out


def test_canonical_phase_timeline_is_strictly_increasing() -> None:
    entries, _, _ = _collect_phase_lines()
    assert entries, "No phase entries found in CHECKPOINTS.md"

    last_entries = _last_occurrence_map(entries)
    timeline = [
        phase for phase, _ in sorted(last_entries.items(), key=lambda item: item[1])
    ]

    assert timeline == sorted(timeline), (
        "Canonical (last-occurrence) phase timeline must be ascending"
    )



def test_verification_ids_are_unique() -> None:
    _, verifications, _ = _collect_phase_lines()
    assert verifications, "No phase verification lines found in CHECKPOINTS.md"

    verification_ids = [phase for phase, _ in verifications]
    assert len(verification_ids) == len(
        set(verification_ids)
    ), "Duplicate phase verification IDs found"



def test_recent_phases_have_verification_lines() -> None:
    entries, verifications, _ = _collect_phase_lines()

    last_entries = _last_occurrence_map(entries)
    last_verifications = _last_occurrence_map(verifications)

    required_phases = [
        p for p in sorted(last_entries) if p >= REQUIRED_VERIFICATION_FROM_PHASE
    ]
    assert required_phases, "No phases found in required verification range"

    missing = [p for p in required_phases if p not in last_verifications]
    assert not missing, f"Missing verification lines for phases: {missing}"



def test_verification_follows_phase_entry_for_recent_phases() -> None:
    entries, verifications, _ = _collect_phase_lines()

    last_entries = _last_occurrence_map(entries)
    last_verifications = _last_occurrence_map(verifications)

    for phase, entry_idx in sorted(last_entries.items()):
        if phase < REQUIRED_VERIFICATION_FROM_PHASE:
            continue

        verification_idx = last_verifications.get(phase)
        assert verification_idx is not None, f"Phase {phase} missing verification line"
        assert verification_idx > entry_idx, (
            f"Phase {phase} verification must appear after its phase entry"
        )

from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_ENTRY_RE = re.compile(r"^- ✅ Phase (\d+):")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:")
BACKTICK_RE = re.compile(r"`([^`]+)`")
RECENT_WINDOW_SIZE = 12


def _recent_phase_alignment_rows() -> list[tuple[int, str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()

    entries_by_phase: dict[int, list[str]] = {}
    verification_ids: list[int] = []

    for line in lines:
        entry_match = PHASE_ENTRY_RE.match(line)
        if entry_match:
            phase = int(entry_match.group(1))
            entries_by_phase.setdefault(phase, []).append(line)
            continue

        verification_match = PHASE_VERIFICATION_RE.match(line)
        if verification_match:
            verification_ids.append(int(verification_match.group(1)))

    assert verification_ids, "No phase verification lines found in CHECKPOINTS.md"
    recent_verification_ids = verification_ids[-RECENT_WINDOW_SIZE:]

    rows: list[tuple[int, str]] = []
    for phase in recent_verification_ids:
        entries = entries_by_phase.get(phase, [])
        assert len(entries) >= 2, f"Phase {phase} should have at least two entry lines"

        first_line = entries[-2]
        artifacts = [
            token
            for token in BACKTICK_RE.findall(first_line)
            if token.startswith("tests/test_checkpoints_") and token.endswith(".py")
        ]
        assert len(artifacts) == 1, (
            f"Phase {phase} should have exactly one checkpoint artifact in first line"
        )

        rows.append((phase, artifacts[0]))

    return rows


def test_recent_artifact_phase_ids_match_recent_verification_phase_ids() -> None:
    rows = _recent_phase_alignment_rows()
    artifact_phase_ids = [phase for phase, _ in rows]

    assert artifact_phase_ids == sorted(artifact_phase_ids), (
        "Artifact phase IDs should remain ordered"
    )
    assert artifact_phase_ids == list(range(artifact_phase_ids[0], artifact_phase_ids[-1] + 1)), (
        "Artifact phase IDs should be contiguous in recent window"
    )



def test_recent_artifact_files_exist_for_aligned_phases() -> None:
    for phase, artifact in _recent_phase_alignment_rows():
        assert pathlib.Path(artifact).exists(), (
            f"Phase {phase} aligned artifact does not exist: {artifact}"
        )

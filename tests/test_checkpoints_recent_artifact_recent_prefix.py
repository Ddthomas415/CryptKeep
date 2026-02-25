from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_ENTRY_RE = re.compile(r"^- ✅ Phase (\d+):")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:")
BACKTICK_RE = re.compile(r"`([^`]+)`")
RECENT_WINDOW_SIZE = 12


def _recent_firstline_artifacts() -> list[tuple[int, str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()

    entries_by_phase: dict[int, list[str]] = {}
    verification_order: list[int] = []

    for line in lines:
        if m := PHASE_ENTRY_RE.match(line):
            phase = int(m.group(1))
            entries_by_phase.setdefault(phase, []).append(line)
            continue
        if m := PHASE_VERIFICATION_RE.match(line):
            verification_order.append(int(m.group(1)))

    assert verification_order, "No phase verification lines found in CHECKPOINTS.md"

    rows: list[tuple[int, str]] = []
    for phase in verification_order[-RECENT_WINDOW_SIZE:]:
        entries = entries_by_phase.get(phase, [])
        assert len(entries) >= 2, f"Phase {phase} must have at least two checklist entries"

        first_line = entries[-2]
        artifacts = [
            token
            for token in BACKTICK_RE.findall(first_line)
            if token.startswith("tests/test_checkpoints_") and token.endswith(".py")
        ]

        assert len(artifacts) == 1, (
            f"Phase {phase} first line should contain exactly one checkpoint artifact"
        )
        rows.append((phase, artifacts[0]))

    return rows


def test_recent_firstline_artifacts_use_recent_prefix() -> None:
    for phase, artifact in _recent_firstline_artifacts():
        assert artifact.startswith("tests/test_checkpoints_recent_"), (
            f"Phase {phase} artifact should use recent-prefix naming: {artifact}"
        )


def test_recent_firstline_recent_artifacts_exist() -> None:
    for phase, artifact in _recent_firstline_artifacts():
        assert pathlib.Path(artifact).exists(), (
            f"Phase {phase} artifact does not exist: {artifact}"
        )

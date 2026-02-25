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
        entry_match = PHASE_ENTRY_RE.match(line)
        if entry_match:
            phase = int(entry_match.group(1))
            entries_by_phase.setdefault(phase, []).append(line)
            continue

        verification_match = PHASE_VERIFICATION_RE.match(line)
        if verification_match:
            verification_order.append(int(verification_match.group(1)))

    assert verification_order, "No phase verification lines found in CHECKPOINTS.md"

    out: list[tuple[int, str]] = []
    for phase in verification_order[-RECENT_WINDOW_SIZE:]:
        entries = entries_by_phase.get(phase, [])
        assert len(entries) >= 2, f"Phase {phase} must have at least two checklist lines"

        first_line = entries[-2]
        artifacts = [
            token
            for token in BACKTICK_RE.findall(first_line)
            if not any(ch in token for ch in "*?[]")
            and token.startswith("tests/test_checkpoints_")
            and token.endswith(".py")
        ]

        assert len(artifacts) == 1, (
            f"Phase {phase} should have exactly one checkpoint artifact reference"
        )
        out.append((phase, artifacts[0]))

    return out


def test_recent_firstline_artifacts_are_unique() -> None:
    rows = _recent_firstline_artifacts()
    artifacts = [artifact for _, artifact in rows]
    assert len(artifacts) == len(set(artifacts)), (
        "Recent first-line checkpoint artifacts should be unique across phases"
    )



def test_recent_firstline_artifact_paths_exist() -> None:
    for phase, artifact in _recent_firstline_artifacts():
        assert pathlib.Path(artifact).exists(), (
            f"Phase {phase} artifact does not exist: {artifact}"
        )

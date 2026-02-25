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
    ordered_verifications: list[int] = []

    for line in lines:
        entry_match = PHASE_ENTRY_RE.match(line)
        if entry_match:
            phase = int(entry_match.group(1))
            entries_by_phase.setdefault(phase, []).append(line)
            continue

        verification_match = PHASE_VERIFICATION_RE.match(line)
        if verification_match:
            ordered_verifications.append(int(verification_match.group(1)))

    assert ordered_verifications, "No phase verification lines found in CHECKPOINTS.md"

    out: list[tuple[int, str]] = []
    for phase in ordered_verifications[-RECENT_WINDOW_SIZE:]:
        entries = entries_by_phase.get(phase, [])
        assert len(entries) >= 2, f"Phase {phase} must have at least two checklist lines"

        first_line = entries[-2]
        artifacts: list[str] = []
        for token in BACKTICK_RE.findall(first_line):
            if any(ch in token for ch in "*?[]"):
                continue
            if (token.startswith("tests/") and token.endswith(".py")) or (
                token.startswith("scripts/") and token.endswith(".py")
            ) or (token.startswith("docs/") and token.endswith(".md")):
                artifacts.append(token)

        assert len(artifacts) == 1, (
            f"Phase {phase} first checklist line should have exactly one artifact"
        )
        out.append((phase, artifacts[0]))

    return out


def test_recent_firstline_artifacts_follow_checkpoint_test_naming() -> None:
    for phase, artifact in _recent_firstline_artifacts():
        assert artifact.startswith("tests/test_checkpoints_"), (
            f"Phase {phase} artifact should follow checkpoint test naming convention"
        )
        assert artifact.endswith(".py"), (
            f"Phase {phase} artifact should be a Python test file"
        )



def test_recent_firstline_checkpoint_artifacts_exist() -> None:
    for phase, artifact in _recent_firstline_artifacts():
        assert pathlib.Path(artifact).exists(), (
            f"Phase {phase} checkpoint artifact path does not exist: {artifact}"
        )

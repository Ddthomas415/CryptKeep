from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_ENTRY_RE = re.compile(r"^- ✅ Phase (\d+):\s+(.*)$")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:")
RECENT_WINDOW_SIZE = 12


SCOPE_TOKENS = ("recent", "tail", "checkpoint")


def _recent_second_line_bodies() -> list[tuple[int, str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()

    entries_by_phase: dict[int, list[str]] = {}
    verification_order: list[int] = []

    for line in lines:
        if m := PHASE_ENTRY_RE.match(line):
            phase = int(m.group(1))
            body = m.group(2)
            entries_by_phase.setdefault(phase, []).append(body)
            continue
        if m := PHASE_VERIFICATION_RE.match(line):
            verification_order.append(int(m.group(1)))

    assert verification_order, "No phase verification lines found in CHECKPOINTS.md"

    rows: list[tuple[int, str]] = []
    for phase in verification_order[-RECENT_WINDOW_SIZE:]:
        bodies = entries_by_phase.get(phase, [])
        assert len(bodies) >= 2, f"Phase {phase} must have at least two checklist entries"
        rows.append((phase, bodies[-1]))

    return rows


def test_recent_second_lines_include_scope_qualifier() -> None:
    for phase, body in _recent_second_line_bodies():
        normalized = body.lower()
        assert any(token in normalized for token in SCOPE_TOKENS), (
            f"Phase {phase} second checklist line should include scope qualifier"
        )

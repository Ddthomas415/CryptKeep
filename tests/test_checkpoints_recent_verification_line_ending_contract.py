from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification: (.+)$")
RECENT_WINDOW_SIZE = 12


def _recent_verification_lines() -> list[tuple[int, str, str]]:
    raw_lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    rows: list[tuple[int, str, str]] = []

    for raw in raw_lines:
        if m := PHASE_VERIFICATION_RE.match(raw):
            rows.append((int(m.group(1)), raw, m.group(2)))

    assert rows, "No phase verification lines found in CHECKPOINTS.md"
    return rows[-RECENT_WINDOW_SIZE:]


def test_recent_verification_lines_have_no_trailing_whitespace() -> None:
    for phase, raw, _ in _recent_verification_lines():
        assert raw == raw.rstrip(), (
            f"Phase {phase} verification line should not have trailing whitespace"
        )



def test_recent_verification_lines_end_with_full_pytest_payload() -> None:
    suffix_re = re.compile(r"full pytest pass \(`\d+ passed`\)$")
    for phase, _, body in _recent_verification_lines():
        assert suffix_re.search(body), (
            f"Phase {phase} verification line should end with full pytest payload"
        )

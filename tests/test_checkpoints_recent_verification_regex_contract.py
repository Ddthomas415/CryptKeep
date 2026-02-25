from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_LINE_RE = re.compile(r"^- ✅ Phase (\d+) verification: (.+)$")
RECENT_WINDOW_SIZE = 12

STRICT_BODY_RE = re.compile(
    r"^"
    r"focused .+ pass \(`\d+ passed`\), "
    r".+ cross-check pass \(`(?:True|False)(?: (?:True|False))*`\), "
    r"full pytest pass \(`\d+ passed`\)"
    r"$"
)


def _recent_verification_lines() -> list[tuple[int, str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    rows: list[tuple[int, str]] = []

    for line in lines:
        match = PHASE_VERIFICATION_LINE_RE.match(line)
        if match:
            rows.append((int(match.group(1)), match.group(2)))

    assert rows, "No phase verification lines found in CHECKPOINTS.md"
    return rows[-RECENT_WINDOW_SIZE:]


def test_recent_verification_lines_match_strict_regex_contract() -> None:
    for phase, body in _recent_verification_lines():
        assert STRICT_BODY_RE.match(body), (
            f"Phase {phase} verification line does not match strict contract: {body}"
        )

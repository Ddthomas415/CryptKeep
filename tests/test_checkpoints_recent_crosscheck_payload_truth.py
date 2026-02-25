from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:(.*)$")
BACKTICK_PAYLOAD_RE = re.compile(r"`([^`]+)`")
RECENT_WINDOW_SIZE = 12


def _recent_crosscheck_payloads() -> list[tuple[int, str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    out: list[tuple[int, str]] = []

    for line in lines:
        match = PHASE_VERIFICATION_RE.match(line)
        if not match:
            continue

        phase = int(match.group(1))
        segments = [segment.strip() for segment in match.group(2).strip().split(",")]
        if len(segments) != 3:
            continue

        payloads = BACKTICK_PAYLOAD_RE.findall(segments[1])
        if not payloads:
            continue

        out.append((phase, payloads[-1]))

    assert out, "No cross-check payloads found in verification lines"
    return out[-RECENT_WINDOW_SIZE:]


def test_recent_crosscheck_payloads_are_boolean_tuples() -> None:
    for phase, payload in _recent_crosscheck_payloads():
        assert re.fullmatch(r"(True|False)(?:\s+(True|False))*", payload), (
            f"Phase {phase} cross-check payload should be a boolean tuple"
        )



def test_recent_crosscheck_payloads_are_all_true() -> None:
    for phase, payload in _recent_crosscheck_payloads():
        values = payload.split()
        assert all(value == "True" for value in values), (
            f"Phase {phase} cross-check payload should contain only True values"
        )

from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:(.*)$")
BACKTICK_RE = re.compile(r"`([^`]+)`")
RECENT_WINDOW_SIZE = 12


def _recent_verification_lines() -> list[tuple[int, str]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    out: list[tuple[int, str]] = []

    for line in lines:
        if m := PHASE_VERIFICATION_RE.match(line):
            out.append((int(m.group(1)), m.group(2).strip()))

    assert out, "No phase verification lines found in CHECKPOINTS.md"
    return out[-RECENT_WINDOW_SIZE:]


def test_recent_verification_lines_have_exactly_three_backtick_payloads() -> None:
    for phase, body in _recent_verification_lines():
        payloads = BACKTICK_RE.findall(body)
        assert len(payloads) == 3, (
            f"Phase {phase} verification should contain exactly three backticked payloads"
        )



def test_recent_backtick_payload_positions_are_per_segment() -> None:
    for phase, body in _recent_verification_lines():
        segments = [seg.strip() for seg in body.split(",")]
        assert len(segments) == 3, f"Phase {phase} must have three segments"
        for idx, seg in enumerate(segments, start=1):
            payloads = BACKTICK_RE.findall(seg)
            assert len(payloads) == 1, (
                f"Phase {phase} segment {idx} should contain exactly one backticked payload"
            )

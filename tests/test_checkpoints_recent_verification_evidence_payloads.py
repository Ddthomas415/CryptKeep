from __future__ import annotations

import pathlib
import re


CHECKPOINTS_PATH = pathlib.Path("CHECKPOINTS.md")
PHASE_VERIFICATION_RE = re.compile(r"^- ✅ Phase (\d+) verification:(.*)$")
BACKTICK_PAYLOAD_RE = re.compile(r"`([^`]+)`")
RECENT_WINDOW_SIZE = 12


PASS_COUNT_RE = re.compile(r"^\d+ passed$")
BOOL_TUPLE_RE = re.compile(r"^(True|False)(?:\s+(True|False))*$")


def _recent_verification_segments() -> list[tuple[int, list[str]]]:
    lines = CHECKPOINTS_PATH.read_text(encoding="utf-8").splitlines()
    out: list[tuple[int, list[str]]] = []

    for line in lines:
        match = PHASE_VERIFICATION_RE.match(line)
        if not match:
            continue
        phase = int(match.group(1))
        segments = [segment.strip() for segment in match.group(2).strip().split(",")]
        out.append((phase, segments))

    assert out, "No phase verification lines found in CHECKPOINTS.md"
    return out[-RECENT_WINDOW_SIZE:]


def test_recent_verification_segments_include_backticked_payloads() -> None:
    for phase, segments in _recent_verification_segments():
        assert len(segments) == 3, (
            f"Phase {phase} verification must keep three segments"
        )
        for idx, segment in enumerate(segments, start=1):
            payloads = BACKTICK_PAYLOAD_RE.findall(segment)
            assert payloads, (
                f"Phase {phase} segment {idx} should include a backticked payload"
            )



def test_recent_verification_payload_shapes_are_valid() -> None:
    for phase, segments in _recent_verification_segments():
        s1_payload = BACKTICK_PAYLOAD_RE.findall(segments[0])[-1]
        s2_payload = BACKTICK_PAYLOAD_RE.findall(segments[1])[-1]
        s3_payload = BACKTICK_PAYLOAD_RE.findall(segments[2])[-1]

        assert PASS_COUNT_RE.fullmatch(s1_payload), (
            f"Phase {phase} segment 1 payload should be '<n> passed'"
        )
        assert BOOL_TUPLE_RE.fullmatch(s2_payload), (
            f"Phase {phase} segment 2 payload should be space-separated booleans"
        )
        assert PASS_COUNT_RE.fullmatch(s3_payload), (
            f"Phase {phase} segment 3 payload should be '<n> passed'"
        )

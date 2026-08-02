from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/ROADMAP_TRACKING_CHECKLIST.md"
BACKLOG = "REMAINING_TASKS.md"
LANE_MAP = "docs/BACKLOG_EXECUTION_LANES.md"


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_roadmap_checklist_preserves_source_of_truth_boundaries() -> None:
    text = _normalized(DOC)

    assert "operator-facing roadmap index" in text
    assert "It does not replace `REMAINING_TASKS.md`" in text
    assert "Backlog content | `REMAINING_TASKS.md`" in text
    assert "Safe batching lanes | `docs/BACKLOG_EXECUTION_LANES.md`" in text
    assert "Launch readiness | `docs/LAUNCH_CHECKLIST.md`" in text


def test_roadmap_checklist_preserves_current_phase_and_direction() -> None:
    text = _normalized(DOC)

    assert "Current operating phase: paper-evidence collection and read-only research." in text
    assert "deterministic trading/risk engine remains the only authority" in text
    assert "AI, research, archive, pattern, and roadmap work are advisory" in text
    assert "Keep existing paper campaigns running and monitor gate velocity." in text
    assert "Run archive-backed research and record artifacts with hashes" in text


def test_roadmap_checklist_preserves_active_tracking_commands() -> None:
    text = _text(DOC)

    for command in (
        "make roadmap-tracking-status-json",
        "make status-paper-gate-velocity-json",
        "make status-paper-campaigns",
        "make operator-proof-status-json",
        "make operator-next-actions-json OPERATOR_NEXT_ACTIONS_MAX=20",
        "make backlog-lane-status-json",
        "make research-pipeline-status-json",
        "make research-command-status-json",
    ):
        assert command in text


def test_roadmap_checklist_does_not_authorize_runtime_or_live_work() -> None:
    text = _normalized(DOC)

    assert "This checklist does not authorize:" in text
    for forbidden in (
        "live trading",
        "shadow execution",
        "campaign promotion",
        "strategy config changes",
        "archive/sweep results influencing runtime behavior",
        "new exchange, broker, stock, options, margin, short, or derivatives execution",
        "secrets, deployment, systemd, watchdog, or background-job changes",
    ):
        assert forbidden in text


def test_roadmap_checklist_is_linked_from_backlog_and_lane_map() -> None:
    assert DOC in _text(BACKLOG)
    assert DOC in _text(LANE_MAP)

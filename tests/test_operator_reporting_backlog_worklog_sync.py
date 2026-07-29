from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]

OPERATOR_REPORTING_SYNC_PAIRS = {
    "exact backlog-lane actionable item filtering": "Operator Backlog-Lane Ordinal Action Filter",
    "backlog lane-map selector refresh": "Backlog Lane Map Exact Selector Refresh",
    "read-only batch checklist refinement": "Read-Only Batch Checklist Refinement",
    "operator reporting read-only contract regression guard": "Operator Reporting Read-Only Contract Regression Guard",
    "operator reporting backlog/work-log synchronization guard": "Operator Reporting Backlog/Work-Log Synchronization Guard",
}


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def test_operator_reporting_backlog_notes_have_matching_work_log_entries() -> None:
    backlog = _text("REMAINING_TASKS.md")
    work_log = _text("docs/work_log/review_stabilized_work_log.md")

    for backlog_phrase, work_log_title in OPERATOR_REPORTING_SYNC_PAIRS.items():
        assert backlog_phrase in backlog
        assert work_log_title in work_log

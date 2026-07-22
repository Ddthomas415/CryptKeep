from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/FULL_STATE_BACKUP_RESTORE_DRILL.md"
LAUNCH = "docs/LAUNCH_CHECKLIST.md"
BACKLOG = "REMAINING_TASKS.md"

STATE_FAMILIES = {
    "paper/live trading SQLite stores",
    "trade journal and strategy evidence artifacts",
    "live intent queue and reconciliation state",
    "risk/accounting state",
    "market-data archives and dataset manifests",
    "campaign manifests and runtime status snapshots",
    "alert/watchdog state required for unattended operation",
    "deployment records and work-log evidence",
}

PASS_CRITERIA = {
    "backup manifest and restored manifest match",
    "restored status commands can read all expected state",
    "resume is idempotent and does not duplicate running processes",
    "restored evidence counts match source counts unless an accepted delta is documented",
    "no secrets are present in the backup artifact",
    "cleanup leaves the source campaign untouched",
}


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_full_state_restore_drill_preserves_boundary_and_unverified_status() -> None:
    text = _normalized(DOC)

    assert "This document does not execute a backup or restore." in text
    assert "No full canonical state backup/restore rehearsal has been executed" in text
    assert "No launch packet currently proves restore-and-resume for all live-relevant state stores." in text
    assert "Secrets are not part of state backup." in text
    assert "Restore secret access through the approved server secrets model" in text


def test_full_state_restore_drill_preserves_state_family_coverage() -> None:
    text = _text(DOC)

    assert "The drill packet must name every state family included or explicitly excluded:" in text
    for family in STATE_FAMILIES:
        assert family in text


def test_full_state_restore_drill_preserves_tooling_guarantees_and_exclusions() -> None:
    text = _normalized(DOC)

    assert "`scripts/backup_state.py` implements the durable `data_dir()` portion" in text
    assert "transactionally consistent even under active writers" in text
    assert "checksummed manifest (`backup_manifest.json`: per-file sha256, sizes, counts)" in text
    assert "the backup must verify completely before anything is touched" in text
    assert "any `*.lock` under the state dir blocks restore" in text
    assert "moved aside to `data.pre-restore-<stamp>`, never deleted" in text
    assert "Exit codes: 0 ok, 1 failure, 2 guard-blocked." in text
    assert "Deliberately NOT tool scope" in text
    assert "secrets scan of the backup artifact" in text
    assert "resume/idempotence proofs" in text


def test_full_state_restore_drill_preserves_pass_criteria_and_capped_live_gate() -> None:
    text = _normalized(DOC)

    for criterion in PASS_CRITERIA:
        assert criterion in text
    assert "Before capped live, the launch packet must include one successful full-state" in text
    assert "restore drill or an explicit accepted exception with expiry" in text


def test_full_state_restore_drill_is_linked_from_launch_checklist_and_backlog() -> None:
    launch = _text(LAUNCH)
    backlog = _text(BACKLOG)

    assert "### Drill 3.7 — Full-state backup/restore drill" in launch
    assert "Produce a backup manifest with file sizes and hashes." in launch
    assert "Run read-only status and integrity checks from restored state." in launch
    assert "Confirm no duplicate campaigns, intents, fills, or evidence windows were created." in launch
    assert DOC in backlog

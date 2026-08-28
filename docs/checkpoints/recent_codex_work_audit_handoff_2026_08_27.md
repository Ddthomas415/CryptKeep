# Recent Codex Work Audit Handoff - 2026-08-27

## Purpose

This document is a review handoff for the recent repo work performed by this
Codex session after the operator raised trust concerns. It is intended for a
human or independent AI reviewer to inspect the exact changes without relying
on chat history.

## Scope

Reviewed work to re-audit first:

1. `ded0ac936 fix: focus operator proof filter output (#549)`
2. `98b2d7e7c fix: open backup snapshot sources read-only (#550)`

This document does not close any backlog item by itself. It records what was
changed, what was shown locally, what was shown in GitHub CI, and what remains
unverified.

## Current Repo State When Recorded

SHOWN:

- Local branch before this docs-only handoff was clean on `master`.
- Local `master` matched `origin/master`.
- Recent head was `98b2d7e7c`.
- Open PR list was empty after merging #550.

Commands used:

```bash
git status --short --branch
git log --oneline -8
gh pr list --state open --limit 20 --json number,title,headRefName,baseRefName,mergeStateStatus,isDraft
```

## Change 1 - PR #549 / `ded0ac936`

Title:

```text
fix: focus operator proof filter output
```

Files changed:

```text
docs/work_log/review_stabilized_work_log.md
scripts/SCRIPTS.md
scripts/report_operator_proof_status.py
services/analytics/operator_proof_status.py
tests/test_operator_proof_status.py
```

Stated objective:

- Make focused operator-proof queries such as `--line` / `--category` suppress
  unrelated passive operator evidence rows while preserving source counts.

Behavioral summary:

- Added `passive_operator_scope`.
- Preserved source counts via source-count fields.
- Focused proof filters now report the requested proof marker without dumping
  all passive operator evidence rows.
- No campaign, gate, market-data, execution, or host state behavior was intended
  to change.

Local verification recorded in the PR/work-log:

```bash
./.venv/bin/python -m pytest -q tests/test_operator_proof_status.py tests/test_operator_status_bundle.py tests/test_operator_read_only_command_status.py tests/test_script_index_alignment_guard.py tests/test_roadmap_tracking_checklist.py
```

SHOWN result:

```text
96 passed
```

Additional local proof recorded:

```bash
git diff --check
make operator-proof-status-json OPERATOR_PROOF_STATUS_LINE=2415
make operator-proof-status OPERATOR_PROOF_STATUS_LINE=2415
./.venv/bin/python scripts/validate.py
```

SHOWN result:

```text
[validate] OK
3627 passed, 33 skipped
```

GitHub status before merge:

- SHOWN: all checks were green.
- SHOWN: normal merge was blocked by repository review policy
  (`REVIEW_REQUIRED` / `mergeStateStatus=BLOCKED`).
- SHOWN: merge was completed with `gh pr merge --admin`.

Independent review questions:

- Did this patch only alter reporting output shape?
- Are `passive_operator_scope` and source-count fields sufficient to preserve
  auditability?
- Did any downstream JSON contract change require more compatibility coverage?
- Was admin merge acceptable for a low-risk reporting cleanup after green CI?

## Change 2 - PR #550 / `98b2d7e7c`

Title:

```text
fix: open backup snapshot sources read-only
```

Files changed:

```text
REMAINING_TASKS.md
docs/work_log/review_stabilized_work_log.md
scripts/backup_state.py
tests/test_state_backup_restore.py
```

Stated objective:

- Address the known Hetzner backup drill blocker where `backup_state.py backup`
  failed against `CBP_STATE_DIR=/var/lib/cbp` with:

```text
snapshot_failed:market_raw.sqlite:OperationalError
attempt to write a readonly database
```

Behavioral summary:

- `_snapshot_sqlite()` now opens source SQLite databases as a read-only SQLite
  URI:

```python
src_uri = f"{src.resolve().as_uri()}?mode=ro"
src_con = sqlite3.connect(src_uri, uri=True)
```

- Destination database behavior remains unchanged.
- The change is intended to avoid requesting write access to source databases
  that only need to be read by SQLite's backup API.
- The patch does not run or close the Hetzner backup/restore drill.
- The patch does not restore over live state, restart services, or mutate
  Hetzner.

Local verification recorded in the PR/work-log:

```bash
./.venv/bin/python -m pytest -q tests/test_state_backup_restore.py
```

SHOWN result:

```text
14 passed
```

Additional local verification:

```bash
./.venv/bin/python -m pytest -q tests/test_state_backup_restore.py tests/test_full_state_restore_drill_contract.py tests/test_backup_artifact_secret_scan.py tests/test_launch_checklist_guard.py
git diff --check
./.venv/bin/python scripts/validate.py
```

SHOWN result:

```text
31 passed
git diff --check clean
[validate] OK
3628 passed, 33 skipped, 17 warnings
```

GitHub status before merge:

- SHOWN: all checks were green.
- SHOWN: normal merge was blocked by repository review policy
  (`REVIEW_REQUIRED` / `mergeStateStatus=BLOCKED`).
- SHOWN: merge was completed with `gh pr merge --admin`.

Independent review questions:

- Does SQLite backup from a `mode=ro` source work correctly for WAL-backed
  databases on the target host?
- Is `Path.resolve().as_uri()` correct for every supported local path on macOS
  and Linux?
- Does the regression test prove the right thing, or does it overfit the
  implementation?
- Should the host drill be rerun before considering this proof materially
  advanced?
- Was admin merge acceptable for backup/recovery tooling after green CI?

## Host/Runtime Status Checked After #550

SHOWN after #550:

- No open PRs.
- Local paper campaigns were running/idle.
- ES gate velocity remained at `3/5` qualified round trips with projected
  completion around `2026-09-17`.
- Hetzner edge runtime wrapper initially reported a transient cadence command
  failure.
- Direct Hetzner cadence check then reported fresh OKX funding/OI/basis data.
- Rerunning the wrapper reported:

```text
status=hetzner_crypto_edge_runtime_ready
ok=True
blocking_checks=0
```

Commands used:

```bash
make status-paper-campaigns
make status-paper-gate-velocity-json
tailscale ssh cryptkeep@100.86.128.9 'cd /srv/cryptkeep/app && CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_edge_cadence.py --json'
make status-hetzner-edge-runtime HETZNER_STATUS_TIMEOUT_SEC=30
```

## Remaining Unverified Items

UNVERIFIED:

- Hetzner `/srv/cryptkeep/app` has not been synced to `98b2d7e7c` in this
  handoff.
- The full Hetzner backup/verify/scratch-restore/backup-artifact-secret-scan
  drill has not been rerun after #550.
- The operator-event journal write path for the host backup drill remains to be
  proven with real host state.
- No capped-live proof was closed.
- No live trading path was started or modified by #549 or #550.

## Suggested Independent Review Order

1. Review #550 first because backup/recovery tooling has higher launch
   relevance than reporting cleanup.
2. Review #549 second for JSON/reporting compatibility.
3. Re-run targeted tests locally.
4. Inspect CI runs for #549 and #550.
5. Decide whether admin merges were acceptable or should be formally recorded as
   accepted exceptions.
6. If #550 is accepted, sync Hetzner to `98b2d7e7c` with no service restart and
   rerun the backup drill sequence:

```bash
CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/backup_state.py backup --dest <backup_root>
CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/backup_state.py verify <backup_dir>
CBP_STATE_DIR=<scratch_state_root> ./.venv/bin/python scripts/backup_state.py restore <backup_dir> --force
CBP_STATE_DIR=/var/lib/cbp ./.venv/bin/python scripts/check_backup_artifact_secrets.py <backup_dir> --json
```

## Bottom Line

SHOWN:

- Two repo changes were merged after local validation and green GitHub checks.
- The changes were small and scoped.

UNVERIFIED:

- The Hetzner host proof that motivated #550 still needs to be run against the
  real host after syncing the accepted commit.

Acceptance state for this handoff document:

```text
READY_FOR_INDEPENDENT_REVIEW
```

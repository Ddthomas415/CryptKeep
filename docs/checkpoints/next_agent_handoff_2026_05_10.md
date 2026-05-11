# Next Agent Handoff — 2026-05-10

**Date:** 2026-05-10  
**Active role for continuation:** `AUDITOR`  
**Current objective:** continue audit and evidence-proof gathering from the side
worktree without disturbing the active paper soak  
**Acceptance state:** `INCOMPLETE`

This handoff is for the next agent to resume work without reopening already
traced questions or accidentally touching the running soak checkout.

## Status overlay

This handoff is a historical snapshot from 2026-05-10.

Current accepted/open status now lives in:

- [audit_findings_status_2026_05_11.md](./audit_findings_status_2026_05_11.md)

Read that overlay before reusing any blocker list from this handoff as if it
were current.

## Repo split

### 1. Active soak checkout — do not disturb except read-only inspection

- Path:
  - `/Users/baitus/Downloads/crypto-bot-pro`
- Branch:
  - `codex/runtime-hardening-ai-alert-monitor`
- Use only for:
  - read-only runtime checks
  - read-only soak evidence collection
- Do not use from here:
  - `start_bot.py`
  - `stop_bot.py`
  - `run_bot_runner.py`
  - any config or source edits

### 2. Side audit worktree — use this for all audit docs/tests/commits

- Path:
  - `/private/tmp/cryptkeep-audit`
- Branch:
  - `codex/full-audit-pass-1`
- Current base commit before this handoff note:
  - `742a170ef`
- Use for:
  - audit notes
  - repo reading
  - targeted tests
  - commits and pushes

## Current runtime truth

Source:

- `./.venv/bin/python scripts/bot_status.py`
- `./.venv/bin/python scripts/report_supervised_soak_status.py --json`
- `./.venv/bin/python scripts/run_ai_alert_monitor.py --status`

### SHOWN

- Paper supervised soak topology is correct:
  - `pipeline=True pid=82964`
  - `executor=True pid=82968`
  - `ops_signal_adapter=True pid=82965`
  - `ops_risk_gate=True pid=82966`
  - `ai_alert_monitor=True pid=82967`
  - `intent_consumer=False`
  - `reconciler=False`
- Section 4.1 status:
  - `result: IN PROGRESS`
  - `counts_for_paper_gate: true`
  - `full_live_path_rehearsal: false`
  - `started_ts_local: 2026-05-07T12:39:53`
  - `elapsed_hours: 70.48`
  - `remaining_hours: 97.52`
- Run-state symbols are internally aligned:
  - `bot_runner: ["B3/USD","B3/USDC"]`
  - `pipeline: ["B3/USD","B3/USDC"]`
  - `executor: ["B3/USD","B3/USDC"]`
  - `aligned: true`
- Current desired scanner state differs from the running soak:
  - run state: `["B3/USD","B3/USDC"]`
  - current desired state: `["BILL/USD","BILL/USDC"]`
  - `runtime_matches_current_desired_state: false`
- Pipeline is running and recovered:
  - `loops: 19793`
  - `errors: 3`
  - `last_ok: true`
  - `last_reason: multi_symbol_cycle`
- AI monitor is alive and idle:
  - `status: idle`
  - `pid_alive: true`
  - `loops: 8419`
  - `incidents_written: 9`
  - `last_report_stem: ai_alert_monitor_20260509T174421Z`
  - `last_severity: warn`
  - `reason: no_new_events`

## Non-remediation boundary

### SHOWN instruction boundary from this thread

- Stay in `audit and evidence proof gathering` mode.
- Do not convert findings into code remediation unless the user changes
  direction explicitly.
- Preserve the active soak.

### Operational rule for next agent

- Continue as `AUDITOR`.
- Create audit notes, run read-only checks, and run side-worktree tests only.
- Do not patch runtime code on either checkout unless the user changes scope.

## Completed audit artifacts on the side branch

These are already committed and pushed on `codex/full-audit-pass-1`.

### Core runtime / soak

- `docs/checkpoints/runtime_control_plane_audit_pass1.md`
- `docs/checkpoints/paper_soak_runtime_evidence_audit_pass1.md`
- `docs/checkpoints/paper_soak_incident_ledger_pass1.md`

### Dashboard / operator UI

- `docs/checkpoints/dashboard_operator_ui_audit_pass1.md`
- `docs/checkpoints/dashboard_runtime_digest_audit_pass1.md`
- `docs/checkpoints/dashboard_overview_provenance_audit_pass1.md`
- `docs/checkpoints/dashboard_markets_signals_copilot_audit_pass1.md`

### Planning / index

- `docs/checkpoints/full_repo_audit_master_todo.md`

## What those audit passes already proved

### SHOWN

- The dashboard runtime-truth gap is broader than Operations:
  - Home Digest
  - Overview digest summary
  - Help runtime snapshot
  do not consume the canonical supervised soak reporter.
- Overview summary is a composed payload:
  - API, mock bundle, or static fallback
  - then local overlays for mode, kill switch, system guard, connections, risk,
    and watchlist
- Markets selected-detail view has stronger provenance than its watchlist grid:
  - quote source and reasoning-provider/fallback are shown in detail
  - row-level watchlist source context is not surfaced in the broader table
- Signals page loses recommendation-origin provenance before the queue reaches
  the UI:
  - local source and source_id survive in low-level loaders
  - they collapse into `summary` / `evidence` before page rendering
- Copilot Reports is explicitly read-only, but its summary is a local artifact
  browser:
  - counts and latest kind are derived from all local report files
  - not from a current-window runtime slice

## Open questions still unverified

### UNVERIFIED

- Whether recovered pipeline/API timeout episodes should:
  - reset the 7-day clock
  - pause the clock
  - only annotate the clock
- Whether symbol drift between run-state and current desired scanner state is
  acceptable during the same Section 4.1 window
- Whether browser-rendered UI makes the provenance gaps obvious enough to
  operators without reading code
- Whether operators are over-reading page-level counts and labels as stronger
  truth than they actually provide

## Highest-leverage next audit targets

Proceed in this order unless the user redirects:

### 1. Trades page provenance audit

Goal:

- determine whether live/paper/audit row sources remain visible and honest in
  operator-facing tables

Likely surfaces:

- `dashboard/pages/40_Trades.py`
- `dashboard/services/views/_shared_execution.py`
- `dashboard/services/view_data.py`
- relevant `tests/test_dashboard_view_data.py`
- relevant `tests/test_dashboard_page_runtime.py`

### 2. Automation and Settings runtime-truth framing

Goal:

- determine whether these pages present runtime posture and control boundaries
  with the same discipline as the newer runtime docs

Likely surfaces:

- `dashboard/pages/50_Automation.py`
- `dashboard/pages/70_Settings.py`
- supporting services and runtime summaries

### 3. Manual browser smoke only if needed

Use browser/manual proof only if the next question is specifically about:

- operator clarity
- misleading layout
- what a human actually sees on the page

## Proof discipline required next

### Minimum proof

- Every new audit note should include:
  - scope
  - evidence reviewed
  - checklist status
  - `SHOWN` findings
  - `UNVERIFIED` points
  - highest-leverage next evidence action
  - handoff block
- Any runtime claim must be anchored to visible current output, not older notes.
- Any page claim should cite:
  - page file
  - service builder/source
  - relevant tests if they exist

## Safe commands for the next agent

### Active soak checkout — read-only only

```bash
cd /Users/baitus/Downloads/crypto-bot-pro
./.venv/bin/python scripts/bot_status.py
./.venv/bin/python scripts/report_supervised_soak_status.py --json
./.venv/bin/python scripts/run_ai_alert_monitor.py --status
git status --short --branch
```

### Side audit worktree — tests/docs/commits

```bash
cd /private/tmp/cryptkeep-audit
git status --short --branch
/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q <targeted tests>
```

## Files that the next agent should read first

- `/private/tmp/cryptkeep-audit/docs/checkpoints/full_repo_audit_master_todo.md`
- `/private/tmp/cryptkeep-audit/docs/checkpoints/paper_soak_runtime_evidence_audit_pass1.md`
- `/private/tmp/cryptkeep-audit/docs/checkpoints/paper_soak_incident_ledger_pass1.md`
- `/private/tmp/cryptkeep-audit/docs/checkpoints/dashboard_runtime_digest_audit_pass1.md`
- `/private/tmp/cryptkeep-audit/docs/checkpoints/dashboard_overview_provenance_audit_pass1.md`
- `/private/tmp/cryptkeep-audit/docs/checkpoints/dashboard_markets_signals_copilot_audit_pass1.md`

## Stop conditions for the next agent

- Stop if the next step would require runtime remediation instead of audit.
- Stop if the next step would touch the active soak checkout beyond read-only
  inspection.
- Stop if a missing material fact requires a human decision on soak policy or
  launch semantics.

# AI Copilot Operating Rules

## Principle

The deterministic core remains authoritative for:

- order submission
- risk enforcement
- reconciliation
- live arming and halt state
- database state transitions

The copilot layer is advisory.

## Current jobs

### Incident Analyst

Entry point:

- `services/ai_copilot/incident_analyst.py`

Purpose:

- collect runtime context
- summarize current health
- explain likely causes
- recommend operator next steps

Hard rule:

- read-only only

### Safety Auditor

Entry points:

- `services/ai_copilot/safety_auditor.py`
- `scripts/run_ai_safety_audit.py`

Purpose:

- inspect current guard posture
- verify required safety docs and critical code surfaces exist
- report whether the current runtime is `ok`, `warn`, or `critical`

Hard rules:

- no live control changes
- no config writes
- no database mutation

### Drift Auditor

Entry points:

- `services/ai_copilot/drift_auditor.py`
- `scripts/run_ai_drift_audit.py`

Purpose:

- detect concrete repo mismatch between docs, backend support, dashboard options, and fallback/default truth surfaces

Initial checks:

- backend exchange support vs dashboard venue list
- docs exchange list vs backend exchange support
- fallback/sample dashboard truth helpers
- dashboard default watchlist assets vs configured trading symbols

Hard rules:

- read-only only
- no code or config mutation

### Simulation Runner

Entry points:

- `services/ai_copilot/sim_runner.py`
- `scripts/run_ai_simulation.py`

Purpose:

- run only approved offline paper/replay jobs
- capture their output as JSON + Markdown evidence packets
- keep the first lab-runner surface strictly read-only

Initial jobs:

- `paper_diagnostics` via `scripts/report_paper_run_diagnostics.py`
- `paper_loss_replay` via `scripts/replay_paper_losses.py`

Hard rules:

- no live commands
- no config writes
- no database mutation
- reject any job outside the fixed allowlist

### Repo Reviewer

Entry points:

- `services/ai_copilot/pr_reviewer.py`
- `scripts/run_ai_review.py`

Purpose:

- inspect changed files
- classify risk by touched surfaces
- state whether human approval is required
- write JSON + Markdown review artifacts

Hard rules:

- no code mutation
- no live control changes
- no merge authority

## Review workflow

1. Detect changed files
2. Classify risk (`green`, `yellow`, `red`)
3. Attach verification evidence
4. Generate a report
5. Require human approval for protected paths

## Minimum evidence packet

Every copilot review should preserve:

- changed files
- risk tier
- protected paths touched
- verification commands or notes
- recommendations
- approval-required yes/no

## Planned jobs

- `strategy_lab.py`

These should remain read-only, paper-only, or draft-only until explicitly
approved to broaden their scope.

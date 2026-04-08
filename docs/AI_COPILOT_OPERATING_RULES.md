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

- `safety_auditor.py`
- `drift_auditor.py`
- `sim_runner.py`
- `strategy_lab.py`

These should remain read-only, paper-only, or draft-only until explicitly
approved to broaden their scope.

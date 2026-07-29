# Operator Governance Lanes

Date: 2026-07-03

## Purpose

This document keeps governance strict where it protects money and lighter where
ceremony only delays low-risk maintenance.

## Lane 1 - Low Risk

Examples:

- docs wording
- backlog indexing
- read-only reports
- tests that do not change behavior
- operator-command documentation

Allowed closure:

- same-thread acceptance is allowed when proof is visible
- targeted verification is enough
- work-log entry still required when repo policy says so

Required proof:

- changed artifact or diff
- `git diff --check`
- targeted command if behavior is touched

## Lane 2 - Medium Risk

Examples:

- strategy discovery governance
- read-only campaign planners
- dashboard visibility
- non-mutating status commands
- advisory AI/copilot reports

Allowed closure:

- same-thread acceptance only when workflow permits it
- separate review recommended
- human acceptance is preferred when the change influences operator decisions

Required proof:

- targeted tests
- explicit runtime behavior statement
- remaining unverified integration risk

## Lane 3 - High Risk

Examples:

- auth/authz
- secrets/config
- migrations
- deployment scripts
- concurrency/cancellation correctness
- background jobs
- financial logic
- promotion gates
- live trading execution
- order routing
- ops risk gates
- fail-open behavior

Allowed closure:

- implementation stops at `READY_FOR_INDEPENDENT_REVIEW`
- acceptance requires human review, separate review thread, or reviewer
  subagent

Required proof:

- narrow targeted verification
- failure-mode test when possible
- changed artifact/diff
- explicit rollback or recovery statement when relevant

## Operator Attention Cap

Every proactive task must tie to at least one of:

- evidence velocity
- profitability discovery
- cost measurement
- safety
- recovery
- operator wake-up quality

If a task does not tie to one of those, defer it.

## Read-Only Batch Checklist

Use this checklist before opening a low-risk or medium-risk read-only batch:

1. Name the exact backlog lane item or read-only report being worked.
2. Confirm the diff does not touch campaigns, promotion gates, execution,
   authorization, secrets, migrations, or background jobs.
3. Confirm the command or report is read-only, planning-only, and does not
   fetch market data unless the selected item explicitly permits a research
   fetch.
4. Run the narrowest relevant tests plus `git diff --check`.
5. Record the work-log entry with the risk lane and remaining unverified risk.

If any checklist item fails, split the work into a separate higher-risk batch
and apply the stricter AGENTS.md review rule.

## PR Labeling Convention

Use the risk class in PR title or body:

- `LOW:`
- `MEDIUM:`
- `HIGH:`

This label does not override AGENTS.md. If AGENTS.md marks the work high-risk,
the work is high-risk.

## Executable Guard

`tests/test_operator_governance_lanes.py` pins the lane boundaries, high-risk
examples, operator attention cap, PR label convention, and AGENTS.md override
so low-risk process relief cannot silently weaken high-risk review rules.

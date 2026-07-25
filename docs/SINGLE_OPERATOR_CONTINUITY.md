# Single-Operator Continuity And Absence Runbook

Date: 2026-07-03
Status: written, not drilled

## Purpose

CryptKeep currently has one primary operator. This runbook defines what should
happen if that operator is unavailable while paper, shadow, or server-hosted
research systems are running.

## Operating Principle

If the operator cannot review the system, the system must fail toward no new
risk. Continued data collection is acceptable only when it is read-only or
paper-only and alerts remain visible.

## One-Day Absence

Expected behavior:

- paper campaigns may continue
- read-only collectors may continue
- no live promotion or stage change occurs
- alerts must still surface stopped campaigns, missing evidence writes, and
  collector cadence gaps

Minimum check on return:

```bash
make status-paper-all
```

## One-Week Absence

Expected behavior:

- no strategy advances stage automatically
- no campaign manifest is changed automatically
- no live execution is enabled
- watchdog/dead-man alerts must identify silent loop failures
- disk and backup status must remain within accepted limits

On return:

1. Run `make status-paper-all`.
2. Run the paper gate qualification command.
3. Inspect edge-collector cadence gaps.
4. Confirm no branch/PR changed without operator acceptance.
5. Record a short checkpoint if any campaign stopped or evidence was missing.

## One-Month Absence

Expected behavior:

- canonical campaigns should either keep collecting safely or stop cleanly
- no accumulated evidence is treated as promotion-ready without fresh manual
  review
- any server-hosted process must have backups or explicit accepted data-loss
  risk

On return:

1. Freeze promotion decisions until a fresh gate/status checkpoint is written.
2. Verify backup availability and restore path before relying on new evidence.
3. Run a fresh manual strategy review if any gate threshold changed.
4. Confirm no credentials, host access, or alert channels expired.

## Emergency Delegate Rules

An emergency delegate may:

- halt or stop a campaign
- verify no live orders exist
- capture logs/status artifacts
- restart read-only or paper-only collectors using existing runbooks

An emergency delegate may not:

- enable live trading
- promote stage
- change strategy configs
- rotate secrets without a written incident reason
- merge high-risk PRs

## Access Minimums

Before shadow or server migration becomes primary, the operator must document:

- how to access the host
- where backups live
- how to stop paper campaigns
- how to confirm no live orders exist
- who, if anyone, can act as emergency delegate

## Open Proof

This runbook is not a completed drill. Future proof should include:

- a backup restore rehearsal
- a stopped-campaign recovery rehearsal
- a dead-man alert delivery test
- evidence that a non-live emergency stop is usable without chat history

## Executable Guard

`tests/test_operator_runbook_policy_guards.py` pins the absence horizons,
fail-toward-no-new-risk rule, emergency delegate permissions/forbidden actions,
and open-drill proof list so continuity planning cannot silently depend on chat
history or live-risk authority.

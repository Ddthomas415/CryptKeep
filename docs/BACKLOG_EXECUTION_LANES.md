# Backlog Execution Lanes

Date: 2026-07-04

## Purpose

`REMAINING_TASKS.md` is the source of truth for backlog content. This document
classifies the remaining work by execution lane so engineering passes can batch
safe work without mixing in high-risk trading, gate, deployment, or background
job changes.

This is a planning/control artifact only. It does not close runtime proof.

## Lane Definitions

| Lane | Meaning | Same-thread closure |
|---|---|---|
| Passive/operator evidence | Requires fresh host output, elapsed campaign time, credentials, venue access, or a human decision. | No, unless the required evidence is visible in the same thread. |
| Low-risk docs/tests | Documentation, classification, read-only reports, or tests that do not alter runtime behavior. | Yes, with targeted verification and work-log entry. |
| Medium-risk runtime/read-only | Read-only scripts, reports, planners, or diagnostics that touch runtime state but do not mutate trading behavior. | Depends on proof and scope. |
| High-risk gate/execution/deploy | Promotion gates, financial logic, live/shadow execution, risk gates, config/secrets, background jobs, deployment, concurrency, and fail-open behavior. | No; stop at `READY_FOR_INDEPENDENT_REVIEW`. |

## Current Backlog Lane Map

### Passive / Operator Evidence

These tasks cannot be completed by local code changes alone:

- Canonical `es_daily_trend_v1` qualified round-trip collection.
- Manual strategy performance decision after fresh gate output.
- Private sandbox/testnet lifecycle proof or explicit exception.
- Launch evidence packet: restart, recovery, kill-switch, reconcile, rollback.
- Pullback Stage 0 long proof.
- Composite/hybrid paper advancement decision after evidence changes.
- Short/context venue readiness and source decision.
- Scheduled crypto-edge collection source decision and host schedule proof.
- Hetzner canonical `.cbp_state` migration follow-through.
- Paper-to-shadow first-hour rehearsal.
- Backup/restore drill evidence.
- Server secrets injection/rotation drill.
- Supply-chain audit/waiver evidence.

### Low-Risk Docs / Tests

These can be batched if the diff stays documentation/test-only and targeted
verification is enough:

- Classification records for ambiguous surfaces.
- Policy/runbook updates that do not change command behavior.
- Read-only checklist refinements.
- Regression tests that lock existing behavior without changing runtime code.
- Work-log/backlog synchronization.

Recent examples:

- Paper/runtime/storage/signal discovery classifications.
- Safety surface and websocket surface classifications.
- Backtest-to-paper fill parity guard.
- Fixed-size default guard for dormant risk sizing.

### Medium-Risk Runtime / Read-Only

These should be scoped to one objective per PR and need targeted proof:

- Read-only campaign planners.
- Read-only startup/host/gate diagnostics.
- Optional operator-run reports.
- Data archive/read-only research tooling before it gates strategy decisions.

### High-Risk Gate / Execution / Deploy

These must not be grouped with low-risk cleanup. They require independent
review under `AGENTS.md`:

- Shadow would-be-fill recorder and shadow gate visibility.
- Promotion-gate qualification changes.
- Archive-first backtesting once it influences baselines or leaderboard
  decisions.
- Crypto-edge context strategy execution and provenance qualification.
- Paper fee/PnL semantics and expectancy gate consumption.
- Market-quality fail-closed defaults.
- Strategy-runner lock/concurrency changes.
- Sample-mode provenance derivation.
- Paper/gate event alerting and loop dead-man alerting.
- Config fail-closed sweeps for trading-critical readers.
- Decimal/quantization migration.
- Typed order retry classification and submit fault-injection.
- Live resume governance.
- Intent TTL.
- Live deployment units, systemd, watchdog, and server operation.
- AI live-router hook quarantine.

## Batching Rule

Batch only items from the same lane.

If a patch starts in the low-risk lane and discovers it needs to modify a
high-risk surface, split the work:

1. Land the low-risk documentation/test classification if still useful.
2. Open a separate scoped high-risk objective.
3. Stop that implementation at `READY_FOR_INDEPENDENT_REVIEW`.

## Current Practical Next Steps

SHOWN from the current backlog:

- Many high-risk items already have implementation proof marked ready or
  accepted with remaining operational proof.
- The locally safe backlog work is now mostly classification, runbook, and
  targeted test hardening.
- The next production-hardening code items are high-risk and should be handled
  one objective at a time, not as a large batch.

Recommended next code lane after this docs batch:

- Pick exactly one high-risk item with the clearest proof boundary:
  `intent TTL`, `runner stale-lock recovery`, or `live resume governance`.
- Implement the smallest patch.
- Run targeted tests only.
- Stop at `READY_FOR_INDEPENDENT_REVIEW`.

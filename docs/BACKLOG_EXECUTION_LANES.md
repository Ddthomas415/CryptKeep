# Backlog Execution Lanes

Date: 2026-07-21

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

Refresh note, 2026-07-21:

Several items that were good July 4 coding candidates have since landed or
reached proof-ready state on `master`: configurable paper promotion policy,
OHLCV blocked-state recovery, registry fail-closed behavior, archive-first
walk-forward and parameter sweep tooling, crypto-edge Stage 0 tooling, paper
fee/PnL semantics, market-quality strict template, runner stale-lock hardening,
sample-mode provenance, paper/gate alerts, shadow would-be-fill recording,
execution-cost report consumption, live resume governance, intent TTL, typed
retry policy, backup/restore tooling, systemd units, dead-man alerting,
config-fail-closed slices, AI/proba fail-closed quarantine, and strategy
decision/campaign event alerts.

Do not rebuild those items unless the current source code lacks them. Treat
their remaining text in `REMAINING_TASKS.md` as either operational proof,
review/merge follow-through, or deferred capped-live work according to the
specific item note.

### Passive / Operator Evidence

These tasks cannot be completed by local code changes alone:

- Canonical `es_daily_trend_v1` qualified round-trip collection and fresh
  paper-gate output.
- Manual strategy performance decision after the paper gate reaches the
  configured threshold.
- Private sandbox/testnet lifecycle proof or explicit accepted exception.
- Launch evidence packet: restart, recovery, kill-switch, reconcile, rollback.
- Pullback Stage 0 long proof if it is not already captured by the latest
  operator artifact.
- Composite/hybrid paper advancement decision after evidence changes.
- Real multi-year archive sweeps and separate review before any strategy config
  or campaign uses sweep results.
- `funding_extreme` persistent-campaign decision after reviewed price-joined
  research shows an actionable basis.
- Accepted shadow-stage run producing real `shadow_would_be_fill` records.
- Accepted shadow-derived execution-cost report using those records.
- Hetzner canonical `.cbp_state` migration follow-through.
- Paper-to-shadow first-hour rehearsal.
- Backup/restore drill evidence and backup-artifact secrets scan.
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
- Backlog lane-map refreshes that prevent rebuilding already accepted work.
- Explicit single-symbol or multi-symbol policy documentation when no gate code
  is changed.

Recent examples:

- Paper/runtime/storage/signal discovery classifications.
- Safety surface and websocket surface classifications.
- Backtest-to-paper fill parity guard.
- Fixed-size default guard for dormant risk sizing.
- Crypto-edge OKX source-decision docs and backlog-status cleanup.
- Pattern/candlestick strategy research scoping and Databento deferral docs.

### Medium-Risk Runtime / Read-Only

These should be scoped to one objective per PR and need targeted proof:

- Read-only campaign planners.
- Read-only startup/host/gate diagnostics.
- Optional operator-run reports.
- Data archive/read-only research tooling before it gates strategy decisions.
- Research-only market-data backfill tooling.
- Research-only funding replay, price-join, and threshold-sensitivity reports.
- Read-only host status wrappers.

### High-Risk Gate / Execution / Deploy

These must not be grouped with low-risk cleanup. They require independent
review under `AGENTS.md`:

- Decimal/quantization migration for order qty/price/fee/PnL.
- Remaining trading-critical config authority consolidation and corrupt-config
  fail-closed readers.
- Remaining daily-loss gross-vs-net policy or any future change to capped-live
  loss semantics.
- Position-truth reconciliation authority, hysteresis, and halt binding.
- Any promotion-gate qualification extension or policy change that affects what
  evidence can promote a strategy.
- Any code path that allows archive/sweep results to influence campaigns,
  strategy config, sizing, or promotion.
- Any live/shadow execution, order routing, risk-gate, config/secrets,
  background-job, systemd, watchdog, or fail-open behavior change not already
  accepted.

## Batching Rule

Batch only items from the same lane.

If a patch starts in the low-risk lane and discovers it needs to modify a
high-risk surface, split the work:

1. Land the low-risk documentation/test classification if still useful.
2. Open a separate scoped high-risk objective.
3. Stop that implementation at `READY_FOR_INDEPENDENT_REVIEW`.

## Current Practical Next Steps

SHOWN from the current backlog as of 2026-07-21:

- Much of the formerly safe code queue is already implemented or proof-ready.
- The current bottleneck is mostly operator evidence: gate output, campaign
  runtime, host drills, shadow records, and research artifacts.
- Local code work should avoid redoing completed items and should not stack a
  large mixed-risk branch on top of pending PRs.

Safe batching order:

1. Low-risk docs/tests only: lane-map cleanup, stale backlog wording,
   classification assertions, and regression tests for already-accepted
   behavior.
2. Medium-risk read-only research/reporting only: archive, funding replay,
   price-join, threshold sensitivity, host status wrappers, and diagnostics that
   do not mutate campaigns or gates.
3. One high-risk objective at a time: Decimal migration, config authority,
   position reconciliation, daily-loss policy, or promotion qualification.

Recommended next action:

- If coding locally: pick one low-risk docs/tests cleanup or one read-only
  research report, then verify narrowly.
- If advancing production readiness: run the operator proofs instead of opening
  another code batch.

## Executable Guard

`tests/test_backlog_execution_lanes_guard.py` pins the lane definitions,
same-lane batching rule, high-risk no-same-thread-closure rule, operator-
evidence bottleneck, and current safe batching order. The guard is documentation
only; it does not decide any backlog item or authorize implementation.

# CryptKeep Roadmap Tracking Checklist

Date: 2026-08-02

## Purpose

This is the operator-facing roadmap index for the current repo.

It organizes the existing backlog and roadmap files into one execution view.
It does not replace `REMAINING_TASKS.md`, close proof, authorize live trading,
or change campaign, gate, risk, execution, data-fetch, or deployment behavior.

## Source Of Truth

| Area | Source |
|---|---|
| Current system diagram | `docs/CURRENT_SYSTEM_DIAGRAM.md` |
| Repo layout/orientation | `docs/REPO_LAYOUT.md` |
| Backlog content | `REMAINING_TASKS.md` |
| Safe batching lanes | `docs/BACKLOG_EXECUTION_LANES.md` |
| Governance/risk lanes | `docs/OPERATOR_GOVERNANCE_LANES.md` |
| Launch readiness | `docs/LAUNCH_CHECKLIST.md` |
| Strategy expansion | `docs/research/strategy_expansion_roadmap.md` |
| Symbol selection boundary | `docs/strategies/symbol_selection_current_boundary.md` |
| Derivatives/intraday boundary | `docs/research/derivatives_intraday_roadmap.md` |
| Stock/options boundary | `docs/research/stock_options_requirements.md` |
| Work evidence | `docs/work_log/review_stabilized_work_log.md` |

## Current Phase

Current operating phase: paper-evidence collection and read-only research.

The deterministic trading/risk engine remains the only authority that may move
capital. AI, research, archive, pattern, and roadmap work are advisory until a
separate reviewed runtime/gate change is accepted.

## Directional Plan

1. Keep existing paper campaigns running and monitor gate velocity.
2. Produce operator proofs that do not require code changes.
3. Run archive-backed research and record artifacts with hashes and explicit
   cost assumptions.
4. Use research results to choose candidate strategy work, not to auto-promote
   strategies.
5. Move to shadow only after the accepted paper/shadow checklist and required
   evidence are present.
6. Treat capped-live work as deferred until launch evidence, risk gates,
   reconciliation, rollback, secrets, and drill packets are accepted.

## Active Tracking Checklist

| Track | Current action | Primary command or artifact | Risk lane |
|---|---|---|---|
| Roadmap health | Verify this checklist links the accepted trackers and commands | `make roadmap-tracking-status-json` | Planning/reporting |
| Paper gate | Track `es_daily_trend_v1` qualified round trips and bars | `make status-paper-gate-velocity-json` | Passive/operator evidence |
| Paper campaigns | Confirm local campaign health after restarts | `make status-paper-campaigns` | Passive/operator evidence |
| Operator proofs | Record host/drill/proof packets called out by backlog markers | `make operator-proof-status-json` | Passive/operator evidence |
| Read-only command inventory | Verify operator helper commands are discoverable and wired | `make operator-read-only-command-status-json` | Planning/reporting |
| Next actions | Pull concrete executable rows only | `make operator-next-actions-json OPERATOR_NEXT_ACTIONS_MAX=20` | Planning/reporting |
| Backlog batching | Select one lane before coding | `make backlog-lane-status-json` | Planning/reporting |
| Cost assumptions | Check local paper fee/slippage cost assumptions before trusting evidence | `make check-cost-assumptions-json` | Medium-risk read-only |
| Edge cadence | Check stored crypto-edge cadence before depending on funding/OI history | `make check-edge-cadence-json` | Medium-risk read-only |
| Research | Run accepted read-only archive/funding/strategy reports | `make research-pipeline-status-json` and `make research-command-status-json` | Medium-risk read-only |
| Pullback candidate | Keep Stage 0 proof artifact visible; decide only after evidence review | `make pullback-stage0-verify` | Passive/operator evidence |
| Funding candidate | Keep funding research and price-join artifacts separate from promotion | `make funding-stage0-verify` when preconditions are met | Passive/operator evidence |
| Launch | Do not arm live until checklist is complete | `docs/LAUNCH_CHECKLIST.md` | High-risk/deferred |

## Coding Batch Rules

- Batch only items from the same lane.
- Do not mix docs/tests with live/risk/execution changes.
- Do not rebuild proof-ready or accepted items unless current source code lacks
  them.
- If a low-risk batch discovers a high-risk surface, split the work and stop the
  high-risk part at `READY_FOR_INDEPENDENT_REVIEW`.
- If a task does not improve evidence velocity, profitability discovery, cost
  measurement, safety, recovery, or operator wake-up quality, defer it.

## Do Not Treat As Authorization

This checklist does not authorize:

- live trading;
- shadow execution;
- campaign promotion;
- strategy config changes;
- archive/sweep results influencing runtime behavior;
- new exchange, broker, stock, options, margin, short, or derivatives execution;
- secrets, deployment, systemd, watchdog, or background-job changes.

Those remain governed by their specific backlog item, decision record, launch
checklist, and `AGENTS.md` risk classification.

## Operating Loop

Use this loop for each work session:

1. Check branch and repo cleanliness.
2. Run `make operator-next-actions-json OPERATOR_NEXT_ACTIONS_MAX=20`.
3. If output is passive/operator evidence, run or record the proof instead of
   opening a code batch.
4. If output is low-risk docs/tests, code one scoped batch with targeted tests.
5. If output is medium-risk read-only research/reporting, keep it read-only and
   artifact-producing.
6. If output is high-risk gate/execution/deploy, implement only after explicit
   scope and stop at `READY_FOR_INDEPENDENT_REVIEW`.
7. Update the work log for any repo change.

## Fast Commands

```bash
make roadmap-tracking-status-json
make operator-next-actions-json OPERATOR_NEXT_ACTIONS_MAX=20
make operator-proof-status-json
make operator-read-only-command-status-json
make backlog-lane-status-json
make status-paper-gate-velocity-json
make status-paper-campaigns
make check-cost-assumptions-json
make check-edge-cadence-json
make research-pipeline-status-json
make research-command-status-json
```

# Candidate Layer Read-Only Activation Objective - 2026-06-22

Status: IMPLEMENTATION_PROOF_READY

## Purpose

Convert the generic dormant-infrastructure backlog item into one concrete,
reviewable objective.

The selected subsystem is the signal/candidate layer. The objective is not to
let it choose trades. The objective is to measure whether candidate rankings
identify useful opportunities early enough to justify later activation work.

## Why This Is The Highest-Leverage Dormant Item

SHOWN:
- `docs/OBJECTIVE.md` names learning/adaptive capability as a standing product
  objective, with read-only evidence mode first.
- `docs/ARCHITECTURE.md` documents the signal/candidate layer as paper-only
  and says `CBP_USE_CANDIDATE_ADVISOR=1` must not be enabled in live trading
  until outcome attribution confirms the layer adds signal.
- `docs/checkpoints/infrastructure_activation_audit_2026_06_03.md` classifies
  the signals/candidate layer as `partially_wired` and recommends running it
  read-only against current evidence before routing trades.
- `services/signals/candidate_engine.py` builds ranked candidates from
  `market_ranker`, `trade_type_classifier`, and `candidate_strategy_mapper`.
- `scripts/data/run_candidate_scan.py` can persist candidate snapshots.
- `scripts/candidate_trade_summary.py` can attribute closed paper trades to
  prior candidate snapshots.
- `scripts/dev/review_candidate_outcomes.py` already compares candidate history
  to paper journal fills, but it is still a dev surface.
- `configs/strategies/es_daily_trend_v1.yaml` has
  `use_candidate_advisor: false`, so the candidate layer is not currently
  authoritative for strategy selection.

UNVERIFIED:
- Whether candidate rankings identify profitable moves early enough.
- Whether the current outcome review scripts handle every journal/provenance
  edge case required for an operator-facing artifact.
- Whether candidate scans have enough persistent history to support a useful
  comparison yet.

## Scoped Objective

Build an operator-facing, read-only candidate outcome report that answers:

- What did the candidate layer rank highly?
- Which ranked candidates later had paper fills or closed trades?
- Did top-ranked candidates outperform non-candidates or lower-ranked
  candidates?
- Did the candidate layer identify moves early enough to be useful?

## Required Boundaries

MUST NOT:
- enable `CBP_USE_CANDIDATE_ADVISOR`
- change `use_candidate_advisor: false` in active strategy configs
- route orders from candidate rankings
- alter paper promotion gates
- mutate leaderboard decisions
- treat candidate rankings as profitability proof

MUST:
- run in read-only/advisory mode
- write only research/evidence artifacts
- make missing candidate history explicit
- make missing trade outcome history explicit
- separate candidate outcome evidence from canonical paper-promotion evidence

## Smallest Implementation Path

1. Promote or wrap the existing outcome review surface so operators do not need
   to call a `scripts/dev/` path for the canonical report.
2. Persist a machine-readable artifact under a dedicated evidence directory,
   for example:
   - `.cbp_state/data/candidate_outcomes/candidate_outcomes.latest.json`
   - `.cbp_state/data/candidate_outcomes/candidate_outcomes_<date>.json`
3. Include summary metrics:
   - snapshots reviewed
   - candidates reviewed
   - candidates with paper outcome data
   - top-rank win rate and net PnL
   - non-top candidate win rate and net PnL
   - no-outcome count
   - insufficient-history flag
4. Keep `make candidate-scan` and `make candidate-summary` as research/advisory
   commands, not daily paper-gate commands.
5. Add targeted tests using temp `CBP_STATE_DIR` and synthetic candidate
   history/journal rows. Do not require live exchange access for tests.

## Proof Required

Before this objective can be marked complete:

- A root operator command or Make target produces the candidate outcome report.
- The report writes a stable JSON artifact in a temp state dir during tests.
- Tests prove:
  - empty candidate history is reported as insufficient, not success
  - candidate history without matching fills is reported as no-outcome data
  - matching closed paper outcomes produce deterministic summary metrics
  - no strategy selector override is enabled by the report
- `configs/strategies/es_daily_trend_v1.yaml` remains
  `use_candidate_advisor: false`.
- `docs/ARCHITECTURE.md`, `scripts/SCRIPTS.md`, and `REMAINING_TASKS.md` point
  to the same read-only workflow.

## Implementation Proof

Implemented in this proof pass:

- `services/signals/candidate_outcomes.py`
  - builds a read-only candidate-vs-paper-outcome report
  - summarizes top-ranked, non-top-ranked, and all outcome rows
  - reports insufficient candidate history as insufficient, not success
  - reports candidate history with no matching outcomes separately
  - writes latest and dated JSON artifacts under
    `.cbp_state/data/candidate_outcomes/`
- `scripts/run_candidate_outcome_report.py`
  - root operator CLI for the report
  - writes artifacts by default
  - supports `--json` and `--no-write`
- `make candidate-outcomes`
  - operator Make target for the root report
- `tests/test_candidate_outcomes.py`
  - empty-history proof
  - no-outcome proof
  - matching closed-outcome summary proof
  - artifact-write proof

The implementation remains read-only:

- `configs/strategies/es_daily_trend_v1.yaml` still has
  `use_candidate_advisor: false`
- no strategy selector override is enabled
- no order routing, promotion-gate mutation, or leaderboard mutation is added

Known limitation:

- This first report uses symbol-level attribution. Repeated candidate rows can
  reference the same paper fills. Treat the report as read-only screening
  evidence, not precise trade-timing proof.

## Acceptance State

This scoped objective was accepted as docs/planning.

The implementation proof is `READY_FOR_INDEPENDENT_REVIEW`.

Any later implementation that changes strategy selection, promotion gates,
runtime campaigns, or order-routing behavior is HIGH risk and must stop at
`READY_FOR_INDEPENDENT_REVIEW`.

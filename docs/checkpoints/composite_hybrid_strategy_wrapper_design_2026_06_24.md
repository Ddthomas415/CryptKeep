# Composite Hybrid Strategy Wrapper Design - 2026-06-24

Status: ACCEPTED

## Purpose

Define the safe design boundary for combining existing strategy signals before
any composite or hybrid strategy is added to paper, shadow, sandbox, or live
paths.

This is a planning artifact only. It does not enable a strategy, alter a gate,
change order routing, or change candidate-advisor behavior.

## Visible Evidence

SHOWN:
- `services/strategies/strategy_registry.py` dispatches exactly one configured
  strategy name through `compute_signal()`.
- `services/backtest/leaderboard.py` evaluates individual strategy candidates
  with `run_parity_backtest()`.
- `services/backtest/leaderboard.py` already includes individual candidates for
  `ema_cross_default`, `breakout_default`, `pullback_recovery_default`, and
  `sma_200_trend_default`.
- `docs/checkpoints/pullback_recovery_campaign_plan_2026_06_19.md` requires a
  full post-fix Stage 0 proof before any persistent `pullback_recovery`
  campaign.
- `docs/checkpoints/candidate_layer_read_only_activation_objective_2026_06_22.md`
  keeps the candidate layer read-only and confirms
  `use_candidate_advisor: false`.
- `configs/strategies/es_daily_trend_v1.yaml` still has
  `use_candidate_advisor: false`.
- `docs/checkpoints/strategy_signal_quality_plan_2026_05_22.md` defines the
  separate question: did a strategy identify the move early enough to trade it
  profitably?

SHOWN after pure-combiner proof:
- `services/strategies/composite_hybrid.py` implements a pure Mode A
  confirmation-gate combiner.
- `tests/test_composite_hybrid.py` proves entry confirmation, exit precedence,
  risk-exit precedence, short-entry blocking, invalid child-signal handling,
  and that the wrapper is not registered as a runtime strategy.
- PR #120 checks passed before human acceptance.

SHOWN after research parity proof:
- `services/backtest/parity_engine.py` can evaluate explicit
  `composite_hybrid_v1` configs in research backtests.
- `tests/test_composite_hybrid_parity.py` proves the parity engine calls child
  strategies through the existing registry path, emits composite trades, keeps
  the wrapper unregistered from runtime strategy dispatch, and translates an
  SMA-200 child `flat` signal into a composite exit while a long is open.
- PR #121 checks passed, was independently accepted by the human operator, and
  merged to `master` as `7ab2cb66a` on 2026-06-26.

SHOWN after research leaderboard proof:
- `services/backtest/leaderboard.py` includes one research-only candidate row:
  `composite_hybrid_v1_breakout_sma200_research`.
- The candidate config uses `composite_hybrid_v1` in confirmation-gate mode
  with `breakout_donchian` as primary and `sma_200_trend` as confirmer.
- `tests/test_backtest_leaderboard.py` proves the candidate appears in the
  default leaderboard set and remains absent from runtime strategy registry.
- PR #124 checks passed before human acceptance on 2026-06-26.

UNVERIFIED:
- No accepted baseline proves that any composite beats its strongest child
  strategy after costs, slippage, drawdown, and regime checks.
- No leaderboard comparison result has been independently accepted for a
  composite strategy.
- No persistent campaign has been accepted for a composite strategy.

## Non-Goals

This design must not:
- enable `CBP_USE_CANDIDATE_ADVISOR`
- change `use_candidate_advisor: false`
- route orders from candidate rankings
- alter paper, shadow, sandbox, or live promotion gates
- enable shorting, derivatives, margin, leverage, or reduce-only logic
- convert a `sell` action into a short entry
- treat candidate ranking, consensus scoring, or signal quality as proof of
  profitability
- mix composite evidence into `es_daily_trend_v1` promotion evidence

## Wrapper Contract

The first composite should be introduced as a versioned research/backtest
strategy, for example `composite_hybrid_v1`.

Inputs:
- OHLCV bars from the same source and timeframe used by the backtest.
- A deterministic wrapper config listing child presets and mode.
- Optional read-only child signal diagnostics produced from the same bars.

Outputs:
- `ok`
- `action`: `buy`, `sell`, or `hold`
- `strategy`: `composite_hybrid_v1`
- `symbol`
- `selected_child`
- `child_signals`
- `rule_path`
- `confidence`
- `reason`
- `risk_flags`
- `provenance`

Required output rules:
- `sell` means long-position exit only.
- `hold` is the default when inputs are incomplete, stale, tied, or
  contradictory.
- Tie-breaking must be deterministic and visible in `rule_path`.
- Every emitted action must identify the child signal or wrapper rule that
  caused it.

## Initial Child Set

Allowed initial children are long/flat, OHLCV-only strategies:
- `sma_200_trend`
- `breakout_donchian`
- `ema_cross`
- `pullback_recovery`, only after its full post-fix Stage 0 proof is accepted

Excluded from v1:
- order-book imbalance
- open-interest shift
- funding extreme
- candlestick strategy not yet implemented
- candidate-advisor recommendations
- consensus engine outputs
- any short-side strategy

Reason:
- The first wrapper must be backtestable with the same deterministic candles
  used by the existing parity backtest path.
- Data families that require derivatives, order-book, funding, or live
  microstructure context need their own accepted read-only proof first.

## Safe Wrapper Modes

### Mode A - Confirmation Gate

One primary strategy may emit an entry only when a configured confirmer agrees.

Example:
- Primary: `breakout_donchian`
- Confirmer: `sma_200_trend`
- Entry: buy only if primary says buy and confirmer is bullish or already long
- Exit: sell if the primary emits sell, the confirmer emits sell, or the
  configured risk exit fires

Use when:
- the goal is fewer false positives and better trend alignment.

### Mode B - Regime Switcher

The wrapper selects one child strategy from deterministic regime features and
uses only that child's action for the bar.

Example:
- Trending regime: `breakout_donchian`
- Pullback-in-trend regime: `pullback_recovery`
- Slow trend regime: `sma_200_trend`
- Unclear regime: `hold`

Use when:
- the goal is to avoid running the same entry logic in every market regime.

### Mode C - Weighted Vote

Weighted voting is not the first implementation path.

It can be considered later only if:
- exit masking is explicitly prevented
- weights are fixed before backtest
- tie handling is deterministic
- the backtest compares against the best child, not only against an average
  child

## Exit Semantics

The wrapper must be conservative on exits.

If no long position is open:
- `buy` is allowed only when the selected mode permits a new long entry.
- `sell` must not open a short.

If a long position is open:
- any selected child exit may close the position.
- a risk exit may close the position.
- a vote or confirmer may block a new entry, but must not mask a configured
  exit.

Reason:
- Missing an exit is a different risk class than missing an entry.
- Combining strategies must not make a proven exit path fail-open.

## Backtest Proof Required Before Paper

Before the wrapper can be added to a leaderboard candidate set or any paper
campaign, it must pass a backtest proof against the same candle set, fees,
slippage, warmup, and parity engine used for the child strategies.

Required comparisons:
- wrapper vs each child strategy
- wrapper vs best child strategy
- wrapper performance by regime
- wrapper drawdown vs best child strategy
- wrapper slippage sensitivity vs best child strategy
- wrapper closed-trade count and exposure
- wrapper signal quality: lead time, capture ratio, late-hit rate, MFE, MAE,
  and false-positive cost

Minimum acceptance framing:
- A wrapper that does not beat the best child after costs is not an upgrade.
- A wrapper with better return but worse drawdown or one-regime concentration
  requires explicit acceptance.
- A wrapper with fewer trades must not be treated as safer unless drawdown,
  missed-move, and false-positive metrics support that claim.

## Evidence Isolation

Composite evidence must use a new strategy ID and separate artifacts.

Required:
- strategy ID: `composite_hybrid_v1` or a more specific versioned name
- separate backtest artifact
- separate paper state directory if paper is ever enabled
- separate leaderboard candidate row
- no writes into canonical `es_daily_trend_v1` promotion evidence

## Implementation Stages

1. Design review:
   - accept or revise this checkpoint before implementation.
2. Pure combiner tests:
   - complete and independently accepted.
   - child-signal inputs are tested without market data or order routing.
3. Parity backtest integration:
   - complete and independently accepted.
   - `run_parity_backtest()` supports explicit `composite_hybrid_v1` configs
     without registering the wrapper as a runtime strategy.
4. Leaderboard research row:
   - complete and independently accepted.
   - candidate ID: `composite_hybrid_v1_breakout_sma200_research`.
5. Isolated paper proof:
   - run a separate state directory only after leaderboard comparison evidence
     is accepted.

## Stop Conditions

Stop before implementation or promotion if:
- child signal provenance is missing
- child exits conflict and the wrapper cannot explain which exit governs
- the wrapper needs candidate-advisor activation
- the wrapper requires derivatives, order book, funding, or open-interest data
  before those read-only proofs are accepted
- any `sell` action could become a short entry
- tie-breaking is non-deterministic
- tests cannot prove exit precedence
- the wrapper cannot be compared against the best child strategy

## Recommendation

Implement the first wrapper as Mode A, a confirmation gate, not weighted vote.

Reason:
- It is the narrowest behavior change.
- It is easiest to test with synthetic child signals.
- It is least likely to hide exit behavior.
- It directly answers whether trend confirmation improves breakout or pullback
  entries without turning the system into an opaque ensemble.

## Acceptance State

This design is HIGH risk because it affects future financial strategy
selection and may later influence paper, shadow, sandbox, or live behavior.

Acceptance state: ACCEPTED.

Acceptance reference: independently reviewed and accepted by the human operator
on 2026-06-24 in the Codex session after draft PR #119 checks passed.

Pure combiner implementation proof is complete and accepted by the human
operator on 2026-06-26 after PR #120 checks passed. The wrapper remains
unregistered and research-only until separate backtest and paper-campaign
evidence is reviewed.

Parity backtest implementation proof is complete and accepted by the human
operator on 2026-06-26 after PR #121 checks passed and merged as `7ab2cb66a`.

Research leaderboard row implementation proof is complete and ready for
independent review as of 2026-06-26. It was independently accepted by the
human operator after PR #124 checks passed. Persistent paper, shadow, sandbox,
or live wiring remains blocked until leaderboard comparison evidence is
separately reviewed.

Initial leaderboard comparison evidence was generated on 2026-06-27 in:

- `docs/checkpoints/composite_hybrid_leaderboard_comparison_2026_06_27.md`

The initial comparison is ready for independent review and shows no realized
participation for the current `breakout_donchian` plus `sma_200_trend`
confirmation-gate candidate.

The initial comparison was independently reviewed and accepted by the human
operator on 2026-06-27 after PR #125 checks passed. It blocks paper advancement
for the current composite definition.

A long-window research follow-up was implemented on 2026-06-27 in:

- `docs/checkpoints/composite_hybrid_long_window_research_proof_2026_06_27.md`

That follow-up is ready for independent review. It gives the current composite
one realized synthetic round trip, but the candidate remains blocked from paper.

The long-window proof was independently reviewed and accepted by the human
operator on 2026-06-28 after PR #126 checks passed. The current composite still
requires accepted comparison evidence across at least three realized synthetic
windows before paper should be reconsidered.

A two-window research follow-up was implemented on 2026-06-29 in:

- `docs/checkpoints/composite_hybrid_long_window_variant_proof_2026_06_29.md`

That follow-up was independently reviewed and accepted by the human operator on
2026-06-29 after PR #143 was opened for review. It gives the current composite
three realized synthetic windows, but the candidate remains blocked from paper
because the evidence is still synthetic-only, low confidence, and has no
persisted paper-history support.

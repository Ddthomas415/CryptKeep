# Pullback Recovery Stage 0 Decision

Date: 2026-07-11

Strategy: `pullback_recovery_default`

## Decision

Keep `pullback_recovery_default` as an isolated research candidate. Do not
start a persistent paper campaign and do not mark it as a promotion candidate
yet.

## Evidence

The post-fix isolated Stage 0 proof passed:

- verifier status: `passed`
- blocking checks: `0`
- expected commit: `2953af16a`
- completed session commit: `2953af16a`
- market data source: `public_ohlcv`
- OHLCV venue/symbol/timeframe: `coinbase` / `BTC/USDT` / `5m`
- strategy attribution: `pullback_recovery_default`
- reconciliation result: `pass`
- canonical paper fill count: `176` before and `176` after
- proof result: no fills; signal held with
  `pullback_out_of_range,no_rebound_confirmation`

Existing governance state:

- `configs/strategies/pullback_recovery_default.yaml` exists as a
  governance-only strategy config.
- `activation.campaign_enabled=false`
- `activation.promotion_candidate=false`
- `strategy.trade_enabled=false`
- `services/backtest/leaderboard.py` already includes
  `pullback_recovery_default` in the research candidate set.

## Rationale

The Stage 0 proof confirms that the isolated campaign path, public-OHLCV
provenance, strategy attribution, and canonical state isolation work. It does
not prove profitability or sufficient trade frequency. The proof window ended
with a valid hold signal and no fills, so there is no paper expectancy evidence
to justify a persistent campaign.

Starting another persistent campaign now would add operator and evidence
surface area while the canonical paper gate still needs qualified round trips
and the higher-value `funding_extreme` path still needs governed Stage 0 proof.

## Required Before Promotion

Before `pullback_recovery_default` can become a persistent campaign or
promotion candidate:

- archive-backed baseline expectations must be populated
- net-fee expectancy must be positive in reproducible research
- no-trade filter settings must be accepted or explicitly waived
- a separately reviewed campaign manifest must be written
- manual strategy review criteria must be satisfied
- promotion impact on the canonical paper gate must be explicitly scoped

## Current Allowed Use

Allowed:

- research leaderboard comparison
- archive-backed parameter sweeps
- isolated one-off proof runs
- manual review of generated evidence

Not allowed without a new reviewed decision:

- persistent daily campaign
- promotion candidate status
- live, shadow, or capped-live use
- changes to canonical paper gate qualification

## Executable Guard

`tests/test_pullback_stage0_decision_guard.py` pins the isolated research
candidate decision, Stage 0 evidence boundary, required-before-promotion list,
allowed/not-allowed uses, and disabled governance config so
`pullback_recovery_default` cannot silently become a persistent campaign or
promotion candidate.

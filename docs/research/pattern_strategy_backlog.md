# Pattern Strategy Research Backlog

Date: 2026-07-03
Updated: 2026-07-21

## Current State

Pattern-style strategies exist or are partially represented:

- `pullback_recovery`
- `gap_fill`
- `volatility_reversal`
- `order_book_imbalance`
- `funding_extreme`
- `open_interest_shift`

Missing pattern research remains intentionally behind archive-first backtesting
and provenance-qualified paper paths.

## Price-Action Context Feature Pack

Status: research-only label tooling added; strategy use remains deferred.

Purpose:

- Turn discretionary price-action concepts into reproducible labels that can be
  joined to existing forward-return and walk-forward artifacts.
- Treat the labels as context/confirmation features first, not strategy
  authorities.
- Avoid adding another persistent campaign until a label improves measured
  forward-return distribution out of sample.

Candidate OHLCV-derived labels:

- `engulfing_candle`: candle body engulfs the prior candle body, direction
  recorded separately.
- `rejection_wick`: long upper/lower wick relative to body and recent range.
- `swing_failure`: sweep above/below a recent swing level followed by close
  back inside the prior range.
- `break_and_retest`: break of a recent swing/range level, retest from the
  other side, and hold/reject classification.
- `fair_value_gap`: three-candle imbalance/gap label, with fill state tracked
  later.
- `displacement_bar`: range/body expansion relative to recent bars.
- `opening_range_state`: first-session range, break, retest, acceptance, and
  rejection labels for intraday data.

Tooling:

- `services.analytics.price_action_context_labels` and
  `scripts/research/run_price_action_context_labels.py` build dataset-hashed
  OHLCV-only context label artifacts from the accepted market archive.
- The artifact is explicitly `research_only`, `not_strategy_config`,
  `not_campaign_evidence`, `not_promotion_evidence`, and
  `not_profitability_evidence`.
- Current labels cover `engulfing_candle`, `rejection_wick`, `swing_failure`,
  `break_and_retest`, `fair_value_gap`, `displacement_bar`,
  `manipulation_candidate`, and `opening_range_state`.
- Use `make price-action-context-labels` with explicit archive parameters.
  This command does not fetch from external sources; the archive must already
  contain the requested OHLCV rows.

Candidate labels requiring stronger data:

- `volume_profile_acceptance`: price acceptance/rejection relative to volume
  concentration. OHLCV-only volume profile is approximate and must be marked as
  such.
- `manipulation_candidate`: displacement followed by fast reversal or liquidity
  sweep; this is a descriptive label, not a claim of intent.
- Microstructure variants using bid/ask, trades, MBP/MBO, or top-of-book state.

Data-source boundary:

- Use the existing OHLCV archive first for candle/session labels.
- Defer volume profile until trade/tick or stronger intraday volume data exists.
- Defer Databento to a separate read-only data-source RFC. Databento is useful
  for high-quality historical/live market data schemas such as MBO, MBP, TBBO,
  trades, and OHLCV, but adopting it adds API-key, cost, dataset/schema,
  symbology, and non-crypto/futures/equities data-governance decisions.

Required artifact shape:

- dataset hash and source archive hash
- symbol, venue, timeframe, session calendar policy
- per-bar labels with no trade decisions
- explicit limitation flags:
  - `research_only`
  - `not_strategy_config`
  - `not_campaign_evidence`
  - `not_promotion_evidence`
  - `not_profitability_evidence`

Research acceptance before use:

- Join labels to forward returns after fees/slippage.
- Compare label-conditioned returns against unconditioned baseline.
- Show out-of-sample stability across multiple windows.
- Show false-positive rate and sample size.
- Review separately before using any label as a confirmation filter for
  `pullback_recovery`, `funding_extreme`, or another strategy.

## Deferred Research Ideas

- candlestick confirmation filters, starting with engulfing and rejection wicks
- fair-value gap filters with fill-state tracking
- swing-failure and break/retest labels
- opening-range and session-context labels
- displacement versus reversal/manipulation-candidate labels
- volume-profile acceptance/rejection labels after stronger data exists
- order-block style zones
- larger chart-pattern recognition
- short-side variants once derivatives data and risk controls are proven
- Databento-backed market-data research after a separate data-source RFC

## Rule

Do not promote a new pattern strategy from idea to campaign without:

- strategy-specific YAML governance config
- archive-backed walk-forward evidence
- net-fee expectancy metrics
- paper provenance contract
- explicit no-trade filters or written waiver

Do not promote a price-action label directly to execution authority. The first
eligible use is as a research-only context feature, then as a separately
reviewed confirmation filter if evidence supports it.

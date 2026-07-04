# Pattern Strategy Research Backlog

Date: 2026-07-03

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

## Deferred Research Ideas

- candlestick confirmation filters
- fair-value gap filters
- order-block style zones
- larger chart-pattern recognition
- short-side variants once derivatives data and risk controls are proven

## Rule

Do not promote a new pattern strategy from idea to campaign without:

- strategy-specific YAML governance config
- archive-backed walk-forward evidence
- net-fee expectancy metrics
- paper provenance contract
- explicit no-trade filters or written waiver

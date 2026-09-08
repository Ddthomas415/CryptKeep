# ES Corrected Policy Comparison Protocol

Active role: AUDITOR. Research only; no promotion evidence or deployment.

## Engine Coverage Finding

SHOWN: services/backtest/parity_engine.py::run_parity_backtest obtains strategy
signals and applies fee/slippage fills, but does not call the runner's
evaluate_strategy_exit_stack. It contains no trailing_stop_pct or max_bars_hold
handling. The baseline report delegates to this engine. Passing risk settings
to that existing report would not constitute an exit-policy comparison.

## Predeclared Comparison

Use one frozen archive slice and hash, fixed warmup of at least 210 bars,
identical initial capital and explicit 7.5 bps fees / 5 bps slippage per side.
These costs are assumptions, not measured execution costs. Compare the full
2x2 matrix: SMA20 versus SMA200, each with old runner defaults (3% stop, 6%
take profit, 2% trailing stop, 60 loop-count limit) versus all four disabled.
Do not choose windows or settings after seeing results. Report closed count,
net return, drawdown, open exposure and exit-reason counts; no winner from a
single in-sample run and no campaign-promotion substitution.

The SMA-only subset can use the current parity engine with explicit labeling.
The exit-policy matrix needs a separately tested research replay that invokes
the actual exit stack. It must not silently approximate runner loops as daily
bars: the old time stop counts loop iterations, and intraday stop triggers
cannot be recovered from daily closes. Daily OHLC also does not determine the
ordering of high/low stop crossings. Report unavailable intraday evidence as
unverified, not a reconstructed historical outcome.

Recommended next execution: produce the SMA-only subset from the existing
archive while specifying the intraday replay data requirements. Do not change
the canonical backtest engine merely to produce a reassuring comparison.
Running campaign positions must be checked separately before any deployment.

Acceptance state: INCOMPLETE (comparison results not yet produced).

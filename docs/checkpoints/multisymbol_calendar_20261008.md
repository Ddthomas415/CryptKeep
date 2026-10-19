# Calendar and uncertainty handoff

ENGINEER, HIGH financial-analysis logic. READY_FOR_INDEPENDENT_REVIEW.
Accepted scope: derive calendar outcomes and uncertainty from frozen final
results; no new strategy signals, tuning, data collection or campaign changes.

New read-only script scripts/research/report_multisymbol_calendar.py reads
the audited final artifact and its plan/snapshot/manifest, requires their hashes
to agree, preserves all75 strategy/control/cost outcomes, and writes a new report
exclusively. It does not modify any frozen implementation or dataset prefix.

UTC daily closes use the final hourly bar of each day; the October1 liquidation
boundary replaces September30's endpoint. Daily changes telescope to final net
profit. ISO weekly/monthly groups retain partial periods and observed day counts.

Uncertainty is post-result exploratory paired circular-block resampling of
additive daily quote changes, not reexecution of a strategy or independent
trades. Same sampled day indices for each strategy and its same-market/fee
100-notional buy-hold control. Seed20261008,2000 replicates, blocks7/14/28days;
report all sensitivities rather than select the most favorable one.
Pointwise percentile95 bands for total quote change, paired quote gap, sampled
daily-close drawdown and paired drawdown gap. No multiplicity correction,
stationarity proof, future prediction or promotion claim. Resampling terminal
cost with its day is explicit. Daily drawdown is not hourly/intrabar drawdown.

Reference for fixed circular blocks/end-to-start wrapping:
https://arch.readthedocs.io/en/stable/bootstrap/timeseries-bootstraps.html
Implementation uses NumPy, not the arch package. This reference does not endorse
the validity of these financial-path inference assumptions.

SHOWN VERIFIED_ENV: targeted tests10passed in0.23s, --noconftest isolated state
and bytecode/cache disabled. Covers midnight, terminal costs, missing/invalid
paths, total consistency, ISO periods, paired identical paths and deterministic
block sampling. Full-suite/CI not run; no real economic report run before review.

Proof requested: separate review of calendar attribution, bootstrap pairing,
method limits, invalid-input refusal and targeted tests. After acceptance,
generate report and independently check reported numerical claims. Frozen
backtest acceptance does not independently approve this new reporting logic.

# Failed Breakout/Retest - Completed Sparse-Price Sensitivity

## Result

SHOWN by saved replay: **the modeled USD1,000 account ended at USD157.59**,
an 84.24% loss. Same-period BTC buy-and-hold ended at USD1,270.19 using
identical modeled entry/exit costs. 167 trades closed: 52 net winners and
115 non-winning trades. One DIMO position remained held, with modeled cash
zero; USD157.59 is its endpoint liquidation estimate, not realized cash.

Carry-forward checkpoint: USD266.27 at September 30 17:00 UTC. Earlier
segment return -73.37%; subsequent carried return -40.82%. No new deposit
or account reset. Worst closed-trade return -13.71%; best +24.35%.
Maximum drawdown across available hourly closes was 84.80%. Eight unvalued
held hours mean this is not a complete hourly or intrabar risk measurement.
The frozen economic screen returned **FAIL**. This specific implementation
has no supporting economic result here; not every price-action setup was tested.

## Why There Is a Separate Version

The original strict run remains unchanged and correctly halted at a missing
TRIA hour. A public Coinbase candle request also omitted August 15 05:00
UTC while returning the adjacent 04:00, 06:00 and 07:00 bars:

`https://api.coinbase.com/api/v3/brokerage/market/products/TRIA-USD/candles?start=1786766400&end=1786777200&granularity=ONE_HOUR&limit=10`

This does not prove there were no trades or executable quotes; it proves
that this endpoint did not supply the candle. No bar was fabricated.

The new version explicitly borrows the existing corrected-dynamic-study
sparse-price convention: retain the position, report null NAV during a
missing/non-positive-volume held hour, and defer a pending sale to the next
recorded positive-volume open. No close decision is made without a bar.
The original timeout still advances in wall time; no hidden delay reset.
No pending exits were deferred in this actual replay; all eight gaps occurred
while holding without a pending sale. Missing entry opens remain skipped.

Independent reviewer Newton also identified an original cancellation mismatch:
unused confirmed retests were discarded before a successful buy. This version
retains them until invalidation/expiry or successful entry. The counterexample
now passes. This fix is not silently applied to the original frozen source.

This is a **post-result data-policy sensitivity**, not the original strict
test, untouched holdout, or independent confirmation. The five-hour swing
lookback, three-hour retest, range-high target, sweep-low stop, 24-hour timeout,
next-open fills, causal volume allocator and all-cash capital rule are unchanged.
All thresholds were retained. No symbol excluded because of a later loss/gap.
No new market download or reconstructed price was added to the inputs.

## Proof and Limits

The source/inputs were frozen before this sensitivity's first outcome. All
395 original archive member checksums still match. Exactly the same raw data
and 403 partly covered USD products were used. The first 101 NAV observations
exactly match the original strict prefix, before its halt. No price carried
into the eight unknown hours. Endpoint and checkpoint prices are observed bars.

Two assumptions are unchanged: modeled 0.50% fee plus 0.25% adverse price per
side; archived/current-product universe and positive-volume bars approximate
historical trading eligibility. Listing/status history, delisted markets,
spread/depth/capacity and executable prices remain unverified. These data were
already researched; no confidence interval or significance claim is made.
Infrastructure, cash interest and live account behavior are not modeled.

Artifacts:

- `scripts/research/failed_breakout_gap_replay.py`
- `tests/test_failed_breakout_gap_replay.py`
- `research/failed_breakout_gap_plan_20261012.json`
- `research/failed_breakout_gap_results_20261012.json`

Source SHA256: `022c7c55a2f70330c7ef4e3f175494b1863c51e0aebbcbb35ab1c3e903cae01d`.
Plan SHA256: `0f40ffe9c774fc23af4cdd057bc202b0adfc7b37d09e5c302ca474b5d7dd3e0e`.
Input/source bindings rechecked after replay and remain unchanged.

VERIFIED_ENV: local .venv Python 3.12. Verification command:

`./.venv/bin/python -B -m pytest -q tests/test_failed_breakout_gap_replay.py tests/test_failed_breakout_retest.py tests/test_price_action_context_labels.py tests/test_price_action_research_boundary_guard.py`

**31 passed in 0.52s.** Tests cover the original normal path, unknown held NAV,
deferred sell at actual next recorded open, missing endpoint refusal, zero-volume
execution refusal, wall-clock timeout, and the reviewer cancellation probe.
Full suite not run. No trading, account, campaign, config, collector or automation
changes. Original strict artifacts remain checksum-bound and replayable.

Acceptance: **READY_FOR_INDEPENDENT_REVIEW**. Newton was asked to reproduce
this sensitivity and check gaps, accounting and the cancellation correction.
Do not retune this rule following the failed economic screen.

## Independent Review Closure

Separate Newton GATE returned **ACCEPTED_WITH_RISK** for this frozen,
post-result sparse-price sensitivity only, with no blocking findings.
The reviewer reproduced the entire saved replay and independently reconciled
trades, allocation, cash, every NAV/null observation and the economic screen.
Original artifacts remain hash-identical; the 101-observation strict prefix
matches. The unselected-watch counterexample and synthetic deferred-exit tests
passed. The reviewer reran the four-file test slice with caching disabled:
**31 passed in 0.43s**. Full suite was not run.

Research implementation/review scope is closed. The economic screen is still
**FAIL**, not an accepted strategy. Missing-hour risk, execution realism and
historical eligibility remain unverified. No new experiment, tuning,
trading activation or deployment follows from this acceptance.

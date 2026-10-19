# Failed Downside Breakout and Retest - One Account

## Economic Result First

SHOWN by frozen replay: the full-window economic result is **INCOMPLETE**.
The first seven closed trades all lost money after modeled costs, totaling
-$189.09. A TRIA position remained open when its hourly price was missing.
At the last common observed cutoff, 2026-08-15 05:00 UTC (04:00 bar close),
the account's modeled liquidation estimate was $819.77 versus $971.86 for
same-period BTC buy-and-hold, from $1,000 each. Neither is an actual fill or
realized account balance. The account held TRIA and had zero modeled cash.

There is no complete August-October result, statistical edge claim, or basis
to trade this rule. Seven losses are adverse partial evidence, not proof
that every failed-breakout/retest strategy loses.

## Fixed Contract

- Existing five-bar `swing_failure:bullish` label: sweep the prior low and
  close above it. The detector gives a simultaneous bearish sweep priority;
  these dual-sided bars are therefore not eligible bullish signals.
- Freeze the preceding five bars' low/high and the sweep bar's low.
- Within the next three completed hourly bars, retest the prior low with
  low above the sweep low and close strictly inside the original range.
- Enter at the next hourly open, only if the modeled fill remains between
  the sweep low and original range high. No entry at the signal close.
- Exit after a close reaches the original range high, closes at/below the
  sweep low, or 24 holding bars complete. Fill at the next open. A stop is
  not a guaranteed price, and a target close does not guarantee net profit.
- One account, all cash reused, no leverage or simultaneous positions.
  Choose the confirmed candidate with the highest trailing-24h sum of
  hourly close times base volume; product ID breaks ties. This is a dollar
  turnover proxy, not measured depth or net buying. No signals while held.
- Keep cash and positions across the September 30 source boundary.

The lookback reuses the existing detector default, not a selected optimum.
No thresholds or allocator were changed after seeing this outcome.

## Data and Proof

Planned interval: August 11 00:00 through October 12 17:00 UTC, 2026.
Earlier raw OHLCV is read directly from the original last-60-day compressed
archive; all 395 USD-product member hashes and the archive checksum match.
Recent candles use the separately retained October 12 public download.
403 symbols have some in-window data; they are not all eligible every hour.
No entire-period completeness filter preselects coins using future data.

The run stops at August 15 05:00 UTC: TRIA has a 04:00 bar and 06:00 bar,
but no 05:00 bar. No carried price or interpolated candle was used.
292 sweeps and 28 confirmed retests were observed while flat; six retests
could not supply the complete causal 24-hour volume ranking window.
No pending entry was skipped in this replay. Eight buys occurred: seven
closed trades and one held position. Maximum observed close-based drawdown
before the halt was 20.63%, not full-window or intrabar drawdown.

The frozen result contains BTC's full-window estimate, $1,270.19. It must
NOT be compared with the stopped account as though the dates match.
The same-cutoff $971.86 above was independently recomputed directly from
original BTC archive rows, with the identical entry/exit cost convention.

Original strategies, source archives, prior studies, and frozen outputs
were not rewritten. New artifacts:

- `scripts/research/failed_breakout_retest.py`
- `tests/test_failed_breakout_retest.py`
- `research/failed_breakout_retest_plan_20261012.json`
- `research/failed_breakout_retest_results_20261012.json`

Source SHA256: `cf2dea6e037a8134545d0c0d77d79c840cb2983e320824d3cf9292b08accdedf`.
Plan SHA256: `20da91156d437bc20416c35eab103c4b728d2d3ba37fac000240c8def7a66863`.
The source and inputs were frozen before replay; each is checked before and
after computation. One fixed rule counts as another research trial, not an
untouched holdout. The economic screen emitted `INCOMPLETE`, not `FAIL`.

## Assumptions and Limits

1. Next-open executions with 0.50% fees and 0.25% adverse price adjustment
   per side are modeled, not book-validated fills. Historical spreads,
   capacity, account-specific historical fees and market impact are unknown.
2. The archived/current USD universe and positive-volume bars approximate
   historical eligibility; listing and trading-status history is unverified.
   Survivorship and unknown/delisted-market coverage remain limitations.

No infrastructure deduction, interest, parameter sweep, confidence interval,
independent holdout, short selling, live orders or campaign changes.

## Verification and Handoff

VERIFIED_ENV: local repository and .venv Python 3.12.

`./.venv/bin/python -B -m pytest -q tests/test_failed_breakout_retest.py`
returned **12 passed in 0.17s**. Tests cover shared-label reuse, delayed
retest/next-open fill, costs, stop gaps, intrabar versus close triggers,
future-bar invariance, missing execution/held bars, causal volume allocation,
carry state, timeout and invalid/frozen data. Full suite not run.

Expanded regression slice including the existing context-label and
research-boundary tests returned **24 passed in 0.48s**:
`./.venv/bin/python -B -m pytest -q tests/test_failed_breakout_retest.py tests/test_price_action_context_labels.py tests/test_price_action_research_boundary_guard.py`.
Frozen source/input checks were rerun and remain unchanged.

Active stage: independent GATE review. Implementation and partial replay
proof are complete; acceptance is **READY_FOR_INDEPENDENT_REVIEW**.
Proof required next: causal-contract/accounting review and independent
reproduction of the halt and same-cutoff comparison. Do not change rules or
exclude TRIA retrospectively to turn this into a complete favorable result.

## Subsequent Review and Separate Sensitivity

Newton independently reproduced all saved figures and returned
**ACCEPTED_WITH_RISK for this halted historical diagnostic only**. General
cancellation correctness was not accepted: unchosen confirmed watches are
removed too early. No skipped buys occurred in this prefix, so its numbers stand.

The original source/plan/results are unchanged. A separately frozen sparse-price
sensitivity retains positions with unknown NAV at gaps and corrects cancellation
without tuning signal thresholds. It ran through the full interval and returned
USD157.59 versus BTC USD1,270.19, with eight unvalued hours. See
`docs/research/failed_breakout_gap_replay_20261012.md` for the explicit data-policy
amendment and pending independent review. It does not replace this strict result.

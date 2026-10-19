# Frozen altcoin candidates rerun under the corrected execution contract - 2026-10-09

Research only. Not promotion evidence, not an independent holdout (all data previously studied).
Original scripts, JSON, workbooks, campaigns, accounts and schedules unchanged.
Output: `research/research_corrections_20261009/altcoins_corrected_v1.json` (+ four `--only` part files).
Script: `scripts/research/rerun_frozen_altcoins.py`, sha256 c07be3c3...056b; shared math d07ae717...9047.
Inputs: the verified `raw_archives_20261009` extraction; every input file hashed in the output.
Tests: `tests/test_rerun_frozen_altcoins.py`, 7 passed.

## What was held fixed and what changed

- Fixed: each study's originally SELECTED version (asserted against its saved JSON), its signal code
  (executed from the hashed original script), sizing, stop and holding parameters, windows, original slippage.
  No re-selection, no new parameters, no pass/fail bar changed or added.
- Changed: entries and exits at the next day's open after the decision close; trailing stops keep the frozen
  close trigger (close <= highest close since entry x (1 - T)) and fill at the next open, never at the stop
  price; held coins with missing candles are not forward-filled (strict = INCOMPLETE); delisted coins not
  sold at last close in strict mode; weekly-weight portfolios rebalance at next open via shared rebalance().
- Fees: 0.50% per side primary (observed account taker tier; product applicability UNVERIFIED);
  0.60% and 1.20% stress. BTC benchmark: same first open, same fee, 0.05% slippage, same end date.
- Statistics: paired 56-day block Sharpe difference vs BTC (2,000 repeats, seed 7), only on complete series.

## Correction to this rerun's own first draft (preserved in the work log, not hidden)

My first draft turned the frozen close-triggered trailing stop into an intraday resting stop order. That is a
rule change, not an execution correction. A concurrent review edit restored the close trigger with next-open
fills and fixed the BTC endpoint for runs that stop early. Outputs from mixed script versions were discarded;
all four groups were rerun on c07be3c3... with the hash checked before and after each run. Two tests that
encoded the wrong stop semantics were rewritten. The script's `--only merge` mode drops the recovery group
(bug); the published file was merged outside the script and says so in `merge_note`.

## Results, primary 0.50% fee, test period of each study ($1,000 start)

| Candidate | Status | End (marked) | BTC same dates | Worst drop | Trades | Sharpe diff vs BTC, 90% block range |
|---|---|---:|---:|---:|---:|---|
| Recovering former-large coins | COMPLETE | $129.51 | $1,840.38 | 92.8% | 188 | -1.36 [-2.08, -0.62] |
| Same + market-up filter (exit all) | COMPLETE | $446.42 | $1,840.38 | 70.3% | 212 | -1.18 [-2.16, -0.08] |
| New listings (day 7, above listing close, 30 days) | COMPLETE | $601.00 | $1,840.38 | 55.8% | 50 | -1.26 [-2.39, -0.17] |
| Early accumulation (3x volume, +/-10%, 35% trail) | COMPLETE | $417.27 | $1,840.38 | 83.1% | 105 | -1.03 [-2.04, -0.43] |
| Small-coin basket (28d, ranks 51-150) | INCOMPLETE 2024-03-21 | $1,214.60 at stop | $1,527.16 at stop | 23.9% | - | not computed |
| Top-10 trend, 2024-26 | COMPLETE | $1,204.80 | $1,840.38 | 30.0% | - | -0.31 [-0.97, 0.47] |
| Top-10 trend, 2020-23 | COMPLETE | $3,216.04 | $5,839.96 | 36.6% | - | 0.17 [-0.51, 0.79] |
| Top-10 trend, 2018-19 | INCOMPLETE 2018-11-16 | $721.29 at stop | $427.58 at stop | 29.9% | - | -1.72 [-3.09, -0.49] |

Incomplete runs stopped on a held coin's missing candle (STRAXUSDT; QUICKUSDT for the basket's training run;
BCCUSDT for top-10 2018-19). Their values are at the stop date only; no full-period result is claimed.
The 2018-19 Sharpe interval covers only the observed stretch before the stop.

Train-period context (0.50%): recovery $5,179.92, filter $9,294.01, new listings $3,939.97, accumulation
$3,115.64, all below BTC's $5,839.96 except the filter; basket INCOMPLETE 2023-07-18.
Stress fees lower every completed result (e.g. recovery test $104.23 at 1.20%); none changes sign or verdict.

## CMC proxy study: not rerunnable under this contract

Its prices are CMC aggregate snapshots, not exchange prices, so next-open execution cannot be modeled.
Fee-only recomputation of the selected version (rank climb, 4 weeks, BTC filter) on those aggregate prices:
test $293.78 at 0.50% (original $282.72 at 0.60%), $224.27 at 1.20%. Labeled as non-executable.

## Reading

- Every completed corrected test result for the four event-driven candidates ends below BTC, and each one's
  90% block range for the Sharpe difference vs BTC lies entirely below zero. These verdicts are unchanged
  from the originals; the corrections do not rescue any of them.
- Top-10 trend kept a positive 2024-26 return (+20.5%) but trails BTC; its intervals include zero in 2020-23 and
  2024-26, so neither under- nor out-performance is established there.
- Same-fee comparison with the originals (both at 0.60% per side, test period): recovery $102.68 -> $125.55;
  filter $402.77 -> $427.57; new listings $597.95 -> $595.53; accumulation $292.87 -> $408.29.
  Accumulation moves most: its stop exits now fill at the next open instead of the triggering close.

Status: READY_FOR_INDEPENDENT_REVIEW. No economic acceptance, promotion or holdout claim.

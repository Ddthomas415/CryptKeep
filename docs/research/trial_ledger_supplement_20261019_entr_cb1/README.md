# ENTR-CB-1 trial and data-reuse supplement

Recorded 2026-10-19 by Claude (Cowork), as required by the frozen ENTR-CB-1 preregistration (section 7:
"Adds one filtered hypothesis and one filtered control on the reused CMC archive. Record both in a new
dated trial-ledger supplement when run, with the low_value_top100 study as prior use of the same data").
This is bookkeeping for a run that has happened; it is not a new experiment.

## Disposition

Pre-registered verdict STOP (`docs/research/coinbase_tradable_entrants_20261019/results_v1/result.json`,
RESULTS_V1.md): condition (3), CB-entrants minus CB-control, failed (-7.17 dollars per USD 1,000 cycle on
96 jointly valued cycles) and condition (2) failed (-30.00 without the largest cycle). Per the
preregistration, no further variants of the historical entrant line on this archive. A declared
sensitivity (XRP's 2021-2023 Coinbase suspension excluded) gave the same verdict.

## Counting units

- One candidate configuration (Coinbase-tradable entrants) and one comparator (Coinbase-tradable control).
  The unfiltered v2 values are reference rows, not additional configurations.
- evaluated_markets = 147 distinct CMC IDs held in either filtered arm (all 35 entrant IDs are also control
  members). market_week_observations = 4,250 asset-cycle selections (41 entrant + 4,209 control); the unit
  is an asset in one four-week cycle, not a market-week. weekly_clusters = 100 four-week cycles. These
  counts are not interchangeable or additive with other studies' units.
- The low_value_top100 study (v1 and v2: 3 hypotheses, 1 horizon) is prior use of the same D_CMC archive;
  this supplement does not re-count it. The whole-project effective trial count remains unresolved.

## Evidence and limits

MODELLED outcomes on CMC weekly reference prices, not Coinbase fills. The Coinbase listing filter rests on
saved public responses (identity map v3 with CMC contract data; 1,396 candle requests) and an independently
reviewed identity map. See RESULTS_V1.md for limits.

# funding_extreme research join: independent review (backlog item 12)

Date: 2026-10-05. Reviewer: Claude (AUDITOR then ENGINEER).
Status: READY_FOR_INDEPENDENT_REVIEW. Patch 0052 (`e4789f4b`), bundle rev63,
folder `60_funding_join_coverage`. Not pushed, not applied to this checkout.

## What holds

The join enters at the close of the first bar opening at or after the funding
snapshot (no look-ahead), applies cost on both legs, and the downstream
reports refuse an input of the wrong artifact type.

## Findings

**P2. The join reported `ok` on a window that had mostly disappeared.** This
checkout's OKX BTC/USDT 5m archive ends 2026-08-13 22:35. Funding collection
continued to 2026-10-05. Each run loads the newest 500 funding rows and
silently drops those past the archive.

| Run | Joined of 500 | ok |
|---|---|---|
| 2026-08-13 | 498 | true |
| 2026-08-25 | 414 | true |
| 2026-08-30 | 282 | true |
| 2026-09-01 | 187 | true |
| 2026-09-03 | 48 | true |

The 09-03 report is four hours of 2026-08-13. Pipeline status: `latest_ok`.

**P3. A snapshot from before the archive window joined to the archive's
first bar at any distance.** Shown by test only; largest lag in the stored
artifacts is 295 s.

## Correction (research tooling only)

- A snapshot joins only to a bar opening within one timeframe of its capture.
- `join_coverage` block and per-row `entry_lag_s`.
- Contract change: `ok: false`, `low_join_coverage`, below
  `--min-join-coverage` (default 0.5; 0 restores the old behavior).
- Pipeline summary records each step's `reason` and `join_coverage`.

## Facts from this checkout's data (read-only)

- 11,467 OKX BTC funding snapshots, 2026-07-11 to 2026-10-05, 75 days with
  data. Range -0.0051% to +0.0100% per 8h. `funding_extreme` acts at
  >= +0.05% or <= -0.01%. Rows meeting either: 0.
- The pipeline tests a 5-minute holding period against a 30 bps modelled
  round-trip cost. Best of 48 hypothetical trades on 09-03: -0.18%.
- Probe over the 20 overlapping days (2,145 entry bars, one row per bar):
  correlation of funding rate with forward return is -0.02 (5 min), -0.04
  (1 h), -0.06 (8 h), -0.31 (24 h). About 20 independent 24-hour periods;
  negative-rate rows fall on 10 days, 62 of 136 on one day. Not evidence of
  an edge.

## Not changed

Strategy thresholds, the 5-minute default horizon, the threshold grid, the
500/500 row limits, the archive (not backfilled), any collector. Paper is
spot and long-only, so the research `sell` return is a short the paper path
cannot take.

## Verification

5 new tests, all fail on the previous code. Full suite at the code of 0052:
4653 passed, 33 skipped, 19 failed (the same 19 as master). Not done: the
patched join was not run against this checkout's databases.

## Decisions for the operator

1. The thresholds have not been reached once in 86 days. Wait, change them,
   change the instrument, or stop treating this as the flagship hypothesis.
2. Pick the holding period the hypothesis is about (8 h or 24 h); 5 minutes
   cannot clear 30 bps.
3. Whether to backfill the OKX archive past 2026-08-13.

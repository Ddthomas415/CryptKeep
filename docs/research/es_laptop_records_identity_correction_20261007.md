# es_daily_trend_v1 on the laptop: none of the eight records is the corrected strategy - 2026-10-07

Reviewer: Claude (AUDITOR). Read-only on the laptop checkout `620bc8dbe`: signal and fill
evidence under `.cbp_state/data/evidence/es_daily_trend_v1`, the runner's stored daily
series in `.cbp_state/data/strategy_state.sqlite` (opened read-only), and the September
checkpoints in `docs/checkpoints`. No code, state, campaign, config or workbook change.

## This corrects my own notes

`trade_record_qualification_and_fee_reconciliation_20261007.md` classed the trades of
2026-06-16, 06-21 and 07-04 as "strategy trades ... entry on a long signal above the
SMA-200" and called them the qualified cohort. That is wrong, and the repo already said so
on 2026-09-08 (`es_sma_archive_results_2026_09_08.md`: "do not treat earlier SMA20-like
paper evidence as validated SMA200 performance"; PR 588, "align managed ES exit policy with
declared controls"). I did not check my classification against those records. Checked now:

| Check | Result |
|---|---|
| Recorded `sma_200` vs a 200-day SMA of the runner's stored daily series, 64 sessions from 2026-06-30 to 09-08 | Never closer than 190 USD; median gap 6,766 USD |
| Same, 29 sessions from 2026-09-09 | Within 95 USD every day (median 50; the live fetch includes the forming candle) |
| Recorded `sma_200` on 06-16 / 07-09 / 09-08 vs a 20-day SMA | 66,121 vs 66,525; 61,840 vs 61,907; 77,984 vs 77,979 |
| Sessions before 09-09 where the recorded direction differs from the SMA-200 direction | 23 of 64, including every day of the 07-04 trade |
| Exit rule on the three trades | `trailing_stop` at 2%: the runner default, not the preset's declared zero |
| Replay of old defaults (3% stop, 2% trailing, 6% take profit) on the recorded daily prices and directions | Reproduces the three recorded entries, exit dates and exit rule |

So before 2026-09-09 the laptop campaign traded a roughly 20-day SMA with the runner's
default exits. From 09-09 it computes the 200-day SMA; no fill has occurred since.

**Qualified cohort for the corrected strategy (SMA-200, declared exits): zero records.**
All eight rows stay in the raw files. The three June-July trades are history of the old
SMA20-like policy and say nothing about the corrected one.

## What the corrected signal did on the laptop's own daily series

The stored series has 299 daily closes (2025-12-13 to 2026-10-07), so a 200-day SMA exists
from 2026-06-30.

| Date | Price | SMA-200 | Direction |
|---|---|---|---|
| 2026-06-30 | 60,260 | 75,558 | flat |
| 2026-08-20 | 69,360 | 69,035 | turns long |
| 2026-10-07 | 85,581 | 71,692 | long, unbroken since 08-20 |

One turn to long in 100 days, no turn back. A position opened at that turn would be open
and unrealized at +16.22 USD on 0.001 BTC (+23.4%) on 10-07. That replaces the "+21 USD
since 18 August" in `es_daily_trend_lockout_review_20261007.md`, which used the SMA20-like
turn. It is one open position in one trend: not a result and not evidence of an edge.

## Why neither es campaign holds that position

- **Laptop** (`.cbp_state`): the kill cooldown lockout since 9 July
  (`es_daily_trend_lockout_review_20261007.md`). The turn was consumed inside the blocked
  loops. The cooldown patches (0001, 0002 and the other session's quantity treatment) remove
  the lockout; they do not create an entry, because the signal has not changed since.
- **Hetzner corrected trial** (`es_corrected_prospective_v1`, launched 2026-09-12, endpoint
  2026-10-13): launched after the 08-20 turn. Entry needs a signal change, the signal has
  been BUY since before launch, so zero trades are expected
  (`es_prospective_endpoint_report_plan_2026_10_04.md`). No lockout is involved there.

The crossover-only entry rule is the accepted contract. Nothing here resets state, forces
an entry or changes either campaign.

## Limits

- One price per day, taken at the session (about 00:00 UTC). No intraday path.
- Days before 2026-06-30 cannot be checked against a 200-day SMA from this series; on
  06-16 and 06-21 the mean of all 186 and 191 earlier closes was about 76,500 against a
  price near 65,000.
- Regime permission is taken as recorded (`entry_allowed` true on every session).
- Which bar count the runner used before 09-09 is inferred from the fit, not read from a
  recorded config.

## Decision for the operator

When the Hetzner trial ends on 2026-10-13 with zero trades (expected), whether a new,
separately labelled trial should state what happens when it starts while the signal is
already long. That is a new trial's rule, not a change to the current one.

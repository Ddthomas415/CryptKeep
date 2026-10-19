# Where the paper evidence stands on this laptop - 2026-10-05

Status 2026-10-08: SUPERSEDED. The es interval is withdrawn and the fee figures are replaced;
see `economic_evidence_current_20261007.md`. The workbook
`cryptkeep_paper_evidence_standing_2026-10-05.xlsx` carries the same superseded figures.

Reviewer: Claude. Read-only: I read the evidence files under `.cbp_state` and
`.cbp_state_challengers/*` with a short script and changed nothing. Checkout `620bc8dbe`.
This is the laptop, not the Hetzner host, which I cannot reach. Fee tiers are not asserted.

## Result

No strategy here shows a positive edge that the data can support.

| Campaign (state dir) | Strategy | Closed trades | Wins | Total PnL (USD) | Mean per trade | 95% interval of the mean | Last fill | Sessions through |
|---|---|---|---|---|---|---|---|---|
| `breakout_default_daily` | breakout_default | 12 | 4 | +3.07 | +0.26 | -0.91 to +2.00 | 2026-09-02 | 2026-10-04 |
| `.cbp_state` (main) | es_daily_trend_v1 | 8 | 0 | -4.16 | -0.52 | -1.05 to -0.09 | 2026-07-09 | 2026-10-05 |
| `ema_cross_default_daily` | ema_cross_default | 2 | 1 | +0.22 | n/a | n/a | 2026-06-19 | 2026-08-04 |
| funding_extreme (3 dirs), pullback_recovery (2 dirs), 3 stage0/probe dirs | | 0 | | | | | never | |

Interval: bootstrap of the mean, 20,000 resamples. Entry size is about 62-75 USD per trade,
BTC/USDT on Coinbase public OHLCV, stage `paper`, sample mode false where recorded.

## What the numbers say

- **breakout_default:** the +3.07 total is one +8.67 trade. Without it the other 11 sum to
  -5.60. t = 0.31. Twelve trades cannot tell this apart from zero or from a loss.
- **es_daily_trend_v1:** eight closed trades, none profitable; the interval is entirely
  below zero. No fill for 88 days while sessions kept running.
- **Pace:** breakout made 12 round trips in 84 days, then none in the 32 days since. At one
  a week, each additional 10 trades takes about ten weeks.
- **Never traded:** funding_extreme and pullback_recovery have session records and no fills.
  For funding_extreme this matches the earlier finding that its thresholds were never
  reached in the collected data.

## Fee sensitivity (breakout_default)

Recorded fees are 1.17 USD over 24 fills, about 7.5 bps of notional per side.

| Fee per side | Total PnL over the 12 trades |
|---|---|
| 7.5 bps (as recorded) | +3.07 |
| 25 bps | +0.36 |
| 40 bps | -1.97 |
| 60 bps | -5.07 |

Break-even is about 27 bps per side. Assumption: every recorded PnL is net of the recorded
fee. Half the rows carry no `pnl_usd_semantics`; if those are gross, the total is about +2.49
and break-even about 23 bps. Which fee applies is the open paper-fee decision.

## What this means for the work

The 45 unreviewed patches make the paper and live paths more correct. They do not create an
edge. On this evidence the binding constraint on profit is the strategies, the fee
assumption and the trade count, not the plumbing.

## Not established

- Whether Hetzner campaigns have more or different evidence.
- Whether the main-state es_daily_trend records include rows written by test runs (the
  suite did not create an evidence directory in the review clone, so probably not).


## Corrections, 2026-10-07 (after the shared review, `paper_evidence_shared_review_20261007.md`)

- **es_daily_trend_v1:** the interval of -1.05 to -0.09 was computed over eight records, five
  of which are development runs or a mispriced fill. It is withdrawn. Three genuine trades
  cannot establish that the intended strategy loses.
- **breakout_default:** 15 minutes a day does not test continuously monitored execution. The
  12 trades are sampled-campaign history, not promotion evidence.
- **Fees:** the 27 bps break-even is approximate. It depends on the unresolved net/gross
  meaning of half the PnL rows and on an estimated turnover (average entry notional times 24
  fills), not on per-fill notionals.

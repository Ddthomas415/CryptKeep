# Trade-record qualification and per-fill fee reconciliation - 2026-10-07

Reviewer: Claude (AUDITOR). Read-only on the laptop checkout `620bc8dbe`: evidence JSONL
under `.cbp_state/data/evidence/es_daily_trend_v1` and
`.cbp_state_challengers/breakout_default_daily/data/evidence/breakout_default`, and
`.cbp_state/data/paper_trading.sqlite` opened read-only. No code, state, campaign, config
or workbook change. No rows deleted or marked. This is the laptop, not Hetzner.

Purpose: `paper_evidence_shared_review_20261007.md` left two things CLAIMED - which es
records are strategy trades, and the breakout session counts - and asked for fee economics
on per-fill notionals. Each is SHOWN below from the raw rows.

## 1. es_daily_trend_v1: 16 fills, 8 round trips

| # | Buy (UTC) | Sell (UTC) | Held | Buy | Sell | Gross USD | Recorded PnL | Class |
|---|---|---|---|---|---|---|---|---|
| 1 | 04-20 01:06 | 04-20 01:10 | 3.9 min | 74,377.82 | 74,275.82 | -0.1020 | 0.0 | development run |
| 2 | 04-20 01:17 | 04-20 01:19 | 2.6 min | 74,385.77 | 74,247.99 | -0.1378 | 0.0 | development run |
| 3 | 04-20 13:23 | 04-20 13:27 | 4.6 min | 75,184.40 | 75,038.30 | -0.1461 | 0.0 | development run |
| 4 | 05-15 01:02 | 05-15 01:03 | 64 s | 81,661.64 | 81,574.42 | -0.0872 | -0.0872 | development run |
| 5 | 05-18 19:02 | 05-26 00:00 | 7.2 d | 39,864.65 | 77,281.20 | +37.4165 | 0.0 | mispriced entry |
| 6 | 06-16 00:50 | 06-18 00:04 | 47.2 h | 66,353.44 | 64,527.09 | -1.8263 | -1.8263 | strategy trade |
| 7 | 06-21 00:04 | 06-24 00:04 | 72.0 h | 64,294.83 | 62,739.07 | -1.5558 | -1.5558 | strategy trade |
| 8 | 07-04 00:31 | 07-09 00:04 | 119.6 h | 62,817.25 | 62,170.22 | -0.6470 | -0.6937 | strategy trade |

Size 0.001 BTC on every fill. Recorded PnL sums to -4.163.

Grounds for each class:

- **Rows 1-4, development run.** A daily-bar strategy closed within 64 seconds to 4.6
  minutes. On those days the evidence directory took 2,411 signal rows from 8 different
  commits (04-20) and 7,890 rows from 7 commits (05-15), including synthetic prices (80.8,
  100.4, 44,800). The campaign's normal day is 2 session rows and 7 to 12 signal rows from
  one commit; 04-20 has 44 session rows, 05-15 has 12. None of these four sells carries an
  exit rule. Rows 1-3 record PnL 0.0 against a real gross loss.
- **Row 5, mispriced entry.** Bought at 39,864.65 when the same file set shows the market
  at 81,532-81,630 on 05-15 and 77,337 on 05-26. All 9,764 signal rows written on 05-18
  carry synthetic prices (maximum 44,800) from 6 commits. On the same day the same state
  database took a `BTC/USD buy 1.0 @ 100.0, fee 0` order and a Kraken ETH/USD ema_cross
  order, so the main state directory was in use by development or test processes. Gross on
  the row is +37.42 USD, recorded as 0.0. Where the 39,864.65 quote came from is not
  established.
- **Rows 6-8, strategy trade.** One commit per day, 7 to 12 signal rows, real prices,
  `market_data_source: public_ohlcv`, `ohlcv_timeframe: 1d`, `ohlcv_sample_mode: false`,
  entry on a long signal above the SMA-200, exit rule `trailing_stop` on all three.

Qualified cohort: rows 6-8. Gross -4.0291, fees 0.2872, net -4.3163 USD. Three trades do
not establish an edge in either direction. The five other rows stay in the raw files; the
operator decides whether the gate counts them.

Signal-file contamination, same directory: before 2026-06-01, 20,242 of 33,267 signal rows
have synthetic prices. From 2026-06-01, 2 of 2,538 do (2026-09-20 20:30, price 310.0,
commit `a39c44208`). The lockout analysis in `es_daily_trend_lockout_review_20261007.md`
uses rows after 9 July and is not affected.

## 2. breakout_default: 24 fills, 12 round trips

129 sessions have a start and an end record; median length 15.2 minutes; 114 start in hour
00 UTC; 112 completed, 17 failed.

| Entry (UTC) | Exit (UTC) | Same session | Windows passed while held | Exit rule | Gross USD | Recorded | Label |
|---|---|---|---|---|---|---|---|
| 06-11 00:03 | 06-11 00:06 | yes | 0 | none | -0.0421 | -0.0421 | none |
| 06-11 00:07 | 06-11 00:11 | yes | 0 | none | -0.1082 | -0.1082 | none |
| 06-11 00:13 | 06-11 00:16 | yes | 0 | none | +0.0423 | +0.0423 | none |
| 06-18 00:04 | 06-19 00:00 | no | 0 | trailing_stop | -1.6999 | -1.6999 | none |
| 06-24 00:07 | 06-25 00:01 | no | 0 | trailing_stop | -1.7992 | -1.7992 | none |
| 06-27 00:01 | 06-30 00:04 | no | 2 | none | +0.0513 | +0.0513 | none |
| 07-18 07:25 | 07-25 00:02 | no | 6 | trailing_stop | +0.0561 | -0.0400 | net_of_fees |
| 07-26 00:07 | 08-01 00:02 | no | 5 | trailing_stop | -1.5694 | -1.6649 | net_of_fees |
| 08-02 00:04 | 08-06 00:17 | no | 3 | none | +1.6382 | +1.5426 | net_of_fees |
| 08-15 00:01 | 08-16 00:01 | no | 0 | none | -0.0277 | -0.1223 | net_of_fees |
| 08-20 00:02 | 08-22 00:01 | no | 1 | take_profit | +8.7851 | +8.6742 | net_of_fees |
| 08-25 00:07 | 09-02 00:04 | no | 7 | trailing_stop | -1.6467 | -1.7640 | net_of_fees |

3 trades opened and closed inside one session; 9 held across sessions. This confirms the
counts in `breakout_campaign_sampling_review_20261007.md`. Whether a stop level was crossed
between windows cannot be shown from these files (no intraday prices here). All 12 remain
sampled-campaign history, not promotion evidence.

## 3. What the recorded PnL means (net or gross)

Checked by arithmetic on each row, to 0.0006 USD:

- Rows with no `pnl_usd_semantics` label: recorded PnL equals gross, `(sell - buy) x qty`.
  No fee is deducted. This holds for all six unlabelled breakout rows and es rows 4, 6, 7.
- Breakout rows labelled `net_of_fees` (from 07-25): recorded equals gross minus both fees.
- es row 8, labelled `net_of_fees` (07-09, commit `447dd22b3`): recorded equals gross minus
  the sell fee only. The buy fee is not deducted. One label, two meanings.
- es rows 1-3 and 5: recorded 0.0, matching nothing.

Every one of the 40 fills carries a fee of exactly 7.50 bps of its own notional, and
`slippage_pct: 0.0`.

## 4. Breakout fee economics on per-fill notionals

| Quantity | Value |
|---|---|
| Sum of notional over 24 fills | 1,555.04 USD |
| Gross PnL | +3.6798 |
| Fees recorded | 1.1663 |
| Net of all fees | +2.5136 |
| Recorded total | +3.0698 (overstates net by 0.5562: the fees of the six unlabelled trades) |
| Break-even fee per side | 23.66 bps (gross / notional) |

| Fee per side | Net over the 12 trades |
|---|---|
| 7.5 bps | +2.51 |
| 25 bps | -0.21 |
| 40 bps | -2.54 |
| 60 bps | -5.65 |

The one take-profit trade is +8.67 net; the other eleven net -6.16 at 7.5 bps.

This replaces the earlier "+3.07, about 27 bps" (estimated turnover, all rows assumed net).
It is exact for these fills under the paper model (zero slippage, fills at the paper
engine's quote). It is not executable economics: which fee tier applies is still the open
paper-fee decision, and these are sampled-campaign trades.

## Not established

- Source of the 39,864.65 quote on 05-18.
- Whether Hetzner evidence has the same label inconsistency or contamination.
- Intraday path of price against stop levels for the nine held-across trades.
- `cryptkeep_paper_evidence_standing_2026-10-05.xlsx` was not changed and still shows the
  superseded figures (es interval, +3.07, 27 bps).

## Decisions for the operator

1. Whether the paper gate counts es rows 1-5. Evidence above supports excluding them.
2. One definition for `pnl_usd` (net of both fees is what the breakout rows since 07-25
   use) and whether older rows are restated in analysis. No rows should be rewritten.
3. The paper fee: at 25 bps per side the breakout sample is already negative.


## Correction, 2026-10-07 (later the same day)

Section 1 is wrong about rows 6-8. They are not trades of the corrected strategy: before
2026-09-09 the campaign's recorded `sma_200` was a roughly 20-day SMA and its exits were the
runner's default 2% trailing stop. The repo recorded this on 2026-09-08. The qualified
cohort for the corrected strategy (SMA-200, declared exits) is zero records, and decision 1
no longer depends on rows 6-8. See `es_laptop_records_identity_correction_20261007.md`.
Sections 2-4 (breakout, PnL label meaning, fee economics) are unaffected.
`cryptkeep_trade_qualification_fee_reconciliation_2026-10-07.xlsx` was reissued the same day with the corrected class and an "ES identity check" sheet.

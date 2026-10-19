# Why the breakout campaign stopped trading, and what its 12 trades measure - 2026-10-07

Reviewer: Claude. Read-only on the laptop (checkout `620bc8dbe`): evidence files, status
files and the campaign manifest. Nothing changed. No patch: the finding is a campaign
design question, not a code defect.

## Finding

The breakout campaign runs for 15 minutes a day, at about 00:00 UTC, on a 5-minute strategy.
Its results come from positions left open between those windows with no process running,
not from the strategy's own entries and exits.

## Evidence

| Fact | Source |
|---|---|
| `runtime_sec: 900`, `signal_source: public_ohlcv_5m` | `configs/paper_evidence_campaigns.laptop.json`; `per_strategy_runtime_sec: 900.0` in the campaign's `paper_strategy_evidence.json` |
| 129 sessions with a start and an end; median length 15.2 minutes; 115 of 129 starts in hour 00 UTC | session records |
| 23 of 24 fills are between 00:00 and 00:18 UTC; the other is in the one session that started at 07 UTC | fill records |
| 15 minutes is 1.04% of a day | arithmetic |

## What the 12 trades are

| Entry | Hours held | Price move | PnL (USD) |
|---|---|---|---|
| 2026-06-11 | 0.0 | -0.07% | -0.04 |
| 2026-06-11 | 0.1 | -0.18% | -0.11 |
| 2026-06-11 | 0.0 | +0.07% | +0.04 |
| 2026-06-18 | 23.9 | -2.63% | -1.70 |
| 2026-06-24 | 23.9 | -2.86% | -1.80 |
| 2026-06-27 | 72.0 | +0.09% | +0.05 |
| 2026-07-18 | 160.6 | +0.09% | -0.04 |
| 2026-07-26 | 143.9 | -2.43% | -1.66 |
| 2026-08-02 | 96.2 | +2.60% | +1.54 |
| 2026-08-15 | 24.0 | -0.04% | -0.12 |
| 2026-08-20 | 48.0 | +12.64% | +8.67 |
| 2026-08-25 | 191.9 | -2.08% | -1.76 |

- Trades opened and closed inside one session: 3, total -0.11 USD.
- Trades held across sessions: 9, total +3.18 USD, held 785 hours (32.7 days) with no
  process watching the position.
- The one large win is a 12.6% move in BTC over two days between two midnight windows.

## Why no trade since 2 September

Nothing broke. In the 32 daily windows from 2026-09-03 to 2026-10-04 the signal read
`inside_channel` 86 times, `low_volatility_filter` 5 times and `no_signal` 4 times. The
entry filter needs a volume ratio of at least 0.95; in the window the median was 0.42 and
30% of readings reached 0.95. A breakout has to happen inside the 15 minutes to be taken.

## Already known in the repo

`docs/checkpoints/extended_venue_observation_trial_2026_09_05.md` describes "the existing
15-minute daily sampling" and adds a 24-hour trial manifest
(`configs/paper_evidence_campaigns.hetzner.extended_observation.json`, ema_cross on Gate.io
and Binance). That document records no launch. The Hetzner manifests I can read also use
`runtime_sec: 900`.

## What this means

- These 12 trades are not a test of the breakout strategy. They cannot support promoting
  it, and they do not show it fails.
- The same applies to any 5-minute campaign run for 900 seconds a day.
- Exits (stops included) are only evaluated inside the window. The four losses of 2.1% to
  2.9% were closed at the first window after the move, not when it happened.

## Decisions for the operator

1. Run 5-minute strategies continuously (as the 24-hour trial manifest does), or keep the
   15-minute cadence and stop treating its fills as strategy evidence.
2. Whether the existing 12 breakout trades count toward the paper gate.

## Not established

- Whether any Hetzner campaign already runs longer than 900 seconds.
- es_daily_trend_v1 (daily bars, `runtime_sec: 20`) is a separate question, not examined here.

# Challenger Review: 2026-09-12

Active role: AUDITOR. Advisory only; no strategy, campaign or gate changes.

## Observed Records

Both Coinbase BTC/USDT campaigns report ok=true, idle/waiting_for_next_day,
last_completed_day=2026-09-12. Breakout local status timestamp 20:01:43Z;
EMA Hetzner status timestamp 20:00:14Z. This verifies reported completion,
not continuous historical uptime or complete data coverage.

| Explicit isolated journal | Fills | Closed FIFO trades | Gross USDT | Fees USDT | Net USDT |
| --- | ---: | ---: | ---: | ---: | ---: |
| Laptop breakout_default_daily | 24 | 12 | 3.679842 | 1.166282 | 2.513560 |
| Hetzner ema_cross_default_daily | 20 | 10 | -1.354085 | 1.033470 | -2.387556 |

Both journal summaries show no remaining FIFO lots. These are all-history
journal results, not provenance-qualified counts or a matched-window experiment.
Fee totals are reported separately; modeled slippage already embedded in fill
prices is not independently measured here.

## Review Findings

- Breakout: continue unchanged paper observation, not promotion. Positive net
  aggregate warrants preserving the candidate, but does not establish an edge.
  Latest replayed loss: Aug 25 to Sep 2, net -1.764037 USDT.
- EMA: prioritize investigation before any expansion or parameter change.
  Aggregate is negative before fees, so fee reduction alone would not make
  this observed sample positive. Latest loss: Sep 9 to Sep 11, net -2.160944.
  Do not retire solely on ten historical closes or optimize against them.
- Next research question: whether matched-window, explicit-cost archive results
  support EMA's existing hypothesis. Check prior research first; do not repeat
  completed comparisons or treat this sample as an untouched holdout.

## Measurement Boundaries

The loss-replay summary's wins/losses use gross pnl (journal_analytics.py),
while loss_replays filter net pnl. Breakout reports 5 gross wins/7 gross losses
but lists 10 net-negative closes; EMA reports 4/6 gross and 7 net-negative.
Do not label gross win rates as after-cost win rates. This distinction was
verified in code, not inferred from the count mismatch.

The generic report_paper_run_diagnostics.py hardcodes .cbp_state and ignores
CBP_STATE_DIR. Its initial output was excluded from this comparison after it
showed canonical SMA status. No runtime fix was made as part of this review.
Explicit journal-path loss replay was used instead, without OHLCV fetching.

Commands: scripts/dev/replay_paper_losses.py --strategy-id breakout_donchian
(local) or ema_cross (host), --symbol BTC/USDT --limit 10 --journal-path
<campaign-state>/data/trade_journal.sqlite. Both returned ok=true.
Local root: /Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/breakout_default_daily.
Host root: /srv/cryptkeep/app/.cbp_state_challengers/ema_cross_default_daily.

Historical configuration segmentation, qualified provenance, data-gap census,
and statistical significance were not verified by these commands. No OHLCV
context requested, so exit causes are not attributed from price alone.
Acceptance state: ACCEPTED for bounded descriptive review; no promotion,
retirement, tuning, or service-change authorization follows from it.

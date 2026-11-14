# Group A scoring (spec v2 sections 7.2-7.4): written before the start

Bot relation: BOT_PAPER (scores the bot's own paper accounts). Claude, 2026-10-31. Standard library only.
Freezing: the script, the tests and `evaluation_rules.json` are frozen by their SHA-256 in `SHA256SUMS` once the owner
approves the two pending values in the rules file (minimum closed trades; drawdown rule). After that, any change is a
dated amendment in the spec, made before the start or never.

## What it does
- Rebuilds each account on two price bases from the recorded quotes, independent of the engine's own booking:
  **bidask** (buys at the ask, sells at the bid, fee on each side; decides pass or fail) and **mid** (reported).
- Per account: net return, profit or loss, maximum drawdown of hourly equity, closed trades, win rate, average win and
  loss, profit factor, fees, time invested, turnover, monthly returns, entries by minute of the hour; holding the coin
  over the same window (bid/ask with fees) and its drawdown.
- Per strategy, pooled over its three coins: closed trades, pooled net return on both bases, mean return per trade, a
  one-sided bootstrap p (calendar weeks resampled whole, all coins of a week together; null imposed by centring), and
  the classification of spec 7.4: Inconclusive, Fail, Promising but unproven, Pass, or (week 26 only) Extend to week 52.
- Week 52 judges only strategies extended at week 26 and keeps the week-26 result for the others.

## Data contract (what the simulation must produce; Codex)
- `fills.csv`, one row per fill: `account_id, strategy, coin, ts_utc` (ISO 8601 with zone), `side` (buy or sell),
  `qty` (coin units), `mid, bid, ask` (the quote recorded at the fill), `fee_rate` (per side, 0.005), `exit_rule`
  (sells). Superseded or expired orders are not fills and do not appear here.
- `hourly.csv`, one row per account per hour: `account_id, ts_utc, mid, bid, ask` (the coin's quote at the mark).
- `validity.json`: `{account_id: {strategy, coin, valid, reasons}}` from the operational checks of spec 7.2
  (decision coverage, outages, reconciliation, replay match, order integrity, fee records).

## Run
`python3 -I score_group_a.py --fills fills.csv --hourly hourly.csv --validity validity.json --rules evaluation_rules.json
--start <official start> --end <start + 26 weeks> --stage 26 --out report_week26.json`; at week 52 add `--week26
report_week26.json` and `--stage 52`. Tests: `python3 -m pytest -q -p no:cacheprovider -o addopts="" test_score_group_a.py`.

## Checks done (2026-10-31)
- Unit tests: `test_score_group_a.py` (round trip on both bases by hand, open position at the end, oversized sell
  refused, bootstrap determinism and power on a clear edge, every classification branch, drawdown rules, an end-to-end
  run and the week-52 rule).
- Dry run on the exit-parity replay (`dryrun_on_replay.py`; outputs `dryrun/summary.json`, `dryrun/report.json`; run
  with Python 3.10 on the device, 1 second): mean per trade -0.73%, -0.77%, -1.32% (breakout, EMA cross, mean reversion)
  against -0.74%, -0.77%, -1.32% in spec 7.6, which subtracted fees additively; account results within 0.2 points of the
  per-trade calculation; drawdowns slightly larger because the scorer marks every hour, not only at exits (spec 7.5 now
  shows the scorer's values). All three classify Fail on these data; breakout BTC also breaches the default drawdown
  rule (55.3% against 40.3% for holding BTC). Unit tests: 7 passed (Python 3.12, pytest).

## Decisions it encodes (from the spec; not chosen here)
Minimum closed trades 42 / 42 / 31 (spec 7.4, derived from the replay; owner approval pending); alpha 0.05/3 per
strategy; 10,000 resamples, seed 20261031; drawdown rule "no worse than holding the coin" unless the owner sets a number
(spec 7.5). An open position at the end is valued as if sold at the bid, with the fee.

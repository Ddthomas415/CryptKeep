# Live paper simulation of the bot: specification v2 (2026-10-31)

Bot relation: BOT_PAPER (the bot itself, run on fake money with live prices).
Status: specification, not built. Claude, 2026-10-31. Codex builds it; an independent reviewer checks it; the owner
approves the start. Earlier versions are in git history (last: commit f432a2bc3).
v2 adds, from the owner's and advisor's review of 2026-10-31: eleven pre-start requirements with acceptance tests
(section 6), evaluation rules for the fixed coins (section 7, for owner approval), outside monitoring and off-server
backups (section 8, owner-approved), and the commissioning and approval procedure (section 9).
Searches for earlier work: `scripts/plan_multi_symbol_paper_campaigns.py`, `plan_managed_paper_campaigns.py`,
`restore_paper_campaigns.py`, `hetzner_paper_host_preflight.py`, `check_hetzner_paper_host_health.py`,
`report_hetzner_paper_campaign_status.py`, `run_paper_strategy_evidence_collector.py`, `packaging/systemd/`,
`services/execution/paper_engine.py`, `paper_runner.py`, `services/strategies/signal_input_capture.py`,
`services/alerts/alert_dispatcher.py`, the cooldown patch reviews of 2026-10-07, `exit_parity_audit_20261031/`,
`bot_audit_20261031/` (BA-01 to BA-22), the runtime config's `paper_trading` keys (read under AGENTS.md
"Configuration inspection"). Reuse the managed paper-campaign tooling; do not build a parallel one.

## 1. Principle
Measure the bot as it is; improve only the reliability, recording and measurement around it. The bot's decision code
(strategies, filters, presets, exit rules, sizing) does not change. The only code changes allowed, each listed in the
run manifest:
- two reliability fixes that restore intended behaviour: the cooldown lockout (R1) and the stray debug line (R5);
- recording that cannot change a decision (R6, R9), proven by a test that replays the same inputs with recording on
  and off and gets identical decisions;
- the simulated exchange and the services around the bot (order expiry, monitoring, restarts, backups).

## 2. Owner decisions
- Host: the Hetzner server, 24/7. Codex sets it up; agents have no server access through Claude.
- Group A: three strategies (breakout_default, ema_cross_default, mean_reversion_default) times three coins (BTC, ETH,
  SOL, Coinbase USD pairs) = 9 accounts, one bot process each until the multi-coin fix (engineering item 1) passes.
- Group B: 9 more accounts on the coins the ranker picks each week (section 4), after Group A.
- Fake money: $1,000 per account. Fees: the account's taker rate for market orders, 0.50% per side (read 2026-10-08);
  re-read on the start day and recorded in the manifest.
- 2026-10-31: outside heartbeat monitoring approved (an independent provider); encrypted off-server backups approved
  (a provider independent of Hetzner).
- The 26-week clock has not started; it starts only by section 9.
- **Open, owner, before the start:** the drawdown limit (7.5); choosing and opening the two provider accounts (8).

## 3. Accounts and settings (each account in its own state directory)
| Setting | Value | Why |
|---|---|---|
| `strategy_runner.symbols` | exactly one coin | D-1: only the last symbol is managed |
| `signal_source` | `public_ohlcv_1h` | the presets were researched on hourly candles; the default is one-second synthetic bars (C-06) |
| strategy and preset | the default preset, unchanged | measure the bot as it is |
| exit settings | code defaults (stop 3%, trailing 2%, take-profit 6%, 60 candles), recorded in the manifest | the bot's own behaviour; the exit-parity replay predicts this case |
| `paper_trading.fee_bps` | 50 | owner decision; the current value is 7.5 |
| `paper_trading.slippage_bps` | 0, with bid and ask recorded at every fill | the engine fills market orders at the mid; the spread is the real slippage |
| `paper_trading.starting_cash_quote` | 1000 | owner decision |
| order size | a full position of about $1,000 | the default `qty` of 0.001 units is too small |
| `strategy_runner.loop_interval_sec` | 15 | the default 1 s makes about one 300-candle request per second per process (BA-11). Side effect: the cooldowns, counted in loops, become 5 and 12.5 minutes instead of 20 and 50 seconds (BA-17); record both |

## 4. Group B: coins picked by the bot's market ranker (pre-registered 2026-10-31)
The bot has no automatic coin selection: its ranker is research-only and blocked from trading until it passes a forward
test net of costs (`docs/research/signal_discovery_classification.md`, 2026-07-03). Group B is that test.
- **Ranker, unchanged:** `services/signals/market_ranker.py` (sha256 d6fc1860...), `signal_library.py` (64405797...),
  `services/analytics/multi_symbol_paper_campaign_generator.py` (f3b6b238...) as of 2026-10-31.
- **Universe:** the 25 coins in `universe` of `config/candidate_universe.yaml` (tier1, tier2, watchlist), ranked and traded
  as their Coinbase USD pairs; coins without one at a ranking (for example BNB, MATIC after its change to POL) are
  excluded and recorded.
- **When:** every Monday 00:05 UTC, on the last 200 completed hourly candles (the file's defaults). Only candles
  completed before the ranking are used.
- **Pick:** the 3 highest composite scores at or above the file's minimum, 38; a slot with no qualifying coin stays in
  cash that week. Same three strategies, $1,000, fees and settings as Group A.
- **Rotation:** a coin that stays in the top 3 keeps its slot; one that drops out is sold at the next decision (exit
  rule "rotation", fees charged) and the slot restarts flat on the new coin.
- **Separation:** the ranking runs as its own weekly job and writes a dated slot file; the bot processes only read
  their coin from it. The ranker is never imported by the runner or the paper path.
- **Recorded each week:** every coin's score, the exact input candles and code identity of the ranking (as R6), the
  picks, and the picks' raw return over the following week against the universe average and BTC.
- **Judged after at least 26 weeks over the same dates as Group A:** per strategy, the weekly net difference B minus A,
  paired block bootstrap, Holm across the 3 strategies. The ranker earns a further step only if B beats A after fees for
  at least 2 of 3 strategies and its picks beat the universe average; otherwise it stays research-only. No early verdict.
  A further step never means live trading without a separate evaluation and the owner's approval.
- **Capacity:** Group B starts when the server has room (Codex measures memory with Group A) or after the multi-coin
  fix; no silent change to either group to make room.

## 5. Known behaviour: recorded, not changed during the run
| ID | Behaviour | How it is handled |
|---|---|---|
| BA-01 | Market orders fill at the mid, not at the ask (buy) or bid (sell) | bid and ask recorded at every fill; the bid/ask result is the primary evaluation number (7.3) |
| C-06, BA-08 | Decisions use the still-forming hourly candle; the volume filter reads its part-hour volume, so signals mostly pass late in the hour | record the candles given to the strategy (R6) and the time to the second |
| BA-09 | Entry filters remove most of the strategies' own sell signals | record the blocked sell signal and its filter |
| C-06 | EMA invalidation exits are inert | record |
| BA-05, BA-18 | A refused or lost order is not re-sent while its condition lasts | record and alert (R3, R8) |
| BA-06 | Positions and cash are per state directory and symbol | one state directory per account |
| BA-10 | A failed candle fetch skips the whole decision, exits included | record every skipped loop and its reason; alert (R3) |
| BA-13 | No candle freshness or gap check in the bot | record and alert (R4) |
| BA-14 | Indicators restart on each 60-candle window | modelled by the replay; note |
| CP-06 | The kill switch is not checked on the paper path | each account stops on its own stop file; one command stops all (R2) |

## 6. Pre-start requirements and acceptance tests
A test that covers a change to the bot's code must fail on the current code and pass after the change (AGENTS.md).
Every test's output goes into the evidence pack (section 9).

**R1 Cooldown lockout fixed (BA-16).** Apply patches 0001 (cooldown kept as a persisted count of blocked loops) and 0002
(protective exits allowed during a cooldown), reviewed 2026-10-07 (combined: ACCEPTED_WITH_RISK), rebased on the
current runner; or an equivalent fix that passes the same tests.
- Set a cooldown, restart the process: the block ends after the configured number of loops, not at the old loop number
  (fails on the current code).
- During a cooldown with an open position, a stop-loss is sent and filled (fails on the current code).
- The cooldowns' wall-clock length (loops x 15 s) is in the manifest.

**R2 Automatic restarts and one stop (BA-19, CP-06).** Every process (each account's runner and paper runner, the
market-data publisher, the watcher, the backup job) runs under systemd with `Restart=on-failure`, a growing delay
between restarts and a start limit that ends a crash loop and alerts; enabled at boot. One instance per account (the
existing lock). One command stops all accounts.
- `kill -9` of each kind of process: back within 1 minute; cash, holdings, entry price, highest price, hours held and
  order history unchanged.
- Server reboot: every account back within 5 minutes, state unchanged.
- A process that fails on start stops after the limit and alerts; a second copy of an account is refused.
- The stop-all command stops every account within 1 minute.

**R3 Alerts reach the owner (BA-21).** An on-server watcher reads every account's status file and the order queue and
calls `send_alert` (alerts enabled) when: a status is older than 10 minutes; `kill_cooldown`; 10 failed candle fetches in
a row, or 5 HTTP 429 replies within 10 minutes; the quote snapshot is stale; an order is refused or expires; an exit is
delayed over 2 minutes; an order sits at `submitting` over 1 minute; disk over 80%; memory over 85%; a backup fails.
- Each condition is triggered once (on a test account where needed) and the owner confirms receipt; date and channel
  recorded.

**R4 Market data and freshness (BA-04, BA-10, BA-13).** The snapshot publisher runs (without it the engine refuses all
orders). At each decision record: the last candle's open time and whether it is complete, missing hours in the window,
quote age, bid/ask present, zero or invalid prices. Stale or gapped candles are recorded and alerted, not blocked, so
the bot's decisions do not change; the engine's existing snapshot gate stays.
- Stop the publisher: orders refused and alerted. Feed stale, gapped and zero-price data: each recorded and alerted.

**R5 Debug line removed (BA-12).** Delete the `/tmp/cbp_debug.txt` write (`strategy_runner.py` line 1208). Logs go to
journald or rotated files with a size cap. The ledger and the decision archive are kept apart from logs.
- 100 loops create no `/tmp/cbp_debug.txt`; the log size cap is shown; decisions identical before and after (replay).

**R6 Every decision's inputs saved, and replay reproduces it.** Extend the existing capture
(`services/strategies/signal_input_capture.py`: content hash, code identity, replay function; today only for the ES
strategy and opt-in) to the three strategies and every decision loop. Per decision: account; UTC time; the exact
candles given to the strategy with their times and completeness; strategy settings; code commit and settings hash;
signal, indicator values and the filter that turned a signal into hold; exit inputs (entry price, highest price, hours
held, current price); every exit condition (R9); the action intended and the action taken. Storage: keep the completed
candles once per change (content-addressed, shared by accounts on the same coin) and the forming candle per loop; the
manifest states the expected size for 26 weeks.
- **A matching replay means:** from the saved inputs, the same code reproduces for every recorded decision the signal
  action, the signal reason (including the filter), the indicator values exactly, every exit condition, the exit rule
  chosen and the intended action.
- Replay of a one-hour recording matches 100%. A deliberately altered input is detected by its hash. Recording on and
  off give identical decisions.

**R7 Fixed-coin evaluation rules approved before the start.** Section 7, including the drawdown limit, approved by the
owner and recorded in this file before the official start.

**R8 Stale orders.** An entry (buy) order not filled within 120 seconds of creation is marked expired and never filled,
with its creation time, expiry time and reason, and an alert. Exit (sell) orders do not expire: the runner never sends an
exit again (BA-05), so expiring one would leave the position without protection; a late exit fills when the engine is
back, with its delay recorded and an alert if over 2 minutes. Nothing is discarded silently.
- Stop the paper runner, queue a buy, wait 3 minutes, restart: expired, not filled, alerted. Same with a sell: filled
  late, delay recorded, alerted.
- The same order ID submitted twice: one fill (the engine refuses a second fill of a client order ID,
  `paper_engine.py` 241-243). Kill the paper runner just after a fill: no second fill on restart.
- An order stranded at `submitting` (BA-18): alerted.
- Each fill charges 50 bps on its notional and records bid, ask and mid with the quote's age and source.

**R9 Every exit condition recorded.** While holding, record at each decision every exit condition and whether it is
true: stop-loss, trailing stop, take-profit, time limit, the strategy's sell signal (and its filter). The order stays as
coded: stop-loss, then trailing stop, then take-profit, then time limit, and the strategy's sell only if none of these
(`services/risk/exit_controls.py` line 53; `strategy_runner.py` 1460-1476). Prices stay as coded: the latest trade price
at each 15-second check (the forming candle's last close), not the candle's low; stops are measured from the price at
the buy decision (`strategy_runner.py` line 1614), not the fill price.
- A synthetic price path with stop-loss, trailing stop and the sell signal true together: all three recorded, the
  stop-loss acted on. Recording on and off give the same actions.

**R10 Outside monitoring and off-server backups.** Section 8, with its tests.

**R11 72-hour commissioning.** Section 9, step 2.

## 7. Evaluation rules for the fixed coins (Group A): proposed 2026-10-31, owner approval required before the start
**7.1 Two questions, never mixed.** Did the simulation run the bot faithfully (7.2)? Does a strategy show an advantage
after costs (7.3-7.4)? A failure of the first makes the result inconclusive, not a strategy failure.

**7.2 Operational validity, per account (all must hold):**
- 26 weeks from the official start; decisions recorded in at least 95% of hours; outages total at most 5% of hours, each
  explained in the log;
- the ledger reconciles daily: cash plus holdings at the mid equals the recorded equity to the cent, and every change is
  explained by a fill and its fee;
- replay matches 100% (R6), or every mismatch is explained and shown not to affect a trade;
- no duplicate fills; every expired, refused or delayed order recorded and explained;
- fees complete: amount and fee on each side.

**7.3 Measures,** for each account, each strategy pooled over its 3 coins, and all 9 together, on two bases: primary,
bid/ask (buys at the recorded ask, sells at the recorded bid, plus 0.50% fee per side); secondary, the engine's mid
fills. Net return; against holding the coin over the same window; against cash (cash earns nothing here, so a positive
net return is the same as beating cash); maximum drawdown of hourly account value; profit factor; win rate; average win
and loss; closed trades; fees paid; time invested; turnover; monthly returns. Also: blocked sell signals and what the
price did afterwards (BA-09); the minute of the hour of entries (BA-08).

**7.4 Classification, per strategy** (pooled over BTC, ETH and SOL; the coins move together, so the nine accounts are
not nine independent tests and no single account can pass on its own):
- **Inconclusive:** operational validity failed for any of its accounts, or fewer than 10 closed trades pooled.
- **Fail:** pooled net return at or below zero on the bid/ask basis, or any of its accounts breaches the drawdown limit.
- **Promising but unproven:** net above zero and no breach, but fewer than 30 closed trades or the test below not met.
- **Pass:** net above zero, no breach, at least 30 closed trades, and mean net return per trade above zero with a
  one-sided p below 0.05 after Holm correction across the 3 strategies (block bootstrap over calendar weeks, all coins of
  a week resampled together, 10,000 resamples, seed fixed in the analysis script, which is written before the start).
- Buy-and-hold is reported, not required: a strategy that holds the market less of the time can be useful without
  beating it. A Pass only allows the owner to consider a next step; it never authorises live trading.

**7.5 Drawdown limit: owner decision before the start.** Figures for these rules from research (7.6) and from holding
each coin over the same 39 weeks (OKX hourly closes, 2026-01-01 to 2026-09-30):

| Coin | Replay account result over 39 weeks (breakout / EMA cross / mean reversion) | Replay maximum drawdown | Holding: return / maximum drawdown |
|---|---|---|---|
| BTC | -54% / -24% / -25% | 54.7% / 27.1% / 25.4% | -4.2% / 40.3% |
| ETH | -53% / -26% / -20% | 53.7% / 29.4% / 19.9% | -9.9% / 55.0% |
| SOL | -53% / -31% / -18% | 57.4% / 31.3% / 18.1% | -4.7% / 58.8% |

Options: (a) the bot's own setting, a 10-point drawdown on its running sum of trade results (the performance kill),
which every replayed account exceeds; (b) a fixed limit of the owner's choosing, as a share of the account; (c) no
worse than holding the coin over the same window; or (b) and (c) together. The limit is the owner's risk choice (open
decision 2, capital); research gives the figures above, not the number.

**7.6 Expectation registered before the start.** Replay of the bot's own rules (exit-parity audit, variant
C_path_w60: 60-candle window, the bot's exit stack, completed OKX hourly candles, BTC/ETH/SOL, 2026-01-01 to 2026-09-30,
5 bps slippage each side, 0.50% fee per side, full account per trade):

| Strategy | Closed trades per 26 weeks (3 coins) | Per trade before fees | Per trade after fees | Win rate after fees |
|---|---:|---:|---:|---:|
| breakout | about 200 | +0.26% | -0.74% | 27% |
| EMA cross | about 79 | +0.23% | -0.77% | 25% |
| mean reversion | about 36 | -0.32% | -1.32% | 17% |

On this evidence all three are expected to lose after costs, breakout the most. The simulation tests this; differences
are measured weekly (7.8). Limits of the expectation: OKX USDT completed candles, not Coinbase USD forming candles;
5 bps slippage, not the measured spread; one 39-week period in which the coins fell.

**7.7 Group B:** section 4.

**7.8 Weekly checks (Claude):** replay match (R6); comparison with the completed-candle replay, which measures the
forming-candle effect; spread and fees against the assumption; uptime, gaps, restarts, alerts. No performance verdict
before week 26.

## 8. Outside monitoring and off-server backups (owner-approved 2026-10-31)
**8.1 Heartbeats.** A hosted heartbeat service independent of Hetzner (for example Healthchecks.io or Better Stack; the
owner chooses and opens the account). One check for each account (9; 18 with Group B), the paper execution side, the
market-data publisher, the on-server watcher and the backup job: 13 for Group A. Each pings at least every 5 minutes;
grace 10 minutes; notifications to the owner through a tested channel (phone and email). Ping addresses are secrets:
kept on the server in a root-only file outside the repository, never in code or logs.
- Stop one account: notification within 15 minutes. Shut the server down: notifications for every check. The owner
  confirms receipt.

**8.2 Backups.** Encrypted on the server before upload (for example restic), to a storage provider independent of Hetzner
(the owner chooses and opens the account).
- What: the account ledgers and state databases (consistent SQLite copies), the decision-input archive, the
  recordings, the run manifest and the configuration without secrets.
- When: every 6 hours. Kept: every backup for 7 days, daily for 30 days, weekly until 3 months after the run ends.
- Credentials: a key used only for backups, stored like the ping addresses, separate from anything else on the server;
  where the provider allows, a key that cannot delete (pruning done separately by the owner).
- Verification: the tool's integrity check after each backup; weekly, an automatic restore of the latest backup to a
  temporary folder with checksums compared, reported to the heartbeat service; during commissioning one manual restore
  with the owner.
- Tests: a backup completes and verifies; a restore reproduces the ledger exactly; a failed backup alerts.

## 9. Commissioning and approval
1. **Build and test.** R1 to R10 implemented; every acceptance test passes. Evidence pack: test outputs, versions,
   configuration hashes.
2. **Commissioning, 72 hours,** all Group A accounts and services on the server with the version to be frozen. Codex
   runs the failure tests on the real set-up: kill an account process (including one holding a position; if none holds
   one, a commissioning test account seeded with a position); kill the paper runner just after a fill; reboot the
   server; cut the network for 10 minutes; stop the market-data publisher; submit a duplicate order; fill a test disk or
   simulate a write failure. It passes when: every account recorded decisions in at least 99% of loops outside the
   deliberate failures; data stayed fresh; each failure behaved as R1-R10 require and its alert reached the owner;
   ledgers reconcile to the cent; replay matched 100% of the 72 hours' decisions; a backup was restored; memory stayed
   under 70% and projected disk use for 26 weeks is under 60%. Commissioning trades are excluded from the evaluation.
   Any failure: fix it and restart commissioning from zero.
3. **Independent review** of the code changes, the evidence pack and the commissioning report by someone other than the
   builder (AGENTS.md "Cross-review").
4. **Owner approval in writing** (here or in `docs/PROJECT_STATE.md`). It sets the official start at the first full hour
   after approval and freezes the git commit, configuration hash, dependency lock and the fee rate read that day. Each
   account restarts at $1,000.
5. **During the run:** no change to the bot's code or settings. An infrastructure fix that leaves the bot's code and
   settings hashes unchanged is logged and allowed. Any change to them starts a new, separately named experiment.

## 10. What to record (append-only, per account)
Per decision: R6 and R9. Per signal change, order, fill and exit: UTC time to the second, coin, strategy, signal and
reason (including the filter that turned a signal into hold), candle time used, price used, bid, ask and mid with quote
age and source, order type, order creation and fill or expiry time, fill price, notional and fee per side, exit rule and
all exit conditions true, position, cash, equity. Every skipped loop with its reason. Hourly: equity mark and the coin's
price. Daily: a summary per account (trades, fees, net on both bases, drawdown, holding the coin over the same time) and
the reconciliation result. Weekly (Group B): the ranking record. Every restart, alert, expiry and outage with its time.

## 11. Done when
Section 9, steps 1 to 3, complete; the owner's approval (step 4) starts the clock. Group B follows when capacity
allows, through the same steps.

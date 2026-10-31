# Live paper simulation of the bot: specification for Codex (owner decisions 2026-10-31)

Bot relation: BOT_PAPER (this is how the bot itself will be run on fake money with live prices).
Claude, 2026-10-31. A specification, not an implementation; Codex builds it, the owner approves the deployment.
Searches for earlier work: `scripts/plan_multi_symbol_paper_campaigns.py`, `plan_managed_paper_campaigns.py`,
`hetzner_paper_host_preflight.py`, `check_hetzner_paper_host_health.py`, `report_hetzner_paper_campaign_status.py`,
`run_paper_strategy_evidence_collector.py` (the two server jobs since 2026-09-16), `services/execution/paper_engine.py`,
`paper_runner.py`, the runtime config's `paper_trading` keys (read 2026-10-31 under AGENTS.md "Configuration
inspection"), and the capital-protection audit. Reuse the managed paper-campaign tooling; do not build a parallel one.

## Owner decisions
- Host: the Hetzner server, running 24/7. Codex sets it up; agents have no server access through Claude.
- Accounts: three strategies (breakout_default, ema_cross_default, mean_reversion_default) times three coins (BTC, ETH,
  SOL, Coinbase USD pairs) = 9 accounts, one bot process each, until the multi-coin fix (engineering item 1) passes.
- Fake money: $1,000 per account.
- Fees: the account's real tier for market orders, 0.50% per side (taker, read 2026-10-08).

## Required settings per account (each in its own state directory, as the existing campaigns do)
| Setting | Value | Why |
|---|---|---|
| `strategy_runner.symbols` | exactly one coin | D-1: only the last symbol is managed |
| `signal_source` | `public_ohlcv_1h` | the presets were researched on hourly candles; the default is one-second synthetic bars (C-06) |
| strategy and preset | the default preset, unchanged | measure the bot as it is |
| exit settings | leave unset (code defaults: stop 3%, trailing 2%, take-profit 6%, 60 candles) and record them in the run manifest | the bot's own behaviour; the replay in `exit_parity_audit_20261031/` predicts this case |
| `paper_trading.fee_bps` | 50 | owner decision; the current value is 7.5 |
| `paper_trading.slippage_bps` | 0, with bid and ask recorded at every fill (see below) | the engine fills market orders at the mid; spread is the real slippage |
| `paper_trading.starting_cash_quote` | 1000 | owner decision |
| order size | sized from the account's cash so a full position is about $1,000 (the default `qty` is 0.001 units) | otherwise positions are tiny and fees round oddly |
| `strategy_runner.loop_interval_sec` | 15 | the default 1 s makes about one 300-candle request per second per process, near Coinbase's public limit with 9-18 processes (bot audit BA-11); 15 s delays an hourly decision by at most 15 s |

## Known flaws to fix or record before the data is trusted
1. **Market orders fill at the mid price** (`paper_engine.py` lines 396-401), not at the ask (buy) or bid (sell).
   Fix: fill at ask/bid when present; until fixed, record bid, ask and mid at each fill so analysis can correct it.
2. **Paper fees are 7.5 bps in the runtime config** (SHOWN 2026-10-31); set 50 bps for these accounts.
3. **EMA invalidation exits are inert** (C-06): record, do not fix during the run (it would change the strategy).
4. **The kill switch is not checked on the paper path** (CP-06): each account must stop on its own stop file, and one
   command must stop all nine.
5. Fill quotes come from the tick snapshot or a public ticker fallback; record which, and the quote age at each fill.
6. **The paper engine refuses every order unless the system-status snapshot is fresh** (`paper_engine.py`
   `_pre_submit_gate`; SHOWN by running), so the snapshot publisher must run alongside the nine accounts.
7. **A refused or rejected intent is final on the paper path too:** `paper_runner.py` marks it rejected and the runner
   does not re-send the same action, so a missed exit stays missed while its condition lasts (as CP-09 on the live
   path). Record every rejected intent with its reason; an alert if an exit is rejected.
8. **Positions and cash are per state directory and per symbol, not per strategy** (`paper_trading_sqlite.py`), so
   each account needs its own state directory; two strategies sharing one would share a position.
9. **The volume filter reads the still-forming candle** (BA-08): signals mostly pass late in the hour. Record, do not fix.
10. **Entry filters remove most of the strategies' own exit signals** (BA-09, known). Record, do not fix during the run.
11. **A failed candle fetch skips the whole decision, exits included** (BA-10). Record every skipped loop and its reason
    (including HTTP 429); alert after 10 consecutive skips in one account.
12. **The runner appends a line per loop to `/tmp/cbp_debug.txt`** (BA-12). Remove that line before the start (it
    changes no decision) or rotate the file; alert when the disk is 80% full.
13. **No freshness or gap check on candles** (BA-13): record the last candle's time and any missing hours at each
    decision; matters most for Group B's smaller coins.

## Group B: coins picked by the bot's market ranker (pre-registered 2026-10-31; owner: "do what's best")
The bot has no automatic coin selection: its ranker is research-only and blocked from trading until it passes a
forward test net of costs (`docs/research/signal_discovery_classification.md`, 2026-07-03). Group B is that test,
run alongside the fixed coins (Group A, above) so the two can be compared week by week.
- **Ranker, unchanged:** `services/signals/market_ranker.py` (sha256 d6fc1860...), `signal_library.py` (64405797...)
  and `services/analytics/multi_symbol_paper_campaign_generator.py` (f3b6b238...) as of 2026-10-31; no weight changes.
- **Universe:** the 25 coins in `universe` of `config/candidate_universe.yaml` (tier1, tier2, watchlist; listed there as
  USDT pairs), ranked and traded as their Coinbase USD pairs, so the coins ranked are the coins traded. Coins without a
  tradable Coinbase USD pair at a ranking (for example BNB, and MATIC after its change to POL) are excluded and
  recorded with the reason. (The standard scan, tier1 plus `coinbase_pairs`, would rank USDT and USD pairs of the same
  coins side by side; not used.)
- **When:** every Monday 00:05 UTC, on the last 200 completed hourly candles (the file's defaults: 1h, 200). Weekly,
  because daily rotation multiplies fees at 0.50% per side.
- **Pick:** the 3 highest composite scores at or above the file's minimum, 38. A slot with no qualifying coin stays in
  cash that week (recorded; this is the ranker's own rule). Scores of all ranked coins are recorded. Three slots x the
  same three strategies = 9 accounts, $1,000 each, same fees and settings as Group A.
- **Rotation:** a coin that stays in the top 3 keeps its slot. A coin that drops out is sold at the next decision after
  the ranking (exit rule "rotation", recorded) and its slot restarts flat on the new coin.
- **Separation:** the weekly ranking runs as its own job and writes a dated slot-to-coin file; the bot processes only
  read their coin from it. The ranker is never imported by the runner or the paper path, so the existing guard and
  the July rule stay intact for everything else.
- **Also recorded, no extra processes:** each week, the 3 picked coins' raw return over the following week against
  the average of the eligible universe and against BTC. This measures the ranking on its own, without strategy noise.
- **Judged after at least 26 weeks:** per strategy, the weekly net difference Group B minus Group A, paired block
  bootstrap, Holm across the 3 strategies. The ranker earns a further step only if B beats A after fees for at least 2
  of 3 strategies and its picks beat the universe average; otherwise it stays research-only. No early verdict.
- **Server capacity:** 18 accounts may be too many processes for the 4 GB server. Codex measures memory with Group A
  first; Group B starts when there is room, or after the multi-coin fix lets one process serve 3 coins. No
  silent change to either group to make room.

## What to record (append-only, per account)
Every loop is not needed; every decision is. Per signal change, order, fill and exit: UTC time (to the second, so the
minute within the hour is known), coin, strategy, signal and reason (including the filter that turned a signal into
hold), candle time used, price used, bid/ask/mid and quote age, order type, fill price, fee, exit rule
(signal, stop, trailing, take-profit, time), position, cash, equity. Hourly: equity mark per account and the coin's
price. Daily: a summary file and one line per account (trades, fees, net, drawdown, holding the coin over the same
time). Heartbeat per process every minute; an alert if any heartbeat is older than 10 minutes.

## How it will be judged (research item, Claude)
- **Parity:** each week, replay the same hours through `exit_parity_replay.py` rules and compare trade by trade
  (entries, exits, exit rule, prices). Differences are findings about the bot, not about the strategy.
- **Costs:** measured spread and fees per fill against the 0.50% assumption.
- **Results:** per account and in total, net of fees, against holding the coin and against cash; no conclusion about
  profitability before about 26 weeks (POP). The point of the first weeks is to learn whether the bot behaves as the
  research says.
- **Operations:** uptime per process, gaps in decisions, restarts, stale quotes.

## Done when (engineering)
Group A's 9 accounts run on the server with the settings above, recording as specified; Group B's weekly ranking job
and 9 accounts follow when capacity allows; a test shows each account's fills
use the configured fee and record bid/ask; one command stops all nine; the run manifest (code hash, settings, start
time) is saved; independent review; owner approves the start. Not before: none. It does not depend on item 1.

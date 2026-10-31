# Whole-bot audit for flaws (research item 1): simulation path first

Bot relation: audit of the bot's own code (not a strategy result).
Owner direction 2026-10-31. Claude, read-only on the repository (probes run on a copy in the Linux shell's home with a
temporary state directory). **Self-checked; Codex to verify.** Budget: three sessions for the simulation path;
sessions 1 and 2 are below. Searches for earlier work: `capital_protection_audit_20261031/`, `exit_parity_audit_20261031/`,
`integrity_audit_20261015/`, the Hetzner paper tooling (`scripts/*paper*`), the July 2026 audit (chat summary).

| Area | Status |
|---|---|
| Paper engine (fills, fees, cash, positions, profit) | Session 1: done below |
| Paper runner (intent consumption) | Session 1: rejection handling done below |
| Market data (candles, quotes, staleness) | Session 2: done below |
| The three default strategies' signal code | Session 2: done below (exit filters already known: failure diagnosis) |
| Restart and recovery on the paper path | Session 3 |
| Monitoring and alerts | Session 3 |
| Runner decisions and exits | Done in earlier audits (D-1, CP-09, C-06) |

## Session 1 findings
| ID | Finding | Evidence | Severity (simulation) | Owner | Disposition |
|---|---|---|---|---|---|
| BA-01 | Market orders fill at the mid price plus configured slippage, never at the ask (buy) or bid (sell). In the probe (bid 99 / ask 101, then 109 / 111) the engine booked +$44.75 on a round trip that is +$39.27 at the quoted prices. | SHOWN by reading (`paper_engine.py` 396-401) and by running (probe P-3) | HIGH | Codex | Fix, or record bid/ask at every fill (spec item 1) |
| BA-02 | The runtime config charges 7.5 bps fees and 5 bps slippage on paper; the account's taker fee is 50 bps. | SHOWN (whitelisted config read) | HIGH | Owner (decided: 50 bps) | Set per account (spec) |
| BA-03 | Accounting is correct by its own rule: fee-inclusive average cost; cash, quantity and realized profit match hand arithmetic to the cent. | SHOWN by running (probe P-3) | Control present | - | - |
| BA-04 | Every paper order is refused unless the system-status snapshot is fresh, the master read-only flag is off, market quality passes and the safety gates allow it. Without the snapshot publisher running, the bot trades nothing. | SHOWN by running (first probe run: `staleness:snapshot_missing`) and reading `_pre_submit_gate` | HIGH (operational) | Codex | Run the publisher; alert on refusals (spec item 6) |
| BA-05 | A refused or rejected intent is final: `paper_runner.py` marks it rejected and the runner does not re-send the same action, so a missed exit stays missed while its condition lasts. | SHOWN by reading (`paper_runner.py` 140-215; runner line 1512) | HIGH | Codex | Record and alert (spec item 7); fix with CP-09 |
| BA-06 | Positions and cash are kept per state directory and per symbol, not per strategy: two strategies in one state directory would share a position. | SHOWN by reading (`paper_trading_sqlite.py` apply_fill) | MEDIUM | Codex | One state directory per account (spec) |
| BA-07 | Fills are whole and immediate (no partial fills, no order-book depth). | SHOWN by reading | LOW at $1,000 | - | Note |

Probe P-3 (`probes/test_probe_paper_engine.py`): the real `PaperEngine` with fixed quotes; its submit gates are
replaced only to test the accounting. Rerun from the repository root:
`CBP_STATE_DIR=$(mktemp -d) python -m pytest -p no:cacheprovider -q -s -o addopts="" docs/research/bot_audit_20261031/probes/`

## Session 2 findings: market data and the three strategies' signal code
Scope: `strategy_runner.py` (sha256 7006466d...) `public_ohlcv_*` branch (lines 813-907, 1180-1290), the signal
functions `ema_cross.py`, `mean_reversion_rsi.py`, `breakout_donchian.py`, `indicators.py`, `market_filters.py`,
`strategy_registry.py`, the default presets, and ccxt 4.5.48 `coinbase.fetch_ohlcv`. Searches for earlier work:
failure diagnosis 2026-10-30 (exit filters), PROJECT_STATE caveat C-06 (forming candle), the exit-parity replay
(60-bar window, variant C_path_w60), the review handoff, `docs/audit_artifacts/`.

| ID | Finding | Evidence | Severity (simulation) | Owner | Disposition |
|---|---|---|---|---|---|
| BA-08 | **The volume filter reads the still-forming hourly candle** (consequence of C-06, not recorded before). `market_context` divides the last candle's volume by the previous 7; with `public_ohlcv_1h` the last candle is the current hour, so its volume is only part of an hour's. Holding prices fixed and scaling only that volume, the share of the strategies' signals that still pass at 25% / 50% / 75% / 90% of the hour: EMA cross buys 18 / 51 / 80 / 90%, sells 14 / 47 / 79 / 91%; mean reversion buys 7 / 18 / 66 / 90%, sells 1.5 / 13 / 54 / 82%; breakout buys 23 / 67 / 89 / 96%, sells 24 / 67 / 90 / 97%. Entries and signal exits therefore mostly wait until late in the hour, and a cross or breakout that reverses before the hour's volume builds up never fires (for EMA cross the signal exists only in the hour of the cross). | SHOWN by reading (`market_filters.py` 41-43) and by running (probe P-4; OKX hourly candles, BTC/ETH/SOL, 6,852 hours each; volume assumed to build evenly through the hour) | MEDIUM (parity with research on completed candles) | Codex / Claude | Do not change during the run; record the minute of the hour of every signal and fill (spec) |
| BA-09 | **The entry filters remove most of the strategies' own exit signals** (already known: failure diagnosis 2026-10-30, C1-C2; counted here on the bot's 60-candle window). Completed hours: EMA cross keeps 128 of 360 cross-down sells (removed: low volume 155, cross gap 50, chop 22, low volatility 5); mean reversion keeps 67 of 1,160 overbought hours (removed: low volume 466, no reversal 376, high volatility 156, too far from average 68, trend 27; counted per hour, and an overbought spell lasts several hours, so fewer exits are lost than hours); breakout keeps 680 of 727 (removed: low volume 45, low volatility 2). A position whose exit signal was removed leaves by stop, trailing stop, take-profit or the 60-hour limit. | SHOWN by running (probe P-5) | MEDIUM (known; the exit-parity replay already includes it) | Owner / Codex | Do not change during the run (it would change the strategy); fix decision after, with ED-002 exit scope |
| BA-10 | **A failed candle fetch skips the whole decision, exits included.** On an exception or empty reply `_fetch_public_ohlcv` returns no rows and the runner sleeps and continues (lines 1194-1203) before stops, trailing stops or signals are evaluated; stops exist only in the bot, not on the exchange. | SHOWN by reading | MEDIUM on paper (missed decisions); HIGH before live | Codex | Record every skipped loop with its reason; alert on runs of failures (spec) |
| BA-11 | **Request rate.** Every loop fetches 300 hourly candles (ccxt caps the bot's `max_bars` 400 at 300), and the loop sleeps `loop_interval_sec`, default 1 second (lines 367, 1814): about one request per second per process for a decision that changes once an hour. 9 accounts make up to about 9 requests per second from the server's address, 18 with Group B, plus the data collector. A limit of 10 public requests per second per IP is commonly cited for Coinbase Advanced Trade (CLAIMED by a third-party summary; not verified against Coinbase's documentation). Over the limit, fetches fail and BA-10 applies. | SHOWN (code, ccxt source); limit UNVERIFIED | MEDIUM | Codex | Set `loop_interval_sec` in the spec (15 s) and count HTTP 429 replies |
| BA-12 | **An unbounded debug file.** Every loop of the `public_ohlcv_*` branch appends a line to `/tmp/cbp_debug.txt` (line 1208), shared by all processes and never rotated: about 60 bytes a loop, up to about 5 MB a day per process at 1-second loops, up to about 8 GB over 26 weeks for 9 processes. | SHOWN by reading | LOW (disk) | Codex | Remove the line (behaviour unchanged) or rotate it; monitor disk (spec) |
| BA-13 | **No freshness or gap check on candles.** The runner does not compare the last candle's time with the clock and does not check for missing hours; the research engine refuses gaps (S4-02). Coinbase omits hours without trades. | SHOWN by reading | LOW for BTC/ETH/SOL; MEDIUM for Group B's smaller coins | Codex | Record the last candle's time and any gaps at each decision (spec) |
| BA-14 | The indicators start again on each loop's 60-candle window: the slow EMA keeps about 1% of its weight on the window's first close, Wilder RSI about 3% on its first 14 changes. Signals near a threshold can differ from a long-history calculation. | SHOWN by reading (`indicators.py`) | LOW (the exit-parity replay variant C_path_w60 already models the 60-candle window) | - | Note |
| BA-15 | Look-ahead in the signal code: none found. Breakout compares the current price with the previous channel (`up[-2]`, excluding the current candle); EMA cross and mean reversion use the latest close only. The only "future" in live use is the opposite: the forming candle (C-06, BA-08). | SHOWN by reading | Control present | - | - |

Probes P-4 and P-5 are scripts, not tests, run on the existing archive `research/multisymbol_baseline_v1/public_archive.sqlite`
(sha256 e74aa378..., untracked, read-only) with the copy of the code (identical to the repository for the files used):
`python3 -I docs/research/bot_audit_20261031/probes/probe_forming_volume.py <repo root> <archive> <out.json>` and the same for
`probe_filtered_sells.py`. Outputs: `probes/forming_volume.json`, `probes/filtered_sells.json`. OKX volumes, not Coinbase's.

**What could overturn this:** intra-hour volume is not even (it bunches around news and the hour), so BA-08's shares
are indicative; Coinbase's real rate limit (BA-11); whether Coinbase returns the forming candle for every product
(C-06 was shown on the runner's code path, not per product).

# Exit-parity audit: do the backtests test what the bot trades?

Research item 1 in `docs/PROJECT_STATE.md` (owner direction 2026-10-31). Claude. **Self-checked; not independently
verified.** Codex cross-review requested (section 8). Diagnostic and in-sample: no new strategy, no tuning, no new
data, no fee optimisation, no change to code, config, the symbol universe or any earlier document's results.

## Short answer
- **No, the backtests don't test what the bot trades.** Every backtest of the bot's own technical strategies since
  October 8, except two (below), tested the strategy signals only. The bot's runner adds an exit stack, enters only
  when the signal changes, and by default computes signals on one-second synthetic bars, not hourly candles.
- **The two exceptions were already done by Claude.** `es_exit_policy_matrix_20261007.md` and
  `strategy_horizon_scan_20261008.md` replayed the runner's rules. Neither was cited in the 2026-10-30 diagnosis or
  the ED-002 review. The 2026-09-23 exit study said runner parity was needed before its results could be used, and the
  research engine labels its own output `signal_only_..._not_campaign_exit_stack`.
- **With the runner's rules the three default strategies still lose after costs on this data.** The losses and their
  causes change (table 4): breakout and EMA cross lose more, mean reversion loses less. The runner's 2% trailing stop
  closes most trades within hours, so trades and fees rise and the occasional large gain is cut short.
- **What the bot is actually set to run is none of the tested configurations** (section 1).
- **New engineering defects found** (section 6), one of which could leave positions unmanaged.

## 1. What the bot is set to run (SHOWN)
- **Runtime config** (`.cbp_state/runtime/config/user.yaml`, last modified 2026-10-11T18:33Z; read with owner
  approval on 2026-10-31, whitelisted `strategy_runner` keys only): strategy `momentum`; `signal_source:
  synthetic_mid_ohlcv`; `min_bars: 80`; `loop_interval_sec: 1.0`; symbols BTC/USD, ETH/USD, SOL/USD; venue coinbase;
  no stop, take-profit, trailing or hold settings, so the code defaults apply (the momentum preset sets none either).
- **Campaign launches override it.** `services/analytics/paper_strategy_evidence_service.py` (lines 573-583) sets the
  strategy and signal source through environment variables. The runner's last run on this computer (status file,
  stopped 2026-10-29T00:04Z, 63 loops, 0 orders) was `sma_200_trend`, preset `es_daily_trend_v1`, daily candles.
- **Local paper records** (`.cbp_state/data/intent_queue.sqlite`, read-only): the three default strategies traded only in
  March-April 2026 (breakout 3, EMA cross 2, mean reversion 65 round trips), with median holds of about 6 seconds,
  consistent with one-second synthetic bars. No hourly-candle paper run of them exists here. The last strategy order
  was 2026-07-09 (`sma_200_trend`; its three June-July exits were trailing stops, under an earlier exit setting).
- **Server:** as of 2026-10-11 (`server_workload_inventory_20261011.md`) the Coinbase EMA campaign was stopped
  (since 2026-09-12; 8 trades, -$2.32) and two daily EMA paper collectors ran. Current server state: UNVERIFIED (no access).
So "B, the actual bot's results" for the strategies backtested here does not exist; section 2 documents B's logic.

## 2. The runner's execution path (`services/execution/strategy_runner.py`, sha256 7006466d...)
| Step | Behaviour | Lines |
|---|---|---|
| Settings | `.cbp_state/runtime/config/user.yaml`. `config/trading.yaml` is not read by the runner, despite its comment. Exit settings: preset `risk`, then `strategy_runner.risk`, then `strategy_runner` keys; if unset, code defaults stop 3%, take-profit 6%, trailing 2%, 60-candle hold. The three default presets set none. | 316-440, 1087-1090 |
| Signal prices | Default `synthetic_mid_ohlcv`: one synthetic one-second bar per mid-price poll, volume 1.0. Only `public_ohlcv_<timeframe>` uses real candles. | 347-351, 620-641, 1290-1329 |
| Candles | With `public_ohlcv_*`, candles are fetched every loop including the one still forming (none dropped). The signal sees the last `min_bars` rows (default 60; config 80), not 300. | 855-866, 1232, 1287 |
| Loop | every `loop_interval_sec` (default and config: 1 s) | 367 |
| Entries | only when the decision changes; buy only when flat; the same action is not emitted twice in a row; the first signal after start does not trade unless `allow_first_signal_trade`. | 1339-1360, 1478-1513 |
| Exit stack | checked every loop while long, before the signal: stop 3%, then trailing 2% from the highest price seen since entry, then take-profit 6%, then 60 candles. The trailing level starts at the entry price, so it fires at -2% before the 3% stop can, except on a gap. | 1461-1476; `services/risk/exit_controls.py` 37-125 |
| EMA invalidation | inert: thresholds are read from the top-level settings, where they are never set (all 0). | 1436-1458 |
| Signal exit | a change to "sell" while long sells the whole position | 1482-1490 |
| Risk and kill switches | entry exposure limits; cool-down after repeated risk blocks, consecutive losing exits or drawdown | 1549-1660 |
| Orders | market-order intent of `qty` units (default 0.001), not a dollar amount; skipped if a strategy intent for the symbol is still queued or submitted. Consumers mark failures `rejected`; no retry found (`intent_consumer.py`, `live_intent_consumer.py`). The runner does not re-send the same action, so a rejected exit is not re-sent while its condition persists (UNVERIFIED by test; the subject of owner decision 3). | 368-369, 1512, 1667-1720 |
| Several symbols | the decision, exit and order block (from line 1331, indent 12) sits outside the `for symbol in symbols` loop (line 1135, body indent 16): each pass computes every symbol's signal but only the last symbol reaches the decision, exit and order code. SHOWN by reading; not tested. | 1135, 1331 |

## 3. Research engines against the runner
| | Research backtests of the bot's strategies | Runner |
|---|---|---|
| Bars | completed hourly (or 5m/daily) candles | 1-second synthetic bars by default; forming candle with `public_ohlcv_*` |
| Entry rule | buy whenever flat and the signal says buy | buy only when the signal changes to buy |
| Exits | signal sell only | exit stack every loop, then signal sell |
| Window | last 300 bars | last `min_bars` (60 default, 80 in config) |
| Size | $100 per entry | `qty` units (0.001 default) |
| Fills | next bar open, modelled fee and slippage | market order at the live price |
No engine in `services/backtest/` calls the exit stack (searched for stop_loss, take_profit, trailing_stop,
max_bars_hold, evaluate_strategy_exit_stack: 0 hits in 32 files).

## 4. Replay: the three default strategies, existing backtest (A) against runner rules (C)
Data: `research/multisymbol_baseline_v1` (OKX hourly; BTC, ETH, SOL, ADA, XRP; 2026-01-01 to 09-30; 32,760 coin-hours);
$100 per entry, 5 bps slippage per side. **A reproduces all 15 saved runs trade for trade, at every fee level (asserted).**
C uses the runner's code-default exits and change-only entries, signals on completed candles, and continuous
monitoring along an assumed path inside each candle (open-low-high-close if it closed up, else open-high-low-close),
filling at the trigger level; every exit is checked against the repository's `evaluate_strategy_exit_stack`.
C_close sees only candle closes (a lower bound on monitoring). Max drawdown is on the combined closed-trade $ curve.

| Strategy | Variant | Trades | Before fees | Net at 0.25% | Net at 0.60% | Fees at 0.25% | Win rate | Profit factor | Max drawdown | In market | Median hold |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Breakout | A | 310 | +$139 | -$16 | -$234 | $155 | 33% | 0.97 | $191 | 48% | 39 h |
| | C | 543 | +$140 | -$132 | -$512 | $272 | 31% | 0.77 | $180 | 19% | 6 h |
| | C_close | 458 | +$168 | -$62 | -$383 | $229 | 35% | 0.90 | $178 | 28% | 17 h |
| EMA cross | A | 129 | +$45 | -$19 | -$110 | $65 | 36% | 0.93 | $161 | 51% | 85 h |
| | C | 204 | +$38 | -$64 | -$207 | $102 | 29% | 0.72 | $87 | 8% | 8 h |
| | C_close | 200 | +$34 | -$66 | -$206 | $100 | 35% | 0.76 | $104 | 13% | 18 h |
| Mean reversion | A | 29 | -$148 | -$162 | -$182 | $14 | 45% | 0.37 | $208 | 51% | 552 h |
| | C | 87 | -$36 | -$79 | -$140 | $43 | 21% | 0.29 | $85 | 4% | 11 h |
| | C_close | 84 | -$58 | -$99 | -$158 | $42 | 24% | 0.34 | $106 | 7% | 20 h |

- The runner's change-only entry rule alone changes nothing here (variant T = A exactly), as the 2026-10-07 matrix found.
- The 60-bar window changes EMA cross and mean reversion slightly (net at 0.25%: -$69 and -$76) and breakout not at all.
- Exits under C: breakout 468 trailing, 53 take-profit, 11 time, 11 signal; EMA 175/19/7/3; mean reversion 80/2/4/1.
  Signal exits, and so the blocked-exit defect of the 2026-10-30 diagnosis, matter little under runner rules.
- Classification (POP): ineffective signal plus execution costs for all three; under runner rules also an exit design
  that cuts the trend (2% trailing on coins that move more than 2% in an hour). No result shows an advantage.

## 5. The 83 breakout trades that reached +6% (`breakout_83_trades.csv`)
Same entries as A; alternative exits replayed from each entry ($100 per trade, before fees).
| | Total | Median per trade |
|---|---:|---:|
| Best gain reached | +$1,040 | +8.8% |
| Realised by the backtest (signal exit) | +$509 | +3.6% |
| Given back after the best point | $531 | 5.5 points |
| Runner's exit stack (51 trailing, 28 take-profit, 4 time) | +$203 | +2.1% |
| Trailing 2% only | +$217 | +2.1% |
| Take-profit 6% only (signal exits kept) | +$489 | +5.9% |
| After the backtest's exit, 72 h later | 30 of 83 higher; median -0.8% | |
The runner's stack did better than the backtest's exit on 26 of 83. **These 83 were chosen because they went up 6%;
any exit capped at 6% looks good on them by construction.** The effect on all trades is table 4, not this table.

## 6. Defects found (for the engineering queue; owner decides)
1. Several symbols in one runner: only the last symbol's signal reaches the decision, exit and order code (section 2).
   The runtime config lists three symbols. Could leave positions in the other symbols without exit checks. Not tested.
2. EMA invalidation exits are inert (thresholds read from the wrong dictionary).
3. The default `signal_source` turns every strategy into a one-second strategy; nothing warns that this differs from
   the hourly or daily design the presets were tested on.
4. Signals on `public_ohlcv_*` use the still-forming candle; research uses completed candles.
5. `config/trading.yaml` says the runner reads it; it does not.
6. A rejected exit is not retried (known; owner decision 3).

**Addendum (2026-10-31, later; self-checked).** Defect 1 confirmed structurally with Python's parser: in `run_forever`,
the `for symbol` loop spans lines 1135-1330; the calls to `get_position`, `evaluate_strategy_exit_stack` and
`upsert_intent` (lines 1334, 1461, 1709) are outside it, while the signal calls (1282, 1329) are inside. The same
structure is in the 2026-07-01 version of the file (commit d65a19b01). The live path runs the same function
(`services/execution/live_trader_loop.py` lines 3-6). The only multi-symbol runner test
(`tests/test_strategy_runtime_runner.py`, startup venue guard) does not check decisions, exits or orders per symbol.
Still not shown by running the loop. On this computer the kill switch is armed (since 2026-09-23) and the system guard
is HALTED (2026-10-09); four old paper positions remain open in the paper ledger (SOL/USD, BTC/USD, ORCA/USD, ADA/EUR;
last updated April-May); server state UNVERIFIED.
**Correction (2026-10-31, later; O-10).** "The live path runs the same function" is true, but the runner writes only to
the paper intent queue and no production code moves strategy intents to any live store, so the defect is not a current
live exposure; it must be fixed before multi-symbol paper results are trusted and before live routing exists. See
`docs/research/capital_protection_audit_20261031/` CP-02. The owner's checks found no process running several symbols.

## 7. Which earlier conclusions could change
| Group | Ledger entries (configurations) | Effect |
|---|---|---|
| Bot strategies, signal-only | MULTISYMBOL_OKX (15), failure diagnosis 2026-10-30, breakout dissection 2026-09-23, REVERSAL_DIAGNOSTIC (unresolved count), CANDLE_DIAGNOSTIC (descriptive), ED-002 design | Describe the signals, not the bot. Here the verdict (no profit after costs) holds under runner rules; the amounts, the causes and the case for exit-unblocked variants change. |
| Bot strategies, runner rules already modelled | ES_EXIT_MATRIX (8), HORIZON_SCAN (40, both modes) | Stand; they are the precedent this audit should have followed. |
| Actual runner paper runs | ES_TRIAL, ES_V1_PAPER, EMA_CAMPAIGNS, BREAKOUT_CAMPAIGN | Real runner logic under whatever settings were active; small samples. |
| Research rules never implemented in the bot | the remaining ~680 (altcoin events, BTC/ETH trend family incl. the candidate, E6-E10, carry, attention, order book) | Not affected by this mismatch; also say nothing about what the bot would do. Trading any of them needs new code and its own parity check. |
No earlier document was changed; corrections are recorded here and in the failure diagnosis (C4).

## 8. Reproduce (for Codex)
From the repository root (Python 3.10+, numpy; read-only on the saved data):
```
python3 -I docs/research/exit_parity_audit_20261031/exit_parity_replay.py . out.json trades.csv b83.csv
python3 -I docs/research/exit_parity_audit_20261031/check_walker_bruteforce.py . docs/research/exit_parity_audit_20261031/exit_parity_replay.py out.json check.json
```
The first asserts A against all 15 saved runs. The second re-runs C with brute-force path stepping (2,000 points per
segment, the repository's exit function at every point) and compares. SHA256SUMS lists inputs and outputs.

Self-checks done (SHOWN): A matches all 15 saved runs (entry and exit prices, per-trade net at 10/25/60 bps). The
brute-force check (`walker_bruteforce_check.json`) gives the same 543/204/87 trades, entry bars and exit rules; exit
prices within 0.0024%; net at 0.25% within $0.13 per strategy. The replay rerun on the owner's computer (Python
3.10.12, numpy 2.2.6) produced byte-identical outputs. A first rerun differed in three drawdown figures because trades
closing in the same hour on different coins were ordered differently by numpy versions; the order is now fixed (exit
time, coin, entry) and the brute-force check, which compares trades and dollars only, is unaffected.
Requested checks: the runner reading in section 2 (especially the several-symbols block and the inert EMA exits),
the replay's entry and exit rules against the runner, and the numbers in tables 4 and 5.

## 9. Limits and unknowns
- In-sample, nine months, five coins, OKX USDT prices standing in for Coinbase USD.
- C cannot reproduce signals on forming candles or one-second synthetic bars; the intrabar path is assumed.
- Code-default exits are used; the active config sets none, but a campaign launch could (UNVERIFIED for future runs).
- Fixed $100 per entry, not the runner's unit quantity; risk and kill switches not modelled.

**Correction (2026-11-05, Claude; bot audit BA-23, omission O-106):** this audit set out to establish what the runner
actually trades, including entries, but it missed that the runner adds to open winning positions.
- A buy transition while a position is open and at least 1.5% in profit adds up to 2 more full-size entries. The
  presets' 0.5 size multiplier is unused.
- Each add resets the entry price, trailing peak and bars held for the whole position.
- The replays here, and `scripts/replay_runner_decisions.py`, model one entry per position, so a runner-versus-replay
  comparison will differ whenever adds occur.

Evidence: `docs/research/bot_audit_20261031/README.md`, BA-23. The text above is kept unchanged.

**Independent correction to that correction (2026-11-05T18:45:50Z, Codex; O-107):**
the claim above omitted the upstream `position_aware=True` default. The actual
shared runner decision refuses a buy while held in that mode, before reaching
scaling. Adds and reset-reference concerns remain conditional when that guard is
disabled, not proven default behavior. Six synthetic shared-decision cases
reproduce the distinction. Runtime configuration was not checked; no replay or
simulation policy was changed. Full evidence and limits:
`docs/research/claude_handoff_audit_20261105/README.md`.

What do I know that could change the owner's decision that I have not yet said?
The original missed branch is conditional; do not change simulation entries on
the basis of the unconditional correction above.

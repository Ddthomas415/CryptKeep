# E01 paper-evidence audit - 2026-10-02

AUDITOR (Claude, separate thread from the Codex sessions). Read-only inspection
of existing paper records. No backtest run, no config, campaign, order, credential
or deployment change. Not yet entered in the work log (that file had uncommitted
edits from another session at inspection time). State: INCOMPLETE for E01.

## Inputs

- `.cbp_state/data/paper_trading.sqlite`, SHA256
  `6017136a1b556f0da1fad6418d863cd42ad70198f670ad1276a4319ac233b310`
  (copied, queried on the copy).
- `.cbp_state/data/evidence/es_daily_trend_v1/signal_*.jsonl`.
- `.cbp_state/runtime/health/paper_sim_monitor.json` (ts 2026-10-02T00:05:09Z).
- Coinbase Exchange public daily candles, BTC-USDT, 2026-05-14..2026-05-28.
- Checkout `codex/research-bundle-proof` @ `620bc8dbe`, 3 behind `origin/master`
  `97c24c8e4`.

## Findings

1. SHOWN: every fill in the paper database (177 fills) was charged 7.5 bps,
   except one zero-fee fill. Venue recorded as coinbase for the candidate.
   Source is `user.yaml paper_trading.*` per `cost_assumptions.latest.json`.
   Whether 7.5 bps is achievable on the operator's account is UNVERIFIED; the
   official Coinbase Advanced fee table is behind login and was not retrieved.

2. SHOWN: the reported `es_daily_trend_v1` net realized PnL of 31.4369 USDT
   (10 round trips, BTC/USDT, 0.001 BTC each) comes from one round trip:
   buy 2026-05-18T19:02:49Z at 39,864.65, sell 2026-05-26T00:00:09Z at
   77,281.20, net +37.3287.
   - Coinbase BTC-USDT traded 76,051.30 to 77,761.07 on 2026-05-18. The buy
     price is about 48% below that day's low.
   - The signal record for that entry shows `price: 44800.0`, `sma_200: 42900.0`
     and carries no market-data provenance fields. These are not market values.
   - Same day the database also holds a BTC/USD buy at price 100.0, qty 1,
     fee 0, and a kraken ETH/USD sell tagged `ema_cross`.
   Root cause of the non-market price is NOT traced here.

3. SHOWN: excluding that round trip, the other 9 round trips total -4.9225
   gross and -5.8918 net at 7.5 bps. None is a net winner.
   Had the 2026-05-18 buy filled inside that day's real range, that trip's gross
   would be between -0.48 and +1.23 USDT, giving an all-history gross between
   -5.40 and -3.69. Whether a real-price signal would have fired at all is
   UNVERIFIED.

4. SHOWN: the 3 gate-qualified round trips (entries 2026-06-16, 06-21, 07-04)
   are all losses: net -1.9245, -1.6510, -0.7408; total -4.3163 USDT on about
   383 USDT traded notional. The gate count (3/5) is unaffected by finding 2,
   because the 2026-05-18 trip is already outside the cohort.
   Three trades are far too few to conclude the strategy loses.

5. SHOWN: fee sensitivity on the 10 recorded round trips (1,409.62 USDT traded
   notional, gross 32.4941): net is 31.44 at 7.5 bps, 24.04 at 60 bps, 15.58 at
   120 bps. All of it is the finding-2 trade, so these figures say nothing
   about real economics.

6. SHOWN: the daily signal has read long with `entry_allowed: true` on every
   day-end record from 2026-08-18 through 2026-10-02 (price 64,542 to 84,786,
   SMA200 63,902 to 71,409). Position flat, `enqueued_total: 0`, no fill since
   2026-07-09. Earlier flips to long on 07-26, 08-06 and 08-08 also produced no
   entry. The repo already tracks a completed-crossover entry correction as
   PR #602 (recorded OPEN in `mistakes_impact_review_20260930.md`); I did not
   verify that #602 fixes this or check its live state.

## Consequences

- There is no positive ACTUAL paper evidence for the candidate. The only
  positive results are CF-MODELLED backtests.
- Any report, dashboard or status line quoting pnl=31.4369 for
  `es_daily_trend_v1` is quoting finding 2.
- The gate cannot reach 5/5 while finding 6 persists, regardless of market.

## Not done

Actual fee tier and infrastructure cost (operator input needed). Challenger
databases and the Hetzner campaigns. Root cause for findings 2 and 6. Strategy
semantics and uninspected-data inventory (remaining E01 deliverables).

## Addendum - root cause of finding 6 (same day)

Read-only. Code read from `origin/master` @ `97c24c8e4`; the local working tree
has the same kill-gate lines. State read from a copy of
`.cbp_state/data/strategy_state.sqlite`.

7. SHOWN: the candidate has been locked out by a performance-kill cooldown since
   2026-07-09T00:03:59Z.
   - State: `loss_streak:coinbase:BTC/USDT:sma_200_trend = 3`,
     `kill_until:... = 51`, both written at the 2026-07-09 exit. Limits are 3
     consecutive losing exits and a 50-loop cooldown
     (`services/risk/performance_kill.py`).
   - `kill_until` is stored as an absolute loop number, but `loops` starts at 0
     in every runner process (`strategy_runner.py` `loops = 0`). Daily sessions
     run 63 loops, so loops 1-50 of every session are blocked.
   - The signal-change edge is recorded before the kill gate: on the first loop
     `last_action` is set to the new decision, then the gate skips the loop. By
     loop 51 `changed` is false, so no entry is emitted.
   - `kill_until` is only reset to 0 after an entry passes the risk check, which
     cannot happen. The lockout does not expire.
   - `paper_sim_monitor.history.jsonl` shows `kill_cooldown` followed by
     `signal_action=buy, signal_changed=false, action=None` on every day from
     2026-07-20 (earliest checked) to 2026-10-02.
   - Flips to buy on 07-26, 08-06, 08-08 and 08-18 were all lost this way.
   I found no mention of this in the work log, research docs or
   REMAINING_TASKS (searched: kill_cooldown, kill_until, loss_streak).

8. SHOWN: PR #602 (`5f9129a61`, open, GitHub reports merge conflicts with
   master) does not touch the kill gate and is opt-in with legacy as default.
   Merging it would not lift the lockout. With its policy enabled an entry could
   still fire after loop 50 on a crossover day, but only because sessions happen
   to run 63 loops.

9. Even with the lockout cleared, the legacy rule needs a hold-to-buy change.
   The signal has been buy since 2026-09-01, so no entry would occur until the
   signal next goes flat and returns to long.

The 3-loss streak that triggered the kill is real (the three cohort losses).
Whether a longer pause after three losses is desired is an operator decision;
the configured behaviour is a 50-loop cooldown, not an indefinite stop.
No state or code was changed. Any fix touches risk/execution code or campaign
state: HIGH risk, needs explicit authorization and independent review.

## Addendum 2 - strategy semantics, fees and uninspected data (same day)

Read-only. Code and spec read from `origin/master` @ `97c24c8e4`; artifacts read
from the local checkout. No backtest run.

10. SHOWN: the account fee rate is already recorded. Work log entry
    "2026-09-26: Separate-window breakout economic check" records maker 25 and
    taker 50 bps per side from Coinbase's authenticated transaction-summary
    endpoint. The paper engine charges 7.5 bps on market orders, so each
    paper fill under-charges by 42.5 bps per side against that taker rate.
    Finding 1's "UNVERIFIED" fee tier is superseded by this record; I did not
    re-query the endpoint.

11. SHOWN: four different rule sets carry the name `es_daily_trend_v1`.

    | Rule | Spec (`docs/strategies/es_daily_trend_v1.md`) | Gate baseline backtest | Paper runtime, 3 gate trades (Jun-Jul) | Paper runtime now |
    |---|---|---|---|---|
    | Entry | next open after close crosses above SMA200, regime permitting | same bar close, any bar long and flat | signal change seen in a daily session | same, locked by kill since 07-09 |
    | Exit | next open after close below SMA200 | same bar close when flat | runner default 2% trailing stop (all 3 exits record `trailing_stop`) | SMA flat only (#588) |
    | Hard stop | 2 x ATR(20) below entry | none | runner defaults | none; `compute_stop` has no caller outside its module |
    | Size | 0.5% capital at risk, 10% notional cap | all cash each trade | fixed 0.001 BTC | fixed 0.001 BTC; `compute_position_size` has no outside caller |
    | Cost per side | not stated | 10 bps fee + 5 slippage | 7.5 + 5 | 7.5 + 5 |
    | Loss kill | not in spec | none | 3 losing exits, 50-loop cooldown | same |

    The trailing-stop mismatch is already recorded and fixed
    (`docs/checkpoints/managed_exit_risk_audit_2026_09_08.md`, #588). That
    record says deployment "must assess ... evidence segmentation".

12. Consequence, SHOWN from 11: the three gate-qualified round trips were
    closed by an exit rule the strategy no longer has, and those three
    trailing-stop losses are what armed the kill in finding 7. The gate still
    counts them as 3/5 for the current rule set. The gate's comparison
    baseline (win rate 22.6%, avg win +78.7%, avg loss -4.1%) comes from an
    all-cash, same-close, no-stop simulation, which is not the rule set that
    produced the paper trades.

13. Uninspected data for the unchanged candidate: effectively none.
    - `backtest_expectations` uses Coinbase BTC/USD daily 2018-01-01 to
      2026-06-04.
    - `daily_trend_cash_comparison_2026_09_23.md` uses the archive through
      2026-07-31.
    - `.cbp_state/data/research/daily_trend_recent_20260926/result.json`
      evaluates 2025-09-26 to 2026-09-25 at 50 bps: SMA200 signal-only, 100 USD
      entries, 4 closed trades, 0 net winners, +8.03 USD after a hypothetical
      terminal sale of an open position (buy-and-hold -23.84).
    BTC daily history has therefore been inspected through 2026-09-25. Only
    days after that are untouched. New independent evidence can only come from
    forward paper trading, which finding 7 currently prevents.
    The `es_continuous_20260928` result cited by the 2026-10-01 checkpoint lives
    outside the connected folder and was not read.

## E01 status after this audit

- Fees: recorded (10). Infrastructure cost: still needs operator input.
- Semantics: not one strategy but four (11). Needs an operator decision on
  which rule set is the candidate before any further economic claim.
- Uninspected data: none of substance (13).
- Actual evidence: no net-winning paper trade at a real price (2-4).
State: INCOMPLETE. No profitability finding is made or upgraded.

## Addendum 3 - fee attribution on recorded paper fills (same day)

Read-only arithmetic on copies of the local paper databases. No fill, fee,
config or gate value was changed. No backtest run.

Inputs: BTC/USDT fills from `.cbp_state/data/paper_trading.sqlite` (SHA256
prefix 6017136a1b556f0d), `.cbp_state_challengers/breakout_default_daily`
(adff9ccf35a44526) and `.cbp_state_challengers/ema_cross_default_daily`
(62090bb4b65f2a97). Coinbase Exchange public BTC-USDT daily candles
2026-04-15 to 2026-09-05, 144 contiguous days. Fee per side: 7.5 bps as
recorded, and 50 bps (taker rate from the 2026-09-26 work log entry; all paper
orders are market orders). The 5 bps slippage already inside recorded fill
prices is left as is. FIFO round trips, 0.001 BTC each.

14. SHOWN: price check. Every fill price was compared with the Coinbase low and
    high for its UTC day, with 20 bps tolerance. 48 of 49 fills pass. The only
    failure is the 2026-05-18 buy at 39,864.65 (finding 2).

15. SHOWN: results by campaign.

    | Campaign | Round trips | Gross | Net at 7.5 bps (recorded) | Net at 50 bps | Net winners at 50 bps |
    |---|---:|---:|---:|---:|---:|
    | es_daily_trend_v1, all | 10 | +32.49 | +31.44 | +25.45 | 1 |
    | es_daily_trend_v1, market-price trades only | 9 | -4.92 | -5.89 | -11.38 | 0 |
    | breakout_default | 12 | +3.68 | +2.51 | -4.10 | 2 |
    | ema_cross_default (local, through 2026-06-19) | 2 | +0.22 | +0.04 | -1.00 | 0 |

    Figures in USDT. ema_cross_default has one open buy not counted; its later
    fills are on Hetzner and were not read.

16. SHOWN: breakout_default changes sign at the recorded taker rate. Its gross
    is +3.68 on 1,555.04 traded notional; fees are 1.17 at 7.5 bps and 7.78 at
    50 bps. One trade (2026-08-20 to 08-22, take-profit exit, +8.79 gross)
    exceeds the campaign's whole gross; the other 11 sum to -5.11 gross.

17. SHOWN: 10 of the 24 round trips opened and closed on the same UTC day,
    most within minutes (6 candidate, 3 breakout, 1 ema_cross). None is a net
    winner at either fee. They are not daily-bar behaviour; their cause was not
    traced here.

Limits: 23 market-price round trips in total, one venue, one symbol, about five
months. This is too few to rank strategies or to conclude any of them loses.
It does show that no local paper campaign has a positive net result at the
recorded taker fee once the non-market fill is set aside. Maker execution
(25 bps) is not what the paper engine simulates and was not modelled.

## Addendum 4 - origin of the non-market fill and of the test records (same day)

Read-only. Evidence directory `.cbp_state/data/evidence/es_daily_trend_v1/` and
a copy of the paper database. No test was run on this machine.

18. SHOWN: 19,151 of the 35,495 signal records in the candidate's evidence
    directory are test-fixture values (price below 5,000, missing SMA, or the
    44,800 / 42,900 pair). They fall on 16 days between 2026-04-20 and
    2026-05-26, plus 2 records on 2026-09-20. On 2026-05-18 alone, 9,724 of
    9,764 records are fixtures (prices 98.2 to 101.0), written in bursts at
    08, 14 and 19 UTC under six different commit stamps. Test runs were
    writing into the production evidence directory.

19. SHOWN: the same day's paper database rows match those bursts: a BTC/USD buy
    at price 100.0, qty 1, fee 0 at 08:26, and a kraken ETH/USD `ema_cross`
    sell at 14:36. The campaign session that produced the non-market buy
    (finding 2) ran 19:02:47 to 19:04:51, inside the 19 UTC burst. All 20 of
    its own signal records carry price 44,800 and SMA 42,900 and no market-data
    provenance. So that session did not trade on market data. Which component
    supplied the 44,800 input and the 39,864.65 fill price was NOT traced; the
    value 44,800 does not appear in the repo's Python, JSON or YAML sources.

20. SHOWN: the leak is mostly historical. After 2026-05-26 the paper database
    holds only the six cohort orders, and no fixture record appears on any day
    from 2026-09-21 to 2026-10-02 although tests were run in that period. The
    two 2026-09-20 records (price 310.0, SMA 210.5, commit a39c44208) were
    written at 20:30:01 UTC and carry `market_data_source: public_ohlcv`; they
    coincide with the test-isolation repair recorded in the work log that day.
    Whether any current test can still write to production state is UNVERIFIED.

21. Consequence. Figures built on all-history records are contaminated: the
    monitor's `net_realized_pnl_total` 31.4369, `fills_total` 20,
    `closed_trades_total` 10, `jsonl_evidence.total_records` 36,124 and the
    paper equity series (realized -1,018.47 includes test rows). The
    provenance-qualified gate count (3) uses only post-2026-06-16 fills and is
    not affected by these records as far as I checked; I did not re-derive the
    gate's qualified-bar or days-recorded counts.

No record was deleted, relabelled or corrected. Any change to reporting is a
separate reviewed change and must keep the historical rows.

## Addendum 5 - live-execution flags on the laptop (same day)

Read-only. Code read from `origin/master` @ `97c24c8e4`; state read from the
local folder. No config, arming state or kill switch was changed. Process
environments and the Hetzner host were not inspected.

22. SHOWN: `config/user.yaml` (untracked, last modified 2026-08-14) contains
    `live_execution: {enabled: true, armed: true}` and
    `execution: {live_enabled: true}`.
    - Nothing in `services/`, `scripts/` or `dashboard/` reads a
      `live_execution` config block. Those two values have no effect.
    - `execution.live_enabled` IS read (`live_arming.is_live_enabled`), so the
      config-level live switch is on.

23. SHOWN for the stored state and the repo `.env` only (corrected after
    Codex's review; this does NOT establish that live trading cannot fire):
    as of 2026-10-02 two other layers were in the blocking position:
    - Kill switch: `.cbp_state/runtime/kill_switch.json` is armed (stop_bot,
      2026-09-23). `place_order` refuses with `kill_switch_on` before anything
      else.
    - Arming: `place_order._is_armed` needs CBP_EXECUTION_ARMED,
      CBP_LIVE_ENABLED or CBP_EXECUTION_LIVE_ENABLED set truthy. The repo
      `.env` defines none of them. The consumers use
      `live_enabled_and_armed`, which falls back to
      `.cbp_state/data/live_arming.json`: armed false (live_disable_wizard,
      2026-09-23), and a persisted value older than 300 s is rejected. That
      expiry applies to the persisted value only. An arming environment
      variable set truthy in a running process or deployment unit overrides
      it with no expiry, and `place_order._is_armed` checks only those
      variables.
    - History: `live_trading.sqlite` holds 8 live orders, all on 2026-04-11 and
      all `rejected`, and 0 live fills.

24. Consequence, limited to what was inspected: `execution.live_enabled: true`
    means the config file does not hold live trading off. In the stored state
    and repo `.env` inspected, the kill switch file was on and the persisted
    arming state was off. Whether live submission is possible in a running
    process is NOT established by that. The roadmap states no live activation
    is authorized. Setting `execution.live_enabled` to false and removing the
    unused `live_execution` block would make the config match that; this is a
    config change (HIGH risk) for the operator to decide and was not done.

25. SHOWN (added 2026-10-02 after Codex's review): arming paths and process
    status files.
    - On `origin/master` @ `97c24c8e4`, the only code that sets an arming
      environment variable is `services/admin/live_enable_wizard.py` and
      `services/admin/resume_gate.py` (both set CBP_EXECUTION_ARMED in their
      own process and write persisted armed=True); `services/execution/
      live_enable.py` writes persisted armed=True. No tracked shell script,
      Makefile, plist, systemd unit, YAML or env example sets one; the systemd
      template and `cbp.env.example` say it must be absent.
    - Status files that the processes write themselves, in
      `.cbp_state/runtime/flags/`: `live_consumer` last wrote 2026-05-07 and
      `live_intent_consumer` 2026-05-15, both `blocked: live_disabled`;
      `live_reconciler` last wrote 2026-05-15 `halted`; `intent_executor` and
      `pipeline` report `stopped`; `system_guard.json` records
      `supervisor_stop` on 2026-09-23. None of the live-path status files has
      been written since `config/user.yaml` was changed on 2026-08-14.
    - This is evidence that no live-path process on this machine has reported
      since May. It is not a process listing. UNVERIFIED: the actual process
      table and environments on the laptop; untracked local launch scripts;
      `/etc/cbp/cbp.env`, units and state on Hetzner. Live submission is
      therefore not excluded.

## Addendum 6 - risk limits the runner actually enforces (same day)

Read-only. Code read on `origin/master` @ `97c24c8e4`; config read from the
local checkout.

26. SHOWN: `services/execution/strategy_runner.py::_cfg()` returns no `risk`
    key. `build_risk_limits`, `build_kill_limits`, `build_scaling_limits` and
    `build_performance_limits` each read `cfg.get("risk")`, so all four run on
    their code defaults whatever a config file or preset says. Only the four
    exit controls (stop loss, take profit, trailing stop, max bars held) are
    carried through, by `_resolved_exit_controls`.

27. SHOWN: the `es_daily_trend_v1` preset (`services/strategies/presets.py`)
    declares limits that differ from those defaults and are therefore not
    enforced:

    | Limit | Preset | Enforced |
    |---|---|---|
    | max_concurrent_positions | 1 | 5 |
    | max_symbol_exposure_pct | 10 | 20 (inert, see 29) |
    | max_total_exposure_pct | 10 | 80 (inert) |
    | max_strategy_exposure_pct | 10 | 50 (inert) |
    | max_consecutive_risk_blocks_per_symbol | 3 | 5 |
    | kill_cooldown_loops | 5 | 20 |

    The preset does not set the scaling or performance-kill limits, so those
    would stay at defaults either way (scaling enabled, 2 adds; 3 losing
    exits; 10% drawdown; 50-loop performance cooldown). The ten other presets
    carry the same values as the code defaults. The local `config/user.yaml`
    has no `strategy_runner` or `risk` block.
    This is a fifth place where the candidate as written and the candidate as
    run differ (see findings on rule sets in Addendum 2).

28. SHOWN: `PaperEngine.mark_to_market` records `equity_quote` as cash plus
    the position of the one symbol being marked. With one symbol this is the
    account equity. With several it understates it, and the newest row is
    whichever symbol was marked last.

29. SHOWN (already in the work log, restated for completeness): on master the
    three percentage limits never refuse, because `summarize_exposure` is
    never given exposure figures.

UNVERIFIED: the config and environment on Hetzner.

## Addendum 7 - provenance of the open paper positions and pricing inputs (2026-10-03)

Read-only. Paper account read from a copy of
`.cbp_state/data/paper_trading.sqlite` taken 2026-10-03 00:2x UTC; nothing in
the account was changed. Code read on `origin/master` @ `97c24c8e4`.
Requested by Codex's rev15 review: establish ownership of the stale positions
and what a current-equity figure could be priced from.

30. SHOWN: none of the four non-zero position rows is supported by the fills
    ledger of the same database.

    | Symbol | Position row | Fills for the symbol | Net of fills |
    |---|---|---|---|
    | SOL/USD | 1.0 @ 85.63, written 2026-04-11 22:26:56 | 22, all 0.001, last 2026-03-26 | 0 |
    | BTC/USD | 1.0 @ 100.0, written 2026-05-18 08:26:54 | 46 | -1.0 |
    | ORCA/USD | 0.001 @ 9.068..., written 2026-04-13 02:58:18 | 2 buys of 0.001 | 0.002 |
    | ADA/EUR | 0.001 @ 9.068..., written 2026-04-13 02:58:27 | 1 buy of 0.001 | 0.001 |

    - SOL/USD: no fill exists at or near the time the row was written, and no
      fill of size 1.0 exists for the symbol at all. The row was written
      without a fill. Which process wrote it is UNVERIFIED.
    - BTC/USD: the last fill is `client_order_id = paper-buy-preset-1`, 1.0 at
      exactly 100.0, fee 0, strategy `sma_200_trend`. That client id appears in
      the repository only in `tests/test_paper_engine_integration.py:685`
      (already recorded as test contamination in Addendum 4).
    - ORCA/USD: two buys of 0.001 but the row holds 0.001.
    - ADA/EUR: the quantity matches its one fill, but the fill price is
      9.068031750000001, identical to 15 digits to the ORCA/USD, LTC/USD,
      LINK/EUR and XRP/EUR fills of the same hours (11 fills across five
      symbols share that price). It is not an ADA/EUR price.
    - None of the four orders carries the campaign's symbol (BTC/USDT). Three
      have `strategy_id` NULL.

31. SHOWN: the account's cash is not the result of trading. The first equity
    row (2026-03-19) records cash 123.45. The last row before 2026-04-11
    22:45:17 records 121.86. At 22:45:17 a sell of 2.0 BTC/USD filled at
    73,025.27 and cash became 146,062.87. Fills for BTC/USD up to that moment
    net to about zero, so the 2.0 sold were not bought through this ledger;
    in the same second an order `paper_intent_smoke-test-intent-1` was
    rejected. Cash today is 148,245.72 and recorded realized PnL is -1,018.47.
    About 146,000 of the equity any percentage limit would be measured
    against comes from that one sale.

32. SHOWN: the paper engine's price lookup is not symbol-exact.
    `services/market_data/tick_reader.py::get_best_bid_ask_last` looks for a
    tick matching venue and symbol and, when there is none, returns the
    venue-level quote from the snapshot whatever symbol that quote is for.
    The snapshot on 2026-10-03 holds one tick, coinbase BTC/USDT at about
    84,515, and the venue-level row carries the same quote. Asked today for
    SOL/USD, ORCA/USD, ADA/EUR or BTC/USD it would return about 84,515.
    The recorded fills show this has happened: one price shared by five
    symbols (finding 30), and XRP/EUR fills ranging from 9.07 to 77,220.81.

33. Consequence for a marked-to-market equity figure (analysis, not a change):
    - With the existing lookup, marking the four positions today would value
      SOL/USD 1.0 at about 84,515 and would be wrong for every symbol except
      BTC/USDT.
    - The positions are quoted in USD, EUR and USDT; cash is one number with
      fees recorded as USDT. No conversion exists in the paper engine.
    - A usable current-equity figure therefore needs, as a minimum: a quote
      matched to the exact symbol, an age limit on that quote, one quote
      currency (or a stated conversion), and refusal when any held position
      cannot be priced. On this account that rule would refuse every
      multi-symbol entry, because three of the four held symbols have no quote.

34. Consequence for patch 0008 (preset limit of one position): the four rows
    that would block every ES entry are not campaign positions and are not
    supported by fills. That supports Codex's recommendation to hold 0008. It
    does not by itself decide what to do with the rows.

UNVERIFIED: who or what wrote the SOL/USD row and the pre-sale BTC/USD
quantity; the state on Hetzner; whether any other paper database is used by a
running campaign.

## Addendum 8 - what the strict market-quality template would have blocked (2026-10-03)

Read-only. Supports backlog item 29 (REMAINING_TASKS.md), which keeps the
market-quality guard's code defaults permissive until the strict template has
been applied to the campaign config and one cycle observed without
false-block storms. This is a look back at recorded evidence. It is not that
observed cycle, and no config was changed.

Source: `.cbp_state/data/evidence/es_daily_trend_v1/signal_*.jsonl` on the
laptop, 140 daily files, 35,557 signal rows. The runner began recording the
guard's result with each signal on 2026-05-29; 2,304 rows on 119 days carry
it (2,178 rows on 103 days since cohort start 2026-06-16).

35. SHOWN: applying the thresholds of `config/templates/market_quality_strict.yaml`
    (quote required, bid and ask required, BTC/USDT spread at most 20 bps,
    quote age at most 120 s) to those 2,304 rows:

    | Outcome under the strict template | Rows |
    |---|---|
    | Pass | 2,301 |
    | Blocked as stale, passed under current defaults | 2 |
    | Blocked as stale under current defaults too | 1 |
    | No quote | 0 |
    | Bid or ask missing | 0 |
    | Spread too wide | 0 |

    Largest recorded spread 10.6 bps (median 2.3). Median quote age 1.6 s.
    The three stale rows: 2026-07-23 00:40 (129 s), 2026-07-28 00:15 (245 s),
    2026-07-29 01:18 (946 s). None falls on a day with an order; the order
    days in the period are 06-16, 06-18, 06-21, 06-24, 07-04 and 07-09.

36. SHOWN: in all 2,303 rows with a price, the quote used differs from the
    signal price of the same row by at most 0.14%.
    CORRECTED 2026-10-03 after Codex's reconciliation: this is consistent
    with the quotes being BTC/USDT quotes, but it is not independent proof of
    the symbol, because the quote and the signal price may share a source.
    The earlier wording ("were BTC/USDT quotes ... the wrong-symbol fallback
    therefore did not affect these rows") overstated it and is withdrawn.

37. Limits. These are checks made at signal time by the strategy runner, not
    at order time by the paper engine. There have been no orders since
    2026-07-09 (session lockout, finding 6), so no order-time evidence exists
    for the period after that. Rows before 2026-05-29 carry no guard result.
    Hetzner evidence was not inspected. The paper engine separately refuses
    orders when the snapshot is more than 5 s old; that check is unchanged
    by the template.

Reading: on this evidence the strict template would not have produced a
false-block storm for the ES campaign: 3 of 2,304 signal checks blocked, all
for a quote older than two minutes, none on an order day. Whether to apply
the template to the campaign config and run the observed cycle is the
operator's decision under item 29.

## Addendum 9 - E01 closing statement: evidence against costs (2026-10-03)

AUDITOR. Arithmetic on existing artifacts only; no new backtest, no new data,
no campaign or config change. Not a profitability finding and not advice to
allocate capital. Whether to tick E01 on the checklist is the coordinator's
and operator's call.

Inputs
- Infrastructure cost: operator stated "under $10" per month on 2026-10-03
  (a range, not a bill; CLAIMED). Figures below use 10 as the upper bound and
  show 5 and 2.5 for sensitivity. USDT is treated as equal to USD.
- Fees: Coinbase taker 50 bps, maker 25 bps per side (work log 2026-09-26,
  verified by Codex). The paper engine charges 7.5 bps.
- Rule set: the documented crossover entry rule (operator decision recorded
  in the work log). Finding 11 stands: the paper campaign ran a different
  rule set (runtime exits), so actual and modelled results below are not the
  same strategy.
- Size: 0.001 BTC per entry, about 62-66 USDT at the June-July fills and about
  84.5 at the 2026-10-03 quote.

38. ACTUAL (paper, gate-qualified, since cohort start 2026-06-16). SHOWN from
    2_e01 fee attribution: 3 round trips, all losses.

    | Measure, 23 days 2026-06-16 to 2026-07-09 | USDT |
    |---|---:|
    | Gross | -4.03 |
    | Net at recorded paper fee (7.5 bps) | -4.32 |
    | Net at verified taker fee (50 bps) | -5.94 |
    | Buy and hold 0.001 BTC over the same window, gross | -4.18 |
    | Buy and hold, net of one round trip at 50 bps | -4.82 |
    | Cash | 0.00 |
    | Infrastructure for the 23 days at 10 / 5 per month | -7.56 / -3.78 |

    No trade since 2026-07-09 (session lockout, finding 6). Three trades are
    not a statistical sample.

39. MODELLED (existing artifacts, 50 bps fee + 5 bps slippage per side,
    signal-only SMA200, 1,000 initial account, fixed entry notional):
    - Three-year continuous sample (economic_feasibility_checkpoint_20261001):
      net 3.36 USDT per month per 100 of entry size, including a hypothetical
      terminal liquidation. Excluding the largest closed winner, closed net at
      100 entry is 2.64 in total over three years.
    - Most recent 12 months (daily_trend_recent_20260926): net +8.03 per 100
      entry, 0.67 per month; 4 closed trades, 0 net winners; the positive
      figure is an open position marked at the end. Buy and hold -23.84, cash
      0. Daily-close drawdown 2.56%, mean exposure 2.15% of the account.
    - Full 2018-2026 sample at 60/10 bps (daily_trend_cash_comparison):
      SMA200 +416.55 against buy and hold +733.51 on 100 entry; drawdown
      21.2% against 38.4%; exposure 7.3% against 33.1%.

40. Modelled monthly net against infrastructure cost, by entry size (linear in
    entry size; sizes above 500 are extrapolation beyond the existing
    scenarios, and 1,490 exceeds the modelled 1,000 account):

    | Entry size USDT | 3-year sample, per month | Recent 12 months, per month |
    |---:|---:|---:|
    | 62 (June-July fills) | 2.09 | 0.42 |
    | 84.5 (today) | 2.84 | 0.57 |
    | 100 | 3.36 | 0.67 |
    | 300 | 10.09 | 2.01 |
    | 500 | 16.82 | 3.36 |

    | Infrastructure per month | Entry size to cover it, 3-year sample | Recent 12 months |
    |---:|---:|---:|
    | 2.5 | 74 | 372 |
    | 5 | 149 | 745 |
    | 10 | 297 | 1,490 |

41. Reading.
    - Actual evidence: negative. Net of real fees the campaign lost more than
      holding the coin over the same days, and both lost against cash.
    - Modelled evidence: positive before infrastructure, small, and resting on
      few trades (one winner in the three-year sample; an unrealised position
      in the recent one).
    - At the present size the modelled result covers infrastructure only if
      that cost is below about 2.1 to 2.8 per month on the three-year sample,
      or about 0.4 to 0.6 on the recent twelve months. At 5 to 10 per month it
      does not.
    - Covering 10 per month needs an entry size near 300 on the three-year
      sample. That is a statement about arithmetic, not a recommendation to
      increase size: the same artifacts say not to scale from these results,
      and no actual trade supports it.

E01 proof items, as listed in ROADMAP_TRACKING_CHECKLIST.md
- Results classified actual / modelled: done (38, 39).
- Complete rules: four rule sets identified; operator chose the documented
  crossover rule; paper evidence ran another (findings 11, 27).
- Cost assumptions: fees verified; paper engine fee differs (finding 10).
- Cash and buy-and-hold comparisons: done (38, 39).
- Drawdown and exposure: modelled only (39). No meaningful actual figure from
  three trades.
- Capital basis: modelled 1,000. The paper account's cash is not a usable
  basis (finding 31).
- Infrastructure cost: operator range, not a bill (above).
- Evidence limitations: findings 2-4, 6, 11, 30-32, 37 and the limits above.

State: the audit's inputs are complete. Result: the candidate is NOT
economically qualified on existing evidence. No profitability claim is made.
UNVERIFIED: the actual infrastructure bill; Hetzner evidence; the modelled
artifacts' underlying simulations, which were not rerun here.

## Addendum 10 - corrections, cash provenance and account options (2026-10-03)

Read-only. Responds to docs/research/conversation_bundle_reconciliation_20261002.md
(Codex). The paper account was read from a fresh copy
(.cbp_state/data/paper_trading.sqlite, SHA256 086737d8269be200...); nothing in
it was changed. No option below was executed.

42. CORRECTION to Addendum 9 (my omission). Addendum 9 treated the laptop's
    records as the only actual evidence. The work log records a separate,
    human-approved isolated trial that I did not take into account:
    - "Corrected ES prospective" trial on Hetzner, own state directory
      (.cbp_state_challengers/es_corrected_prospective_v1), seeded config with
      starting cash 10,000 USDT, quote currency USDT, qty 0.001, the four exit
      controls at zero. Launched 2026-09-12; evaluation 2026-09-13 to a fixed
      end 2026-10-13 00:00 UTC (work log, "Human-Approved Isolated ES Trial
      Launch").
    - Recorded state through 2026-09-28: sessions completing daily, signal
      BUY unchanged, zero intents, fills and closes (work log 2026-09-19 and
      2026-09-28 entries). The operator's crossover-entry decision came out
      of that diagnosis.
    - CLAIMED from the work log; I cannot reach Hetzner and did not inspect it.
    Consequence: a clean capital basis for the candidate already exists there.
    Addendum 9's line "Capital basis: ... not a usable basis" applies to the
    laptop account only. Addendum 9's arithmetic is unchanged. Its closing
    line is narrowed: E01 is not closed by this audit; the trial's result at
    its fixed end is actual evidence still to come, and with no fills so far
    it may be "insufficient evidence".

43. SHOWN: cash provenance reproduced. Replaying all 177 fills in time order
    from the first recorded cash (123.45 on 2026-03-19) gives 148,245.72,
    equal to the stored cash to the cent. So the stored cash is exactly what
    the fills ledger implies; what is wrong is the fills.
    - Two sells had no fill-supported holding: 2.0 BTC/USD at 73,025.27 on
      2026-04-11 and 1.0 ETH/USD at 2,103.59 on 2026-05-18. One buy is the
      test-fixture order `paper-buy-preset-1` (1.0 BTC/USD at 100.0).
    - Replaying without those three leaves cash 302.70, still not the
      starting 123.45: the remainder comes from fills priced with another
      symbol's quote (finding 32), for example XRP/EUR sold at 77,220.81.
    - The ledger's net positions (LINK/EUR 0.003, ORCA/USD 0.002, ADA/EUR
      0.001, XRP/EUR 0.001) do not match the position table (SOL/USD 1.0,
      BTC/USD 1.0, ORCA/USD 0.001, ADA/EUR 0.001).
    Reading: there is no "correct" figure this account can be adjusted back
    to. Neither the cash nor the positions can be made valid by removing a
    known set of rows.

44. Account options, originals preserved in every case (for the operator;
    none executed, none is a recommendation to restart or reset a campaign):

    A. Declare the laptop account non-evidentiary. Keep the file untouched as
       an archive. Take candidate evidence only from isolated state
       directories, as the Hetzner corrected trial and the challengers
       already do. No code change. Open point for the operator: the three
       gate-qualified round trips since 2026-06-16 were recorded in this
       account. Their per-trade prices sit inside Coinbase's daily range
       (finding 4) and do not depend on the account's cash, but they ran
       under runtime exit rules (finding 11). Whether they stay in the cohort
       is a gate decision, not an accounting one.

    B. A new isolated account for any further laptop campaign: its own
       CBP_STATE_DIR, a seeded config that declares starting cash and quote
       currency, the original account left where it is. This is the existing
       mechanism (scripts/research/build_es_trial_package.py; the managed
       campaign planner's per-campaign state_dir), not a new one. It would
       also give patch 0009 a declared cash currency and remove the stale
       rows that make patch 0011 refuse every entry. Cohort continuity is the
       operator's decision.

    C. Compensating entries in the existing account (copy first, then append
       adjusting records). Not supported by the evidence: finding 43 shows
       there is no valid target state to adjust to, and it changes history.

    D. Rebuild the account from its fills into a new file. Not supported:
       the fills themselves include unsupported and mispriced ones (43).

    On the evidence, A with B is the only pair that leaves history intact and
    yields a valid capital basis. Narrowing the risk scope to hide the rows,
    or deleting them, is not among the options (reconciliation, "Accepted
    direction").

45. Contract gap in patch 0009, confirmed. It takes the account currency from
    the entry symbol. The paper engine has a declared one
    (`paper_trading.quote_currency`, default USDT). Proposed revision, not
    built: require the entry symbol's quote currency to equal the declared
    account currency, and refuse otherwise. Pending entries are still valued
    at their queue-time price; that remains a stated limit.

UNVERIFIED: everything about Hetzner in finding 42; who wrote the unsupported
position rows; whether any other process uses the laptop account.

## Addendum 11 - how long the candidate takes to produce evidence (2026-10-03)

Read-only arithmetic on an existing artifact; no new backtest, no new data.
Purpose: the "sample feasibility" input that roadmap item E02 requires, and
the waiting cost for E01. Not a forecast.

Source: `.cbp_state/data/research/daily_trend_comparison_20260923.json`
(dataset SHA256 640957cb...), the dated trade list of its `sma200_signal_only`
arm: Coinbase BTC/USD daily, 2018-07-20 to 2026-07-31 (2,933 days), entry on a
completed-close crossover executed at the next open. MODELLED. This is the
closest existing artifact to the operator's chosen entry rule; it has no
regime filter, ATR stop or runner exit stack, and its archive provenance is
recorded there as not independently verified.

46. SHOWN: entries are rare and clustered.
    - 31 entries and 31 exits in 8.03 years: 3.86 round trips a year.
    - By year: 2019 2, 2020 4, 2021 9, 2022 0, 2023 3, 2024 5, 2025 8.
    - Gap between consecutive entries: median 30 days, longest 388; five gaps
      exceed 180 days and two exceed a year.
    - Holding time: median 5 days; 20 of 31 round trips lasted a week or less;
      the longest 385 days. Seven of 31 were net winners at 10/5 bps.

47. SHOWN: share of windows, started on every day of the sample, that contain
    at least one event:

    | Window | At least one entry | At least one completed round trip |
    |---|---:|---:|
    | 30 days | 21.2% | 17.4% |
    | 90 days | 46.1% | 36.7% |
    | 180 days | 72.8% | 57.5% |
    | 365 days | 98.3% | 85.4% |

    Days from a start day to the k-th round trip entered after it:

    | Round trips needed | Median days | Shortest | Longest | Reached within 365 days |
    |---:|---:|---:|---:|---:|
    | 1 | 154 | 1 | 603 | 78% of start days |
    | 2 | 245 | 4 | 616 | 66% |
    | 5 | 473 | 42 | 1,006 | 27% |

    (9% to 17% of start days, those late in the sample, never reach the
    count before the data ends and are counted as not reached.)

48. Reading, against what is running.
    - The isolated Hetzner trial is a 30-day window. On this history about
      four in five 30-day windows contain no entry at all. Zero fills through
      2026-09-28 (work log) is the usual outcome for this rule, not by itself
      a sign of a fault. The recent-12-month artifact shows the model already
      long from 2026-08-20, which fits a signal that stays BUY with no fresh
      crossover.
    - The paper gate needs 5 qualified round trips and stands at 3 of 5. Two
      more took a median of 245 days in this history; five from scratch took
      a median of 473 days and arrived within a year for about a quarter of
      start days.
    - Waiting cost at the operator's stated range: 245 days is about 8 months,
      40 to 80 at 5 to 10 per month; 473 days is about 15.5 months, 78 to
      155. Addendum 9 put the modelled net at today's size at roughly 0.6 to
      2.8 per month.
    - So on existing artifacts the candidate, at its present size, costs more
      to observe than it is modelled to earn, and reaching the gate's sample
      takes most of a year or longer. That is an input for the E03 decision
      (continue, revise or retire); it is not that decision.

Limits: one asset, one history, clustered entries, so the percentages are
descriptive of this sample and not probabilities for the future. Signal-only
model; the runner's own rules differ (finding 11). The 2018-2026 archive's
original collection is not independently verified.

## Addendum 12 - CORRECTION: I read the wrong config file (2026-10-03)

Read-only. This withdraws part of Addendum 5 and corrects Addendum 6. The
error is mine and was not caught in review.

49. SHOWN: the code does not read `config/user.yaml`.
    `services/admin/config_editor.py` sets
    `CONFIG_PATH = config_dir() / "user.yaml"`, and
    `services/os/app_paths.py::config_dir()` is `<state root>/runtime/config`.
    On the laptop the effective file is therefore
    `.cbp_state/runtime/config/user.yaml` (120 lines, last modified
    2026-09-23 04:09, SHA256 25c7529747aabaf8...). No code in `services/`,
    `scripts/` or `dashboard/` loads the repository's `config/user.yaml`.

50. WITHDRAWN: finding 22's statement "the config-level live switch is on" and
    finding 24's "`execution.live_enabled: true` means the config file does
    not hold live trading off". They described `config/user.yaml`, which is
    not loaded. In the effective file:
    - `execution.live_enabled: false`, `execution.executor_mode: paper`
    - `live.enabled: false`, `live_trading.enabled: false`
    - `risk.enable_live: false`
    So the config-level live switch is OFF. `live_arming.is_live_enabled`
    reads this file (through `load_user_yaml`) and returns false.
    The rest of findings 23 and 25 (kill switch file armed, persisted arming
    false, no arming variable in the repo `.env`, live-path status files
    silent since May) is unaffected and now agrees with the config.
    Still UNVERIFIED, as before: process environments on the laptop and
    everything on Hetzner.
    My repeated recommendation to "set execution.live_enabled to false" is
    withdrawn: it is already false where it counts. The stray
    `config/user.yaml` (live_enabled true, armed true) has no effect; whether
    to delete or keep that unused file is the operator's choice.

51. CORRECTED: finding 27 said the local config has no `strategy_runner` or
    `risk` block. The effective file has both:
    - `strategy_runner`: venue coinbase, symbols BTC/USD, ETH/USD, SOL/USD,
      strategy `momentum`, `signal_source: synthetic_mid_ohlcv`. It has no
      `risk` key inside it.
    - A top-level `risk` block (for example `max_concurrent_positions: 10`).
      The runner's limit builders read `cfg["risk"]` from the dict `_cfg()`
      returns, which on master carries no `risk` key (finding 26), so this
      block does not reach them either. Finding 26 stands.
    - `paper_trading`: `strategy_id: es_daily_trend_v1`, fee 7.5 bps,
      slippage 5 bps, and no `quote_currency` (so the engine default USDT).
    The ES campaign's BTC/USDT symbol does not come from this file; the
    evidence collector passes it per run.

52. Consequences for work already shipped.
    - Bundle folder 17 (item-29 proposal) was a diff against
      `config/user.yaml`. Applied there it would have had no effect. It is
      replaced in revision 21 by a diff against the effective file. The
      effective file has no `market_quality_guard` block, so Addendum 8's
      statement that the guard runs on code defaults is unchanged.
    - REVIEW_HANDOFF's open point about `execution.live_enabled: true` is
      removed.
    - Patch 0009 migration note, made concrete: the effective default runner
      config is three USD pairs with an undeclared paper currency (USDT). Run
      as it stands under 0009, every entry would be refused
      (`account_currency_mismatch`).

# Second-stage review of the forensic audit (2026-11-12)

Bot relation: SIGNAL_ONLY for the candidate's trade records (research harness, not the bot); BOT_RULES for the
integration assessment (bot code read, not run); runtime configuration not re-read.

Requested by the owner on 2026-11-12, forwarding two outside reviews of
`docs/research/forensic_audit_20261112/README.md`. The second review listed eight questions.
- Written by Claude (Cowork). Read-only: no code, setting, scheduled task or data changed, and no experiment run.
  The one new calculation is a re-analysis of trade records already saved in the repository (section 2).
- **Codex's independent verification (question 1) has not happened yet.** This report gives Codex an exact checklist
  (section 1). Until Codex returns it, everything below is Claude's own, self-checked.
- Labels as in the audit: SHOWN (in the cited file), CLAIMED, UNVERIFIED.

---

## Summary

| Result | Findings |
|---|---|
| **Verified (re-checked against source files today)** | The candidate's A/B/C/full figures. The registered 1.2% REJECT. The +854.4% to +1.3% ES exit result as recorded. The forward-tracker history |
| **New evidence that narrows confidence** | The candidate's profit rests on a few big trends. 5 of its 108 trades made 82% of its net trade profit at 0.50% fees, and the other 98 lose money together (section 2) |
| **Disputed: my own earlier recommendation** | The stock-index ETF test is withdrawn as a priority. With the rule's 50% volatility target, its volatility sizing is inactive at stock-market volatility, so the "identical rule" would not test the same mechanism (section 8) |
| **Missing** | Codex's verification; measured execution costs; any live execution through the bot; the ES result at realistic costs and fills |
| **Go / no-go** | **Go** for a bounded, pre-registered BTC+ETH paper experiment, built only after Codex's verification and a frozen design. **No-go** for real money, more strategy search, or infrastructure not needed by that experiment |

---

## 1. Codex independent verification (question 1): pending, with the exact checklist

Paste to Codex. This is also recorded in `PROJECT_STATE.md`.

> Independently verify `docs/research/forensic_audit_20261112/README.md` and
> `docs/research/second_stage_review_20261112/README.md`. Challenge them; do not assume they are right. Read-only:
> rerun existing scripts on scratch copies only, no code, setting, task or data changes, and no new experiments.
> Report verified and disputed items in the work log.
> 1. Candidate figures: rerun `docs/research/btc_eth_corrected_comparison_20261012/compare.py` and
>    `docs/research/candidate_descriptive_20261107/describe.py` (hash-checked inputs). Compare with audit table 3a and
>    the trade-concentration figures in section 2 of the second report.
> 2. The 1.2% rejection: rerun `docs/research/btc_eth_stress_test_20261009/stress_btc_eth.py` through
>    `scripts/research/rerun_frozen_stress.py`. Confirm the verdict "reject" and "5 of 13 variants beat the mix".
> 3. The configuration count: re-derive the 747 floor from `docs/research/trial_ledger_reconciliation_20261015/`, and
>    give the current total including studies after 2026-10-15.
> 4. The ES exit result: rerun the script in `docs/research/es_exit_policy_matrix_20261007/` on the frozen archive
>    (sha256 `c0d64661...`). Confirm +854.4% (no exits) and +1.3% (old defaults: 3% stop, 6% take-profit, 2%
>    trailing). State its fee (7.5 bps) and fill convention (signal bar close).
> 5. Challenge the conclusion "no past loss is shown to come from a software defect", using the paper-run records.
> 6. Confirm the forward-tracker facts in section 4 of the second report.

---

## 2. Trade-level records of the candidate (question 2)

**Source:** `candidate_descriptive_20261107/results.json`, `round_trip_list` for the full period 2016-08 to
2026-10-08. These are 108 round trips, recorded per asset holding spell, with net P&L including every fee and
slippage on that asset.
- Re-analysed today, read-only. The trades come from the same instrumented loop that reproduced the reviewed harness
  exactly.
- Not yet independently checked (checklist item 1).

| Measure | At 0.50% + 0.05% | At 1.2% + 0.05% |
|---|---|---|
| Net P&L of the 108 closed round trips | $84,531 | $41,558 |
| Of which the best 1 trip | $24,896 (29%) | $13,305 (32%) |
| Best 3 trips | 58% | 68% |
| Best 5 trips | **82%** | **99%** |
| Best 10 trips | 132%: **the other 98 trips lose $26,689** | 160%: the other 98 lose $24,982 |
| Median return per trip | -2.8% | -4.2% |
| Mean return per trip | +16.6% | +14.6% |
| Mean return per trip without the best 10 (by %) | +2.25% | +0.60% |

The equity change over the full period ($101,426) also includes two spells still open at the end: BTC from
2026-08-24, +$2,350, and ETH from 2026-07-06, +$14,544.

**The five best trips at 0.50%**

| Asset | From | To | Return | Net P&L |
|---|---|---|---|---|
| ETH | 2025-07-07 | 2025-09-22 | +70.5% | +$24,896 |
| BTC | 2024-09-30 | 2024-12-23 | +38.5% | +$12,027 |
| ETH | 2024-02-05 | 2024-04-08 | +51.0% | +$11,729 |
| BTC | 2020-10-05 | 2021-03-22 | +227.6% | +$10,653 |
| BTC | 2024-02-12 | 2024-04-15 | +37.5% | +$10,081 |

**Net P&L by exit year:** 2021 +$32,876, 2024 +$44,192, 2025 +$17,913; 2022 -$8,075 and 2026 -$14,438.

**What this means**
- **Yes, the historical result depends heavily on a few exceptional trades.** This is the normal shape of trend
  following: many small losses, cut quickly (the median trip loses 2.8%), and a few large trends. It is not a sign of
  a bug.
- **It does mean the result rests on about five to ten big trends,** mostly in 2020-21 and 2024-25.
- **Dollar shares overweight recent years.** The account grew, so later trades are larger. In percentage terms the
  dependence is smaller but still real: the mean trip return falls from +16.6% to +2.25% without the best 10.
- **Consequence for forward testing:** a few months without a strong trend will look like a loss even if the rule
  works. Six months may contain no big trend at all, which is why the stop rule has to be about drawdown and
  comparison against benchmarks, not only profit (section 6).

---

## 3. Lower execution costs without changing the signal (question 3)

Kept separate from optimisation: nothing below changes the 28-day trend signal or its volatility sizing.

**How big costs are**
- Turnover is 11.3x the account a year over the full period: 486 resizes, 110 entries and 108 exits
  (`candidate_descriptive_20261107/`, SHOWN).
- Approximate cost per year = turnover x cost per side (derived arithmetic, not a run):

| Cost per side | Cost per year |
|---|---|
| 0.55% (taker 0.50% + slippage 0.05%) | About 6% (SHOWN in the descriptive report) |
| 1.25% (stress fee) | About 14% |
| 0.25% (maker fee, no slippage, every order filled) | About 2.8%, an upper bound on the saving |

- That cost difference is the whole difference between the registered REJECT at 1.2% and the pass at 0.5%
  (`stress_fee050_exploratory_20261011/`).

**Lever 1: cheaper fills.**
- The account's maker rate is 0.25% (`RESEARCH_BRIEF.md` line 556, read from the account 2026-10-08).
- Resting limit orders at the weekly open could cut the fee, but some will not fill, and an unfilled order then costs
  the taker fee plus any price move.
- Only measurement answers this. The planned study (E1) is drafted but not frozen; its order-book capture is not
  built.
- A smaller first step is to record the bid/ask spread at each weekly decision. That measures the slippage
  assumption, not maker fill rates.

**Lever 2: skip tiny resizes.** 486 of the 704 full-period trades were resizes.
- A 10-point no-trade band was tested before (E9, registered).
- It had higher Sharpe and end value than the plain rule in both periods at both fees: H 2024-26 at 0.50%, $1,867
  against $1,846. It cut rebalances from about 38 to 21-22 a year.
- It failed only a turnover criterion the record calls mis-specified (`candidate_band_20261013/`).
- It is already tracked forward as the `rule_band10` account in tracker v2. No new parameter is needed: the
  forward results decide.

**Not a cost lever:** changing the lookback, the volatility target or the rebalance day. These are signal changes,
which would be optimisation.

---

## 4. Why only five weeks of forward results, and can it be made reliable? (question 4)

**Why so short:** both trackers were started only a month ago. The rule was chosen on 2026-10-09 to 10-12.

| Tracker | What runs it | Start | On-time weekly decisions | Missed |
|---|---|---|---|---|
| v1, `paper_btc_eth_trend_20261009/` | Claude scheduled task, Mondays 00:47 UTC, on the Mac | Close of 2026-10-11 | 4 weekly rebalances to 2026-11-08 (v1 records no lag field; its scheduled runs show as succeeded) | None found |
| v2, `paper_btc_eth_trend_v2_20261012/` | Codex app automation, Sundays 20:47 New York, on the Mac | First decision 2026-10-18 | **1** (2026-10-25, 0.87 h after close) | 2026-10-18 (reconstructed 168.87 h late), 2026-11-01, 2026-11-08 |

**Why v2 missed** (SHOWN in the v2 README, 2026-11-12):
- The Codex automation definition disappeared from the Mac (`~/.codex/automations/` held only a salt file).
- The Codex app reported "the automation does not exist".
- Who or what removed it is UNVERIFIED.
- One replacement with the same ID was created on 2026-11-12. Its next run, 2026-11-15 20:47 New York, is the first
  proof it works.

**Single points of failure today**
1. Both trackers run on the Mac, which must be awake with the right app open. This is also why the CMC log missed
   2026-11-10 and 11.
2. v2 depends on the Codex app's own scheduler, which lost the task once without any alert.
3. Nothing alerts anyone when a weekly decision is missed. v2's ledger only shows it afterwards.

**Ways to make it reliable** (owner decisions; none done):
- **(a)** Keep the Mac on power and awake for the scheduled times. No code needed.
- **(b)** Add a missed-run check: a separate scheduled task that, on Monday, confirms v1's and v2's latest decision
  day equals the last Sunday and messages the owner if not. Small; read-only.
- **(c)** Move the trackers off the Mac, to the Hetzner server or a cloud scheduled job.
  - Coinbase's public price API answered from the cloud workspace today (HTTP 200 to a header request).
  - This removes the Mac dependency, but needs a server or repository change and owner approval.
- Missed weeks can never become on-time evidence. A later catch-up is labelled reconstructed, as v2 already does.

---

## 5. Integrating the candidate into the paper-trading bot (question 5)

**What the bot does today** (`services/execution/strategy_runner.py`; `exit_parity_audit_20261031/` section 2;
SHOWN by reading):
- **Positions:** one position per symbol. It buys only when flat (the `position_aware` default), and a sell signal
  sells the whole position.
- **Order size:** a fixed number of units (`qty`, default 0.001), not a dollar amount or a share of the account.
- **Exits:** the exit stack runs every loop. Stop 3%, trailing stop 2% from entry, take-profit 6%, 60-candle hold.
- **Signal input:** by default one-second synthetic bars. With `public_ohlcv_1d`, signals see the still-forming
  candle (defect 4).
- **Several symbols in one process:** broken in the deployed code. Fixed in source on 2026-11-03, not deployed.
- **Paper fills and fees:** paper fills at the mid price (BA-01), and the paper config charges 7.5 bps (BA-02).
- **Precedent:** `es_daily_trend_v1` (`sma_200_trend`) already runs a daily trend rule with the exit stack switched
  off (all exits 0).

**What the candidate needs**

| Part | Change needed | Size (Claude's estimate) |
|---|---|---|
| Signal and weight | New strategy module: for each asset, weight = 0.5 x min(1, 0.5 / 30-day volatility) if the 28-day return is positive, else 0. Per asset, so it fits the per-symbol structure | Small |
| Timing | Decide only on the Sunday daily close, from completed candles; trade at the next open | Small to medium (a forming-candle fix and a weekly gate) |
| Position sizing | Turn the target weight into an order size from the account's current value | Medium |
| Resizing | Buy or sell the difference between the current and target position each week. **This is the main gap:** the runner can only open from flat or close in full | Medium to large (new order path in runner and paper engine, with tests) |
| Exits | Exit stack off for this strategy (as in the ES preset); exits come only from weight 0 | Small (configuration) |
| Two assets in one account | Deploy the reviewed multi-symbol fix, or run one process per asset with careful shared-cash handling (BA-06) | Medium (deployment and testing) |
| Execution costs | Charge 0.50% (or measured maker/taker); record bid/ask and fill price at every fill | Medium (BA-01/BA-02 work, partly in the simulation spec) |
| Reporting | Weekly NAV, trades and costs against tracker v2 and the benchmarks | Small to medium |
| Parity check | Trade-for-trade comparison of the bot's version against the research harness on history, before any live run | Medium |

**Total, Claude's estimate before Codex reads the code**
- About 6 to 9 Codex working sessions for source, tests and parity, plus one independent review per step.
- At Codex's recent pace (the multi-coin fix took about a day with two reviews), that is roughly one to two weeks of
  bounded work, then a deployment step.
- The largest uncertainty is the resize path. Codex should give its own estimate after reading
  `strategy_runner.py`, `paper_engine.py` and `paper_runner.py`.

**A cheaper alternative** (about 3 to 4 sessions): a small weekly executor that uses the bot's paper engine for fills
and accounting but not the runner's loop.
- It tests costs and accounting.
- It does not test the runner, the part with most of the known defects.

---

## 6. Proposed simulation: does the candidate have an advantage, and does the bot execute it reliably? (question 6)

A proposal for the owner to approve, change or reject. Nothing below is built or authorised.

**Accounts (all paper, live public prices, same start Sunday)**
1. The candidate through the bot (section 5), 0.50% fee, bid/ask recorded at every fill.
2. The candidate in tracker v2, unchanged (research reference, outside the bot).
3. `rule_band10` in tracker v2 (the cost lever, already running).
4. Benchmarks in tracker v2 or alongside it: hold BTC, hold ETH, a fixed BTC/ETH mix at the rule's own average
   exposure, 25/25/50, cash.

**Question B, does the bot execute it reliably** (checked weekly; any failure is recorded with a cause)

| Check | Pass condition |
|---|---|
| Parity | The bot's target weights match tracker v2's within 1 percentage point every week |
| Missed decisions | None. Two missed decisions stops the experiment for repair |
| Execution gap | Recorded fill price against the quoted bid/ask; average slippage reported against the 0.05% assumption |
| Restarts and failed price fetches | Each recorded; none silently skips a decision |
| Accounting | Cash, positions and fees reconcile to the cent each week |

**Question A, does the candidate have an advantage after realistic costs**
- The go/stop rule is fixed before the start. It extends the 2026-10-11 proposal in
  `strategy_decision_report_20261011.md` section 5.
- **Duration:** 26 weeks, with the decision on a pre-set date. The rule should also say what happens if the period
  contains no market fall of at least 20%: the risk-reduction claim stays untested, so the result is "extend once,
  with the same criteria" rather than pass.
- **Keep the rule only if, after costs:**
  - its return is at least that of the fixed mix at the same exposure;
  - its worst drop is smaller than BTC's.
- **Otherwise stop active trading of the rule.** The honest alternative is a fixed BTC/ETH-plus-cash allocation with
  no bot.
- **Reported, but not deciding:** return against holding BTC and holding ETH, Sharpe, and the band account.
- **Limits stated in advance:**
  - 26 weekly decisions cannot establish statistical significance.
  - Section 2 shows that a few months without a strong trend look like a loss.
  - So the experiment can stop a bad idea and expose execution problems. It cannot prove a good one.

**What it needs before starting:** Codex's verification, the integration (section 5), the paper minimums
(section 7), and the owner's written approval of these criteria.

---

## 7. Minimum safety requirements (question 7)

**For the paper experiment to be trustworthy**
1. Fees at 0.50% and bid/ask recorded at every fill (BA-01, BA-02).
2. Signals on completed daily candles, with a freshness and gap check (defect 4, BA-13).
3. Exit stack off for this strategy, and no adds to positions (BA-23 guard on).
4. Two assets handled correctly: the multi-symbol fix deployed and tested, or one process per asset (D-1, BA-06).
5. A failed price fetch or a refused order recorded and alerted, never silent (BA-10, BA-05).
6. No restart lockout (BA-16 fix deployed), and a restart either automatic or detected within a day (BA-19).
7. A missed-decision alert for the owner (BA-21 in its simplest form: one check that the weekly decision exists).
8. The parity check against the research harness passes before the first live-price week.
9. A run manifest: code version, settings and start date, frozen.

Not needed for paper: off-server encrypted backups, outside heartbeat services, the position cap, exchange-side
protection, the live arming ceremony.

**Additional requirements before real money**
1. The live position limit enforced (LP-11) and exposure limits working (BA-24).
2. Exits never blocked by entry limits (CP-09), and rejected exits retried (BA-05 with owner decision 3).
3. A decision on exchange-side protection (LP-05).
   - Note: the candidate uses no stops, so an outage means a missed weekly rebalance, not an unprotected stop. The
     risk is smaller than for the default strategies, but it still needs a written decision.
4. Live arming tied to the enable ceremony (LP-08), and key permissions checked at start (LP-03).
5. The daily-loss write failure fixed (BA-28), and a decision on the 72 unapplied reviewed patches (LP-10).
6. Process supervision, outside heartbeats and backups (R2, R3, R10 in the simulation spec).
7. The owner's capital and maximum-loss decision (decision 2). At $1,000 the roughly $240 a year of infrastructure is
   a 24% hurdle.

---

## 8. The stock-index ETF test: useful evidence or a distraction? (question 8)

**My earlier recommendation is withdrawn as a priority.** Reasons, from the rule's own code
(`btc_eth_stress_test_20261009/stress_btc_eth.py` line 47):
1. **The identical rule would not test the same mechanism.**
   - Each asset's weight is 0.5 x min(1, 0.5 / volatility).
   - Broad stock indexes usually run at roughly 15-25% annual volatility, so 0.5 / volatility is above 1 and the
     weight is capped at 0.5 almost always. The volatility sizing, half of the rule, would be switched off.
   - So it would test only a 28-day trend filter. (Typical index volatility is general market knowledge, not
     measured in this repo.)
2. **It mostly reproduces published results.** Trend timing on stock indexes is widely studied and generally shows
   smaller crashes, not higher returns. A pass would add little about whether the crypto settings are lucky. A
   failure could come from the very different volatility and the short 28-day lookback, not from luck in crypto.
3. **The bot cannot trade it.** CryptKeep trades on Coinbase. Even a pass has no direct use without new
   infrastructure, which the second review's rule 2 rules out.

**Better independent evidence already exists or is already running**
- E10 applied the same rule to 10 other coins (`multisymbol_trend_20261015/`). It cut drawdowns on every coin by 10-50
  points but rarely improved risk-adjusted return. That supports the risk-reduction mechanism and not a return edge.
  It is the same conclusion as the candidate's.
- The forward test (section 6) is the only genuinely new evidence.

**Verdict:** a distraction at this stage, unless the owner wants a stock-index product for its own sake.

---

## Recommended next steps and effort

| Step | Who | Effort (estimate) | Depends on |
|---|---|---|---|
| 1. Independent verification (section 1) | Codex | About 1 session | Owner sends the checklist |
| 2. Freeze the go/stop rule and experiment criteria (section 6) | Owner, with a Claude draft | About 1 hour of owner time | Step 1 |
| 3. Forward-tracker reliability: Mac awake, plus a missed-run check (section 4 a-b) | Owner and Claude | Small | None |
| 4. Codex's own integration estimate after reading the code (section 5) | Codex | Part of a session | Step 1 |
| 5. Build the integration and the paper minimums (sections 5 and 7) | Codex, reviewed | About 6-9 sessions (about 1-2 weeks) | Steps 1, 2, 4 and owner approval |
| 6. Run the 26-week experiment | Automatic, weekly check | About 15 minutes a week | Step 5 |
| 7. Spread recording at each weekly decision (cheap first step of E1) | Codex | About 1 session | Owner approval |

Not recommended now: the ETF test; any new strategy search; simulation infrastructure for the default strategies;
real-money preparation.

## Go / no-go

- **Go:** steps 1 to 4 now. They are cheap and change no code.
- **Conditional go:** steps 5 and 6, once Codex's verification passes and the owner signs the criteria.
- **No-go:** real money; more strategy search; building infrastructure that the experiment does not need.

This matches the second review's three proposed rules: no endless strategy search, no infrastructure without a
defined experiment, no profitability claims without independently verified after-cost forward results. Those rules
are the owner's to adopt; they are not recorded as adopted.

## Limits
- Self-checked. Codex's challenge is pending, and the integration estimate is Claude's reading of the code, not a
  build.
- The trade-level analysis uses recorded research trades, not exchange fills.
- No new data was downloaded, no script was rerun, and nothing was changed.

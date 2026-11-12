# Why the tested strategies lose: a diagnosis

Research item 1 in `docs/PROJECT_STATE.md`, owner-approved 2026-10-30. **Diagnostic, historical and in-sample.**
No new strategy, no tuning, no new data, no change to any strategy, configuration or the 25-symbol universe.

## Cross-review correction - 2026-11-03 UTC (Codex)

Bot relation: SIGNAL_ONLY - the default-strategy diagnosis does not establish current bot performance; the cross-family rows below include STANDALONE studies. Two permitted local configuration files were inspected through a trading whitelist on November 2; active processes, environment/preset resolution and server configuration were not checked.

Independent source/arithmetic review found three material errors. The original text and results below are retained as a historical record, NOT reaffirmed. The pre-correction README is preserved in `../claude_conversation_audit_20261102/failure_diagnosis_README_before_correction.md`; the original SHA256SUMS remains the seal of the earlier artifact, not this added correction.

- **SHOWN: cost hypothesis 2 has a round-trip mismatch.** A roughly 0.45% before-fee trade does not survive 0.35% cost per side (about 0.70% round trip). The fee-only break-even is approximately 0.22% per side under the saved fixed-notional convention. Its before-fee price return already includes assumed slippage; an all-in budget and a fee-only budget are not interchangeable. E1 remains an unproven measurement hypothesis, not a demonstrated solution.
- **SHOWN: the in/out-of-market return attribution is invalid at trade boundaries.** `diag_inout.py` lines 16-20 and `diag_trades.py` lines 118-122 classify a close-to-close return using holdings AFTER that bar's open. `next_open_research.py` executes before recording those holdings. Entry opening gaps are incorrectly credited to the new position; exit opening gaps are incorrectly attributed to cash. The rises-missed/falls-avoided totals and the conclusion that this attribution demonstrates informative timing are WITHDRAWN pending corrected gap/intrabar accounting. This does not alter the saved trades or their net cash results. The separate trade-price re-entry statistic is not withdrawn by this specific finding.
- **SHOWN: the blocked-exit dollar estimates are not established.** `diag_trades.py` lines 113-114 and 145-147 multiply an exit-price ratio by $100, rather than valuing the exit-price difference at the original position quantity with consistent execution adjustments. The -$15/+$28/+$65 counterfactual dollar effects, their percentages and any causal recommendation relying on them are WITHDRAWN. The source-level SELL-filter veto is still shown; its net economic effect requires a correctly specified contrast.

Additional limits: a weak correlation with the preceding 24-hour move cannot rule out all entry-timing problems; costs, fills, sizing and venue conventions vary across the family table, so the blanket "same assumptions everywhere" answer is too broad. No new market run, strategy verdict, statistical qualification or operational acceptance follows from this correction. Three synthetic counterexamples are saved with the conversation audit; they demonstrate the defects, not corrected market outcomes.

What do I know that could change the owner's decision that I have not yet said?

## Corrections and disclosures (2026-10-31, Claude; self-checked, not independently verified)
These correct or narrow this report as first written on 2026-10-30. Earlier text is kept; corrected lines are marked [C1]-[C3].
- **[C1] Prior work not cited.** The breakout exit-filter defect was documented on 2026-09-23
  (`docs/research/breakout_economic_dissection_2026_09_23.md`: 28 of 42 trades, BTC 5m). An isolated exit-policy comparison
  tool was then built and independently reviewed (branch `codex/breakout-exit-treatment`, commits 909239e48 and bc0156090,
  not in HEAD; `docs/research/breakout_exit_treatment.md` on that branch) and the economic run was shelved: no eligible
  data and no runner-parity proof. This report presented the defect as a new finding. What is new here is the same check
  on EMA cross and mean reversion, and the dollar effect on the OKX replay.
- **[C2] Scope of the exit finding.** This replay, the saved baseline and the ED-002 design all test the strategy signal
  functions only. The paper/live runner adds exits that they do not model (SHOWN in `services/execution/strategy_runner.py`):
  EMA-cross invalidation sells on low volatility, chop or lost cross gap (lines 1436-1458), and default stop-loss 3%,
  take-profit 6%, trailing stop 2% and 60-bar maximum hold (lines 1087-1090; the three default presets do not set these;
  whether the runtime config overrides them is UNVERIFIED, the config was not read). So "the strategies block their own
  exits" is SHOWN for the signal functions and for every replay here; for paper/live trading it is UNVERIFIED, and for EMA
  cross the runner sells on the same filters. "Mean reversion has no loss exit" holds for its signal function only.
- **[C3] The +$139 is not evidence of an edge.** t = 1.45; bootstrap 95% interval -$38 to +$336 (includes zero); the top
  10 of 310 trades made 169% of it. The 2026-09-23 result (-0.10% before fees, profit factor 0.99) is a different test
  (Coinbase BTC 5m, June-August, 42 trades, gapped data); both show a small before-fee result not distinguishable from zero.
  This report's headline "+$139" stated the figure without that qualification.
- **[C4] Correction to C2 (2026-10-31, later the same day).** The runner's EMA-cross invalidation exits are inert as
  the code is written: they compare against `min_volatility_pct`, `min_trend_efficiency` and `min_cross_gap_pct`
  read from the runner's top-level settings (`strategy_runner.py` lines 1446-1448), which `_cfg()` never fills (those
  keys live in the strategy block), so every threshold is 0 and no condition can be true. SHOWN by code reading, not
  by a test. C2's "for EMA cross the runner sells on the same filters" is withdrawn. C2 also omitted two earlier
  runner-rule replays by Claude: `es_exit_policy_matrix_20261007.md` and `strategy_horizon_scan_20261008.md`.
  See `docs/research/exit_parity_audit_20261031/`.

**Sources.** The trial ledger (`trial_ledger_reconciliation_20261015/trial_inventory.csv`, `pass2_findings_20261015.md`);
each family's own report (cited below); and a trade-by-trade replay of the three default strategies in
`multisymbol_baseline_v1` (OKX hourly, BTC/ETH/SOL/ADA/XRP, 2026-01-01 to 2026-09-30, $100 per trade) by
`diag_trades.py`, which reproduces all 15 saved runs trade for trade before measuring anything (`diag_trades_result.json`).

## Short answer
The failures have **two different causes, plus one code defect**:
- **Most short-horizon altcoin rules lose before any cost.** Their signals have no edge here; costs are not the reason.
- **A few signals make a small profit before costs** (about 0.3-0.5% per trade) that taker costs of 0.5-0.9% per side remove.
- **The three default strategies block their own exits** [C1, C2: signal functions; known for breakout since 2026-09-23]. Each applies its entry filters to sell signals too
  (SHOWN in `services/strategies/breakout_donchian.py` lines 59-66, `ema_cross.py` 114-121,
  `mean_reversion_rsi.py` 57-64). That cost EMA cross and mean reversion money; it did not hurt breakout.
- **"When to stay out" is the capability with the best evidence:** the BTC/ETH trend filter, and breakout's in-market hours.

## The families (results as recorded in each report)
| Family (configurations) | Costs and fills | Before fees | After fees | Main cause |
|---|---|---|---|---|
| Altcoin event, recovery and listing rules (~544, 448 of them one search) | 0.50% + 0.30% slippage per side, next open | not recorded; losses of $399-$870 per $1,000 exceed the most costs could take ($80-$339) | $129-$601 vs BTC $1,840 (`altcoins_corrected_rerun_20261009.md`) | signal |
| Short holds of top gainers (14) | 0.50% + 0.10% | 13 of 14 lose at zero fees (`short_hold_corrected_rerun_20261009.md`) | lose | signal |
| Leader pullback and target rules (10) | 0.50% + 0.25% | negative mean before costs (`leader_target_test_20261012.md`) | all lose | signal |
| Breakout campaign, BTC hourly (Sep) | 0.10% + 0.05% | -0.10%, profit factor 0.99, turnover 75x capital (`breakout_economic_dissection_2026_09_23.md`) | -12.2% | no edge, high turnover |
| Default breakout (OKX, 5 coins) | 0.10 / 0.25 / 0.60% + 0.05% | **+$139** over 310 trades, positive on all 5 coins [C3: not distinguishable from zero] | -$16 at 0.25%; -$234 at 0.60% | costs |
| Default EMA cross | same | **+$45** over 129 trades | -$19 / -$110 | blocked exits + costs |
| Default mean reversion | same | **-$148** over 29 trades | -$162 / -$182 | signal + blocked exits |
| Reversal scan (6) | 0.50% + 0.10% | small profit (`reversal_diagnostic_20261012.md`) | negative at higher costs | costs |
| Funding carry (1) | spot 0.50%, perp 0.10% | +$2 | -$5; -$25 after server | costs |
| BTC/ETH slow trend and variants (155, 118 a robustness grid) | 0.50% + 0.05% | positive | survives 0.50%, rejected at 1.2%; variants lost to it | survives, as risk reduction |
| Weekly cross-sectional momentum, E6 (9) | 0.50% + 0.25% | not recorded | FAIL | unknown |
Holding the same five coins with the same $100 per entry lost $67 over the OKX period.

## Trade-level detail: the three default strategies (OKX hourly, 2026)
| | Breakout | EMA cross | Mean reversion |
|---|---|---|---|
| Trades | 310 | 129 | 29 |
| Before-fee profit | +$139 | +$45 | -$148 |
| Trades whose exit was blocked by a filter | 28 (9%) | 77 (60%) | 28 (97%) |
| Exiting at the first blocked signal instead would have changed profit by | -$15 (blocking helped) | +$28 | +$65 |
| Coin's hourly return while in vs out of the market (all 5 coins) | in higher on 5 of 5 | in higher on 3 of 5 | in lower on 4 of 5 |
| Rise in the 24 h before entry, and its link to the trade result | +0.9 to +1.6%; correlation -0.19 to +0.01 | +1.3 to +2.1%; -0.28 to -0.06 | falls of 2.5-4.5%; too few trades |

- **Entry:** no sign that late entries cause the losses: the run-up before entry does not predict the trade result.
- **Exit:** blocked exits cost EMA cross about $28 (62% of its before-fee profit) and mean reversion about $65. Mean
  reversion also has no loss exit: it buys falls and holds until an overbought signal that may not come.
- **Staying out:** breakout was in the market while its coins rose and out while they fell, on all five coins.
  Its timing carries information; its trading frequency costs more than that information earns.

## The owner's seven questions
1. **Profitable before fees, not after?** Yes for a minority (default breakout and EMA cross, reversal, carry). Most
   altcoin and short-horizon rules lost before fees.
2. **Same cost and execution assumptions everywhere?** Yes: taker fills at the next bar's open, fees mostly 0.25-0.60% per
   side (0.10% in two studies) plus slippage, long-only, fixed sizing. No test used measured maker fills. This decides the outcome for the
   small-edge group; it does not explain the group that loses before fees.
3. **Entry and exit timing?** Entries: no evidence of a problem. Exits: a real, code-level defect in all three default strategies [C2: in the signal functions; paper/live effect UNVERIFIED].
4. **Too rigid?** The rules are fixed. Regime filters were tried (market-up exit, crash brake) and failed; the one survivor
   is a simple regime switch (trend or cash). In the defaults, the rigidity that hurts is filters applied to exits.
5. **Systematic biases?** Survivor-selected lists, reused history, short samples and proxy venues all bias results toward
   optimism, so they do not explain the failures.
6. **Are the 747+ configurations independent?** No: about 9-35 effective tests; about 73% are one mechanism (altcoin event rules).
7. **Multiple testing?** Applied where it matters: the candidate's deflated Sharpe at up to 120 trials; nothing else survived to need it.

## At most three hypotheses (for owner approval; each is forward and falsifiable)
1. **Exits:** in the 25-symbol forward comparison, add a pre-registered variant of each default strategy whose sell
   signals bypass the entry filters, with nothing else changed. Prediction: net results at least as good as the
   defaults at both fee levels, better for EMA cross and mean reversion. Needs Codex before the freeze; adds 3 arms.
2. **Costs:** run the already-designed maker-versus-taker study (E1) on BTC and ETH. Prediction: measured all-in cost per
   side, including unfilled orders finished as taker, stays at or below 0.35%. Below that, before-fee edges of about
   0.45% per trade could survive; above it, they cannot.
3. **Staying out:** in the forward comparison, measure each strategy's in-market minus out-of-market hourly return per
   coin (no extra arms). Prediction: positive for default breakout on a majority of the 25 coins.

**Bearing on the 25-symbol comparison as designed:** its default breakout trades at 0.50% or 0.90% plus 0.25% per side,
a round trip of at least 1.5%, against a before-fee edge here of about 0.45% per trade; it is very likely to lose.
That makes hypothesis 1 the cheapest way to add information before the 182-day run starts.

## Addendum: staying out, both sides (`diag_inout.py`, `diag_inout_result.json`)
The coins' hourly log returns while each strategy was in cash, split into rises missed and falls avoided, summed over
the five coins, plus the price change from each exit to the next re-entry:

| | Breakout | EMA cross | Mean reversion |
|---|---|---|---|
| Rises missed while in cash | 3,485 points | 3,518 | 3,280 |
| Falls avoided while in cash | 3,688 | 3,621 | 3,161 |
| Net while in cash (negative = staying out helped) | -202 | -103 | +119 |
| Re-entries; average price change from exit to re-entry | 305; -0.6% | 124; -1.0% | 24; +0.9% |
| Re-entries above the exit price | 54-67% per coin | 52-68% | 25-67% |

Breakout and EMA cross avoided slightly more falls than they missed rises, and on average re-entered below their exit
price; most re-entries were higher, but the lower ones were larger. The margin is thin: rises missed are 95-97% of
falls avoided. The coins fell 5-30% over the period, which favours staying out; in a rising market the same timing would
miss more. Mean reversion did the reverse. In-sample, nine months; points are summed log-return percentages.

## Addendum: the breakout's 310 trades (`diag_breakout_trades.py`, `breakout_trades.csv`, `breakout_trades_summary.json`)
One row per closed trade: entry and exit time and price, hold, before-fee return (prices include 5 bps slippage per side),
net dollars at 0.10/0.25/0.60% fees, best gain reached during the trade. The trades are identical at all three fee levels (checked).

| Question | Answer (in-sample, $100 per trade) |
|---|---|
| Did a few trades make the profit? | Yes. Top 5 trades +$152, top 10 +$235 (169% of the $139); the other 300 lost $96. |
| Were most trades marginally profitable? | No. 194 of 310 lost before fees; median trade -0.89%, mean +0.45%. 27 trades were within +/-0.5%. |
| Did it trade too often? | 6.9 trades per coin per month, median hold 39 h. It breaks even at 0.22% fee per side; fees at 0.25% ($155) exceed the before-fee profit. 103 trades made more than 0.5% before fees, 87 more than 1.2%. |
| Which market conditions? | Profit came in rising months: July-September +$174 while the five coins rose 9-29% a month. It lost $64 in March-May, when the coins moved -5% to +4% a month, and little in sharp falls (February -$1, June -$2 while the coins fell 15% and 23%), when it was in the market less (34% and 41% of coin-hours, against 47-55% in other months). January +$33 in a -13% month is the exception. Nine months: a pattern, not a tested regime rule. |
| Are the cost assumptions realistic? | The account's own fee tier is 0.25% maker / 0.50% taker (SHOWN, authenticated read 2026-10-08). The replay buys and sells at the next open, which is a taker order: at 0.50% per side this would lose about $171 (arithmetic, not a run). At 0.25% it needs every order to fill as a maker order; unfilled orders are E1's question. The 5 bps slippage is an assumption on OKX prices, not a Coinbase fill. |
| Would the paper/live runner give the same result? | Unknown [C2]. 83 trades reached a 6% gain at some point (they made +$509), 87 were held over 60 h (+$447), 52 lost more than 3% (-$208): the runner's default take-profit, maximum hold and stop would have changed all of these, in a direction not measured. |

**Limits:** OKX USDT hourly prices, five coins, nine months; costs are modelled, not fills; the altcoin cost bound uses
the most cost could have taken; E6's before-fee result was not recorded and was not rerun.

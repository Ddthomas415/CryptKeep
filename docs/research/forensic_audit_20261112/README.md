# Forensic audit: every strategy, test and simulation in CryptKeep (2026-11-12)

Bot relation: covers all four labels (STANDALONE, SIGNAL_ONLY, BOT_RULES, BOT_PAPER; definitions in
`result_labels_20261031/`); runtime configuration not re-read for this audit (the last whitelisted read was
2026-10-31, `exit_parity_audit_20261031/` section 1).

Requested by the owner on 2026-11-12, before any further development is approved.
- Written by Claude (Cowork) from the repository's own records. Read-only: no code, configuration, scheduled task
  or data was changed, nothing was rerun and no new experiment was launched.
- **Self-checked, not independently reviewed.** Codex should verify it before anything is decided on it.
- Repository state when written: branch `backup/2026-10-31`, HEAD `3b49ead3f` (pushed to GitHub 2026-11-12).
- Paths are relative to `docs/research/` unless they start with another top-level folder.

**Labels used**
- **SHOWN:** the fact or figure is in the cited repository file. Figures are copied, not re-derived, unless the text
  says so.
- **CLAIMED:** a record states it, but that record says it was not independently checked, or the artifact behind it
  is not in the repository.
- **UNVERIFIED:** no record establishes it.
- **Not computed:** the study never calculated that metric. No figure is filled in for it.

---

## 0. Verdict in brief

1. **No strategy has demonstrated profitability after realistic costs on data it was not developed on.** None has
   traded real money. Every positive result is historical (a backtest, mostly in-sample) or a few weeks of paper data.
2. **The strongest evidence is for the BTC+ETH 28-day trend rule** (volatility-sized, weekly).
   - Its supported value is lower drawdown and better risk-adjusted return than holding BTC, at a 0.50% fee.
   - It has no demonstrated return edge over holding BTC, and it was rejected under its own registered 1.2% stress
     test.
   - Forward data so far: 4 weeks (v1) and 1 week (v2).
3. **Almost every other idea lost money.**
   - About 750 configurations in about 30 families were tested; 747 is the ledger's floor, not a complete count.
   - Most altcoin and short-term price-pattern rules lost money before any cost: a strategy failure.
   - A few small before-cost gains were removed by fees: a cost failure.
4. **The bot itself has never run a strategy that showed an advantage.**
   - Its three default strategies lose after costs when replayed with the bot's own rules.
   - Its default exits turned one in-sample trend rule from +854% into +1.3%: an execution-design failure.
   - The only candidate is not implemented in the bot.
5. **Several earlier tests were compromised.** They were corrected or withdrawn (section 5), and no correction
   turned a failure into a success.
6. **The evidence supports continuing only in a narrow form:** the candidate's forward test, cost reduction and one
   out-of-sample check, under a dated stop rule. It does not support open-ended development (section 10).

---

## 1. Complete inventory of strategies tested

### 1a. Every family with a trading outcome

The master lists are the trial ledger (`trial_ledger_reconciliation_20261015/trial_inventory.csv`, 42 entries) and
the 50-row label register (`result_labels_20261031/result_labels.csv`). Rows below are grouped by purpose. "Configs"
is the configuration count recorded in those files; "UNRESOLVED" means the record has no exact count.

**A. BTC/ETH trend family (contains the only candidate)**

| Family (ID) | What it does | Data | How tested | Dates | Configs | Status | Bot relation |
|---|---|---|---|---|---|---|---|
| BTC+ETH 28-day trend, primary (MAJORS) | Section 1b | Coinbase BTC-USD and ETH-USD daily, 2016-08 to 2026-10 | Historical; forward paper since 2026-10-11 (v1) and 2026-10-19 (v2) | 2026-10-09 to now | 4 rules (primary pre-registered) | CANDIDATE, not established | STANDALONE |
| Stress neighbourhood (STRESS_NEIGHBOURHOOD) | 105-setting grid plus 13 variants around the rule | Same | Historical, registered | 2026-10-09 | 118 | REJECT at 1.2% (registered); "keep researching" at 0.5% (exploratory) | STANDALONE |
| Corrected comparison (CORRECTED_COMPARISON) | Rule against BTC, matched mix, 25/25/50 mix | Same | Historical, corrected harness | 2026-10-12 | 0 new | CANDIDATE | STANDALONE |
| Deflated Sharpe check | Selection-bias correction of the rule's Sharpe | Same | Statistical | 2026-10-11 | 0 new | Absolute Sharpe survives; no edge over BTC | STANDALONE |
| E7 funding crash brake | Rule cut when funding is extreme | Rule plus Binance BTC/ETH funding, 2019-2026 | Historical, registered | 2026-10-13 | 5 | FAIL | STANDALONE |
| E8 composite v1 | 20/50/100/200-day trend ensemble plus band | BTC/ETH daily | Historical, registered | 2026-10-13 | 4 | FAIL | STANDALONE |
| E9 rebalance band 0.10 | Skip small weight changes | BTC/ETH daily | Historical, registered | 2026-10-13 | 3 | FAIL on the turnover criterion, which the record calls mis-specified | STANDALONE |
| E10 10-coin trend | Same rule over 10 core coins, equal 1/N | Coinbase daily, 10 coins, 2019-2026 | Historical, registered | 2026-10-15 | 13 | FAIL against BTC+ETH | STANDALONE |
| Top-N trend (TOP10) | Trend on the top 5/10/20 coins, delisted included | Binance daily, all 677 pairs, 2017-2026 | Historical | 2026-10-09 | 3 | Failed | STANDALONE |
| Binance hybrid (HYBRID) | Trend / top-5 momentum / hybrid | Binance daily, 484 pairs, 2019-2026 | Historical, train/test | 2026-10-09 | 10 | Failed; 4 paths incomplete (LUNA) | STANDALONE |
| Descriptive report | Regimes, trades, win rate for the rule | Coinbase daily 2016-2026 | Description only | 2026-11-07 | 0 | Description, not a test | SIGNAL_ONLY |

**B. The bot's own strategies**

| Family (ID) | What it does | Data | How tested | Dates | Configs | Status | Bot relation |
|---|---|---|---|---|---|---|---|
| Default breakout / EMA cross / mean reversion (MULTISYMBOL_OKX) | The bot's three default presets (section 1b) | OKX hourly, BTC/ETH/SOL/ADA/XRP, 2026-01-01 to 09-30 | Historical, signals only | 2026-10 | 15 | Lose after costs | SIGNAL_ONLY |
| Same, with the runner's rules (EXIT_PARITY_AUDIT) | Adds the runner's exit stack and change-only entries | Same | Historical replay | 2026-10-31 | 15 | All lose after costs | BOT_RULES |
| Horizon scan (HORIZON_SCAN) | 8 registry strategies, default presets | Coinbase/OKX 5m, 1h, 1d; 2025-06 to 2026-08 | Historical, runner rules, 7.5 bps fee | 2026-10-08 | 40 | No promotion | BOT_RULES |
| ES SMA-200 exit matrix (ES_EXIT_MATRIX) | BTC above or below its 200-day average, 4 exit policies | Coinbase BTC-USD daily, 2018-01 to 2026-06 | Historical, runner rules, 7.5 bps fee | 2026-10-07 | 8 | Research only; one in-sample path | BOT_RULES |
| Breakout economic dissection | Breakout on BTC 5-minute | Coinbase BTC/USDT 5m, 2026-06 to 08 | Historical plus paper campaign | 2026-09-23 | UNRESOLVED | Failed economically | BOT_PAPER |
| Reversal diagnostic (REVERSAL_DIAGNOSTIC) | RSI mean reversion and volatility reversal presets | AVAX/QNT/ICP daily | Historical | 2026-10-12 | UNRESOLVED | 1 trade in 9 runs | SIGNAL_ONLY |
| Candle diagnostic | Repository presets on GTC/RSR | Coinbase candles | Descriptive | 2026-10-12 | 0 | Descriptive only | SIGNAL_ONLY |
| 25-symbol comparison design (ED-002) | Forward comparison of the defaults on 25 coins | Not collected | Design | 2026-10-27 | 0 | Paused, then put on hold 2026-11-12 | SIGNAL_ONLY |

**C. Paper runs through the actual bot**

| Run (ID) | Strategy | Where | Dates | Result | Source |
|---|---|---|---|---|---|
| Corrected ES prospective trial (ES_TRIAL) | `sma_200_trend` | Server | Ended 2026-10-13 | Zero orders, fills or positions | `../checkpoints/es_prospective_endpoint_result_2026_10_16.md` |
| ES daily trend v1 (ES_V1_PAPER) | `es_daily_trend_v1` | Laptop | To 2026-07-09 | 8 closed trades, 0 wins, -$4.16 (fee figures later superseded) | `paper_evidence_standing_20261005.md` |
| Breakout default daily | `breakout_default` | Laptop | To 2026-09-02 | 12 closed trades, 4 wins, +$3.07 (superseded fee figures) | same |
| EMA cross campaigns (EMA_CAMPAIGNS) | `ema_cross` | Server | Coinbase stopped 2026-09-12 | Coinbase: 8 trades, -$2.32. Gate.io/Binance collectors: value UNVERIFIED | `server_workload_inventory_20261011.md` |
| Breakout campaign (BREAKOUT_CAMPAIGN) | breakout | Server | 2026-09 | Failed economically (CLAIMED from the ledger) | `breakout_economic_dissection_2026_09_23.md` |
| Laptop paper records | Defaults on 1-second synthetic bars | Laptop | 2026-03 to 04 | Breakout 3, EMA 2, mean reversion 65 round trips; median hold about 6 s | `exit_parity_audit_20261031/` section 1 |

**D. Altcoin price action (all STANDALONE, all failed or withdrawn)**

| Family (ID) | What it does | Data | Dates | Configs | Status |
|---|---|---|---|---|---|
| Altcoin event rules (ALT_EVENT_SEARCH) | Pump, dip and regime entries, several exits | Coinbase hourly, about 395 coins, the 60 days to 2026-10-08 (the earlier 10 months used for some reruns) | 2026-10-08/09 | 448 | No rule survived the corrected rerun |
| Dynamic Coinbase top gainers (DYNAMIC) | Rotation and breakout on recent gainers | Same | 2026-10-09 | 6-8 | Failed |
| Short holds of top gainers (SHORT_HOLD) | Buy the top 3 by recent gain, hold briefly | Same | 2026-10-09 | 14 | Failed |
| Recovery momentum (RECOVERY, RECOVERY_REGIME) | Crashed coins recovering, with or without a market filter | Binance daily, 2019-2026 | 2026-10-09 | 16 + 32 | Failed its pre-registered test |
| Three ideas (THREE_IDEAS) | New listings, early accumulation, small-coin basket | Binance daily | 2026-10-09 | 24 | Failed; small-coin basket INCOMPLETE |
| CMC attention proxy (CMC_PROXY) | Weekly CMC rank and volume proxies | CMC weekly, 2018-2026 | 2026-10-09 | 20 | Failed |
| Top-gainer pullback, daily (LEADER_DAILY_PULLBACK, LEADER_TARGET) | Buy the day's leader after a pullback | Coinbase daily | 2026-10-12 | 2 + 8 | All lose |
| Top-gainer pullback, hourly (LEADER_HOURLY) | Same on hourly leaders | Coinbase hourly, 2026-08 to 10 | 2026-10-12 | 3 or more | $1,000 to $493 as one account |
| Failed breakout and retest (FAILED_BREAKOUT) | Buy a failed downside breakout | Coinbase hourly, 2026-08 to 10 | 2026-10-12 | 1 | $1,000 to $157.59 |
| Weekly cross-sectional momentum (E6) | Hold the top 5 recent risers | Coinbase daily, about 480 products, 2018-2026 | 2026-10-12 | 9 | FAIL, also after correction |
| Dip-recovery screen (DIP_RECOVERY_SCREEN) | Buy after red candles | Coinbase daily and hourly | 2026-10-12 | UNRESOLVED | Withdrawn: used future information |
| Monday effect (MONDAY_DIAGNOSTIC) | Monday open to Tuesday open | 9 coins, 26 Mondays | 2026-10-12 | 1 | Noise until registered |
| BLAST/VARA events | Event study on two coins | Coinbase hourly and daily | 2026-10-09 | UNRESOLVED | No verdict recorded |
| Low-value top-100 screens | Cheap coins, ranks 51-100, new entrants | CMC weekly, 2019-2026 | 2026-10-18 | Several baskets | No edge established |
| New top-100 entrants on Coinbase (ENTR-CB-1) | New entrants that trade on Coinbase | CMC weekly, 2019-2026 | 2026-10-19 | 1 | STOP |
| Dips on 10 popular coins | 1-5% dip, then 1-5% target | Coinbase hourly 2025-10 to 2026-10; daily 2017-2026 | 2026-11-08 | 250 cells x 2 data sets | Description; all lose under the main rule |

**E. Carry, execution and information**

| Family (ID) | What it does | Dates | Status |
|---|---|---|---|
| Funding and basis signals (FUNDING_SIGNALS) | Funding-rate signals | 2026-09/10 | No actionable candidate (CLAIMED) |
| Funding carry (CARRY_FEASIBILITY) | Own spot, short the perpetual, 30 days, $1,000 | 2026-10-12 | +$2 funding; -$5 after costs; -$25 after the server |
| Order-book imbalance pilot (FC01_R1) | Buy on bid-heavy order book | 2026-10-04 | STOP |
| Volatility forecast (VOLFC_1) | Chronos-2 model against trailing volatility | 2026-10-18 | FAIL (a forecast test, not a trading test) |
| Wikipedia attention (ATTN_1) | Page views as a signal | 2026-10-21 | BLOCKED_DATA |
| CMC trending log | Forward log of trending coins | Collecting since 2026-10 | Primary analysis not before 2027-02-15; first 32 entry days now affected by two missed days |
| Maker vs taker (E1) | Measure the cost saving of limit orders | Drafted 2026-10-11 | Not run; pre-registration not frozen |
| CTREND-OOS | Out-of-sample test of a published trend factor | Drafted 2026-10-22 | On hold; never run |
| Liquidation rebound (LIQ-1) | Price after heavy forced selling | 2026-10-12 | 2-hour descriptive check only |

### 1b. Entry and exit conditions of the main strategies

| Strategy | Entry | Exit | Parameters | Source |
|---|---|---|---|---|
| BTC+ETH 28-day trend (candidate) | Each Sunday close, each of BTC and ETH is held if its close is above its close 28 days earlier | Weight 0 when the 28-day return is not positive; decisions only on Sunday closes, traded at the next day's open | Weight per asset = 0.5 x min(1, 0.5 / 30-day annualised volatility); at most 100% invested; no stop | `btc_eth_stress_test_20261009/stress_btc_eth.py` lines 41-57 (`target`, `run`) |
| Default breakout (`breakout_default`) | Close breaks the 20-candle Donchian channel, with filters | Signal sell (filters also applied to sells) | `donchian_len` 20, `filter_window` 8, `min_volatility_pct` 0.2, `min_volume_ratio` 0.95, `min_trend_efficiency` 0.1, `min_channel_width_pct` 0.25, `breakout_buffer_pct` 0.05 | `services/strategies/presets.py` |
| Default EMA cross (`ema_cross_default`) | 12-period EMA crosses above the 26, with filters | Opposite cross (filtered) | `ema_fast` 12, `ema_slow` 26, `min_volatility_pct` 0.2, `min_volume_ratio` 0.95, `min_trend_efficiency` 0.15, `min_cross_gap_pct` 0.02 | same |
| Default mean reversion (`mean_reversion_default`) | RSI(14) below 30, near the 50-period SMA, with filters | RSI above 70 (filtered); no loss exit in the signal function | `rsi_len` 14, `rsi_buy` 30, `rsi_sell` 70, `sma_len` 50, `max_volatility_pct` 1.5, `max_sma_distance_pct` 6.0 | same |
| ES daily trend (`es_daily_trend_v1`, strategy `sma_200_trend`) | Close above the 200-day SMA, with an ATR regime gate | Below the SMA; 2 x ATR stop in the strategy module | `sma_period` 200, `atr_period` 20, `atr_stop_multiplier` 2.0, `max_position_notional_pct` 10 | same; `services/strategies/es_daily_trend.py` |
| The runner's own rules (apply to every bot strategy) | Buy only when the signal changes to buy | Every loop: stop 3%, trailing stop 2% from entry (fires first), take-profit 6%, 60-candle hold; then the signal sell | Default signal input is one-second synthetic bars; loop 1 s; order size `qty` 0.001 units | `exit_parity_audit_20261031/` section 2 |

The 448 altcoin event configurations and the other grids are defined in their scripts (paths in the `evidence` column
of `result_labels.csv`). They are not reproduced here.

---

## 2. Why each failure failed

### 2a. The five failure types

| Type | What it means | Families where it is the main cause (proven unless marked) |
|---|---|---|
| Strategy failure | The idea loses before any cost | Altcoin event, recovery and listing rules; short holds; leader pullbacks; failed breakout; E6 momentum; mean reversion default; the 2026-11-08 dips in falling markets |
| Cost failure | A gross gain disappears after fees and slippage | Default breakout (+$139 before fees, -$16 at 0.25%); EMA cross default (+$45, -$19); reversal scan; funding carry; the candidate at 1.2% |
| Execution failure | The idea might work, but the bot's rules execute it badly | ES SMA-200: +854.4% with no exits, +1.3% with the runner's old default exits (in-sample, one asset). Default strategies: the runner's 2% trailing stop raised trades and fees (breakout 310 trades become 543). Entry filters block exit signals in the default strategies |
| Data failure | Results cannot be trusted because of the data | E6 stale prices for missing candles (corrected, still FAIL); BTC 2017-04-15 bad $0.06 low in the 10-coin daily file (affects only the dip study's worst-case statistic; the candidate uses opens and closes); E10 uses today's surviving coins (unmeasured bias) |
| Testing failure | The method produced misleading results | Dip-recovery screen (future information, withdrawn); the original 2026-10-08/09 execution assumptions (corrected under H-01); the research backtest filling at the signal bar's own close (BA-35, bias unmeasured); paper fills at mid price and 7.5 bps fees (BA-01, BA-02); one-second synthetic bars in paper runs |

### 2b. Family by family

| Family | Before costs | After costs | Cause | Proven or suspected | Evidence |
|---|---|---|---|---|---|
| Altcoin event, recovery, listing rules (about 544 configs) | Not recorded; losses of $399-$870 per $1,000 exceed the most costs could take ($80-$339) | $129-$601 from $1,000 against BTC $1,840 | Strategy (no signal edge) | Proven by the size of the loss relative to the maximum cost | `failure_diagnosis_20261030/` family table; `altcoins_corrected_rerun_20261009.md` |
| Short holds (14) | 13 of 14 lose at zero fees | All lose at 0.50% | Strategy | Proven | `short_hold_corrected_rerun_20261009.md` (CLAIMED from the diagnosis) |
| Leader pullbacks (10) | Negative mean before costs | All lose, in both halves | Strategy | Proven | `leader_target_test_20261012.md` |
| Hourly leader as one account | Event study positive per event | $1,000 to $493.06 (43 trades, 31 net winners, worst drop 80.73%) | Strategy: a few large losses outweigh many small wins; overlapping events looked better than a real account | Proven for this rule | `leader_single_account_20261012.md` |
| Failed breakout retest | Not recorded | $1,000 to $157.59 (167 trades, 52 winners) | Strategy | Proven | `failed_breakout_gap_replay_20261012.md` |
| E6 weekly momentum | Not recorded | $1,000 to $158 over 2018-2026 (drawdown 97%, turnover 31x a year) | Strategy and turnover | Proven; a data defect flattered it and the corrected rerun also fails | `xs_momentum_20261012/README.md` |
| Default breakout (OKX, signals only) | +$139 over 310 trades; positive on all 5 coins | -$16 at 0.25%, -$234 at 0.60% | Cost. The +$139 is not distinguishable from zero (t 1.45; 95% interval -$38 to +$336; top 10 trades made 169% of it) | Proven that costs remove it; the gross edge itself is not shown | `failure_diagnosis_20261030/` [C3] |
| Default EMA cross | +$45 over 129 trades | -$19 / -$110 | Cost, plus filters that block exit signals | Cost proven; the dollar effect of blocked exits was withdrawn by Codex's cross-review (2026-11-03) | same; correction at the top of that README |
| Default mean reversion | -$148 over 29 trades | -$162 / -$182 | Strategy; no loss exit in the signal function | Proven | same |
| Defaults with the runner's rules | Breakout +$140, EMA +$38, mean reversion -$36 | -$132, -$64, -$79 at 0.25% | Execution design: the 2% trailing stop closes most trades within hours, so trades and fees rise and big winners are cut | Proven on this data (in-sample, 9 months, OKX prices standing in for Coinbase) | `exit_parity_audit_20261031/` table 4 |
| Horizon scan (8 strategies) | Not reported separately | Almost every cell negative at 7.5 bps; positives are tiny samples (4 and 2 trades) | Strategy, small samples | Proven for these short windows | `strategy_horizon_scan_20261008.md` |
| Breakout campaign, BTC 5m (Sep) | -0.10%, profit factor 0.99, turnover 75x capital | -12.2% | No edge plus very high turnover | Proven | `breakout_economic_dissection_2026_09_23.md` |
| Funding carry | +$2 | -$5; -$25 after the server | Cost and capital size | Proven for $1,000 over 30 days | `funding_carry_feasibility_20261012.md` |
| Order-book imbalance pilot | Not recorded | -$15.99 at $100 per entry | Strategy (pilot) | Small pilot; not a full test | `fc01_r1_exploratory_result_20261004.md` |
| E7 / E8 / E10 | Not applicable | Each below the plain candidate (table 3c) | Added complexity did not help | Proven on the registered criteria | The three READMEs |
| E9 band | Not applicable | Better than the plain candidate in D and H at both fees | Failed only a turnover criterion the record calls mis-specified | Proven failure of the criterion, not of the idea | `candidate_band_20261013/README.md` |
| Candidate at the 1.2% stress fee | Positive | Below both fixed mixes on Sharpe in period A, below BTC on Sharpe in period C | Cost | Proven (registered REJECT) | `btc_eth_corrected_comparison_20261012/README.md` |
| Dips, 10 popular coins (2026-11-08) | Hourly year negative even with no fees | All 25 combinations lose at 0.50% (main rule) | Strategy in falling markets: misses held 30 days lost about 20% each | Proven, descriptive | `dip_recovery_majors_20261108/README.md` |

**Questions the owner listed, answered across families**
- **Poor entries:** proven for the altcoin rules, which lose before costs. For the default strategies, entries are
  not shown to be the problem: the correlation between the preceding 24-hour move and the result is weak, which
  cannot rule out every timing problem.
- **Exits too early or late:** proven for the runner's exit stack (2% trailing stop). Of the 83 breakout trades that
  reached +6%, the best points totalled +$1,040, the backtest's own exits kept +$509 and the runner's exit stack kept
  +$203.
- **Fees:** decisive for the default breakout and EMA cross, the reversal scan, carry, and the candidate at 1.2%.
- **Spread and slippage:** modelled as fixed assumptions (0.05%-0.30% per side), never measured (E1 not run).
- **Trading too often:** proven for the breakout campaign (75x turnover) and E6 (25-35x a year).
- **Market conditions:** the candidate and the dip trades do better in falling and rising markets respectively
  (section 3e).
- **Stops and take-profits behaving incorrectly:** EMA invalidation exits are inert, and a rejected exit is never
  retried (section 6). There is no evidence that a stop fired at the wrong price.
- **Implementation bugs affecting results:** E6 (stale prices) and the dip screen (future information) are proven
  and handled. The research backtest's same-bar fill (BA-35) is unmeasured.
- **Unrealistic backtest assumptions:** see section 5.
- **Overfitting:** the candidate was selected after about 576 configurations (DSR study count; the ledger now counts
  at least 747). Its registered robustness test failed at 1.2%: only 5 of 13 nearby settings beat the fixed mix.
- **Differences across coins:** the default breakout was positive before fees on all 5 coins. EMA cross was positive
  after 0.25% fees only on ETH and SOL (section 3b). The trend rule cut drawdowns on every coin in E10 but rarely
  improved risk-adjusted return.

---

## 3. Full numerical results

### 3a. The candidate (BTC+ETH 28-day trend)

$1,000 start, 0.50% fee plus 0.05% slippage per side, the reviewed corrected harness. Sources:
`btc_eth_corrected_comparison_20261012/README.md` (end values, Sharpe, drawdown) and
`candidate_descriptive_20261107/README.md` (trades, win rate, profit factor). Period A 2016-08 to 2019, B 2020-2023,
C 2024 to 2026-10-08.

| Measure | A | B | C | Full 2016-08 to 2026-10 |
|---|---|---|---|---|
| End value | $5,555 | $9,920 | $1,780 | $102,426 |
| Hold BTC end value | $11,782 | $5,862 | $1,837 | $134,319 |
| Hold ETH end value | $11,728 | $17,432 | $1,045 | $225,629 |
| Sharpe (rule / BTC) | 1.49 / 1.30 | 1.70 / 1.00 | 0.82 / 0.70 | 1.42 / 1.05 |
| Worst drawdown (rule / BTC) | 51.9% / 83.8% | 32.8% / 76.7% | 32.0% / 53.1% | 51.9% / 83.8% |
| Round trips (BTC / ETH) | 35 (19 / 16) | 38 (19 / 19) | 35 (20 / 15) | 108 (58 / 50) |
| Win rate after costs (round trips) | 34.3% | 47.4% | 31.4% | 39.8% |
| Average win / average loss | $922 / -$283 | $524 / -$181 | $135 / -$42 | $3,833 / -$1,235 |
| Profit factor after costs | 1.70 | 2.61 | 1.49 | 2.05 |
| Median holding spell | 28 days | 35 days | 21 days | 28 days |
| Days with trades (per year); entries / exits / resizes | 136 (39.8); 35 / 35 / 165 | 152 (38.0); 40 / 38 / 202 | 106 (38.3); 37 / 35 / 117 | 394 (38.7); 110 / 108 / 486 |
| Turnover per year | 8.8x | 9.2x | 12.8x | 11.3x |
| End value at 1.2% fee | $4,522 | $7,671 | $1,383 | $50,448 |

Other figures:
- Costs: at 0.55% per side, about 6% of capital a year.
- Exposure: invested about 37-48% of the time.
- Dollar averages over the full period are dominated by later, larger trades, because sizes grow with the account.
- From 2018-01: rule $13,434 (Sharpe 1.01, drawdown 52%) against BTC $6,027 (0.64, 81%).

**Forward paper (live public prices, not reused history)**
- v1 (`paper_btc_eth_trend_20261009/`, fee 0.60% plus 0.05%): started at the 2026-10-11 close. On 2026-11-08 the
  account was $941.21 (-5.88%, worst drop 5.88%) against BTC held $893.35. It has been all cash since the 2026-10-25
  rebalance. That is 4 weekly decisions.
- v2 (`paper_btc_eth_trend_v2_20261012/state/`): one week of marks to 2026-10-25. Rule $985.38, hold BTC $970.83,
  25/25/50 mix $982.95, cash $1,000. The 2026-11-01 and 2026-11-08 decisions were missed; the registration was
  restored on 2026-11-12.

### 3b. The bot's three default strategies (OKX hourly, 5 coins, 2026-01 to 09, $100 per entry, 0.05% slippage)

A = the existing signal-only backtest. C = the runner's rules. Source: `exit_parity_audit_20261031/README.md` table
4. Starting capital is not defined: fixed $100 per entry. Drawdown is on the closed-trade curve.

| Strategy | Variant | Trades | Before fees | Net at 0.25% | Net at 0.60% | Win rate | Profit factor | Max drawdown | Median hold |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Breakout | A | 310 | +$139 | -$16 | -$234 | 33% | 0.97 | $191 | 39 h |
| Breakout | C | 543 | +$140 | -$132 | -$512 | 31% | 0.77 | $180 | 6 h |
| EMA cross | A | 129 | +$45 | -$19 | -$110 | 36% | 0.93 | $161 | 85 h |
| EMA cross | C | 204 | +$38 | -$64 | -$207 | 29% | 0.72 | $87 | 8 h |
| Mean reversion | A | 29 | -$148 | -$162 | -$182 | 45% | 0.37 | $208 | 552 h |
| Mean reversion | C | 87 | -$36 | -$79 | -$140 | 21% | 0.29 | $85 | 11 h |

Holding the same five coins with the same $100 per entry lost $67 over the period. Average win and average loss:
not computed in that table. Sharpe: not computed.

**By coin, variant A** (`failure_diagnosis_20261030/diag_trades_result.json`, before fees / net at 0.25%):

| Coin | Breakout | EMA cross | Mean reversion | Holding, net at 0.25% |
|---|---|---|---|---|
| BTC | +$16.69 / -$14.35 (62 trades) | -$18.50 / -$29.95 (23) | -$19.87 / -$23.32 (7) | -$5.17 |
| ETH | +$33.59 / +$4.50 (58) | +$44.75 / +$33.64 (22) | -$33.32 / -$35.74 (5) | -$10.19 |
| SOL | +$51.69 / +$23.06 (57) | +$17.91 / +$1.87 (32) | -$57.23 / -$59.09 (4) | -$5.83 |
| ADA | +$5.93 / -$28.58 (69) | +$9.23 / -$4.29 (27) | +$3.16 / -$0.85 (8) | -$26.59 |
| XRP | +$31.17 / -$0.90 (64) | -$8.27 / -$20.75 (25) | -$40.45 / -$42.85 (5) | -$19.65 |

The research tool's "win rate" is before fees (BA-39). The after-fee win rates above come from the exit-parity
replay.

### 3c. Other families (from $1,000 unless stated)

| Family | End value or result | Benchmark same period | Trades | Win rate | Profit factor | Drawdown | Sharpe | Source |
|---|---|---|---|---|---|---|---|---|
| Altcoin selected candidates, 2024-26 test | Recovery $129.51; filtered recovery $446.42; new listings $601.00; accumulation $417.27 | BTC $1,840.38 | Not in summary | Not in summary | Not computed | 92.8% / 70.3% / 55.8% / 83.1% | Not computed | `consolidated_economic_summary_20261010.md` |
| Dynamic breakout 15%, recent about 53 days | $1,566.14 | BTC $1,292.32 | Not in summary | Not in summary | Not computed | 24.0% (BTC 7.8%) | Not computed | same; one trade (USELESS, +150%) carries it |
| Same rule, earlier 10 months | $126.88 | BTC $581.76 | Not in summary | Not in summary | Not computed | Not in summary | Not computed | same |
| Short holds, 14 variants | Recent $0-$737; earlier $0-$2 | Not in summary | Not in summary | Not in summary | Not computed | Not in summary | Not computed | same |
| Top-10 trend | 2020-23 $3,216.04; 2024-26 $1,204.80 | BTC $5,839.96 / $1,840.38 | Not in summary | Not in summary | Not computed | 36.6% / 30.0% | Intervals include zero | same |
| Binance hybrid | Best complete strategy +8.0% test-segment return | BTC +93.3% | Not in summary | Not in summary | Not computed | Not in summary | Not computed | `strategy_decision_report_20261011.md` |
| CMC proxy, selected | $293.78 (fee-only test, 0.50%) | Not in summary | Not in summary | Not in summary | Not computed | Not in summary | Not computed | `consolidated_economic_summary_20261010.md` |
| Pump/dip breakout events | Mean net per event +5.34% (3x volume, 114 events), +3.96% (2x, 195) | Not applicable | Events, overlapping | Not in summary | Not computed | Not applicable | Intervals include zero | same; not a portfolio |
| Hourly leader, one account | $493.06 | BTC $1,270.19 | 43 | 31 of 43 net winners | Not computed | 80.73% (BTC 7.80%) | Not computed | `leader_single_account_20261012.md` |
| Same plus filter | $619 | Not in summary | Not in summary | Not in summary | Not computed | Not in summary | Not computed | `edge_map_20261013.md` |
| Failed breakout retest | $157.59 | BTC $1,270.19 | 167 | 52 net winners | Not computed | 84.80% | Not computed | `failed_breakout_gap_replay_20261012.md` |
| E6 momentum top 5, 2018-26 | $158 (CAGR -19.0%) | Hold BTC (period A $2,836; B $1,756) | Not in summary | Not in summary | Not computed | 97% | 0.12 | `xs_momentum_20261012/README.md` |
| E7 braked rule, D 2020-12..2023, 0.50% | $3,548 | Plain candidate $3,654; BTC $2,171 | Not in summary | Not in summary | Not computed | 32.8% | 1.352 | `crash_brake_20261013/README.md` |
| E8 composite, D 2017-2023, 0.50% | $38,010 | Candidate $42,583; BTC $42,355 | Not in summary | Not in summary | Not computed | 45.0% | 1.592 | `composite_v1_20261013/README.md` |
| E8 composite, H 2024-2026-10 | $1,278 | Candidate $1,846; BTC $1,848 | Not in summary | Not in summary | Not computed | 34.0% | 0.450 | same |
| E9 band 0.10, D / H, 0.50% | $53,367 / $1,867 | Candidate $42,583 / $1,846 | 20.9 / 22.5 rebalances a year | Not in summary | Not computed | 54.0% / 32.0% | 1.620 / 0.883 | `candidate_band_20261013/README.md` |
| E10 10-coin trend, D 2019-2023 / H, 0.50% | $5,742 / $1,331 | Candidate $11,603 / $1,858 | Not in summary | Not in summary | Not computed | 42.4% / 38.9% | 1.20 / 0.51 | `multisymbol_trend_20261015/README.md` |
| Funding carry, $1,000, 30 days | +$2 funding; -$5 after costs; -$25 after the server | Not applicable | Hedge held | Not applicable | Not applicable | Not applicable | Not applicable | `funding_carry_feasibility_20261012.md` |
| Order-book imbalance pilot | -$15.99 ($100 per entry) | Not in summary | 17 entries | Not in summary | Not computed | Not in summary | Not computed | `fc01_r1_exploratory_result_20261004.md` |
| New top-100 entrants (all) | Mean +$139.05 per $1,000 four-week cycle; median -$1.25; worst -$528.27 | Broad top-100 control at least +$17.12 | 100 cycles | 29 of 100 cycles positive | Not computed | Not computed | Not computed | `low_value_top100_20261018/README.md` |
| New entrants, Coinbase only (ENTR-CB-1) | Paired mean -$7.17 per cycle against its control; -$30.00 without the largest cycle | Control basket | 34 funded cycles | Not in summary | Not computed | Not computed | Not computed | `coinbase_tradable_entrants_20261019/RESULTS_V1.md` |
| ES SMA-200, BTC daily 2018 to 2026-06, 7.5 bps, no exits | +854.4% | Hold BTC +674.6% | 31 | 22.6% | 2.80 | 64.3% | Not computed | `es_exit_policy_matrix_20261007.md` |
| Same with the runner's old default exits | +1.3% | Same | 35 | 31.4% | 1.02 | 20.4% | Not computed | same |
| Volatility forecast (VOLFC-1) | Rank correlation 0.5217 against 0.5123 for trailing volatility; +0.03 needed | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | `RESEARCH_BRIEF.md` section 4 |

Recovery, three ideas, CMC proxy and dynamic grids: full per-variant figures are in
`research/research_corrections_20261009/` (hashes in `consolidated_economic_summary_20261010.md`). They are not
repeated here.

### 3d. Paper runs through the actual bot
See table 1c.
- Combined, the bot's paper record holds about 30 closed strategy trades on hourly or daily settings, plus about 70
  one-second round trips from March and April.
- No run shows a positive result distinguishable from zero. ES v1 has 0 wins in 8 trades, and its mean of -$0.52 per
  trade has a 95% interval of -$1.05 to -$0.09. These are the 2026-10-05 figures, whose fee figures were later
  superseded (`economic_evidence_current_20261007.md`).
- Fees and slippage in these runs were set at 7.5 bps and 5 bps, below the account's 50 bps taker fee (BA-02), so
  they flatter the results.

### 3e. Performance by market condition
- **Candidate, all periods** (`candidate_descriptive_20261107/README.md`, weeks labelled by BTC against its 200-day
  average and that average's 20-day slope):

  | Weeks | Rule | Hold BTC | Hold ETH |
  |---|---|---|---|
  | Bear | +14% | -37% | -72% |
  | Mixed | +59% | +342% | Not repeated here |
  | Bull | +4,643% | +3,006% | +76,325% |

  The rule beat both holds in every calendar year BTC fell (2018, 2022, 2025, 2026), and gained less than BTC in 6 of
  the 7 years BTC rose.
- **Dips on 10 popular coins** (`dip_recovery_majors_20261108/README.md`, daily main rule, split with hindsight):
  - Years BTC rose: 10 of 25 combinations above zero at 0.50% both sides, best +0.48% per trade.
  - Years BTC fell: 0 of 25 above zero.
- **E6 momentum:** $1,120 in 2018-21 against BTC $2,836; $133 in 2022-26 against BTC $1,756.
- **E10 by coin:** per-symbol table in `multisymbol_trend_20261015/README.md`. Trend cut drawdowns by 10-50 points on
  every coin. Risk-adjusted return rarely improved, and DOT's trend Sharpe in H was -0.32.

---

## 4. The strategy that showed promise: BTC+ETH 28-day trend

| Question | Answer | Label and source |
|---|---|---|
| What made it perform better? | Being in cash during falling markets. It gained 14% in bear weeks while BTC lost 37%. The benefit is avoiding large drops, not picking better entries. It is invested about 37-48% of the time | SHOWN: `candidate_descriptive_20261107/`; `btc_eth_corrected_comparison_20261012/` |
| How much history supports it? | About 10 years of daily BTC/ETH (2016-08 to 2026-10), three separate periods | SHOWN |
| Tested on data never seen during development? | Partly. Period A (2016-07 to 2019) was declared unseen before the majors run, and is the cleanest slice. Periods B and C were used in selection, and 2024-26 was reused in later studies (`RESEARCH_BRIEF.md` rule 5.8) | SHOWN: `dsr_btc_eth_trend_20261011/README.md` |
| Tested on live prices? | Yes, as paper only: v1 for 4 weeks, v2 for 1 week, outside the bot | SHOWN: section 3a |
| Fees and slippage included? | Yes. 0.50% (the account's taker rate, read 2026-10-08) plus 0.05% slippage on every trade, including the benchmarks; also 1.2% | SHOWN |
| How many trades? | 108 round trips over 2016-08 to 2026-10 (35, 38 and 35 in the three periods), with a 39.8% net win rate. Trades fall on about 39 days a year, mostly small size adjustments (486 resizes over the full period). About 108 independent outcomes is a small sample | SHOWN: `candidate_descriptive_20261107/README.md` |
| Weaknesses that remain | No return edge over BTC: the active Sharpe is negative in every window. It is rejected at 1.2% fees. It was selected after a search of about 576 configurations (747 or more now). Only 5 of 13 nearby settings beat the fixed mix at 1.2%. It trails BTC in rising markets. It is not implemented in the bot. Forward data is 5 weeks in total, with 2 missed weeks | SHOWN: DSR, stress and comparison reports |
| Evidence still needed before calling it profitable | Forward results over a full market cycle that beat a fixed BTC/ETH-plus-cash mix after real costs, with a smaller worst drop than BTC. The rule was proposed on 2026-10-11 (`strategy_decision_report_20261011.md` section 5) but never adopted. Measured execution costs (E1). Implementation in the bot with a parity check | Proposal, not adopted |

**Is it being overstated?** The repository's own label, CANDIDATE, not established, is accurate. It would be
overstated if it were called profitable or better than holding. Over the full period it ended below holding BTC
($102,426 against $134,319 at 0.50%) and far below holding ETH. Its advantage is risk reduction, and that advantage
depends on costs.

---

## 5. Testing methodology and reliability

| Area | What was done | Weakness | Source |
|---|---|---|---|
| Data sources | Coinbase public candles (hourly for about 395 coins, 12 months; BTC/ETH daily since 2015-16; 10 coins daily since 2017-21); Binance daily, including delisted pairs; CMC weekly top-1000 snapshots 2018-2026; OKX hourly for the default-strategy replay; Binance funding | OKX USDT prices stand in for Coinbase USD in the default-strategy replay; CMC prices are reference prices, not fills | `raw_archives_20261009/README.md`; `exit_parity_audit_20261031/` |
| Frozen inputs | Archives with SHA-256 lists; later studies hash-check them | Hourly history covers only one year, 2025-10 to 2026-10, a falling market for all 10 large coins | `raw_archives_20261009/`; `dip_recovery_majors_20261108/` |
| Missing data | The corrected contract refuses gaps and does not forward-fill (since 2026-10-09). E6's original simulator traded at stale prices (H-02), corrected | The bot's runner has no candle freshness or gap check (BA-13) | `altcoins_corrected_rerun_20261009.md`; H-02 |
| Look-ahead | Decide at a close, trade at the next open (the corrected contract). No look-ahead found in the bot's signal code (BA-15). The dip screen used future information and was withdrawn (H-03) | The research backtest `run_parity_backtest` fills at the signal bar's own close (BA-35); bias unmeasured. This affects the ES matrix and the horizon scan | `bot_audit_20261031/` BA-15, BA-35 |
| Parameters changed after results | Pre-registration from 2026-10-09 on, for E6-E10 and the stress test. The 0.5% stress rerun was an operator-authorised exploratory rerun, labelled as such | E6 script deviated from its pre-registration; E7-E9 registrations were underspecified (H-04) | H-04 |
| Training and testing separated | Some studies used train/test windows (recovery, hybrid). The candidate's period A was declared unseen | Most data was reused across studies; no untouched holdout remains for BTC/ETH 2017-2026 | `RESEARCH_BRIEF.md` rule 5.8 |
| Multiple testing | Trial ledger floor of 747 configurations; DSR with N from 1 to 576 | The count is a floor, not complete (H-05) | `trial_ledger_reconciliation_20261015/` |
| Fees and slippage | 0.50% per side (account taker, SHOWN read 2026-10-08) plus 0.05-0.30% slippage; stress at 1.2% | Slippage is assumed, never measured. Maker fills (0.25%) never measured. Paper runs used 7.5 bps fees and mid-price fills (BA-01, BA-02) | `RESEARCH_BRIEF.md` line 556; bot audit |
| Executable prices | Research fills at the next open plus slippage | Not checked against real bid/ask; partial fills not modelled (BA-07) | Bot audit |
| Survivorship | Top-10 used all Binance pairs including delisted | E10 uses today's surviving Coinbase symbols, an unmeasured bias | `integrity_audit_20261015/METHODOLOGY_NOTES.md` |
| Reproduction | Integrity audit 2026-10-15: blind reimplementations reproduced the candidate's A/B/C results exactly once the same sizing convention was used | The perturbation results' findings live in a Claude Doc, not re-read for this audit | `integrity_audit_20261015/` |

**Tests known to be compromised, and what happened to them**
- **Original 2026-10-08/09 execution assumptions (H-01):** rerun under the corrected contract. Figures moved;
  verdicts unchanged.
- **E6 stale prices (H-02):** a corrected rerun was archived on 2026-10-15. Still FAIL.
- **Dip-recovery screen (H-03):** withdrawn.
- **The 2026-10-30 failure diagnosis:**
  - Its in/out-of-market attribution and blocked-exit dollar effects were withdrawn by Codex's cross-review on
    2026-11-03.
  - Its claim that the strategies "block their own exits" holds for the signal functions only.
- **Paper runs:**
  - Fees of 7.5 bps against the account's 50 bps (BA-02), and fills at mid price (BA-01).
  - The default strategies ran on one-second synthetic bars, not the hourly candles they were tested on.
  - So these runs neither confirm nor refute the backtests.
- **ES SMA-200, +854%:** in-sample, one asset, 7.5 bps fees, filled at the signal bar's close. It is the result
  most exposed to these issues.
- **Dynamic breakout, $1,566 recent:**
  - Chosen in hindsight as the best of its family.
  - One trade carries it.
  - The same rule lost 87% in the earlier window.

---

## 6. The trading bot itself (software, separate from strategies)

Sources: `bot_audit_20261031/` (BA-01 to BA-39, LP-01 to LP-13), `capital_protection_audit_20261031/` (CP-01 to
CP-15), `exit_parity_audit_20261031/` section 6, `PROJECT_STATE.md` engineering queue.

**Works as designed (SHOWN by reading or running)**
- Paper accounting is correct to the cent (BA-03).
- One gate in front of every exchange order (CP-01, LP-01).
- Duplicate live orders are refused (LP-02).
- The runner refuses to start on an unknown or open position (CP-11).
- The live consumer recovers stuck intents at restart (CP-10).
- Order precision is checked (LP-13).
- Credentials come from the OS keyring and are not logged (LP-12).
- **No strategy can reach a live order today: everything writes to the paper queue (CP-02).** This is not a
  guarantee that live submission is impossible.

**Defects found, and their status**

| Defect | Severity | Status |
|---|---|---|
| Several symbols in one runner: only the last symbol reaches decisions, exits and orders (D-1, CP-03) | HIGH | Fixed in source and independently reviewed (2026-11-03). Not on master; not deployed |
| A restart can lock an account out of trading for days (BA-16) | HIGH | Fixed in source (R1, accepted with risk). Not deployed |
| A rejected or refused exit is final; never retried (BA-05) | HIGH | Source groundwork accepted (R12). Wiring waits for owner decision 3. Open |
| Live exits are subject to entry limits such as the daily trade cap (CP-09) | HIGH before live | Open, parked as pre-live |
| Live position-size limit is read but never checked (LP-11, H-06) | HIGH before live | Open (engineering item 3, on hold) |
| Exposure-percentage limits never block (BA-24) | MEDIUM | Open |
| No protection on the exchange if the bot or server stops (LP-05) | HIGH before live | Open; owner decision needed on backstop orders |
| Live arming trusts an environment variable, not the enable ceremony (LP-08) | MEDIUM before live | Open |
| Paper fills at mid price, never bid/ask (BA-01); paper fees 7.5 bps (BA-02) | HIGH for evidence | Owner decided 50 bps for the simulation; fix or recording planned in the spec |
| A failed candle fetch skips the whole decision, exits included (BA-10) | MEDIUM | Open (record and alert planned) |
| No candle freshness or gap check (BA-13) | LOW to MEDIUM | Source for R4 (refuse buys on stale candles) written; not deployed |
| Nothing restarts the bot processes (BA-19) | MEDIUM | Open (R2 incomplete) |
| No alert if an account stops (BA-21) | HIGH for 24/7 | Open (R3 incomplete) |
| EMA invalidation exits are inert (exit-parity defect 2) | MEDIUM | Open |
| Default signal input is one-second synthetic bars (defect 3) | MEDIUM | Open |
| Entry filters remove most of the strategies' own exit signals (BA-09) | MEDIUM (strategy design) | Open by design |
| A failed daily-loss write counts as success (BA-28) | HIGH before live | Open; part of the 72 unapplied reviewed patches (LP-10, U-09) |
| Paper daily-loss and trade-count gates can never fire (BA-25) | MEDIUM | Open |
| Adds to winning positions (BA-23) | Conditional | Blocked by the default `position_aware` guard (O-107); risk only if that is switched off |
| 72 reviewed patches from early October never applied (LP-10) | HIGH (process) | Open; owner decision U-09 |

**The owner's specific questions**
- **Does the bot handle entries and exits correctly?**
  - Single symbol: yes as coded.
  - Several symbols: no, until the fix is deployed.
  - The default exit stack's 2% trailing stop fires before the 3% stop.
  - Exits are skipped when a candle fetch fails.
  - EMA invalidation exits are inert.
- **Can it recover after a restart?**
  - It refuses unknown positions (good).
  - But a restart can lock an account out (fixed in source only), a paper intent can strand at `submitting` (BA-18),
    and nothing restarts the processes (BA-19).
- **Are rejected orders handled safely?** No. A rejected exit is not retried (BA-05), and live exits can be blocked by
  entry limits (CP-09).
- **Are position limits enforced?**
  - Per-order and daily notional caps: yes.
  - The live position-size limit: no (LP-11).
  - Exposure percentages: no (BA-24).
- **Are exchange-side positions protected if the bot stops?** No (LP-05).
- **Kill switch:** on the laptop the kill switch has been armed since 2026-09-23 and the system guard HALTED since
  2026-10-09. Four old paper positions remain open in the paper ledger (exit-parity addendum).

**Strategy failures against software failures**
- No past trading loss is shown to be caused by a software defect. The losses are strategy and cost failures, plus
  the execution design of the default exits.
- The software defects above are risks for future paper or live trading, not explanations of past results. The
  exception is the paper runs, whose fee and fill settings make them unreliable as evidence.

---

## 7. The paper simulation decision

**Status:** not started and not deployed (`PROJECT_STATE.md` engineering item 2). Since 2026-11-12 it is on hold by
owner direction.

**What it would reveal that backtests cannot:**
- How the bot behaves on live data: missed or failed candle fetches, restarts, rejected orders.
- The real gap between expected and quoted prices at each fill (bid and ask recorded).
- Exits firing on time, and multi-symbol behaviour after the fix.
- These are execution and software questions.

**Weaknesses it would expose:** the open defects in section 6, under real conditions instead of code reading.

**Which strategies it should run:**
- As specified, it runs the three default strategies, which already lose after costs in the replay. It would mostly
  confirm their losses.
- To produce evidence on profit, it would need the BTC+ETH rule, which is not in the bot.
- The bot's `sma_200_trend` path shows a daily trend rule can be wired through the runner, but its default exit stack
  must be off for a trend rule. The ES matrix shows what the default exits do: +854% to +1.3%.

**Should BTC+ETH be integrated?** Only if the forward tracker keeps supporting it. That needs a parity check showing
the bot's version reproduces the research version trade for trade.

**Minimum period and sample:**
- The spec's minimum trade counts for the default strategies are 42, 42 and 31, derived from the replay (spec 7.4,
  awaiting owner approval). Its clock is 26 weeks.
- For a weekly rule, 26 weeks gives about 26 decisions and few round trips. That is enough to catch execution
  problems, not to prove profit statistically.
- The candidate's risk-reduction claim can only be checked through at least one significant market fall.

**Measures that would decide whether it deserves more work:**
- After-cost return against holding BTC and against a fixed BTC/ETH-plus-cash mix at the same average exposure.
- Worst drop against BTC's.
- Fill price against the quoted bid/ask.
- Missed decisions, and exits that fired late or not at all.

---

## 8. Recommendations: the next five actions

Ranked by whether they can establish or disprove a genuine advantage. This is Claude's assessment, for the owner to
decide; none is adopted.

1. **Keep the candidate's forward evidence running, and write a dated go/stop rule now.**
   - The tracker is the only evidence not reused from history.
   - The 2026-10-11 proposal is a ready starting point: after 6 months, keep the rule only if it beats the fixed mix
     after costs with a smaller worst drop than BTC; otherwise use a fixed allocation with no bot.
   - Cost: none beyond keeping the Mac awake for the scheduled runs.
2. **Measure real execution costs (E1, maker versus taker).** Costs are about 6% of capital a year at 0.50%. They
   decide the 1.2% rejection, and every point saved goes straight to profit.
3. **Test the candidate's mechanism on data it has never seen.** For example, the same frozen rule on stock-index
   ETFs. If trend-plus-volatility sizing fails there, the crypto result is more likely luck. Needs a data download and
   owner approval.
4. **Only if 1 to 3 hold up: put the BTC+ETH rule into the bot** with a trade-for-trade parity check and the default
   exit stack off. Then run a short paper trial with recorded bid/ask to measure the execution gap.
5. **Do not fund more strategy search on altcoin or short-term price patterns.** More than 10 families failed, and
   each new variant mainly adds false-positive risk (`edge_map_20261013.md`). Do not prioritise unfinished
   infrastructure (simulation alerts, backups, live safety) until a strategy passes item 1.

---

## 9. Supporting evidence (index)

| What | Where |
|---|---|
| Master result registers | `result_labels_20261031/result_labels.csv` (50 rows); `trial_ledger_reconciliation_20261015/trial_inventory.csv` (42); `RESEARCH_BRIEF.md` section 4 |
| Summaries of the 2026-10-09 to 10-13 program | `consolidated_economic_summary_20261010.md`; `strategy_decision_report_20261011.md`; `edge_map_20261013.md` |
| Candidate | `btc_eth_corrected_comparison_20261012/`; `dsr_btc_eth_trend_20261011/`; `btc_eth_stress_test_20261009/`; `stress_fee050_exploratory_20261011/`; `candidate_descriptive_20261107/`; `majors_trend_20261009/` |
| Candidate forward | `paper_btc_eth_trend_20261009/` (v1 ledger and state); `paper_btc_eth_trend_v2_20261012/state/` |
| Candidate extensions | `crash_brake_20261013/`; `composite_v1_20261013/`; `candidate_band_20261013/`; `multisymbol_trend_20261015/` |
| Corrected reruns and artifacts | `research/research_corrections_20261009/`; `altcoins_corrected_rerun_20261009.md`; `raw_archives_20261009/` |
| Default strategies | `exit_parity_audit_20261031/` (replay, trades CSVs); `failure_diagnosis_20261030/` (with corrections); `strategy_horizon_scan_20261008.md`; `es_exit_policy_matrix_20261007.md`; `breakout_economic_dissection_2026_09_23.md` |
| Bot paper runs | `paper_evidence_standing_20261005.md` (superseded fee figures; see `economic_evidence_current_20261007.md`); `server_workload_inventory_20261011.md`; `../checkpoints/es_prospective_endpoint_result_2026_10_16.md` |
| Altcoin studies | `leader_*_20261012.md`; `failed_breakout_gap_replay_20261012.md`; `xs_momentum_20261012/`; `low_value_top100_20261018/`; `coinbase_tradable_entrants_20261019/`; `dip_recovery_screen_20261012.md`; `dip_recovery_majors_20261108/` |
| Methodology | `integrity_audit_20261015/`; `trial_ledger_reconciliation_20261015/`; `PROJECT_STATE.md` history rows H-01 to H-07 and omission register |
| Software audits | `bot_audit_20261031/`; `capital_protection_audit_20261031/`; `exit_parity_audit_20261031/` section 6; `patch_inventory_20261031/` |
| Source code | `services/execution/strategy_runner.py`; `services/strategies/` (presets, registry, strategy modules); `services/execution/paper_runner.py`; `services/execution/place_order.py` and the live path files named in the audits |
| Configuration | Runtime config read 2026-10-31 through whitelisted keys only (`exit_parity_audit_20261031/` section 1); not re-read here |
| GitHub | Branch `backup/2026-10-31` at `3b49ead3f` (public); master `be34a18a3` lacks the reviewed fixes |

---

## 10. Final independent verdict

The verdict is Claude's, from the records above. It is not independently reviewed.

1. **Have we developed a strategy with demonstrated profitability after realistic costs?** No. No strategy has
   positive after-cost results on forward data, and none has traded real money.
2. **Which strategy has the strongest evidence?** BTC+ETH 28-day trend.
   - It has 10 years of history and higher Sharpe than BTC and fixed mixes in every period at 0.50%.
   - Its absolute Sharpe survives selection deflation, and it has smaller drawdowns in every period.
   - It has no return edge over BTC, is rejected at 1.2%, and has 5 weeks of forward data.
3. **Strategy design or software defects?**
   - The failures were overwhelmingly strategy failures (no signal edge) and cost failures.
   - The bot's default exit stack is an execution-design failure: it made the default strategies lose more, and turned
     an in-sample trend rule from +854% into +1.3%.
   - No past loss is shown to come from a software bug. The software defects are risks for future trading.
4. **Were previous tests compromised?** Yes, several (section 5): the original execution assumptions, E6's stale
   prices, the dip screen's future information, same-bar fills in the research backtest, and the paper runs' low fees
   and mid fills. All known cases were corrected or withdrawn, and none changed a failure into a success. The
   positives most exposed are ES SMA-200 (+854%) and the recent dynamic breakout ($1,566).
5. **Is BTC+ETH genuinely promising, or overstated?**
   - Promising as risk reduction: smaller losses in falling markets, at similar or lower return.
   - Overstated if called profitable or better than holding: it ended below holding BTC over the full period and in
     two of three sub-periods, and its advantage disappears at 1.2% costs.
6. **Is continuing justified?**
   - Only narrowly: low-cost forward tracking of the candidate, a cost measurement and one out-of-sample test, under a
     dated stop rule.
   - The repository's own objective accepts "no viable system yet" as an answer.
   - The evidence does not justify more strategy search on altcoins and short-term patterns, or infrastructure for a
     strategy that has not passed forward testing.
7. **What must happen before risking real money?**
   - Forward results that meet a go/stop rule written in advance.
   - Execution costs measured.
   - The strategy implemented in the bot, with a trade-for-trade parity check.
   - The pre-live safety items: position limit enforced (LP-11, BA-24); rejected exits retried and exits exempt from
     entry limits (BA-05, CP-09); a decision on exchange-side protection (LP-05); the multi-symbol fix deployed;
     restarts and alerts working (BA-19, BA-21); live arming tied to the ceremony (LP-08).
   - A capital decision, which also sets the loss limit (owner decision 2). At $1,000 the roughly $240 a year of
     infrastructure is a 24% hurdle on its own (`consolidated_economic_summary_20261010.md`).

---

## Limits of this audit
- It summarises existing records. It did not rerun any test, and its figures are as good as the records they come
  from.
- Records marked SHOWN in their own files were copied, not re-derived. CLAIMED entries rely on reports, not code.
- The integrity audit's perturbation findings live in a Claude Doc that was not re-read. The perturbation tests
  check whether results change when the input data is randomly disturbed.
- Server state was not inspected. The last read-only inventory of the server was on 2026-11-11.
- Per-variant numbers for the large grids are in the cited JSON files, not in this report.

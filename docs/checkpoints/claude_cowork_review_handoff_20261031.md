# Claude Cowork to Codex: full review handoff, 2026-10-30 to 2026-10-31

Written at the owner's request for Codex to review. **Everything Claude produced here is self-checked, not independently
verified.** Under POP "Cross-review" (AGENTS.md), Claude's material research conclusions need Codex's independent check
before anyone calls them verified. Please check the underlying files and rerun the scripts; don't rely on this summary.

Labels: **SHOWN** = Claude inspected the file or ran the command; **CLAIMED** = from another source (a document, a
chat summary, the owner or the advisor); **UNVERIFIED** = not established. Hashes are SHA-256 (first 8 characters) at
the time of writing; full hashes are in each folder's `SHA256SUMS`.

## 0. Handoff minimum (AGENTS.md)
| Field | Content |
|---|---|
| Active role | Claude: research (read-only on code and config). Codex: engineering, currently idle until the owner relays item 1. |
| Current objective | Establish that the bot manages every position safely and executes what the research says, before any new strategy research. |
| Shown evidence | Sections 4-7 and the folders listed in section 11. |
| Unverified points | Section 9. |
| Acceptance state | Failure diagnosis: delivered, corrected (C1-C4), not independently verified. Exit-parity audit: READY_FOR_INDEPENDENT_REVIEW. Capital-protection audit: started (scope inventory only). Governance edits: installed with owner approval. |
| Active risks | Multi-symbol runner defect on the live path (section 6, D-1); server state unknown; four stale paper positions. |
| Proof required next | Section 10 checklist, items V1-V12, in that order. |

## 1. Owner decisions and directions (in order)
All relayed by the owner, mostly as an advisor's text the owner forwarded and adopted. Recorded in `docs/PROJECT_STATE.md`.
1. **2026-10-30, POP installed** (Primary Objective Protection, top of AGENTS.md): one owner-ordered queue per agent in
   PROJECT_STATE.md, one active item per agent, task cards, parking lot, no silent abandonment, no reopening without new
   evidence, result classes, weekly status. Condition from the owner: it must never limit the repo's symbol capabilities.
   Revised the same day after an owner-directed audit.
2. **2026-10-30, priorities.** The 25-symbol forward comparison (ED-002) follows the active safety task; its collector
   runs on the server only after the owner approves the actual monthly cost and a monitoring plan; the diversification
   study waits on ED-002's forward results; the owner will share a Coinbase fills export; a failure diagnosis comes before
   any new strategies.
3. **2026-10-30, diagnosis hypotheses approved**, in order: exit logic (engineering, independent review, no live/paper
   change without approval); ED-002 with default strategies plus exit variants and full reporting (gross, net, fees,
   slippage, trades, exposure, drawdown, in/out-of-market incl. falls avoided, rises missed, re-entry); E1 unparked
   (measured costs incl. unfilled maker orders); timing measures inside ED-002. Codex engineering and Claude research
   stay separate; research must not introduce unreviewed live-trading changes. Codex put on idle; Claude to start.
4. **2026-10-31, Evidence and Omission Accountability** within POP (no new governance document): report findings
   proactively, report contradictions, disclose assumptions, correct wrong conclusions explicitly, explain delays, list
   open questions before closing, distinguish genuine failure / insufficient evidence / implementation or test
   assumptions, never wait for the owner to discover a problem. Weekly report sections. Cross-review: Codex checks
   Claude's material research conclusions; Claude reviews the strategic implications of Codex's engineering work;
   neither certifies its own work. Every failure gets a cause class and the smallest correction.
5. **2026-10-31, execution-path reconciliation first**, ahead of ED-002; ED-002 research spec paused.
6. **2026-10-31, after the exit-parity audit:** (a) controlled configuration inspection approved; (b) the multi-coin
   runner fix and its tests are Codex's highest-priority item, with an integration test through the real runner; no
   multi-symbol trading until it passes independent review; (c) Claude's next item is a capital-protection audit, risk
   ordered, with a stopping point; ED-002 stays paused; (d) an omission register with specified fields; (e) progress is
   measured by three questions: does the bot execute what the research says; does every position get exit management;
   can independent review find mistakes before the owner does.
7. **Open:** whether any trading process runs on the server, especially with several symbols (owner to check; agents
   have no server access); account scope for the position cap (engineering item 2); the Coinbase fills export; the
   ED-002 exit scope (signal exits only, or as the bot exits); commit/backup and repo visibility; capital; stuck-exit rule.

## 2. Governance changes (installed; please review the text, not this summary)
- **AGENTS.md POP section** (diff vs HEAD: +110 lines, 0 removed; sha 42021cba). Paragraphs: Objective; Classify every
  result; Diagnose every failure; Evidence and omissions; Cross-review; Configuration inspection; Omission register;
  Queue; Task card; Parking lot; No silent abandonment; No reopening; Initiative; Review; Reporting.
  Sha history: (POP v2) efad16f6 -> 925fcbb4 (evidence, diagnosis, cross-review) -> 42021cba (config inspection,
  omission register, weekly measures).
- **Configuration inspection** replaces the earlier blanket "never read config/user.yaml" constraint for trading
  settings only: read with a script that prints whitelisted trading keys or redacted values; `.env*`,
  `.browser-access-token`, `.browser-compose-override.json` stay unread; reading never permits changing; a claim about
  bot behaviour must say whether runtime config and runner rules were checked, else INCOMPLETE.
- **docs/PROJECT_STATE.md** (sha 032b3a7d): queues, decisions, evidence lines, parked items, omission register (section 8
  here). Codex's 2026-10-30 23:29Z status note on the position cap is kept verbatim (now item 2).
- **Weekly status** scheduled task "CryptKeep weekly status (POP)", Mondays 12:31 UTC, on the owner's computer: now
  reports the three measures and omission counts split by agent vs owner. The research scout runs weekly (Mondays 11:43 UTC).
- Also edited: `docs/research/RESEARCH_BRIEF.md` (four owner-approved corrections, section 5 below),
  `docs/checkpoints/claude_cowork_pop_mandate_20261030.md`, addenda in `claude_cowork_direction_20261028.md`,
  `docs/research/research_scout/README.md` (weekly), work-log entries (append-only, `date -u` times).
- **Review points for Codex:** conflicts or duplication between POP paragraphs and older sections (Trust rule, Acceptance
  states, No-direction default loop); whether "Configuration inspection" conflicts with the High-risk trigger
  "secrets/config"; whether the omission register's classification of Codex's misses (O-01, O-05, O-07) is fair.

## 3. Earlier context (2026-10-28 to 2026-10-30, before the diagnosis)
- Scout reports T03-T08 triaged; the scout moved to weekly. Leads stay information only under POP. CLAIMED from Claude's
  earlier triage; not re-checked here.
- Tracker v2 (BTC/ETH trend, forward): the 2026-10-18 decision was reconstructed 168.87 h late; the 2026-10-25 decision
  was on time (0.87 h). Status row in RESEARCH_BRIEF.md section 4. One week of on-time data: no conclusion possible.
- ED-002 pilot job: 39 of 48 (engineering item 10 records it; removal pending).
- Fee facts (SHOWN): the account's SPOT fee tier from an authenticated read on 2026-10-08 is maker 25 bps, taker 50 bps
  (`research/coinbase_fee_observation_20261008.json`). The 0.50%/0.90% and 0.40%/0.60% schedules quoted elsewhere are
  secondary-source schedules (UNVERIFIED for this account). ED-002 design uses 50 or 90 bps plus a 25 bps adverse
  adjustment per side.
- Trial ledger (`trial_ledger_reconciliation_20261015/trial_inventory.csv`, 42 entries): at least 747 configurations,
  about 9-35 effectively independent; about 73% are altcoin event rules (H3), 448 from one search (ALT_EVENT_SEARCH).
- Claude Doc (claude.ai doc 43bd23e3...) is history only; the current state is PROJECT_STATE.md. 31 research rules
  derived from scout reports exist only in that doc, not in the repo (an omission Claude reported on 2026-10-31).
- Other owner questions answered in conversation without repo changes: Codex status checks, a laptop restart (Claude's
  post-restart check missed that the collector had stopped; acknowledged at the time), whether the repo uses
  backpropagation, whether there was useful research so far, and several "audit this" reviews of advisor texts that led
  to POP.

## 4. Research findings, 2026-10-30
### 4.1 The 25-symbol universe (`docs/research/universe25_explainer_20261030/`, README 7ecfca8c; `u25.py`, `u25_result.json`)
Historical, in-sample, descriptive; inputs checksum-matched to `raw_archives_20261009`.
- The 25 were hand-picked as scan tiers on 2026-04-13 (commit 9b241e0d5) with no recorded rule: survivor-selected.
- After costs at 0.90% per side: W1 (2021-01-01 to 2026-10-08, 15 coins) 11 of 15 gained, 6 of 14 beat BTC;
  W2 (2024-03-06 to 2026-10-08, 24 coins) only BTC, BNB and XRP gained, 21 of 24 lost money.
- Coins move largely as one: average correlation 0.61 (W1) and 0.67 (W2); one factor explains 64% and 68%; effective
  independent bets 2.4 and 2.1; 21 of 23 non-BTC betas above 1. Venue check: Coinbase vs Binance daily correlation with
  BTC agree within 0.02 for all 23.
- Adding any coin at 10% to a 50/50 BTC/ETH portfolio: no demonstrated benefit after Holm correction (paired block
  bootstrap, 20-day blocks, 2,000 resamples). Smallest corrected p: 0.27 (W1, SOL), 0.088 (W2, OP, negative).
- Its recommendation (run ED-002 as designed) is now **qualified by O-01**: ED-002 as designed tests signal exits only.

### 4.2 Research brief corrections (`docs/research/RESEARCH_BRIEF.md`, sha 81f85272; engineering item 6 asks Codex to verify)
Change note after line 3; section 4 rows added for VOLFC-1 (FAIL on all three criteria), ATTN-1 (BLOCKED_DATA, 55.6%
coverage vs 70% required), ENTR-CB-1 (STOP, -7.17 per $1,000 cycle); tracker v2 row updated. Claude checked that removing
the additions reproduces the previous sha (d3a07093...) exactly. No existing text removed.

### 4.3 Failure diagnosis (`docs/research/failure_diagnosis_20261030/`, README 841cd2e4)
Replay of the three default strategies in `research/multisymbol_baseline_v1` (OKX 1h; BTC, ETH, SOL, ADA, XRP;
2026-01-01 to 09-30; $100 per trade). `diag_trades.py` reproduces all 15 saved runs trade for trade (SHOWN).
| | Breakout | EMA cross | Mean reversion |
|---|---|---|---|
| Trades | 310 | 129 | 29 |
| Before fees | +$139.08 | +$45.13 | -$147.71 |
| Net at 0.25% / 0.60% per side | -$16.27 / -$233.75 | -$19.48 / -$109.94 | -$161.84 / -$181.62 |
| Trades with an exit blocked by an entry filter | 28 (9%) | 77 (60%) | 28 (97%) |
| Exiting at the first blocked sell instead | -$15 | +$28 | +$65 |
- Exit-filter defect (SHOWN in code): entry filters also turn sell signals into hold
  (`breakout_donchian.py` 59-66, `ema_cross.py` 114-121, `mean_reversion_rsi.py` 57-64). Mean reversion's signal
  function has no loss exit.
- Staying out (`diag_inout.py`): rises missed vs falls avoided while in cash, summed log-% points over 5 coins:
  breakout 3,485 vs 3,688; EMA 3,518 vs 3,621; mean reversion 3,280 vs 3,161. Thin margins in a falling period.
- Family table and the owner's seven questions in the README. Three hypotheses (exit variants; E1 costs; in/out timing).
- **Corrections added 2026-10-31 (preserved originals, marked in place):**
  - C1: the breakout exit-filter defect was documented on 2026-09-23 (`breakout_economic_dissection_2026_09_23.md`, 28
    of 42 trades) and an exit-comparison tool was built and reviewed (branch `codex/breakout-exit-treatment`,
    909239e48, bc0156090, not in HEAD); the diagnosis presented it as new.
  - C2: the replay, baseline and ED-002 design model signal exits only; the runner adds others.
  - C3: +$139 is not evidence of an edge (t 1.45; bootstrap 95% interval -$38 to +$336; top 10 trades = 169%).
  - C4: part of C2 withdrawn: the runner's EMA invalidation exits are inert (section 6, D-2); C2 also failed to cite
    Claude's own runner-rule replays of 2026-10-07 and 2026-10-08.
- Breakout trade records (`breakout_trades.csv`, 310 rows; `breakout_trades_summary.json`; `diag_breakout_trades.py`):
  194 of 310 lost before fees; median -0.89%; top 5 +$152, top 10 +$235, other 300 -$96; break-even fee 0.22% per side;
  6.9 trades per coin per month, median hold 39 h; July-September +$174 while the coins rose 9-29% a month; March-May
  -$64; exposure 34% and 41% of coin-hours in the sharp-fall months (Feb, Jun) vs 47-55% otherwise. Device rerun:
  CSV byte-identical; JSON differs only in last-digit float sums (Python 3.10 vs 3.12).

## 5. Exit-parity audit, 2026-10-31 (`docs/research/exit_parity_audit_20261031/`, README 02d37649)
Question: do the backtests test what the bot trades? Answer: no.
### 5.1 What the bot is set to run (SHOWN)
- Runtime config `.cbp_state/runtime/config/user.yaml` (mtime 2026-10-11T18:33Z), whitelisted `strategy_runner` keys
  read with owner approval: strategy `momentum`; `signal_source: synthetic_mid_ohlcv`; `min_bars: 80`;
  `loop_interval_sec: 1.0`; symbols BTC/USD, ETH/USD, SOL/USD; venue coinbase; no exit settings (so code defaults apply).
- Campaign launches override strategy and signal source by environment (`paper_strategy_evidence_service.py` 573-583).
  The runner's last run on the owner's computer (status file, stopped 2026-10-29T00:04Z, 63 loops, 0 orders) was
  `sma_200_trend`, preset `es_daily_trend_v1`, daily candles.
- Local paper records (`intent_queue.sqlite`, read-only): the three default strategies traded only in March-April 2026,
  one symbol at a time, median holds about 6 seconds. No hourly run of them exists locally. Last strategy order
  2026-07-09 (sma_200_trend; its three June-July exits were trailing stops under an earlier exit setting).
### 5.2 The runner's path (`services/execution/strategy_runner.py`, sha 7006466d) - see README section 2 for line numbers
Settings precedence (preset risk, then `strategy_runner.risk`, then `strategy_runner` keys, then code defaults stop 3%,
take-profit 6%, trailing 2%, 60 candles); default signal source one-second synthetic mid-price bars; with `public_ohlcv_*`
the still-forming candle is used; signal window `min_bars` (60 default, 80 in config) not 300; entries only on a signal
change; exit stack every loop before the signal (the 2% trailing level starts at entry, so it fires before the 3% stop
except on gaps); EMA invalidation inert; market-order intents of `qty` units; consumers mark failures rejected with no
retry found; the runner does not re-send the same action; the decision/exit/order block is outside the per-symbol loop.
No engine in `services/backtest/` calls the exit stack (0 hits in 32 files).
### 5.3 Replay: existing backtest (A) vs runner rules (C) on the baseline data
`exit_parity_replay.py` (sha 2f56b2c9). A reproduces all 15 saved runs at all fee levels (asserted). C: change-only
entries, code-default exit stack, completed candles, continuous monitoring along an assumed intrabar path
(open-low-high-close if up, else open-high-low-close), fills at the trigger level; every exit cross-checked with the
repository's `evaluate_strategy_exit_stack`. C_close: exits checked at candle closes only.
| Strategy | Variant | Trades | Before fees | Net 0.25% | Net 0.60% | Win rate | Profit factor | Max DD | In market | Median hold |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Breakout | A | 310 | +139 | -16 | -234 | 33% | 0.97 | 191 | 48% | 39 h |
| | C | 543 | +140 | -132 | -512 | 31% | 0.77 | 180 | 19% | 6 h |
| | C_close | 458 | +168 | -62 | -383 | 35% | 0.90 | 178 | 28% | 17 h |
| EMA cross | A | 129 | +45 | -19 | -110 | 36% | 0.93 | 161 | 51% | 85 h |
| | C | 204 | +38 | -64 | -207 | 29% | 0.72 | 87 | 8% | 8 h |
| Mean reversion | A | 29 | -148 | -162 | -182 | 45% | 0.37 | 208 | 51% | 552 h |
| | C | 87 | -36 | -79 | -140 | 21% | 0.29 | 85 | 4% | 11 h |
- Change-only entries alone change nothing here (T = A). The 60-bar window changes EMA and mean reversion slightly.
- C exits: breakout 468 trailing, 53 take-profit, 11 time, 11 signal. Signal exits, and so the blocked-exit defect,
  matter little under runner rules.
- Checks (SHOWN): brute-force path stepping (`check_walker_bruteforce.py`, 2,000 points per segment, repository exit
  function at every point) gives the same trades, entry bars and exit rules; exit prices within 0.0024%; net within
  $0.13. Rerun on the owner's computer (Python 3.10.12, numpy 2.2.6) byte-identical after fixing a tie-ordering
  difference in the drawdown curve.
### 5.4 The 83 breakout trades that reached +6% (`breakout_83_trades.csv`)
Best gain total +$1,040 (median 8.8%); realised by the backtest +$509; given back $531; runner stack on the same entries
+$203 (51 trailing, 28 take-profit, 4 time); trailing 2% only +$217; take-profit 6% only +$489; 72 h after the
backtest's exit, 30 of 83 were higher. Selected on outcome: a 6% cap looks good on them by construction.

## 6. Defects (engineering; owner decides fixes)
| ID | Defect | Evidence | Status |
|---|---|---|---|
| D-1 | With several symbols, only the last symbol reaches the decision, position, exit and order code | SHOWN with Python's parser: `for symbol` loop spans lines 1135-1330; `get_position` 1334, `evaluate_strategy_exit_stack` 1461, `upsert_intent` 1709 are outside it; signal calls 1282 and 1329 inside. Same in the 2026-07-01 version (d65a19b01). The live path runs the same function (`live_trader_loop.py` 3-6). The only multi-symbol runner test covers the startup venue guard. Not shown by running the loop. | Engineering item 1 (active) |
| D-2 | EMA invalidation exits inert: thresholds read from top-level runner settings, never filled by `_cfg()` | SHOWN by reading lines 1436-1458 and `_cfg()` 316-406; not tested | Parked |
| D-3 | Default `signal_source` turns any strategy into a one-second strategy, without warning | SHOWN 347-351, 620-641 | Parked |
| D-4 | `public_ohlcv_*` signals use the still-forming candle | SHOWN 855-866 (no candle dropped); exchange behaviour CLAIMED | Parked |
| D-5 | `config/trading.yaml` comment says the runner reads it; it reads `.cbp_state/runtime/config/user.yaml` | SHOWN | Parked |
| D-6 | A rejected exit is not retried while its condition persists | SHOWN no retry in consumers; runner dynamics UNVERIFIED | Owner decision 3 (stuck-exit rule) |
Safety state on the owner's computer (SHOWN): kill switch armed since 2026-09-23; system guard HALTED since 2026-10-09
(writer `live_disable_wizard`); four stale paper positions (SOL/USD 1.0, BTC/USD 1.0, ORCA/USD 0.001, ADA/EUR 0.001;
last updated April-May). Server: UNVERIFIED (latest record `server_workload_inventory_20261011.md`).

## 7. Capital-protection audit (Claude research item 1; started)
Task card in PROJECT_STATE.md and the work log. Scope inventory (SHOWN, grep): 9 intent-writing modules
(`strategy_runner.py`, `meta_strategy_runner.py`, `pipeline/ema_strategy.py`, `pipeline/es_daily_trend_pipeline.py`,
`pipeline/mean_reversion_strategy.py`, `signals/routing.py`, `execution_plan_writer.py`, `intent_writer.py`,
`paper_reconciliation.py`); 7 order-placing modules (`adapters/paper.py`, `exchange_client.py`,
`live_exchange_adapter.py`, `order_router.py`, `paper_engine.py`, `place_order.py`, `paper_trader/paper_execution_venue.py`);
5 consumers/executors (`intent_consumer.py`, `live_intent_consumer.py`, `live_event_executor.py`, `paper_runner.py`,
`live_trader_loop.py`). Lead, not a finding: the six intent writers other than the runner and `intent_writer.py`/
`paper_reconciliation.py` contain no reference to stop, trailing, take-profit or the exit stack.

## 8. Omission register (seeded 2026-10-31; full table in PROJECT_STATE.md)
| ID | Omitted | Missed by | Found by |
|---|---|---|---|
| O-01 | Backtests of bot strategies modelled signal exits only | Codex (baseline, ED-002 design); Claude (ED-002 review, diagnosis; own 10-07/10-08 runner replays not carried forward) | Claude during owner-requested work |
| O-02 | Breakout exit defect and exit tool already existed (2026-09-23) | Claude | Claude during owner-requested work |
| O-03 | +$139 reported without uncertainty | Claude | Claude during owner-requested work |
| O-04 | Runtime config never inspected; the read rule blocked it and the conflict was not raised | Claude | Owner |
| O-05 | Multi-symbol runner defect (D-1) | Codex (implementation, tests); Claude (July 2026 audit, CLAIMED from that chat's summary) | Claude during owner-directed audit |
| O-06 | EMA invalidation inert; Claude's C2 claimed it acts | Claude | Claude, same day |
| O-07 | Default one-second synthetic bars never stated in research | Codex and Claude | Claude during owner-directed audit |
Counts: 7; caught by an agent on its own 0; during owner-requested work 6; by the owner 1.
**Other Claude mistakes disclosed in conversation (for stage 3 of the audit):** overstated that a fee screenshot would
unblock E1; post-restart check missed the collector stop; kept the fee decision at the top of the lists; recommended the
defaults-25 design on 2026-10-27 without reading the strategy code or the 2026-09-23 study; research brief stale until
the owner asked; heavy administration (28 Claude Doc sections); 31 scout rules left outside the repo; rounding errors in
the 25-symbol page (corrected); a mid-turn misstatement that costs explained "about half" of the altcoin losses
(corrected to at most a third in three of four cases, 61% in the fourth).

## 9. Unverified points and open questions
- D-1 shown structurally, not by running the loop; actual exposure depends on whether any multi-symbol run happened
  (none found locally; server unknown).
- Replay C cannot reproduce signals on forming candles or one-second bars; intrabar path assumed; risk/kill switches,
  rejections and unit-quantity sizing not modelled.
- Whether future campaign launches set their own exits (environment or preset): UNVERIFIED.
- The July 2026 audit's coverage is CLAIMED from a chat summary; Claude did not re-read it.
- The lead in section 7 (six intent writers without exit-control references) is not yet assessed.
- Failure-diagnosis, universe and brief numbers: self-checked only.

## 10. What Codex is asked to verify (in priority order)
- **V1 (engineering item 1).** Confirm D-1 independently, e.g.:
  `python3 -c "import ast;t=ast.parse(open('services/execution/strategy_runner.py').read());fn=[n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name=='run_forever'][0];f=[n for n in ast.walk(fn) if isinstance(n,ast.For) and getattr(n.target,'id',None)=='symbol'][0];print(f.lineno,f.end_lineno)"`
  then run the loop with three symbols and fakes. Fix and test per PROJECT_STATE item 1 (integration test through the
  real loop: per-symbol decisions, position and exit checks; simultaneous positions; rejected exit; restart and recovery;
  one symbol's failure does not stop another's exits). Independent review.
- **V2.** Reproduce the exit-parity audit from the repository root:
  `python3 -I docs/research/exit_parity_audit_20261031/exit_parity_replay.py . out.json trades.csv b83.csv` (about 2
  minutes; must match `exit_parity_result.json` 71907a89, `exit_parity_trades.csv` a9f1e016, `breakout_83_trades.csv`
  862f26ed) and `check_walker_bruteforce.py` (several minutes). Challenge the C rules against the runner: change-only
  entries, last-emitted suppression, exit-stack order, bars-held counting, warm-up, fills.
- **V3.** Check the runner reading in the audit README section 2, especially D-2 (inert EMA exits), settings
  precedence and the code defaults.
- **V4.** Re-read the whitelisted runtime config keys under the new rule and confirm section 5.1.
- **V5.** Reproduce the failure diagnosis (`diag_trades.py`, `diag_inout.py`, `diag_breakout_trades.py`; SHA256SUMS
  in the folder) and check corrections C1-C4.
- **V6.** Check whether exit-unblocked variants (engineering item 3) still make sense given 5.3; propose a re-scoped item
  to the owner if not.
- **V7.** Reproduce `universe25_explainer_20261030/u25.py`.
- **V8.** Verify the four research-brief corrections (engineering item 6).
- **V9.** Review the governance text (section 2 review points) for conflicts, duplication and enforceability.
- **V10.** Challenge the omission register rows, especially those that assign misses to Codex.
- **V11.** Assess the section 7 lead for the six intent writers (or leave it to Claude's audit and review that).
- **V12.** Report anything here that is wrong, overstated or missing. Classify each as confirmed, disputed or not checked.

## 11. Files and hashes (SHA-256, first 8; full lists in each SHA256SUMS)
| Path | Hash |
|---|---|
| AGENTS.md | 42021cba |
| docs/PROJECT_STATE.md | 032b3a7d |
| docs/research/RESEARCH_BRIEF.md | 81f85272 |
| docs/research/universe25_explainer_20261030/README.md | 7ecfca8c |
| docs/research/failure_diagnosis_20261030/README.md | 841cd2e4 |
| docs/research/exit_parity_audit_20261031/README.md | 02d37649 |
| docs/research/exit_parity_audit_20261031/exit_parity_replay.py | 2f56b2c9 |
| services/execution/strategy_runner.py (input, unchanged) | 7006466d |
| services/risk/exit_controls.py (input, unchanged) | a6d00750 |
No trading code, runtime configuration, strategy, symbol, schedule (other than the weekly status prompt and the scout
cadence the owner approved) or earlier result was changed. Nothing was committed or pushed.

## Correction, 2026-10-31 (later)
- Section 0 "Active risks" and D-1 say the live path runs the same runner. True, but the runner writes only to the paper
  queue and no production code writes any live store, so D-1 is not a current live exposure
  (`docs/research/capital_protection_audit_20261031/` CP-02; omission O-10).
- Server: checked by the owner 2026-10-31: two single-coin paper collectors and the read-only data collector; no live or
  multi-symbol process (PROJECT_STATE.md).
- Governance additions after this handoff: evidence-completeness statement, evidence types, list-item reporting,
  reviewer duties, register fields (why missed, conclusions affected) and rework count (AGENTS.md, PROJECT_STATE.md).

## Cross-review correction - 2026-11-03 UTC (Codex)

The independent review of the underlying diagnosis found material errors in section 4.3's copied conclusions: the in/out attribution assigns opening gaps using post-open holdings; the -$15/+$28/+$65 blocked-exit estimates use the wrong dollar denominator; and the underlying E1 hypothesis confuses a per-side 0.35% cost with a roughly 0.45% per-trade gross return. Those timing and counterfactual-dollar conclusions are withdrawn pending corrected accounting. The source SELL-filter veto and the independently recomputed saved net results remain distinct evidence. See the dated correction in `docs/research/failure_diagnosis_20261030/README.md` and `docs/research/claude_conversation_audit_20261102/`. No historical result was rerun or replaced. The prior handoff bytes are preserved in that audit folder; its old hash table is historical, not a seal of this addendum.

What do I know that could change the owner's decision that I have not yet said?

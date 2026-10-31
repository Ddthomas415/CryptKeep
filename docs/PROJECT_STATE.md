# PROJECT STATE

The single source of truth for priorities, decisions and status. Item tags: [research], [safety], [operations]. The owner orders it; agents propose changes.
Rules: `AGENTS.md`, "Primary Objective Protection (POP)".
Last updated: 2026-10-31 08:26Z by Claude Cowork (Codex status note on engineering item 1 kept verbatim) at the owner's direction. HEAD 389020130 (2026-10-19); uncommitted entries: about 540.

**Scope.** POP orders work; it never narrows symbol scope. Supported universe: the 25 symbols in
`config/candidate_universe.yaml` (`docs/research/MULTI_SYMBOL_MANDATE.md`); per-symbol status in
`research/symbol_coverage.csv` (41 rows; its 4 registry checks passed on 2026-10-30).

## Evidence now
- No strategy has shown an advantage on forward data yet; tracker v2 has one week.
- BTC+ETH 28-day trend rule, historical and in-sample: higher Sharpe than holding BTC and than fixed BTC/ETH/cash
  mixes in every window at 0.50% per side, and smaller drawdowns (risk reduction). No return edge over holding BTC
  since 2016; rejected at the 1.2% stress fee. Sources: `btc_eth_corrected_comparison_20261012/`, `dsr_btc_eth_trend_20261011/`.
- At $1,000 of capital, about $240 a year of infrastructure cancels its 2024-26 return (`strategy_decision_report_20261011.md`).
- Other symbols and families: `research/symbol_coverage.csv`; negative results are scoped to their tested conditions.
- Default breakout, historical and in-sample (OKX hourly, 5 coins, 2026-01 to 09, $100 per trade): +$139 before fees on 310
  trades, not distinguishable from zero (95% interval -$38 to +$336); the top 10 trades made 169% of it; it breaks even at
  0.22% fee per side. Self-checked (`failure_diagnosis_20261030/`, corrections C1-C3).
- No strategy can reach a live order today: every intent writer writes the paper queue and no production code writes
  any live store (`capital_protection_audit_20261031/` CP-02). Every exchange order goes through one gate,
  `place_order.py` (kill switch, system health, arming, balance), CP-01. Before any live launch: D-1, CP-09 and the
  portfolio cap must be fixed and tested. D-1 and CP-09 shown by running (probes, 2026-10-31); the 169 existing tests
  for these areas pass with both defects present. Self-checked.
- Of 42 recorded results with a trading outcome, 30 (about 743 configurations) tested rules the bot cannot run,
  including the only CANDIDATE (BTC/ETH 28-day trend; no implementation found in the bot); 5 tested the bot's signals
  only; 3 replayed the bot's rules; 4 were bot paper runs. Only the exit-parity audit checked the runtime config.
  (`result_labels_20261031/`, self-checked.)
- Backtests of the bot's own strategies, the diagnosis and the ED-002 design test signal exits only. The runner enters
  only on a signal change and adds stop 3%, trailing 2%, take-profit 6% and a 60-candle hold (code defaults; the active
  config sets none). Replayed with those rules, the three default strategies still lose after costs on the OKX data
  (net at 0.25%: breakout -$132, EMA cross -$64, mean reversion -$79, against -$16/-$19/-$162 as backtested). Self-checked
  (`exit_parity_audit_20261031/`). (Corrected 2026-10-31: the EMA invalidation exits named here earlier are inert.)
- The runtime config (read 2026-10-31 with owner approval, whitelisted keys) runs `momentum` on one-second synthetic
  bars for BTC/ETH/SOL; campaign launches override it. No hourly-candle run of the three default strategies exists.

## Owner decisions (at most 3 open)
1. Approve commit and backup of the work, and whether the GitHub repo is made private first. Urgent (audit S4-07): the
   last 12 days of work (547 uncommitted entries, on local branch checkpoint/2026-10-19) exist only on the laptop.
2. Capital: the amount the system is for, or "engineering project for now".
3. Approve the stuck-exit rule: keep a rejected exit pending with a reason and an alert; never convert, reprice, mark filled, drop or cancel it.
- Blocking engineering item 2 (Codex note below): confirm whether the DEFAULT portfolio holds all your Coinbase coins and open orders.
- Decided 2026-10-30: the 25-symbol comparison follows the active safety task (now item 4, after the multi-coin fix and exit logic); its collector runs on the
  server once the owner approves the actual monthly cost and a monitoring plan; the diversification study waits on its
  forward results; the owner will share a Coinbase fills export; a failure diagnosis comes before any new strategies.
- Decided 2026-10-30: the diagnosis hypotheses are approved; order of new work: exit logic, the 25-symbol comparison with exit
  variants, E1, timing measures inside the comparison. Research changes must not introduce unreviewed live-trading changes.
- Decided 2026-10-31: POP now requires a cause diagnosis for every failure, evidence and omission reporting, and
  cross-review (AGENTS.md). Codex independently checks Claude's material research conclusions; Claude reviews the
  strategic implications of Codex's engineering work; neither certifies its own work.
- Decided 2026-10-31: the execution-path reconciliation audit comes before the 25-symbol comparison is frozen or collected.
- Decided 2026-10-31 (owner): controlled configuration inspection (AGENTS.md); the multi-coin runner fix and its tests
  are Codex's highest-priority item; the capital-protection audit is Claude's next research item; the 25-symbol
  comparison stays paused; no multi-symbol trading until the fix passes independent review. Open: whether any trading
  process runs on the server, especially one with several symbols (owner to check; agents have no server access).
  Owner's MacBook checked 2026-10-31: no bot process running; kill switches armed in `crypto-bot-pro` and
  `crypto-bot-pro-test`; `crypto-bot-pro` system guard HALTED. Server checked by the owner 2026-10-31: no live-trading
  process and no multi-symbol process; running are two single-coin paper collectors (ema_cross, BTC/USDT, Gate.io and
  Binance, 5-minute candles, since 2026-09-16) and the read-only crypto-edge data collector (since 2026-10-24). No
  kill_switch.json or system_guard.json found on the server's root filesystem (for the capital-protection audit).
- Next when one closes: approve the server cost and monitoring plan for the 25-symbol collector (Codex to report them).

## Engineering queue (Codex; one active)
1. [active] [safety] Multi-coin runner fix (owner, 2026-10-31: highest priority). First confirm the defect independently
   (`exit_parity_audit_20261031/` section 6 and addendum). Fix the per-symbol structure of `run_forever` so every
   symbol gets its own entry decision, position check, exit checks and order step. Done when an integration test that
   drives the real runner loop (not only unit tests) shows, with three symbols: each symbol independently gets entry
   decisions, position checks and exit checks; simultaneous positions; a rejected exit order; restart and recovery; and
   one symbol's failure (no price, error, rejected order) does not stop another symbol's exit management. Independent
   review. No multi-symbol paper or live trading until it passes. No other runner behaviour change without approval.
2. [safety] Position cap (fix 4) with complete balance reading (fix 1), wired into the live order path; independent review.
   INCOMPLETE (Codex, 2026-10-30): default-off paging and native-v3 funding/quote guards are separately accepted source work
   (245 offline cases independently passed). All-account cap integration is not complete. The October 29 metadata check
   returned one matching default portfolio, not proof that it covers all manual holdings and open orders. Need account-scope
   confirmation before selecting a production evidence provider; no further private call or cap-policy activation authorized.
   The accepted synthetic reservation model is not being reopened. This safety dependency does not block paper/research.
   Blocked on the owner's account-scope answer.
3. [safety] Exit logic in the three default strategies (owner-approved 2026-10-30, priority 1 of the new work): entry filters
   currently block sell signals (`failure_diagnosis_20261030/`). Establish the separation between entry conditions and
   exit/risk controls; build exit-unblocked variants as separate configurations without changing the defaults; offline
   tests; independent review. No change to live or paper execution without review and owner approval.
   First: independently check the failure diagnosis's and the exit-parity audit's material conclusions (cross-review). Start from the existing
   exit-comparison tool on branch `codex/breakout-exit-treatment` (909239e48, reviewed 2026-09-23, shelved for lack of
   eligible data and runner parity; not in HEAD). Resolve the scope gap: say which exits each variant tests, signal
   only or the runner's (invalidation, stop, take-profit, trailing, hold limit).
4. [research] 25-symbol forward comparison (ED-002): protocol frozen before collection, with the existing default strategies
   plus the approved exit variants, benchmarks, costs and acceptance criteria; held-coin rule for limit-only or delisting
   announcements; reporting per strategy and coin of gross and net returns, fees, slippage, trade count, exposure and
   drawdown, and in-market versus out-of-market returns (falls avoided, rises missed, exit-to-re-entry price change).
   Collector on the server; report the actual monthly cost and a monitoring plan; deploy only after owner approval.
5. [research] E1 maker-versus-taker study (unparked by the owner 2026-10-30): measured execution costs on BTC and ETH,
   including unfilled maker orders finished as taker. As designed it models fills from public order-book data; measuring
   real fills needs live orders, which is a separate owner decision behind the safety items.
6. [research] Verify Claude's four research-brief corrections of 2026-10-30 (owner-approved) in `docs/research/RESEARCH_BRIEF.md` section 4.
7. [operations] Protect the work: commit and backup. Starts as soon as decision 1 is approved.
8. [safety] Stuck-exit rule (fix 2) wired, after decision 3; independent review.
9. [research] Tracker v2 stays on time: the 2026-10-18 decision was reconstructed 168.87 hours late; the 2026-10-25 decision
   was on time (0.87 hours). Confirm the next weeks run on time.
10. [operations] Remove the expired ED-002 pilot job (`com.cryptkeep.ed002.public-inputs`) and record the 39-of-48 pilot result.

## Research queue (Claude; one active)
1. [active] [safety] Capital-protection audit (owner-approved 2026-10-31; read-only). Stage 1 delivered 2026-10-31,
   READY_FOR_INDEPENDENT_REVIEW (`docs/research/capital_protection_audit_20261031/`). Stage 2 delivered 2026-10-31
   (`docs/research/result_labels_20261031/`), started without waiting for Codex because it does not depend on stage 1
   (owner: agents must not stall on each other). Stage 3 delivered 2026-10-31
   (`docs/research/omission_history_20261031/`). Stage 4 delivered 2026-10-31 (`docs/research/integrity_checks_20261031/`).
   All four stages READY_FOR_INDEPENDENT_REVIEW; stopped. Decision it serves: whether every
   route that can place an order manages every position correctly. Done when each order route (strategy runner, live
   trader loop, pipelines, intent consumers, paper engine) has an explicit assessment of: per-symbol exits, rejected and
   retried orders, restart and recovery, kill switch, position cap and balances; and every finding has an owner,
   evidence (SHOWN, CLAIMED or UNVERIFIED), severity and disposition; then Codex verifies the findings. Budget: two
   sessions. Stop rule: stop when the defined checks are done; no fixes, no new research, no configuration change.
   Stages 2 (label every result signal-only, bot rules or paper) and 3 (historical omissions and failed review
   controls) follow, in that order, then stage 4 (owner "carry on", 2026-10-31): backtest integrity (look-ahead,
   survivorship, missing candles, redenominations), data integrity, operations (scheduled tasks, backups, stopping
   all trading), the quality of Codex's tests, whether the rules work, and why reviews missed what they missed.
   Each stage has defined checks and stops when they are done.
2. [handed back for cross-review 2026-10-31] [research] Execution-path reconciliation audit (owner direction 2026-10-31).
   Report delivered (`docs/research/exit_parity_audit_20261031/`); acceptance needs Codex to reproduce it (engineering item 3).
   Establish what the paper/live runner actually trades (entries, exits, stop/take-profit/trailing, hold limit, EMA
   exits, config overrides, rejection and retry), which exits each backtest engine models, a replay of the three default
   strategies with the runner's exits (existing backtest vs corrected), the 83 trades that reached +6%, and which earlier
   conclusions could change. No new strategies, fee optimisation, universe change or scope expansion. Done when the
   findings are reproducible by another agent from the saved scripts, commands and hashes; then report and stop.
3. [paused 2026-10-31, owner direction] [research] ED-002 research specification: define the measurements above (gross and net, fees, slippage, trades,
   exposure, drawdown, in-market versus out-of-market with falls avoided, rises missed and re-entry gaps), state the
   exit-variant arms' hypotheses and pass/fail in advance, and review Codex's freeze before collection starts. No new arms
   beyond the approved exit variants. Open question for the owner before the freeze: should the comparison test the
   strategies' signal exits only (as designed) or also as the paper/live runner would exit them?
4. [research] Owner trade-history study: waiting on the owner's Coinbase fills export (CSV). The raw file stays out of the
   repository; only aggregate, de-identified findings are saved. Trade-level profit after actual fees against holding BTC and cash.
5. [research] E1 analysis once its data exist.
6. [research] Descriptive report on the candidate: market regimes, holding ETH alone, trade count, win rate, profit factor.
   Labelled descriptive, not a test. Needs owner approval.
- Done 2026-10-30: failure diagnosis (`docs/research/failure_diagnosis_20261030/`); its three hypotheses were approved with the order above.
- [dependent] Multi-symbol diversification pre-registration: waits on the 25-symbol comparison's forward results (owner 2026-10-30).
- [recurring] Weekly status, Mondays 12:31 UTC (scheduled task).

## Parked (not started until the owner moves it into a queue)
- Pre-live defects from the capital-protection audit (2026-10-31), reported at once because they could lose money once
  live routing exists: CP-09 exit orders are blocked by entry limits (daily loss, trade count, notional, market-order
  switch) and a rejected exit is never retried; CP-04 meta strategy runner buys repeatedly without position checks or
  exits (keep it off); CP-12 two inert live executors. For Codex review and owner decision; no fix without approval.
- Other runner defects found 2026-10-31 (`exit_parity_audit_20261031/` section 6): EMA invalidation exits inert; default
  one-second synthetic bars; signals on the forming candle; misleading `config/trading.yaml` comment. For Codex review
  and owner decision; no fix without approval. (The multi-symbol defect is engineering item 1.)
- Rest of fix 3 (funding-rate data). Previously approved work, parked by Claude on 2026-10-30 under the owner's
  "proceed with the best approach"; owner to confirm or move back. Reason: no live decision uses it. The existing
  300-second collector keeps running.
- Fee screenshot (useful, not blocking).
- Dedicated Coinbase portfolio and key: required before any live money.
- CMC failure alerts (window opens 2026-11-10); state of residence; tax lot method; USD vs USDC.
- New strategy families outside the 25-symbol work, ML and sentiment research.

## Closed (reopen only with new evidence)
Done 2026-10-30: 25-symbol analysis (`docs/research/universe25_explainer_20261030/`); its recommended next experiment is the 25-symbol forward comparison (now engineering item 4).
E6, E7, E8, E9, E10, VOLFC-1, ATTN-1, ENTR-CB-1. CTREND-OOS on hold.

## Omission register (AGENTS.md "Omission register"; seeded 2026-10-31 with omissions found that day)
Found by: A = agent review on its own; R = agent during owner-requested work; O = owner. Historical entries before
2026-10-30 are added by the capital-protection audit's stage 3.
| ID | Omitted | Should have been found | Missed by | Changed a result or decision | Why missed | Conclusions affected (status) | Found by | Control | Control tested |
|---|---|---|---|---|---|---|---|---|---|
| O-01 | Backtests of the bot's strategies modelled signal exits only, not the runner's entry rule and exit stack | 2026-09-23 (parity named as required); 2026-10-08 baseline; 2026-10-27 ED-002 review; 2026-10-30 diagnosis | Codex (baseline, ED-002 design); Claude (ED-002 review, diagnosis; own 10-07/10-08 runner replays not carried forward) | Yes: default-strategy results; ED-002 design | research method; evidence discovery | multisymbol baseline results, failure diagnosis, ED-002 design, 25-symbol recommendation: relabelled signal-only in exit_parity_audit; ED-002 paused | R, Claude 2026-10-31 | Search and cite prior work (POP); proposed shared decision function for bot and backtests | No |
| O-02 | Breakout exit-filter defect and an exit-comparison tool already existed (2026-09-23) | 2026-10-27, 2026-10-30 | Claude | Yes: diagnosis presented it as new; ED-002 carried it | evidence discovery | failure diagnosis: corrected (C1) | R, Claude 2026-10-31 | Search and cite prior work (POP) | No |
| O-03 | Breakout +$139 before fees reported without its uncertainty (t 1.45) | 2026-10-30 | Claude | Yes: headline overstated | reporting | failure diagnosis headline: corrected (C3) | R, Claude 2026-10-31 | Evidence labels (POP) | No |
| O-04 | Runtime config never inspected; the never-read rule blocked it and the conflict was not raised | Every bot-behaviour conclusion | Claude (did not raise it) | Yes: exits assumed from code defaults | configuration visibility; instruction | every bot-behaviour claim: exit_parity_audit used the inspected config; earlier claims labelled | O, owner direction 2026-10-31 | Configuration inspection rule | Once (whitelisted read 2026-10-31) |
| O-05 | Runner with several symbols: only the last symbol reaches decision, exit and order code | By 2026-07-01; Claude's July audit | Codex (implementation, tests); Claude (July audit) | Unknown: no multi-symbol run found in local records | implementation; verification | any multi-symbol run (none found on the MacBook or server): engineering item 1 open | R, Claude 2026-10-31 (owner-directed audit) | Integration test (engineering item 1) | No |
| O-06 | Runner EMA invalidation exits are inert; Claude's correction C2 said they act | 2026-10-31 | Claude | Corrected the same day (C4) | verification | correction C2: corrected (C4) | R, Claude 2026-10-31 | Read the code path before claiming behaviour; cross-review | No |
| O-07 | Runner default signal source is one-second synthetic bars; never stated in research | Any research on runner strategies | Codex and Claude | Yes: the default strategies' paper runs are not comparable with hourly backtests | research method; evidence discovery | default strategies paper runs (Mar-Apr) not comparable with hourly backtests: labelled in exit_parity_audit | R, Claude 2026-10-31 | Bot-rules label on results (proposed) | No |
| O-08 | Already held the server's last known state (`server_workload_inventory_20261011.md`: the same two single-coin paper collectors, PIDs 1541537 and 1541539) and cited it in the exit-parity audit, yet told the owner the server was unknown and had him run commands that only confirmed it | 2026-10-31, before asking the owner | Claude | No decision changed; cost the owner time | evidence discovery; reporting | none (owner time) | O, owner 2026-10-31 | Before asking the owner to check or do anything, state what the repo already shows and what the check would add; let the owner decide if it is worth doing | No |
| O-09 | Implemented only part of the advisor's Evidence and Omission Control text (2026-10-31) without listing what was left out: no evidence-completeness statement at completion, no evidence-type distinction, no root-cause class or affected-conclusions field in this register, no rework count, no reviewer duty to search for omissions, no conflict and duplication review of the rules, and no diff shown before installing | 2026-10-31, when reporting the installation | Claude | No decision changed; the owner believed more was in place than was | reporting | owner view of the governance state: corrected 2026-10-31; missing items installed | O, owner 2026-10-31 | When implementing a list, report each item as done, partly done or not done | No |
| O-10 | Told the owner the multi-coin defect "would apply to real money too" because the live loop runs the same runner, without checking where the runner's intents go: only the paper queue; nothing writes any live store | 2026-10-31, before making the claim | Claude | Contributed to the owner's priority call (the fix stays first: it is needed before multi-symbol paper results or any live bridge) | verification | exit_parity_audit addendum and review handoff: corrected 2026-10-31 | R, Claude 2026-10-31 (capital-protection audit) | Trace a claim's path to the order before stating its consequence | No |
| O-11 | Capital-protection audit CP-14 described the position cap without citing the brief's 2026-10-20 finding that `check_live` parses a position-notional limit but never checks it | 2026-10-31, when writing CP-14 | Claude | No decision changed; CP-14 corrected | evidence discovery | CP-14: corrected | R, Claude 2026-10-31 (audit stage 3) | Task cards list the searches run and earlier documents found (proposed) | No |
| H-01 | Altcoin, short-hold and majors studies used execution assumptions replaced by the corrected execution contract | 2026-10-09, at the original runs | Not recorded | Figures moved; verdicts unchanged | research method | reruns in research_corrections_20261009: corrected | Not recorded | Corrected execution contract | Yes (reruns) |
| H-02 | E6 simulator executed at a stale last close for missing candles; downloader could save incomplete files | 2026-10-12, before registration | Not recorded | E6 kept as defective record; FAIL unchanged | implementation; verification | E6: corrected rerun archived 2026-10-15 | A, review 2026-10-12 | Pre-stated corrected rule; blind re-implementation | Yes |
| H-03 | Dip-recovery screen used future information | 2026-10-12, before reporting | Not recorded | Screen withdrawn | research method | withdrawn | Not recorded | None recorded | No |
| H-04 | Survey citations overstated (1 contradicted, 14 partly supported); mandate said 25 coins trade on Coinbase (24 do); E6 script deviated from its pre-registration; E7-E9 registrations underspecified | 2026-10-12 to 10-15, when written or reviewed | Claude (survey, mandate wording); registration reviews | Wording corrected; no verdict changed | reporting; verification | survey, mandate, E6, E7-E9: corrected or documented | A, Claude integrity audit 2026-10-15 | Citation audit; blind re-implementation | Yes (once) |
| H-05 | Trial count of 576 and effective-N estimates were not a verified count | Before 2026-10-11 use | Not recorded | Deflated-Sharpe inputs relabelled | verification | DSR inputs: relabelled historical | A, ledger reconciliation 2026-10-15 | Trial ledger | Yes |
| H-06 | E7 reused funding history treated as untouched; `check_live` never checks its position-notional limit | 2026-10-13 (E7); when the gate was written | Not recorded | Disclosure required; limit unenforced on that path | research method; implementation | E7 disclosure; position cap: engineering item 2 | Not recorded (reviewed corrections, 2026-10-20) | None for the gate yet | No |
| H-07 | July 2026 codebase audit did not find the multi-symbol runner defect (CLAIMED from a chat summary) | 2026-07 | Claude | Defect persisted about 4 months | verification | D-1: engineering item 1 | R, Claude 2026-10-31 | Integration test (item 1) | No |
Counts 2026-10-31: 11 omissions found since the register began (O-01 to O-11): caught by an agent unprompted 0; during
owner-requested work 8; by the owner 3. Historical H-01 to H-07 (`omission_history_20261031/`): found by agent review 3,
during owner-requested work 1, not recorded 3.
Rework 2026-10-31 (accepted or closed work later corrected): 4 - failure diagnosis (closed 2026-10-30; C1-C4),
25-symbol analysis (closed 2026-10-30; recommendation qualified), multisymbol baseline (2026-10-08; relabelled
signal-only), ED-002 design (reviewed 2026-10-27; exit scope reopened).

## Open caveats (owner-approved 2026-10-31; each line stays until closed with evidence; new work is checked against it)
- C-01 Research results mostly do not describe the bot: 30 of 42 are STANDALONE, 5 SIGNAL_ONLY (`result_labels_20261031/`).
- C-02 The BTC/ETH candidate has no implementation in the bot (name search, 2026-10-31).
- C-03 Runner with several symbols serves only the last symbol (D-1; engineering item 1).
- C-04 Exits are blocked by entry limits and never retried (CP-09; `place_order.py`, live consumer, `check_live`).
- C-05 Portfolio position cap not enforced; `check_live` ignores its position-notional limit (CP-14, H-06; item 2).
- C-06 Runner defaults: one-second synthetic bars; forming candle with `public_ohlcv_*`; EMA invalidation exits inert.
- C-07 Live routing from strategies is not wired; any bridge needs its own reviewed design (CP-02).
- C-08 Earlier runner-rule replays (2026-10-07, 2026-10-08) did not check the runtime config: INCOMPLETE.
- C-09 E10 survivorship bias unmeasured; the 25-symbol list is survivor-selected.
- C-11 No automatic alert if the data collector stops (S4-05).
- C-10 Fee schedules other than the account tier (maker 0.25%, taker 0.50%, read 2026-10-08) are UNVERIFIED.

## Recurring
- Weekly status: Mondays 12:31 UTC (scheduled task "CryptKeep weekly status (POP)").
- Research scout: Mondays 11:43 UTC.
- Tracker v2 (Codex automation); weekly v1 paper test until v2 proves reliable; CMC daily log; existing 300-second research collector.

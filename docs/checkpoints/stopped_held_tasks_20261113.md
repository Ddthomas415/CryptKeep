# CryptKeep: every task stopped, on hold, parked, waiting, stalled, dropped or closed

As of 2026-11-13 19:30 UTC. Compiled by Claude (Cowork), read-only. Sources:
- `docs/PROJECT_STATE.md` (queues, Parked, Undecided ideas, Closed, omission register);
- `docs/work_log/review_stabilized_work_log.md`;
- `REMAINING_TASKS.md`;
- `docs/checkpoints/claude_cowork_direction_20261028.md`.

Everything is SHOWN by reading those files unless marked otherwise. No queue, task or file was changed to make this
list.

## 1. Held or parked by an agent, not by the owner's explicit words

| # | Task | Held by, when | Recorded reason | Now |
|---|---|---|---|---|
| 1 | Paper simulation of the bot (engineering item 2) | Claude, 2026-11-12 18:03 UTC, reading the owner's "stick to tasks that shows promise" as option C | Claude's reading of a one-line reply; never confirmed | **Hold withdrawn** 2026-11-13 19:23 UTC. Owner told Codex "finish the simulation tasks"; Codex task active since 19:25 UTC |
| 2 | Position cap with complete balance reading (eng 3) | Same option C reading | "Only matters for the simulation or live money" | Still held; also blocked on the owner's account-scope answer |
| 3 | Exit logic in the three default strategies (eng 4; owner-approved 2026-10-30 as "priority 1 of the new work") | Same option C reading | Same | Still held |
| 4 | 25-symbol forward comparison, ED-002 (eng 5) | Same option C reading (the owner had already paused it 2026-10-31 behind the multi-coin fix) | Same | Still held |
| 5 | Stuck-exit rule wiring (eng 9) | Same option C reading | Same | Still held |
| 6 | Remove the expired ED-002 pilot job and record the 39-of-48 result (eng 11) | Same option C reading | Same | Still held |
| 7 | Whole-bot audit for flaws (research 1, owner 2026-10-31) | Same option C reading | Same | Still held, unfinished |
| 8 | Cross-reviews of Claude's capital-protection audit and execution-path audit (research 2, 3) | Same option C reading | Same | Still held; never cross-reviewed |
| 9 | Weekly triage of research-scout reports (research 9) | Same option C reading; proposed, never approved | Same | Still held |
| 10 | Stock-index ETF test of the same trend rule | Proposed by Claude in option C; withdrawn by Claude 2026-11-12 (second-stage review) | Volatility sizing inactive at index volatility; the bot cannot trade ETFs | Dropped |
| 11 | Rest of fix 3, funding-rate data | Claude, 2026-10-30, under the owner's "proceed with the best approach" | No live decision uses it | Parked; "owner to confirm or move back" |
| 12 | UNLOCK-1 and FRESH-1 historical work | Claude's 2026-10-28 direction note ("Hold, do not start") | Host baskets lost 74-95% | Owner decision never recorded |
| 13 | Module A/E11 allocator, Polymarket counts, Coinbase Preview Orders log | Same note | Preview log needs the owner's API key | Held |
| 14 | CTREND-OOS | The owner's 25-symbol choice; listed as held in the same note | Superseded by the 25-symbol work | "On hold" in Closed |

## 2. Stopped by the owner

| # | Task | When | Owner's words or reason | Now |
|---|---|---|---|---|
| 1 | R10 encrypted off-server backups (part of the simulation) | 2026-11-12 04:48 UTC | "Stop the backup (R10) work where it is and don't run the downloaded tools" | Stopped. **This now blocks the simulation:** the composed service target produces no runnable units without the required backup role (Codex, 2026-11-13 19:25 UTC). Codex has asked you to clarify |
| 2 | Native backup tool | Owner-authorised single retry 2026-11-12 17:44 UTC crashed (SIGABRT) | Not a proven permission denial | Parked |
| 3 | 25-symbol comparison | 2026-10-31 | "Stays paused" until the multi-coin fix passes | Also held by item 1.4 |
| 4 | ED-002 research specification (research 4) | 2026-10-31 | Owner direction | Paused |
| 5 | Dip-recovery study follow-up | 2026-11-08/09 | "If this didn't produce any useful data back to thinking" | Closed after the study |

## 3. Waiting on the owner (decision or action)

| # | Item | Waiting since | What it blocks |
|---|---|---|---|
| 1 | Decision 1: push group D (unreviewed backup commit), large-data backup | 2026-10-31 | Today's work is also uncommitted: frozen criteria, forensic audit, verification, diagnostics, scripts, tests |
| 2 | Decision 2: capital amount, or "engineering project for now" | 2026-10-31 | Sets the simulation's drawdown limit and minimum trade samples, needed before its start |
| 3 | Decision 3: stuck-exit rule for the live path | 2026-10-31 | Live path |
| 4 | Account scope: does the DEFAULT portfolio hold all Coinbase coins and open orders? | 2026-10-30 | Position cap (eng 3) |
| 5 | OV-01 security: check and rotate `.env.docker` (in GitHub history since 2026-01-22) | 2026-10-31 | Security |
| 6 | Coinbase fills export (owner trade-history study, research 5) | 2026-10-30 | Measuring your real fees and fills |
| 7 | Server cost and monitoring plan for the 25-symbol collector | 2026-10-30 | Eng 5 |
| 8 | Heartbeat provider and account provisioning (spec v2) | 2026-10-31 | Simulation commissioning |
| 9 | Missed-run check for the trackers and CMC ("create the check") | 2026-11-12 | Catching a missed Sunday decision in time |
| 10 | E1 public quote capture from this Sunday's open (yes/no) | 2026-11-13 | Measuring maker fill rates |
| 11 | Simulation: A full spec or B unofficial trial now | 2026-11-13 | Engineering item 2 route |
| 12 | BA-23 to BA-27: disable adds in the simulation or model them; exposure and loss gates that never fire | 2026-11-05 | Like-for-like simulation |
| 13 | Pre-live defects CP-09, CP-04, CP-12 and runner defects (inert EMA invalidation exits, one-second synthetic bars, forming-candle signals, misleading config comment) | 2026-10-31 | "No fix without approval" |
| 14 | Pursue, park or drop for U-01 to U-49 (section 7) | 2026-11-05 | All blank |

## 4. Started but not finished

| # | Task | State |
|---|---|---|
| 1 | Multi-coin runner fix (eng 1) | Code independently accepted 2026-11-03; not deployed |
| 2 | R3 Linux deployment target | Linux image test passed 2026-11-11 02:14 UTC (7 fixtures). Host preflight, local candidate composition and offline unit composition were accepted 2026-11-11. The runnable release, configuration and sizing, permissions and delivery are still open; the target refuses to run without the R10 backup role |
| 3 | R4 price identity and freshness, R6 observed-hour host commissioning | Open |
| 4 | Deployment to the server, 72-hour commissioning, review, owner approval, official start | Not started. Codex's completion task (19:25 UTC) is working toward this |
| 5 | Group B (ranker-picked coins) | Staged after Group A; not started |
| 6 | Tracker v2 on time (eng 10) | 1 of 4 decisions on time; 1 Nov and 8 Nov missed; restored schedule unverified; first in-window run Sunday |
| 7 | CMC daily log | No entries 10, 11, 13 Nov; Codex diagnosis 2026-11-13: study INCOMPLETE, repair needs its own scope |
| 8 | E1 maker-versus-taker costs (eng 6) | Capture tool built; one Friday capture INCOMPLETE (ETH); no Monday data |
| 9 | E1 analysis (research 6) | Waits on E1 data |
| 10 | Bot integration of the BTC+ETH candidate (Q3) | Not authorised; Codex estimate 4-8 sessions, unverified |
| 11 | v3.3 cost, per-coin, ETH-control and 0.90% evaluator | Not built; needed by May 2027 |
| 12 | Verify Claude's four research-brief corrections (eng 7) | Not started |
| 13 | Group D commit | Unreviewed; Codex fixes needed before merge |
| 14 | Four release/signing workflows | Offline repair accepted 2026-11-12; published runs still failing |
| 15 | Dated correction notes on Claude's forensic audit and second-stage review | Proposed 2026-11-13; not done |

## 5. Dropped, ignored or removed

| # | Item | What happened | Source |
|---|---|---|---|
| 1 | October review series: 72 reviewed patches (Claude, 2026-10-07) | Never applied; only patch 0004 reused | O-18, U-09 |
| 2 | Cooldown restart lockout (found 2026-10-02, patches reviewed 2026-10-07) | Missing from the queue until 2026-10-31; now R1, done in code | O-15 |
| 3 | Exit-comparison tool, branch `codex/breakout-exit-treatment` (reviewed 2026-09-23) | Shelved; not in HEAD | O-02 |
| 4 | Research order agreed in July | Replaced in September, then again in October; two unlinked task lists | O-21 |
| 5 | 191 unmerged branches, 118 with work not in master | No list of wanted or obsolete | U-45 |
| 6 | Two old paper collectors on the server since 2026-09-16 | Output unused; not stopped | U-47 |
| 7 | Shadow-stage session (simulated-fill records) | Recorder on master since September; never run | U-06 |
| 8 | Original AI plan, phase 2; AI engine; `services/learning` | Never built, never trained, never connected | U-03, U-04 |
| 9 | MCB-1 market-context baseline | Stage 1 partly built, never activated; stages 2-3 never built | U-08 |
| 10 | Measurement layer ("adopt now", 2026-10-11) | Not built | U-10 |
| 11 | Research copilot, about 130 failing tests | No decision | U-48 |
| 12 | UNLOCK-1, FRESH-1 | Not carried into PROJECT_STATE on 2026-10-30 | U-12, U-13 |
| 13 | BA-23 owner decision request | Withdrawn 2026-11-06 after Codex's qualification | Work log |
| 14 | Duplicate weekly-status scheduled task | Disabled by Claude 2026-11-12 (duplicate; no work lost) | Session record |

Correction: Claude's 2026-11-13 19:23 UTC queue note said the next simulation step was the R3 image test. That was
wrong; the test had already passed on 11 Nov. Codex corrected the note at 19:25 UTC.

## 6. Closed with evidence (reopen only with new evidence)
- E6, E7, E8, E9, E10, VOLFC-1, ATTN-1, ENTR-CB-1.
- 25-symbol analysis, done 2026-10-30.
- The candidate's registered stress test: REJECT at 1.2% fees, unchanged.

## 7. Never started: undecided ideas U-01 to U-49 (PROJECT_STATE, 2026-11-05; owner column blank)
- **Research directions:**
  - U-01 lower-value and prospect coins;
  - U-02 short holding periods;
  - U-03 machine learning role;
  - U-05 whale concentration screen;
  - U-07 walk-forward coin selection;
  - U-14 FUND-1 funding hypothesis on unseen data;
  - U-15 VENUE-1 outage context;
  - U-16 volatility-targeted holding;
  - U-17 trend rule on the 15 untested mandate coins;
  - U-18 liquidation rebound;
  - U-19 Coinbase listing study;
  - U-20 low-volatility factor;
  - U-21 Module A allocator;
  - U-22 ETF and stablecoin flows, sentiment and value measures;
  - U-23 token-contract and wash-trading screens, sector rotation;
  - U-24 altcoin focus.
- **Settings and process never answered:**
  - U-25 live venue, direction, risk gates, stress level, turnover cap, server, tax, altcoin benchmark;
  - U-26 sealed holdout;
  - U-27 30 proposed research rules;
  - U-49 data and spending envelope.
- **Scout approval items, all unanswered:** U-29 to U-43. These cover:
  - spread-estimator check;
  - cost report download;
  - Polymarket logs;
  - Coinbase transfer incidents;
  - hack screen;
  - open-interest flag;
  - ETF flow log;
  - index changes;
  - unlock calendar;
  - volatility estimators;
  - Preview Orders log;
  - VIP3 promotion terms;
  - status feed;
  - Kraken haircuts.
- **Engineering:**
  - U-11 spread/timing veto gate;
  - U-44 the 19-item pre-live backlog (section 8);
  - U-46 isolated paper account, strict market quality, patch 0011.

## 8. Deferred until before live money (`REMAINING_TASKS.md`, 19 items)
1. Decimal order maths with venue step sizes.
2. Fail-closed trading config.
3. Typed exchange-error retry classification.
4. Crash-consistency tests for submit, fill and reconcile.
5. Server deployment units, or retire them.
6. Trading-loop metrics and dead-man alerting.
7. State-store decision record.
8. Full-state backup and restore drill.
9. Evidence-write failures surfaced in status.
10. Single config authority.
11. Clock and venue-time checks.
12. Server secrets and rotation model.
13. Supply-chain verification.
14. Operator event coverage audit.
15. Execution-cost research.
16. Optional AI live-router hook.
17. Resume-hard live governance.
18. Intent time-to-live.
19. Remove hard-coded reference-price fallbacks.

# Commissioning evidence pack: template and status (spec section 9)

Claude (Cowork), 2026-11-14, owner direction "begin working on all recommended supporting tasks" (support for Codex's
workload, area A5). This is the checklist Codex fills when the owner authorises commissioning. It changes no rule of the
frozen spec v2; where it quotes a test, the spec's wording governs. Status column: SHOWN from `docs/PROJECT_STATE.md`
engineering item 2 and the work log as of 2026-11-14T18:50Z; self-checked, not independently verified.
Bot relation: BOT_RULES (the simulation runs the bot's code). Nothing here authorises a start, a deployment, R10 or a
market-data run.

## 0. Gate before anything below (owner decisions, all open)
| Decision | Why it blocks | Recorded where |
|---|---|---|
| R10 stopped 2026-11-12T04:48:51Z: keep the spec and resume R10 with limits, change the spec, or run an unofficial trial | Section 9 step 1 requires R10; step 2 requires "a backup was restored" | work log 2026-11-12/13; stopped_held_tasks_20261113 |
| Activation profile approval (nine candidate profiles, `paper_profile_candidate_20261114/profiles/`) | No account can start without its `user.yaml` | PROJECT_STATE item 2, 2026-11-14T12:02Z |
| Market-rules cache provisioning on the server (a market-data run; command exists: `scripts/refresh_market_rules.py --paper-state-dir`) | Cash sizing refuses every BUY without fresh rules (6-hour TTL) | item 2, 2026-11-14T05:15Z; BA-50; Claude 2026-11-13T23:54Z |
| Server access scope for deployment (last read-only preflight 2026-11-14T12:44Z exceeded its wording, O-165) | Every step below runs on the server | work log 2026-11-14T12:49:17Z |
| Codex verification of BA-40 to BA-51 (BA-44 fixed by 0067; BA-51 patch specified) | Audit findings on the simulation path | bot_audit README sessions 9-13 |

## 1. Step 1: build and test. R1-R10 and R12 implemented; every acceptance test passes
Record for each: test file(s), command, pass count, run time, and the commit or file hashes of the code under test.
"Source accepted" means a separate GATE accepted the source on synthetic tests; it is not an operations result.

| R | Acceptance tests (spec) | Source status (SHOWN) | Operations status | Evidence to attach |
|---|---|---|---|---|
| R1 cooldown lockout | restart keeps the count; stop-loss fills during cooldown; cooldown wall-clock in manifest | accepted with risk 2026-11-03 (patches 0001/0002 rebased) | not run on server | test output; manifest line `cooldown_loops x 15 s` |
| R2 restarts and one stop | `kill -9` each process kind: back in 1 min, state unchanged; reboot: all back in 5 min; crash loop stops and alerts; second copy refused; stop-all within 1 min | INCOMPLETE: renderer only (2026-11-04); unit composition 2026-11-11 (0 units until a backup role exists) | not deployed | systemd unit files + hashes; `systemctl` output; kill/reboot timings; stop-all transcript |
| R3 alerts | each listed condition triggered once; owner confirms receipt; date and channel | INCOMPLETE: review-only renderer names `scripts/run_group_a_alert.py watch <release>`; no executable startup directive | not deployed | per-condition table: trigger time, alert time, channel, owner confirmation |
| R4 freshness | publisher stop: buys refused, pending exit fills on restart; stale candles + fresh quotes: buy refused, sell fills; gapped/zero data recorded and alerted | INCOMPLETE | not run | decision records showing candle open time/completeness, quote age, bid/ask; refusal reasons |
| R5 debug line | 100 loops, no `/tmp/cbp_debug.txt`; log size cap shown; replay identical before/after | GATE accepted (correction closeout) | not run | `ls /tmp` after 100 loops; log config; replay diff |
| R6 inputs saved, replay reproduces | every recorded decision reproduces action, reason incl. filter, indicators exactly, exit conditions, exit rule; 26-week size estimate in manifest | accepted with risk 2026-11-03 (with R9), operations partial | not run | replay report: decisions N, matched N, mismatches 0; archive size per day x 182 |
| R7 evaluation rules | section 7 approved before the start | approved and frozen 2026-11-14T12:35Z | n/a | the frozen section's hash in the manifest |
| R8 order lifecycle | stop runner, queue buy, wait 3 min, restart: expired + alerted; sell: filled late, delay recorded, alerted; duplicate client ID: one fill; 5-minute reconciliation | account check owner-accepted with risk; buy lifecycle READY_FOR_INDEPENDENT_REVIEW 2026-11-03 | not run | order rows with created/picked-up/final times; reconciliation log |
| R9 exit conditions recorded | synthetic path with stop, trailing and signal true together: all recorded, stop acted on; recording on/off same actions | accepted with risk 2026-11-03 (with R6) | not run | decision record sample; on/off action diff |
| R10 heartbeats and backups (section 8) | stop one account: notification within 15 min; shutdown: all checks notify; backup every 6 h, integrity check, weekly automatic restore | STOPPED by owner 2026-11-12; offline pieces exist (bundle, acquisition bridge, sqlite_backup) | none | provider accounts (owner), check list (13 for Group A), restore log |
| R12 stuck exits retried | stop-loss fills during cooldown, after an injected refusal, while quotes are stale; never fills twice; superseded when holding is zero | source closure 2026-11-03 READY_FOR_INDEPENDENT_REVIEW, later "durable source prerequisites accepted with risk" | not run | the three blocker tests' outputs; duplicate-send test |

Also required by section 9 step 1: the evidence pack lists versions (Python, SQLite, ccxt, systemd: preflight 2026-11-14
showed Python 3.12.3, SQLite 3.45.1, ccxt 4.5.48, systemd 255 on the sampled host) and configuration hashes (each
account's `user.yaml` without secrets; presets; frozen spec section 7; the strategy source files).

## 2. Step 2: 72-hour commissioning on the server (all Group A accounts and services, version to be frozen)
Record start/end UTC, the commit hash under test, and for each failure test: UTC injected, what happened, UTC recovered,
which R it exercised, alert time and owner confirmation.

| # | Failure test (spec) | Expected (R) | Pass evidence |
|---|---|---|---|
| F1 | Kill an account process holding a position (seed a commissioning test account if none holds one) | back within 1 min; cash, holdings, entry price, peak, hours held, order history unchanged (R2) | pre/post state diff = none; restart time |
| F2 | Kill the paper runner just after a fill | fill persisted once; no duplicate; reconciliation clean (R8, R12) | fill rows; reconciliation log |
| F3 | Reboot the server | every account back within 5 min, state unchanged (R2) | boot log; per-account status times |
| F4 | Cut the network for 10 minutes | buys refused, exits pending then filled on recovery, alerts (R4, R12, R3) | refusal reasons; pending exit fill time |
| F5 | Stop the market-data publisher | buys refused; pending exit fills on restart; both alerted (R4) | as F4 |
| F6 | Submit a duplicate order | one fill (R8) | order rows |
| F7 | Fill a test disk or simulate a write failure | failure recorded, alert; no silent drop (R3, R8) | alert record; ledger integrity |
| F8 | R12 three blockers on a commissioning test account: cooldown; refused stop sell; stale quotes | stop-loss fills in each (R12, R1) | three fill records with reasons |

Pass criteria (all must hold; record the measured value next to each):
- decisions recorded in at least 99% of loops outside the deliberate failures (per account: loops expected, recorded);
- data stayed fresh (max quote age, max candle gap, outside failures);
- each failure behaved as R1-R10 and R12 require and its alert reached the owner (table above complete);
- ledgers reconcile to the cent (per account: cash + holdings x mark vs fills and fees);
- replay matched 100% of the 72 hours' decisions (R6 replay report);
- a backup was restored (R10; blocked while R10 is stopped);
- memory stayed under 70% (peak sampled every 5 min) and projected disk for 26 weeks under 60% (measured growth x 182 / disk size);
- commissioning trades excluded from the evaluation (list their order IDs).
Any failure: fix, then restart commissioning from zero (record the attempt number).

## 3. Step 3: independent review
Reviewer other than the builder (AGENTS.md "Cross-review"): code changes since the last accepted hashes, this pack, the
commissioning report. Record reviewer, UTC, disposition, residual risks.

## 4. What this pack does not do
It does not resolve any decision in section 0, does not make any INCOMPLETE row complete, and does not substitute for
the owner's approval to start. Rows marked "not run" are unknown until run; a passing synthetic test is not a passing
commissioning test.

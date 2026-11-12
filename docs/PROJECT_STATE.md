# PROJECT STATE

The single source of truth for priorities, decisions and status. Item tags: [research], [safety], [operations]. The owner orders it; agents propose changes.
Rules: `AGENTS.md`, "Primary Objective Protection (POP)".
Last updated: 2026-11-09 12:36Z by Claude weekly status (POP), "Evidence now" first bullet refreshed with facts only; previous line: 2026-11-05 03:06Z by Claude weekly status (POP). HEAD 82b5f216e (2026-11-01) on branch backup/2026-10-31; `git status --porcelain`: 150 lines.

Cross-review update 2026-11-03 UTC (Codex, owner-directed continuation): the timestamp/HEAD/count above are historical, not current inventory. Independent saved-result diagnosis finished with separate ACCEPTED_WITH_RISK for reporting only; captured Claude chat read 350/350 by the audit team, original-content certification INCOMPLETE because attachment/code/tool bodies are missing. Evidence and dated corrections: `docs/research/claude_conversation_audit_20261102/`. No queue reordering, strategy/configuration, operations or trading change.

Attachment supplement update 2026-11-03 UTC: owner supplied the missing package. All twenty full bodies now read and hash/body-checked; the earlier attachment-body access gap is CLOSED. Two new export-related messages were read, and fully loaded UI pagination showed 352 containers (the exporter's 357-turn count remains an attributed discrepancy). The provided captured text plus all twenty bodies is reviewed; native verbatim/revision history, thirteen exact message bindings and old hidden code/tool content are not certified. Those limits do not block approved engineering item 1 or require another attachment upload for the completed scope. See `docs/research/claude_conversation_audit_20261102/attachment_supplement_20261103/`.

Independent supplement GATE ACCEPTED_WITH_RISK for that narrow document/evidence scope (twenty bodies plus captured messages), not economics/runtime/trading. The beta/downside and venue-proxy interpretation corrections are dated in the universe report; source/results unchanged. No new market test or queue change.

**Scope.** POP orders work; it never narrows symbol scope. Supported universe: the 25 symbols in
`config/candidate_universe.yaml` (`docs/research/MULTI_SYMBOL_MANDATE.md`); per-symbol status in
`research/symbol_coverage.csv` (41 rows; its 4 registry checks passed on 2026-10-30).

## Evidence now
- No strategy has shown an advantage on forward data yet. Tracker v2 (checked 2026-11-09T12:35Z, SHOWN in
  `paper_btc_eth_trend_v2_20261012/state/`): one week of marks (2026-10-19 to 10-25), last_completed_day 2026-10-25;
  NAV rule 985.38, rule_band10 985.38, hold_btc 970.83, mix_25_25_50 982.95, cash 1000.00; no 2026-11-01 or 2026-11-08
  decision recorded (state files unchanged since 2026-10-26 00:52Z); cause not yet classified. Tracker v1 (SHOWN,
  `paper_btc_eth_trend_20261009/paper_state.json`, generated 2026-11-09 00:47Z, 0.60% fee + 0.05% slippage): 28 days
  from 2026-10-11, rule $941.21 (-5.88%, all cash since the 2026-10-25 rebalance; 4 Sunday rebalances recorded) against holding BTC $893.35.
- BTC+ETH 28-day trend rule, historical and in-sample: higher Sharpe than holding BTC and than fixed BTC/ETH/cash
  mixes in every window at 0.50% per side, and smaller drawdowns (risk reduction). No return edge over holding BTC
  since 2016; rejected at the 1.2% stress fee. Sources: `btc_eth_corrected_comparison_20261012/`, `dsr_btc_eth_trend_20261011/`.
- At $1,000 of capital, about $240 a year of infrastructure cancels its 2024-26 return (`strategy_decision_report_20261011.md`).
- Other symbols and families: `research/symbol_coverage.csv`; negative results are scoped to their tested conditions.
- Default breakout, historical and in-sample (OKX hourly, 5 coins, 2026-01 to 09, $100 per trade): +$139 before fees on 310
  trades, not distinguishable from zero (95% interval -$38 to +$336); the top 10 trades made 169% of it; it breaks even at
  0.22% fee per side. Self-checked (`failure_diagnosis_20261030/`, corrections C1-C3).
- Cross-review 2026-11-03: that report's in/out return attribution and -$15/+$28/+$65 blocked-exit dollar effects are
  withdrawn pending correct opening-gap and original-quantity accounting. Its 0.35%-per-side survival hypothesis has
  a round-trip error. Saved trades/net results remain distinct, unchanged evidence. Three synthetic counterexamples
  pass; no new market run. Repeated chat claims of "no after-cost profit" are contradicted by positive historical
  models; these still establish neither forward advantage nor realized profit. See the dated report correction.
- In the audited source paths, the named strategy intent writers write the paper queue and no production writer to
  the live stores was found (`capital_protection_audit_20261031/` CP-02; self-checked source finding). This is not a
  current process/environment/server inspection or a guarantee that live submission is impossible. The audit traces exchange orders through the gate,
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
   Progress 2026-10-31: repository private (owner; unauthenticated GitHub web and API both return 404); four local
   commits on branch `backup/2026-10-31` (020beb69f, 0265746ad, 4decb32e4, b059f1efa: groups A, B, C, F of
   `docs/checkpoints/commit_plan_20261031/`). Open: owner review then push; large-data backup (owner); group D after
   Codex confirms its code. Later 2026-10-31: bcb9ccd02 (later docs) added; owner pushed the branch (GitHub matches
   bcb9ccd02). Codex unavailable, owner: "resolve or document": group D committed as an unreviewed backup, not ready to
   merge; its test status and what Codex must fix are in the commit plan README, section "Group D". Open: push that
   commit (owner); large-data backup (owner); Codex's fixes before any merge.
2. Capital: the amount the system is for, or "engineering project for now". Also sets the paper simulation's drawdown
   limit (spec v2 section 7.5; research figures there; if no number is set, "no worse than holding the coin" applies) and
   approves the minimum trade samples (7.4: 42, 42, 31, derived from the replay), needed before the simulation starts.
3. Approve the stuck-exit rule: keep a rejected exit pending with a reason and an alert; never convert, reprice, mark filled, drop or cancel it.
   Approved for the paper simulation 2026-10-31 (owner forwarded the advisor's final authorisation: "you can now
   proceed"; spec v2 R12, with one exception: a pending sell is closed as superseded, unsent, when the holding is
   already zero, so nothing is sold twice). Still open for the live path.
- Owner action, security (2026-10-31, OV-01): `.env.docker` was committed on 2026-01-22 and is in GitHub's history while
  the repository was public; check it (`git show b6476a5b1:.env.docker`) and rotate anything real.
- Pre-live list: the 19-item "Deferred Live-Money Substrate Backlog" in `REMAINING_TASKS.md` (Codex) is part of it; new
  pre-live findings are checked against it first (O-20, OV-02).
- Blocking engineering item 3 (Codex note below): confirm whether the DEFAULT portfolio holds all your Coinbase coins and open orders.
- Decided 2026-10-30: the 25-symbol comparison follows the active safety task (now item 5, after the multi-coin fix, the paper simulation, the position cap and exit logic); its collector runs on the
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
- Decided 2026-10-31 (owner): run the bot on fake money with live prices, 24/7 on the Hetzner server: breakout, EMA
  cross and mean reversion defaults on BTC, ETH and SOL (9 accounts, one process each until the multi-coin fix), $1,000
  each, fees at the account's 0.50% taker rate. And audit the whole bot for flaws, starting with what the simulation runs.
  Owner, 2026-10-31 ("do what's best"), after O-12: add Group B, 9 more accounts on the 3 coins the market ranker picks
  each week, pre-registered, as the forward test the ranker needs before it may trade; staged after Group A for capacity.
  Owner, 2026-10-31, after the advisor's review: adopt eleven pre-start requirements (spec v2 section 6); outside
  heartbeat monitoring by an independent provider and encrypted off-server backups (non-Hetzner) approved; the 26-week
  clock starts only after a 72-hour commissioning, independent review and the owner's written approval; the bot's
  decision code stays unchanged. Storage-provider selection adopted2026-11-11:
  MEGA primary for encrypted state/archive backups, TeraBox optional;
  Git for source/docs/manifests. Heartbeat provider and account provisioning/
  access remain unresolved; this selection does not authorize installs or uploads.
- Next when one closes: approve the server cost and monitoring plan for the 25-symbol collector (Codex to report them).

## Engineering queue (Codex; one active)
**Owner direction 2026-11-12 (2026-11-12T04:48:51Z, recorded by Claude; the owner replied "do it" to this message, written for Codex):**
> Stop the backup (R10) work where it is and don't run the downloaded tools. Next, in this order: (1) commit the current
> work in reviewed groups, as in the 31 Oct commit plan, and tell me when it's ready to push; Claude reviews before the
> push. (2) Find out why tracker v2 hasn't run since 26 Oct and get it running before Sunday. One step each, one review,
> then report. No extra controllers or rounds of tests unless a real defect is found.
- Effect: engineering item 2's R10 backup work is on hold where it stopped at 2026-11-12T04:44:38Z; the proposed native
  restic/rclone test is not approved, and the staged tools are not run. Accepted sources stay as they are.
- Approval given: local commits in reviewed groups (owner decision 1). Pushing waits for Claude's review.
- 2026-11-12T04:57:16Z Codex local preservation grouping independently
  ACCEPTED_WITH_RISK by Rawls (checked04:54:51Z), exact757paths:A9/B80/C550/D118.
  B95f91bec7 research, Caaf7f8d5c evidence, D2a6e42526 source/tests committed
  on backup/2026-10-31 after staged bytes matched frozen inventory. Governance
  closes this range in the next local commit. Base82b5f216e; no push, merge,
  rebase, new tests or operational acceptance. Claude pre-push review remains
  required. Tracker v2 is next, not forgotten; R10 stays stopped.
- Codex receipt2026-11-12T04:49:48Z:R10 stopped immediately on receipt of this
  direction. One earlier continuation-triggered invocation exited1 in
  verify_inputs before any sandbox or downloaded client execution; no retry.
  Read-only diagnosis confirmed unsafe_tool_pin_path because the pins argument
  was relative. No source repair authorized or made; source-readiness claim is
  narrowed by this actual invocation defect. Owned empty attempt directory
  /private/tmp/cryptkeep-backup-native-9brdbcqh retained. Not an encrypted backup.
- Tracker v2: state files unchanged since 2026-10-26 00:52Z (2026-11-01 and 2026-11-08 decisions missed). Next decision
  Sunday 2026-11-15 20:47 New York (2026-11-16 01:47 UTC).
- 2026-11-12T05:01:17Z commit step complete:four local commits95f91bec7,
  aaf7f8d5c,2a6e42526,27cd39cca. Claude pre-push range82b5f216e..27cd39cca;
  no push/merge. Tracker diagnosis now active:current exact-ledger hash/mtime
  check confirms no1/8Nov decisions; known local automation definition absent.
  App view returned a card only, not machine-readable status; Codex UI access
  denied, not bypassed. Deletion/migration/dispatch cause UNVERIFIED. Asked
  owner whether displayed original-task card shows an existing task or not
  found before update/replacement; no duplicate created or state backfill.
  Restoration INCOMPLETE, not a running schedule claim. R10 remains stopped.
- 2026-11-12T08:43:33Z superseding registration result:app explicitly rejected
  original-ID update as nonexistent. One separately reviewed minimal replacement
  creation succeeded, same IDbtc-eth-weekly-research-tracker-v2, ACTIVE; saved
  configuration readback SHA4e79aae5... confirms Sunday20:47 recurrence and
  attachment to this chat. Expected next15Nov20:47NewYork/16Nov01:47UTC.
  Registration repair DONE; actual next unattended output still UNVERIFIED.
  No manual tracker run, source/ledger rewrite, tests, second creation or
  unrelated schedule change. Missing-registration cause/deleter unknown;
  no historical missed observation repaired. R10 remains stopped, no push.
  Separate Nash GATE08:44:21UTC independently ACCEPTED_WITH_RISK persisted
  configuration only; source/four output hashes unchanged. File lacks explicit
  timezone, so15Nov20:47NewYork is intended, not independently proved effective
  scheduler timezone. Future delivery remains separate required evidence.
- 2026-11-12T09:29:48Z owner-authorized Claude pre-push review completed in
  existing handoff chat. ACCEPTED_WITH_RISK for preservation only; no blocking
  findings in82b5f216e..aad07d655,758unique paths. Material scope correction:
  cached origin/backup/2026-10-31 tip28f196e6f is19commits behind HEAD, so a
  normal push may include14earlier local ancestors. Claude scanned those14
  only for secrets/names/size, not full content. Exact local Git counts checked.
  Need current privacy/remote-scope check and owner awareness before any push;
  no force/merge/rebase/deploy or source readiness inferred. Review copy:
  docs/checkpoints/commit_plan_20261112/CLAUDE_PREPUSH_REVIEW.md. Source tip
  frozenaad07d655; receipt docs uncommitted, no push. R10 remains stopped.
- 2026-11-12T09:57:52Z live prerequisite reads COMPLETE:GitHub reports
  Ddthomas415/CryptKeep PUBLIC/isPrivate=false; remote backup/2026-10-31
  remains28f196e6f, an ancestor ofaad07d655, so19commits would be outgoing.
  PUBLIC was already recorded1Nov12:42:48UTC(base82b5f216e); the31Oct-private
  premise in the review was stale. No new visibility change/actor inferred.
  No push or setting change. Needed owner choice:authorize public publication
  of this19commit preservation range, or make private first. Earlier14scanned
  only, not fully content-reviewed. No force/merge/rebase; R10 stays stopped.
- 2026-11-12T12:28:35Z owner chose "push" after public/private clarification,
  authorizing the disclosed19commit public preservation range. Current PUBLIC
  identity/ref rechecked; one non-force exact-tip push failed HTTP400/sideband
  disconnect. Actual post-failure remote remains28f196e6f, not aad07d655;
  publication not applied. GitHub API reports ADMIN for this repository, not
  proof the git transport works. No login/visibility/source change or retry.
  Found existing31Oct13:32:43log:the same HTTP400 succeeded using per-command
  http.version=HTTP/1.1 and http.postBuffer=157286400. Missed prior evidence
  recorded O133. One-attempt budget reached; next decision is one corrected
  retry with that documented transport, same reviewed SHA/ref, no force/global
  config changes. R10 stopped; receipts remain uncommitted outside reviewedtip.
- 2026-11-12T12:33:22Z owner-approved corrected retry SUCCEEDED, exit0,
  using command-scoped HTTP/1.1/postBuffer157286400. Exact19commit public
  preservation push28f196e6f->aad07d655 on backup/2026-10-31, no force/tags/
  submodules. Fresh actual remote read independently confirms fullSHA
  aad07d655cc79d30d92fbb9689b59ab5f6b66200. Only that local tracking ref
  synchronized afterward; no merge/rebase/deploy/source/config setting change.
  Publication task DONE, conditional preservation acceptance only. Four review/
  receipt paths remain local/uncommitted and excluded; ignored large data not
  backed up by Git. R10 remains stopped; tracker unattended output still awaits
  its intended next slot. No new controller, tests or runtime operation.
- 2026-11-12T12:45:29Z read-only post-push check follow-through:2existing
  checks succeeded(script-path-integrity,Governance Smoke),4release/build/
  signing workflows failed validation with0jobs. Actual GitHub annotations
  confirm18direct secrets.* references in step if expressions across4files.
  These workflow files are unchanged by28f196e6f..aad07d655, inherited defects,
  not demonstrated application-test regressions. No rerun/source/release or
  signing/credential change. Narrow workflow repair proposed in PARKED only;
  owner has not ordered it into a queue. Full CI remains NOT GREEN. Evidence
  and exact run IDs/locations in commit_plan_20261112/README.md. R10 paused.
- 2026-11-12T13:09:21Z owner-reported laptop restart checked read-only.
  Host reports lastboot11Nov21:55:15UTC(16:55NewYork), not proof of a later
  reboot. Local source/tracking refs stillaad07d655 and same4receiptpaths
  retained. Tracker savedACTIVE config SHA4e79aae5... and all4primary-file
  hashes unchanged; actual future dispatch still unverified. Neither existing
  collector script matched in permitted process queries; saved PIDs21851/2737
  also absent. Context status saysrunningbutdated4Nov02:38UTC; paper status
  idle29Oct14:33UTC. Stale files are not liveness or proven reboot causation.
  No restart/source/schedule/account/host/trading action. Existing market-context
  restart with recorded settings needs owner approval; paper/R10 remain untouched.
- 2026-11-12T13:29:34Z owner-authorized existing market-context collector
  restarted once with the actual29Oct paired-raw argv, frozen PLAN/OPTIONS,
  original archive,live_public,300second post-cycle interval and no loop cap.
  SHOWN unique surviving PID51426; fresh13:29:05UTC cycle loops1,writes1,
  errors0,last_oktrue,all6source checks successful. Stored OI1,basis1,quotes2,
  book1 and raw funding1; normalized funding0 by design. Funding remains
  raw_okx_pairs_unverified/normalization_eligiblefalse; research_onlytrue,
  execution_enabledfalse. First-cycle restoration demonstrated, not sustained
  uptime or boot persistence. Six historically bound runtime sources match;
  shared app_paths was absent from old bindings, not a changed-file mismatch;
  current helper matchesHEAD/Marchcommit and explicit local state root retained.
  Paper/tracker/R10/workflows/trading settings unchanged. Runtime trading config
  not checked. Evidence:work-log task card/completion, selected fresh status and
  committed snapshot IDs; no new controller/source/tests/scheduler or push.
- 2026-11-12T14:42:07Z owner "carry out the next steps" in direct response
  to the proposed four-workflow repair orders that parked item into the active
  engineering queue. Scope:18invalid secret-context step conditions only,
  focused offline verification and one independent review. R10 stays paused;
  no build/release/signing/deployment, publication, credential or task changes.
  Preserve triggers, permissions, OS restrictions and step-scoped secret values.
- 2026-11-12T14:45:46Z four-workflow source repair submitted
  READY_FOR_INDEPENDENT_REVIEW. All18conditions use job-level boolean
  availability plus explicit 'true' step comparisons; only12availability
  expressions added across6jobs. Raw-secret step scope/OS checks preserved.
  New16focused tests fail on original workflows and pass on correction;
  parsed comparison confirms all other workflow fields unchanged. No full
  actionlint/hosted-engine validation available; local tests are not hosted
  CI/build/signing proof. Exact diff/hashes/limits in existing commit-plan
  README. One separate GATE requested; no commit/push/workflow execution.
- 2026-11-12T14:47:54Z separate Darwin GATE ACCEPTED_WITH_RISK for
  the exact five hashed source/test files, offline scope only. Reviewer
  independently passed16tests0.34s, expanded all18replacement predicates to
  their original forms, confirmed41unchanged raw-secret step fields and all
  other parsed workflow data unchanged; no duplicate YAML keys. Author's
  before16failures not independently rerun. Five hashes unchanged after
  review. No actionlint/hosted-engine or actual build/signing/release proof;
  full CI remains unverified, original published runs still failed. Source
  repair complete; uncommitted/unpushed. R10 stays paused; no next item started.
- 2026-11-12T15:07:25Z owner continuation authorizes local preservation
  follow-through for the reviewed workflow repair and existing local receipts,
  under the already ordered reviewed-group commit workflow. Two groups only:
  five unchanged reviewed workflow/test files, then four existing governance/
  review-receipt files. Separate source acceptance reused; no repeated tests
  or new implementation. Another agent's CMC snapshot excluded. No push or
  GitHub execution; Claude review of this new committed range remains required
  before a separately authorized publication. R10 stays stopped.
- 2026-11-12T15:08:56Z reviewed workflow source preserved locally in
  a22fef9c0f07173fa2ed4c838bbddbd1904007fa (exact5paths, staged bytes match
  separateGATE seal). This receipt's containing governance commit preserves
  only4existing receipt files; newCMC snapshot excluded. New review range
  aad07d655..HEAD is ready for Claude pre-push review, not yet reviewed by
  Claude or published. No tests/source/operational action repeated. Cached
  remote ref is not a fresh remote check. No push/build/release; R10 stopped.

1. [done for source scope 2026-11-03; operations not started] [safety] Multi-coin runner fix (owner, 2026-10-31: highest priority). **A fix already exists: patch 0004
   of the October series (2026-10-02; "current form needs final review"), in
   `docs/review_artifacts/20261004_rev32_bundle/cryptkeep_series_on_be34a18a_rev88.zip`; start from it (review, rebase,
   test) rather than writing a new one (O-18).** First confirm the defect independently
   (`exit_parity_audit_20261031/` section 6 and addendum). Fix the per-symbol structure of `run_forever` so every
   symbol gets its own entry decision, position check, exit checks and order step. Done when an integration test that
   drives the real runner loop (not only unit tests) shows, with three symbols: each symbol independently gets entry
   decisions, position checks and exit checks; simultaneous positions; a rejected exit order; restart and recovery; and
   one symbol's failure (no price, error, rejected order) does not stop another symbol's exit management. Independent
   review. No multi-symbol paper or live trading until it passes. No other runner behaviour change without approval.
   Progress 2026-11-03 (Codex): existing 0004 round-robin/fresh-price change rebased, with multi-symbol
   turn-error and loaded-state persistence isolation. First independent review found two gaps (O-38/O-39);
   both corrected with regression tests. SHOWN final offline real-loop/SQLite harness: 28 passed;
   original source under the initial 22-case harness: 19 failed, 3 passed; six new cases against the
   initial review snapshot: 5 failed, 1 passed. Final combined focused regression: 197 passed.
   Author implementation ended READY_FOR_INDEPENDENT_REVIEW; separate reviewer Poincare subsequently
   ACCEPTED the corrected source scope, independently rerunning all 28 integration cases and three failure probes.
   Combined 197-case regression remains author self-checked, not separately rerun. Operational readiness INCOMPLETE.
   Evidence/diffs/hashes: `docs/review_artifacts/multisymbol_runner_repair_20261103/`.
   Each symbol is serviced once per N outer turns, not every turn. Rejected-exit retry, cooldown, intent-accounting
   and aggregate-risk defects remain separate dependencies. No runtime config, deployment, service/account,
   collector/schedule or trading change; all 25 supported symbols retained. Next queued item is 2; no service
   startup or deployment is inferred from completing this source repair.
2. [active: stage 3 R4 source; R8 account check owner-accepted with risk, operations remain open] [operations] Live paper simulation of the bot on the server (owner, 2026-10-31), per
   `docs/research/paper_simulation_spec_20261031/README.md`: 9 single-coin accounts, hourly candles, $1,000, 0.50% fees,
   bid/ask recorded at every fill, one command stops all, run manifest; reuse the managed paper-campaign tooling.
   Group B (ranker-picked coins, weekly, pre-registered in the spec) follows Group A once server memory allows or item 1
   lets one process serve 3 coins; the ranker runs as a separate weekly job, never imported by the runner.
   Must be in place before the start: spec v2 (design frozen 2026-10-31) section 6, R1-R12 with their acceptance tests,
   built in the order of section 12: (1) cooldown lockout (BA-16, known since 2026-10-02 and missing from this queue
   until 2026-10-31; start from patches 0001/0002 of the October series, O-18) and stuck exits retried, with stop-loss tests under all three blockers; (2) decision inputs and
   exact replay, every exit condition recorded; (3) order lifecycle and reconciliation, market data with buys refused
   on stale candles; (4) debug line, restarts, on-server alerts; (5) outside heartbeats and encrypted off-server
   backups; (6) 72-hour commissioning; then section 9 (independent review, owner approval, official start).
   Independent review; owner approves the start. Does not depend on item 1; the owner may reorder.
   Progress 2026-11-03: R1 rebased from 0001/0002 with the already reviewed 0006 four-status lookup and
   finite position-reducing quantity treatment. SHOWN: 37 new real-loop/SQLite integration cases fail against
   the saved before-runner; corrected focused suite 274 passed, including the restored 40 original cases,
   accepted multi-symbol regressions and real paper-engine stop/trailing fills with synthetic prices/safety inputs.
   Author implementation ended READY_FOR_INDEPENDENT_REVIEW; separate GATE Poincare ACCEPTED_WITH_RISK:
   77 R1 cases and 12 additional probes independently passed; 37 before-runner cases independently failed.
   Reviewer inspected, not reran, the combined 274-case receipt. R1 does not implement R12 or finish stage 1.
   R12 retries, all later R requirements, owner evaluation/provider decisions, commissioning and official start
   remain pending; no server/config/service/account/scheduler/trading action performed. Evidence:
   `docs/review_artifacts/paper_simulation_r1_20261103/`. Next in this same item: R12 stuck-exit recovery.
   Timing caveat: cooldown-blocked turns skip interval sleep; no fixed elapsed pause is demonstrated.
   No queue reordering or scope narrowing.
   R12 source closure 2026-11-03: author implementation ended READY_FOR_INDEPENDENT_REVIEW, not operation. Stable tagged
   exit/client identity; refusals held/retried; authoritative ledger filled/superseded fences; bounded current
   holdings; normal journal-before-terminal recovery; alert-dispatch evidence. SHOWN focused 397 passed (23 files,
   zero skips/errors); before-runner hybrid 26 failed/2 passed, before-storage 63 failed/2 passed. Separate review
   initially REJECTED (two P1/two P2), corrected with failing-before/passing-after cases. Final combined
   487 passed (23 files); separate GATE ACCEPTED_WITH_RISK after 183 integration/atomicity cases and eight
   independent probes. Eleven corrected hashes matched; reviewer inspected but did not rerun all 487. Evidence:
   `docs/review_artifacts/paper_simulation_r12_20261103/`.
   Known before-start dependencies remain: first-emission bookkeeping/queue-write failure (R8) and the existing
   tick_reader wrong-symbol venue fallback (reuse October 0010 under R4). R12 tests do not establish quote identity,
   actual alert delivery or server readiness. R1 timing caveat remains; all later requirements stay queued.
   R1/R12 durable source prerequisites now separately accepted with risk. R6/R9 source scope ACCEPTED_WITH_RISK (2026-11-03), operations partial:
   opt-in exact decision-input replay and all-exit-condition recording, preserving current decisions and ES v1
   artifacts. Initial 643-test candidate (30 files), 366/366 synthetic-hour decisions and three CLI matches was
   independently REJECTED for O-47 (loaded-code identity omitted active bindings), despite the passing tests.
   Bounded active-caller/fingerprint correction: 143 affected tests passed; one test-only observation fixture
   failed then its corrected isolated case passed. Not a single all-green 144-case run. Separate corrected-source
   GATE ACCEPTED_WITH_RISK after the three original probes plus an active-alias probe passed; 11/11 final hashes
   matched. Reviewer independently ran the affected slice (143 passed/one fixture failure), then the repaired
   isolated case (one passed). The earlier 643-case suite was not rerun after correction. Corrected
   six synthetic-hour summaries replay 366/366. Nominal nine-account journal-only sizing is 56.74-58.05 GiB
   (not a capacity pass; excludes other storage and faster blocked loops). Evidence:
   `docs/review_artifacts/paper_simulation_r6r9_20261103/`. Actual observed hour, literal elapsed hours held and
   intended-host capacity remain INCOMPLETE (O-45/O-46 clarify source priority/clock). Scope is offline proof only;
   no deployment, provider setup or observed-hour commissioning authorized or started by this work.
   Next-stage progress 2026-11-03: R8 prerequisite source work ACTIVE: reusing October 0020/0021/0023 journal and
   0022 queue-first recovery design for exactly-once provisional written-sell accounting. Initial write failures
   must not count losses; stop-reset basis is preserved, not implicitly redesigned. Offline test/review in progress.
   Initial 32-file selection: 788 passed/one obsolete durable-evidence fixture failed; strengthened same-assertion
   cooldown file then passed 21 cases. Separate review ran 137 journal/accounting cases but REJECTED the source
   for duplicate-key metadata admitting a paper buy (O-50). Bounded strict-decoder/raw-empty correction: eight
   before-boundary regressions fail as expected; corrected focused selection 167 passed. Separate corrected GATE
   ACCEPTED_WITH_RISK: reviewer independently passed 167 cases, the three unchanged original probes and eleven
   corrected hashes; independently reproduced the eight before-method failures. Evidence:
   `docs/review_artifacts/paper_exit_accounting_r8_20261103/`. No whole-suite or one-command 789-pass claim.
   Full R8 creation/pickup/terminal times, buy expiry/watchdog, R4 data guards and all operation/start gates stay open.
   R8 buy-lifecycle continuation 2026-11-03: source submitted READY_FOR_INDEPENDENT_REVIEW, self-checked;
   fixed 120-second original-intent age at pickup and atomic fill, durable missing-order fences,
   commit-uncertain order recovery, pickup/terminal event history and retained alert-dispatch outcomes.
   Original four test failures resolved without weakening assertions; expanded regression exposed legacy
   `open` compatibility (O-52), corrected. Final 18-file selection 625 passed (33.90s), twelve source/test
   hashes frozen. Two same-behavior before-source probes fail for actual late fill/premature refusal.
   Independent GATE then REJECTED that candidate: failed legacy-origin persistence permitted a late fill,
   and reported identity faults were ignored by ordinary reconciliation (three failing reviewer probes).
   One bounded source correction is sealed READY_FOR_INDEPENDENT_REVIEW: authoritative read-only queue
   origin at expiry/fill, plus canonical order/full-fill receipt before attribution. Affected selection:
   485 passed (18.78s), including the eight unchanged reviewer probes. Separate correction GATE
   ACCEPTED_WITH_RISK: independently passed 356 narrow cases and 21 new adversarial probes, verified
   all twelve hashes, and found both original P1s resolved. The earlier 625-pass receipt predates correction.
   This is not full R8 or deployment: cash/position/fill watchdog, deletion detection, real delivery/cadence,
   R4 identity/freshness and commissioning remain open. Evidence: `docs/review_artifacts/paper_buy_lifecycle_r8_20261103/`.
   Next R8 source stage submitted 2026-11-03: fresh-only opening-balance evidence, all-row locked snapshots,
   fill/fee/cash/holdings checks, overdue/deleted-intent evidence, alerts and per-day receipts. Explicit mode
   of the existing paper monitor; no new job or runtime activation. Current fourteen-file selection:
   546 passed (14.77s); saved original initializer fails the opening-receipt probe as expected. Seven-file
   incremental source/test seal in `docs/review_artifacts/paper_account_reconciliation_r8_20261103/`.
   Author ended READY_FOR_INDEPENDENT_REVIEW, self-checked; separate GATE unavailable due reviewer usage limit,
   with no review disposition returned. Owner subsequently said "approve": source ACCEPTED_WITH_RISK
   through human acceptance, not independent technical verification (seven hashes/work log/git checked
   2026-11-04T01:13:24Z). No operational permission inferred. Unknown legacy origin is not
   inferred from current cash. Actual host performance/delivery, R4 fill quote provenance and operation stay open.
   R4 exact-symbol prerequisite rebased 2026-11-04 UTC: production hunks match original October 0010 exactly
   (patch_equivalence.json). Current sixteen-file selection 483 passed (16.70s); thirteen targeted before
   cases fail as expected for borrowed prices/lost normalization. Four-file seal in
   `docs/review_artifacts/paper_market_data_r4_20261103/`; author READY_FOR_INDEPENDENT_REVIEW,
   self-checked; separate GATE ACCEPTED_WITH_RISK: independently passed 52 reader/snapshot, 18 adversarial
   and 13 caller cases, reproduced thirteen before failures and verified all four hashes/original production
   hunk equivalence. Status/work log/git checked 2026-11-04T01:27:04Z. No guard defaults, runtime settings or operations changed.
   Full stale/gapped candle checks, per-fill quote provenance, actual publisher coverage and commissioning stay open.
   New review finding O-55: held symbols without quotes still write cash-only mark-to-market equity with ok=True.
   Those rows are not valid economic evidence. Owner's subsequent "carry out the next steps" directs the proposed
   bounded repair: active under this item, source/synthetic only; no balance/history rewrite or operation.
   O-55 repair submitted 2026-11-04: failed held-price marks return explicit incomplete/null equity and P&L,
   do not insert equity rows, and propagate unknown valuation to the current paper monitor. Flat cash-only
   and valid requested-symbol marks retain numeric results. Eleven-file selection: 241 passed (4.59s);
   twelve held-price cases fail against the saved original method. Three-file seal in
   `docs/review_artifacts/paper_missing_price_valuation_r4_20261103/`; author READY_FOR_INDEPENDENT_REVIEW,
   self-checked; separate GATE ACCEPTED_WITH_RISK after 58 focused cases, five additional probes, all twelve
   before-method failures and the three-file seal were independently checked. Work log/git checked
   2026-11-04T01:44:33Z. Whole-account aggregation/other dashboard paths and full R4 are not certified.
   Next R4 hourly-candle source boundary submitted 2026-11-04: explicit default-off paper profile, public-cache
   market/timeframe identity, current-hour/sixty-hour diagnostics, submission and serialized fill checks,
   sell bypass, reasons/alerts through existing reconciliation and decision-archive fields/code identity.
   Seventeen-file selection 839 passed (29.96s); four original-method pipeline cases fail as expected.
   Nine-file seal in `docs/review_artifacts/paper_candle_freshness_r4_20261103/`; author READY_FOR_INDEPENDENT_REVIEW,
   self-checked, separate GATE pending. Actual configuration/activation, quote/fill evidence and operation stay open.
   Initial candle GATE REJECTED: 199 focused tests passed, but a new successful diagnostic-write delay
   carried a buy from age119 to121 and committed a fill. O-56's first correction was incomplete for latency.
   The unchanged independent probe and rejected seal are preserved; the single bounded correction is active.
   Bounded correction now submitted: retain pre-diagnostic expiry, resample after successful diagnostics,
   recheck canonical age before accounting and use the refreshed fill time. Corrected affected selection:
   480 passed/one old-seal pin deselected (10.84s), including unchanged late-fill probe. New nine-file seal
   submitted READY_FOR_INDEPENDENT_REVIEW; separate correction GATE pending, not corrected 839/full-suite proof.
   Closeout SHOWN (git/work log checked 2026-11-04T02:36:57Z): separate GATE ACCEPTED_WITH_RISK for
   the corrected sealed buy guard and TTL only. Independent 101 passed/one old-seal pin deselected;
   four unchanged behavioral probes passed and all nine current hashes matched. See
   `docs/review_artifacts/paper_candle_freshness_r4_20261103/independent_review/correction_review.md`.
   Invalid-feed decision archiving is INCOMPLETE (O-58): a nonfinite candle is rejected by the guard,
   but the raw record also fails archive validation before its diagnostic can be retained. Full R4,
   quote/fill evidence and operation remain open. One correction budget used; no further implementation
   without a budget decision. The profile defaults off; runtime configuration was not inspected.
   2026-11-04T05:23:01Z continuation (SHOWN, git/work log): O-58 diagnostic-only source and tests
   are READY_FOR_INDEPENDENT_REVIEW. An hourly negative assessment can now survive decision input
   validation failure in a separate, non-replayable journal; the full capture still reports failure.
   Two before cases failed to retain a receipt; 208 focused tests passed after. Only the capture
   module changed from the prior nine-file R4 seal; previous review applies to the prior bytes.
   No runtime or queue change. Full R4 and independent acceptance of this increment remain open.
   2026-11-04T05:32:52Z review closeout (SHOWN, git/work log): independent GATE REJECTED the O-58
   increment, not the previously sealed buy guard. The NaN receipt works, but a settings-only validation
   failure can trigger a candle receipt and the receipt omits public/sample source (O-59/O-60).
   The 30 focused independent passes do not resolve those probes. No source changes in this review;
   a bounded correction needs an owner budget decision. Full R4 remains INCOMPLETE.
   2026-11-04T05:44:26Z closeout (SHOWN, git/work log): independent GATE ACCEPTED the bounded
   O-58 correction for O-59/O-60. Settings-only failure no longer produces a candle receipt;
   malformed rows still do, and the runner's public/sample source labels are distinct (otherwise
   unknown). Six author before cases failed as expected; 209 focused passed after. Separate probes
   and all four current hashes matched. Full R4 stays INCOMPLETE: quote freshness, per-fill quote
   evidence and commissioning remain open. No runtime or queue change.
   2026-11-04T05:51:06Z continuation (SHOWN, git/work log): R4 strict snapshot freshness and
   atomic per-fill quote evidence source is READY_FOR_INDEPENDENT_REVIEW. Default-off paper-only
   policy checks a two-sided exact-market publisher row and snapshot age at submit/fill, preserves
   paper pricing rules and retry/expiry, and commits quote evidence with the ledger fill.
   Fourteen behavior cases failed with the hash-verified previous engine methods; 540 focused
   cases passed with the current source. No runtime change. Per-decision quote diagnostics,
   evidence extraction into evaluation, intended-host publisher coverage and commissioning are
   not established by this pass; full R4 remains INCOMPLETE.
   2026-11-04T05:54:44Z review closeout (SHOWN, git/work log): independent GATE REJECTED the
   six-file quote/fill increment. A mismatched ticker can be mislabeled and fill the wrong market
   (O-61); direct guarded fills can violate the quote and canonical limit (O-62); a buy retry can
   return a nonexistent fill ID with no receipt (O-63). Independent 37 focused passes and 14
   expected before failures did not cover away those findings. Earlier candle/TTL review remains
   scoped to its prior seal. No source or operations changed in review; full R4 remains INCOMPLETE.
   2026-11-04T09:09:58Z bounded correction (SHOWN, git/work log): O-61/O-62/O-63 source
   READY_FOR_INDEPENDENT_REVIEW. Verify returned ticker identity, enforce modeled price against
   stored side/type/limit at the fill boundary, and return the committed fill on strict-mode retry.
   Three behavioral before failures, 548 focused passes after. Initial profile-off regression
   corrected without changing its tests (O-64). Full R4 remains INCOMPLETE; no operation.
   2026-11-04T09:10:52Z correction closeout (SHOWN, git/work log): independent GATE ACCEPTED
   O-61/O-62/O-63 on the six matched hashes after 14 focused passes. O-64 is resolved in the
   tested source scope. Per-decision quote diagnostics, bid/ask evaluation extraction and
   intended-host coverage/commissioning remain open. No queue, config or operation change.
   2026-11-04T09:17:58Z continuation (SHOWN, git/work log): per-decision quote diagnostics and
   archived account/window bid/ask fill-input export are READY_FOR_INDEPENDENT_REVIEW. The
   export preserves ledger values, uses stored ask/bid and 50 bps per side for modeled inputs,
   and reports INCOMPLETE for absent or invalid evidence. 207 focused tests passed. Full R4
   remains INCOMPLETE; no campaign data, actual configuration, publisher coverage or alerts
   inspected, and no evaluation, commissioning or operation performed.
   2026-11-04T09:21:07Z review closeout (SHOWN, git/work log): separate GATE REJECTED the
   decision/export increment. Decision observation passed; export accepted duplicate fill or
   receipt associations (O-65) and created WAL sidecars on a checkpointed archive (O-66).
   Earlier sealed fill/quote acceptance is unaffected. No source changed in review.
   2026-11-04T09:27:47Z correction closeout (SHOWN, git/work log): separate GATE ACCEPTED
   the bounded O-65/O-66 source correction. Duplicate associations and WAL/sidecar-dependent
   sources fail closed; a standalone rollback-format archive exports without creating sidecars.
   Four before failures, 89 focused passes after, 8 independent passes and all seven hashes
   matched. Decision recording remains unchanged from the preceding review. Full R4 remains
   INCOMPLETE pending intended-host evidence, alerts and commissioning. No operation.
   2026-11-04T09:30:04Z operational evidence review (SHOWN, git/work log): Group A is the
   intended Hetzner scope; the default read-only remote status target uses the older campaign
   configuration. Historical host/context and mocked alert results do not prove current Group A
   quote coverage or Slack delivery. The reviewed 0046 test command is not in this checkout
   (O-67). No remote connection or message sent; obtain bounded read-only host authorization
   first, then treat alert setup/send and commissioning as separate actions. Full R4 INCOMPLETE.
   2026-11-04T09:32:45Z read-only attempt (SHOWN, git/work log): one scoped SSH attempt
   requested an additional Tailscale check and exited 255 on timeout. No remote inventory
   was returned and no snapshot was read. Group A deployment, quote coverage and alert
   delivery remain UNVERIFIED; this does not establish a host or publisher failure.
   2026-11-04T09:34:14Z retry closeout (SHOWN, git/work log): authorized read-only inventory
   reached the documented Hetzner host. The standard checkout is `580ca31ea983af6452a1e02ab8d4b51645e9b43c`,
   lacks the strict paper quote module, and its publisher/engine hashes differ from the reviewed local files.
   No Group A-named unit appeared in the bounded system-service inventory. This does not exclude other
   deployment paths. No matching snapshot path was verified, no quote sample or alert was sent, and no
   service or configuration changed. Full R4 remains INCOMPLETE; prepare a reviewed release handoff
   before considering a separately authorized deployment or commissioning.
   2026-11-04T09:39:04Z release rehearsal (SHOWN, git/work log): 55-path review overlay on
   the exact clean host commit is INCOMPLETE, not deployable. Two host SMA overlap files
   three-way merge to the current overlay bytes, but the clean runner cannot import
   market_context_capture. Two execution-identity dependencies are also absent by static
   inspection. Synthetic rehearsal: 58 passed, 64 failed, 2 errors. Review-only archive,
   hashes and isolation/rollback boundaries: `docs/review_artifacts/group_a_release_rehearsal_20261104/`.
   Next resolve/review exact dependency closure and repeat clean-target verification;
   no upload or operation.
   2026-11-04T09:43:24Z dependency closeout (SHOWN, git/work log): clean-host 66-path
   candidate passed 634 focused tests after adding the three modules, compatible journal,
   five tests and two frozen test artifacts. All 66 archive hashes matched after extraction;
   host #600/#601 evidence retained. Separate GATE ACCEPTED_WITH_RISK for exact dependency
   additions, not the combined release. Final composition review remains open; no deployment
   or operations. Candidate: `docs/review_artifacts/group_a_release_candidate_20261104/`.
   2026-11-04T09:47:00Z package review (SHOWN, git/work log): separate GATE ACCEPTED_WITH_RISK
   the exact 66-path overlay on the named host base, with 17 independent smoke tests passed.
   Dated correction: the regular-file runner three-way merge has four conflicts; only the
   overlapping test merges byte-for-byte. The pinned package's SMA tests passed (O-68).
   Operational release INCOMPLETE. Isolation/rollback draft recorded; R5 global debug
   write remains in the package, followed by the existing R2/R3/R10 gates. No host action.
   2026-11-04T09:52:01Z R5 continuation (SHOWN, git/work log): removed the shared debug write
   in current source and added opt-in bounded per-component logs, without changing the accepted
   66-path archive. 100-turn old/current parity, no new debug file and rotation bounds shown;
   206 passed/6 deselected. R5 source READY_FOR_INDEPENDENT_REVIEW; deployed ownership, all
   launcher/service log sinks and host policy remain UNVERIFIED. No operation.
   2026-11-04T09:55:47Z R5 review (SHOWN, git/work log): separate GATE REJECTED the increment.
   Debug deletion and 100-turn parity passed; opt-in logging exposed synthetic confidential
   exception/extra fields and raw args on formatter errors, and could exceed its byte cap
   (O-69/O-70/O-71). No source change in review. Do not enable this handler; bounded correction next.
   2026-11-04T14:10:09Z R5 correction closeout (SHOWN, git/work log): separate GATE ACCEPTED
   O-69/O-70/O-71 on four matching hashes. Corrected handler omits exceptions/extras,
   emits a fixed error marker and measures the same bytes it writes. Four behavioral
   before failures, 41 focused passes after, 13 independent passes. Operational R5
   remains INCOMPLETE; ownership and host log sinks unverified, prior archive unchanged.
   2026-11-04 R2 offline source increment: release-scoped systemd policy renderer and
   exact stop roster for the nine Group A accounts and support roles. No base services
   or failure sender wired; no installation or service operation. Source increment
   READY_FOR_INDEPENDENT_REVIEW; full R2 and Group A remain INCOMPLETE.
   2026-11-04T14:17:41Z independent R2 review: source increment REJECTED (O-72).
   A failure hook can be queued after its stop job if a member times out during
   shutdown. Source-derived, not daemon-reproduced. Next R2 scope is a bounded
   correction requiring an active target for failure-hook start without pulling
   the target back up. No use of the stop vector, installation or operation.
   2026-11-04T14:21:11Z independent R2 correction closeout: O-72 source ACCEPTED.
   The hook requires and is ordered after the release target; failure jobs
   cannot replace a conflicting queued stop. Three before regressions failed;
   29 static tests passed locally and independently. Full R2 INCOMPLETE: base
   units, runtime alerting, restart/reboot, state and stop timing remain open.
   2026-11-04T14:26:38Z independent R2 account composition review: REJECTED (O-73/O-74).
   The 18 paper-only base units matched the roster and 40 static tests passed, but
   the incomplete composition is startable with support roles missing, and the
   env wrapper can see loader variables before its allowlist takes effect.
   Do not stage these bytes. Correct both boundaries before adding support units.
   2026-11-04T14:30:36Z independent R2 correction closeout: O-73/O-74 offline draft
   ACCEPTED. It emits no runnable unit or target file and declares manager-side
   removal of known loader inputs before exec. Two before failures; 42 static
   tests passed locally and independently. Full R2 remains INCOMPLETE. Next:
   complete owned-unit composition and verify physical and effective boundaries;
   no staging, service activation or host verification authorized by this result.
   2026-11-04T14:36:32Z independent Group A publisher/routing review: REJECTED (O-75).
   Synthetic quote, atomic-write and route checks passed, but fresh-process
   rejection created directories in the disallowed state root via a transitive
   import. Next correct the pre-validation and offline-renderer import paths;
   prove an absent root remains absent. No public fetch or service operation.
   2026-11-04T14:38:53Z independent Group A publisher O-75 correction: ACCEPTED
   for offline source only. Launcher validation and lock precede stateful imports;
   fresh launcher, renderer and lock-only processes left unowned roots absent.
   Two before failures and 53 focused passes locally and independently. Group A
   and full R2/R4 remain INCOMPLETE; next support scope is the watcher and failure
   sender, with off-host backup and composed Linux evidence still open.
   2026-11-04T14:44:13Z Group A R3 offline watcher/terminal adapter: separate GATE
   ACCEPTED the corrected source scope after the O-76 input-attribution rejection.
   Three before regressions failed; 44 focused tests passed locally and independently.
   No telemetry collection or real dispatcher wiring. Next R3 scope is the actual
   observation producer/aggregator, especially durable OHLCV and HTTP 429 counts;
   external receipt, backup and full R2/R3/R4 remain INCOMPLETE.
   2026-11-04T14:49:07Z R3 opt-in candle telemetry source verification: 119 passed,
   two strict xfails (O-77). Both flag states reproduce an unbound price after
   an empty first candle fetch. That runner treatment is not part of telemetry;
   verify no-price, held-position and prior-price cases before Group A starts.
   2026-11-04T14:52:15Z R3 telemetry O-78 correction ACCEPTED by separate GATE.
   Restart no longer assumes an uninterrupted streak, retaining only verified
   prior 429 evidence. 120 focused passes, two O-77 xfails; six independent
   telemetry passes. Next resolve O-77 before Group A commissioning, then wire
   the bounded observation aggregator and real receipt path. R3 INCOMPLETE.
   2026-11-04T19:15:34Z O-77 no-price source correction ACCEPTED by separate GATE.
   First missing inputs no longer crash, later gaps cannot reuse an earlier
   price, and pending exits are still serviced before price evaluation. 181
   focused passes; reviewer reproduced five failures on the exact prior source
   and passed 24 focused checks. Next wire bounded watcher observations; real
   outage behavior, Group A commissioning and R3 remain INCOMPLETE.
   2026-11-04T19:21:47Z R3 status/candle aggregation: 117 focused local passes;
   READY_FOR_INDEPENDENT_REVIEW. It reads fixed status files and accepts candle
   counts only with matching runner generation and fetch attempt. No runtime
   watcher or delivery. Queue, quote and host inputs and commissioning remain
   INCOMPLETE; matching files do not attest that a process is still live.
   2026-11-04T19:24:01Z independent GATE ACCEPTED the corrected offline
   R3 status/candle aggregation (O-79/O-80). Both rejected-source regressions
   reproduced; 119 focused local passes and 26 independent passes. Next add
   bounded queue, shared quote and host evidence adapters. No live watcher,
   alert delivery or commissioning proof.
   2026-11-04T19:33:23Z independent GATE ACCEPTED the corrected offline R3
   support adapters (O-81 through O-84). 117 focused local passes, 54
   independent passes and exact counterexamples replayed. Queue copies, shared
   quotes and resource samples can now be classified; trusted runtime
   producers, backup evidence, delivery cursor and owner receipt are not
   wired or verified. Next build the bounded producer-to-watcher path.
   2026-11-04T19:40:47Z independent GATE ACCEPTED the corrected offline R3
   producer cycle (O-85/O-86). 72 focused local passes, eight independent
   passes. It captures coherent in-memory WAL-aware samples and isolates a
   reader with failed cleanup. Next: verify safe runtime reader acquisition
   and physical identity, then delivery/cursor integration. No host or send.
   2026-11-05T01:50:45Z independent GATE ACCEPTED the offline O-87
   correction after matching all three hashes and passing both replacement
   regressions. 79 focused local passes. Protected Linux reader compatibility
   and trusted identities are UNVERIFIED; durable delivery/cursor remains next
   offline work, not authorized deployment. R3 and Group A remain INCOMPLETE.
   2026-11-05T01:59:51Z independent GATE ACCEPTED the offline O-88/O-89
   delivery cursor corrections (four regressions; 93 focused local passes).
   Next R3 evidence: queue-event coverage, protected runtime wiring, bounded
   dispatcher and separately authorized owner receipt. R3 remains INCOMPLETE.
   2026-11-05T02:12:22Z independent GATE ACCEPTED the offline O-90/O-91
   retained-event corrections (both regressions; 99 focused local passes).
   Next: protected observation-to-delivery and terminal-hook composition,
   including a bounded sender and cursor lifecycle. Historical completeness,
   Linux runtime and owner receipt remain UNVERIFIED. R3 is INCOMPLETE.
   2026-11-05T03:35:27Z independent GATE ACCEPTED the offline O-93 Slack
   acknowledgement correction. 92 focused local passes; 10 independent parser
   passes and five prior failures reproduced. Next: protected Linux runtime
   wiring and cursor lifecycle. Actual Slack framing and owner receipt remain
   UNVERIFIED; no send or deployment authorized. R3 INCOMPLETE.
   2026-11-05T03:44:06Z independent GATE ACCEPTED the offline fail-closed
   O-94/O-95 correction only. 86 local passes, five independent tests and a
   no-I/O CLI refusal probe. Terminal credentials require a read-only file
   mount; watcher launcher refuses until a protected SQLite main/journal
   open exists. R3 remains INCOMPLETE; no host action or send.
   2026-11-05T09:24:57Z candidate O-94 repair READY_FOR_INDEPENDENT_REVIEW:
   protected watcher uses an in-memory SQLite cursor and descriptor-relative
   serialized-image persistence, not a main/journal pathname. 155 focused
   local passes. No provisioning, migration, Linux runtime or alert receipt
   verified. Keep the accepted fail-closed boundary until separate review.
   2026-11-05T09:31:42Z independent GATE ACCEPTED the offline O-96 schema
   correction only: four independent passes, 158 focused local passes.
   Protected cursor source now uses descriptor-relative image persistence,
   with exact schema validation and explicit provisioning seed. Runtime,
   cadence, capacity recovery, backup and actual delivery remain INCOMPLETE.
   2026-11-05T09:40:58Z cadence/capacity design submitted for independent
   review before implementation: one existing watcher supervisor, no added
   scheduler, one bounded pending-condition summary, non-destructive cursor
   recovery. 93 synthetic conditions encode to 15,310 bytes against a proposed
   24 KiB cap. Review pending; no installation or source behavior changed.
   2026-11-05T11:19:46Z independent design review ACCEPTED_WITH_RISK after
   closing summary-transport, child-ownership, source/cursor-capacity and
   account-scoped health-suppression gaps (O-100/O-101). This supersedes the
   pending-review status above, not the implementation boundary. Direct
   summary transport uses the shared 40-second cycle budget; the existing
   terminal worker remains unchanged. Local reference checks: 16 passed;
   valid maximum 93 findings plus five health codes encode to 17,318 bytes,
   inner text 16,288, control/result 134/239. These are design calculations,
   not implemented controller tests. Next within R3: offline implementation
   against the reviewed failure matrix, then independent source review.
   Host, provisioning, service/scheduler, credentials and sends untouched;
   full R3 remains INCOMPLETE.
   2026-11-05T11:40:02Z offline R3 implementation submitted to independent
   source review: fixed summary/health protocol, direct single-POST transport,
   protected image batch acknowledgement/old-pending fallback, explicit source
   coverage, inherited-lock/parent-death supervisor and review-only launch argv.
   Consolidated local selection: 210 passed, 1 native-Linux skip. Paired API
   probe at capacity: legacy path sends nothing and leaves two pending; new
   summary sends one batch, acknowledges both and retains the same one digest.
   This compares legacy/new paths, not a pre-edit commit replay. Source status
   READY_FOR_INDEPENDENT_REVIEW; no provisioning, live send or operation.
   2026-11-05T11:49:09Z independent GATE REJECTED the integrated candidate:
   final source replacement was reflected in health but not filtered from
   report/events, and nonfatal POST failures lacked a fixed local diagnostic.
   Protocol, direct transport and old-pending persistence passed independent
   offline probes; the 210-pass/one-skip selection was reproduced. O-103/O-104
   corrections have failing-before/passing-after tests and are awaiting
   diff-only review; no operation authorized.
   2026-11-05T11:54:06Z independent GATE ACCEPTED_WITH_RISK the corrected
   integrated offline-source candidate. All three new regressions and both
   reviewer probes passed; four correction seals matched and the other 16
   stayed unchanged. Final local selection: 213 passed, 1 native-Linux skip;
   reviewer reran the earlier 210/1 selection and the corrections, not final
   213 together. Source implementation boundary is complete for this increment.
   R3 remains INCOMPLETE pending bounded Linux integration, effective namespace/
   unit and stable-lock provisioning proof, sustained source/cursor capacity,
   approved staging, actual Slack compatibility and owner-confirmed receipt.
   No host/service/scheduler/credential/trading action or deployment occurred.
   2026-11-05T18:45:50Z audit update: Claude's independent 15:03:05Z review
   ACCEPTED_WITH_RISK the R3 Linux fixture packet/proposal only
   (`docs/research/r3_linux_packet_review_20261105/`). No fixtures or Docker
   commands were executed by that review. Native execution remains separately
   unauthorized; timeout/start-receipt and non-vacuous fork checks are review
   recommendations, not completed repairs. R3 remains INCOMPLETE.
   2026-11-05T18:54:49Z owner-approved single local Linux attempt stopped at
   local fingerprint preflight: Docker CLI observed `e6bb967a...` differs from
   reviewed `3afd9fef...`; packet still matches `9027d7dd...`. Zero Docker
   commands/daemon calls, containers or fixtures; no cleanup required and no
   automatic retry. Cause of CLI drift, daemon and cached image remain
   UNVERIFIED. This is not a tampering/repair diagnosis. Receipt:
   `docs/review_artifacts/group_a_release_candidate_20261104/r3_native_probe_20261105/attempt_20261105T185449Z.json`.
   R3 remains INCOMPLETE; changed CLI identity must be resolved before a new
   separately authorized runtime attempt. No production state changed.
   2026-11-05T18:58:10Z local read-only identity diagnosis complete: app metadata
   reports 4.98.0/build 245422 (previous proposal 4.97.0); CLI digest e6bb967a...
   stayed stable. CLI and app strict codesign checks both returned invalid
   signature in this restricted environment. Cause, publisher provenance and
   independent host confirmation remain UNVERIFIED; no tampering/damage claim.
   No Docker CLI/daemon operation, download, restart or repair. Evidence and
   data-preservation guidance: `docs/review_artifacts/group_a_release_candidate_20261104/r3_native_probe_20261105/cli_identity_diagnosis_20261105.md`.
   Next identity proof is independent host confirmation, not silently replacing
   the approved fingerprint. R3 remains INCOMPLETE; no new runtime authorized.
   2026-11-05T20:57:28Z host signature confirmation supersedes the restricted
   result for host verification: Apple control, Docker CLI and app all passed
   strict codesign. Same stable CLI SHA256 e6bb967a..., version 4.98.0/build
   245422. No repair indicated by this result. Host receipt:
   `docs/review_artifacts/group_a_release_candidate_20261104/r3_native_probe_20261105/cli_host_confirmation_20261105.md`.
   Request a new bounded R3 attempt against this CLI digest and the unchanged
   packet, not a restart or repair. No Docker/daemon action performed; image
   availability and Linux fixtures remain UNVERIFIED. R3 is INCOMPLETE.
   2026-11-05T21:12:01Z newly approved R3 attempt: verified CLI and packet,
   daemon responded Linux arm64 (Engine 29.9.2/API 1.56), and the selected
   cache check returned `No such image: python:3.12-slim`. Stopped after two
   read-only Docker commands; zero container creation, fixtures or downloads.
   Receipt: `docs/review_artifacts/group_a_release_candidate_20261104/r3_native_probe_20261105/attempt_20261105T211150Z_faf26603.jsonl`.
   R3 remains INCOMPLETE. Next decision: allow a bounded official-image
   download and new test, or keep the no-download boundary and leave the test
   pending. No repeat or changes to existing Docker state.
   2026-11-11T02:03:09Z (November 10 New York) resumed the owner-approved
   single official-image pull/test after checking for later work. CLI and
   packet hashes unchanged. The sole daemon metadata call failed because
   `/Users/baitus/.docker/run/docker.sock` is absent. Stopped before registry
   metadata, pull, container creation or fixtures; no retry/startup/repair.
   Receipt: `docs/review_artifacts/group_a_release_candidate_20261104/r3_native_probe_20261105/pull_test_20261111T020303Z_bbea93b7.jsonl`.
   Current endpoint reachability differs from November 5; cause/current app
   process state remain UNVERIFIED. R3 remains INCOMPLETE. Starting Docker
   is outside the approved no-restart/no-existing-container-change scope and
   needs an owner decision with saved-container startup effects disclosed.
   2026-11-11T02:10:54Z read-only host inspection found Docker Desktop,
   backend/virtualization processes and the original Unix socket now present;
   Codex did not start them. `/var/run/docker.sock` points to the same socket.
   Historical companion records show restart policy no but do not establish
   today's complete container inventory. No startup/repair is needed on current
   evidence. Receipt: `docs/review_artifacts/group_a_release_candidate_20261104/r3_native_probe_20261105/startup_impact_20261111T020849Z.json`.
   The owner's explicit continuation resumes the still-unexecuted approved one
   image pull/one container test, not an automatic retry or app startup. Record
   the new attempt separately; original receipt remains unchanged.
   2026-11-11T02:14:37Z (November 10 New York) approved official-image pull
   and native increment completed: pinned Linux arm64 Python image acquired;
   unchanged packet ran 7 tests, 0 failures/errors/skips; owned container
   inspected exited/0 with matching label and removed. Seven Docker calls,
   3.885 seconds total; image retained as approved. Separate Linnaeus GATE
   ACCEPTED_WITH_RISK the recorded disposable-process evidence, not full R3.
   All 21 packet sources match current files; no production code changed.
   Evidence: `docs/review_artifacts/group_a_release_candidate_20261104/r3_native_probe_20261105/NATIVE_RESULT_20261110.md`.
   Native local proof is no longer pending. Claude R-1/R-2 assertion limits
   remain; intended-host equivalence, effective units/namespaces/permissions,
   sustained capacity, actual Slack acceptance and owner receipt remain
   separate proof. R3 INCOMPLETE; no deployment, server, app restart, account,
   collector, schedule or trading authorization inferred.
   2026-11-11T02:54:35Z (November 10 New York) owner-approved read-only
   host preflight made one strict-host-key SSH connection attempt. SSH exited
   255 in 5.968 seconds with empty stdout/stderr; no remote observation was
   returned and identity was not established. No retry or operational action.
   Receipt: `docs/review_artifacts/group_a_release_candidate_20261104/r3_native_probe_20261105/host_preflight_20261111T025404Z.json`.
   Current host source/runtime/unit/capacity proof remains UNVERIFIED; the
   cause of access failure is unknown, not evidence of host outage, required
   sign-in or bad deployed code. Local Linux acceptance remains unchanged.
   Next proposed scope: bounded read-only local Tailscale/route diagnosis,
   with at most one freshly authorized preflight if access prerequisites pass.
   2026-11-11T03:30:55Z (November 10 New York) owner-approved local
   connectivity diagnosis passed: Tailscale Running, self and matching target
   peer online, route to 100.86.128.9 through utun4. The one authorized
   conditional SSH attempt then returned the explicit additional Tailscale
   SSH-check challenge and exit 255/timeout; no remote inventory returned.
   This identifies this retry's access blocker, not a general sign-in failure
   or proof of the cause of the earlier empty-output attempt. Agent changed
   no authentication/network/service settings and made no further retry.
   Receipts: `local_connectivity_20261111T032723Z.json` and
   `conditional_host_preflight_20261111T032723Z.json` in the existing native
   probe evidence folder. Temporary approval URL is shown only to the owner,
   redacted from repository evidence. Await owner SSH-check confirmation and
   authorization for one new same-scope preflight. R3 remains INCOMPLETE.
   2026-11-11T03:40:05Z owner confirmed the SSH check; the single authorized
   fresh preflight still returned a new check URL and exit 255/timeout, no
   inventory. No further connection attempted. Found a handoff defect: prior
   URL was relayed only after its SSH process had exited. Current check period
   and why approval did not carry over remain UNVERIFIED; do not blame owner
   sign-in or weaken ACLs. O-111/O-112 record banner suppression/live-handoff
   omissions. Proposed next scope is ONE live read-only session, five-minute
   ceiling, surfacing its URL while the SAME connection remains open; owner
   approval of that larger window is pending. Correction/evidence:
   `docs/review_artifacts/group_a_release_candidate_20261104/r3_native_probe_20261105/SSH_APPROVAL_HANDOFF_CORRECTION_20261110.md`.
   2026-11-11T04:19:41Z approved live attempt kept session 87640 while owner
   confirmed, but still exited 255/timeout with no inventory, before the intended
   window. Local ssh -G showed a missed ServerAliveInterval=5/CountMax=1 deadline
   despite ConnectTimeout=210. Offline correction sets alive interval 0 while
   retaining the 300-second outer cap, strict identity and unchanged remote scope;
   7 local contract tests pass (no SSH connection). O-113 records this incomplete
   correction. Review pending at that handoff; no further SSH authorized.
   Evidence: `docs/review_artifacts/group_a_release_candidate_20261104/r3_native_probe_20261105/SSH_PACKET_TIMEOUT_CORRECTION_20261110.md`.
   2026-11-11T04:22:29Z separate Harvey GATE ACCEPTED_WITH_RISK the corrected
   invocation design only and independently reproduced all 7 offline tests.
   No remote action in review. Contract SHA256 f4efff14...; tests ec0c3a1a... .
   Live behavior and actual host proof remain UNVERIFIED. Fresh owner
   authorization needed before one corrected attempt; no automatic retry.
   2026-11-11T07:37:19Z owner approved one corrected live preflight. Reviewed
   builder and actual ssh -G were validated before the single session70737;
   effective alive interval0, connect210, outer300. Session ID was persisted
   before surfacing its live URL. Owner confirmed; the SAME process remained
   pending through successive polls, then exited142 (consistent with outer
   alarm), no inventory. No new connection or operational change. Receipt:
   `docs/review_artifacts/group_a_release_candidate_20261104/r3_native_probe_20261105/corrected_live_preflight_20261111T072949Z.json`.
   The early cutoff no longer reproduced. Why SSH approval did not yield an
   inventory remains UNVERIFIED; awaiting the actual approval-page status
   wording already requested. Do not send another dead link or retry until
   that missing information is resolved. Host proof and R3 remain INCOMPLETE.
   2026-11-11T08:58:36Z clarification: owner does not know the approval-page
   wording. Saved client evidence contains only the check prompt, no completion
   or remote inventory. Page wording is unavailable, not an owner obligation
   or proof of failed approval. No new SSH attempt authorized or made.
   Next proposal is stage-specific sanitized client diagnostics, subject to
   review and fresh authorization for any connection; do not repeat the
   unchanged approval loop. Effective policy/server state remain UNVERIFIED.
   2026-11-11T09:06:41Z offline stage-diagnostic kit independently
   ACCEPTED_WITH_RISK by Rawls:28 focused passes independently reproduced,
   no network connection. Fixed client markers, default link suppression,
   URL-free receipt projection and exact DEBUG1-only argv delta prepared;
   prior command/deadlines/security unchanged. Artifacts and separate review:
   `docs/review_artifacts/group_a_release_candidate_20261104/r3_native_probe_20261105/SSH_STAGE_DIAGNOSTICS_20261111.md`
   and `SSH_STAGE_REVIEW_20261111.md` in the same folder.
   This is an offline component/recipe, NOT a complete live wrapper. Native
   executor pre-persistence filtering, stdout validation and same-session
   deadline/liveness integration remain unproved. No new attempt or broader
   authorization requested. Next within R3: close that integration boundary
   offline before proposing any connection. Host proof/R3 INCOMPLETE.
   2026-11-11T11:12:39Z execution-path wrapper implemented and frozen for
   independent GATE: same-child nonblocking stdin/stdout/stderr, pre-storage
   filtering, PID-before-link receipt, strict bounded JSON projection,
   non-reaping ownership fence and absolute recovery reserve.68 focused
   synthetic/offline tests passed with host permissions; restricted run64/4
   failed closed when own-group metadata was denied. No SSH connection.
   New wrapper/40 tests and `SSH_INTEGRATION_20261111.md` are in the same
   probe folder. READY_FOR_INDEPENDENT_REVIEW; host proof/R3 INCOMPLETE.
   Guardian295 shortens the work window; cleanup uses remainder of target300.
   A bounded local own-PGID metadata fallback is disclosed for a future
   specifically authorized attempt. Partial inventory is not unit-policy or
   operational acceptance. No retry or new runtime authorization inferred.
   2026-11-11T11:19:32Z first frozen integration REJECTED by separate GATE:
   a first SIGINT during cleanup could bypass its own cleanup. Two actual
   SIGINT regressions failed before the correction (including a descendant
   with closed stdio). Temporary record-only SIGINT handling now covers the
   whole owned-process lifetime, cancels work and defers cleanup interruption;
   prior handler restored afterward.2/2 regressions pass and consolidated70
   pass with host permissions. Corrected source frozen for diff-only GATE;
   READY_FOR_INDEPENDENT_REVIEW, not a runtime acceptance or new connection.
   2026-11-11T11:21:33Z final status checked against git/log/hashes: separate
   Rawls diff-only GATE ACCEPTED_WITH_RISK the corrected offline integration,
   P1 closed. Reviewer independently passed both new real-SIGINT regressions
   (not the full corrected70); author full targeted70 passed. Final wrapper
   hash5ef1b78a..., tests0e9eb6fd..., note f6b35fab... unchanged after review.
   Review: same folder `SSH_INTEGRATION_REVIEW_20261111.md`.
   Offline implementation/review DONE. Next is a fresh owner decision on one
   instrumented read-only connection using the documented revised bounds;
   no runtime action or further hardening starts automatically. Host/R3
   remain INCOMPLETE; no source acceptance implies deployment or profit.
   2026-11-11T11:31:34Z owner-directed one-shot instrumented preflight DONE:
   native session31953 stayed the same through owner confirmation; exit0 in
   89.651s, owned group no_live_members and leader reaped, no retry. Host
   sample11:27:17Z identifies ubuntu-4gb-nbg1-3/cryptkeep UID1000, Linux
   aarch64, systemPython3.12.3/SQLite3.45.1, checkout580ca31ea983af6452a1e02ab8d4b51645e9b43c.
   Eight of11 checked source paths are missing there; all3 present hashes
   differ from current local files. All11 exist locally. Evidence:
   same probe folder `HOST_PREFLIGHT_RESULT_20261111.md`, final receipt
   `instrumented_attempt_20261111T112512Z.json` (SHA d6afffc5...), handoff
   and source comparison. Separate Rawls GATE ACCEPTED_WITH_RISK the recorded
   access/partial inventory; original chat/native chronology not independently
   reconstructed. No code, policy, database, service or trading change.
   Dated correction: current access is now SHOWN, but earlier timeout causes
   remain unknown. Unit/path/venv/capacity sections retained only as digests,
   not usable value proof. Runtime trading config/loaded-service source and
   GroupA deployment readiness remain INCOMPLETE. No further connection is
   authorized by this result. Next recommendation within R3: local, hash-bound
   reconciliation/commissioning proposal for the demonstrated source gap;
   never copy the dirty laptop tree to the host or deploy automatically.
   2026-11-11T11:45:30Z local reconciliation proposal prepared, independent
   review pending. All11 retained host source observations match protected
   base580ca31..., including8 expected absences; this narrows "source gap"
   to undeployed candidate increments, not observed checkout corruption.
   Verified old66-file archive/manifests intact,62 current matches/4 later
   reviewed replacements; native21-file packet21/21 current matches but not
   a full runtime package. Static5-root discovery53 paths,32 outside both
   archives:15 base-identical/2 changed/15 new, not a release manifest.
   Preserve #600/#601 and use isolated composition; keep unrelated live paging
   drift out unless a clean-tree test proves a need. Exact hashes, limitations,
   proposed local composition/verification and later separate operational
   boundaries: same probe folder `SOURCE_RECONCILIATION_PROPOSAL_20261111.md`,
   `source_reconciliation_20261111.json`, readonly auditor. No package built,
   app imports/tests, network, host, config or service operation in this task.
   READY_FOR_INDEPENDENT_REVIEW for the proposal only; full R3 INCOMPLETE.
   2026-11-11T11:47:51Z separate Rawls GATE ACCEPTED_WITH_RISK the local
   reconciliation proposal/evidence, no blocker. It independently ran the
   auditor once and matched the saved snapshot except checked_utc. Frozen
   hashes unchanged; current local HEAD82b5f216e. Review in same folder:
   `SOURCE_RECONCILIATION_REVIEW_20261111.md`. Local proposal task DONE;
   exact new candidate composition/rehearsal NOT DONE, deployment/R3 still
   INCOMPLETE. Next proposed local action is plan steps1-2: compose against
   protected base and prove/review the exact candidate, without a server
   connection, configuration change, staging or activation. No automatic
   host action or new strategic queue item is authorized by this review.
   2026-11-11T13:36:10Z local composition/rehearsal now has a frozen v3:
   `docs/review_artifacts/group_a_composed_candidate_20261111_v3/`,126-file
   source/test overlay SHA724b4785... on protected base580ca31...,1960-file
   scratch tree. Same59-file selection:1616 passed/1 Linux-only skip, no
   errors/failures or source mutations; NOT repository full-suite/CI proof.
   v1 failed33 due omitted baseline/test assets; additive v2 fixedthose33
   but fullv2 exposed1 WAL fixture-lifetime failure. Deterministic control
   shows bytes changed before the reader during GC, not during it; explicit
   fixture close fixes the old assertions. Permanent regression fails before,
   corrected module63 pass. V2/v3 differ only in that test file; production
   bytes unchanged. Old archives/results preserved. Separate final GATE pending;
   READY_FOR_INDEPENDENT_REVIEW for source composition only, R3/deployment
   INCOMPLETE. No actual host/service/configuration/alert/trading operation.
   2026-11-11T13:40:45Z final exact v3 source composition and fixture correction
   separately ACCEPTED_WITH_RISK by Rawls, no blocker. It verified archive126
   members/hashes/modes, reproduced the GC control, independently passed13
   focused cases, and inspected (did not rerun) consolidated1616 pass/1
   Linux-only skip. Runtime bytes unchanged from v2; all earlier failures
   preserved. Review/README in the v3 folder, archive SHA724b4785..., manifest
   928b12da..., tree manifest74ffffcc..., testfixturee8d2a9ad....
   Local composition/rehearsal task DONE for paper-source scope. Linux lock,
   runnable unit composition, actual target values/configuration/namespaces,
   capacity/delivery and commissioning NOT DONE; R3/deployment INCOMPLETE.
   No further source hardening or operational action automatically starts.
   Next within R3 is the separately authorized target-compatibility/value
   preflight against this frozen candidate before staging/activation decisions.
   2026-11-11T14:42:43Z owner-directed one read-only compatibility capture
   succeeded: session66754,2.065s,exit0,one connection; receipt
   r3_native_probe_20261105/compatibility_attempt_20261111T144228Z.json
   SHA2b0c30e8.... Capture source separately ACCEPTED_WITH_RISK after41
   focused synthetic cases independently passed; old controller/candidate
   unchanged. Values: expected host/base580ca31..., systemd255, isolated
   venvPython3.12.3/SQLite3.45.1, ccxt4.5.48/PyYAML6.0.3/NumPy2.4.4.
   Proposed3 candidate paths and2 service users absent; parent0750UID/GID1000
   requires an explicit provisioning/access design. Available disk33.46GB
   and memory3.06GB are samples, not load proof. Proposed44-unit collision
   query unavailable; sanitized ReadWritePaths=null is UNKNOWN. No clear
   namespace, complete compatibility, runnable release or deployment claimed.
   No install/service/config/stateDB/credential/account/alert/trading changes,
   no automatic second capture. Post-capture Rawls evidence review checked
   14:44:25Z ACCEPTED_WITH_RISK for retained facts only; R3/deployment
   INCOMPLETE. Access depends on uninspected groups/ACLs/mounts, not just
   directory mode; cadence inactivity is not a demonstrated fault. Details in
   r3_native_probe_20261105/COMPATIBILITY_CAPTURE_20261111.md. Next proposed
   in-item action: exact runnable-unit/provisioning design against these facts,
   with namespace/policy unknowns explicit; no staging/activation authority.
   2026-11-11T16:23:46Z runnable-unit/provisioning PROPOSAL completed and
   independently ACCEPTED_WITH_RISK by Rawls, no planning blocker. Same probe
   folder RUNNABLE_UNIT_PROPOSAL_20261111.md SHA0ebd5b73... and separate
   RUNNABLE_UNIT_PROPOSAL_REVIEW_20261111.md. Reviewer read full proposal and
   checked11 underlying frozen identities, launch/role mapping and capture
   limits.45 intended files=23base(target+21services+failuretemplate)+22
   lifecycle drop-ins; quote account fragments REPLACE, not duplicate, the18
   earlier account files. Existing APIs remain explicitly non-startable.
   Required backup role has no complete GroupA foreground/R10 integration;
   fixed cfg.qty does not establish aboutUSD1000 buy sizing; watcher cross-UID
   read access/WAL lifecycle and inode receipt bootstrap require proof. These
   are open implementation requirements, not closed by plan acceptance.
   Proposed narrow ACL/traversal approach is unproved; no broad permission or
   UMask change, owner-group membership or root-watcher workaround adopted.
   No new code/config/unit/installer or target operation. O118-O120 record
   earlier capture omissions; no repeat connection or rework count increase.
   Planning task DONE; R3/deployment INCOMPLETE. Next proposed in-item work is
   the offline composition/integration increment and focused failure-matrix
   proof under this proposal; resolve sizing before config approval and retain
   provider/access/namespace unknowns. No staging/start/trading authority.
   2026-11-11T16:44:43Z explicit offline unit composition implemented and
   separately ACCEPTED_WITH_RISK by Rawls, no blocker. New
   services/control/group_a_unit_composition.py SHA41520005... and permanent
   tests/test_group_a_unit_composition.py SHAb525f3c0.... Old4 renderers
   byte-identical to frozen724b... candidate and remain non-startable. NewAPI
   composes45files/22launches/43ownedstopargs IN MEMORY on complete synthetic
   entrypoint refs; deployment_status alwaysINCOMPLETE. Missing required refs
   yieldsNO files/launches, no partial target; no installer/export/start path.
   Actual frozen-manifest probe, independently repeated, is refused for missing
   scripts/run_group_a_backup.py. Backup argv is only a proposed interface,
   not an implementing program or R10success. No fake source or backup stub.
   Focused5file run96pass0.97s; separate reviewer96pass0.95s in fresh state.
   Artifact docs/review_artifacts/group_a_unit_composition_20261111/ includes
   rawXML,README,independentreview; source composition not yet rebuilt as an
   operating package. No existing configuration/financial logic/source archive
   or target operation changed. Wiring-source taskDONE; R3/deploymentINCOMPLETE.
   Next proposed in-item increment is real backup-program integration/reuse,
   retaining existing provider/credential decisions and unresolved permissions/
   sizing before operating configuration or deployment. No automatic host,
   provider,credential,service,scheduler,alert or trading authorization.
   2026-11-11 provider clarification:owner says none selected and offers
   Git,MEGA or TeraBox as options. This is not a provider/account selection.
   Source-code/manifests in Git, encrypted state/archive bundles outside Git
   is the engineering recommendation, not a new repository rule. MEGA has
   first-party scriptable upload/download documentation; MEGAcmd also starts
   a persistent helper, so installation/use is not assumed. TeraBox official
   integration pages did not render in the reader; headless suitability remains
   UNVERIFIED, not disproven. No provider CLI/API/account inspected or invoked,
   no upload/install/start/spending. Provider-neutral local backup implementation
   remains the next work; full off-server R10 still needs actual selection,
   encryption/credentials/capacity and a verified restore. No clock starts.
   2026-11-11T17:02:46Z owner "use your recommendation and keep the other as
   optional":ADOPTED Git for source/docs/manifests, MEGA primary for encrypted
   state/archive backups, TeraBox optional (not automatically configured or
   duplicated). This supersedes the earlier provider-undecided statement, not
   the frozen R10 encryption/coverage/retention/restore requirements. Provider
   choice DONE; account/capacity/authentication/client verification and actual
   encrypted upload/download/restore NOT DONE. No install/login/configuration,
   spending/remote write/service/schedule/trading operation follows from the
   choice. Continue existing offline backup integration; no new provider task.
   2026-11-11T22:28:43Z local selected-input backup/verify/fresh-restore core
   ACCEPTED_WITH_RISK by separate Rawls source GATE after closing its final
   deadline-check finding. Evidence:docs/review_artifacts/group_a_backup_bundle_20261111/.
   SHOWN123focused tests pass; actual synthetic nine-account SQLite/WAL and
   selected-artifact restore, not a live account or encrypted remote test.
   Legacy SQLite helper bodies preserved. Complete live acquisition, physical
   source attribution, full operating-config projection, encryption/key/client,
   MEGA upload/download/restore, retention and foreground entrypoint remain
   NOT DONE. No fake run_group_a_backup.py or deployment-success claim;
   compositor/frozen candidate unchanged. Existing R3/R10 remains INCOMPLETE.
   2026-11-11T23:32:57Z declared-nine-account acquisition bridge separately
   ACCEPTED_WITH_RISK by Rawls after one producer-path selection fix. Source
   services/control/group_a_backup_acquisition.py SHA1efc8726...; evidence
   docs/review_artifacts/group_a_backup_acquisition_20261111/.
   SHOWN155focused tests pass; independent initial151-case run and final
   diff-only four-fail-before/five-pass-after checks. Actual producer capture
   survives acquisition/fresh restore/replay on synthetic data. Required
   three stores/account are pathname-attributed through caller query-only
   connections; attribution is NOT connection-held inode proof. All known
   local artifact paths inventoried, frozen and rehashed, unknown paths refuse
   before payload/scratch; no generic extension-based secret clearance.
   Source supports quiescent local recordings only. Shared/outside objects
   and changing artifacts refuse, not silently omit. Complete live-source/
   shared acquisition, full config, encryption/MEGA/retention/service proof
   remain NOT DONE; no fake foreground entrypoint or operating action.
   2026-11-12T01:55:39Z (owner local11Nov) separate active-prefix/shared-CAS
   acquisition implemented and independently ACCEPTED_WITH_RISK by Rawls.
   Source services/control/group_a_backup_prefix.py SHA4b3dc234...; artifact
   docs/review_artifacts/group_a_backup_prefix_20261112/. Strict/quiescent
   API/core/composition unchanged. SHOWN181focused tests pass; reviewer ran
   all26new tests independently and verified181-case XML, not a full-suite run.
   Existing producer local/shared/mixed journal capture survives fresh restore
   and replay; shared objects deduplicate by verified digest. Hash-bound mapping
   records per-journal cutoffs; later appends are allowed, captured-prefix
   mutation refuses, new sessions after enumeration are explicitly excluded.
   Nonblocking reader acquisition may delay the writer while copying; busy
   locks/transient publication windows safely refuse without retry or repair.
   Native source/connection/permissions/config, encryption/MEGA recovery,
   retention/service/heartbeat/commissioning remain NOT DONE. R3/R10 operating
   status INCOMPLETE; no entrypoint stub, install, host/service/provider action.
   2026-11-12T03:29:32Z native-toolchain fit/proposal independently
   ACCEPTED_WITH_RISK (proposal only), no code/native operation. Proposed
   restic+rclone; not owner-adopted yet. Artifact
   docs/review_artifacts/group_a_backup_native_20261112/. SHOWN current shell
   uname Darwinarm64 and no named clients on PATH, not a full installed-app
   inventory. Next material owner decision:adopt this stack and bounded
   official-binary download/preparation; native test remains held pending
   actual controller/tool/isolation review and applicable authorization.
   Local native encryption/transport/restore proof would not establish MEGA
   login/quota/unattended MFA or cloud durability. No binaries downloaded,
   installed or run; no account/provider/credential/host/service action.
   2026-11-12T04:42:28Z update supersedes that pending adoption/download:
   owner continuation adopted restic+rclone for isolated preparation only.
   One approved download completed:restic0.19.1/rclone1.76.0 Darwinarm64,
   official HTTPS/API/published-checksum provenance; no independent signature
   verification. Tools remain mode0600, outside Git, never executed. Receipt
   docs/review_artifacts/group_a_backup_native_20261112/DOWNLOAD_RECEIPT.json.
   Download controller/executor independently ACCEPTED_WITH_RISK04:26:39UTC.
   Native local-test source independently ACCEPTED_WITH_RISK04:40:50UTC after
   two fail-before/pass-after shared-deadline regressions;21policy tests pass.
   Source SHA28530fa0...; this is not native execution or sandbox proof.
   Next owner boundary:one local synthetic native encryption/restore test,
   300seconds including owned cleanup, no network/accounts/services. No test
   authorized or run yet; MEGA delivery/recovery and R3/R10 remain INCOMPLETE.
   Final focused author source slice242passed14.68s, zero failures/errors/
   skips, one deliberate duplicate-ZIP warning. Self-checked consolidated
   result, not full suite/native encryption; reviewer independently21policy
   tests plus exact regressions. No operational change or new queue started.
3. [safety] Position cap (fix 4) with complete balance reading (fix 1), wired into the live order path; independent review.
   INCOMPLETE (Codex, 2026-10-30): default-off paging and native-v3 funding/quote guards are separately accepted source work
   (245 offline cases independently passed). All-account cap integration is not complete. The October 29 metadata check
   returned one matching default portfolio, not proof that it covers all manual holdings and open orders. Need account-scope
   confirmation before selecting a production evidence provider; no further private call or cap-policy activation authorized.
   The accepted synthetic reservation model is not being reopened. This safety dependency does not block paper/research.
   Blocked on the owner's account-scope answer.
4. [safety] Exit logic in the three default strategies (owner-approved 2026-10-30, priority 1 of the new work): entry filters
   currently block sell signals (`failure_diagnosis_20261030/`). Establish the separation between entry conditions and
   exit/risk controls; build exit-unblocked variants as separate configurations without changing the defaults; offline
   tests; independent review. No change to live or paper execution without review and owner approval.
   First: independently check the failure diagnosis's and the exit-parity audit's material conclusions (cross-review). Start from the existing
   exit-comparison tool on branch `codex/breakout-exit-treatment` (909239e48, reviewed 2026-09-23, shelved for lack of
   eligible data and runner parity; not in HEAD). Resolve the scope gap: say which exits each variant tests, signal
   only or the runner's (invalidation, stop, take-profit, trailing, hold limit).
   Owner-directed cross-review stage 2026-11-02/03: independent saved-result diagnosis finished; 350 captured Claude
   messages read with review/source receipts. Full original-content certification remains INCOMPLETE (20 pasted-file
   controls, external document revisions and code/tool tails). Corrections concern evidence, not an implemented exit
   repair. The existing September tool and October patch 0004 must not be rebuilt as new discoveries. Item 1 remains
   the highest-priority engineering implementation; this stage does not mark it complete.
   Attachment supplement 2026-11-03: all twenty bodies are now available and fully read; only broader original-export/
   revision/hidden-content certification remains limited. No previous market study was repeated and no new experiment
   or operational prerequisite was invented. The existing queue is unchanged.
5. [research] 25-symbol forward comparison (ED-002): protocol frozen before collection, with the existing default strategies
   plus the approved exit variants, benchmarks, costs and acceptance criteria; held-coin rule for limit-only or delisting
   announcements; reporting per strategy and coin of gross and net returns, fees, slippage, trade count, exposure and
   drawdown, and in-market versus out-of-market returns (falls avoided, rises missed, exit-to-re-entry price change).
   Collector on the server; report the actual monthly cost and a monitoring plan; deploy only after owner approval.
6. [research] E1 maker-versus-taker study (unparked by the owner 2026-10-30): measured execution costs on BTC and ETH,
   including unfilled maker orders finished as taker. As designed it models fills from public order-book data; measuring
   real fills needs live orders, which is a separate owner decision behind the safety items.
7. [research] Verify Claude's four research-brief corrections of 2026-10-30 (owner-approved) in `docs/research/RESEARCH_BRIEF.md` section 4.
8. [operations] Protect the work: commit and backup. Starts as soon as decision 1 is approved.
9. [safety] Stuck-exit rule (fix 2) wired, after decision 3; independent review.
10. [research] Tracker v2 stays on time: the 2026-10-18 decision was reconstructed 168.87 hours late; the 2026-10-25 decision
   was on time (0.87 hours). Confirm the next weeks run on time.
   2026-11-05T03:12:39Z (New York November 4): SHOWN original Codex chat records
   the October 25 success but no November 1 invocation, and the saved ledger
   ends October 25. The former local automation directory is absent; current
   Scheduled status and the cause of the missed run remain UNVERIFIED.
   30 synthetic tracker tests passed; saved ledger hashes unchanged. Confirm
   the existing schedule before any repair; do not create a duplicate or
   count any later reconstruction as contemporaneous. INCOMPLETE.
11. [operations] Remove the expired ED-002 pilot job (`com.cryptkeep.ed002.public-inputs`) and record the 39-of-48 pilot result.

## Research queue (Claude; one active)
1. [active] [safety] Whole-bot audit for flaws (owner, 2026-10-31; read-only), simulation path first: market data
   (candles, quotes, staleness), the three default strategies' signal code, the paper engine (fills, fees, cash,
   positions, profit), restart and recovery, monitoring and alerts; then the rest of `services/`. Every finding with
   owner, evidence, severity, disposition. Budget: three sessions for the simulation path. Stop when its checks are
   done; report before the simulation starts. Sessions 1-3 done 2026-10-31 (`docs/research/bot_audit_20261031/`,
   BA-01 to BA-22; spec flaws 9-16 and the before-start list). Simulation-path audit complete; the rest of `services/`
   not audited. Also 2026-10-31: the simulation's Group A scoring script written and tested before the start
   (`docs/research/paper_simulation_spec_20261031/evaluation/`; 7 unit tests pass; dry run on the replay reproduces
   spec 7.5-7.6); frozen once the owner approves the minimum samples and drawdown rule. Live path session 1 done
   2026-10-31 (LP-01 to LP-07: placement and retries careful; HIGH before live: no protection on the exchange if the
   bot or server stops, LP-05; MEDIUM: key permissions checked once, not at start, LP-03). Live path session 2 done
   2026-10-31 (LP-08 to LP-13): the final gate trusts an environment variable, not the ceremony (known; plus two code
   paths around it); position limit still unchecked (H-06); HIGH process finding LP-10, reviewed safety patches of
   early October missing from the code and untracked. Live-path audit complete; rest of `services/` not audited.
   2026-11-05 (Claude, owner "stick to prioritize tasks"): rest of `services/`, session 1 of 3 done (budget 3 sessions,
   task card 12:43:47Z): BA-23 runner adds to winning positions, unmodelled in any backtest or replay; BA-24 runner
   exposure-percentage limits never block; BA-25 paper daily-loss and trade-count gates never fire; BA-26 and BA-27
   additions to deferred items 29 and 16. Self-checked; Codex to verify (`docs/research/bot_audit_20261031/`).
   2026-11-05 session 2 of 3 done: BA-28 known and still present (a failed live daily-loss write counts as success;
   fix in unapplied patches 0059/0076, U-09; HIGH before live); BA-29 to BA-32 LOW (health check, lost trade counts,
   simulation monitor fill lookup, deployment stages not consulted by the default bot). Self-checked; Codex to verify.
   2026-11-05 session 3 of 3 done; budget reached, item stopped: BA-33 email alerts do not verify the mail server's
   certificate (LOW now). 34 of 103 gap modules read or scanned; 69 not covered (non-default strategies and presets,
   research backtest engines, analytics, markets helpers). Owner: extend (suggested 2 sessions), cut, or park the rest.
   2026-11-05 extension (owner "continue your investigation"), sessions 4-5 done; budget reached, item stopped:
   BA-34 (non-default RSI reads a flat market as 100) and BA-35 (research backtest fills at the signal bar's close; a
   missing close charts as 0), both LOW. Coverage 51 of 103 gap modules; the 52 left are off the default simulation
   order path (ES campaign, analytics, stores, helpers). Owner: close the item with this coverage, or extend.
   2026-11-05 second extension (owner: ES campaign and analytics), sessions 6-7 done; budget reached, item stopped:
   BA-36 known (capped-live size gate always passes; the cap it cites is in code no order path calls); BA-37 control
   kernel treats a measured fill rate or regime stability of 0 as perfect (LOW now); BA-38 optional ops risk gate has no
   age check; BA-39 partly known (research win rate is before fees). ES signal evidence stops 2026-10-29; whether ES
   should run is not recorded. Coverage 61 of 103 gap modules. Self-checked; Codex to verify.
   2026-11-05T18:45:50Z independent Codex audit of the complete supplied handoff:
   all BA-23..39 source claims checked; 17 synthetic behavior probes passed.
   BA-23 is conditional on `position_aware=False`, not default runner behavior;
   the default true guard suppresses held-position buys before scaling. The
   proposed simulation-policy choice is therefore not established as necessary.
   BA-28's ignored daily-loss failure was reproduced through the real sink.
   BA-35's archive assurance is too broad (finite zero/negative prices survive).
   Coverage remains INCOMPLETE: 61 read/scanned is author-reported, not identified
   per file in the CSV; ES evidence staleness is not current process proof.
   Full disposition: `docs/research/claude_handoff_audit_20261105/`. No code,
   configuration, queue priority or operating state changed.
2. [handed back for cross-review 2026-10-31] [safety] Capital-protection audit (owner-approved 2026-10-31; read-only). Stage 1 delivered 2026-10-31,
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
3. [handed back for cross-review 2026-10-31] [research] Execution-path reconciliation audit (owner direction 2026-10-31).
   Report delivered (`docs/research/exit_parity_audit_20261031/`); acceptance needs Codex to reproduce it (engineering item 4).
   Establish what the paper/live runner actually trades (entries, exits, stop/take-profit/trailing, hold limit, EMA
   exits, config overrides, rejection and retry), which exits each backtest engine models, a replay of the three default
   strategies with the runner's exits (existing backtest vs corrected), the 83 trades that reached +6%, and which earlier
   conclusions could change. No new strategies, fee optimisation, universe change or scope expansion. Done when the
   findings are reproducible by another agent from the saved scripts, commands and hashes; then report and stop.
4. [paused 2026-10-31, owner direction] [research] ED-002 research specification: define the measurements above (gross and net, fees, slippage, trades,
   exposure, drawdown, in-market versus out-of-market with falls avoided, rises missed and re-entry gaps), state the
   exit-variant arms' hypotheses and pass/fail in advance, and review Codex's freeze before collection starts. No new arms
   beyond the approved exit variants. Open question for the owner before the freeze: should the comparison test the
   strategies' signal exits only (as designed) or also as the paper/live runner would exit them?
5. [research] Owner trade-history study: waiting on the owner's Coinbase fills export (CSV). The raw file stays out of the
   repository; only aggregate, de-identified findings are saved. Trade-level profit after actual fees against holding BTC and cash.
6. [research] E1 analysis once its data exist.
7. [research] Descriptive report on the candidate: market regimes, holding ETH alone, trade count, win rate, profit factor.
   Labelled descriptive, not a test. Needs owner approval.
   2026-11-07 done (Claude; owner "find something within your capacity" taken as the approval): `docs/research/
   candidate_descriptive_20261107/` (plan written before computing; harness curve reproduced exactly; round trips reconcile).
   Descriptive only: net win rate 31-47% and profit factor 1.5-2.6 at 0.50%; the rule gains in BTC bear weeks while both
   holds lose (FULL), trails holding BTC in mixed weeks; holding ETH alone ends highest over FULL but worst in 2024-26.
   Self-checked; Codex to verify.
8. [done 2026-10-31, Claude part; owner "ok"] [safety] Reviewed-patch inventory
   (`docs/research/patch_inventory_20261031/`): the October series (72 patches, branch `claude/series-rev34`, rev88,
   in the repository as `docs/review_artifacts/20261004_rev32_bundle/cryptkeep_series_on_be34a18a_rev88.zip`) is not
   in the laptop's code at all. Includes the multi-symbol fix (0004), the cooldown fixes (0001/0002) and many live-path
   fixes. GitHub master (`be34a18a3`, 2026-10-07, unchanged since) has none of them either; the series' bundle verifies
   against it. Next: Codex recreates `claude/series-rev34` locally from the bundle (no push; Claude's work is pushed only
   after independent review) and reviews 0004 and 0001/0002 first; the owner decides apply or drop for the rest,
   live-path fixes first. The laptop's work also lacks master's PRs #600 and #606 (O-19).
9. [proposed, needs owner approval] [research] Weekly triage of the research-scout reports (OV-06): the top three leads
   ranked against the current plan, each marked pursue, park or drop, for the owner. 30 reports untriaged since 2026-10-19.
10. [done 2026-11-08, Claude; owner request, defaults approved with "go ahead"] [research] How long popular coins take to
   rise 1-5% after a 1-5% dip from the 24-hour high (`docs/research/dip_recovery_majors_20261108/`; plan written before
   computing; 10 coins, hourly 2025-10 to 2026-10 and daily 2017-2026, each beside buying at any hour or day).
   Descriptive only: +1% usually within hours, dip or not. No dependable head start from a dip: the hourly year
   reversed between its halves. Under the main rule (sell at the target, else after 30 days) every combination
   lost after 0.50% costs, dip or random; under the conservative check, 9 of 25 daily dip combinations were slightly
   positive (+0.04% to +0.33% per trade, untested). Self-checked; Codex to verify.
   2026-11-08 additions (owner challenges): charging the sale at the 0.25% maker rate changes no conclusion. A hindsight
   split by calendar year shows daily dips above zero in 10 of 25 combinations in years BTC rose (13 of 25 with a maker
   sale; best -3%/+5% at +0.48% per trade) and in 0 of 25 in years it fell. Owner closed the item ("back to thinking");
   no hourly download for a rising period.
11. [done 2026-11-09, Claude; owner "make a note the findings"] [research] Inventory of the factors that move coin
   prices: what CryptKeep has tested, which have data or code in the repo, and Claude's advice
   (`docs/research/price_factors_inventory_20261108/`). In the bot: price-only strategies, ATR, the spread and staleness
   guard; funding, open interest, Fear & Greed, liquidation and sentiment code exists but does not decide trades. No
   data or code for macro, ETF or stablecoin flows, on-chain, unlocks, news, hacks or fundamentals. Advice is a
   proposal, no owner decision: tracker v2 first, E1 costs second, other factors only as filters on the candidate.
- Done 2026-10-30: failure diagnosis (`docs/research/failure_diagnosis_20261030/`); its three hypotheses were approved with the order above.
- [dependent] Multi-symbol diversification pre-registration: waits on the 25-symbol comparison's forward results (owner 2026-10-30).
- [recurring] Weekly status, Mondays 12:31 UTC (scheduled task).

## Parked (not started until the owner moves it into a queue)
- Four inherited invalid release/build/signing workflows:owner moved this proposal to active engineering12Nov14:42UTC; separate Darwin GATE ACCEPTED_WITH_RISK14:47UTC closes offline source repair only. Original4published runs still failed/0jobs. Availability-booleans repair preserves raw-secret scope;16focused tests independently pass, hosted/complete-standard validation unverified. Changes uncommitted/unpushed; no builds/releases/reruns/new credentials. Exact evidence:docs/checkpoints/commit_plan_20261112/README.md. This line preserves the parked-proposal history, not a second active item.
- Local Git executable selection:2026-11-12 env/gh selected Intel-only /usr/local/bin/git and failed bad CPU type, while /usr/bin/git works. Native absolute-path/per-command selection sufficed; no global install/PATH/config repair. Decision served:reliable operator/automation CLI invocation; park any environment-wide repair rather than expand this pre-push check.
- Earlier companion ProcessExecutor callers:2026-11-12 independent backup-adapter review reproduced spawn-time SIGINT leaving a synthetic child and found signalling after leader reaping. Existing scripts/research/companion_existing_controller.py is unchanged; older callers/acceptance lanes were not re-audited here. Decision served:restore valid cancellation/ownership claims where those callers still operate; propose a scoped follow-up rather than silently certify or modify them during R3 tool preparation.
- Agent-tooling proposal (owner-requested assessment, Codex 2026-11-03): selective, capped Superpowers
  debugging-method pilot inside an approved task; do not stack Clavix or add Composio grants without a demonstrated
  missing capability. Evidence: `docs/review_artifacts/agent_tooling_review_20261103/README.md`. Decision served:
  fewer missed boundaries/rework at lower effort; installation, efficacy and private workspace grants unverified.
- Cost-evidence proposal (2026-11-03): Claude's latest work-log search CLAIMS public Coinbase fee reductions;
  exact applicability/current account tier UNVERIFIED here. Reconcile that evidence with E1/cost inputs before
  revising economic conclusions; no account call, fee assumption change or new experiment authorized/started.
- R1 timing clarification (Codex, 2026-11-03): inherited cooldown early-continue skips the configured interval
  sleep, so the earlier 5/12.5-minute claim and this session's initial 285/735-second estimate are withdrawn.
  Measured blocked cadence/interval handling must be addressed within item 2's operations/start evidence;
  no separate scheduling-policy repair started or priority changed. Decision served: faithful paper timing/load.
- Pre-live defects from the capital-protection audit (2026-10-31), reported at once because they could lose money once
  live routing exists: CP-09 exit orders are blocked by entry limits (daily loss, trade count, notional, market-order
  switch) and a rejected exit is never retried; CP-04 meta strategy runner buys repeatedly without position checks or
  exits (keep it off); CP-12 two inert live executors. For Codex review and owner decision; no fix without approval.
- Other runner defects found 2026-10-31 (`exit_parity_audit_20261031/` section 6): EMA invalidation exits inert; default
  one-second synthetic bars; signals on the forming candle; misleading `config/trading.yaml` comment. For Codex review
  and owner decision; no fix without approval. (The multi-symbol defect is engineering item 1.)
- Runner and gate defects found 2026-11-05 (bot audit BA-23 to BA-27, `docs/research/bot_audit_20261031/`, "Rest of
  `services/`, session 1"), reported at once because they affect the simulation and the position cap: BA-23 the runner adds
  up to 2 full-size entries to winning positions, resets their stop, take-profit and hold references, and no backtest or
  replay models it (disabling scaling removes the limits); BA-24 runner exposure-percentage limits never block; BA-25 paper
  daily-loss and trade-count gates never fire; BA-26, BA-27 additions to deferred items 29 and 16. Decision it serves:
  whether the simulation compares like with like (owner: disable adds in the simulation, or model them in the replay).
  For Codex review and owner decision; no fix without approval.
- Dated qualification 2026-11-05T18:45:50Z to the BA-23 parked entry above and
  O-106: held-position adds are suppressed by the default `position_aware=True`
  guard. Conditional scaling defects remain with that guard disabled, but no
  runtime setting was checked by this review. Do not change the simulation
  solely on the earlier unconditional claim. See O-107 and the handoff audit.
- Rest of fix 3 (funding-rate data). Previously approved work, parked by Claude on 2026-10-30 under the owner's
  "proceed with the best approach"; owner to confirm or move back. Reason: no live decision uses it. The existing
  300-second collector keeps running.
- Fee screenshot (useful, not blocking).
- Dedicated Coinbase portfolio and key: required before any live money.
- CMC failure alerts (window opens 2026-11-10); state of residence; tax lot method; USD vs USDC.
- New strategy families outside the 25-symbol work, ML and sentiment research.

## Undecided ideas (owner-requested list, 2026-11-05)
Ideas raised, proposed or agreed that were never tested, rejected or individually parked. Compiled by Claude (Cowork)
2026-11-05 at the owner's request ("ok") from the work log, Claude's research document (claude.ai artifact
9N9nKeyLa1MStLzzq9SRsh, rev 129, not in the repo), the captured chat (`docs/research/claude_conversation_audit_20261102/`)
and earlier chats. Nothing here is queued or started; an item starts only when the owner marks it pursue and moves it into
a queue. Not repeated because already tracked in this file: Group B (engineering item 2 spec), the rest of fix 3,
CTREND-OOS, CMC alerts, tax lot, state, USD vs USDC, fee screenshot, fills export, capital, the ED-002 exit question,
the descriptive report and the scout triage proposal (research item 9). Scout sorting reached T08 (2026-10-30): 283 leads,
25 plan-changing (most feed U-10, U-12, U-13, U-16, U-26 or the queued E1 and 25-symbol comparison), 31 rule leads,
45 desk checks, 17 approval items (3 are in Parked; the rest are U-29 to U-43), 165 notes; T09 and T10 are unsorted.

| ID | Idea | Raised (who, when) | What happened | Source | Owner: pursue / park / drop |
|---|---|---|---|---|---|
| U-01 | Research on lower-value top-100 and new "prospect" coins instead of BTC/ETH | Owner, Oct (captured msg 28) | Low-value screens and ENTR-CB-1 ran (no edge; STOP); the forward tracker, the candidate and simulation Group A stayed on BTC/ETH (SOL); the 25-symbol comparison is not frozen (research item 4 paused 2026-10-31) | `low_value_top100_20261018/`, `coinbase_tradable_entrants_20261019/`, `paper_simulation_spec_20261031/` | |
| U-02 | Short holding periods; results per hour, day, week and month | Owner, Oct | Every candidate trades weekly or every 4 weeks; asked as "holding range" in the research document's decision list, never answered or carried here | Research document s.15 and decisions | |
| U-03 | Role of machine learning / AI in trading | Owner 2026-11-02 (msgs 190, 321, 325) | AI engine off and never trained; `services/learning` never connected; covered only by the generic Parked "ML and sentiment" line | Captured msgs 191, 322, 326 | |
| U-04 | Original AI plan, phase 2: paper broker with owner approval per trade, event replay, new signals run beside old ones before promotion | trade-ai-mvp, Jan-Mar 2026 | Never built | Captured msg 326 (trade-ai-mvp in git history) | |
| U-05 | Whale / holder concentration as a risk screen (ONCHAIN-1) | Claude 2026-10-20; owner 2026-11-05 | Last in every ranking, never started; scout T01 found nulls for flow signals and no test of concentration | `research_scout/reports/2026-10-22_0343Z_T01.md`, `2026-10-27_1352Z_T01.md` | |
| U-06 | Shadow-stage session producing simulated-fill records | July sequence (owner-agreed) | Recorder on master since Sep; REMAINING_TASKS still lists running a session as remaining | `REMAINING_TASKS.md` (shadow-stage evidence) | |
| U-07 | Walk-forward coin selection (July sequence) | July | Never run; Group B is the planned forward test | Spec s.4 | |
| U-08 | MCB-1 market-context baseline (three gated stages) | Sep | Part of stage 1 built 2026-09-24, default off, never activated; stages 2-3 never built | `docs/research/market_context_capture_v0.md`; branch `codex/mcb1-scope-contract` | |
| U-09 | October review series: 72 reviewed fixes | Claude 2026-10-07 (rev88) | Never applied (O-18); patch 0004 reused for item 1; no decision on the rest | `docs/research/patch_inventory_20261031/` | |
| U-10 | Measurement layer: record order book and trades at each signal, markouts, real cost model | Claude recommendation 2026-10-11 ("adopt now") | Not built; E1 arrival capture not built; no E1 freeze recorded by its 2026-11-03 date | Chat 2026-10-11; research document decisions | |
| U-11 | Spread/timing veto gate (paper, with counterfactual tracking) | Same recommendation ("defer with a written gate to reopen") | Never revisited | Chat 2026-10-11 | |
| U-12 | UNLOCK-1: avoid coins around large token unlocks | Survey rank 3, 2026-10-13 | Held by Claude's 2026-10-28 direction note; not carried here on 2026-10-30; next step a data check, $69-300 only if its gates pass | `docs/checkpoints/claude_cowork_direction_20261028.md`; research document s.4, s.15 | |
| U-13 | FRESH-1: avoid or flag fresh listings (forward only) | Oct | Held 2026-10-28; needs a ruling on whether ENTR-CB-1's STOP bars the history | Same | |
| U-14 | FUND-1: new funding hypothesis on unseen 2019-2020 Binance data | Claude 2026-10-18 ("best near-term candidate") | Never written | `docs/checkpoints/claude_cowork_handoff_20261018.md` | |
| U-15 | VENUE-1: exchange outage and status context | Claude 2026-10-18 ("best-fitting first information candidate") | No incident ledger built | `information_edge_assessment_20261018.md` | |
| U-16 | VOLTGT-1: volatility-targeted holding | Oct | Never scheduled | Research document family 14 | |
| U-17 | MANDATE-15: trend rule on the 15 untested mandate coins | Oct | No decision | `research/symbol_coverage.csv` (UNTESTED 15) | |
| U-18 | LIQ-1: liquidation rebound (BTC rose after 14 of 17 heavy-selling minutes in a 2-hour check) | 2026-10-12 | No follow-up; not in the trial ledger | `liquidation_markout_diagnostic_20261012.md` | |
| U-19 | Historical Coinbase listing study from data already in the repo | Claude 2026-10-19 | Not run | `research/coinbase_listing_stepB_20261019/` | |
| U-20 | LOWVOL-1: low-volatility factor | Oct | Not started | Research document s.4 | |
| U-21 | Module A allocator (E11) | Parameters asked 2026-10-18 | Held 2026-10-28; parameters never set | `chronos_vol_forecast_20261018/PREREGISTRATION.md` | |
| U-22 | Only discussed: ETF and stablecoin flows; news and social sentiment; value measures (fees, users, developer activity per market cap) | Survey and scout | Never proposed or costed | Research document families 18-20 | |
| U-23 | Never assessed: token-contract and wash-trading screens; sector and narrative rotation | Coverage audit 2026-10-20 | Never assessed | Research document families 21-22 | |
| U-24 | Altcoin focus: continue as filters, fold into the 25-symbol comparison, or pause | Research document decision list | Never answered | Research document s.18 and decisions | |
| U-25 | Settings never confirmed: live venue, direction, live risk gates, stress level, turnover cap, whether the server stays, after-tax reporting, altcoin benchmark | Research document s.3 | Never answered (capital and drawdown are decision 2) | Research document s.3 | |
| U-26 | Sealed holdout (answers PASS or FAIL only, query budget fixed) before the 25-symbol comparison freezes | Scout T09-1, 2026-10-27 | Not answered | Research document s.17 | |
| U-27 | Research rules from scout sorting (e.g. dated label snapshots for on-chain features), kept only in the research document | Claude 2026-10-20 to 2026-10-30 | Not in `RESEARCH_BRIEF.md` or AGENTS.md | Research document s.8, 14, 16, 17, 20-26 | |
| U-28 | The research document itself (s.1-29) | Claude 2026-10-20 | Saving it into the repo was asked, never answered; Codex and this file cannot see it | claude.ai artifact 9N9nKeyLa1MStLzzq9SRsh | |
| U-29 | T05-5: spread-estimator check (needs live order-book snapshots) | Scout approval item | Not answered | Research document s.8 | |
| U-30 | T05-9: a cost report the owner downloads (fetch failed) | Scout approval item | Not answered | s.8 | |
| U-31 | T06-4: forward log of Polymarket launch-valuation markets | Scout approval item | Not answered | s.8 | |
| U-32 | T11-3: forward log of Coinbase per-network transfer incidents | Scout approval item | Not answered | s.8 | |
| U-33 | T11-4: descriptive hack-event screen for small coins (DeFiHackLabs dates; low power) | Scout approval item | Not answered | s.8 | |
| U-34 | T00-4: forward altcoin open-interest concentration flag | Scout approval item | Not answered | s.8 | |
| U-35 | T01-3: forward daily altcoin spot-ETF flow log (terms check first) | Scout approval item | Not answered | s.8, s.14 | |
| U-36 | T02-2: forward observation of index additions and removals for top-100 altcoins | Scout approval item | Not answered | s.8, s.14 | |
| U-37 | T02-4: frozen forward unlock calendar for top-100 coins | Scout approval item | Not answered | s.8, s.14 | |
| U-38 | T03-2: forward comparison of volatility estimators (trailing SD, EWMA 0.94, a shorter EWMA) | Scout approval item | Not answered | s.8, s.14 | |
| U-39 | T05-2: read-only Coinbase Preview Orders log (no orders; needs the API key) | Scout approval item | Not answered | s.16 | |
| U-40 | T06-3: metadata-only count of Polymarket token-launch and listing markets (a download) | Scout approval item | Not answered | s.16 | |
| U-41 | T05-3: check the terms of Coinbase's 30-day VIP3 fee promotion (rule: promotions never enter backtest costs) | Scout rule, owner answer | Not answered | s.16 | |
| U-42 | T11-9: read-only forward log of Coinbase's exchange status feed (limit-only flips, delistings) | Scout approval item | Not answered | s.17 | |
| U-43 | T03-2 (second pass): weekly snapshot of Kraken per-coin collateral haircuts, only if altcoin research continues | Scout approval item | Not answered | s.21 | |
| U-44 | REMAINING_TASKS "Deferred Live-Money Substrate Backlog" (19 items to resolve before live money) not linked here | Codex sweep OV-02, 2026-10-31 | No decision | `docs/research/overlooked_sweep_20261031/README.md` | |
| U-45 | 191 unmerged GitHub branches, 118 with work not in master | OV-03 | No list of wanted or obsolete | Same | |
| U-46 | Isolated paper account; strict market-quality configuration; patch 0011 (runner applies the preset's risk limits) | rev87 bundle, OV-04 | Never decided | Same | |
| U-47 | Two old paper collectors on the server since 2026-09-16 (EMA cross, Gate.io and Binance), output unused | OV-05 | Not stopped or documented | Same | |
| U-48 | Research copilot: fix its about 130 failing tests or freeze it | Claude 2026-11-02 (captured msg 324) | No decision | Captured msg 324 | |
| U-49 | Standing data and spending envelope (draft offered) | Research document decisions | Never drafted | Research document decisions | |

Audit qualification, 2026-11-05 (Codex, owner-requested): the introductory
"never tested" / "not repeated" wording above is too broad. U-01 includes completed
screens; U-07, U-10 and U-21 overlap existing work/dependencies. This is a mixed
decision inventory, not 49 independently verified untested experiments. Private
artifact rankings/adoptions and historical operational counts remain attributed,
not newly verified. No owner decision or queue position changes. Full evidence:
`docs/research/onchain_handoff_audit_20261105/README.md`.

Import note, 2026-11-05 (Claude, owner: "take care of what needs to be done for codex"): the U-28 document is now in
`docs/research/claude_research_document_20261020/` (claude.ai artifact rev 129, SHA256 `8f138aec...b67152`). The U-27 rules are
listed verbatim in `proposed_rules_reconciliation.md` there: 30 rules, all PROPOSED, none in AGENTS.md or RESEARCH_BRIEF.md.
Owner decision columns and queues unchanged.

## Closed (reopen only with new evidence)
Done 2026-10-30: 25-symbol analysis (`docs/research/universe25_explainer_20261030/`); its recommended next experiment is the 25-symbol forward comparison (now engineering item 5).
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
| H-06 | E7 reused funding history treated as untouched; `check_live` never checks its position-notional limit | 2026-10-13 (E7); when the gate was written | Not recorded | Disclosure required; limit unenforced on that path | research method; implementation | E7 disclosure; position cap: engineering item 3 | Not recorded (reviewed corrections, 2026-10-20) | None for the gate yet | No |
| H-07 | July 2026 codebase audit did not find the multi-symbol runner defect (CLAIMED from a chat summary) | 2026-07 | Claude | Defect persisted about 4 months | verification | D-1: engineering item 1 | R, Claude 2026-10-31 | Integration test (item 1) | No |
| O-12 | Asked the owner to choose fixed coins (BTC, ETH, SOL) for the paper simulation without saying that the bot has no automatic coin selection: its market ranker is research-only and blocked from trading by design (`signal_discovery_classification.md`, 2026-07-03), and seven research families that picked the strongest coins failed after costs | 2026-10-31, when asking | Claude | The owner chose without that information; choice reopened | reporting | simulation scope: reopened; owner chose "do what's best": ranker group (Group B) added to the spec | O, owner 2026-10-31 | When offering choices, state what the system can and cannot do for each | No |
| O-13 | Set the simulation's loop interval to 15 s (BA-11) without checking what else counts loops: the kill cooldowns become 5 and 12.5 minutes instead of 20 and 50 seconds | 2026-10-31, when writing the setting | Claude | Spec setting; side effect now recorded | search not done for code that counts loops | spec `loop_interval_sec` row (corrected) | R, Claude 2026-10-31 (bot audit session 3) | Before proposing a setting, search the code for everything that reads it | No |
| O-14 | Integrity check S4-05 said no scheduled run of the data-collector cadence check was found; a systemd timer for it is in the repository (`packaging/systemd/cbp-edge-cadence.timer`) | 2026-10-31, stage 4 | Claude | The proposal "schedule the check" was partly wrong (the timer exists; installation on the server unknown) | search scope: `packaging/` not searched | S4-05 (corrected by BA-22) | R, Claude 2026-10-31 (bot audit session 3) | Task cards list the search scope | No |
| O-15 | The kill-cooldown restart lockout (found 2026-10-02, patches reviewed 2026-10-07, never applied) was missing from the engineering queue, the simulation spec, and bot audit session 1, which marked runner decisions and exits as done | 2026-10-31, when writing the spec and session 1 | Claude; the queue since 2026-10-07 | A HIGH defect for the simulation would have gone in unaddressed | findings do not propagate (as H-06, O-11); no prior-work search for the runner in session 1 | spec flaw 14 and engineering item 2 added; session 1 claim corrected | R, Claude 2026-10-31 (bot audit session 3) | Spec and audits check one open-defects list | No |
| O-16 | Spec v2 kept only the cooldown test for stops under known blockers, although Claude's own review reply the same day recommended a test that a stop-loss fills under each blocker (cooldown, refused exit not re-sent, stale data); on current code the last two would fail | 2026-10-31, when writing spec v2 | Claude | Spec v2 would have let the simulation start without proving stops work under BA-04/BA-05 | carried a recommendation into the spec incompletely; no check of the spec against the reply | spec v2 corrected 2026-10-31: R12 adds the stop and trailing-stop tests under all three blockers | O, owner 2026-10-31 (third review shared by the owner) | Check each adopted recommendation line by line against the written spec before reporting | No |
| O-17 | Bot audit LP-10 reported that markers of patches 0056 and 0057 were present in the code; the strings predate those patches (in base `97c24c8e4`), so they showed nothing | 2026-10-31, when writing LP-10 | Claude | A wrong "two fixes present" was reported to the owner | marker not checked against the base | LP-10 (corrected the same day) | R, Claude 2026-10-31 (patch inventory) | A presence check compares against the base, not only the current code | Yes (inventory method) |
| O-18 | The October review series (72 patches, Claude, rev88, 2026-10-07, ready for review, never pushed or applied) was absent from PROJECT_STATE and from this session's work: D-1 was proved as new (fix 0004 existed since 2026-10-02), the multi-coin fix was queued for Codex as new work, the cooldown fix specified as R1 | 2026-10-30, when D-1 was diagnosed | Claude; PROJECT_STATE since 2026-10-07 | Engineering item 1 and simulation R1 were planned as new work; earlier fixes for live-path defects were not considered | the bundles and work log not searched for prior fixes; the series' status lived only in its bundle README | engineering items 1 and 2, bot audit, capital-protection audit CP-03 (status: open) | R, Claude 2026-10-31 (patch inventory) | Before diagnosing or queuing a fix, search `docs/review_artifacts/` bundles and the work log for an existing patch | No |
| O-19 | The commit review and integrity check S4-07 said the laptop was "4 commits ahead" of GitHub master; it had forked at `adde462ff` (2026-09-23) and was also behind (PRs #600, #601, #603; GitHub has since added #605, #606). The laptop's code holds #601, #603 and #605 but not #600 or #606 | 2026-10-31, commit review | Claude | The backup and merge plan did not mention that the laptop's work must be reconciled with master | counted `origin/master..HEAD` only, not the reverse | commit plan, S4-07 (corrected) | R, Claude 2026-10-31 (after the owner's fetch) | State ahead and behind counts and the merge base for any branch comparison | No |
| O-20 | This session's audits did not search `REMAINING_TASKS.md`, whose "Deferred Live-Money Substrate Backlog" (19 items) already held several findings reported as new (BA-19, BA-21, LP-02, LP-08/LP-09, simulation R8, backups, secrets); `PROJECT_STATE.md` never references that file | 2026-10-31, bot audit and live-path sessions | Claude | Duplicate findings; the pre-live list here was incomplete | two task lists not linked; search scope limited to `docs/` | bot audit BA-19/BA-21, LP-02/LP-08/LP-09; spec R8 (status: cross-referenced in `overlooked_sweep_20261031/`) | R, Claude 2026-10-31 (owner's question) | `PROJECT_STATE.md` points to that backlog; new pre-live findings are checked against it first | No |
| O-21 | Did not tell the owner that the project as a whole keeps changing course before finishing (research order agreed July, replaced September, replaced again October; 72 reviewed fixes dropped and re-planned; two unlinked task lists; 191 unmerged branches; the laptop's work apart from GitHub since 2026-09-23). The pieces were in this session's own findings (O-15 to O-20, LP-10, OV-02, OV-03) but were logged one by one, never reported as one problem | 2026-10-31, by the patch inventory at the latest | Claude | The owner had to raise it himself | findings recorded separately; no step that looks across them | none changed; reporting | O, owner 2026-10-31 | When several findings share a cause, report the shared cause to the owner when it is first seen | No |
| O-22 | Gave the owner "outside the box" advice and asked him for the project's goal, budget and date without first searching the repo, which already holds the goal (AGENTS.md POP objective, 2026-10-30), the cost and capital arithmetic and a proposed finish line (`strategy_decision_report_20261011.md`: test only the BTC+ETH 28-day trend in the existing weekly paper test, decide after six months, no new machinery); also advised parking the research copilot without knowing the owner chose to restore it (2026-10-11, decision I01) | 2026-10-31, before advising | Claude | The advice repeated an earlier answer as new and contradicted an owner decision | prior-work search skipped for advice | none changed (advice only) | O, owner 2026-10-31 | Search the repo and work log for an existing answer or decision before advising or asking the owner | No |
| O-23 | The commit review recommended making the repository private without saying that GitHub Actions storage and minutes are free only for public repositories; on GitHub Free a private repository gets 500 MB of artifact storage (existing artifacts count, hourly) and \$12 a month of compute, and `.github/workflows/nightly.yml` builds macOS and Windows apps every day at 02:00 UTC and uploads them with the default 90-day retention. The owner received a 100%-of-storage email on 2026-11-01 | 2026-10-31, commit review | Claude | Storage quota reached; nightly macOS builds will also use up the included compute | consequences of the visibility change not checked against the workflows | commit review (corrected in chat 2026-11-01) | O, owner 2026-11-01 | Before recommending a settings change, list what it changes in billing and automation | No |
| O-24 | Told the owner the nightly build had filled the Actions storage and that the branch pushes started only two checks, from the workflow files alone. GitHub's own records (read 2026-11-01, public API) show: every nightly run failed in about 25 s and stored nothing (last run 2026-10-22; switched off manually 2026-11-01); the storage is 426 old build files, 27.2 GB, of which 26.3 GB are 212 macOS builds from `ci-pyinstaller.yml` (2026-08-13 to 2026-10-07, push to master and pull requests); each branch push started six workflows, four of which failed at once with no job run (0 jobs) | 2026-11-01, before answering | Claude | Wrong cause given to the owner for a billing problem | inferred from repository files instead of checking GitHub's records | corrected in chat 2026-11-01 | R, Claude 2026-11-01 (while acting on the owner's "you do it") | Check the system's own records before naming a cause | No |
| O-25 | E1 viability hypothesis compared 0.35% per-side costs with about 0.45% per-trade gross return | 2026-10-30 diagnosis and subsequent review | Claude; no prior independent arithmetic acceptance established | Yes: proposed cost threshold unjustified | research method; verification | diagnosis hypothesis 2 and copied advice: dated correction; measurement hypothesis remains open | R, Codex/reviewer 2026-11-02/03 | Explicit one-way/round-trip and fee-only/all-in calculation | Yes, synthetic counterexample; no corrected market result |
| O-26 | In/out attribution used post-open holdings to classify close-to-close opening gaps | 2026-10-30 diagnosis | Claude; prior review of this attribution not established | Yes: timing and rises-missed/falls-avoided conclusions unsupported | implementation; research method | diagnosis attribution and handoff totals: withdrawn pending corrected accounting; saved trades unchanged | R, Codex/reviewer 2026-11-02/03 | Check interval ownership at both trade boundaries before attribution | Yes, buy-at-200/sell-at-100 counterexample; market correction not implemented |
| O-27 | Exit-price ratio times $100 reported as fixed-entry-notional counterfactual dollars | 2026-10-30 diagnosis | Claude; prior independent acceptance not established | Yes: -$15/+$28/+$65 and dependent percentages unsupported | implementation; verification | diagnosis and handoff dollar effects: withdrawn; SELL-filter source finding retained | R, Codex/reviewer 2026-11-02/03 | Original quantity times matched execution-price difference | Yes, synthetic denominator counterexample; corrected market totals unknown |
| O-28 | CMC sorting summary did not distinguish raw Coinbase product matches from identity-qualified coins, including excluded AI | 2026-11-02 sorting report | Claude | Could affect perceived candidate eligibility; no scored result changed | reporting | message 350 and work-log summary: qualified by this audit; logger retains correct mismatch exclusion | R, Codex/reviewer 2026-11-02/03 | Report raw matches, verified identities and exclusions separately | Latest metadata checked; historical CSV aggregation not verified |
| O-29 | Repeated no-profit/all-lost claims omitted positive historical models and favourable E9 metrics despite earlier corrections | Each renewed claim, including messages 202/276/332/334 | Claude; earlier reviews did correct some wording | Yes: misleading research direction/closure, not changed registered verdicts | reporting; evidence discovery | blanket claims rejected in cross-review; scoped FAIL/STOP and positive historical outcomes both preserved | R, Codex/reviewers 2026-11-02/03 | Include favourable counterexamples before family-level rejection; profit is not edge | Selected saved outcomes checked; no universal revalidation |
| O-30 | Historical product coverage and eight removed-winner checks described as exhaustive uncertainty resolution | 2026-10-19 entrant closure (messages 40/65/67) | Claude | Could change confidence in closure; effect of residual data limits unresolved | research method; reporting | historical tradability and only-remaining-check assurances narrowed; registered dataset STOP preserved | R, Codex/reviewer 2026-11-02 | Explicit unresolved control gaps, losers, regional and historical-universe limits | Saved review/results compared; complete listing history unverified |
| O-31 | Companion work described as uncommitted after its unreviewed backup commit | Messages 324/340, after 290 | Claude | Misstated preservation state; no acceptance or push follows from commit | reporting | companion status: distinguish committed backup from reviewed/integrated/running | R, Codex/reviewer 2026-11-03 | Read commit metadata and test-failure categories before status report | Local backup commit checked; current remote/runtime not checked |
| O-32 | All-72-patches author-only wording omitted recorded patch-specific independent-review distinctions | Message 332 | Claude | Misstated historical acceptance; series still needs current integration proof | reporting | patch inventory/review status: retain individual acceptance/risk/current-form limits; no blanket series approval | R, Codex/reviewer 2026-11-03 | Compare patch review receipts and current-form hashes, not marker presence alone | Saved inventory/review wording checked; full series not rerun |
| O-33 | Task card was not recorded at the start of this audit; first in-memory capture was lost and a local editor tool blocked for 4,408.375 seconds | 2026-11-02 before work and at the failures | Codex | Owner time/resource cost; no market outcome or authorization changed | reporting; verification | this audit: late card/failure disclosed, durable copy saved, full-source completeness not claimed | R, Codex 2026-11-02/03 | Record task card first; persist capture before long work; stop treating tool delay as progress | Durable capture/hash verified; timeout cause unknown; prevention not proven |
| O-34 | Credential format treated as evidence that a string could not be real | 2026-10-19 message 65 | Claude | Could mislead publication clearance; actual provenance unresolved | verification; reporting | synthetic-provenance assurance rejected; no secret content inspected or clearance granted | R, Codex/reviewer 2026-11-02 | Require source provenance/owner confirmation, not vendor-shape heuristics | No; no credentials read |

| O-35 | Full-window beta above one interpreted as evidence that 21/23 coins fall further on BTC's worst days | 2026-10-30 universe analysis; initial conversation cross-review | Claude (report), advisor attachment 8 (repetition), Codex (initial review did not flag it) | Narrows downside-risk interpretation; saved return/correlation numbers unchanged | research method; verification; reporting | universe README and repeated advice: dated correction; beta and downside correlation separated | R, Codex/reviewer during attachment supplement 2026-11-03 | Trace each interpretation to its actual conditional or unconditional calculation | Source formula checked independently; no new market run |
| O-36 | Similar BTC correlations over twelve months used as general evidence of venue equivalence | 2026-10-30 universe analysis; initial cross-review | Claude; Codex initial review did not challenge the scope | Narrows proxy-data validity claims; no numerical result changed | research method; verification | universe README: dated correction; returns/fills/liquidity/cost/earlier-history equivalence remains unverified | R, Codex attachment/source review 2026-11-03 | State the exact property/window a venue comparison checks | Source/wording checked; equivalence not established |
| O-37 | Weekly status task (trig_01RhwsmMCnq4eAsqqqkurWZC) created and edited 2026-10-30/31 and recorded as ready ("repo folder attached", "re-signed") without a test run; its first run (2026-11-02 12:38Z) found no folder connected and stopped, so no weekly status was produced | 2026-10-30 at setup; each edit on 2026-10-31 | Claude | Yes: the only standing check of Codex and the queues did not run in its first week | verification | weekly status 2026-11-02: not produced; earlier "re-signed" work-log lines did not show folder access | R, Claude 2026-11-03 (missing record, during owner-requested monitoring check); cause from the run output the owner supplied | Test-run each scheduled task after creating or editing it and check the file it writes | No |

| O-38 | Initial multi-symbol repair repeated every symbol's venue resolution outside the runtime error boundary; 22 passing tests omitted post-startup venue errors | Before the 2026-11-03 initial implementation handoff | Codex implementation/self-check | Yes: initial narrow code submission rejected; no deployment or trading occurred | implementation; verification | item 1 failure-isolation completion narrowed, corrected, awaiting separate re-review | R, independent reviewer Poincare during owner-requested engineering 2026-11-03 | One-time all-symbol startup validation; local subsequent venue resolution; new venue uncertainty still fails closed | Yes, later venue error regression fails initial submission and passes correction; separate re-review pending |
| O-39 | New per-turn checkpoint could replace unreadable saved price history with an empty fallback; partial-latch-read tests did not cover price-read failures | Before the 2026-11-03 initial implementation handoff | Codex implementation/self-check | Yes: initial narrow code submission rejected; no operational data was touched | implementation; verification | item 1 persistence-safety completion narrowed, corrected, awaiting separate re-review | R, independent reviewer Poincare during owner-requested engineering 2026-11-03 | Track successful price-history loading separately; gate periodic and final writes; quote/no-quote tests through fifth visit in both branches | Yes, four cases fail initial submission and pass correction; separate re-review pending |

| O-40 | Estimated cooldown wall time by multiplying counts by configured interval, overlooking early-continue skipping sleep | R1 report preparation 2026-11-03; earlier simulation BA-17 inference | Codex R1 report and initial R1 review caveat; earlier Claude specification | Yes: timing estimates withdrawn before final handoff; counts and trading settings unchanged | verification; reporting | R1 report and frozen-spec timing claims: dated qualification; separate final source review ACCEPTED_WITH_RISK, actual blocked cadence unknown | R, Codex during owner-requested engineering 2026-11-03 | Trace each timing branch to actual waits; measure cadence before simulation start | Source checked and two independent zero-sleep probes pass; runtime cadence not measured |

Counts 2026-11-03 after attachment supplement: 36 omissions (O-01 to O-36): agent unprompted 0; during owner-requested work 28; owner 8. The earlier November 3 checkpoint had 34 (26 during requested work).
Counts 2026-11-03 01:36Z (Claude, after O-37): 37 omissions (O-01 to O-37): agent unprompted 0; during owner-requested work 29; owner 8.
Counts 2026-11-03 05:10Z (Codex, after O-38/O-39): 39 omissions; agent unprompted 0; during owner-requested work 31 (including these two caught by separate agent review); owner 8. These two were corrected before acceptance, so do not increment accepted-work rework count.
O-38/O-39 closure update 2026-11-03: independent focused re-review ACCEPTED both corrections; 28 integration
cases plus three independent probes passed. The earlier pending-review cells above are historical; source
corrections are now accepted, operational proof remains INCOMPLETE.
Counts after O-40: 40 omissions; agent unprompted 0; during owner-requested work 32; owner 8.

| ID | Omitted | Should have been found | Missed by | Changed a result or decision | Why missed | Conclusions affected (status) | Found by | Control | Control tested |
|---|---|---|---|---|---|---|---|---|---|
| O-41 | Pending-exit atomic fence recognized only an exact policy, allowing malformed marked exits into ordinary accounting | Before R12 initial submission 2026-11-03 | Socrates implementation; Codex integration/self-check | Yes: initial R12 source rejected; no operation occurred | implementation; verification | malformed-state/fence claim withdrawn pending correction/re-review | R, independent reviewer Poincare 2026-11-03 | Detect marker presence first, then validate; malformed/superseded-replacement regressions | Correction tests pending |
| O-42 | R12 reused generic linked-order reconciliation without canonical-root and real-fill receipt proof | Before R12 initial submission 2026-11-03 | Codex implementation/self-check | Yes: source rejected; probe falsely completed unfilled roots | implementation; verification | truthful terminal/journal guarantee narrowed; correction pending review | R, independent reviewer Poincare 2026-11-03 | Ledger authority/canonical link required before journal or terminal; unrelated-buy and zero-receipt probes | Two regressions fail initial submission and pass correction; review pending |
| O-43 | Optional strategy identity accepted by ledger prepare was overwritten by configured empty value at engine insertion | Before R12 initial submission 2026-11-03 | Codex implementation/self-check | Yes: API request could be accepted then never filled; actual runner failure unproven | implementation; verification | API-coherence claim corrected; review pending | R, independent reviewer after Codex identified possible edge during handoff 2026-11-03 | Preserve pending optional identity consistently; direct API regression | Regression fails initial submission, passes correction; review pending |
| O-44 | Routed root quantity differed from the executable holding-bounded retry quantity | Before R12 initial submission 2026-11-03 | Codex implementation/self-check | Yes: conditional starvation with size-sensitive router; current router holding-bound refusal not established | implementation; verification | routed-retry coherence corrected; review pending | R, independent reviewer after Codex flagged edge 2026-11-03 | Route bounded copy; cap execution at routed quantity even if holdings grow; root immutable | Two regressions fail initial submission, pass correction; review pending |
Counts after O-41 to O-44: 44 omissions; agent unprompted 0; during owner-requested work 36; owner 8.
These four are corrections to a rejected, not accepted, source candidate; accepted-work rework count unchanged.
Correction evidence 2026-11-03: all four source defects corrected, final focused 487 passed; five new routing/
identity/reconciliation cases fail the initial submitted modules and pass corrections. Eighty-five added storage
cases give 60 failures/25 preservation passes against the initial submission, and pass corrected storage.
The earlier pending-test cells above are historical. At that correction handoff, separate re-review was pending.
Final O-41/O-44 closure 2026-11-03: separate corrected-source GATE ACCEPTED_WITH_RISK after all four original
findings and routed-growth protection were rechecked; 183 cases/eight probes passed. Earlier pending-review cells
are historical, not the current source disposition. All operational/other-requirement limits remain.

| ID | Omitted | Should have been found | Missed by | Changed a result or decision | Why missed | Conclusions affected (status) | Found by | Control | Control tested |
|---|---|---|---|---|---|---|---|---|---|
| O-45 | R9 described the exit stack's priority as the entire runner's order, omitting preceding EMA invalidation | Frozen paper-spec preparation/review, 2026-10-31 | Claude specification; earlier review did not qualify the full runner order | No strategy rule changed; generic priority claim corrected; zero-threshold invalidations remain inert | verification; reporting | R9 ordering description: dated correction; source replay review pending | R, Codex during owner-requested R6/R9 implementation 2026-11-03 | Compare real runner precedence with stack; record all predicates and actual winner | Saved old-block comparison and EMA-priority regression pass; current runtime not checked |
| O-46 | R6 requested hours held without establishing that the runner stores elapsed holding time; it stores distinct-bar count | Frozen paper-spec preparation/review, 2026-10-31 | Claude specification; earlier review did not identify clock representation | Literal elapsed-hours field remains unmet; cannot silently label bars as observed hours | implementation; verification | R6 completeness: explicitly partial for elapsed time and commissioning, not closed by synthetic replay | R, Codex during owner-requested R6/R9 implementation 2026-11-03 | Name actual state clock; retain exact bars; require explicit decision before changing hold semantics | Source inspected; elapsed-time field/control not implemented or independently accepted |
Counts after O-45/O-46: 46 omissions; agent unprompted 0; during owner-requested work 38; owner 8.
These qualify the already counted paper-spec rework item (O-40), not two additional accepted artifacts.

| ID | Omitted | Should have been found | Missed by | Changed a result or decision | Why missed | Conclusions affected (status) | Found by | Control | Control tested |
|---|---|---|---|---|---|---|---|---|---|
| O-47 | V2 loaded-code identity hashed defining modules/four canonical runner functions, not all active decision bindings; changed aliases could replay as matching code | Initial R6/R9 source submission 2026-11-03 | Linnaeus archive implementation; Codex integration/self-check | Yes: independent source GATE REJECTED; no operation occurred | implementation; verification | implementation-identity claim withdrawn pending alias/caller correction and re-review | R, independent reviewer Poincare 2026-11-03 | Fingerprint explicit whitelisted active caller functions/aliases, compare canonical replay bindings; alias and noncanonical-caller regressions | Three independent probes failed initial candidate; correction/before-after proof in progress |
Counts after O-47: 47 omissions; agent unprompted 0; during owner-requested work 39; owner 8.
O-47 corrects rejected candidate work, not an independently accepted source artifact; accepted-work rework count unchanged.
O-47 closure 2026-11-03: explicit active-caller bindings and deterministic typed code identity corrected the gap;
seven added cases fail the rejected capture module. All three original independent probes plus an active-alias
probe pass; final eleven hashes matched, separate GATE ACCEPTED_WITH_RISK. The affected slice gave 143 passed and
one observation-fixture failure, followed by the corrected isolated case passing (not one 144-pass command).
Earlier pending-control cells are historical. O-45's description is corrected; O-46 elapsed-time requirement and
R6 observed-hour/host commissioning remain open, not accepted by this source disposition.

| ID | Omitted | Should have been found | Missed by | Changed a result or decision | Why missed | Conclusions affected (status) | Found by | Control | Control tested |
|---|---|---|---|---|---|---|---|---|---|
| O-48 | A durable queue sell contradicted an existing journal `unwritten` marker, but recovery allowed entries with an uncounted event | R8 accounting development before source handoff, 2026-11-03 | Codex initial integration/self-check | Yes: initial controller silently reported settled; corrected before independent source review | implementation; verification | exactly-once authority/entry-block claim corrected, review pending | R, test worker Parfit during owner-requested implementation | Treat permanent-unwritten versus written queue evidence as unresolved; never discard either | Regression fails initial controller and passes correction; 44-case current integration passed |
| O-49 | Extending decision capture to accounting included the storage module but skipped storage-class methods in its fingerprint | R8 integration development before source handoff, 2026-11-03 | Codex initial dependency wiring | Yes: draft fingerprint missed changed journal apply code; corrected before review | implementation; verification | loaded-code coverage extended to services/storage classes, review pending | R, Codex during owner-requested implementation | Method-mutation regression on the newly referenced storage class | Regression fails initial prefix guard, passes correction |
Counts after O-48/O-49: 49 omissions; agent unprompted 0; during owner-requested work 41; owner 8.
These correct development candidates before acceptance, not additional accepted-work rework.

| ID | Omitted | Should have been found | Missed by | Changed a result or decision | Why missed | Conclusions affected (status) | Found by | Control | Control tested |
|---|---|---|---|---|---|---|---|---|---|
| O-50 | Queue-first accounting metadata used permissive JSON decoding although the journal rejected duplicate keys; conflicting loss/gain keys could count a gain and admit a paper buy | R8 prerequisite submission 2026-11-03 | Codex implementation/self-check; test matrix missed duplicate/nested keys | Yes: separate P1 review REJECTED source candidate; no operational run occurred | implementation; verification | fail-closed corrupt-evidence claim withdrawn pending correction/re-review | R, independent reviewer Poincare 2026-11-03 | Reuse journal strict finite-object decoder at queue-evidence boundary; preserve raw metadata in quarantine; duplicate-key real-runner tests | Original probes fail initial candidate; six corrected duplicate-level/flat-held cases pass; re-review pending |
Counts after O-50: 50 omissions; agent unprompted 0; during owner-requested work 42; owner 8.
O-50 is a rejected-candidate correction, not a new accepted-work rework item.
O-48/O-49/O-50 source closure 2026-11-03: separate corrected prerequisite GATE ACCEPTED_WITH_RISK;
167 cases plus all three original probes pass independently; eight old-method ambiguity cases fail as expected,
11/11 corrected hashes match. Earlier pending-review cells are historical. The corruption boundary is corrected
for this source scope; full R8/R4, current DB/venue/configuration and operational readiness remain INCOMPLETE.

| ID | Omitted | Should have been found | Missed by | Changed a result or decision | Why missed | Conclusions affected (status) | Found by | Control | Control tested |
|---|---|---|---|---|---|---|---|---|---|
| O-51 | Initial paper-buy lifecycle draft could dispose a queue row while an order/fill survived a lost response, or lose the older intent age on legacy-order recovery | R8 buy-lifecycle implementation before source acceptance | Codex integration/self-check; initial draft tests | Yes: narrow source-completion claim withheld; no operation occurred | implementation; verification | corrected source ACCEPTED_WITH_RISK by separate correction GATE; operation unverified | R, Codex during owner-requested continuation; separate GATE exposed failed first correction | Ledger-first fence, commit-uncertain recovery and authoritative read-only queue origin at expiry/fill even after failed metadata binding | Before-source late-fill/response-loss probes fail; unchanged transient-write/restart probe and independent lock-wait/origin probes pass; source closed with risk |
| O-52 | New buy fill guard treated only `new` as active, rejecting the previously supported legacy `open` status and preventing real-ledger harness holdings | Expanded R8 regression before source handoff | Codex/storage worker self-check covered canonical `new` but not legacy active status | Yes: first consolidated selection failed; no deployment/trade | implementation; verification | corrected source ACCEPTED_WITH_RISK by separate correction GATE | R, Codex consolidated regression during owner-requested continuation | Preserve explicit legacy active status while applying the same TTL; no weakening of the real multi-symbol harness | Initial selection 554 passed / 34 failed / 33 errors; fresh/expired-open regressions pass in corrected independent 356-case slice; source closed with risk |
| O-53 | Recovery reported contradictory buy identity but the ordinary reconciliation loop still attributed the linked fill and terminalized the intent | R8 buy-lifecycle source integration before acceptance | Codex integration/self-check; original happy-path identity tests | Yes: independent GATE rejected source; no operation occurred | implementation; verification | corrected source ACCEPTED_WITH_RISK by separate correction GATE | R, separate GATE during owner-requested continuation | Consume unresolved recovery faults and validate canonical order/fill receipts again before attribution, including rows arriving after inventory | Original wrong-link/wrong-quantity probes pass unchanged; additional inventory/receipt/canonical probes pass; source closed with risk, not full account reconciliation |
Counts after O-53: 53 omissions; agent unprompted 0; during owner-requested work 45; owner 8.

2026-11-03 correction to O-51: the first attempted older-origin persistence fix was insufficient.
A reviewer-triggered SQLite write failure rolled it back, after which evaluation filled at queue age 121 seconds.
The candidate was REJECTED; original-age safety is not closed by the earlier passing tests or metadata write alone.
This is pre-acceptance correction, not accepted-source rework. O-52 compatibility remains subject to corrected review.
Final 2026-11-03 disposition: that separate correction review ACCEPTED_WITH_RISK closes O-51/O-52/O-53
for the sealed source boundaries only. Full R8, R4, runtime/host/alert evidence and operation remain incomplete.
| O-54 | Draft account initializer validated new-account defaults even when an existing cash balance made them unused, potentially preventing existing paper exits on construction | R8 account reconciliation integration before source handoff | Codex storage draft/integration; initial validation placement | Yes: moved validation before handoff; no operation or financial state changed | implementation; verification | existing-account initialization compatibility corrected; separate review pending | R, Codex source inspection during owner-requested continuation | Validate only inputs needed for an actual initialization/certification; never re-baseline an existing balance | Existing-balance/unused-invalid-default cases in snapshot tests pass; consolidated 546 passed; current source awaiting independent review |
Counts after O-54: 54 omissions; agent unprompted 0; during owner-requested work 46; owner 8.
O-54 source disposition 2026-11-04 UTC: owner accepted submitted correction with risk after the source handoff;
technical tests remain self-checked, no independent reviewer disposition. Operating behavior is unverified.
These are development-candidate corrections, not additional independently accepted-work rework.
| O-55 | Missing-price mark-to-market writes cash-only equity and zero unrealized P&L with ok=True while a position remains held; exact-symbol repair exposes this more often | R4 price-change caller/consequence review before economic or commissioning acceptance | Existing implementation and Codex exact-symbol caller self-check did not surface valuation consequence | Yes: old valuation rows cannot support economics; source repaired before operation; no frozen research outcome changed | implementation; verification; reporting | Engine/current-monitor source ACCEPTED_WITH_RISK by separate GATE; full R4, other views and simulation remain incomplete | R, separate R4 GATE during owner-requested continuation | Held missing/invalid reference produces incomplete/null valuation and no equity insert; current monitor preserves unknown; no historical rewrite | Twelve old-method cases fail; current author 241-case slice passes; separate 58 focused plus five probes pass and three-file seal matches; narrow source closed with risk |
Counts after O-55: 55 omissions; agent unprompted 0; during owner-requested work 47; owner 8.
| O-56 | Draft candle diagnostics were persisted before the post-read buy TTL verdict, so a selective diagnostic-write failure could prevent required expiry | R4 guarded-fill integration before source handoff | Codex storage draft/integration; initial precedence check omitted combined failure | Yes: source ordering corrected before review, no operation | implementation; verification | post-read expiry precedence corrected; separate GATE pending | R, Codex main source inspection during owner-requested continuation | Check deadline/fence before optional diagnostic persistence; no late fill or diagnostic-induced permanent expiry obstruction | Four corrected combined boundary cases included in final 839; worker's claimed initial four failures lack standalone preserved artifact; current review pending |
| O-57 | Candle-diagnostic projection passed a new dictionary through the old global public-key whitelist, dropping completeness/missing-hour fields | First R4 archive integration check before source acceptance | Codex capture integration | Yes: required diagnostic fields absent from draft; no operating data loss | implementation; verification | field-specific safe projection corrected; separate GATE pending | R, Codex focused tests during owner-requested continuation | Explicitly whitelist diagnostic keys and sanitize values individually; test retained required fields and dropped secrets | Initial 89 passed/one field assertion failed; corrected capture and consolidated 839 cases pass; separate review pending |
Counts after O-56/O-57: 57 omissions; agent unprompted 0; during owner-requested work 49; owner 8.
O-56 dated qualification, 2026-11-04: independent initial GATE reproduced a late fill when the successful
diagnostic write delayed an unexpired buy across120 seconds. The first correction covered already-expired
write failure, not this delay. Candidate REJECTED; retain pre-diagnostic expiry and add a post-diagnostic
recheck in the one bounded correction. Source-completion claims remain unaccepted. No new omission count
is added for this second variant of the same ordering boundary; no operation or accepted-source rework occurred.

O-56/O-57 closeout, 2026-11-04: separate GATE ACCEPTED_WITH_RISK for the corrected buy guard and TTL.
The delayed-write regression passes unchanged; field projection is shown for serializable records only.
This is not independent acceptance of complete invalid-feed archiving.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-58 | Archive projection proof omitted malformed raw OHLCV that causes strict validation to reject the entire record before diagnostic persistence | R4 capture integration before claiming diagnostic completeness | Codex initial integration and archive tests | Yes: invalid-feed diagnostic completeness remains open; no effect on the sealed buy guard acceptance | implementation; verification | Full R4 and invalid-feed diagnostic retention INCOMPLETE; bounded guard/TTL ACCEPTED_WITH_RISK | R, Codex synthetic probe during owner-requested work | Test a diagnostic-only error receipt separately from raw record validation; preserve sanitizer and execution authority | Gap reproduced with a NaN close; proposed receipt not implemented or tested |

Counts after O-58: 58 omissions; agent unprompted 0; during owner-requested work 50; owner 8.

O-58 dated update, 2026-11-04: diagnostic-only retention implemented and self-checked (208 targeted
passes); READY_FOR_INDEPENDENT_REVIEW. Strict raw-record rejection and the original O-58 evidence
are unchanged. This is not proof of operating capture, a successful replay or a fill.

O-58 independent review, 2026-11-04: REJECTED for this increment. The NaN retention claim is supported;
accurate archive-failure attribution and source distinction are not.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-59 | A negative assessment plus an unrelated settings-validation failure can create a candle diagnostic when raw bars pass archive validation | O-58 fallback design and author verification | Codex implementation and self-check | Yes: source not accepted; receipt can misdirect diagnosis | implementation; verification | O-58 increment REJECTED, earlier buy guard unaffected | R, independent GATE during owner-requested review | Require raw-bar validation failure, including when projection independently fails | Failure demonstrated; correction not started |
| O-60 | Diagnostic receipts omit source, so public and sample candle input are indistinguishable | O-58 receipt contract and actual runner caller check | Codex implementation and self-check | Yes: receipt cannot attribute a negative observation to the public feed | implementation; reporting | O-58 increment REJECTED; no runtime evidence affected | R, independent GATE during owner-requested review | Propagate bounded observed source labels; never infer public when unknown | Failure demonstrated; correction not started |

Counts after O-59/O-60: 60 omissions; agent unprompted 0; during owner-requested work 52; owner 8.

O-59/O-60 dated closeout, 2026-11-04: separate GATE ACCEPTED the correction after independent
raw-bar attribution, source labeling, opt-in and replay-isolation probes. The controls are tested
for the bounded synthetic scope. Earlier rejected results remain in the record; no live proof.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-61 | Publisher does not verify returned ticker identity before stamping the requested market as public | R4 strict publisher-to-fill integration | Codex implementation and self-check | Yes: wrong-market quote priced a synthetic paper sell; source not accepted | implementation; verification | Strict quote/fill increment REJECTED; no observed live fill | R, independent GATE during owner-requested work | Check the returned instrument against the requested venue instrument; retain verified identity or fail strict qualification | Mismatched response reproduced through publisher and real paper ledger; correction not started |
| O-62 | Serialized fill validates the receipt but not the submitted fill price against quote and canonical limit | R4 guarded ledger boundary design and tests | Codex implementation and self-check | Yes: direct call committed a synthetic buy above its limit with unrelated price evidence | implementation; verification | Strict quote/fill increment REJECTED; normal evaluator refused correctly in the probe | R, independent GATE during owner-requested work | Derive or verify modeled price from validated quote, canonical order and declared slippage policy inside the transaction | Direct-call counterexample reproduced; correction not started |
| O-63 | Idempotent buy reply derives fill ID and fee from retry values rather than the stored fill | R4 fill receipt linkage and retry verification | Existing ledger branch and Codex self-check | Yes: retry returned a nonexistent evidence key; no duplicate ledger accounting shown | implementation; verification | Strict quote/fill increment REJECTED; do not infer all previous buy accounting failed | R, independent GATE during owner-requested work | Recover authoritative fill ID, price, qty and fee; fail explicitly on missing/conflicting evidence | Changed-price retry reproduced; correction not started |

Counts after O-61/O-62/O-63: 63 omissions; agent unprompted 0; during owner-requested work 55; owner 8.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-64 | First R4 receipt correction also changed profile-off filled-order retry semantics | O-63 correction design | Codex implementation | Yes: ten existing legacy/precedence regressions; no operation | implementation; verification | Corrected source READY_FOR_INDEPENDENT_REVIEW; profile-off behavior restored | R, Codex focused verification during owner-requested work | Apply the authoritative retry behavior only in strict quote mode; keep legacy regression expectations | Initial 538 passed/10 failed; final 548 passed, no legacy test changes |

Counts after O-64: 64 omissions; agent unprompted 0; during owner-requested work 56; owner 8.

O-61 through O-64 dated closeout, 2026-11-04: separate GATE ACCEPTED the bounded source
correction after wrong ticker, direct limit bypass, authoritative retry/conflict and profile-off
checks. Earlier rejected and development results are retained. Full R4 and runtime evidence remain open.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-65 | Export does not verify unique fill/order/receipt association in an archived ledger | R4 export implementation and author tests | Codex implementation and self-check | Yes: modeled cash flow can double-count while reporting complete | implementation; verification | R4 decision/export increment REJECTED; earlier fill correction unaffected | R, independent GATE during owner-requested work | Reject ambiguous associations; do not silently deduplicate or model either member of a conflict | Two counterexamples reproduced; correction not started |
| O-66 | Read-only SQLite open can create WAL/SHM files beside the archived database | R4 export filesystem and operator contract tests | Codex implementation and self-check | Yes: main database bytes were unchanged but archive directory was modified | implementation; verification | R4 decision/export increment REJECTED; no live archive accessed | R, independent GATE during owner-requested work | Require a standalone frozen archive and verify no sidecar creation or ignored committed WAL | Checkpointed WAL-mode reproduction confirmed; correction not started |

Counts after O-65/O-66: 66 omissions; agent unprompted 0; during owner-requested work 58; owner 8.

O-65/O-66 dated closeout, 2026-11-04: separate GATE ACCEPTED the duplicate-association and
standalone-archive corrections after independent invalid/valid input and no-sidecar checks.
The rejection above is preserved as historical evidence; this does not establish archive
provenance, campaign completeness, or actual execution economics.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-67 | Next-step handoff named host/alert verification without distinguishing the older campaign status default or confirming the reviewed Slack test command was present | R4 export closeout before operational handoff | Codex source closeout | Yes: the default probe would not verify Group A and the reviewed delivery command is absent locally; no operation took place | evidence discovery; reporting | Host publisher and alert delivery remain UNVERIFIED; full R4 INCOMPLETE | R, Codex during owner-requested continuation | Resolve actual target, campaign and deployed source, then confirm notification test path before any send | Repository default and local absence verified; actual host path and delivery not checked |

Counts after O-67: 67 omissions; agent unprompted 0; during owner-requested work 59; owner 8.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-68 | Release handoff reported a clean runner three-way merge without a reproducible regular-file conflict check | First host-base overlay rehearsal | Codex author verification/reporting | Yes: clean-rebase claim withdrawn; pinned package still passed bounded host SMA tests | verification; reporting | Exact package ACCEPTED_WITH_RISK, no automatic merge or operation proof | R, independent GATE during owner-requested package review | Materialize both Git blobs and local file, verify merge exit and conflict count, separate smoke tests from textual merge | Four runner conflicts reproduced; test overlap verified clean |

Counts after O-68: 68 omissions; agent unprompted 0; during owner-requested work 60; owner 8.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-69 | Bounded log formatter only redacts the message, leaving exception text and JSON extras | R5 logging design and proof | Codex implementation/self-check | Yes: synthetic secrets persisted; no observed credential exposure | implementation; verification | Opt-in logger REJECTED | R, independent GATE during owner-requested work | Sanitize or omit exception and arbitrary structured data in bounded output | Reproduced; correction not started |
| O-70 | Standard logging error handler can dump raw template arguments when formatting fails | R5 failure-path verification | Codex implementation/self-check | Yes: synthetic secret printed to stderr | implementation; verification | Opt-in logger REJECTED | R, independent GATE during owner-requested work | Use only fixed, secret-free diagnostics on formatting or I/O failure | Reproduced with raiseExceptions enabled; correction not started |
| O-71 | Rollover measures a different formatting call than the payload actually written | R5 byte-cap verification | Codex implementation/self-check | Yes: 682 bytes written under a 512-byte cap | implementation; verification | Opt-in logger REJECTED | R, independent GATE during owner-requested work | Render once and use identical bytes for cap check and emission | Reproduced with stateful string conversion; correction not started |

Counts after O-69/O-70/O-71: 71 omissions; agent unprompted 0; during owner-requested work 63; owner 8.

O-69/O-70/O-71 dated closeout, 2026-11-04: separate GATE ACCEPTED the bounded correction
after prior and corrected probes reproduced. This is source proof only; no actual log
records or secrets inspected and no log destination was enabled.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-72 | Stop-all graph allows a terminal failure hook to be queued after its own stop job finishes | R2 stop-timeout design and static tests | Codex implementation/self-check | Yes: an alert process can start after the group has been stopped | implementation; verification | Offline R2 overlay REJECTED, full R2 INCOMPLETE | R, independent GATE during owner-requested work | Gate hook activation on an active target without starting it; include timeout and queued-failure cases in composed stop rehearsal | Source path inspected; daemon behavior not reproduced |

Counts after O-72: 72 omissions; agent unprompted 0; during owner-requested work 64; owner 8.

O-72 dated closeout, 2026-11-04: separate GATE ACCEPTED the offline source correction.
No daemon reproduction; no guarantee of suppression if stop-all fails and the target
remains active. Retain the composed Linux stop-timeout and normal-alert cases.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-73 | Missing Group A support units are reported but do not prevent accounts starting | R2 account composition design | Codex implementation/self-check | Yes: incomplete release could start without the publisher, watcher, backup or failure sender | implementation; verification | Account composition REJECTED; full R2 INCOMPLETE | R, independent GATE during owner-requested work | Keep partial artifacts non-startable; verify full composition before exposing activation units | Source and v254 Wants semantics checked; no runtime operation |
| O-74 | Clear-environment wrapper itself starts with inherited loader variables | R2 account environment design | Codex implementation/self-check | Yes: loader could act on an inherited value before the wrapper clears it; no host occurrence shown | implementation; verification | Account composition REJECTED; full R2 INCOMPLETE | R, independent GATE during owner-requested work | Filter before the first executable and verify effective environment and loader inputs before any launch | Source and loader documentation checked; no runtime environment inspected |

Counts after O-73/O-74: 74 omissions; agent unprompted 0; during owner-requested work 66; owner 8.

O-73/O-74 dated closeout, 2026-11-04: separate GATE ACCEPTED the corrected offline
draft. Support roles, unit promotion, effective loader inputs and operational
isolation remain unverified; no deployable unit set was produced.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-75 | Group A publisher launcher and offline draft import a state-initializing dependency before validating scope | Publisher boundary design and fresh-process test | Codex implementation/self-check | Yes: synthetic invalid root acquired six state directories despite launch refusal | implementation; verification | Publisher/routing REJECTED; R2/R4 INCOMPLETE | R, independent GATE during owner-requested work | Validate before side-effectful imports; assert absent state stays absent in fresh launcher and renderer processes | Fresh-child counterexample reproduced; correction pending |

Counts after O-75: 75 omissions; agent unprompted 0; during owner-requested work 67; owner 8.

O-75 dated closeout, 2026-11-04: separate GATE ACCEPTED the bounded source
correction. No intended-host path, effective mount or cadence was verified.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-76 | Watcher trusted input-defined equality or formatting before exact account and service attribution | R3 offline input-contract design and tests | Codex implementation/self-check | Yes: synthetic objects impersonated other identities; no live misattribution observed | implementation; verification | Initial watcher scope REJECTED; corrected offline scope ACCEPTED; R3 INCOMPLETE | R, independent GATE during owner-requested work (release formatting confirmed by author) | Require plain roster inputs before comparisons and formatting; preserve future compositor boundary | Three before failures and 44 after passes, independently rechecked |

Counts after O-76: 76 omissions; agent unprompted 0; during owner-requested work 68; owner 8.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-77 | Single-symbol runner's first empty public candle fetch falls through to exit evaluation without a bound price | Runner and Group A outage verification | Codex implementation/self-check | Yes: synthetic runner crashes with telemetry off or on, which can interrupt exit management; no operational incident established | implementation; verification | Runner no-price handling and Group A commissioning INCOMPLETE | R, author during owner-requested telemetry verification | Treat an unpriced turn explicitly; prove first and later empty fetch, held-position management and no stale-price use | Two reproduced strict xfails; treatment pending |

Counts after O-77: 77 omissions; agent unprompted 0; during owner-requested work 69; owner 8.

O-77 dated closeout, 2026-11-04: separate GATE ACCEPTED the offline runner
correction. The reviewer also reproduced warm-up failure on the exact prior
source. No operating incident or commissioning acceptance is claimed.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-78 | Telemetry assumed a completed checkpoint proved uninterrupted failure streak across writer restart | R3 checkpoint failure and restart design | Codex implementation/self-check | Yes: lost record of a successful call produced 10 claimed consecutive failures when actual was one | implementation; verification | Initial restart scope REJECTED; bounded correction ACCEPTED; R3 INCOMPLETE | R, independent GATE during owner-requested work | Treat streak continuity as unknown on new writer; preserve only known 429 evidence across the gap | Exact old/new independently reproduced, six tests passed |

Counts after O-78: 78 omissions; agent unprompted 0; during owner-requested work 70; owner 8.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-79 | New runner status could bind to a prior fetch after symbol mapping failed before transport | R3 observation attribution design | Codex implementation/self-check | Yes: previous quiet evidence was classified as current | implementation; verification | Initial status/candle source REJECTED; runtime R3 INCOMPLETE | R, independent GATE during owner-requested work | Bind only to a sequence advanced during the current turn | Synthetic before/after reproduced |
| O-80 | Candle checkpoint parser accepted duplicate writer or sequence keys | R3 parser and identity tests | Codex implementation/self-check | Yes: an ambiguous checkpoint could satisfy an exact identity match | implementation; verification | Initial status/candle source REJECTED; runtime R3 INCOMPLETE | R, independent GATE during owner-requested work | Reject duplicate keys before consuming checkpoint identity | Synthetic before/after reproduced |

Counts after O-79/O-80: 80 omissions; agent unprompted 0; during owner-requested work 72; owner 8.

O-79/O-80 dated closeout, 2026-11-04: separate GATE ACCEPTED the offline
correction. File attribution is not process liveness; operational R3 is INCOMPLETE.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-81 | Watcher accepted a mismapped quote or classified a malformed tick list as stale | R3 quote adapter and publisher parity | Codex implementation/self-check | Wrong market could look fresh or malformed evidence could look stale | implementation; verification | Initial support adapter REJECTED | R, independent GATE during owner-requested work | Require exact canonical mapping and valid row structure | Before probes reproduced; corrected tests pass locally |
| O-82 | SQLite PRAGMAs did not distinguish an unnamed temporary DB from a memory copy | R3 queue boundary design | Codex implementation/self-check | Disk-backed SQLite could be accepted under a memory-only claim | implementation; verification | Initial support adapter REJECTED | R, independent GATE during owner-requested work | Construct the memory connection inside the copy holder | Before probe reproduced; corrected test passes locally |
| O-83 | Queue row limit did not bound non-meta field bytes | R3 SQLite query boundary tests | Codex implementation/self-check | A 1 MiB ID crossed the adapter's data boundary | implementation; verification | Initial support adapter REJECTED | R, independent GATE during owner-requested work | Bound all SQL projections and aggregate payload bytes | Before probe reproduced; corrected test passes locally |
| O-84 | Inner joins dropped orphan refusal events and returned quiet | R3 queue event completeness tests | Codex implementation/self-check | Inconsistent queue copy suppressed a refusal signal | implementation; verification | Initial support adapter REJECTED | R, independent GATE during owner-requested work | Reject orphan refusal and expiry evidence as unknown | Before probe reproduced; corrected test passes locally |

Counts after O-81 through O-84: 84 omissions; agent unprompted 0; during owner-requested work 76; owner 8.

O-81 through O-84 dated closeout, 2026-11-04: separate GATE ACCEPTED corrected
offline source; no runtime input completeness or alert delivery was verified.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-85 | Denied rollback escaped the watcher cycle and left a borrowed reader in transaction | Producer cleanup and account isolation tests | Codex implementation/self-check | A single failed reader hid other accounts' findings | implementation; verification | Initial producer cycle REJECTED | R, independent GATE during owner-requested work | Mark unusable reader by account, close copy, continue other accounts | Before failed, after passed locally |
| O-86 | Exact queue path did not rule out an immutable SQLite reader ignoring WAL frames | Producer provenance tests | Codex implementation/self-check | Synthetic committed expiry missing from an otherwise successful copy | implementation; verification | Initial producer cycle REJECTED | R, author during owner-requested work | Require WAL-aware reader and retain physical ownership verification | Before failed, after passed locally |

Counts after O-85/O-86: 86 omissions; agent unprompted 0; during owner-requested work 78; owner 8.

O-85/O-86 dated closeout, 2026-11-04: separate GATE ACCEPTED corrected offline
source. Runtime reader acquisition, physical ownership and R3 remain INCOMPLETE.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-87 | Account or queue replacement after copying could mix evidence from different identities | Reader acquisition tests through report composition | Codex implementation/self-check | Retired queue expiry and replacement account status could appear together | implementation; verification | Initial reader acquisition REJECTED; corrected source submitted for review | R, independent GATE during owner-requested work | Revalidate the copied account's data directory, main file and sidecars after all account reads; discard affected account evidence | Two before/after synthetic cases |

Counts after O-87: 87 omissions; agent unprompted 0; during owner-requested work 79; owner 8.

O-87 dated closeout, 2026-11-05: separate GATE ACCEPTED the offline correction
only. Runtime namespace and read-only WAL compatibility remain INCOMPLETE.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-88 | Delivery did not recheck cycle identity after releasing and retaking the writer reservation | Cursor concurrency tests | Codex implementation/self-check | A superseded call could retry a newer finding immediately | implementation; verification | Initial offline cursor REJECTED | R, independent GATE during owner-requested work | Verify exact cycle under send reservation | Before failed, after passed locally |
| O-89 | Delivery treated successful SQL execution as proof that staging and acknowledgement took effect | Cursor storage-failure tests | Codex implementation/self-check | Ignored writes allowed replay, lost staging or falsely confirmed a durable acknowledgement | implementation; verification | Initial offline cursor REJECTED | R, independent GATE during owner-requested work; author added ignored finding insert | Check staging row effects and revision; read back acknowledgement before commit | Three before/after cases locally |

Counts after O-88/O-89: 89 omissions; agent unprompted 0; during owner-requested work 81; owner 8.

O-88/O-89 dated closeout, 2026-11-05: separate GATE ACCEPTED the offline
corrections only. Runtime delivery and owner receipt remain INCOMPLETE.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-90 | Tracked delivery accepted a timestamp earlier than the actual observation | Retained-event provenance tests | Codex implementation/self-check | An alert could be recorded as observed before the queue event occurred | implementation; verification | Initial retained-event source REJECTED | R, independent GATE during owner-requested work | Bind exact producer observation time before staging | Before failed, after passed locally |
| O-91 | Mutable current-state timestamp could move an old journaled expiry across the cutoff | Retained-event cutoff tests | Codex implementation/self-check | Metadata-only update could trigger an expiry notice | implementation; verification | Initial retained-event source REJECTED | R, independent GATE during owner-requested work | Use matching retained buy transition when available; disclose mutable fallback | Before failed, after passed locally |

Counts after O-90/O-91: 91 omissions; agent unprompted 0; during owner-requested work 83; owner 8.

O-90/O-91 dated closeout, 2026-11-05: separate GATE ACCEPTED the offline
corrections only. Mutable fallback and historical coverage remain limited.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-92 | Replacement weekly status was enabled while the original remained enabled, without a successful output test for the replacement | At replacement setup and first manual run | Claude setup/self-check | Both tasks are due in the same slot; neither has a proven repo output, and both can write if their folder bindings work | verification; implementation | Weekly status O-37 remains INCOMPLETE; duplicate recurrence independently observed | R, Codex part-2 audit candidate, confirmed in the Claude app during owner-requested work | Keep one proven recurrence; preserve old run history and verify the expected work-log append after a manual test | Duplicate confirmed; repair not tested |

Counts after O-92: 92 omissions; agent unprompted 0; during owner-requested work 84; owner 8.

O-37/O-92 dated follow-up, 2026-11-05T03:08:10Z: original weekly status is paused
with history retained. The replacement is the only active copy and passed one
manual report/output test after the owner-authorized repo grant. The manual
report describes the historical duplicate but is not current scheduler evidence.
November 9 unattended output remains UNVERIFIED.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-93 | A short HTTP read could treat a truncated Slack response as a complete acknowledgement | Sender acknowledgement boundary tests | Codex implementation/self-check | Could clear a pending alert without a proven acknowledgement | implementation; verification | Initial offline Slack sender REJECTED | R, independent GATE during owner-requested work | Require single exact response length and the entire expected body; reject unsupported framing | Five before/after real-parser cases locally |

Counts after O-93: 93 omissions; agent unprompted 0; during owner-requested work 85; owner 8.

O-93 dated closeout, 2026-11-05: separate GATE ACCEPTED the offline correction
only. Actual Slack acknowledgement framing and owner receipt remain UNVERIFIED.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-94 | Cursor precheck did not constrain SQLite's later pathname open | Watcher runtime path tests | Codex implementation/self-check | A synthetic late symlink redirected writes outside the checked cursor directory | implementation; verification | Initial runtime composition REJECTED; watcher fails closed; protected opener INCOMPLETE | R, independent GATE during owner-requested work | Do not open until actual main/journal access is bounded by a reviewed design | Refusal regression passed locally; secure open not implemented |
| O-95 | Read-only credential directory did not prove the opened credential was read-only | Credential mount tests | Codex implementation/self-check | A writable file submount could reach the sender | implementation; verification | Initial runtime composition REJECTED | R, independent GATE during owner-requested work | Verify the opened descriptor's mount before reading | Before failed, after passed locally |

Counts after O-94/O-95: 95 omissions; agent unprompted 0; during owner-requested work 87; owner 8.

O-94/O-95 follow-up, 2026-11-05: independent GATE ACCEPTED containment and
credential validation only. O-94's protected cursor open remains INCOMPLETE.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-96 | Serialized cursor loader accepted missing tables and filtered out a reserved-name trigger | Protected cursor schema tests | Codex implementation/self-check | Could initialize unsupported state or suppress a pending alert without sending | implementation; verification | Initial cursor-image source REJECTED | R, independent GATE during owner-requested work | Require exact full persisted schema from shared definitions; only explicit seed initializes | Three before/after schema cases locally |

Counts after O-96: 96 omissions; agent unprompted 0; during owner-requested work 88; owner 8.

O-94/O-96 source follow-up, 2026-11-05: independent GATE ACCEPTED the bounded
offline schema correction; intended-host proof and commissioning remain INCOMPLETE.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-97 | Specific scout wallet-label rules and their claimed adoption remained in a private research artifact, absent from the inspected canonical brief/instructions | Scout triage handoff, October 22/27 | Claude handoff; exact private adoption unverified | Codex cannot establish the operative wording or adoption from the canonical files | evidence discovery; reporting | U-27/U-28 visibility gap SHOWN; private decision history UNVERIFIED | R, Codex during owner-requested handoff audit; Claude also self-reported it | Attach the existing source, reconcile proposed rules before relying on them | Absence searched; import/adoption not performed |
| O-98 | On-chain summary generalized directional-flow nulls to a historical-data impossibility, transferred HHI findings to holder percentages, and omitted the cited BTC experiment's exposure/loss comparison | November 5 on-chain handoff source review | Claude source synthesis/self-check | Could reject an untested risk-screen hypothesis or exaggerate what concentration data establishes | research method; reporting | ONCHAIN-1 remains UNTESTED, not rejected; categorical and metric claims qualified in dated audit | R, Codex during owner-requested audit | Match hypothesis, metric, population, timing and exposure baseline to each source; report material contrary evidence | Primary source comparisons performed; no empirical replication |
| O-99 | Undecided inventory described mixed completed/held/overlapping work as uniformly untested and nonduplicative | November 5 inventory handoff | Claude table/self-check | Could inflate missing-work counts and owner decisions; no queue change established | reporting; verification | Intro qualified by dated addendum; 49 rows retained, decisions unchanged | R, Codex during owner-requested audit | Check each row against its status and existing queue dependencies before totals | All 49 rows read; every underlying private source not verified |

Counts after O-97 through O-99: 99 omissions; agent unprompted 0; during owner-requested work 91; owner 8.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-100 | Initial cadence design did not reconcile the existing sender's small input limit, child ownership after parent death, or independent health/old-pending delivery at upstream limits | R3 cadence design before implementation | Codex design/self-check | Design could not support bounded summary delivery or claim backlog protection; no runtime change occurred | implementation; verification | Original design INCOMPLETE; revised design accepted with risk only | R, independent Bohr review during owner-requested continuation | Cross-review exact sender, source limits and process lifetime before code; keep old pending separate from failed new staging | Source comparison and local byte calculation; Linux implementation not tested |
| O-101 | Revised health result/suppression grouped by code, omitting affected-account identity and known-clear versus unknown evidence | R3 revised design before implementation | Codex design/self-check | Acknowledgement for A could hide B or fail to rearm after recovery; no running behavior changed | implementation; verification | Corrected 21-key tri-state generation contract independently accepted with risk for design | R, independent Bohr review during owner-requested continuation | Fixed per-scope masks, exact acknowledged subset, explicit recovery/unknown states | 16 local reference checks including transition/encoding; no production controller exercised |

Counts after O-100/O-101: 101 omissions; agent unprompted 0; during owner-requested work 93; owner 8.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-102 | Initial summary validation reused the stored-event cap before reaching old-pending fallback, and inspected stored finding times before rejecting a stale cycle | R3 summary implementation before handoff | Codex implementation/self-check | Capacity path could strand old pending; stale input could be misreported as corrupt storage and send health | implementation; verification | Corrected candidate READY_FOR_INDEPENDENT_REVIEW; no runtime affected | R, Codex targeted tests during owner-requested implementation | Separate bounded incoming producer limit from retained-event limit; reject cycle identity/time before inspecting time-relative pending rows | Both failing development tests now pass; consolidated 210 pass/1 Linux skip; paired legacy/new overflow probe |

Counts after O-102: 102 omissions; agent unprompted 0; during owner-requested work 94; owner 8.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-103 | Final identity check changed health but retained report findings and event IDs from the replaced account/queue | R3 composition-to-delivery tests | Codex implementation/self-check | Could send and acknowledge retired evidence beside an unavailable-source warning | implementation; verification | Initial integrated source REJECTED; corrected candidate awaits diff-only review | R, independent Bohr GATE during owner-requested work | One final identity verdict filters findings, unknowns, queue events and health together, preserving unaffected accounts | Account/queue replacement tests fail before and pass after |
| O-104 | Nonfatal summary POST failures continued planned cadence without a sanitized local diagnostic | R3 supervisor failure reporting tests | Codex implementation/self-check | A running supervisor could silently repeat failed delivery attempts | implementation; reporting | Initial integrated source REJECTED; corrected candidate awaits diff-only review | R, author self-review concern independently confirmed by Bohr during owner-requested work | Emit one fixed diagnostic per unconfirmed planned cycle, without payload or hidden retries | Two-cycle diagnostic test fails before and passes after |
| O-105 | CP-14 said the runner checks exposure limits before entries without tracing whether those limits can block; no position row carries `exposure_pct` or `notional_pct`, so per-symbol, total and strategy exposure are always 0 | Capital-protection audit stage 1, 2026-10-31 | Claude | Overstated position protection on the runner path; no recorded decision rested on it | verification (call site read, data flow not traced) | CP-14 (dated correction 2026-11-05) | R, Claude during research item 1 (BA-24) | A limit counts as enforced only after each input it reads is traced to a writer | No |
| O-106 | The exit-parity audit, scoped to what the runner actually trades including entries, missed that the runner adds up to 2 full-size entries to winning positions and resets their exit references; its replays and `scripts/replay_runner_decisions.py` model one entry per position | Exit-parity audit, 2026-10-31 | Claude | Runner-versus-replay comparisons will differ when adds occur; not yet used for a decision | scope (exits traced, entry branches not enumerated) | exit_parity_audit_20261031 (dated correction 2026-11-05) | R, Claude during research item 1 (BA-23) | Enumerate every order-emitting branch of the runner before describing what it trades | No |

Counts after O-103/O-104: 104 omissions; agent unprompted 0; during owner-requested work 96; owner 8.
Counts after O-105/O-106 (Claude 2026-11-05): 106 omissions; agent unprompted 0; during owner-requested work 98; owner 8.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-107 | BA-23 and the O-106 correction omitted the upstream default position-aware guard while claiming that the runner adds to held winners | 2026-11-05 scaling-path audit and exit-parity correction | Claude | Presented an unnecessary simulation disable-adds/model-adds choice as required; no simulation change observed | verification; reporting | BA-23/O-106 qualified: default guard blocks adds, conditional scaling bugs remain; runtime mode UNVERIFIED | R, Codex independent audit during owner-requested work | Trace order selection before downstream sizing; distinguish source defaults from runtime mode | Six real shared-decision probes and one disabled-scaling probe passed |
| O-108 | BA-35 generalized non-finite rejection into an assurance that archived data cannot contain invalid/zero prices, and called same-close fill bias merely slight without measurement | 2026-11-05 backtest audit | Claude | Overstated reliability of archived backtest execution/valuation; no result recomputed | verification; research method; reporting | BA-35 corrected; historical tradability and size of bias remain UNVERIFIED | R, Codex independent audit during owner-requested work | Probe finite zero/negative prices and distinguish idealized fills from measured execution bias | Two finite-price preservation/NaN rejection probes passed |
| O-109 | Handoff treated incomplete static coverage as assurance that remaining modules are off the paper order path, and stale ES files as proof the campaign stopped | 2026-11-05 audit coverage and operational report | Claude | Could justify premature audit closure or an unnecessary restart; neither done here | verification; reporting | Whole-bot coverage and current ES operation remain INCOMPLETE/UNVERIFIED | R, Codex independent audit during owner-requested work | Identify per-file review coverage; require current runtime evidence for liveness claims | CSV/source counterexample checked; no runtime inspection |

Counts after O-107/O-109 (Codex 2026-11-05): 109 omissions; agent unprompted 0; during owner-requested work 101; owner 8.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-110 | Initial host signature wrapper interpolated away the child argument list and emitted zero status markers without running the intended checks | Before the first host verification wrapper invocation | Codex | Could have falsely certified executable signatures from a no-op; result was discarded before relying on it | implementation; verification | Initial wrapper invalid; actual host result SHOWN only by corrected command output | R, Codex during owner-requested work | Smoke-test argument forwarding with known output; require per-command evidence, not an outer exit code | Interpolation reproduced; corrected printf smoke and actual three host verification outputs checked |

Counts after O-110 (Codex 2026-11-05): 110 omissions; agent unprompted 0; during owner-requested work 102; owner 8.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-111 | Initial SSH diagnostics used LogLevel ERROR, which can hide the INFO-level Tailscale check banner, leaving a silent 255 failure | Before interpreting the first silent host preflight | Codex | Delayed recognizing an access check; earlier exact cause remains unproven, no host conclusion accepted | verification; reporting | Intended-host proof INCOMPLETE; local route/session were not established as broken | R, Codex source investigation during owner-requested work | Keep authentication banner visible with bounded, secret-redacted diagnostics | Native later VERBOSE output and first-party issue checked; no controlled same-challenge replay |
| O-112 | Asked owner to approve an SSH URL only after its connection exited, then started a fresh connection rather than preserving a live approval handoff | First additional SSH-check handoff in November 10 preflight work | Codex | Repeated owner approval did not produce inventory; caused rework without proving owner/auth/host fault | implementation; verification; reporting | Host preflight INCOMPLETE; live handoff proposal awaiting owner window approval | R, Codex after the owner-confirmed retry still requested a check | Surface URL only while same bounded SSH process is alive; continue that process after approval, never silently replace it | Not yet live-tested; existing tool ordering and upstream connection behavior checked |

Counts after O-111/O-112 (Codex 2026-11-11 UTC): 112 omissions; agent unprompted 0; during owner-requested work 104; owner 8.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-113 | Live approval revision changed ConnectTimeout but retained a five-second alive-interval/count packet timeout | Before promising/executing the five-minute live SSH handoff | Codex | Owner-confirmed same-session attempt still timed out without inventory; exact installed internal exit not instrumented | implementation; verification | SSH preflight INCOMPLETE; corrected invocation READY_FOR_INDEPENDENT_REVIEW | R, Codex after owner confirmation and same-session failure | Inspect all effective client deadlines with ssh -G; remove short alive packet deadline while preserving outer bound and security; use tested argv builder | Actual old effective config rejected/new accepted and five scope/security mutations refused, 7 offline tests; no live proof yet |

Counts after O-113 (Codex 2026-11-11 UTC): 113 omissions; agent unprompted 0; during owner-requested work 105; owner 8.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-114 | First integration draft could reap the SSH leader before its final group signal; initial deadline cleanup also lost evidence of a concurrent watchdog kill | SSH wrapper failure-matrix/ownership design before implementation | Codex | Could target a reused PGID or falsely mark cleanup unknown; only local synthetic drafts ran, no host connection or accepted runtime claim | implementation; verification | Initial draft not accepted; corrected offline integration READY_FOR_INDEPENDENT_REVIEW; host/R3 INCOMPLETE | R, Rawls plan review plus Codex synthetic tests during owner-requested work | Non-reaping kqueue/WNOWAIT fence; disable all group signals before reap; retain watchdog send evidence; fixed absolute cleanup reserve |40 integration tests pass with host permissions, including forbidden-poll/wait-order, dead leader/retained pipes, timeout and cleanup uncertainty; not live host proof |

Counts after O-114 (Codex2026-11-11 UTC):114 omissions; agent unprompted0; during owner-requested work106; owner8. No accepted-work rework increment: this draft was corrected before acceptance.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-115 | Interrupt matrix covered handoff/work but not first SIGINT during cleanup after watchdog cancellation | Integrated SSH wrapper cancellation tests before independent GATE | Codex | Could bypass group signalling, leader reap and final bookkeeping; first frozen candidate REJECTED, no host run occurred | implementation; verification | Initial68-pass candidate REJECTED; corrected integration READY_FOR_INDEPENDENT_REVIEW; live/R3 INCOMPLETE | R, independent Rawls GATE during owner-requested work | Record-only SIGINT handler installed before spawn, cancellation checkpoints during work, deferral through cleanup, prior handler restoration | Two real SIGINT regressions fail before/pass after, one with closed-stdio descendant; final70 focused passes with host permissions |

Counts after O-115 (Codex2026-11-11 UTC):115 omissions; agent unprompted0; during owner-requested work107; owner8. Rejected-before-acceptance work does not increment accepted-work rework.

| ID | Omission | When it should have been found | Who missed it | Decision or result impact | Cause class | Affected conclusions and status | How found | Prevention control | Tested? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-116 | Initial clean-tree selection omitted baseline core, saved strategy/exit before-fixtures and static legacy systemd test assets needed by the expanded selection | Local candidate dependency/test-asset composition before its first rehearsal | Codex |33 failures in v1; no release or operational acceptance; additional local rework | implementation; verification | v1 INCOMPLETE; dependencies added without altering existing source/test expectations | R, Codex composed-tree tests during owner-requested work | Treat runtime imports and test assets as separate manifest requirements; pin all before-fixtures through existing hash manifest; retain required public baseline assets | Original33 fail; corrected focused33 pass; final v3 selected1616 pass/1 Linux skip |
| O-117 | Queue test fixture used a transaction context without closing its WAL writer before the physical-byte baseline | Snapshot read-only verification fixture design before the earlier accepted package | Codex |GC could checkpoint before the reader and falsely fail physical preservation; fullv2 one failure, no operating DB incident | implementation; verification | Earlier test stability narrowed, not production read-only mode contradicted; fixture correction READY_FOR_INDEPENDENT_REVIEW | R, Codex full rehearsal and controlled GC probe during owner-requested work | Explicit fixture writer close before baseline, same original assertions, new closed-writer regression | Controlled old failure occurs before reader, close control passes; regression fails before/pass after; module63 pass; final selected1616 pass/1 skip |

Counts after O-116/O-117 (Codex2026-11-11 UTC):117 omissions; agent unprompted0; during owner-requested work109; owner8. O-116 was corrected before acceptance; O-117 corrects a previously accepted verification fixture, not trading logic.

O-116/O-117 follow-up2026-11-11T13:40:45Z: exact v3 paper-source composition
and fixture-only correction independently ACCEPTED_WITH_RISK. Reviewer
reproduced causal control and13 focused passes; author consolidated1616 pass/
1 explicit Linux skip inspected, not independently rerun. No operational claim.

| ID | What was omitted | When it should have been found | Missed by | Decision/result effect | Cause class | Affected conclusions/status | How found | Recurrence control | Tested |
|---|---|---|---|---|---|---|---|---|---|
| O-118 | Supplemental capture deadline initially allowed the inherited collector to reset/cancel it; later draft disabled the timer before final output | Compatibility capture failure matrix before source GATE on2026-11-11 | Codex | Both drafts corrected before connection/acceptance; no target timeout observed | implementation; verification | Initial deadline proof REJECTED; corrected source ACCEPTED_WITH_RISK, not a guarantee against kernel-uninterruptible I/O | R, separate Rawls review during owner-requested work | One absolute timer through collector reset/cancel and final output/process exit | Local reset/cancel, expired-budget and blocked-emitter regressions; final41 independent passes |
| O-119 | Proposed-user absence branch used dictionary equality, accepting numeric0 as Boolean false | Compatibility projection typed-schema tests before source GATE on2026-11-11 | Codex | Rejected before live capture; no malformed host absence recorded | implementation; verification | Initial projection REJECTED; corrected exact-Boolean branch ACCEPTED_WITH_RISK | R, separate Rawls review during owner-requested work | Require Boolean identity, not numeric equality, at metadata boundaries | Reviewer reproduced0 acceptance; numeric-presence regression and final41 independent passes |
| O-120 | Compatibility projection discarded safe exit/truncation details along with unrestricted text for an unavailable unit-collision query | Designing diagnosable failure receipts before the2026-11-11 capture | Codex | Captured44-unit collision remains UNKNOWN; exact failure stage/cause cannot be reconstructed, no namespace clearance accepted | verification; reporting | Retained facts ACCEPTED_WITH_RISK; collision/complete compatibility INCOMPLETE | R, Codex actual-receipt inspection during owner-requested work | If another bounded read is authorized, retain whitelisted status/exit/truncation/refusal codes without raw secrets; unavailable is not absent | Existing truncation/unknown refusal tested; retained diagnostic-code enhancement not implemented or tested |

Counts after O-118/O-120 (Codex2026-11-11 UTC):120 omissions; agent
unprompted0; during owner-requested work112; owner8. O-118/O-119 were
corrected before acceptance; no accepted-work rework increment. O-120 does
not invalidate the retained values or justify an automatic second connection.

| ID | What was omitted | When it should have been found | Missed by | Decision/result effect | Cause class | Affected conclusions/status | How found | Recurrence control | Tested |
|---|---|---|---|---|---|---|---|---|---|
| O-121 | Initial bundle writer used recursive mkdir(mode0700), which does not apply that mode to all intermediate parents | New local backup writer before first source verification2026-11-11 | Codex | Eight initial fixture failures shared this cause; no deployment or accepted backup claim, outer bundle remained0700 | implementation; verification | Initial local core INCOMPLETE; fixed per-component private creation pending independent source review | R, Codex targeted tests during owner-requested work | Create/check each parent with0700, do not broaden existing modes | Initial failures retained in work-log evidence; round-trip and every-directory-private regression pass |
| O-122 | Initial completion path synced files and root but not all newly created nested directories before the manifest | Local bundle durability/failure matrix before independent source GATE2026-11-11 | Codex | Could overstate completion durability after a crash; corrected before source review or any operating backup | implementation; verification | Initial publication design superseded; corrected local-only content/durability distinction pending independent review | R, Codex pre-handoff source review during owner-requested work | Sync nested directory entries deepest-first before manifest, then final root/parent; retain late failure as uncertain | Ordering/private-directory test and injected pre/post-manifest fsync failures pass; actual power-failure recovery not tested |

Counts after O-121/O-122 (Codex2026-11-11 UTC):122 omissions; agent
unprompted0; during owner-requested work114; owner8. Both corrected before
acceptance; accepted-work rework stays6. No actual operating backup/data loss.

| ID | What was omitted | When it should have been found | Missed by | Decision/result effect | Cause class | Affected conclusions/status | How found | Recurrence control | Tested |
|---|---|---|---|---|---|---|---|---|---|
| O-123 | Verification lacked a final deadline check after the last metadata read/validation | Local bundle deadline matrix before initial source GATE2026-11-11 | Codex | Could return local_verified after cooperative deadline expiry; independent GATE rejected initial source before acceptance, no operating backup affected | implementation; verification | Initial source REJECTED pending correction; one final budget check added, diff-only review pending | R, separate Rawls reviewer during owner-requested work | Check deadline immediately before verified receipt, not only during hashing/iteration | Corrected last-entry deterministic-clock regression fails before fix and passes after;123 focused tests pass, hard I/O interruption not claimed |

Counts after O-123 (Codex2026-11-11T22:28:08Z):123 omissions; agent
unprompted0; during owner-requested work115; owner8. Corrected before
acceptance; accepted-work rework stays6. No operating-data incident.

O-121/O-123 follow-up2026-11-11T22:28:43Z:separate Rawls GATE accepted the
corrected local core WITH_RISK; pending statuses in the historical rows above
are superseded for source only. O-123 independently reproduced failing before
and passing after. O-121/O-122 regressions were in the independent initial
122-case run. Physical power-failure recovery and operating R3/R10 remain
unverified; no operating backup was deployed or modified.

| ID | What was omitted | When it should have been found | Missed by | Decision/result effect | Cause class | Affected conclusions/status | How found | Recurrence control | Tested |
|---|---|---|---|---|---|---|---|---|---|
| O-124 | Automatic acquisition treated generic artifact extensions as producer authorization, permitting unrecognized config.json with an api_token field | Nine-account source-acquisition design/first source GATE2026-11-11 | Codex | Could copy credential-bearing JSON despite correct bundle hashes; initial source REJECTED before acceptance, synthetic probe only | implementation; verification | Initial auto-selection safety claim superseded; closed producer-path guard implemented, diff-only review pending; no real credential access or operating backup | R, separate Rawls GATE independently reproduced after author flagged possibility during pending review | Closed producer artifact/directory allowlist before payload/scratch reads; unknown paths refuse, never silently skipped | Four refusal regressions fail before fix and pass afterward; corrected155-case focused run passes, trusted producers still require source provenance |

Counts after O-124 (Codex2026-11-11 UTC):124 omissions; agent
unprompted0; during owner-requested work116; owner8. Corrected before
acceptance; accepted-work rework stays6. No operating credential/data event.

O-124 follow-up2026-11-11T23:32:57Z:separate Rawls diff-only GATE accepted
corrected declared/quiescent acquisition WITH_RISK. Four refusal regressions
independently fail before the guard and pass after, plus actual-producer
fresh-restore/replay check. Path authorization is not content secret clearance;
trusted producers/provenance remain assumptions. Initial rejected source and
failed fixture run are preserved; R3/R10 operating status stays INCOMPLETE.

| ID | What was omitted | When it should have been found | Missed by | Decision/result effect | Cause class | Affected conclusions/status | How found | Recurrence control | Tested |
|---|---|---|---|---|---|---|---|---|---|
| O-125 | Reused process executor spawned before entering its cleanup region, permitting cancellation immediately after spawn to leave a child | New backup download CLI integration2026-11-12; earlier executor review scope not re-audited | Codex | Independent synthetic SIGINT probe left a child, reviewer cleaned/reaped it; new CLI REJECTED and downloads held, no native client/account operation | implementation; verification | Initial new CLI ownership claim withdrawn; dedicated gated/masked backup adapter implemented, separate review pending; older caller impact UNVERIFIED/parked | R, independent Rawls GATE during owner-requested work | Block cancellation across fork/registration, child READY/GO gate, cleanup scope before fork | Real SIGINT/SIGTERM-after-fork regressions pass in corrected49-test slice; source GATE pending |
| O-126 | Reused process executor reaped/joined leader before signalling its process group, removing the PID-reuse ownership fence | New backup CLI ownership design2026-11-12 | Codex | Could misdirect a group signal after PID reuse; no misdirected signal observed, initial CLI rejected before downloads | implementation; verification | New adapter uses live unreaped leader until group signalling is disabled; older helper unchanged and its prior acceptance impact unresolved | R, independent Rawls GATE during owner-requested work | Retain gated live leader, signal only while fenced, reap only after signalling ends | Real normal/timeout workers and recorded signal-before-wait order pass; separate source review pending |
| O-127 | Attributed an owned-group EPERM test failure to the app sandbox before cross-environment evidence established its cause | First corrected worker test2026-11-12 | Codex | One escalated synthetic rerun still failed EPERM; sandbox-only explanation withdrawn, no policy/login change or real client operation | reporting; verification | Environment-cause claim contradicted; exact kernel cause UNVERIFIED; live-leader hold resolves observed failure | R, Codex diagnostic rerun during owner-requested work | Separate observed errno from causal explanation; retain failed/default and escalated results before asserting cause | Both environments showed EPERM, corrected leader-hold tests pass; automated causal-diagnosis prevention not claimed |

Counts after O-125/O-127 (Codex2026-11-12 UTC):127 omissions;
agent-unprompted0; during owner-requested work119; owner8. New adapter
corrections are before acceptance. Recorded accepted-work rework stays6;
whether older executor callers add historical rework remains UNVERIFIED,
not declared unaffected. No actual archive download/native client execution
or account/service/trading incident has occurred in this preparation stage.

| ID | What was omitted | When it should have been found | Missed by | Decision/result effect | Cause class | Affected conclusions/status | How found | Recurrence control | Tested |
|---|---|---|---|---|---|---|---|---|---|
| O-128 | New ownership-fence executor did not reject ignored/custom SIGCHLD handlers that can reap its leader | Backup executor entry-context design2026-11-12 | Codex | Independent SIGCHLD=SIG_IGN probe forked then raised ChildProcessError; no PID reuse/misdirected signal observed; transfer held | implementation; verification | Initial new executor rejected; explicit pre-fork default-SIGCHLD guard independently accepted WITH_RISK04:26:39UTC | R, Rawls GATE confirmed after author flagged possible precondition during pending review | Reject ignored/custom SIGCHLD dispositions before mask/pipe/fork work | Both regressions fail before guard, pass after; reviewer independently12process tests pass, retained51-case XML verified |

Counts after O-128 (Codex2026-11-12 UTC):128 omissions;
agent-unprompted0; during owner-requested work120; owner8. New executor
corrections predate acceptance. Earlier-callers rework impact still unresolved;
recorded accepted-work rework stays6, not a claim that older callers are safe.
O-125/O-126 new backup-adapter corrections independently accepted WITH_RISK
04:26:39UTC; original companion helper/callers remain unchanged and parked.
One approved download subsequently completed; no downloaded client executed.

| ID | What was omitted | When it should have been found | Missed by | Decision/result effect | Cause class | Affected conclusions/status | How found | Recurrence control | Tested |
|---|---|---|---|---|---|---|---|---|---|
| O-129 | Native-test parent verified tools before giving the worker a fresh300second budget | Native controller deadline design2026-11-12 | Codex | Synthetic9second preparation allowed309seconds total; exhausted preparation still started work; no native program ran | implementation; verification | Initial native source REJECTED; shared-deadline correction independently ACCEPTED_WITH_RISK04:40:50UTC; actual native proof INCOMPLETE | R, independent Rawls GATE during owner-requested work | One absolute deadline before parent preparation; first worker phase verifies tools; exhausted budget starts no worker | Both9/301second clock regressions independently fail before/pass after;21policy tests pass |

Counts after O-129 (Codex2026-11-12 UTC):129 omissions;
agent-unprompted0; during owner-requested work121; owner8. This correction
predates source acceptance; recorded accepted-work rework remains6. Older
companion caller impact is still UNVERIFIED, not declared unaffected.

| ID | What was omitted | When it should have been found | Missed by | Decision/result effect | Cause class | Affected conclusions/status | How found | Recurrence control | Tested |
|---|---|---|---|---|---|---|---|---|---|
| O-130 | Native CLI accepted a relative pins argument but verify_tools required an absolute canonical path; synthetic tests used absolute paths | Native invocation integration before04:48UTC attempt | Codex; source review | One attempt refused verify_inputs before sandbox/clients; no encrypted backup produced | implementation; verification | Native operational readiness INCOMPLETE; R10 stopped by owner, no repair/retry | R, Codex actual attempt and read-only verification during owner-requested work | Before resuming, reconcile CLI path contract and regression-test the actual invocation; no extra controller | Actual invocation and read-only verifier both refuse; correction not implemented/tested |

Counts after O-130:130 omissions;0agent-unprompted/122during owner-requested
work/8owner. Accepted-work rework7 includes native source-readiness correction;
older companion caller impact remains unresolved. R10 is on hold by owner.

| ID | What was omitted | When it should have been found | Missed by | Decision/result effect | Cause class | Affected conclusions/status | How found | Recurrence control | Tested |
|---|---|---|---|---|---|---|---|---|---|
| O-131 | Five-commit pre-push handoff did not compare the actual branch tracking ref, omitting14older unpublished ancestors | Preservation pre-push scope assessment2026-11-12 | Codex grouping/handoff | Could imply only5commits would leave laptop; cached branch comparison instead shows19, older14not content-reviewed in this pass; no push occurred | verification; reporting | Five-commit preservation review ACCEPTED_WITH_RISK; full outgoing scope/privacy still unverified | R, Claude pre-push review during owner-requested work, then Codex local Git verification | Compare intended review base and actual upstream range/counts before describing push scope; disclose partial older-content review | Current cached ref0behind/19ahead,14older commits/20files independently confirmed; no live remote or push test |

Counts after O-131:131 omissions;0agent-unprompted/123during owner-requested
work/8owner. Recorded accepted-work rework remains7; this scope correction
preceded push approval and did not reopen source acceptance. Remote state is
not inferred from cached refs. Earlier companion caller impact unresolved.

| ID | What was omitted | When it should have been found | Missed by | Decision/result effect | Cause class | Affected conclusions/status | How found | Recurrence control | Tested |
|---|---|---|---|---|---|---|---|---|---|
| O-132 | Privacy framing carried31Oct PRIVATE forward but omitted the1Nov PUBLIC observation already in base commit82b5f216e | Current pre-push evidence reconciliation2026-11-12 | Claude pre-push review; Codex handoff | Could imply current PUBLIC is a new unexplained change or a newly invented requirement; no visibility mutation/push occurred | evidence discovery; reporting | Current GitHub PUBLIC independently shown; historical31Octprivate remains dated; publication intention unresolved, not guessed | R, Codex live prerequisite query followed by targeted work-log search during owner-requested work | Reconcile newest already-recorded visibility with live metadata and owner intent; separate setting observation from authorization/actor attribution | Live GH API PUBLIC and1Nov12:42:48log inspected; no setting changed and no guarantee against future stale reporting |

Counts after O-132:132 omissions;0agent-unprompted/124during owner-requested
work/8owner. Recorded accepted-work rework remains7; current publication
decision is pending, no prior source acceptance or live state was changed.

| ID | What was omitted | When it should have been found | Missed by | Decision/result effect | Cause class | Affected conclusions/status | How found | Recurrence control | Tested |
|---|---|---|---|---|---|---|---|---|---|
| O-133 | Authorized push did not reuse the31Oct documented HTTP400 transport correction before invoking default Git HTTP transport | Earlier-work search before12:24UTC push2026-11-12 | Codex | One push failed HTTP400; remote verified unchanged, no publication applied; unnecessary failed attempt and delay | evidence discovery; implementation | Push objective INCOMPLETE, source/review acceptance unchanged | R, Codex targeted work-log search after actual failure during owner-authorized push | Search prior exact publication failures/working command before execution; verify actual remote after disconnect before retry |31Oct successful settings found; current remote unchanged verified; corrected retry not yet run |

Counts after O-133:133 omissions;0agent-unprompted/125during owner-requested
work/8owner. Recorded accepted-work rework remains7; no source acceptance was
reopened and no publication succeeded. Corrected transport requires extending
the recorded one-attempt budget, not new code or authentication changes.

| ID | What was omitted | When it should have been found | Missed by | Decision/result effect | Cause class | Affected conclusions/status | How found | Recurrence control | Tested |
|---|---|---|---|---|---|---|---|---|---|
| O-134 | Four known zero-job Actions failures remained without an exact workflow-validation cause or repair proposal;18invalid secrets-in-if conditions now confirmed | Earlier workflow-validity acceptance/failed-run diagnosis; original introduction date unknown;1NovO24already recorded0jobs | Historical workflow authors/reviewers UNVERIFIED; subsequent diagnostic follow-up gap | Prevents4release/build/signing pipelines from starting; not a new19commit regression or evidence of failing trading tests | implementation; verification; failure diagnosis | Push preservation remains complete; fullCI notgreen; workflow repair unstarted | R, Codex existing-check follow-through during owner-requested next steps | Validate workflow expressions before release acceptance; inspect actual startup annotations and distinguish0jobs from test execution | GitHub annotations for all4and unchanged-file diff confirmed; proposed repair/validator tests not run |

Counts after O-134:134 omissions;0agent-unprompted/126during owner-requested
work/8owner. Recorded accepted-work rework remains7; no full CI green claim
was accepted/reopened. Source defect is inherited, not introduced by this push.

O-114/O-115 follow-up2026-11-11T11:21:33Z: corrected offline wrapper
ACCEPTED_WITH_RISK by separate Rawls GATE after diff-only review. Reviewer
independently reran the two cleanup-SIGINT regressions; author consolidated
70-test result remains self-checked. No host connection; R3 INCOMPLETE.

O-103/O-104 follow-up, 2026-11-05T11:54:06Z: independent GATE accepted both
corrections and the integrated offline source WITH_RISK. Three before/after
regressions and both reviewer probes pass. Native Linux behavior and real
delivery remain unverified; this does not close R3 or authorize operations.

O-01/O-02 also qualify the later "no review ever checked research against the bot" claim: earlier runner-rule studies
exist; incomplete parity and failure to carry findings forward are not total absence of earlier checks. O-04/O-10/O-11
cover the renewed default-config/safety/cap overstatements. O-23's nightly-build causal implication is superseded by
O-24; it is preserved as an incident record, not a current explanation or verified billing state.

Historical counts 2026-11-01: 24 omissions found since the register began (O-01 to O-24): caught by an agent unprompted 0; during
owner-requested work 16; by the owner 8. Historical H-01 to H-07 (`omission_history_20261031/`): found by agent review 3,
during owner-requested work 1, not recorded 3.
Rework 2026-10-31 (accepted or closed work later corrected): 4 - failure diagnosis (closed 2026-10-30; C1-C4),
25-symbol analysis (closed 2026-10-30; recommendation qualified), multisymbol baseline (2026-10-08; relabelled
signal-only), ED-002 design (reviewed 2026-10-27; exit scope reopened).
Rework update 2026-11-03: 5, adding the accepted paper-simulation specification's cooldown-time interpretation
(O-40); code thresholds unchanged. O-38/O-39 implementation defects were rejected before acceptance, not added here.
Rework update2026-11-11:6, adding the accepted snapshot verification fixture's
WAL-writer lifetime correction (O-117). Existing assertions and production
reader remain unchanged; earlier physical-byte proof needs the stable fixture.

## Open caveats (owner-approved 2026-10-31; each line stays until closed with evidence; new work is checked against it)
- C-01 Research results mostly do not describe the bot: 30 of 42 are STANDALONE, 5 SIGNAL_ONLY (`result_labels_20261031/`).
- C-02 The BTC/ETH candidate has no implementation in the bot (name search, 2026-10-31).
- C-03 Dated correction 2026-11-03: the historical last-symbol-only source defect (D-1) is repaired with separate
  source GATE ACCEPTED (engineering item 1). Deployment/current host operation and consumer recovery are not
  established; round-robin cadence and separate lifecycle/risk dependencies remain. Evidence:
  `docs/review_artifacts/multisymbol_runner_repair_20261103/`.
- C-04 Exits are blocked by entry limits and never retried (CP-09; `place_order.py`, live consumer, `check_live`).
- C-05 Portfolio position cap not enforced; `check_live` ignores its position-notional limit (CP-14, H-06; engineering item 3).
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

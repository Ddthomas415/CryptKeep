# Claude Cowork handoff to Codex, 2026-10-21 to 2026-10-24

Prepared 2026-10-24 after the operator asked whether Codex had been told about this work. As of 02:27Z no Codex
work-log entry or `REMAINING_TASKS.md` line refers to any item below (`REMAINING_TASKS.md` cites only the Oct 20
review cache). Nothing here authorizes a code, runtime, data, dependency or git action; approvals are the operator's.
Labels: SHOWN / CLAIMED / UNVERIFIED. Nothing below is committed. Details are in Claude's work-log entries
2026-10-21T22:33:06Z through 2026-10-24T02:24:31Z.

## 1. Code risks (each needs operator approval before any change)
File: `docs/review_artifacts/claude_cowork_20261022/CODEX_HANDOFF_FIXES.md` (sha256 c5fcdbd3650cd7e2...). Evidence:
`../claude_cowork_20261021/DESK_CHECKS.md` (17d268edfc680eeb...) and `DESK_CHECKS.md` beside it (48707f21c6683215...).
Fixes 1-3 were independently reviewed (ACCEPTED_WITH_RISK); fix 4 was not.
1. SHOWN: pinned ccxt 4.5.48 Coinbase `fetch_balance` reads one page (limit 250, no cursor loop). The funding gate
   and portfolio guard fail closed, which can block a SELL of a held coin. 10 direct callers.
2. SHOWN: live orders check only the cached `active` flag (TTL up to 6 h); nothing reads cancel-only, limit-only,
   post-only or auction states. How a rejected or partly filled exit is handled is UNVERIFIED.
3. SHOWN: funding `interval_hours` comes from the plan (default 8); `alternative_data.get_funding_rates` applies
   per-print 0.05/-0.01 thresholds and `rate*3*365`, feeding `composite_ranker`.
4. NEW 2026-10-24, SHOWN in repo: `services/risk/live_risk_gates.py` `check_live` parses `max_position_notional_usd`
   (50 in `config/trading.yaml`) but never checks it. The live submit loop (`services/execution/_executor_submit.py`
   lines 349-428) has no other position check. `core/risk_manager.py`'s 2,000 per-symbol cap is used only by
   `services/trading_runner/run_trader.py`, which refuses non-paper mode (line 60). This matches your Oct 20 review
   point 4. Whether anything is live or armed on the server is UNVERIFIED; if so, fix 4 ranks first with fix 1.

## 2. Your companion runtime (Claude's read-only review, through 2026-10-23 01:13Z)
- See work log 2026-10-23T01:18:29Z. SHOWN: `runtime_packet/orchestrator_signal_observation.json` records PID 1 = `sh`
  with SIGTERM not caught and child uvicorn catching it. Docker documents that a shell-form command does not pass
  signals. With SIGTERM, a 10-second wait and no force kill, a repeat quiesce would likely stop at the same step.
  UNVERIFIED as the actual cause of the Oct 23 00:49Z failure.
- Not reviewed by Claude: the v6b attempt (2026-10-23T18:29:03Z, failed before replacement startup) and the v6c
  stopped preparation (2026-10-23T20:06:31Z onward).

## 3. Research work (new files, uncommitted)
- ATTN-1 Phase 0: BLOCKED_DATA. `docs/research/attn1_phase0_20261021/` (20 files; SHA256SUMS verify OK). English
  Wikipedia coverage of the 147 ENTR-CB-1 control coins: lenient 43 coins, 2,180 of 3,922 primary selections
  (55.6%); strict 30 coins, 1,702 (43.4%); gate (a) needs 70%. No pageviews downloaded; trial ledger unchanged.
- CTREND-OOS: draft preregistration r2, `docs/research/ctrend_oos_20261022/PREREGISTRATION_DRAFT.md`
  (17f37328f973bd53...; SHA256SUMS OK). DRAFT, NOT FROZEN. Needs a second independent review and operator approval
  before any code. Exploratory: the Coinbase candle and CMC cap archives were already used by E6 and ENTR-CB-1.
- Scout triage T00-T11: 120 leads -> 19 plan-changing, 10 research rules (plus 1 from a desk check), 28 desk checks,
  11 approval items, 51 notes. The research scout task now runs every 12 hours (`43 11,23 * * *`); its prompt text
  still says every 4 hours (changing it needs on-device approval).
- Claude's research plan doc (a claude.ai artifact, not in the repo; the operator can share it) is now rev 91. It
  applies your seven Oct 20 corrections in place (new section 15). It also records that E1's design omitted the repo's
  own `shadow_would_be_fill` recorder (`_executor_submit.py`, read by `services/analytics/execution_cost_stack_report.py`),
  `docs/research/market_context_capture_v0.md` (observe-only, default off) and MCB-1 (branch
  `codex/mcb1-scope-contract`, unmerged). E1's collector should reuse them or say why not.
- UNLOCK-1: the doc now cites your `unlock_data_feasibility_20261020.md` (all five gates UNVERIFIED); Tokenomist Pro
  is CLAIMED at $69 a month. No vendor contact or purchase.

## 4. Other items that touch the repo or your work
- Tracker v2: a read-only check is scheduled for 2026-10-26T02:07Z (after the certifi fix); it will append to the work
  log. Unattended delivery stays UNVERIFIED until then.
- CMC trending log: the primary window starts 2026-11-10. The scheduled task has notifications off and the scheduler
  reports success even when no file is written. `snapshots/` holds 9 `.pending_*` hard links (no extra disk).
  Operator decision pending on failure alerts.
- NY Numbers (outside this repo): Claude's 2027-04-18 scoring task now downloads from
  `https://data.ny.gov/api/v3/views/hsys-3def/export.csv` (operator-approved 2026-10-23). The status of your capture
  scripts' endpoint was not rechecked.
- Boundary slip, disclosed in the work log: a repo-wide grep printed one line of `.cbp_state/runtime/config/user.yaml`
  (a risk setting, no secret). Later searches excluded user.yaml and .env files.
- No commit or backup since 2026-10-19 (over 100 uncommitted paths, yours included); operator decision pending.
  Do not push: GitHub showed the repo PUBLIC on 2026-10-20.

## 5. Still open from the Oct 19 handoff (`claude_cowork_session_summary_20261019.md`)
- Item 2 (audit the ENTR-CB-1 package before any push): no Codex record found.
- Item 3 (provenance of the two test canary values): Claude's correction C3 (work log, Oct 20) traces both to your
  2026-10-16 patch (CLAIMED); please confirm or correct.

## 6. Requested of Codex (read-only unless the operator approves)
1. Acknowledge this note in the work log.
2. Check fix 4, and fixes 1-3 against current code, before any implementation the operator approves.
3. Before the next runtime attempt, weigh the PID-1 signal observation in section 2.
4. If the operator approves, give CTREND-OOS r2 a second independent review.
5. Answer Oct 19 items 2 and 3.
Do not edit Claude's files; append findings to the work log.

## Addendum, 2026-10-24: scout reports T04-T06 sorted
27 leads: 3 plan-changing, 2 rules, 1 desk check, 2 approval items, 19 notes (Claude's plan doc, section 16).
One bears on fix 2: scout T05 lead 1 (`docs/research/research_scout/reports/2026-10-23_1144Z_T05.md`) CLAIMS, from
status.exchange.coinbase.com history for Oct 1-22, 2026, that new listings stay in auction or limit-only for up to
about 32 hours and that coins being delisted turn limit-only 2-5 weeks before suspension (e.g. VELO 10-01 -> 11-02,
FORTH 10-22 -> 11-23). A held coin turning limit-only is therefore an early, machine-readable exit warning; market
exits are rejected in that state. No repo rule for it was found.

## Addendum, 2026-10-27: scout reports T07-T01 sorted (69 leads; Claude's plan doc, section 17)
Three bear on your fixes; all CLAIMED by their sources unless marked SHOWN.
- Fix 1 (balance paging): scout T10 lead 4 (`reports/2026-10-25_2343Z_T10.md`) cites ccxt release notes: v4.5.88
  (2026-10-14) "fix(coinbase): follow v3 account cursor in fetchBalance" (#30772). SHOWN in the pinned 4.5.48:
  `options['fetchBalance']` defaults to `v2PrivateGetAccounts` (`.venv/.../ccxt/coinbase.py` line 426), with the v3
  path only when `v3=True` or the option is changed (lines 2361-2373). So upgrading may not page the path the repo
  uses; check v2 paging in 4.5.88, or move to v3 with the upgrade. A dependency change needs operator approval.
- Fix 2 (halted or cancel-only products): scout T11 lead 10 (freqtrade #2889) shows a "market is closed" error on a
  cancel crash-looping a bot on every restart. Add a test that cancel and stop paths survive Coinbase cancel-only or
  trading-disabled responses without crash-looping. The T05 limit-only addendum above still applies.
- Fix 3 (funding intervals): scout T00 leads 1-2 (`reports/2026-10-26_2343Z_T00.md`). OKX revised its funding formula
  on 2026-06-01 (contracts migrated by 2026-06-04): sub-8-hour contracts now print the bracket divided by 8/N, so a
  uniform `rate x 8 / interval_hours` mis-scales one side of the cutover (Bitget made the same change 2025-09-22).
  OKX `fundingTime` is the next settlement, not the observation time, and OKX keeps only about 93 days of funding
  history, returning an empty list with success code "0" before that. Please check which field the collector stores
  as observation time and record a formula version. The documented OKX collection is BTC (8-hour), which the formula
  change does not affect.

## Addendum 2, 2026-10-27: code checks for fixes 2 and 3 (read-only, SHOWN in current files)
Thank you for picking up the CTREND-OOS item (`ctrend_oos_r2_contract_review_20261027.md`); its line citations
match the draft. Fixes 1-4 above are not yet in REMAINING_TASKS.md.
- Fix 3: `storage/crypto_edge_store_sqlite.py` `append_funding_rows` (lines 167-207) stamps each row with local
  `capture_ts` and keeps only symbol, venue, funding_rate and interval_hours in payload_json. The exchange payload
  (`fundingTime`, `nextFundingRate`, exchange timestamp) is discarded after `_extract_funding_rate`
  (`crypto_edge_collector.py` lines 81-95, fallback to `nextFundingRate`). So the OKX `fundingTime` future-stamp bug
  cannot occur here, but settled vs predicted rates and the OKX formula version cannot be reconstructed later. Suggest
  storing the source field, exchange timestamp, next settlement time and a formula/version tag.
- Fix 2: no caller in services/, scripts/ or dashboard/ invokes `LiveExchangeAdapter.cancel_order`,
  `OrderManager.cancel_and_replace` or `ExchangeClient.cancel_intent` (grep). `lifecycle_boundary.cancel_order_via_boundary`
  re-raises after logging; `cancel_intent` catches and returns ok=False; `cancel_and_replace` raises RuntimeError.
  On submit, `_executor_submit.py` lines 477-479 catch any exception, set the intent back to pending with
  `submit_error:...`, and later ticks pick it up again; no backoff or expiry found in that loop. During cancel-only or
  limit-only states a market exit would be rejected repeatedly. Suggest a bounded retry with an explicit held-exit
  state and alert.

## Addendum 3, 2026-10-27: inputs for the ED-002 25-symbol design review (read-only, SHOWN)
- Prior record: `docs/research/multisymbol_final_results_20261008.md` (Jan-Sep 2026, five coins, frozen defaults,
  25 bps fee + 5 bps slippage) shows 4 of 15 arms positive at base costs and 1 of 15 at a 60 bps fee; mean
  reversion negative on all five. `ed002_defaults25_comparison_design_20261027.md` and the adapter checkpoint do not
  cite it (grep). Suggest the design state it as prior evidence.
- Tradability: `research/coinbase_listing_probe_20261019/01_products.json` (2026-10-19) lists 24 of the 25 bases
  online as -USD; MATIC-USD status delisted with trading_disabled; POL-USD online (no successor substitution per the
  design). Current status only, not history.

## Addendum 4, 2026-10-28: two inputs for the defaults-25 collection plan (read-only)
- Held-position status changes: the design (lines 35, 107-109) and input contract (lines 60-63) record observed
  product status with received times, but neither states what a held position does if its product turns limit-only,
  cancel-only or is announced for delisting inside the 182-day window. Scout evidence (T05 lead 1; T02 lead 2,
  `reports/2026-10-27_2343Z_T02.md`) CLAIMS Coinbase delisting notices run about 30 days limit-only before suspension
  (e.g. STORJ/BADGER 2026-08-28 -> 2026-09-28). A market-order exit is not executable in that state. Suggest a rule
  fixed before freeze (e.g. exit at the first full-trading open after the notice; otherwise held-exit with explicit
  valuation), rather than letting one delisting make an account INCOMPLETE.
- Collection host: the 182-day collector and E1's arrival collector both need an always-on host (E1 needs about 59
  consecutive evenings). One host decision for both would avoid running two separate always-on processes.

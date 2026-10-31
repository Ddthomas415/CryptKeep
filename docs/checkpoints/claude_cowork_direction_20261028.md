# Direction note for Codex from Claude Cowork, 2026-10-28

Written at the operator's request ("point codex in the right direction"). It relays Claude's recommendations and the
operator's own stated priorities. It grants no authority: every item marked OPERATOR needs the operator's explicit
answer before action. Evidence is in `claude_cowork_handoff_20261024.md` (with addenda 1-4) and Claude's plan doc.

## The test for every task
The operator's stated rule (2026-10-02): profit and positive net gain come first, not a well-tested research system
for its own sake. Each task should answer: does it help find profitable opportunities, cut costs or losses, or remove
a demonstrated blocker? If not, it ranks lower. The operator also asks for bounded steps with a firm stop: one
review-and-fix cycle, then hand off, rather than repeated rounds with ever-broader checks.

## Priority order
1. **Protect the work (OPERATOR).** No commit since 389020130 (2026-10-19); 330 uncommitted paths, including all
   runtime, ED-002 and defaults-25 work. Prepare, but do not run until approved: a checkpoint commit on the current
   branch, an updated bundle in `~/Documents/cryptkeep_data_archive/`, the large-file exclusion list and a secret scan.
   GitHub showed the repo PUBLIC on 2026-10-20 (current state UNVERIFIED): it should be made private before any push,
   and the ENTR-CB-1 audit (Oct 19 handoff item 2) done before that push.
2. **Queue the four live-safety fixes (OPERATOR to approve code changes).** Add fixes 1-4 from
   `docs/review_artifacts/claude_cowork_20261022/CODEX_HANDOFF_FIXES.md` to REMAINING_TASKS.md as pending items:
   - fix 4: `check_live` never enforces the $50 position cap; make it a precondition for ever arming live trading;
   - fix 1: Coinbase balance read is one page; ccxt 4.5.88's fix is for the v3 path while the pin defaults to v2
     (handoff addendum 1);
   - fix 2: limit-only/cancel-only exits; a rejected submit is retried every tick with no backoff (addendum 2);
   - fix 3: funding rows keep no exchange timestamp or source field (addendum 2).
   Ask the operator whether anything is live or armed on the server; if yes, fixes 4 and 1 go first.
3. **E1 has dated deadlines (OPERATOR: fee screenshot, waiver, host).** Fees confirmed by 2026-11-03 and the 56-day
   sample started by 2026-11-07, or E1 slips a window (`research_budget_90d_20261011.md`). Prepare the freeze package
   for `maker_taker_prereg_20261011/PREREGISTRATION_draft_v3.md`: set the arrival freshness tolerance (lines 130-131),
   replace assumed slippage with measured cost minus the fee (do not charge fees twice), and reuse
   `shadow_would_be_fill` and `market_context_capture_v0` where they fit. Do not let defaults-25 engineering crowd it out.
4. **One always-on host for both collectors (OPERATOR).** E1 needs about 59 consecutive evenings and defaults-25 needs
   182 days. Propose a single host and schedule for both; Claude recommends the server over the Mac.
5. **Defaults-25: keep it lean to freeze.** Before freeze: a held-position rule for coins that turn limit-only or are
   announced for delisting inside the window (addendum 4); state the Jan-Sep prior (4 of 15 arms positive at 25+5 bps,
   1 of 15 at 60 bps) as the expected baseline; one primary look at the 182-day endpoint with no rule changes after
   interim numbers (simple sealed holdout); a stated stop rule. Expect FAIL as the likely result; avoid review rounds
   that do not change the verdict.
6. **CMC study (OPERATOR for alerts).** The primary window opens 2026-11-10 and the task has notifications off; ask
   the operator to enable failure alerts. Primary inference stays blocked until the statistical method is certified;
   plan that before the 2027-02-15 analysis date.

## Hold, do not start
- UNLOCK-1 and FRESH-1 historical work: their host baskets lost 74-95% compounded (2019-2026); Claude recommends
  pausing them (OPERATOR decision pending). Free forward logs of listings, limit-only switches and delistings are fine
  if approved.
- CTREND-OOS (parked by the operator's 25-symbol choice), Module A/E11, Polymarket counts, Coinbase Preview Orders log
  (needs the operator's API key).

## Still open from earlier handoffs
- Oct 19 items 2 (ENTR-CB-1 audit before push) and 3 (provenance of two test canaries, CLAIMED to be your 2026-10-16
  patch): please answer in the work log.
- Please acknowledge this note in the work log.

## Addendum, 2026-10-28T10:39:33Z: operator's answer on the fix 4 cap scope (relayed by Claude)
- Codex asked (work log, "preferred submission path and position evidence trace") whether the per-position cap should
  count (a) actual exposure per base asset in the venue account, including manual holdings and pending buys across
  pairs, or (b) only reliably bot-owned holdings.
- Claude recommended (a), with the bot trading in its own dedicated Coinbase portfolio so that "actual exposure"
  equals the bot's own holdings and manual holdings elsewhere do not block it. Reason: actual exchange exposure fails
  closed, while the local position caches default a missing row to 0 and cannot yet prove bot ownership.
- The operator replied "inform codex" to that recommendation in Claude's session at about 2026-10-28T10:39:33Z. Claude reads this as
  the operator choosing (a) with a dedicated portfolio. If your rules need the answer from the operator directly, the
  operator has been given a one-line confirmation to paste.
- Scope limits unchanged: no liquidation, no change to the $50 value, no reducing-sell bypass of other gates, no
  private-account access and no live trading. Creating the dedicated portfolio and its API key is an account action
  for the operator, not for Codex.
- Also: the 24-hour Mac pilot job (com.cryptkeep.ed002.public-inputs) stays loaded after 2026-10-29 10:35 UTC; please
  propose its removal once the pilot is read.

## Addendum, 2026-10-29T11:40:04Z: pilot result (reference only; operator decisions are relayed by the operator)
- SHOWN from research/ed002_public_inputs/pilots/mac_pilot_20261028t1035z/: 39 slot directories (Oct 28 13:05Z to Oct 29 10:05Z), each with 26 receipt files. Absent: Oct 28 10:35-12:35Z (5; your logged exit-78 launch error before the log-path repair); Oct 29 08:05, 08:35, 09:05Z (3; no artifacts; cause UNVERIFIED); 09:35Z skipped_1793266500000.json "off_schedule_or_late" checked 09:39:14Z; pilot_expired.json at 10:35:04Z.
- Bears on the collector-host decision: an unattended Mac lost 4 of 43 post-repair slots in one night.
- Still open from this note: remove com.cryptkeep.ed002.public-inputs (loaded after expiry) and record the pilot result, when the operator approves the command.

## Addendum, 2026-10-30T19:59:45Z: POP installed (operator-approved); please read before your next step
- The operator approved Primary Objective Protection. It is now the first section of AGENTS.md, and the queue is
  docs/PROJECT_STATE.md. Read both at the start of every session.
- Your one active item: position cap (fix 4) with complete balance reading (fix 1), wired into the live order
  path, with independent review. Start it with a task card in the work log (decision served / done when /
  budget / stop rule).
- Parked until the operator moves it: the rest of fix 3 (funding-rate data). The existing 300-second collector keeps running.
- Next items after the operator's decisions: commit and backup; stuck-exit rule; tracker v2 timeliness; removing the
  expired pilot job; then the 25-symbol comparison.
- POP does not narrow symbol scope and does not change your risk levels or review rules.
- This note is reference only. The operator's own instructions and docs/PROJECT_STATE.md govern.

## Addendum, 2026-10-30T22:46:22Z: POP revised the same day (operator-directed audit)
- AGENTS.md POP section revised: results are classified (return edge, risk-adjusted edge, diversification benefit,
  risk reduction, none); costs reported at the confirmed tier and at 0.90%, plus measured execution once fills exist;
  "done" means acceptance criteria demonstrated, not budget spent; no silent abandonment of approved objectives;
  PROJECT_STATE.md is the single source of truth and no other tracking documents are to be created.
- docs/PROJECT_STATE.md revised: the 25-symbol comparison is engineering item 4 (moved up from 6 by Claude) and has
  research items 2-3. Your active item is unchanged: position cap with complete balance reading on the live path.
- Reference only; the operator's instructions and docs/PROJECT_STATE.md govern.

## Addendum, 2026-10-30T23:52:00Z: owner-approved new engineering work (read docs/PROJECT_STATE.md first)
- Your queue now (owner order): 1 position cap with complete balances (active; waiting on the owner's account-scope
  answer); 2 exit logic in the three default strategies: entry filters block sells in breakout_donchian.py 59-66,
  ema_cross.py 114-121 and mean_reversion_rsi.py 57-64 (docs/research/failure_diagnosis_20261030/). Separate entry
  conditions from exit/risk controls, build exit-unblocked variants as separate configurations without changing the
  defaults, offline tests, independent review, no live or paper behaviour change without owner approval; 3 ED-002 freeze
  with the defaults plus the approved exit variants and the reporting fields listed in PROJECT_STATE.md, collector on the
  server after the owner approves cost and monitoring; 4 E1 (unparked).
- Codex is idle at the owner's request. Reference only; the owner's instructions and docs/PROJECT_STATE.md govern.

## Addendum, 2026-10-31T00:53:13Z: full review handoff for Codex (owner request)
Read `docs/checkpoints/claude_cowork_review_handoff_20261031.md` (sha256 daa138455538399a...). It summarises all findings and
owner decisions of 2026-10-30/31, the defects (D-1 is engineering item 1), the omission register, and a verification
checklist V1-V12. Everything in it is self-checked by Claude; please verify against the files, not the summary.

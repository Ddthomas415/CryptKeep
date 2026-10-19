# Patch series 0001-0030: acceptance ledger - 2026-10-04

AUDITOR (Claude), compiling the reviewer's own recorded dispositions. This
adds no acceptance and changes no code. Purpose: every review since rev25
ends "overall series INCOMPLETE"; this lists, in one place, what has a
disposition, what does not, and what would have to be true for the series to
be complete. Sources are Codex's review notes in `docs/research/` and the
bundle's `REVIEW_HANDOFF.md`. Where I am quoting my own handoff rather than
a review, the row says so.

Series identity (cloud clone, CLAIMED): branch `claude/series-rev33`, head
`c53dbdac087ab6ee71e06c78c93196c8bb1e73d8` (after 0030), tree
`0544af67b7a1eb90e27774af488dacd81530d263`; base master
`97c24c8e4884629347a5492ae848133becd9027b`. Bundle rev41 in
`docs/review_artifacts/20261004_rev32_bundle/`. Not pushed, merged or deployed.
Apply order: 0001-0010, 0012-0018, 0020-0030. Not applied: 0011 (HELD),
0019 (superseded).

## 1. Disposition per patch

| Patch | Subject | Latest recorded disposition | Source |
|---|---|---|---|
| 0001-0003 | Kill cooldown, protective exits, PnL labels | Earlier bounded reviews; "not a fresh deployment approval" | handoff (reconciliation) |
| 0004 | Multi-symbol runner | "current form needs final review" | handoff |
| 0005 | Pending entries count toward exposure | Tested; reservation/concurrency not established | handoff |
| 0006 | submitting/held intent lookup | Addresses the lookup gap; not lifecycle proof | handoff |
| 0007 | Percentage exposure at cost | Intermediate dependency, not the final equity contract | handoff |
| 0008 | Invalid valuation rejected | Human-accepted correction (Codex's code) | handoff |
| 0009 | Current paper equity | Inspected/tested; account provenance and currency contract unresolved | handoff, rev23 |
| 0010 | Exact-symbol quotes | Bounded review; downstream permissive guard remains | handoff, rev23 |
| 0011 | Preset risk wiring | **HELD - not applied** | all |
| 0012 | Paper engine currency refusal | Not accepted alone: one blocking finding, treated by 0013 | rev23 |
| 0013 | Malformed config refuses buys | ACCEPTED_WITH_RISK (operator; Codex's code) | work log 2026-10-03 |
| 0014 | Test-mock signatures | ACCEPTED | rev25 |
| 0015 | Config read failure names its cause | ACCEPTED_WITH_RISK | rev25 |
| 0016 | Entries refused while an intent is in flight | ACCEPTED_WITH_RISK | rev27 |
| 0017 | Held-back exit records no bookkeeping | **INCOMPLETE** (applied; mechanism replaced by 0022) | rev28 |
| 0018 | Exit counters after the sell is written | **INCOMPLETE** (applied; mechanism replaced by 0022) | rev29 |
| 0019 | JSON-list exit events | INCOMPLETE - **not applied**, superseded | rev30 |
| 0020 | Exit-event journal prototype | ACCEPTED_WITH_RISK (operator; Codex's code) | work log 2026-10-03 |
| 0021 | Journal: confirmation, quarantine, reducer | ACCEPTED_WITH_RISK (bounded storage review) | rev32 |
| 0022 | Runner wired to the journal | INCOMPLETE at review; its finding fixed by 0023; **no explicit acceptance since** | rev32, rev34 |
| 0023 | Fixes from the 0021/0022 review | Malformed-event finding "resolved"; "not blanket acceptance" of its other storage changes | rev34 |
| 0024 | Venue hold | INCOMPLETE; findings fixed by 0025 | rev34 |
| 0025 | Venue ownership, queue recovery | INCOMPLETE; findings fixed by 0026 | rev35 |
| 0026 | Entry permission apart from venue | ACCEPTED_WITH_RISK (scoped) | rev36 |
| 0027 | Read-only inspection + procedure | INCOMPLETE; finding fixed by 0029 | rev39 |
| 0028 | Open position pins the venue | INCOMPLETE; finding fixed by 0029 | rev39 |
| 0029 | Ownership re-read; filter cannot hide a blocker | ACCEPTED_WITH_RISK (scoped) | rev41 |
| 0030 | Refusal reason logged; procedure extended | ACCEPTED_WITH_RISK (scoped) | rev41 |

Reading: 10 patches carry an explicit acceptance (0008, 0013-0016, 0020,
0021, 0026, 0029, 0030). The rest are either earlier bounded reviews
(0001-0007, 0009, 0010), accepted only through their corrections (0012,
0022-0025, 0027, 0028), or recorded INCOMPLETE and still applied (0017,
0018). No review has ever looked at the series as one applied tree.

## 2. What the reviews say is missing for "series complete"

Collected from the "remaining" sections of rev25 through rev41. Each is the
reviewer's statement, not mine.

| # | Gap | Kind | Who can close it |
|---|---|---|---|
| G1 | No full-suite run by the reviewer on the applied tree; cloud totals are CLAIMED | Verification | Codex: one run, about 4 minutes locally |
| G2 | No full-tree reproduction by the reviewer (apply all patches on master, compare tree hash) | Verification | Codex: `apply_order.txt` is in bundle folder 36 |
| G3 | No CI result | Verification | Needs a pushed branch or draft PR: operator's decision |
| G4 | No Hetzner / campaign-state proof; inspection command never run on real state | Verification | Operator / Codex on the host |
| G5 | `position_owner_conflict`: the open position runs without its correct stop state | Decision | Operator: what to do with such a position |
| G6 | Stop basis and position identity from the 0017 review (cells where a sell is lost) | Decision | Operator |
| G7 | Recovery procedure is PROPOSED; no accepted operator release procedure | Decision + review | Operator, then review |
| G8 | Concurrent runners, externally introduced venue history, partial state/queue restore | Untested conditions | New bounded tests, or an explicit "not supported" statement |
| G9 | 0004 "needs final review"; 0005-0007, 0009, 0010 carry open caveats | Review | Codex |
| G10 | 0017 and 0018 are INCOMPLETE yet applied | Bookkeeping | A statement, reviewed, that 0022 replaces their mechanism (or a squash) |
| G11 | 0011 HELD; account provenance and currency contract | Decision | Operator |
| G12 | Two stores with no shared transaction; WAL synchronous=NORMAL | Accepted limit? | Reviewer to record as accepted risk or blocker |

## 3. The shortest path, as I see it (a proposal, not a plan in force)

1. G1 + G2 together: Codex applies the 26 patches from bundle rev41 on a
   clean checkout of master, confirms the tree hash, runs the full suite
   once. This is the single cheapest step and it converts the largest
   CLAIMED item into SHOWN. Nothing is pushed.
2. G10: one reviewed paragraph on whether 0017/0018's INCOMPLETE findings
   still exist in the final tree. My claim, CLAIMED: the single-plan
   mechanism they criticise is gone after 0022 and Codex's own probes for
   those findings (`tests/test_review_exit_write_failure.py`,
   `tests/test_review_exit_event_loss.py`,
   `tests/test_review_restart_degraded.py`) pass on the final tree. That is
   checkable in the same run as step 1.
3. G5, G6, G7, G11: operator decisions. They do not need more code first.
4. G3: only after 1-3, and only if the operator wants CI evidence, push as
   an unmerged review branch. Still the operator's rule that decides.
5. G4, G8: last; they need the host or new tests.

## 4. What this ledger does not claim

It does not say the series is ready, safe to deploy or economically useful.
The economic notes of the same date say the candidates this code protects
are not economically qualified. A complete, reviewed series would make the
runner safer to operate; it would not make any strategy profitable.

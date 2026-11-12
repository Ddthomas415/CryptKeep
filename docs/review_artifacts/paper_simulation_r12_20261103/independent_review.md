# Initial R12 GATE - 2026-11-03

Bot relation: BOT_RULES; runtime configuration not inspected.

Reviewer: Poincare, separate agent 01a19fcb-7ac7-7fd3-b750-bc2834721e49. **REJECTED** initial source submission.
All eleven submitted hashes matched. The author's 397-pass receipt was inspected, not independently rerun.

## Four demonstrated findings

1. P1: malformed marked policy could fall into ordinary accounting instead of the atomic terminal fence. Three
   probes demonstrated malformed-policy execution, supersession bypass selling replacement holdings, and real
   engine execution. Exact-policy detection was insufficient; marked-but-invalid state must fail closed.
2. P1: the normal reconciler trusted linked-order identity/filled status without validating a pending root's canonical
   order and authoritative fill receipt. Two probes falsely completed an exit from an unrelated filled buy or a
   canonical filled flag with zero fills. Holdings remained 0.6/0.5; neither was proof the exit filled.
3. P2: strategy_id=None was accepted during prepare but replaced by empty configured identity during insertion,
   producing exit_identity_mismatch/no fill. Demonstrated API inconsistency, not an observed runner failure.
4. P2: routing used immutable root size while execution used holding-bounded size. A synthetic size-sensitive router
   saw 0.5 three times against holding 0.3 and kept the exit held. Current inspected router has no holding-bound check;
   that specific real-router refusal cause is unproven. The interface mismatch and conditional starvation are shown.

## Independent evidence

- Atomicity plus real-path R12 suite: 93 passed in 3.76s.
- Existing multi-symbol/R1 integration: 65 passed in 7.31s.
- Before-runner hybrid: 26 failed / 2 passed in 2.17s.
- Before-storage: 63 failed / 2 passed in 0.75s.
- Ten independent in-memory probes: seven failed / three passed. Passing cases covered journal-write recovery,
  multi-symbol refusal isolation and alert backoff. These are not pristine-tree comparisons or full-suite proof.
- Frozen hashes and whitespace check passed; no files or operational state were changed by review.

Initial README malformed-state/fence claims are qualified by this rejection. Full simulation INCOMPLETE. Retry
guarantees begin after durable tagged-intent creation; first-write/accounting remains R8, quote identity remains R4,
skip-sleep remains R1/operations caveat. Mocked router/safety/quote/channel values do not establish current operation.

## Corrections in progress

All four source corrections and regression deltas are complete. Main correction regressions: five fail submitted
modules and pass corrected code. Storage deltas: 60 failures / 25 preservation passes on the submitted store; all
pass corrected code. Corrected combined focused receipt: 487 passed in 21.08s. The implementing thread does not
certify those as independent acceptance; corrected_hashes.json binds the focused re-review now requested.
This initial submission/rejection remains preserved. At that correction handoff, acceptance was pending; the final
separate disposition is recorded below.

## Corrected R12 GATE: ACCEPTED_WITH_RISK

Separate reviewer Poincare closed all four initial findings on corrected_hashes.json, 11/11 hashes matched.
Invalid marked/JSON state and stripped-metadata tombstones fail closed; reconciliation requires canonical identity
and authoritative receipts; optional strategy None is preserved; routing and execution share a bounded attempt cap.
No remaining blocker was found within this focused correction scope. Initial rejection remains historical evidence.

Independent verification:
- Corrected atomicity/integration: **183 passed in 4.85s** (150 atomicity, 33 integration).
- Original counterexamples plus routing-growth case: **eight independent probes passed in 1.10s**.
- Rejected four-module snapshots: five correction cases failed in 0.67s.
- Rejected storage snapshot: 60 selected fence cases failed in 0.71s.
- Correction diffs/hash/whitespace checks passed.
- Author's **487 passed in 21.08s** receipt inspected, not independently rerun.

Acceptance is the separate reviewer's disposition, not author self-approval. It covers the durable-tagged-intent
R12 source dependency only. Full simulation remains INCOMPLETE. Same before-start R8 first-emission/accounting,
R4 quote identity, R1 timing, actual router/safety/channel/config/runtime/commissioning limitations remain.
No files or operational state changed during review.

What do I know that could change the owner's decision that I have not yet said?

# R12 pending paper exits - 2026-11-03

Bot relation: BOT_RULES; runtime configuration not checked. Source and synthetic local integration only.

AUDITOR (records separate GATE), HIGH risk. Author implementation ended READY_FOR_INDEPENDENT_REVIEW.
Corrected R12 source GATE: ACCEPTED_WITH_RISK. Full simulation: INCOMPLETE. No deployment/start.

Final disposition 2026-11-03: separate reviewer passed 183 atomicity/integration cases and eight independent probes,
closed all four findings and checked all eleven corrected hashes. The 487-case combined receipt remains author
verification, not separately rerun. This completes the durable-tagged-intent R12 source dependency; it does not
approve operation or the unfinished simulation. See independent_review.md for rejection and correction history.

**Dated correction after initial review, 2026-11-03:** the submitted candidate was REJECTED for two P1 blockers
and two P2 coherence failures (independent_review.md). The earlier passing tests did not establish blanket malformed-
state fencing or truthful reconciliation. In particular, malformed policy could enter ordinary accounting, unrelated
or unreceipted filled orders could falsely finish a root, optional strategy identity was inconsistent, and routing
used the wrong attempt quantity. Corrections/regressions are in progress; the implementation description below is
the intended contract, not acceptance of those uncorrected paths. Original submitted snapshots/hashes are retained.

**Corrected candidate, 2026-11-03:** all four findings have regression-backed source corrections. Marked invalid
policy/metadata and canonical tombstones cannot enter ordinary accounting; reconciliation requires canonical
identity and an authoritative fill receipt. Optional strategy identity is preserved. Routing receives a bounded
attempt copy; execution cannot increase that amount if holdings grow after routing. The queue root remains frozen.
Final combined focused receipt: **487 passed in 21.08s**, zero errors/failures/skips. Five main correction cases
fail submitted modules and pass current code. Eighty-five added storage cases give **60 failed/25 passed** on
submitted storage and pass corrected code (preservation passes are not claimed as new fixes).
See corrected_hashes.json and focused.corrected.*. Focused independent re-review subsequently ACCEPTED_WITH_RISK.

## What changed

New strategy paper sells carry retry_until_filled_v1 and a stable paper_exit_id equal to the intent ID. Queue creation
binds canonical client ID paper_intent_<exit_id> and freezes venue, symbol, type, limit price, quantity and metadata.
Ordinary/live orders and historical untagged terminal rows do not acquire this protocol or get silently resurrected.

Refusals stay held, with append-only refusal/retry/dispatch events. On a symbol's next runner visit, pending recovery
runs before quote/signal evaluation, preserves the root, and blocks new entry/duplicate exit accounting. A recovered
or unchanged signal is not required to retry. An uncertain claim/submission is recovered through the same canonical
paper order, not a second order identity.

The paper ledger transaction is the authority: preparation validates immutable identity, limits attempts to current
holding/original quantity, and rearms a rejected order only after unchanged downstream submission gates pass. Actual
fill accounting clamps a concurrently reduced holding and scales the fee. Filled/superseded tombstones commit with
the fill/holding state and permanently fence the root against selling a later replacement holding. A zero holding
supersedes without sending; it is not guessed filled. Limit prices/types are never converted or repriced.

Recovery of a committed fill restores submitted plus its linked order, then uses the ordinary reconciler to journal
before terminal filled. It does not bypass that journal boundary. Tagged resting orders wait on both a fresh snapshot
and a nonfuture, at-most-five-second-old quote. Over-two-minute pending exits request an alert; failed dispatches can
retry at most every 120 seconds and never erase/block the pending exit. A skipped/failed alert is not delivery proof.

## Evidence

VERIFIED_ENV: clean child environments, repository venv, bytecode/cache/plugin autoload disabled; temporary SQLite;
test harness blocks network/subprocess access and replaces configuration, router verdicts, quotes and external safety
inputs. No runtime settings or private accounts inspected. Real run_forever, paper consumer, engine, atomic ledger,
normal reconciler and journal execute locally.

- SHOWN combined focused receipt: **397 passed, zero failures/errors/skips in 20.38s**, 23 files. Exact command,
  environment, stdout and JUnit in focused.submitted.command.json / .txt / .xml.
- New real-loop/consumer/engine cases: 28; atomicity cases: 65. Existing multi-symbol, R1, ordinary paper-engine,
  queue, lifecycle, reconciler, exit and storage regressions are in the combined receipt.
  These are the initial submission counts; corrections extend them to 33 integration and 150 atomicity cases.
- Before-runner hybrid proof: new 28 integration cases select saved accepted-R1-before-R12 runner while other
  components stay current: **26 failed, 2 passed in 2.15s**. This is not a pristine full-tree baseline. Some cases
  first detect missing protocol metadata; the seeded held-root/unchanged-signal case specifically detects absent
  runner recovery. Cooldown passage is preservation of accepted R1, not a newly discovered R12 repair.
- Before-storage proof: 65 new atomicity cases against saved original storage in memory, temporary DBs: **63 failed,
  2 passed in 0.93s**. New-method failures and actual old accounting/idempotency counterexamples are not conflated.
  before_storage_probe.py asserts the expected failing pytest status rather than claiming a green baseline.
- Main and worker source/tests compile; changed-path whitespace check passed. No full-suite result claimed.

Original sources, submitted snapshots, incremental diffs and SHA256 identities are preserved. submitted_hashes.json
binds the candidate reviewed. Atomic storage worker Socrates edited only storage/paper_trading_sqlite.py and its new
tests; test worker Dewey wrote the real-path integration file. Main reviewed both and added post-order rejection,
lost-after-fill receipt, immutable payload and seeded recovery cases. Separate GATE requested; no author acceptance.

Legacy decision-unit test doubles explicitly stub only the new DB recovery callback; they do not establish R12.
The separate real-store harness tests it. Its minimal consumer now uses the required canonical client ID and new
order status for tagged exits; old assertions were retained. These fixture corrections were not production repairs.

## Requirement Disposition

| R12 requirement | Evidence | Status |
| --- | --- | --- |
| Refused protective/signal sells remain pending under one identity | Held/refusal/retry events, unchanged-signal and recovered-price tests | Implemented, self-checked |
| Stop and trailing under cooldown/refusal/stale quote | Six real-loop/consumer/engine cases, actual fees/holdings checked | Implemented, self-checked |
| Quantity at most current holding; zero superseded | Ledger transaction, partial/current/original cap and supersession tests | Implemented, self-checked |
| Never change price/type or fabricate a fill | Immutable queue/order identity; limit test; ledger evidence/journal ordering | Implemented, self-checked |
| Restart after claim/submission/committed fill | Same root/order receipt recovery; one fill/fee/journal | Implemented, self-checked |
| No duplicate root fill | Concurrent same-ID atomic tests and later-position fencing | Implemented, self-checked |
| Refusal/retry/time/alert evidence | Queue transaction/event table; delayed failed/successful-dispatch tests | Implemented, self-checked |
| Independent review | Separate GATE ACCEPTED_WITH_RISK; 183 cases and eight reviewer probes pass | Done for durable-tagged-intent source scope |
| Actual alerts/server commissioning/campaign operation | Not attempted | NOT DONE |

## Limits And Open Questions

- These guarantees begin with a durable tagged intent. The inherited first-exit bookkeeping-before-queue-write defect
  is not redesigned; an initial failed queue write can still consume a signal and miscount provisional performance.
  Retries demonstrably do not rerun that bookkeeping. First-write/accounting failure remains a before-operation R8
  lifecycle dependency, not evidence that the strategy made or lost money.
- Existing tick_reader venue-only fallback can still return another symbol's quote (known October patch 0010);
  this task adds timestamp rejection for pending fills but does NOT claim quote identity correctness. R4 must reuse
  that earlier fix/identity proof before a market-backed simulation. Synthetic tests supply the requested identity.
- No live retry, real router authorization, current master/read-only state, account-scope reconciliation, external
  alert receipt, measured execution, profitability or readiness is established. Full state-store/disk failure can
  prevent progress/evidence; malformed ledger evidence stays blocked rather than being dropped or marked filled.
- Exactly-once means this canonical paper exit root in the local ledger. It is not a guarantee against independent
  order writers, or proof of externally reconciled live fills. A position replaced entirely between observations
  without an observed zero has no generation identity here; that remains a separate ownership/reconciliation issue.
- R1's inherited skip-sleep cadence caveat remains. Pending recovery does not serve cooldown counts; the debt resumes
  after pending resolution. No threshold/time policy retuning or scheduling change is introduced.
- All 25 supported symbols remain supported. Existing per-account shared-cash/venue conventions and frozen campaign
  scope are unchanged. R6/R9 recording, R8/R4 lifecycle/data, R2/R3 operations, R10 providers/backups, owner evaluation
  choices and commissioning/start remain pending. No frozen market study or strategy criterion was altered.

Inspected: current source paths above, queue/storage transitions, prior pure exit planner (unwired with bounded retry
policy, not substituted for R12), October pending-event patches, frozen spec, targeted tests and generated receipts.
Not inspected: runtime config, live processes, private accounts, server, actual network/quotes or external channels.
Independent counterexamples, a missing lifecycle boundary or actual runtime evidence could change completion.

What do I know that could change the owner's decision that I have not yet said?

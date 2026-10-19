# Independent treatment candidate review

Active role: GATE. Acceptance: REJECTED for this candidate.
Reviewer: Hume, agent 01a11750-cb23-71b3-b694-1a02d3820c0e.
Exact patch and ten source hashes matched the manifest. Read-only static review;
reviewer ran no tests/imports and modified no files. Existing JUnit is not
independent test execution. No account incident or duplicate venue fill claimed.

## Findings

1. P1: _executor_reconcile.py:302 treats missing/None filled quantity as zero.
   Empty local coverage can therefore allow canceled/rejected/expired orders to
   become terminal at line 491 without affirmative execution-quantity evidence.
   Required proof: missing quantity remains pending; explicit valid zero can
   finish; complete priced trade evidence has an explicit quantity contract.
2. P1: fill_sink.py:147 commits daily accounting separately from the loss
   counter effect at line 169. Distinct events can interleave: an older profit
   resumes after newer losses and resets the newer lock at store line 452.
   Exactly-once markers prevent duplicate effects but do not establish order.
   Required proof: registered/enforced per-symbol ordering contract and a
   deterministic paused-profit/newer-loss regression, including restart.
3. P2: quantity-bound refusal at execution_store_sqlite.py:231 is unhandled
   at reconciler lines 412/464. A competing writer can abort the pass rather
   than return per-intent incomplete evidence and process remaining intents.
   Required proof: reconciliation-level writer conflict, retry and progress
   for an unaffected subsequent intent.

References refer to the frozen candidate under
/private/tmp/cryptkeep-treatment-candidate-5n68179x/source, not deployed source.
These are static source findings; fault-injection reproduction is still required.

## Main-agent proof and disposition

Forward applicability against the disposable base index and reverse applicability
against the candidate both pass. Exactly ten changed source/test paths shown.
The original 66-test slice remains SHOWN but insufficient for the findings.
Earlier mixed-snapshot full-suite proof does not supersede this review.
No push, merge, deployment, config/account/credential/process/order change.

Next bounded correction: reproduce and repair explicit missing-quantity handling,
with targeted tests, without silently selecting a distinct-event ordering policy.
Ordering semantics require a documented decision before implementing that repair.
Preserve the frozen rejected candidate as evidence; revised financial work must
return to independent review. Do not run release CI as if this were accepted.

# V6c Single Runtime Attempt

## Result

Role: ENGINEER. Risk: HIGH. Runtime: INCOMPLETE.
Operator authorized the single fixed handoff after the explicit scope question.
It ran once, exit 1. No retry, marker reset, new preparation or source repair.

SHOWN by the receipt: all four originals quiesced; all four prepared replacements
activated with passing replacement checks. Configured compatibility then returned
recipient_bindings=false, all other reported compatibility checks true, and
precondition=complete. The controller refused before any replacement start intent
or explanation query. The exact recipient subcondition remains UNVERIFIED: the
aggregate check catches several failures and no activated metadata/subcheck trace
was retained before owned cleanup.

Recovery removed the four replacements, restored original names/network
configuration and restarted the original apps. The controller reports
rollback_verified=true, rollback_exact_baseline=false, receipt_complete=true and
no unresolved ownership lists. services_started=true includes recovery starts;
it does not mean replacements started. Preparation and runtime attempt are
consumed. Do not reuse their IDs, reset receipts or invoke the wrapper again.

## Verification

- Offline preflight: 36 frozen bindings matched, actual inert loader passed,
  reservation absent and CLI digest matched. No tests rerun or implementation edit.
- One approved native handoff invocation; exit 1, runtime_verification failure,
  query_attempted=false and query_passed=false.
- Original receipt copied unchanged to runtime_attempt_v6c/receipt.jsonl.
- Read-only postcheck at 2026-10-24T02:42:47Z: all seven original IDs running;
  names, images, network IDs, restart policies and restart counts match baseline.
  All three storage start times unchanged. Four app start times changed following
  restoration. Docker reports healthy for PostgreSQL and all four apps; Qdrant
  and MinIO have no reported health status. This is not a new endpoint check.
- Postcheck required three bounded read calls: first optional-Health template
  failed (stderr not retained), exact original-ID check succeeded, corrected
  optional-field-safe seven-ID capture succeeded. No additional service actions.

No account, scheduler, strategy/risk or trading operation was performed. Selected
storage identity/start-time continuity is shown; volume bytes, healthy application
connectivity, full-system restoration and usable cited explanations are not.

## Artifacts

Under docs/review_artifacts/companion_worker_preparation_20261023/runtime_attempt_v6c/:

- outcome.json: exact sanitized terminal result and limits.
- receipt.jsonl: copied controller phase evidence, unchanged.
- postcheck.json: selected read-only original-ID inventory comparison.
- independent_review.json: separate GATE ACCEPTED_WITH_RISK for record fidelity
  only, no runtime success or cause confirmation.

Frozen SHA256 values:

```text
outcome.json  f93ae73cc94e5a4ab1576fda0274b32dbf099eb554bfe7ab2ee117442e7bbe3e
receipt.jsonl  a993c16b9c61a483b60700daf5ceb8b6180356ee138f14a6d55ac669c7aa0981
postcheck.json  45bca12b4f5a03c1dab991681013f84c9177362aa624845871b459481063d478
independent_review.json  ef02af1091292fb1d1158951d2f5afff5a302e83645d643f052efe3a0582f134
```

## Next Boundary

Separate GATE reviewed all 62 receipt events, saved outcome/postcheck and bound
source, and accepted record fidelity with risk. Parent read the complete review
and verified all three frozen artifact hashes unchanged. The postcheck stores
selected comparison booleans rather than complete raw metadata; replacement
removal is the controller recovery verdict, not an independent ID enumeration.
The exact first postcheck-template error remains unverified. No extra native
action or tests by the reviewer, no implementation change.

The next useful offline scope is to expose a bounded, secret-free reason for the composite
recipient-binding refusal and test it without weakening the predicate. A fresh
runtime attempt is not authorized and cannot be manufactured from consumed IDs.
No claim that the configured-network correction or guard repair resolved the
operational objective is justified.

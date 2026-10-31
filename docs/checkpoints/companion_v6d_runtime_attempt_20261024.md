# V6d Runtime Attempt

Role: ENGINEER. Risk: HIGH. Runtime: INCOMPLETE.
Outcome evidence: READY_FOR_INDEPENDENT_REVIEW.

## Execution And Result

User explicitly approved one bounded runtime attempt. After verifying 38 frozen
bindings, the inert loader, CLI bytes and unused cutover path, the fixed V6d
wrapper ran exactly once with --execute-once (session 29325), exit 1.
No retry, reservation reset or fresh preparation occurred.

SHOWN by the complete receipt and fixed controller flow:

- All nine configured compatibility checks true; recipient diagnostic null.
- Four replacement starts confirmed. Post-start recipient and health checks
  returned acceptance before the controller proceeded to one query.
- Companion transport returned HTTP 200, provider fallback, five evidence
  entries and execution_disabled=true. Provider fallback here is not the
  static dashboard_fallback provider.
- Client normalization rejected the companion envelope as foreign_asset;
  dashboard selected its static fallback. Explanation acceptance failed.
- The subsequent stored-document/archive/citation verification was not invoked.

This is not a working explanation-path result. HTTP 200, healthy service gates
and citation-shaped rows do not establish relevance or successful source
verification. The receipt does not retain original answer prose or matched
foreign tokens. Valid cross-asset rejection versus false positive remains
UNVERIFIED; do not disable or relax the guard to make this test pass.

## Recovery

Controller recovery quiesced and removed all four running replacements,
restored original names/networks and restarted originals. It reports
rollback_verified=true, rollback_exact_baseline=false and no unresolved lists.
Both preparation and cutover are consumed; prepared IDs must not be reused.
Audit/client/log effects may persist, as disclosed before authorization.

Read-only postcheck used three native reads: daemon ID census before/after and
one selected seven-original inspect. Census stable, prepared IDs absent. All
seven originals running; complete selected snapshot comparison differs only
in four app start timestamps. Three storage snapshots unchanged. Docker reports
healthy for four apps/PostgreSQL and no health field for Qdrant/MinIO. No new
endpoint request, query or credential value export occurred in the postcheck.
No volume bytes, continuous health or reversal of earlier audit writes proven.

## Citation Identity Observation

Using the actual response-summary hash method, none of the five returned
document-ID hashes matches the registered topical document 7 hash. This is only
a hash/identity comparison; it does not determine the response IDs' original
types, content relevance, or why retrieval chose them. No document contents or
private database were read. Query diagnostics repeated during failure handling
are not a second query.

## Preserved Artifacts

Under docs/review_artifacts/companion_worker_preparation_20261023/runtime_attempt_v6d/:

```text
outcome.json 6632d19acb5a4510a614f4f1e1bf06213bc0617cef0a40715dad921e465a4114
receipt.jsonl 0ca55ea24bf18b7ff5442d974267497de00f2f3a5e2af1c372459f35aa43b1a9
postcheck.json ae910c0b2bc4a7ef6886a71190abaf0dbf8c2b4b2b2c71231c1ccbeeba60a8ea
```

Receipt is an unchanged copy of the consumed original. The separate
citation_hash_comparison.json preserves the deterministic identity check.
No source/tests, accepted packet or historical records changed. No full suite
or targeted tests rerun: this was the approved runtime operation and read-only
outcome assessment, not a source repair.

## Next Boundary

Independent review of outcome fidelity, restoration and diagnosis limits.
Next useful repair scope should be offline retrieval/normalization contract
reproduction using existing evidence, not another startup loop. Preserve the
asset guard, frozen question and topical witness. No further query, cutover,
token access, new preparation or trading follows automatically.

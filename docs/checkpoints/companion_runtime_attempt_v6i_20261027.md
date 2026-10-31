# Actual V6i Runtime Attempt

Role: GATE closeout of separate review. Risk: HIGH. ACCEPTED_WITH_RISK
for the single committed archival runtime result. Broader research/interactive
readiness remains INCOMPLETE and is not claimed.

## Authorization and Invocation

Operator explicitly approved one reviewed V6i handoff: private reuse of the
existing internal token, graceful stop of four originals, start of four prepared
replacements, required checks and one frozen cited query. Storage services/volumes,
trading, risk settings and schedules stay untouched. Controller has 600 seconds
including 180 recovery, preceded by separate ten-second CLI/token-source checks;
no whole-wrapper 600-second guarantee. Success leaves replacements running only
if all checks pass; failure recovery is best effort. Logs/audit writes may persist.
No automatic retry/reset.

Before execution, 49 nonhistorical handoff-review bindings matched, exact review
and launcher hashes matched, and the cutover marker was absent. Checkpoint hash
exception was documentation-only historical closeout, not an executable waiver.
Invoked the reviewed command ONCE, execution session 26515, exit zero:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_integration_inputs_v6i_20261027.execute_reviewed_v6i --execute-once
```

## Shown Result

Exact saved tool stdout reports running_update_complete=true, query_attempted=true,
query_passed=true, receipt_complete=true, services_started=true,
prepared_ids_preserved=true, preparation_consumed=true. All unresolved lists empty;
controller_failure_stage null. rollback_verified=false/rollback_exact_baseline=null
are not a failed rollback claim: this is the successful path, no recovery attempted.
No extra native inspection, query, restart, retry or reset performed after it.

Saved records: docs/review_artifacts/companion_integration_inputs_v6i_20261027/actual_runtime_v6i/.

- receipt.jsonl: 73 events, SHA256
  266f582303978fce5ea87ca33cc804ef3ef3e46ba32528379bde586593815148.
- provisional_result.json: SHA256
  cda66d4e334e7c968c25cb0a57fc9f0290dbf111b3f2e00a3172f1122ca26dae;
  its exact digest is bound by cutover_result_committed in the receipt.
- tool_result.json stores the exact returned stdout/exit metadata plus session ID.
- outcome.json parses that stdout, not independent execution observation.

State files are copied byte-identically, originals preserved. Receipt contains
four quiesce confirmations and four replacement-start confirmations for audit,
risk, memory and orchestrator; no unresolved operation is reported. These are
controller attestations, not an additional independently inspected live inventory.
Success leaves the reviewed replacements running as authorized. Three storage
services and their recorded identities remain outside the replacement scope.

## Query and Evidence Lane

Frozen question: What news explains Bitcoin liquidations?
The approved single-cited-query-v1 archival probe used the actual dashboard
get_research_explain client, companion HTTP transport, normalizer and asset guard.
The saved diagnostics show companion HTTP 200, normalized accepted response,
five citation hash records and execution_disabled=true. Provider is fallback:
the companion's deterministic retrieved-evidence synthesis, not an external LLM
or static dashboard_fallback. No model-enabled/general interactive result claimed.

The primary invalid_envelope diagnostic has no HTTP status and arises within the
approved probe's primary-route isolation, not proof of a live primary API outage.
Existing companion_probe_request returns None from the legacy primary envelope
path while retaining the actual companion request/normalization path. Normal
dashboard configuration was not rewritten. No browser/UI request was performed.

All nine runtime-compatibility checks report true. Evidence verification reports
all five checks true: persisted_identity,article_view_mapping,content_hash,
topical_support,causal_limits; fixed diagnostic complete/ok. These are successful
verifier results on this one response, not independent proof of current market
causation or profitability. Latest market data is explicitly excluded by this
archival probe contract; ordinary market-aware behavior is not tested here.

The installation_checks_passed_pending_return payload labels its application
Snapshot installed_before_startup and network_connectivity_verified=false.
Those are the existing installation/configuration evidence lane, not a fresh
post-start inventory or proof that all networks were independently certified.
Later start confirmations, successful checks and real companion response are
distinct evidence. Do not silently relabel the earlier created-state Snapshots
as a running-state capture.

Only sanitized diagnostics/citation hashes and committed result are saved; raw
answer prose remains ephemeral by design. Citation identities can be correlated
against the fixed archived evidence; no verbatim answer reconstruction claimed.

## Review and Remaining Boundary

No source change or tests/full suite rerun for this operation. Planned runtime
checks and the one actual query are its verification. No new strategy, trading,
account, risk or schedule changes. Internal credential handling followed the
reviewed private handoff; no token value appeared in tool output or these records.
No secure zeroization or universal log-absence claim.

Request independent review of saved 73-event receipt/result/commit, input binding,
actual-ID correspondence, diagnostic lane/citations and success scope. No new
native actions authorized by that review. One successful archival proof does not
establish sustained health, unrestricted live-market explanations, external model
operation or a tested interactive dashboard. Attempt is consumed. Preserve the
running approved resources and all evidence; do not rerun the consumed handoff.

## Independent Result Acceptance

Separate GATE accepted the single committed result with risk, no blockers.
Review: actual_runtime_v6i/independent_review.json, SHA256
e3c6c0a3f06d97d7e02744e3329b1a1011cce4f71b5d570fa88e1a13a86880b6.
It read all 73 events, verified state-file copies/result commit/tool consistency,
input/record/actual-ID bindings and literal nine compatibility/five evidence
successes. All five citation/document/URL hash triples correlate to the fixed
55-row archive: keyword_5/document5, keyword_47/document47,
keyword_18/document18, past_1/document5 and future_1/document26. This is identity
correlation, not answer-prose reconstruction or a new causal claim.

Parent rehashed all 45 unique review-bound files before this documentation-only
closeout. There are 65 references because the 20-consumer map repeats entries;
duplicate hashes agree. No mismatches. The checkpoint digest now identifies
pre-closeout text; saved runtime/review/source/policy artifacts remain unchanged.
Reviewer made no native/credential/DB/query calls and reran no tests. Its
acceptance rests on saved records, not an independently observed live process.

The bounded archival restoration/probe objective is complete and accepted with
risk. Four approved replacements were left running following successful checks;
the single cited query passed with execution disabled. Attempt remains consumed;
no repeat, reset, new query, postcheck or service action follows. Any separate
general UI/live-market/model or sustained-health objective needs its own defined
scope and authorization. This success is not a profitability or trading claim.

# Legacy submitter claim ownership and acknowledgement recovery

2026-10-28. ENGINEER stage, HIGH risk financial concurrency/recovery.
Status READY_FOR_INDEPENDENT_REVIEW. Local source only; no deployment.

## Repair

The inspected legacy ExchangeClient.submit_order ignored insertion ownership
for created claims. An existing in-flight row could reach submit. It also built
the client before replay/block checks, and could mark error after an acknowledged
order's persistence failed. These are source/fixture findings, not live incidents.

The other live_intent_consumer already checks _inserted for in-flight rows.
This closes the legacy caller's parity gap, not a new global dedupe design.

Applied a bounded correction to services/execution/exchange_client.py:

- Match claim exchange/intent/symbol/client ID to the actual request.
- Only an atomic submission-claim owner may submit a created row. Unrecognized/unknown and
  non-replayable terminal/acknowledged states block. A known remote ID cannot
  reenter submit merely because its row says created or error.
- Valid stored replays return, and blocked claims refuse, before building a
  client. A built client is closed. A build failure follows existing error handling.
- A returned acknowledgement with failed persistence remains unknown, retains
  the known remote ID through the existing store method, and passes it to existing
  reconciliation. A contradictory not-placed result cannot authorize retry
  after acknowledgement. If the unknown write also fails, created remains
  protective against another caller.

Existing store claim gains opt-in claim_error_for_submit. Under BEGIN IMMEDIATE
it inserts a fresh claim or moves a matching error/no-RID row to created, reads
it in the same transaction, and returns _submit_claimed. ExchangeClient requires
that explicit ownership before build. _inserted keeps its original meaning.
Default callers do not opt into error reclamation; their behavior is preserved.
No schema/reset/reconciliation algorithm or numerical retry policy added.

Cooperating ExchangeClient retries from error are now serialized. Delay/count
limits remain unchanged and unbounded by this patch. Other submitting paths
not using this opt-in protocol and arbitrary state writers are not fenced or
certified. Exact-name ambiguity classification is unchanged. This is not
complete duplicate prevention or full Fix2 closure.

## Verification

VERIFIED_ENV, isolated venv, SQLite only at explicit temporary paths, fake
build/placement/reconciliation and socket/DNS/private-loader refusal:

    env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_exchange_client_claim_owner.py tests/test_exchange_client_retry_flow.py tests/test_order_dedupe_store.py tests/test_order_dedupe_unknown.py tests/test_retry_reconciliation_regression.py

Corrected-v2 author final46passed1.21s,exit0:37new selected-submit/claim cases,
4existing client cases and5store/source regressions. The ownership probe failed on the original
source (DID NOT RAISE,0.20s); archived original remains a negative control.
Initial36case submission was REJECTED under EXCHANGE-CLAIM-01; see below.

Two real SQLite claim callers compete while a fake submit is held; only one
reaches placement. Three post-ack reconciliation outcomes, unknown-write failure,
malformed acknowledgement, missing ownership, wrong identity, known remote IDs,
replay/cleanup and pre-ack ambiguity are covered.

The4existing client cases import the actual module/SDK package but replace every
build, credential and placement boundary before use; no real SDK client, keyring/
config credential read or account call. Directory creation is stubbed and DB
paths explicit. Dummy claims now match actual identity/ownership fields; original
test bytes are preserved. The37new cases AST-load actual selected method/helper
bodies and use the real dedupe store only against disposable databases.

No full suite, actual order/venue, deployed or distributed fencing proof. Missing
acknowledged identity remains unknown, not inferred not placed. Authenticated
fill/source truth, checkpoint integration, live cache freshness and original
funding-rate Fix3 remain unresolved.

No account/credential/network access, real DB/schema/migration, service/restart/
deployment/scheduler/pilot, trading/capital/risk setting, dependency/commit/push
action. Previous accepted gate/planner/checkpoint/cap sources unchanged.
Freeze exact source/test diffs and hashes for one separate independent GATE.

## Rejected V1 And Bounded Correction

Independent reviewer rejected submission01a18456-a590-7400-9fe9-34958aebdee8,
P1 EXCHANGE-CLAIM-01, despite36tests passing1.33s. On retry from an existing
error row, two failed persistence methods left error/no-RID, permitting another
placement. This is not just the previously disclosed concurrent-retry residual.
Exact v1 source/tests/docs/bindings/diffs are retained in rejected_v1.

Author reproduced both surviving error state (1failed0.21s) and two fake
placements (1failed0.20s). Added this paired regression and a rejected-v1
negative control, plus competing error-retry and direct-store opt-in/default
cases. Corrected claim commits created before a possible order, so later
write failures cannot leave the prior error eligible. Default store API remains
compatible. V2 source/test proof is frozen separately in corrected_v2 and
remains READY_FOR_INDEPENDENT_REVIEW until a new actual verdict.

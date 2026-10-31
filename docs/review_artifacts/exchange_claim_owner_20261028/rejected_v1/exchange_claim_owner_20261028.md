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
- Only the insertion owner may submit a created row. Unrecognized/unknown and
  non-replayable terminal/acknowledged states block. A known remote ID cannot
  reenter submit merely because its row says created or error.
- Valid stored replays return, and blocked claims refuse, before building a
  client. A built client is closed. A build failure follows existing error handling.
- A returned acknowledgement with failed persistence remains unknown, retains
  the known remote ID through the existing store method, and passes it to existing
  reconciliation. A contradictory not-placed result cannot authorize retry
  after acknowledgement. If the unknown write also fails, created remains
  protective against another caller.

No new store method, schema, reset, reconciliation algorithm or numeric policy.
Existing error rows without remote IDs retain their old retry behavior. This
does NOT serialize competing error-lane retries or set retry delay/count limits.
Those remain unresolved; this is not complete duplicate prevention or Fix2
closure. Other state writers and the exact-name ambiguity classifier are
unchanged and not certified by this repair.

## Verification

VERIFIED_ENV, isolated venv, SQLite only at explicit temporary paths, fake
build/placement/reconciliation and socket/DNS/private-loader refusal:

    env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_exchange_client_claim_owner.py tests/test_exchange_client_retry_flow.py tests/test_order_dedupe_store.py tests/test_order_dedupe_unknown.py tests/test_retry_reconciliation_regression.py

Author final36passed1.45s,exit0:27new selected-submit cases,4existing client
cases and5store/source regressions. The ownership probe failed on the original
source (DID NOT RAISE,0.20s); archived original remains a negative control.
Intermediate20passed0.63s,30passed1.53s and36passed1.68s preceded the final
stored-remote-ID assertion and36case rerun against the final source bytes.

Two real SQLite claim callers compete while a fake submit is held; only one
reaches placement. Three post-ack reconciliation outcomes, unknown-write failure,
malformed acknowledgement, missing ownership, wrong identity, known remote IDs,
replay/cleanup and pre-ack ambiguity are covered.

The4existing client cases import the actual module/SDK package but replace every
build, credential and placement boundary before use; no real SDK client, keyring/
config credential read or account call. Directory creation is stubbed and DB
paths explicit. Dummy claims now match actual identity/ownership fields; original
test bytes are preserved. The27new cases AST-load actual selected method/helper
bodies and use the real dedupe store only against disposable databases.

No full suite, actual order/venue, deployed or distributed fencing proof. Missing
acknowledged identity remains unknown, not inferred not placed. Authenticated
fill/source truth, checkpoint integration, live cache freshness and original
funding-rate Fix3 remain unresolved.

No account/credential/network access, real DB/schema/migration, service/restart/
deployment/scheduler/pilot, trading/capital/risk setting, dependency/commit/push
action. Previous accepted gate/planner/checkpoint/cap sources unchanged.
Freeze exact source/test diffs and hashes for one separate independent GATE.

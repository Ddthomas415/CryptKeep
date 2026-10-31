# Legacy submitter typed uncertainty and retry eligibility

2026-10-28. ENGINEER stage. HIGH risk financial submission logic.
Acceptance: READY_FOR_INDEPENDENT_REVIEW. Local implementation, not deployment.

## Shown defect and bounded correction

The previous exact-name ambiguity helper missed actual CCXT OnMaintenance
and builtin ConnectionResetError subclasses. The isolated OnMaintenance
regression failed before the change (1 failed, 0.87s). The archived accepted
pre-change client is retained as a negative control; it misses both types.
No observed exchange incident is claimed.

Reuse the existing is_retryable_exception helper and CCXT OperationFailed
hierarchy for submit uncertainty. Operation failures can follow placement;
uncertainty requires the existing reconciliation path, not retry permission.
SafeToRetryAfterReconciliation now additionally requires positive eligibility
from the unchanged shared retry helper. Acknowledged orders still cannot
authorize this retry signal. InvalidNonce retains its existing no-retry rule,
even though it now follows conservative uncertainty/reconciliation handling.
BadResponse and CancelPending likewise do not gain retry permission.

Known SDK rejections remain outside this uncertainty classification regardless
of misleading timeout/503/connection-reset message text. Existing shared helper
exact-name fallbacks for non-SDK transport errors remain unchanged.

Changed source: services/execution/exchange_client.py only.
Changed tests: test_exchange_client_claim_owner.py and
test_exchange_client_retry_flow.py. The latter now uses actual TimeoutError
classification rather than forcing ambiguity for a generic RuntimeError.
No store schema, ownership protocol, numerical timing/count policy, dependency
or public API change. Prior accepted atomic claim code remains intact.

## Verification

VERIFIED_ENV: isolated local venv, fake build/placement/reconciliation,
explicit temporary SQLite paths and offline guards. SDK package/type imports
are used, but no real SDK exchange client, credential loader or account call.

    env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_exchange_client_claim_owner.py tests/test_exchange_client_retry_flow.py tests/test_retry_policy_typed.py tests/test_order_dedupe_store.py tests/test_order_dedupe_unknown.py tests/test_retry_reconciliation_regression.py

Author result: 112 passed in 1.80s, exit 0. This includes the unchanged shared
retry-policy tests, real SDK subclass/message matrix, five error types across
three reconciliation outcomes, archived old-helper negative control, nonce
precedence and the previously accepted ownership/recovery regressions.
No full suite, market-data experiment or live submission test.

## Limits and next proof

Opaque generic exceptions remain a separate unresolved classification lane;
this patch does not establish all errors are safe. A retry signal does not
reset an unknown row or guarantee a subsequent submission. Reconciliation
truth, nonparticipating writers, live retry limits, partial-fill/checkpoint
integration, fresh venue metadata, alerts and original funding-rate Fix3
remain INCOMPLETE/UNVERIFIED.

No account/credential/network access, production database, service/scheduler/
pilot, deployment, trading/capital/risk-setting, install, commit or push action.
Preserve the pre-change archives and freeze hashes/diffs for a separate GATE
review of the exact source and documented six-file test command.

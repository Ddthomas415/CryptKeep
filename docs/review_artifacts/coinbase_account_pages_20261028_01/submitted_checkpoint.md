# Unwired Coinbase account-page reader

2026-10-28. ENGINEER stage. HIGH risk: private financial evidence and
cancellation boundaries. Status READY_FOR_INDEPENDENT_REVIEW.

## Scope And Change

Continues the accepted offline balance-integration preparation. Added
`services/execution/coinbase_account_pages.py` and
`tests/test_coinbase_account_pages.py`. No existing caller, factory option,
preflight, reconciliation, portfolio guard, account-wide cap or deployment
changed. No client was constructed or private request made.

The new module preserves the accepted synthetic pager's core definitions
AST-identically; the original prototype and its historical proof are unchanged.
It adds sync/async bindings to an existing caller-owned Coinbase client. An
explicit version selects exactly `v2PrivateGetAccounts` or
`v3PrivateGetBrokerageAccounts`. Each invocation supplies only limit/cursor;
there is no fetch_balance fallback, order method or server-directed next_uri.
All page, row, decoded-JSON and clock budgets remain mandatory caller inputs.
No defaults silently choose an account, API version or operational budget.

SHOWN by installed SDK source: both method names occur in the sync and async
Coinbase implementation. This is source compatibility evidence, not a real
client or provider-response test. SDK modules were not imported by the tests.

SHOWN by fake-client tests: terminal paging returns the complete supplied
sequence; page-two failure withholds the entire view. Wrong clients, missing
methods and invalid budgets fail before endpoint invocation. Async cancellation
propagates without retry. Expired clocks prevent the initial request or withhold
a returned page before the next request. Declared coroutine methods are rejected
by the sync reader; a coroutine returned dynamically is closed and withheld.

## Evidence Boundaries

The result is a raw-page research envelope, not a CCXT balance. It says
`SUPPLIED_SDK_PAGES_NOT_AUTHENTICATED_SCOPE_OR_CCXT_BALANCE` and retains
scope_authenticated=false, spendable_verified=false, execution_authority=false.
V2 availability remains unknown. V3 native accounts are not rewritten into V2
info.data. Currency labels are not certified canonical asset identities.

Two material assumptions apply only to a future invocation: the caller supplies
the intended Coinbase client/account marker, and the clock is the intended
monotonic clock. Neither assumption grants account scope or execution authority.
The account marker labels observations; it is not sent as an account filter or
authenticated independently. Pagination is not an atomic account/order snapshot.

Deadlines are pre/post method checks, not interruptible transport deadlines.
SDK-internal HTTP retries, recipients and effective transport configuration are
UNVERIFIED and not bounded by page-method counts. Blocking sync methods or hung
awaits can exceed the deadline. The async wrapper accepts sync methods, which can
block its event loop. A dynamically returned non-coroutine awaitable is refused
by the sync reader but not cancelled because its ownership is unknown.
Decoded JSON budgets are not wire-byte or peak-memory bounds. No raw private
payload persistence or secret logging is introduced by the module.

## Targeted Verification

VERIFIED_ENV: repository venv, isolated environment, invented SDK clients only.

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_coinbase_account_pages.py
```

Author result: 21 passed in 0.20s, exit 0. Socket/DNS entry points are patched to
refuse calls; no SDK client, credentials or existing execution module imported.
The 21 cases include six sync/async V2/V3 success combinations, four page-two
failures, six cancellation/deadline cases and five interface/core checks.
The accepted pager core is AST-identical, not a newly revised paging algorithm.
No full suite, previously accepted cap tests, backtests or runtime checks run.

An initial inspection command used two nonexistent paths (root directional plan
and execution __init__.py); it returned 1. Read the actual
docs/PROJECT_DIRECTIONAL_PLAN.md afterward. Execution is a namespace package;
the isolated import/test succeeded. No nonexistent source claimed inspected.

## Handoff

Freeze the source, test and this checkpoint with generated diff and hashes in
`docs/review_artifacts/coinbase_account_pages_20261028_01/`. Separate GATE review
must verify this narrow, unwired scope and its tests. Existing source authority,
real-client transport, authenticated completeness, full account exposure and
actual caller integration remain INCOMPLETE. No account, credential, service,
scheduler, trading/risk/capital, package, migration, commit or push action.

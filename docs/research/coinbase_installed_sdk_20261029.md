# Installed Coinbase SDK Paging Compatibility

2026-10-29. ENGINEER. Evidence READY_FOR_INDEPENDENT_REVIEW.
Existing production paging/cap integration remains INCOMPLETE.

## Result And Scope

The current account-page reader works with actual installed CCXT4.5.48 Coinbase
sync/async clients' implicit endpoint dispatch and balance parser under invented
request responses. A page-two-only asset and held amounts survive the complete
two-page path; failed/invalid continuation withholds the view. This closes the
specific previously missing installed-client dispatch/parser compatibility
proof, not live transport, authenticated account completeness or production use.

Only a new test file was added. This work edited no reader, order/funding guard,
SDK file, prototype or execution caller. No new pager, adapter or framework.

Packet generation initially stopped on the old whole-file place_order.py hash.
Comparison with the accepted funding snapshot shows one unrelated existing
change: _enforce_fail_closed now passes order_type to market-rule validation.
All other definitions, including tested funding/async helpers, are AST-identical.
Current full-file SHA137a3e7260381eec79982c63a716928446f6acc6909df37db92e91a0ce80664b
is recorded rather than falsely asserted equal to historical8d04313c... . That
existing change is preserved, not approved/reverted by this compatibility work.

## Verification Boundary

tests/test_coinbase_account_pages_installed_sdk.py has26cases covering sync/async
xV2/V3, page-two balances and same-currency aggregation, locked holdings, page-two
failure, repeated cursors, conflicting IDs, page budget, async cancellation and
refusal to follow server-provided next_uri as a recipient.

Actual clients are constructed with apiKey/secret None. The SDK's real Entry
descriptors call a supplied client.request stub; actual parse_custom_balance
runs on the merged native info. This is NOT a real signed HTTP request. Sign,
credential checking, fetch_balance, orders, requests/aiohttp transport and socket
connect/DNS entry points are refused. Async clients close within their event loop.

The first harness run had22setup errors: vendored toolz version metadata tried
to launch Git during SDK import and hit our blanket AssertionError process guard.
The guard now raises FileNotFoundError instead, allowing the SDK's existing
metadata-unavailable fallback without launching Git or changing installed files.
This was a harness issue, not a production paging defect. Version metadata for
that vendored dependency is unavailable in this test context. Network and order
guards were not relaxed. The first corrected26-minus4case run passed22cases3.81s.

VERIFIED_ENV final consolidated command:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_coinbase_account_pages_installed_sdk.py tests/test_coinbase_paged_preflight_compatibility.py tests/test_proposed_async_balance_preflight.py tests/test_coinbase_account_pages.py
```

SHOWN:98passed6.98s,exit0.26new actual-SDK cases plus72existing selected-parser/
funding, async-preflight and fake-client reader cases. Those older selected-source
tests do not become full-module order tests through sharing a command. Scoped
git diff --check passed. No full suite, market study, private account, credentials,
source wiring, deployment, order, capital/risk or scheduler/service action.

## Preserved Limits And Next Integration Boundary

The reader still says scope_authenticated=false, spendable_verified=false and
execution_authority=false. Scope is caller-supplied, not verified by test labels.
V2 availability remains unverified despite the SDK parser calling totals free.
V3 native accounts/locked fields are preserved, not rewritten into legacy
info.data; existing portfolio/funding compatibility limitations remain.

The tests replace request before signing/HTTP: they do not bound SDK retries,
recipients after signing, wire bytes, real latency or cancellation of an ongoing
HTTP call. Existing cooperative deadlines are not interruptible transport limits.
Paging is not an atomic holdings/order snapshot, and no pending external order,
canonical asset identity, account-wide reservation or position cap is implemented.

Before production integration, the existing caller must supply the intended
API/account scope and bounded transport policy, preserve native/raw and aggregate
coherence, and refuse incomplete/unauthenticated evidence. Do not silently wire
this result into live admission or convert a missing asset into proven zero.
No production account or trading change is authorized by these tests.

Independent review packet: docs/review_artifacts/coinbase_installed_sdk_20261029/.
Two assumptions are limited to fixture interpretation: invented responses represent
the specified native shapes; the supplied request stub is the deliberate transport
boundary. Neither is account authentication or evidence about a live provider.

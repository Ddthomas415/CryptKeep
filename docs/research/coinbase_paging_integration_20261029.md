# Opt-In Coinbase Paging Integration

2026-10-29. ENGINEER. HIGH-risk financial/configuration source change.
Implementation READY_FOR_INDEPENDENT_REVIEW. Production policy/activation absent.

## Delivered Source Path

The accepted pager is now reachable through the existing sync/async common
preflight and preferred LiveExchangeAdapter.fetch_balance. It is not another
pager algorithm or order router. Reuses the existing client's native endpoint
methods and installed parse_custom_balance. No new client is created by reading.

New coinbase_balance_observation.py supplies read_balance_sync/read_balance_async.
With no options.cbp_balance_paging key, legacy balance behavior is unchanged.
When the key is present, every policy field is mandatory; None/invalid settings
are errors, not permission to fall back. Page failure, bad continuation, parser
failure, unknown/rounded totals, altered raw info, reserved-key collision or a
late result withholds the entire observation. No configured-path fetch_balance
fallback is used. Total holdings and V3 free/locked aggregates must agree exactly
with the pager's rational amounts; raw native info is preserved.

make_exchange and LiveExchangeAdapter accept optional balance_paging_policy;
the adapter validates before credential loading and the factory copies it into
client.options. Existing kwargs/configuration are unchanged when omitted.
Legacy clients can already carry this key through their existing options dict;
the common preflight recognizes it. Direct raw SDK.fetch_balance calls elsewhere
are NOT monkeypatched or automatically paginated.

## Explicit Policy, No Adopted Operator Values

Required keys: version(v2/v3), scope(coinbase plus caller account marker),
page_size(positive integer<=250), max_pages, max_rows, max_json_bytes and
timeout_seconds(positive finite). Integer budgets reject booleans. No page,
account, byte or duration default is invented. No existing config enables it.
Changing this configuration in a real client is a separate operator decision.

Each read derives a shared monotonic deadline and uses it across all pages and
before/after parsing; backward/invalid clocks and late results are refused.
These are cooperative result-acceptance checks, NOT interruptible HTTP timeouts,
wire-byte limits, peak-memory caps or bounded SDK-internal retries/recipients.
A blocked SDK method can outlive the window. No shared client transport settings
are mutated to pretend to enforce a hard deadline.

The existing portfolio/funding validators still decide funding permission.
V3 native accounts are not relabelled as V2 info.data: current legacy portfolio
checks therefore continue to refuse that incompatible path. V2 spendability
is not certified by the SDK parser's free label. Rounding mismatches may refuse
otherwise legitimate balances; the source does not silently manufacture precision.

Returned paging evidence says all_supplied_pages_returned, not authenticated
account coverage. scope_authenticated/spendable_verified/transport_limits_verified/
execution_authority remain false. Scope is caller supplied. Currency aliases,
other portfolios, pending manual orders, atomic snapshots and reservations are
not established by paging. The account-wide position cap remains INCOMPLETE.

## Verification

49new cases use actual installed CCXT sync/async dispatch/parser with supplied
request responses. Cover real read/parse flow, default preservation, V2/V3,
page-two failure, cursors, parser/raw mismatch, precision, reserved metadata,
invalid policy, clock regressions/late parser, cancellation, actual common
preflight to synthetic submission marker, V3 guard refusal, factory copying and
preferred adapter constructor/fetch routing. No real credentials or private I/O.

VERIFIED_ENV final command:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B docs/review_artifacts/coinbase_paging_integration_20261029/verify_offline.py
```

SHOWN:211passed12.88s exit0 across8files:154prior cases+49new+8factory regressions.
The wrapper blocks network/process entry points and allows SQLite only within
disposable state, including pytest basetemp. Full-module cases use invented
clients and unit dependency stubs, not real signed requests or observed orders.
Intermediate new45cases passed5.60s and7file199passed12.48s; final adds collision
checks and existing factory cases. No full repository suite or deployment proof.

Existing structural tests project out only the exact new async import/read
substitution before checking the previous proposal AST, in addition to the
already reviewed sync bridge projection. Behavior tests execute current source.
Old harness/source bytes are preserved; no frozen study or criterion changed.

## Handoff And Boundaries

Before-source copies, exact diff and hashes are in
docs/review_artifacts/coinbase_paging_integration_20261029/.
Independent review must verify all changed caller/factory paths and tests.
No production paging policy, account call, secret lookup, cap value, trading
activation, process reload, deployment, collector or scheduled job changed in
this work. Tests use None-key SDK clients and invented adapter credentials;
actual credential loading is stubbed before constructor invocation.

Two assumptions: callers intentionally supply the client/policy scope; native
responses follow the declared V2/V3 contracts. Neither grants account truth.
No claim of live completeness, authenticated exposure, hard transport budgets,
position-cap enforcement or profitability follows from this integration.

Next boundary is an adopted operator paging/transport/account-scope policy,
followed by separately authorized qualification; current source stays opt-in.

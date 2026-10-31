# Opt-in paired funding in the existing collector service

2026-10-29 America/New_York. ENGINEER. HIGH risk: financial capture/persistence.
Implementation READY_FOR_INDEPENDENT_REVIEW; overall Fix3 INCOMPLETE.

## Delivered integration

Added okx_funding_pair_batch.py and tests/test_okx_funding_service.py; changed
crypto_edge_collector_service.py only. Pre-change service archived in before/.
The new optional cfg.okx_pair_options defaultsNone, preserving both ordinary
and SDK raw collector behavior. Existing CLI, plans, jobs and source producer,
journal, decoder, strategy gates and model artifacts stay unchanged.

Opt-in requires raw_funding_only=True, explicit db_path/source, existing raw
row/byte budgets, and an exact options dictionary with max_requests,
total_timeout_seconds, request_timeout_seconds and max_response_bytes. Every
funding row must explicitly name venue=okx, configured symbol and distinct
native inst_id; no guessed symbol mapping or alias duplication. All rows and
options are validated and copied before any funding request.

max_requests must equal2times the declared row count, with one shared <=30s
funding capture budget, <=10s per-process timeout, <=1MiB per body. A dispatch
wrapper rechecks the shared deadline and clips subprocess/curl timeouts, so
per-symbol calls do not quietly multiply the time allowance. Failed pairs are
not retried; later symbols may run within the remaining budget. Expired symbols
produce explicit zero-dispatch diagnostics. Tests exercise25synthetic IDs, not
historical tradability or the real study universe.

The existing collector receives a funding-empty copy of the plan; other streams
are preserved, and unexpected funding from that call is refused. Other-stream
SDK calls retain their existing behavior and are OUTSIDE the funding request/
capture budget. No claim is made that it bounds the whole collector, local
processing, process creation/OS cleanup or persistence. No live requests ran.

Successful pairs use the accepted journal wrapper. Failed/partial/expired
attempts use a distinct diagnostic-only raw payload marker, retaining public
body bytes as base64, receipts, failure type and requested/configured identities.
They never become valid pairs or normalized rates. All funding evidence goes
through the existing atomic bounded raw writer; legacy funding table untouched.
Insufficient actual encoded-byte budget can still refuse the whole raw batch.

Service output adds JSON-safe capture counts/limits and separate as-recorded
forecast quotes. Any failed pair makes service ok=False with partial/all-failed
reason, even when diagnostic rows or other streams were written. Raw count
includes diagnostics; successful/failed pairs are explicitly separate. Old
funding aggregates stayNone and stale legacy meta stays excluded. All execution/
strategy/crowding boundaries remain unchanged and false for these observations.

## Verification

VERIFIED_ENV isolated command, no conftest/plugins/cache. Author278passed in
1.99s,exit0; five unknown-slow-marker warnings from existing tests because
project marker registration is bypassed. Not full-suite or live-system proof.

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_okx_funding_service.py tests/test_okx_funding_pair_producer.py tests/test_okx_funding_journal.py tests/test_okx_cash_cost.py tests/test_okx_funding_contract.py tests/test_synthetic_funding_observations.py tests/test_funding_receipts.py tests/test_funding_store_bridge.py tests/test_crypto_edge_collector_service.py
```

Fake transports; temporary SQLite only. New cases refuse subprocess/socket/
default-directory/non-temp-DB operations, test1/2/25contract batches, identity/
budget preflight, default signature preservation, nonfunding stream retention,
partial failure/raw-byte recovery, shared deadline, option-mutation isolation,
serialization and reopen/readback. Prior receipt/service parity cases included.
No new market data, strategy/backtest or financial return computed.

## Operational limits and handoff

Two assumptions: caller-owned plan/options/transports obey their interfaces;
public data/local clock remain unauthenticated and do not certify payments or
live freshness. Existing binary signature-trust limitation remains unresolved;
no new binary check or integrity condition was added to this source step.

The service retains its existing store constructor/DDL behavior. Opting in on a
real database could initialize existing schema and write; this source acceptance
would not authorize that. Source remains off by default and CLI cannot enable
the new option. No actual config/collector/scheduler/server/Docker/account/
credential/realDB/trading/capital/risk/deploy/dependency/Git operation occurred.

Exact diff/bindings and before copy under
docs/review_artifacts/okx_funding_service_20261029/. Separate GATE reviews the
shared bounds, failure honesty, defaults, source compatibility and one focused
command. Stop at implementation proof pending review, without another runtime
attempt. Recurring activation, historical intervals and crowding qualification
remain separate unresolved boundaries.

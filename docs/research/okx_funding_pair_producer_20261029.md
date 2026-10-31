# Opt-in one-shot OKX funding pair producer

2026-10-29 America/New_York. ENGINEER; HIGH risk: external transport/persistence.
Implementation proof READY_FOR_INDEPENDENT_REVIEW; original Fix3 INCOMPLETE.

## Delivered source scope

Added services/analytics/okx_funding_pair_producer.py and
tests/test_okx_funding_pair_producer.py. No existing source or frozen artifact
changed. All27inputs from the accepted journal packet still match their hashes.
No CLI, scheduler, process, default collector mode or configuration was added.

collect_okx_funding_pair is disabled by default. Enabled use requires an
explicit native uppercase swap identity and explicit limits. One invocation
permits exactly two application GET dispatches at most: current funding, then
five-row funding history for that same native identity. No SDK/load_markets,
discovery, account, authentication, pagination, redirect or application retry.
The old single-endpoint collector stays unchanged and is not silently enabled.

The fixed transport command uses /usr/bin/curl with curl config disabled,
clean environment, no proxy, HTTPS/TLS verification, no redirect/retry, GET
only and stdout body plus final HTTP status trailer. Fixed host/paths and a
native-ID grammar prevent caller-directed hosts, queries or shell commands.
No shell is invoked; stderr and exception messages are not returned or logged.
Explicit falsey injected transports are retained, not replaced by live defaults.

Source caps:2dispatches, total capture budget at most30s, per-process timeout
at most10s (also clipped to remaining time), body cap at most1MiB each. Limits
must be positive finite typed values; booleans are not budgets. First-response
transport/API/identity/JSON failure stops before history. Each attempt retains
its raw bytes or explicitly truncated prefix, request/receipt times, body hash,
transport/HTTP outcome when available and a type-only failure. Failed or late
captures never become a pair. Partial evidence is returned to the caller, not
automatically durable. No partial data is substituted into a valid pair.

Capture budget is checked between operations and after final pair validation.
This is not a hard whole-process watchdog: process creation/OS cleanup, local
parsing/clock stalls and caller persistence are not globally interruptible.
subprocess.run applies its own timeout to its child communication. Per-call
limits are not a global quota for multiple callers, loops or DNS/TLS internals.
No crash/cancellation cleanup certificate follows from the fake-transport tests.

## Journal integration and uncertainty

collect_and_journal_okx_pair requires a caller-owned existing store, explicit
source and journal-byte budget. Invalid writer interfaces are refused before
enabled capture. Disabled/failed capture never writes. Complete validated pairs
use the already accepted one-row bounded atomic journal adapter; no constructor
or DDL is invoked by this wrapper. Passing a real store would write to it.

A persistence exception returns journal_state=unknown, retaining the captured
pair and making no retry. It never equates an exception with definitely not
written; a post-commit fault case proves that distinction. MemoryError and
KeyboardInterrupt propagate rather than becoming ordinary success/failure
receipts. A successful source result means raw pair captured/journaled under
that supplied interface, not live freshness, trader payment or financial edge.

## Verification actually run

VERIFIED_ENV isolated venv tests; no plugins/conftest/cache. All new transport
calls fake; new cases refuse real subprocesses, sockets, default directories
and non-temporary SQLite. Command exit0, author252passed1.61s:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_okx_funding_pair_producer.py tests/test_okx_funding_journal.py tests/test_okx_cash_cost.py tests/test_okx_funding_contract.py tests/test_synthetic_funding_observations.py tests/test_funding_receipts.py tests/test_funding_store_bridge.py
```

Earlier author247passed1.81s then251passed1.57s preceded extra dependency and
store-preflight cases. No full suite or live transport result is claimed.
Cases cover fixed URL/command/env/timeout controls, invalid options, explicit
falsey transport, HTTP/API/identity/deep-JSON/overflow errors, redirect refusal,
timeouts/partial bodies, byte/deadline limits, systemic exception propagation,
no store calls after failure/disable, disposable capture/write/reopen/read,
source/byte preflight and a post-commit uncertainty fault with no recapture.

The accepted saved public bodies are inert parsing fixtures; mutations and
receipt times are synthetic test inputs. No new API call, market experiment,
signal, order, account balance or profitability result was produced.

## Assumptions, review and next boundary

1. Explicit transports/clocks/stores honor their documented caller-owned
   interfaces; this module is not a sandbox against malicious dependencies.
2. Public data and local receipt clocks are not independent payment/freshness
   proof. Existing forecast/crowding/strategy/execution limitations remain.

Freeze exact source/tests/checkpoint/diff/dependencies under
docs/review_artifacts/okx_funding_pair_producer_20261029/. Separate GATE reviews
request ownership, bounds, failure retention and journal uncertainty, and runs
the one documented focused command. High-risk source is not self-accepted.

After source acceptance, a separately authorized two-GET foreground transport
check can verify real behavior, retaining evidence without a real DB write or
collector activation. Any recurring collector change, real-store initialization
or deployment remains separate. Do not repeat old backtests or rewrite history.

No network/SDK/account/credential/realDB/schema/service/server/Docker/scheduler/
collector/config/trading/capital/risk/deploy/dependency/commit/push operation.

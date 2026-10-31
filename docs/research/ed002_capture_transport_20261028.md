# ED-002 bounded public-capture preparation

2026-10-28. Role ENGINEER. Risk HIGH: HTTPS, process supervision and research inputs.
Implementation READY_FOR_INDEPENDENT_REVIEW. Live capture NOT RUN or authorized.

## Approval And Delivered Scope

Operator replied "approve. carry out the next steps" to the submitted candle
adapter. Record human ACCEPTED_WITH_RISK for that exact synthetic implementation,
not independent review, live capture authority or confirmed source authenticity.
Submitted candle source SHA256 remains
`9425211207738f0395f28b3f8c02c8a292c9a2e80e5d8d4b203e5ec5ebf273de`.

Added `scripts/research/capture_descriptive_inputs.py` and fake-transport tests.
Reuses the existing exclusive raw-response/receipt pattern and the accepted
metadata/candle adapters; does not modify the old archive or registered collector.
Default CLI mode is read-only plan inspection. No scheduler or persistent worker.

## Fixed Proposed Capture Boundary

| Boundary | Prepared implementation |
| --- | --- |
| Purpose | One two-completed-hour schema/receipt feasibility capture, not a study |
| Requests | At most 27 transport calls: products, currencies, up to 25 candle GETs |
| Recipient | HTTPS api.exchange.coinbase.com, only those public paths |
| HTTP behavior | No application HTTP retry, redirect, credentials or environment proxy |
| TLS | Existing certifi CA file, certificate verification and hostname checks on |
| Time | 5-second socket timeout; 110-second cooperative loop; 120-second parent worker wait |
| Cleanup | Kill only the owned capture worker, wait up to 5 seconds; failure recorded |
| Payload | At most 2 MiB stored per response and 16 MiB overall; one overflow-detection byte may be read before stopping |
| Persistence | Exclusive new public folder, raw bodies, intents, receipts, source/plan hashes |

Socket timeout is not a five-second whole-request/DNS guarantee. The parent
watchdog bounds its worker wait, not process creation or initial/final filesystem
operations. Killing/reaping can fail; the manifest reports that failure. No claim
of a universally guaranteed 125-second total command, memory cap or security
sandbox. Initial plan checks, process creation and final receipt/hash operations
are outside the parent wait. No live timing or cleanup behavior was exercised.

The two-hour window is resolved once at worker start and stored before requests.
It is not an evaluation start or backdated study registration. All 25 identity
rows are retained. Current fetched metadata decides required candle captures:
known-ineligible flat symbols stay visible without requiring their candles;
unknown identities/status produce INCOMPLETE, not silently excluded assets.

Raw payloads and sanitized per-request evidence persist on failure. An intent
records an imminent call, not proof a request reached Coinbase. HTTP/transport
failures stop the attempt, with no reset/retry. Oversized payload prefixes are
labelled truncated, never a full-body hash claim. Worker preflight/client/capture/
write failures have stage/type diagnostics without exception messages. A killed
worker may leave partial files; they are preserved, not overwritten or deleted.

The parent rechecks worker receipt shape/counts and saved payload hashes before
accepting a COMPLETE capture. Such status means only required window coverage
and transport completion. Latest-bar one-hour receipt diagnostics remain explicit;
capture completeness is not causal availability certification, real identity
approval, warm-up readiness, observed execution or profitability.

## Prepared Candidate Plan And Read-Only Preview

- Plan: `research/ed002_public_inputs/plans/feasibility_20261028.json`.
- References: `research/ed002_public_inputs/plans/candidate_id_sources_20261028.json`.
- All 25 vendor product/base/quote candidates were extracted from the preserved
  October 27 products/currencies responses; both payload hashes matched their
  receipt. References contain no reused permission interval. These are dated
  vendor ID candidates, not independently approved semantic identities.
- Live code must refresh metadata before any candle request; old status is not
  reused. Unknown/current conflicts remain visible. No POL substitution.

VERIFIED_ENV actual read-only preview, exit 0:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ./.venv/bin/python -B scripts/research/capture_descriptive_inputs.py --plan research/ed002_public_inputs/plans/feasibility_20261028.json --output research/ed002_public_inputs/NOT_STARTED_20261028
```

SHOWN: dry_run=true, planned_max_requests=27. No output capture directory was
created, no worker started and zero market requests occurred. `--execute` is
deliberately absent. The preview does not authorize adding it.

## Verification And Remaining Proof

VERIFIED_ENV final targeted command, exit 0:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_capture_descriptive_inputs.py tests/test_descriptive_candles.py tests/test_descriptive_metadata.py
```

SHOWN: **116 passed in 2.93s**: 34 new transport, 34 candle, 48 metadata cases.
Earlier transport slice: 116 passed in 3.03s before stage/type diagnostics were
added; final proof uses the submitted source. Fake transports/processes only.
Checks cover all 25 labels, known exclusions versus unknowns, no-tick gaps,
HTTP failures/no retry, redacted transport errors, byte/time budgets, clock
rollback, invalid plans/URLs, TLS/proxy/header policy, owned timeout/interrupt
cleanup including cleanup failure, tampered/forged receipts, unchanged inputs,
output reuse refusal and dry-run behavior. Test guards are not import/OS proof.

Next is exact independent or human review of this transport and plan. Then
separate bounded authorization would be needed for one actual public feasibility
capture; neither code acceptance nor the read-only preview grants it. No broad
warm-up backfill, repeated capture, schedule, server/account/credential, capital/
risk or trading change. No A/E/B freeze or market experiment, full suite, previous
backtest, random audit, dependency installation, commit or push. Statistical and
182-day study readiness remain INCOMPLETE.

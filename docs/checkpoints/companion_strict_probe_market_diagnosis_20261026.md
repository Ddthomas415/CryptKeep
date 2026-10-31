# Strict-Probe Market Diagnosis, October 26

Implementation role: ENGINEER. Risk: HIGH.
Separate GATE outcome: ACCEPTED_WITH_RISK, diagnosis/bounded harness proof only.
Runtime INCOMPLETE. No implementation or additional live operation.

## Actual producer path

Saved-result review V6H-DIAG-01 correctly found the standalone default snapshot
is not used by the strict probe. That counterexample stays preserved, not
promoted to a historical cause or used to widen the verifier whitelist.

Actual path: orchestrator.explain -> get_probe_tool_results -> memory.retrieve_context
-> _compute_market_summary -> _build_evidence_bundle -> verifier. The strict
branch never calls get_market_snapshot/_default_market_snapshot or ordinary
reasoning. Memory still reads market_ticks and attaches its summary, alongside
the frozen document evidence.

SHOWN with real handlers and synthetic in-process HTTP/DB seams:
- No market rows: market ok false/reason no_market_data, market_snapshot empty;
  all five verifier checks pass in the controlled archived-document fixture.
- One positive-price row: market ok true/latest_price/row timestamp and source;
  market_snapshot stays empty; verifier rejects bundle_market.
- One zero-price row: summary still ok true with row provenance; likewise
  rejected. Zero price alone is not no-market evidence.

Each case exercises real strict orchestrator/tools/memory/risk handlers and
bundle/verifier. Exactly two synthetic tool requests (memory POST/risk GET), one
synthetic market query and zero standalone snapshot/default/ordinary calls.
Reused fixtures bypass real Settings readers, SDK/storage constructors and
startup lifespans. All credentials/rows are synthetic. The first harness failed
to stub risk audit: review blocked three non-ASGI audit POST attempts, which
production swallowed. No external request completed in that guarded review;
the original run's exact attempt count was not measured. Its zero-attempt claim
is withdrawn. Preserved version: actual_runtime_v6h/strict_path_harness_v1.tar.

The first correction fixed risk audit, but v2 review REJECTED full counter
closure: the loaded fixture replaced counting socket guards with non-counting
guards. No network leak was found; the claimed swallowed-error detection was
incomplete. Preserved version: strict_path_harness_v2.tar; review unchanged.

Current harness makes no_native explicitly depend on loaded so counting hooks
are installed last, then asserts their real composed identities. It stubs risk
audit and blocks/counts non-ASGI HTTP, socket and process attempts during the
guarded test interval. A synthetic-object negative test deliberately swallows
a guard exception and proves teardown still raises. Import/setup before these
hooks is not included in that counter claim; reused loaded stubs remain in place.
This proves reachability with controlled inputs, not actual live row availability,
the precise rejected field or historical causation. Current health is unknown.

## Verification

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_v6h_strict_probe_contract.py
```

SHOWN current run: 5 passed in 1.16 seconds, ten existing FastAPI deprecation
warnings. Actual guarded test paths record zero forbidden attempts; the negative
case intentionally records a fake-object call only. Prior guarded review passed
3 in 0.71 seconds with three blocked audit attempts; it accepted diagnosis only,
not a wholly in-process/no-attempt harness. That review is preserved as
actual_runtime_v6h/strict_path_independent_review.json.
Diagnosis only, no production change, relaxed criterion, full suite or live replay.

Final narrow review closed V6H-STRICT-02: independently 5 passed in 0.70 seconds,
all six guard identities observed in all five cases, zero active-path attempts,
and fake-object swallowed-error detection verified. No old receipt/diagnosis or
other test module rerun. Prior v2 rejection remains valid for its earlier version.
Review: actual_runtime_v6h/strict_path_independent_review_v3.json, SHA256
6ec56cb19cca4f44262255adeedd3ff6c9dfee2ef93fa812d25a785a914e01f9.
Parent verified its five input bindings and all 20 unchanged runtime-consumer
hashes before this documentation-only closeout. Review-bound checkpoint digest
identifies pre-closeout text. Tests/reports/archives/reviews remain unchanged.

This closes offline diagnosis and bounded test-harness proof, not service
restoration. No unique historical cause, exact live payload or current health
is established. No production repair, retry or new operation is approved.

## Proposed Disposition, Not Implemented

Do not fix the unrelated fallback or accept populated prices merely to pass.
Instead make the special archival probe explicitly exclude market evidence,
using a truthful fixed exclusion marker checked narrowly by its verifier.
Preserve ordinary research market retrieval; no system-wide feature removal.
Keep prices absent, identity/protocol guards, archive/witness/citation checks,
all-five-true acceptance and timeouts intact.

Excluded by the archival probe must not be falsely described as no market data
in the database. This is a small producer/consumer contract decision, requiring
offline implementation, empty/populated/ordinary-path tests and independent
review before any new operation. No repair or operational authority here.

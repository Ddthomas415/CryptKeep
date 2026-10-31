# Paired Funding Cadence Repair

2026-10-29. Active role: ENGINEER. Risk: HIGH (monitor fail-open behavior).
Implementation: READY_FOR_INDEPENDENT_REVIEW. Operational rollout: INCOMPLETE.

## Operator Outcome

The existing cadence CLI can explicitly check raw paired funding capture using
an exact source and all required OKX native IDs. It no longer needs synthetic
legacy funding rates to recognize the new capture lane. No scheduled invocation
is changed and no original archive is accessed by this implementation/tests.

The default legacy table lane remains available. Future capture timestamps are
now missing rather than clamped to zero age in either lane. Store-error output
uses exception type only, not exception text/path/payload. Financial authority
is unchanged and always false in paired-cadence diagnostics.

## Design And Failure Matrix

Reuse the accepted journal's canonical stored-pair validator, including strict
JSON hooks. Read via SQLite mode=ro; do not construct the writer or initialize
tables. Source filtering is exact. A source row's journal append ID defines
recency. Every encountered envelope/key/index is validated BEFORE its symbol
can be used to discard or attribute it; unrelated-but-valid rows can be skipped.
For each requested native identity, only
the newest encountered row can satisfy the check; a failed attempt cannot be
hidden by an older success. All required identities must validate. The oldest
valid capture determines aggregate freshness under unchanged age thresholds.

- Valid canonical pair: explicit validated_okx_pair_capture lane; capture may
  be fresh while financial normalization/strategy/execution remain false.
- Another source/native ID or fresh legacy row: cannot substitute for a pair.
- Missing DB/table/identity: missing; no initialization or implicit fallback.
- Failed/latest SDK/partial attempt: not_a_successful_pair, not fresh.
- Corrupt body/key/wrapper/index, duplicate JSON keys, exponent overflow or
  excessive JSON nesting: diagnostic and fail closed; evidence untouched.
- Unattributable corruption encountered before coverage is resolved: no green
  result; explicit diagnostic. Corruption after the selected newest evidence
  is outside this bounded check, not declared absent or repaired.
- Future capture: fail closed even when another required ID has an older valid
  capture. Canonical UTC index timestamps are checked against the record.
- Stale capture: unchanged configured threshold; disabled checks remain disabled.
- Bounded window: default100source rows, configurable1-1000; max4MiB per fetched
  payload/8MiB aggregate decoding. Unseen identities remain missing and scan
  exhaustion is disclosed. SQLite query execution is not hard-time-bounded.

No DB connection, network, time-series experiment, process start, schedule,
credential, account, capital, strategy or risk setting is needed for the repair.
Tests use saved public parsing fixtures and disposable synthetic databases.
Future operational read-only SQLite use is not a promise about OS-wide absence
of all metadata/SHM side effects; the original archive was not opened here.

## Verification

VERIFIED_ENV consolidated command:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_okx_funding_cadence.py tests/test_edge_cadence.py tests/test_okx_funding_cli.py tests/test_run_crypto_edge_collector_loop.py tests/test_okx_funding_service.py tests/test_okx_funding_pair_producer.py tests/test_okx_funding_journal.py tests/test_okx_cash_cost.py tests/test_okx_funding_contract.py tests/test_synthetic_funding_observations.py tests/test_funding_receipts.py tests/test_funding_store_bridge.py tests/test_crypto_edge_collector_service.py
```

SHOWN final v2:354passed,8known slow-marker warnings,3.00s,exit0. Includes39new paired
cadence cases,11existing cadence cases and304previously reviewed source cases.
Initial v1:351passed2.90s; independent review REJECTED it as OKX-CADENCE-01
because unvalidated symbol attribution could discard a newer corrupt attempt
and let an older success report healthy. Rejected source/diff/hashes are saved
under v1. Two new regression cases fail against that saved v1 (expected test
exit1;2failed37deselected0.27s), then pass after canonical envelope/key/index
validation is moved before attribution. Legitimate unrelated rows still work.
Focused corrected slice:50passed0.88s. No full-suite,
real archive, collector restart, live freshness or financial-validation claim.
git diff --check passed for changed source/test/operator-doc paths.

The accepted previous rollout replay remains preserved unchanged: it records
the pre-repair legacy-only mismatch and is not overwritten to claim a rerun.
Exact changes against saved before-files and hashes are in
docs/review_artifacts/okx_funding_cadence_20261029/.

## Remaining Boundary

After independent acceptance, the operational next step is separately approved
full-family foreground validation with the original archive and fresh backup,
then a separate recurring decision, as recorded in
docs/checkpoints/okx_full_collector_rollout_20261029.md. Existing monitor jobs need
the explicit paired arguments when that rollout is authorized; no automatic
job update or default flip is hidden in this patch.

Assumptions: caller supplies the intended source/native universe; stored receipt
clocks/public responses are evidence, not independently authenticated freshness
or proof of financial semantics. No additional material assumption is needed.

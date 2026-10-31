# Funding receipt capture and opt-in journal path

2026-10-29 America/New_York. ENGINEER stage. HIGH risk financial evidence/runtime
source. Acceptance: READY_FOR_INDEPENDENT_REVIEW. No operational activation.

## Scope and preservation

Source-only integration of the separately reviewed raw decoder and store
bridge. The running collector, its plan/settings/schedule and default service
behavior are unchanged. New raw_funding_only mode defaults to False and requires
caller-supplied positive row and byte budgets. No CLI or installed job enables
it. Tests select this mode explicitly on disposable data.

This is not full Fix3 closure. The legacy funding path and alternative-data/
normalized-summary consumers retain their previously documented limitations.
No frozen experiment, historical record or rate formula was revised.

## Changes

- New collector function captures the SDK payload and request-start/receipt
  times, mapped requested symbol and method. It deep-copies the response before
  the next SDK call can mutate a reused object. JSON payloads with missing/
  invalid rates remain diagnostics, rather than being coerced to zero or lost.
  Failures return type-only reasons; clients close through the existing helper.
- Receipt-aware records use schema2; no-receipt schema1 output remains
  byte-semantics compatible with the frozen prototype. Native rate field names
  present in info and raw info.time are retained. Field presence and symbol/
  clock consistency are not authenticated native-to-unified semantic mapping.
- Decoder keeps caller capture time separate from exchange/settlement fields.
  A regressed local clock or mismatched response symbol is preserved as
  uncertainty, never used to authorize scoring. Every record remains unscored.
- Store readback reconstructs schema1 or schema2 without upgrading old rows.
  Comparison now uses canonical JSON rather than Python value equality, so
  boolean/numeric substitutions cannot pass as exactly equivalent evidence.
- Explicit raw service mode writes only the raw journal, never append_funding_rows.
  It refuses mixed raw/legacy capture contracts. Its report marks normalized
  funding unavailable (None/unknown), removes stale legacy funding metadata,
  and exposes raw diagnostics separately. Other report components are retained.
- Invalid mode/budgets and an oversized funding plan fail before SDK calls.
  Row/byte limits are persistence/input limits, not a certified HTTP/time budget.
  Existing public-client market loading/retries/timeouts are unchanged.

No new interval endpoint, strategy, order, private API client or retry job was
introduced. One fake SDK funding call per requested symbol was observed in
tests, not proof of a single HTTP request in a real SDK.

## Verification

VERIFIED_ENV: selected actual collector/service bodies and config dataclass,
fake exchanges/clock/symbol mapping/plan loader, full store module against
explicit temporary paths, socket/DNS/default-directory refusal. No actual
configuration, credential loader, SDK client or application entry imported.

    env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_funding_receipts.py tests/test_funding_store_bridge.py tests/test_synthetic_funding_observations.py tests/test_crypto_edge_store_sqlite.py

Final author result: 100 passed in 0.90s, exit0.
Initial96passed0.89s; an added receipt-type corruption case then failed
(1failed0.22s, DID NOT RAISE) because True == 1 under the prior equality check.
After canonical comparison and four added cases, all100passed.

Coverage includes fake fetch -> schema2 receipt -> real temporary SQLite ->
close/reopen -> diagnostic-only report; 1h/4h/8h and unknown intervals;
exact raw/native timestamps and symbol retention; invalid-rate diagnostics;
sanitized fetch failure/cleanup; explicit budgets and pre-fetch plan limit;
mixed capture refusal; reused response isolation; v1/v2 coexistence; unchanged
legacy default collector/service results; previous store/prototype regressions.

The legacy-default comparison is a bounded fixture comparison, not a full
system equivalence proof. No actual run_forever, full suite, price/backtest run,
HTTP trace, process-kill/power-loss, host or live database test performed.

## Review and operation boundary

Exact before copies of collector, service, decoder, store and affected bridge
test are preserved under docs/review_artifacts/funding_receipts_20261029/before/.
Earlier review hashes remain historical for those bytes; do not describe a
changed current source as still byte-identical to an old submission.
Original research prototype, original35tests and normalized/archive artifacts
are unchanged.

Freeze the diff/hashes for separate GATE review. Source acceptance would not
enable the mode or initialize a real database. Real use would perform the
previously disclosed additive raw-table DDL through store initialization;
that operation and any actual capture/collector change require authorization.

Remaining: verified venue/native-field semantics and formula/effective-interval
contract, normalized consumer repair, actual SDK/request/source evidence,
operational path/budgets, authorized initialization/capture and independent
runtime proof. Default legacy readers can still produce old unverified
estimates; this opt-in source patch is not a claim they are repaired.

No installed job/config/source plan, collector state/process, real schema/
migration/database, account/credential, public data capture, trading/capital/
risk, dependency, commit or push operation changed.

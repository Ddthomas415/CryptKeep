# Legacy funding archive reporting and display correction

2026-10-29 America/New_York. ENGINEER stage, HIGH risk financial reporting.
Acceptance: READY_FOR_INDEPENDENT_REVIEW. Offline source proof only.

## Shown defect

A legacy archive row containing rate0.0001/interval8 produced10.95% annualized
without source/effective-interval qualification. New report regression failed
before repair (1failed0.21s). Several views also converted missing estimates to
0.00%/flat, or reused cached numeric claims and funding deltas.

Chosen path: preserve stored rows and the frozen uniform-interval modelling
function; stop presenting unqualified archive economics as verified reports.
No historical field/source/interval can be reconstructed from absent evidence.

## Source changes

- build_crypto_edge_report now uses an unverified-funding summary. Original
  rows are deep-copied into diagnostics, counts retained; average/last/annualized
  rates and sign ratios are None, direction unknown and eligibility false.
  A caller's model interval or claimed eligibility cannot authenticate them.
- summarize_funding_carry itself is byte-semantics/AST unchanged. It remains
  the old uniform-interval modelling API for reproducibility, not a verified
  archive consumer. Existing model tests retain their arithmetic expectations.
- Store funding history preserves capture/source/snapshot/count metadata but
  no longer replaces unavailable estimates/ratios with zero. No persisted row,
  payload, schema, index or journal was changed by this reporting repair.
- Shared funding_display returns N/A/Unknown for current supported inputs,
  including cached numbers and untrusted qualification flags. No supported
  verified-normalization contract exists yet; this is deliberately not a
  formatter that can be enabled by a boolean assertion.
- Research and Operations funding cards, structural summary metrics, digest
  funding summary, workspace funding text and funding trend use that guard.
  Cached funding yield comparisons are explicitly unverified, not numeric
  changes. Non-funding basis/dislocation displays retain their behavior.

Impact: collection, raw evidence, counts, non-funding analytics and explicit
legacy model arithmetic remain available. Qualified funding economics are
withheld pending an evidenced contract, not replaced by an optimistic zero,
and funding research is not retired.

## Verification

VERIFIED_ENV: real reporting/store/workspace functions with disposable SQLite
or fake stores; existing fixtures use explicit temporary paths. New tests
refuse sockets/DNS/default-directory initialization. Dashboard cards/component/
digest checks select actual AST expressions/functions without executing page
auth, Streamlit rendering, buttons or services.

    env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_funding_archive_views.py tests/test_crypto_edge_analytics.py tests/test_crypto_edge_store_sqlite.py tests/test_dashboard_crypto_edge_research.py tests/test_funding_consumers.py tests/test_funding_receipts.py tests/test_funding_store_bridge.py tests/test_synthetic_funding_observations.py tests/test_funding_provenance_boundary.py

Final author216passed1.95s,exit0. Initial26passed0.91s preceded the expanded
archive/view matrix. Tests cover unknown/zero/mixed-interval/claimed-qualified
data, raw-copy isolation, exact legacy row preservation after report/history
reads, stale numeric/None/nonfinite cache guards across cards/component/digest,
funding-trend suppression and preserved basis values. Old report is retained
as a negative control; unchanged legacy model AST/results are compared at
1h/4h/8h. Prior receipt/store/advisory suites included.

Two existing test expectations changed: history is unqualified instead of
increasing annualized carry, and a fake unverified long-pays field no longer
becomes a live summary assertion. Original tests are archived. The old direct
model diagnostic was renamed to identify that legacy API, not falsely report
the repaired archive reader as a new unresolved defect.

Not run: full suite, actual Streamlit/auth rendering, host/service/collector
check, real database access, API capture, price/backtest run or experiment.

## Preservation and handoff

Before sources/tests are preserved in
docs/review_artifacts/funding_archive_views_20261029/before/.
Changes are limited to reporting boundaries, display expressions and their
tests. No model rule, original study artifact or stored history was overwritten.
Prior review hashes are historical for their archived versions, not claims
that changed current report/store files are still old accepted bytes.

Freeze exact source/test/diff bindings for a separate GATE. This implementing
thread cannot independently accept the high-risk reporting change.

Remaining original Fix3: source/native/effective-interval semantics and validated
normalization, legacy collector and context-replay/model qualification, and any
authorized raw-mode schema/capture/runtime proof. Direct legacy modelling APIs
are not global security/eligibility boundaries.

No actual account/credential/config/API capture, collector/service/scheduler/
pilot, real database/schema/migration, trading/capital/risk, dependency,
commit/push or saved-result change occurred.

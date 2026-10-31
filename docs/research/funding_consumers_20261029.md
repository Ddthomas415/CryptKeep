# Funding advisory consumers: exclude unqualified rates

2026-10-29 America/New_York. ENGINEER stage, HIGH risk financial/advisory logic.
Acceptance: READY_FOR_INDEPENDENT_REVIEW. Working-copy source and offline proof,
not deployed runtime or complete original Fix3 acceptance.

## Evidence and scope

SHOWN: a fake current-reader response with fundingRate0.0001 and no interval
produced annualized10.95 and a neutral signal. New regression failed before
repair (1failed0.19s, expected None but got10.95). Raw rate collection did not
establish a common interval or crowding basis.

Opened the primary API documentation and inspected installed CCXT parser:
Binance documents lastFundingRate as its latest funding rate and exposes
nextFundingTime separately. CCXT maps them to fundingRate/fundingTimestamp.
That evidence does not itself establish a settled payment or its effective
interval for every response.
[Binance API](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data#mark-price).

The opened official OKX mechanism page describes interval dependence and
adjustable settlement frequency. Its documentation is not a historical field/
contract certification.
[OKX mechanism](https://www.okx.com/en-au/help/perps-funding-fee-mechanism).

The earlier cash-cost versus crowding distinction still applies. This patch
does not choose a guessed normalizer or certify a new funding signal.

## Repair

- Existing alternative_data.get_funding_rates now returns raw rate percent
  and schema2 receipt/provenance using the reviewed decoder. Its normalized
  rate_pct and annualized fields are None; signal is unknown and normalization
  eligibility false. Missing rates remain diagnostics rather than zero.
  Even explicit intervals do not establish a verified crowding basis.
- Fetch/setup/close failures are visible with type-only errors. A close error
  does not erase already captured observations. complete concerns raw capture,
  not funding eligibility. No new API endpoint/interval request was added.
- Ranker funding_input explicitly excludes structured or declared-eligibility
  observations; a caller's True flag cannot qualify them. Other scoring
  components continue. Missing/unverified funding has a None breakdown entry
  and explicit reason, not a neutral financial interpretation.
- Unmarked finite numeric inputs retain the old per-print model for frozen
  fixture compatibility, with legacy_unverified status. They are NOT certified
  live inputs. This compatibility lane remains a limitation, not a global
  guarantee that arbitrary callers cannot submit old unqualified rows.
- Market Intelligence page does not call the strategy for unqualified or
  cached legacy rows; action is None and the reason is visible. Raw percent
  remains shown. Nested provenance uses JSON display rather than forcing
  heterogeneous provider dictionaries into a tabular column.

Impact: funding collection/diagnostics and non-funding ranking remain available.
The current reader cannot produce a qualified funding strategy action until
a separately evidenced normalization/semantic contract is implemented. It
does not retire funding research or alter funding_extreme's frozen rules.
No capital/execution authority is introduced or changed.

## Verification

VERIFIED_ENV: real reader/ranker modules with fake SDK factory/method/clock,
socket/DNS refusal, no actual client, credentials, config or application entry.
Dashboard check executes only the actual selected funding loop, not auth/
Streamlit. Existing receipt/store suites use explicit disposable SQLite.

    env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_funding_consumers.py tests/test_funding_receipts.py tests/test_funding_store_bridge.py tests/test_synthetic_funding_observations.py tests/test_crypto_edge_store_sqlite.py tests/test_funding_provenance_boundary.py

Author final153passed1.30s,exit0. Includes45new consumer cases,100previous
receipt/store/prototype cases,8historical/current defect diagnostics.
Checks cover unknown/1h/4h/8h, positive/negative/zero/invalid rates, finite
percent overflow, raw/source/time retention, errors/cleanup/completeness,
untrusted eligibility flags, old model score parity at eight thresholds,
unchanged other score components and selected dashboard suppression.

Archived dashboard loop is a negative control. The diagnostic suite's old
alternative-data reproduction now explicitly loads the preserved pre-change
source; its assertions were not rewritten to imply a repair. Other remaining
legacy collector/summary defects continue to be reproduced, not called fixed.

No full suite, real provider/HTTP trace, actual dashboard rendering, market
comparison/backtest, fee change, database/history update or operational run.

## Preservation and remaining work

Exact pre-change reader/ranker/page/diagnostic test are archived under
docs/review_artifacts/funding_consumers_20261029/before/.
Historical hashes are for those bytes, not changed current sources. No saved
results or criteria were replaced or rerun. One guessed nonexistent test/context
path during inspection was not read; no absent source claimed verified.

Remaining original Fix3: interval/field/effective-time and cash/crowding
qualification, legacy collector/default archive summaries and downstream views,
actual provider/runtime proof and any authorized activation of raw collection.
This reader retains public observations in its returned snapshot, not a new
durable job. Existing public Binance route/SDK retry/HTTP-budget posture remains
unchanged and unverified here.

No real account/credential/API capture, collector/service/scheduler/pilot,
schema/migration/production database, trading/capital/risk setting, dependency,
commit/push or model-result modification. Freeze exact diff and dependencies
for separate GATE; source author cannot independently accept this work.

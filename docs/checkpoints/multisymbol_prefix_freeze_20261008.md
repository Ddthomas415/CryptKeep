# Bounded backfill and frozen research prefixes

Role: ENGINEER. Risk: HIGH for financial evidence consistency.
Separate GATE: ACCEPTED_WITH_RISK for prefix freeze/verification only.

The operator requested bounded public backfill, dataset-prefix freezing, then
discovery. Existing archive backfill tooling is used with no credentials, five
exact OKX spot markets, hourly data, 30 pages/300 rows per page and at most
6,852 rows per market. Inclusive last candle is 2026-09-30 23:00 UTC. The
separate database is research/multisymbol_baseline_v1/public_archive.sqlite.
No default archive, campaign, service or account is mutated.

Public probe succeeded outside the network sandbox. A sandbox NetworkError was
not treated as authentication failure. Backfill summaries describe downloaded
rows; strict hourly completeness must be checked before economic execution.

New prefix freeze reads discovery, validation and final prefixes separately and
requires exact nesting before publishing hashes. Simulation requires a manifest
whose plan/snapshot identifiers and current-phase row hash match before any
signal computation. Changed historical data cannot quietly change carried
cash/positions. The manifest is content identity, not authenticity proof.

Selected implementation fingerprints in the strategy snapshot were updated
before any economic results to include this reviewed dependency. Signal preset
configurations, fee scenarios, universe, dates and carry-forward policy were
not changed. Missing or invalid data is never substituted.

SHOWN: 40 tests passed in 0.41 seconds with isolated state:

```sh
CBP_STATE_DIR=/private/tmp/multisymbol-prefix-tests-20261008 PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest --noconftest -q -p no:cacheprovider tests/test_multisymbol_archive_runner.py tests/test_next_open_research.py tests/test_frozen_strategy_comparison.py
```

UNVERIFIED until completion is recorded: all-market download/grid coverage,
published real dataset manifest and discovery simulation. Independent review
is requested before using the new prefix guard for financial results. Full
suite, CI and deployment are not run. Exclusive output creation is not atomic
crash-safe publication; partial JSON fails closed and must not be overwritten
silently. No candidate selection, promotion or profitability claim follows.

Separate reviewer independently reproduced 40 passed in 0.33 seconds with no
blocker. Accepted use requires the same preserved manifest across phases;
the runner records its hash but cannot prevent operator replacement/regeneration.
Source and row hashes do not attest exchange-data authenticity. No download or
economic result was independently inspected in this bounded review.

## Completed data ingestion and freeze

SHOWN: bounded public backfill completed for all five markets, each with 6,852
hourly rows. Strict phase reads and nested-prefix validation succeeded for all
markets: discovery 4,644, validation 6,132, final 6,852 rows, including 300 warmup
bars. These are exact registered ranges, not completeness inferred from counts
alone. Public instrument/candle calls used no account credentials.

Preserved manifest: research/multisymbol_baseline_v1/dataset.freeze.json.
SHA256: 907768a3d839232e847dd1e9f62d5bd0c261572c062f7ae32790ced6172bac30.
Backfill receipts are the five *_backfill_20261008.json files in that directory.
The same manifest must be used for any later phase; do not regenerate it to
accommodate changed data. Original default/campaign archive was not written.

Discovery-only simulation was started after separate acceptance of the prefix
guard and successful freeze. Validation/final signals were not evaluated.

Discovery completed: all five markets MODELLED_RESULTS. Full artifact:
research/multisymbol_baseline_v1/discovery_20261008.json. All 75 strategy/control
cost outcomes passed local accounting/hash checks. Base 25bps fee+5bps slippage:
all15 strategy/coin arms negative. No profitability/promotion conclusion follows.
See docs/research/multisymbol_discovery_results_20261008.md for the full table,
open-position and cost caveats. Validation/final remain unevaluated.

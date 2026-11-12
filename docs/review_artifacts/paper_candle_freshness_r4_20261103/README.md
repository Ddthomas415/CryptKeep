# R4 hourly-candle source boundary

Date/status check: 2026-11-04T02:36:57Z, current work log/git. Active role: ENGINEER, HIGH risk.
Bot relation: BOT_RULES; runtime configuration/process/host state NOT checked.
Author: READY_FOR_INDEPENDENT_REVIEW, self-checked. No actual profile activation or operation.

**Independent initial GATE: REJECTED**, 2026-11-04T02:15:20Z. A successful diagnostic write can delay a
buy from age119 to121 after the last TTL sample and still commit a fill. See `independent_review/README.md`
and its unchanged regression probe. The original 839-pass candidate is preserved as `rejected_stage.diff`,
`rejected_hashes.json` and `rejected/storage/paper_trading_sqlite.py`. The one bounded correction is complete.

**Bounded correction submitted:** the original pre-diagnostic expiry check remains, followed by a second
canonical deadline check after successful diagnostics and before candle refusal/accounting. Fill evidence uses
that refreshed clock. Corrected affected selection: **480 passed / one deselected in 10.84s**,
`corrected_affected.txt`, including the original unchanged deadline probe. The deselected case pins the initial
candidate's literal seal hashes; it is preserved, not rewritten to pass. Corrected seal is checked separately.
Worker's seven added delay-boundary cases yielded six failures/one pass on rejected source and all 53 boundary
cases pass after correction; raw receipts are saved as `rejected_delay_cases.txt` and `worker_corrected_boundary.txt`.
Those worker receipts are attributed/self-checked and overlap the main selection. No corrected 839/full-suite claim.

Corrected `stage.diff` SHA256 `2378d23335498e035a5d84eeb12a306c4a62b4c633e52ab9e78d333c6cb8e2ea`;
`hashes.json` SHA256 `5f4c5cd56362be5ac9379ddf12f15d2092a099cca93ca344f2d38ef15c86dbfe`.
Original reviewer probe SHA256 remains `336d03bc651df8fd26c7acaad97bd69c8db495e02fd3de5dde13d493f05ef378`.
**SHOWN: Separate GATE ACCEPTED_WITH_RISK for the sealed buy guard and TTL correction only.**
The [correction review](independent_review/correction_review.md) reports 101 passed / one old-seal pin
deselected, including four unchanged behavioral probes; all nine corrected source/test hashes matched.
Complete invalid-feed diagnostic archiving remains **INCOMPLETE**.

## Outcome

Frozen R4 rule, not a new strategy: new buys refuse stale/gapped/invalid hourly candles; candle quality never
blocks sells. The source capability is explicit `paper_trading.require_fresh_hourly_candles`, default **false**,
so non-hourly/legacy paper workflows remain unchanged. True enables the hourly simulation boundary;
malformed values refuse buys, not engine construction or sells. Actual setup/configuration needs separate approval.

- DONE, source/self-checked: pure assessment of the required sixty-hour window, original open time, completeness,
  missing hours and bad OHLCV. Within 300 seconds after the UTC hour opens, a missing current forming candle
  permits checking the preceding sixty complete hours; after 300 seconds it is required and reported missing.
  With the current candle present, the window ends there. Forming remains forming; signal rules are unchanged.
- DONE, source/self-checked: reuse the existing cache. Its v3 envelope adds venue/symbol/timeframe, preserving
  ordinary legacy readers and actual source labels. Unknown/legacy/sample/mismatched/unreadable/oversized cache
  cannot authorize a guarded buy. There is a 1 MiB read budget and market-path validation, not a new fetcher.
- DONE, source/self-checked: guarded submission reads the cache. Atomic fill independently reads the canonical
  order/account cache under the ledger writer lock, samples TTL after reading, and preserves filled/terminal/fence
  precedence. Expiry is rechecked after diagnostic writes; this is not a bound on physical commit time.
- DONE, source/self-checked: failed candle verdict rejects an active buy with reason and durable diagnostic.
  A diagnostic-write failure rolls back, returns unresolved, does not fill or falsely count a terminal refusal,
  and does not abort evaluation of other orders. Sells do not read candles or expire. Normal queue reconciliation
  retains the rejection reason and attempts existing alerts; a skipped alert is not delivery.
- PARTLY DONE, source/self-checked: opt-in decision archives retain whitelisted candle diagnostics in
  otherwise valid, serializable records and bind the loaded assessor/module constants into code identity.
  The synthetic [probe](diagnostic_probe.py) and [receipt](invalid_input_recording_detail.txt) show that a
  NaN close yields `invalid_ohlcv`, but strict archive validation rejects the whole decision record with
  `ValueError`. No separate diagnostic is retained for that case. The GATE inspected the compact receipt,
  not a rerun of this probe. The sanitizer remains unchanged; no diagnostic-only event repair was started.
- PARTLY DONE: full R4. Quote completeness/age/source and bid/ask/mid at every fill, actual publisher/data coverage,
  configuration/cadence/capacity and delivery/commissioning remain open. This does not certify a current bot.
- NOT DONE: configuration change, collector/job/service startup, deployment, account access, market experiment,
  strategy/capital/risk-setting change, historical data repair, commit/push or profitability claim.

## Evidence And Corrections

VERIFIED_ENV for isolated Python/temp SQLite, synthetic rows/router/quotes/alerts; no network or private configs.
Rejected candidate's seventeen-file selection: **839 passed in 29.96s**, zero failures/errors/skips, `consolidated.txt`.
It covers the new assessor/real-cache/serialized-boundary cases, existing provenance/capture/replay, multi-symbol,
runner, R8/R12 fill/expiry, account and valuation cases. Predecessor 148/46/42 counts overlap, not added.

Four real pipeline cases with preserved original submission/fill methods: **4 expected failures, 40 deselected,
0.46s** (`before_probes.txt`). Old methods permit stale/gapped/zero candles at submission and a fill after the
cache becomes gapped. A test-only shim removes only the newly introduced keyword when invoking the original
fill body; original production files are not swapped. No import/API-error failure is called behavioral proof.

Development disclosure: first integration run 89 passed/one archive-field assertion failed because `_public`
removed the newly whitelisted fields; projection now sanitizes each explicitly allowed value without widening
the global whitelist. Main inspection also found diagnostic-write failure could precede required TTL expiry;
the worker moved expiry before diagnostic persistence and added four regressions. The worker reported four
pre-correction failures but did not preserve a separate initial-method artifact/receipt; that count remains
CLAIMED by the worker, not independently inspectable proof. Main's four original-pipeline failures are preserved.

Consolidated command, repository root:

```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_STATE_DIR=/private/tmp/cbp-candle-consolidated \
  CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_hourly_candle_quality.py tests/test_paper_candle_fill_boundary.py \
  tests/test_ohlcv_snapshot_provenance.py tests/test_runner_decision_capture.py \
  tests/test_runner_decision_kernel.py tests/test_runner_multi_symbol_integration.py \
  tests/test_strategy_runtime_runner.py tests/test_pending_paper_exit_integration.py \
  tests/test_paper_exit_atomicity.py tests/test_paper_buy_fill_expiry.py \
  tests/test_paper_buy_lifecycle.py tests/test_paper_engine_integration.py \
  tests/test_paper_engine_honesty.py tests/test_paper_engine_limit_and_status.py \
  tests/test_paper_account_reconciliation.py tests/test_paper_account_snapshot.py \
  tests/test_paper_missing_price_valuation.py --tb=short
```

Before proof adds `CBP_CANDLE_BEFORE_ROOT=docs/review_artifacts/paper_candle_freshness_r4_20261103/before`
and selects `tests/test_hourly_candle_quality.py -k 'enabled_profile_refuses or fresh_at_submit'`.
`seal.py` preserves the five production baselines, uses HEAD only for the previously unmodified provenance test,
and emits the nine-file incremental diff/hashes. Public source only; unrelated dirty changes are excluded.

## Required Review And Limits

Independently check 300-second/sixty-hour conventions, identity/read failure behavior, guards at both boundaries,
canonical account/market and locked read placement, expiry/evidence precedence, sell isolation, disabled-profile
compatibility, capture sanitation/loaded identity and refusal/alert integration. A concrete counterexample or
changed seal can overturn source acceptance. No current raw exchange or live execution conclusion follows.

Cache labels are producer assertions, not authenticated exchange identity; mappings/current configuration are
uninspected. Normal cache replacement is atomic, but arbitrary external rewrites after a read are not fenced by
a cross-filesystem transaction. File-size budget is not an interruptible I/O deadline. Full-history reads under
the paper lock and source/profile deployment need intended-host checks before operation. Failed diagnostic
writes can leave a buy unresolved until expiry/recovery; no guarantee of durable evidence on a broken store.
Direct API clients without queue intents must consume their returned refusal; normal alert proofs are for the
registered queued pipeline. Intra-hour refresh liveness is not inferred from the presence of a current candle.
Decision diagnostics are observed/hashed metadata, not a new historical market-data study or a regraded result.
No supported symbol is removed. Sample/legacy caches are still readable by their old consumers; they simply
cannot authorize buys in the opt-in public-hourly profile.

What do I know that could change the owner's decision that I have not yet said?

Answer: these tests demonstrate an opt-in source boundary, not an enabled running simulation. Default-off
means deployment/setup must explicitly select it; otherwise existing paper behavior remains unchanged.
Invalid-feed diagnostics are not retained when the raw record fails validation. The correction budget is used;
a diagnostic-only receipt needs a new bounded pass without weakening validation. Actual data, quote freshness,
fill quote evidence and commissioning still need their accepted evidence lanes.

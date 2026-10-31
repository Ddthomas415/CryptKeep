# ED-002 input feasibility and candle receipts

2026-10-28. Active role ENGINEER after bounded source-fit inspection.
Risk HIGH: research availability/provenance. READY_FOR_INDEPENDENT_REVIEW.
Study/data readiness INCOMPLETE; no dates frozen, acquisition or scoring run.

## Approval And Practical Finding

Operator replied "approve. carry out the next steps" to the submitted descriptive
report. Record human ACCEPTED_WITH_RISK for its exact synthetic implementation,
not independent review or observed profit. Submitted report source remains
`f600940d9db7b5bdafe278253d00de86017fdf8c40d379f8fd3e4e26db279130`.

SHOWN in the inspected source: the existing confirmation runner explicitly
accepts only its five-market baskets. Its bounded batch wrapper delegates to
that contract. Do not widen the registered experiment or change its source
hashes merely to collect this new study. [Contract checks](../../scripts/research/run_coinbase_confirmation.py).

SHOWN: the general archive has OHLCV values but no first-receipt/raw-response
fields, and writes `INSERT OR REPLACE`. Its normalizer also coalesces duplicate
timestamps. Content hashes alone cannot recover when a candle was first known.
These are fit limits for this prospective contract, not new defects in the
historical studies or reasons to migrate/delete their data.
[Schema/write path](../../storage/market_store_sqlite.py),
[archive normalization](../../services/backtest/ohlcv_archive.py).

SHOWN: existing listing probes demonstrate exclusive raw-response files and
send/receive/hash manifests. They are not directly suitable for this protocol:
one is a fixed listing probe, the other searches daily history with retries and
resumable state. Reuse the capture pattern, not their study, dates or commands.
[Probe](../../scripts/research/probe_coinbase_listings.py),
[daily search](../../scripts/research/fetch_coinbase_listing_dates.py).

Saved October 27 metadata is dated evidence only. Its one-hour model permission
has expired; 24 online candidates at that receipt are not 24 current approvals.
The previously audited hourly archives end October 9 and carry no observation
times. Current 25-symbol warm-up/receipt coverage remains UNVERIFIED, not proven
missing everywhere. No live database, processes or schedulers were inspected.

## Small Implemented Gap

Added `services/backtest/descriptive_candles.py`: a pure adapter of caller-supplied
raw candle responses to the existing panel's `row` / `known_at_ms` records.
No HTTP, filesystem writer, background task, database migration or new simulator.

- Exact declared product mapping and identity references; unresolved symbols
  stay in coverage. Supplied identity hashes are not independently authenticated.
- Require the recorded public Coinbase product URL, GET method and hourly
  granularity; a daily listing-study response cannot be relabelled hourly just
  because its timestamps happen to fall on an hour. This validates the supplied
  receipt structure, not that an untrusted caller recorded it truthfully.
- Decode raw Coinbase `[time,low,high,open,close,volume]` into the existing
  millisecond OHLCV order, validating aligned integral times and finite ranges.
- Preserve raw-body hashes and receipts. A candle is usable only after completion
  at its actual supplied receipt, not at an invented publication time. Repeated
  equal numeric versions keep the earliest supplied completed receipt.
- Ignore forming/out-of-window rows and future captures as explicitly counted
  diagnostics. Future data cannot repair or corrupt a previously selected cutoff.
- Conflicting completed versions make that hour unknown; retain both versions
  and their source hashes. Never choose a revision using returns. Malformed/HTTP
  failures remain explicit errors. A failed request does not erase an already
  valid observation or make an observed complete window permanently fail; a
  still-missing/conflicting hour remains INCOMPLETE. Completeness of a requested
  window is distinct from success of every attempted request.
- No interpolation or zero-volume candle insertion. Window completeness is a
  data audit, NOT a new all-assets trading gate: the unchanged bridge separately
  skips documented ineligible flat assets. Missing MATIC candles must not narrow
  scope, force a POL substitution, or make it necessary to trade MATIC.

## Endpoint Fit And Resource Estimate

Opened official Coinbase documentation, not a market endpoint: hourly granularity
is supported, a response has at most 300 candles, may include earlier rows, and
no-tick intervals can be absent. Raw receipts are necessary but cannot guarantee
continuous prices or real fills.
[Coinbase candle reference](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles).

Planning arithmetic only: 300 warm-up hours for each eligible default asset,
with 1464 hours for BTC and ETH's 61-day incumbent history, means 9828 rows if
all 25 are eligible, or 9528 for the dated 24-candidate case. At most 300 rows per
request gives nominal 33 or 32 candle pages, plus metadata; this is a lower-bound
page estimate, not guaranteed coverage or an authorized request budget. Inclusive
window boundaries, omissions or failed responses can require a new bounded plan.

Hourly monitoring would nominally require one product snapshot plus up to 25
candle requests per hour: at most 26 per cycle, 113568 over 4368 evaluation hours,
excluding warm-up/currency metadata. This is request-count arithmetic, not a
vendor quota, promised service cost or approved automation. No purchased feed,
new service layer or scheduler is justified by this inspection alone.

## Verification And Next Boundary

VERIFIED_ENV, exit 0:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_descriptive_candles.py tests/test_descriptive_metadata.py
```

SHOWN: 82 passed in 2.54s (34 new candle / 48 accepted mapper cases). Invented
bytes only: raw-column order, hashes/times, forming/revised/equal versions,
nonfinite/invalid rows, duplicates, empty responses, HTTP failures, wrong product,
daily/unrelated route rejection, causal prefix isolation, later valid observation,
25 coverage labels and actual HourlyPanel cutoff rejection. Initial development
slices passed 74 then 80 cases before these final boundary checks. No strategy call,
return calculation, old backtest, random calibration, live API or full suite.
Test-body external-work guards are not system-wide import/process certification.

Next after exact adapter review: prepare a bounded, foreground-only public
capture using the existing raw-response pattern and this adapter, with explicit
request/body/time caps, verified TLS, no credentials/retries/redirects and
exclusive new artifacts. Its transport still needs implementation/review; no
capture command is certified or authorized by this note. Preserve original
archives/registrations and record any partial failure. Demonstrate availability,
identity and warm-up before future freeze/A/E/B; do not manufacture dates now.
No service/schedule/account/credential/risk/capital/trading, commit or push change.

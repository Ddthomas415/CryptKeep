# ED-002 saved-input inventory

2026-10-27 New York. Active role AUDITOR. Acceptance: ACCEPTED for the
bounded metadata/index inventory only. Experiment activation: INCOMPLETE.

## Answer

Saved inputs are not limited to BTC/ETH. All25 configured labels have one
same-base USD product candidate in the saved Coinbase product response.
At that response's October19 timestamp,24were online and MATIC-USD was delisted
with trading disabled. The archive checksum index lists24corresponding hourly
files in each of its two Coinbase windows, with MATIC absent. These are metadata
and filename findings, NOT a fresh market check, complete-candle verification
or proof that24assets are eligible for a future experiment.

No new simulator is needed. Next data proof is bounded row/timestamp/availability
verification of existing archives and an explicit venue-to-model metadata
contract. No raw candles, returns or strategy outcomes were examined here.
The indexed archives are described as ending before the proposed future test;
they cannot supply its future outcomes or guarantee its eventual warm-up. This
was not an exhaustive search of every later data capture in the repository.

## What Is Shown And What Is Not

| Evidence lane | SHOWN in saved inputs | Remaining limit |
| --- | --- | --- |
| Declared scope |25unique labels from tier1/tier2/watchlist; none removed | Config ticker labels do not independently establish cross-venue token identity |
| Saved products |25unique same-base USD candidates;24online,1delisted | Status observed2026-10-19T05:47:42.446478Z, not current or a valid-through interval |
| Saved currencies | Matching venue currency records and USD precision metadata | Currency response is2026-10-19T06:02:09.822189Z; not an atomic observation with products |
| Prior identity sidecar |22labels have mapped CMC references in identity_map_v3 | BTC/ETH/JTO are absent from that particular sidecar, not absent from Coinbase; CMC IDs are not mandatory for an exchange-only study |
| Hourly archive indexes |24matching names in cb/h1 and24in cb2/h1; MATIC absent | Payloads, row counts, timestamps, gaps and observation availability were not checked |
| Venue precision/minima | Base/quote increments and min_market_funds recorded for all25 | These require semantic interpretation; no executable model-rule records were generated |
| Future confirmation | No activation/data record supplied for this proposal | Old archives remain reused history, not future outcomes or an untouched holdout |

Exact per-label metadata, index entries and source hashes are in
`ed002_defaults25_saved_input_inventory_20261027.json`.

## Documentation Check: Avoid Invented Missing-Field Blockers

SHOWN in the opened official documentation: Coinbase removed `base_min_size`
in2022; quantity-specified market orders and limit notional checks have different
rules. Therefore the missing field is not itself a reason to reject all25.
Do not silently invent a positive quantity minimum or treat currency `min_size`
as a market-order rule. [Exchange changelog](https://docs.cdp.coinbase.com/exchange/changes/changelog#2022-jun-02).

SHOWN: `base_increment` concerns base quantity increments; `quote_increment`
is the order-price tick. Treating the latter as the ledger's cash-rounding step
would conflate two different quantities. The saved USD currency record supplies
`max_precision=0.01`, but this inventory does not certify fee/fill settlement
rounding from that field. `min_market_funds` also must not be blindly applied to
every modelled order. The bridge accepts caller rules; no such mapper was
implemented or found defective in this task. [Product reference](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-all-known-trading-pairs), [currency reference](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/currencies/get-all-known-currencies).

The missing `view_only` property is recorded as absent, not false. This is an
Exchange response, not an Advanced Trade/account permission object. Do not
require a different API's field without deciding which contract is being used,
or equate public product metadata with geographic/account trading entitlement.
No conclusion about live routing or account permission follows.

These observations correct potential input interpretations; no new financial
mapping, rounding policy or venue eligibility is adopted here.

## Recommendation And Next Bounded Scope

Keep all25in scope. For MATIC, preserve the dated exclusion evidence; do not
substitute POL or remove its row. Keep the24archived product candidates available
for input validation rather than re-downloading or repeating backtests.

Recommended next check: existing archived candle timestamps, row hashes and
gaps only, with no signal evaluation or returns. Separately specify a
quantity-specified market model and its explicit amount-rounding policy from
documented semantics, before constructing model `rules`. No new precision
assumption, request to Coinbase, account read or paid source is authorized by
this inventory. Statistical calibration/protocol adoption still remain open.
Before treating the October19 product snapshot as current feasibility, request
one fresh public metadata capture: at most two GETs (`/products`, `/currencies`),
ten seconds each within30seconds, no retries/auth/credentials, append-only output.
This proposed capture does not fetch candles, score strategies or activate a job.

No material assumptions were used to fill unknowns. Index presence is not
substituted for completeness, snapshot time for historical validity, or old
identity sidecar absence for proof of an unlisted asset.

## Verification And Preservation

VERIFIED_ENV: local standard-library JSON/text reads, distinct asset/product
counts and SHA256 checks against saved receipt/identity bindings. The generated
JSON records exact inputs and verification counts. Source hashes bind this
inventory, not the completeness or correctness of the upstream observations.

No pytest was run: no source or financial behavior changed. No raw candle/archive
payload was opened, extracted or rehashed, and no SQL/market-data simulation,
statistical calibration, price API, account/credential/service/scheduler, capital
or risk operation occurred. Public official documentation was read on the web;
that is separate from market-data collection. Prior proof/results/registries and
the independently accepted bridge are unchanged. No commit or push.

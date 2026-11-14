# Shared Coinbase precision repair

Bot relation: BOT_RULES. Current runtime configuration not inspected or changed.
Checked Git/latest work log2026-11-14T10:43:31Z. HIGH risk; separate Nash final
GATE10:41:32Z ACCEPTED_WITH_RISK for source/synthetic scope. All four accepted
hashes match SOURCE_SHA256SUMS. R10 remains STOPPED.

## Owner direction and scope

Owner continued the explicit recommendation to correct the shared/legacy
provider, source-only, after the accepted paper-opt-in implementation. This
completes O162's shared-fetch portion, not a cache migration or deployment.
No real HTTP, cache refresh, account/credential, configuration, service, host,
scheduler, trading, backup, installation, commit or push operation was performed.

## Source correction

SHOWN: installed CCXT4.5.48 Coinbase uses TICK_SIZE4. Native increments1 and2
were translated by the old default into0.1 and0.01. The previously reviewed
paper-only strict path was correct; default/explicitFalse callers were not.

The shared provider now applies the native-increment validator to every call.
The keyword strict_precision remains compatible, including explicitFalse, but
cannot re-enable the wrong decimal-count branch. Invalid keyword types or
missing/unknown precision modes refuse active rules. Quantity and price increments
must be finite, positive, representable, and agree with native fields. Native
price_increment retains precedence over quote_increment. Requested canonical
symbol, native market ID and raw product ID must agree; a raw id alias remains
supported. No raw product payload or credentials are emitted.

Only services/markets/fetch_coinbase_ccxt.py changes in production. Other venues,
quantization, cache schema/TTL, rules/get/validate APIs and actual settings are
unchanged. Existing paper_coinbase_precision calls remain source-compatible.
coinbase_adv still dispatches to a provider returning venuecoinbase and storing
under that namespace; the alias-cache mismatch was not silently repaired.

## Verification

Before source change, whole-unit regressions produced4failures/2passes: default
and explicitFalse misread1/2; the existing explicitTrue path passed. Identical
tests against the preserved before-copy still reproduce4failures/2passes.
After correction the six cases pass. Full new/affected test selection initially
119passed/1fixturefailure: fractional0.02 was below the fixture's minimum1.
The synthetic market minimum was corrected to its declared step; no production
minimum check was weakened. Then120passed0.72s.

Final focused seven-file selection: **220passed3.36seconds**, no failures/errors/
skips. This is not a full repository suite or actual exchange integration:

```sh
./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_coinbase_shared_precision.py tests/test_refresh_paper_market_rules.py \
  tests/test_coinbase_market_mode_gate.py tests/test_coinbase_exit_mode_gap.py \
  tests/test_market_rules_decimal_validation.py tests/test_market_rules_validation.py \
  tests/test_paper_cash_entry.py --tb=short
```

Synthetic public CCXT inputs exercise the real provider/cache/validator/rounding
path for1,2 and fractional increments. Invalid quantities are refused and BUY
rounding never increases quantity. Missing/mismatched IDs, nonfinite/underflow/
unrepresentable/native fields and flag/mode failures are included. Historical
negative controls remain in their old archived sources. The earlier test's
legacy0.1 assertion is retained against the exact before-copy, with a dated
correction asserting that the current shared default must return1. The mode
metadata fixture now supplies native increments and imports the actual provider
instead of executing an extracted function without its globals.

Before source/test copies, incremental diff and SOURCE_SHA256SUMS preserve the
change boundary. Separate reviewer independently121tests passed1.09seconds;
receipt in INDEPENDENT_REVIEW.md. Author220total was not independently reproduced
as the full seven-file selection.

## Limits and remaining work

DONE at source level: shared fetch correction, no flag bypass, product identity,
native precision checks, unchanged other-venue paths and focused regression proof.
Independent final source review completed ACCEPTED_WITH_RISK.
NOT DONE: actual cache inventory/refresh, real public product validation, profile/
host readiness, periodic metadata freshness, activation/commissioning or forward
performance. Existing cache contents were not invalidated or rewritten; a fresh
old row can retain the wrong increment under the existing six-hour TTL. A synthetic
test demonstrates that limitation and the corrected explicit refresh path.

The source assumes native product fields and the known CCXT mode can be verified;
unknown evidence is refused, not inferred from token price. Source acceptance
cannot establish that actual cached data, quantities or fills were correct.
No historical study, account result or profitability claim changes here.

What do I know that could change the owner's decision that I have not yet said?
Deploying a corrected fetcher alone would not immediately correct fresh old
cache rows. Operational acceptance must include separately authorized cache
inventory/refresh and exact row read-back before relying on the quantities.

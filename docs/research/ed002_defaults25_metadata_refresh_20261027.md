# ED-002 approved public metadata refresh

2026-10-27. Active role AUDITOR. Acceptance: ACCEPTED for the bounded capture
and descriptive comparison only. Experiment readiness remains INCOMPLETE.

## Result

SHOWN at2026-10-27 17:17:32 New York (21:17:32UTC): all25configured labels have
one same-base Coinbase USD product candidate.24are online; MATIC-USD is delisted
and trading_disabled=true. The24online products have false trading_disabled,
cancel_only, limit_only, post_only and auction_mode flags in this observation.
These are public venue facts, not account eligibility or trading authorization.

The11compared product fields and five selected currency fields for these25
are unchanged from the October19 snapshot. This is not a claim that every field
or every product on Coinbase is unchanged. Whole responses grew from842to845
product records and511to514currency records; no out-of-scope coin ranking or
opportunity analysis was performed. USDmax_precision/min_size remain0.01 in
the currency response; no fee/fill settlement precision was inferred from them.

## Approved Action And Receipt

Direct operator selected "Approve public metadata refresh (Recommended)".
The single capture made exactly two public GET attempts, `/products` and
`/currencies`; both returnedHTTP200. Receipt elapsed time0.171504seconds, within
the30-second overall/10-second per-request bounds. No retries, redirects,
authentication headers, credentials, accounts, candles, returns or signals.

VERIFIED_ENV: repository Python3.12.10, default CA count0, installed certifi.
An ephemeral TLS context used certifi with hostname/certificate verification
enabled; no trust-store/environment/configuration files changed. Proxy lookup
was disabled in the clean environment. Redirects were refused, not followed.
No TLS bypass or authentication repair was needed.

Raw responses, exclusive-create attempt/final receipts and offline comparison:
`../../research/coinbase_metadata_20261027/20261027T211732_235339Z_01ee9d4c/`.
The initial ATTEMPT record is intention evidence; `manifest.json` records the
actual OBSERVED result. Original payloads/receipts were not edited during
offline comparison. All new files were created without overwriting prior data.

- Products received21:17:32.329430UTC:845records,356321bytes,
  SHA256 `5b5e7a15b45c34a888ffb684d90fde4095b588a0b4e66c00c9efc3b4dca67d7b`.
- Currencies received21:17:32.402702UTC:514records,563029bytes,
  SHA256 `f838353e69507517c87565178d91296709c65d55c454d90208b78160346cc62a`.

The two response times are separate, not an atomic exchange-state transaction.
Server HTTP dates agree to the second with the received UTC timestamps.

## Verification And Limits

Read-only post-capture verification rehashed both payloads against the receipt,
checked HTTP/schema/budget outcome, uniqueness of25assets/products/currencies,
and compared actual field presence and values (absent is not false). The
comparison binds seven source files and retains one record per configured asset.
No test suite was rerun: no production source, ledger, strategy or behavior
changed. The accepted synthetic bridge and all frozen studies remain intact.

This consumes the approved two-request capture. It does not authorize another
refresh, collector, scheduler, server, account, financial-model rule, experiment
or trade. No raw candle/archive payload was opened or study evaluated.

Remaining research inputs: verified warm-up/coverage and per-observation
availability, explicit model rounding/order semantics, fees/cost assumptions,
and independently validated inference before a future protocol freeze. Keep
all25in the consideration denominator; do not silently replace MATIC with POL.
Next candle-coverage or statistical work needs its own bounded research scope;
the public snapshot is not a forecast, continuous status proof or net edge.

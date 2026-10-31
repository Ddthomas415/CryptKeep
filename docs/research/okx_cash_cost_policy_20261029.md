# OKX cash-cost normalization policy, offline scope

2026-10-29 America/New_York. ENGINEER; HIGH risk, financial evidence logic.
Implementation: READY_FOR_INDEPENDENT_REVIEW. Original Fix3: INCOMPLETE.

## Decision and useful outcome

Use separate policies for cash-cost comparison and crowding. A published
per-period forecast can be expressed in a common time unit without reversing
the premium/interest/cap formula. It remains a forecast, not a settlement or
return. Do not require a reconstructed premium formula for this arithmetic.
No existing funding strategy threshold, collector or eligibility gate changes.

Added scripts/research/synthetic_okx_cash_cost.py and tests/test_okx_cash_cost.py.
The pure offline wrapper calls the separately accepted endpoint classifier
itself; callers cannot substitute a pre-marked eligible result. Existing
decoder/store/collector/model/context sources and original artifacts unchanged.

## New primary evidence, actually accessed

SHOWN: opened the official funding mechanism page through the web reader. It
explains per-period assessment, rate sign, adjustable intervals and cash fees
as position value times the rate. Its current formula is interval-dependent.
This is venue documentation, not a promise of actual trader receipts.
[Official mechanism](https://www.okx.com/en-au/help/perps-funding-fee-mechanism).

SHOWN: the API language landing page opened but provided no field definitions;
the full English guide exceeded the web reader's4MiB limit again. Instead of
claiming success, made one bounded public documentation GET with systemcurl:
HTTP200,5,280,636bytes, max15s/16MiB, no retry/redirect/proxy/credentials. No
market-data request was made. Parsed inert HTML only; no downloaded code ran.

Read both actual REST sections. Current fundingRate is documented as a forecast;
settFundingRate depends on settState. The history section distinguishes its
predicted fundingRate from actual realizedRate. The API directs clients to the
fundingTime/nextFundingTime difference for the current funding interval.
[Current API section](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-funding-rate),
[History API section](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-funding-rate-history).

Exact extracted HTML byte ranges and hashes, plus whole-document hash/size and
source URL, are retained in docs/review_artifacts/okx_cash_cost_policy_20261029/.
The whole HTML remains a temporary file; only the two sections are retained in
the repo. Original failed reads remain recorded, not retroactively relabeled.
Third-party search results were not used as semantic evidence.

The API and mechanism pages list differing examples of interval frequencies.
Do not hard-code either list as an exhaustive guarantee. Use a valid explicit
schedule difference for the forecast being described, not a fixed8h default.

## Implemented policy

For the documented current_period mechanism, a finite current fundingRate and
positive scheduled difference N support the arithmetic r*8/N. The source ts
must be present and not later than receipt; fundingTime must still be upcoming
at that receipt. Unsupported method, unknown rate/time, invalid schedule or
unrepresentable arithmetic returns no normalized value and explicit reasons.

Output names deliberately include forecast: forecast_rate_per_8h, kind
forecast_not_settled, as_of_receipt and scheduled_interval_hours. Positive rate
means long pays short. No notional, leverage, personal balance or PnL assumed.
The calculation is an as-recorded comparison, not a live freshness assessment;
live_freshness_verified=False. It is not a projection that rates will persist.
Decimal arithmetic uses a local50-significant-digit context and reports
overflow/underflow as unknown, never an invented0. Repeating ratios are rounded
within that context, not claimed to be infinitely precise.

Historical realizedRate retains its documented actual-per-period meaning, but
settled_rate_per_8h remainsNone without a verified effective interval for that
particular settlement. Today's scheduled interval is NOT borrowed for old
events. Adjacent saved timestamps alone cannot certify absence of missing rows.

Crowding comparability staysFalse: neither interval scaling nor the formula
tag reconstructs the premium/interest/cap inputs. No formula inversion is done.
Strategy/execution flags remainFalse; annualized output remainsNone. The earlier
classifier's conservative flags stay unchanged. calculation_available=True
means only this explicit forecast arithmetic is available, not financial
qualification, origin authentication or permission for a consumer to trade.

## Verification and limits

VERIFIED_ENV isolated command; plugins/conftest/cache disabled. New tests refuse
external sockets and SQLite. Author result148passed0.86s,exit0:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_okx_cash_cost.py tests/test_okx_funding_contract.py tests/test_synthetic_funding_observations.py tests/test_funding_receipts.py
```

Cases include equivalent synthetic1/2/4/6/8/16h schedules, signs/zero,
formula-tag independence for cash arithmetic, bad mechanism/rate/time/schedule,
overflow/underflow, local precision/input ownership and forged-receipt refusal.
One existing saved sample is a decoding/arithmetic fixture, not a strategy
experiment, new capture or source of a yield/profitability claim. Previous
112test cases are included, not reopened for new acceptance.

Two material assumptions: the saved documentation applies to the explicitly
named public endpoint/current_period field; caller-supplied capture bytes,
receipts and local clock may be dishonest or incomplete. If either fails,
the result is not authenticated venue evidence. Hashes do not solve that.

Native semantics are documented now; actual settlement/account applicability,
historical intervals, historical formula/crowding equivalence, live freshness
and integration remain unverified. No full suite, host or live consumer proof.

## Handoff

Freeze exact source/tests/sections/checkpoint and dependency hashes in BINDINGS.
Separate GATE must assess the distinction between forecast arithmetic and
strategy eligibility and run the one documented command. No author acceptance.
If accepted, the next source boundary is compatibility with the raw adapter;
do not start a collector, initialize a real store or activate normalized scoring
under this handoff. Historical settled normalization needs event-specific
interval evidence rather than more invented defaults.

No SDK/account/credential/database/schema/collector/service/server/Docker/job/
scheduler/trading/capital/risk/config/deploy/dependency/commit/push operation.

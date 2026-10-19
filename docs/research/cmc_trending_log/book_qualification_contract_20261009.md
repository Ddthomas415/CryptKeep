# Book evidence qualification

Read-only structural qualification uses the exact requested Coinbase product URL,
recorded product ID, valid recorded SHA256, ordered aware request/receipt times,
explicit nonauction state, finite positive prices/sizes and noncrossed bid/ask.
Auction or unknown auction state remains unqualified. Empty/malformed/error records
are invalid. The recorded response hash is not recomputed from unavailable raw bytes.

Sizes are base units and are not multiplied by order count. An optional declared
base quantity can be compared with displayed ask/bid size. This comparison is not
a fill guarantee, market-impact model or strategy sizing decision. No quantity is
invented when the caller supplies none. Decimal arithmetic preserves values.

Capture duration is reported without asserting quote freshness. Book server time
does not by itself establish quote age or synchronized clocks. No freshness cutoff,
capacity acceptance rule or scoring eligibility is silently introduced. Public
response/request metadata cannot independently authenticate the asset identity.
Existing identity/cohort/timing rules remain separate.

Tests:21 combined book/ticker-evidence tests passed. Existing BTC/ETH bounded probe
records pass structural checks with85/67ms capture durations. No live request made
for these checks; input artifact unchanged. No integrated scorer replacement.

Acceptance: READY_FOR_INDEPENDENT_REVIEW. R03 remains incomplete for primary
qualification until study-level age, quantity and missing-evidence policy is fixed.

## Review correction and approved100USD sensitivity

Side and level containers must be JSON arrays; string sides/rows cannot become
price/size pairs. Empty and truncated levels are invalid. Regression coverage
pins both sides. This repairs the independent review's malformed-row finding.

Operator acknowledged the recommended100USD entry-notional sensitivity. It is
notional excluding separately charged fees, not an all-in100USD cash budget.
Quantity is100/recorded ask; compare only with displayed ask size at that capture.
For a future exit, retain the same entry quantity rather than deriving a new one
from an exit's100USD notional. Current output is entry-only, not round-trip capacity.

Existing BTC/ETH probe has sufficient displayed ask size for this sensitivity;
no order was placed and no later exit evidence exists in this probe. Artifact:
research/research_corrections_20261009/cmc_book_100usd_sensitivity_v1.json.
34 combined book/ticker/logger tests passed. Correction and sensitivity remain
READY_FOR_INDEPENDENT_REVIEW; primary freshness/scoring policy remains incomplete.

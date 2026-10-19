# BTC/ETH funding carry: capital-scale feasibility

Status: READY_FOR_INDEPENDENT_REVIEW. Public research only, no trading.

## Result first

For September 12 17:00 UTC through October 12 17:00 UTC, the capital-constrained
BTC/ETH hedge produced too little funding to support the assumed monthly server
cost. This is not a general verdict about carry across all assets or periods.

| Separate 1,000-USDT scenario | Funding receipts | Gross basis change | Net before overhead | Net after overhead |
| --- | ---: | ---: | ---: | ---: |
| BTC, zero execution cost reference | 1.98 | 0.04 | 2.02 | -17.98 |
| ETH, zero execution cost reference | 1.54 | 0.06 | 1.60 | -18.40 |
| BTC, assumed costs | 1.98 | 0.04 | -5.14 | -25.14 |
| ETH, assumed costs | 1.53 | 0.06 | -5.33 | -25.33 |

These are separate allocations of the same budget, not a combined 2,000-USDT
portfolio. Overhead is 20 USD per 30 days, converted by an explicitly unverified
USD/USDT-parity assumption. Values above are USDT estimates, not actual dollars
or account balances. Actual fees and eligibility were not obtained.

## Fixed mechanism and sizing

Always own spot and short an equal base quantity in the linear USDT perpetual.
Do not retrospectively enter only before positive settlements. Fixed quantity
through the full period, no directional selection or rebalancing. Spot purchase,
short collateral equal to initial short notional, and entry fees must jointly
fit inside 1,000 USDT. Current published contract/spot lot and minimum sizes
checked; no extra funding assumed. Collateral is a sizing model, not a margin
or liquidation engine. Short venue risk and intraperiod liquidation remain
unverified; hedging does not eliminate them.

BTC quantity 0.0064, contracts 0.64 in both cases; assumed initial use 993.01 USDT.
ETH quantity 0.196, contracts 1.96 in the assumed-cost case; initial use 995.16.
Fee assumptions: spot 50 bps, perpetual 10 bps, adverse execution price 5 bps
per leg per side. These are not verified OKX account fee tiers. Zero-cost
reference is a sensitivity, not attainable execution or a general profit bound.

## Data, timing and accounting

18 public requests retained exact response bytes, SHA-256 hashes, parameters
and local receive times. Actual funding comes from realizedRate in funding
history, not predicted fundingRate. Each asset has 90 settlements; BTC includes
14 negative payments, ETH 16. Missing settled rates or mark observations refuse
calculation. Interval/boundary checks flag gaps over eight hours, but historical
schedule certification remains unverified if intervals changed to shorter ones.

Entry/exit price proxies are confirmed hourly candle opens one hour after the
funding-window boundaries. Positions are not assumed to open at an assessment
instant. Settlement position value uses the confirmed four-hour mark candle's
OPEN at the settlement timestamp, not the exact assessed mark. Thus rates are
actual historical records but cash receipts and hedge PnL are modeled.
Basis PnL is equal-quantity spot change plus short-perpetual change; fees and
adverse prices are deducted separately. No leverage adjustment, maintenance
margin, liquidation, borrow, transfer, tax or account-access model is provided.

Official sources:
- https://www.okx.com/en-us/help/perps-funding-fee-mechanism
- https://www.okx.com/docs-v5/en/#public-data-rest-api-get-funding-rate-history

## Proof and scope

Plan/source frozen before collection. Three tests passed: actual-rate use with
negative settlements; equal-quantity direction hedge; total budget/cost/rounding;
missing actual rates and marks refused. No full suite for isolated research.
Separate Hilbert review requested. Currency, execution and margin assumptions
prevent live-feasibility or profitability certification. No private credentials,
orders, venue transfers, account, campaign, risk, collector or scheduling changes.
The previous public gainer watch stays paused. Original studies are preserved.

Artifacts under research/: funding_carry_plan_20261012.json,
funding_carry_raw_20261012.json and funding_carry_results_20261012.json.
Source: scripts/research/funding_carry_feasibility.py.

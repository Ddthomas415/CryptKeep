# Dynamic Coinbase USD gainers scan

Public Coinbase catalogue: 925 products, no next page. Selected 403 unique
online USD spot markets, excluding disabled, view-only and cancel-only products.
This is a dynamic venue universe, not the previous fixed five coins. Fifteen
eligible products are limit-only: inclusion is not market-order executability.

Comparison windows: seven and thirty completed UTC days ending October 9 00:00
UTC. Daily first open to last close determines ranking. Strict finite OHLCV
and complete daily grids are required per window. New/sparse markets excluded
from ranking must be reported, not treated as zero returns. Current-online
selection excludes delisted products and therefore has survivorship bias.

Each winning product is inspected for hourly coverage. Missing hours are
reported explicitly, never filled or described as a complete grid. Price path
uses the initial open and observed hourly closes. Its pre-peak minimum to sampled maximum
is a hindsight description, not a monotonically rising interval or an exact
intrahour extreme. Peak-to-end describes subsequent movement, not a captured
short profit. No live or simulated strategy earnings are established here.

Raw catalogue, daily and hourly responses and summary are isolated under
`research/coinbase_gainers_20261009/`. The prospective study is unchanged.
Source: https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/public/list-public-products

Verification: synthetic complete-grid and missing-day checks passed. Separate
GATE ACCEPTED_WITH_RISK for initial scan logic; final raw-artifact and sparse
hourly diagnostic audit pending. Initial strict RLC hourly check found29missing
hours; the diagnostic now preserves these omissions instead of repairing them.

## Saved results

- Seven days: 400 markets ranked, 3 excluded for incomplete daily histories.
  RLC +142.4767%, OGN +117.7396%, HONEY +112.7380%, DIMO +56.8432%,
  SAND +47.4501%. RLC observed minimum0.3607 to peak1.0226: +183.5043%
  over49hours; end0.8831, -13.6417% over60hours afterpeak. Hourly gaps29.
- Thirty days: 398 markets ranked, 5 excluded for incomplete daily histories.
  DIMO +301.0217%, AURORA +258.3359%, QNT +250.8459%, RLC +185.1469%,
  DRV +167.6584%. DIMO observed minimum0.00763 to peak0.05342: +600.1311%
  over549hours; end0.0314, -41.2205% over75hours afterpeak. Hourly gaps15.

All prices USD. These leaders are highest among eligible complete-daily-grid
markets, not proof that omitted markets could not have had a higher return.

RLC sampled rise: October4 11:00 to October6 12:00 UTC. DIMO sampled rise:
September13 00:00 to October5 21:00 UTC. Separate AUDITOR finalized saved-raw
verification with no discrepancies in rankings, exclusions, prices, timestamps,
gap lists or arithmetic. Descriptive audit complete; no trading-profit proof.

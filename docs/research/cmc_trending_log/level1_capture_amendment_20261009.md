# Optional level-1 capture

User approved adding book prices and sizes for future captures. The existing v3
command remains ticker-only unless `--capture-level1` is explicitly supplied.
The schedule has not been edited and no collection was started for this change.

The option requests each distinct watched Coinbase product plus BTC-USD and
ETH-USD once. Raw responses retain bid/ask sizes, sequence, auction fields,
request/receipt timestamps and response hashes supplied by the existing fetcher.
Product ID and request URL are stored alongside each response. Failures remain
visible per product and do not replace ticker observations.

Source: https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-book
Level1 sizes are aggregated base quantities; order counts must not multiply them.
Auction prices are indicative. Displayed sizes can change before order arrival.
Neither a server response timestamp nor capture latency alone guarantees freshness
or a fill. No size/freshness threshold or scoring eligibility is inferred here.

Original snapshots and frozen ticker scoring rules remain unchanged. Additional
book requests add collection latency and API load; no live API or unattended run
has verified this option. Qualification and activation remain separate work.

Verification:38 targeted logger/envelope/report tests passed, including preserved
raw sizes, request deduplication, auction evidence and isolated request failures.
Acceptance: READY_FOR_INDEPENDENT_REVIEW.

# Public Liquidation Data - Bounded Feasibility Check

## Result First

**SHOWN: real public venue liquidation records and matching prices are
available.** This supports an event-based research question rather than using
large red candles as invented liquidation evidence. No trading result or edge
has been calculated.

Frozen cutoff: October 13, 2026, 02:11 UTC (October 12, 22:11 New York).
One bounded foreground download made 22 public requests, zero request errors.

| Market | Sampled records | Long-liquidation sell records | Sell minute bins | Sell records with complete following spot/perp price grid |
| --- | ---: | ---: | ---: | ---: |
| BTC-USDT perpetual | 600 | 422 | 17 | 422 |
| ETH-USDT perpetual | 600 | 388 | 17 | 388 |

810 long/sell records are NOT 810 independent opportunities. Twelve sell
minute bins overlap between BTC and ETH; their union is 22 distinct UTC minutes,
which also are not necessarily independent liquidation episodes. Both samples
span approximately 00:06 through 02:06 UTC, only two hours.

All 810 long/sell records have confirmed, positive-price candles for every
minute of the following 15-minute window in BOTH spot and perpetual markets.
The anchor is the first minute boundary strictly after the liquidation's
reported timestamp. No incomplete candle or interpolated gap is accepted.
Short-liquidation buys are retained separately, not mislabeled forced selling.
39 records across both directions are too recent for the full forward window;
these are immature observations, not failed recoveries. No mature record in
this bounded sample had a missing forward price minute.

## History and Source Limits

Discovery API route:
`https://www.okx.com/api/v5/public/liquidation-orders`

Its API error required `instFamily`, after which the route returned records
for `BTC-USDT-SWAP` and `ETH-USDT-SWAP`. Six pages per market used a strictly
decreasing `after` timestamp, 100 records per page. This route was reachable
but not found in the current official documentation inspected, so its ongoing
support, semantics and complete historical retention are NOT certified.

Separate probes asking for records older than cutoff minus seven days and
older than cutoff minus thirty days returned successful empty responses for
both assets. This does NOT establish an exact retention limit or prove that
there were no liquidations then. A months-long retrospective dataset was not
obtained; only the recent bounded sample was observed.

Official OKX documentation describes its live liquidation channel as partial,
not total venue liquidations:
`https://www.okx.com/docs-v5/en/#public-data-websocket-liquidation-orders-channel`
Binance likewise publishes only the latest liquidation per symbol in each
one-second snapshot:
`https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/ws-streams/market`
Neither stream should be presented as a complete forced-flow total.

Other crucial distinctions:

- `bkPx` is bankruptcy price, not an execution, bid/ask or hypothetical entry
  price. It is preserved as raw evidence and never used as a market price.
- `sz` is contract quantity, not automatically base coins or USD. Public
  definitions were saved: BTC has 0.01 BTC contract value; ETH 0.1 ETH, each
  with multiplier 1 and linear USDT settlement. No notional total was computed.
- No stable venue order ID is supplied in these records. Fingerprints remove
  byte-equivalent record duplicates for diagnostics; identical genuine orders
  cannot necessarily be distinguished. Records are not certified order counts.
- Event timestamps do not prove when a historical trader could receive the
  information. Current receipt timestamps are saved; historical publication
  latency is unknown. A price grid after event time is not actionable-entry proof.
- One-minute candle opens/closes are not historical spread/depth, queue position,
  maker fill probability, or evidence that a standing discount bid was filled.

## Artifacts and Verification

New, non-overwriting artifacts:

- `scripts/research/liquidation_data_probe.py`
- `tests/test_liquidation_data_probe.py`
- `research/liquidation_data_probe_plan_20261012.json`
- `research/liquidation_data_probe_raw_20261012.json`

Every request preserves URL path/parameters, request/receive times, HTTP status,
exact response bytes as base64, and SHA256. All 22 response hashes were checked.
The source and UTC cutoff were frozen before this recorded collection; no
trading rules, return thresholds or parameter search were introduced.

Source SHA256: `4d0b1e342d2d667078746e446ccdd1935416abc98c5f17e2b11acbe74957fee8`.
Raw SHA256: `32c7fd8f5b64826d4d8f6d3283d6800901518a4aa4f175311b7427a90a258efa`.

VERIFIED_ENV: local .venv Python 3.12 and successful public HTTPS requests with
normal certificate verification. Test command:
`./.venv/bin/python -B -m pytest -q tests/test_liquidation_data_probe.py`
returned **6 passed in 0.48s**. Tests cover identity/direction, post-cutoff
exclusion, post-event continuous price grids, immature horizons, confirmed
candles/finite prices, and record counts versus clustered minute bins.
Full suite not run. Separate reviewer Newton was asked to check raw integrity,
pagination, schema interpretation and coverage counts. Review is pending.

No account credentials, private data, orders, positions, production feed,
configuration, campaign, collector restart or new recurring job was touched.
The existing liquidation-context scaffold remains unchanged.

## Research Consequence

This check establishes a usable recent public observation source, NOT a tested
edge. A future economic test must freeze an actual exhaustion/re-entry rule,
separate correlated bursts, retain continuation losses as well as rebounds,
include realistic execution/costs, and evaluate one capital-constrained account.
Do not claim that the two-hour sample establishes profit or extrapolate it
to a months-long backtest. Wider historical coverage and historical availability
timing remain unresolved. No paid data purchase or collector activation follows
from this diagnostic.

## Independent Review Closure

Newton GATE returned **ACCEPTED_WITH_RISK** for the saved availability diagnostic.
All 22 receipts were independently decoded/hash-verified, normalized records
and price grids rebuilt, pagination checked, and coverage counts reproduced.
Six tests passed independently. There is one failure-path limitation in the
collector: fatal schema validation can abort before receipts are saved. It did
not affect this completed download; general failure-path preservation is not
accepted. Original source and recorded artifacts remain unchanged.

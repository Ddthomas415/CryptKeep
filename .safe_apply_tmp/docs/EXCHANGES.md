# Exchanges supported (adapters)
We operate through CCXT where applicable, but we do not claim “zero delay” execution.
Real execution includes: network latency, exchange matching latency, rate limits, partial fills, queue position, and order lifecycle delays.

## Venues configured
- binance
- coinbase
- gateio

## Notes
- LIVE: execution safety gates apply (min order notional, max trades/day, max daily loss if pnl source exists).
- PAPER: optional latency simulation (`execution.paper_latency_ms`) adds realistic delay before fill.

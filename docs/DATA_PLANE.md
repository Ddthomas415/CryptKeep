# Data Plane (Phase 2)

Goal: Read-only market data collection to a canonical event stream.

## Implemented
- Binance Spot WS (combined streams): trades + depth@100ms deltas
- Coinbase Advanced Trade WS: market_trades + heartbeats; endpoint wss://advanced-trade-ws.coinbase.com
- Gate.io Spot WS v4: spot.trades and spot.order_book
- SQLite append-only `data/events.sqlite` store

## Run
- macOS: `./.venv/bin/python -m services.data_collector.main`
- Windows: `.\.venv\Scripts\python.exe -m services.data_collector.main`

## Env vars
- `CBP_FEEDS=binance,coinbase,gateio`
- `CBP_CHANNELS=trades,book_l2`
- `CBP_BINANCE_SYMBOLS=btcusdt,ethusdt`
- `CBP_COINBASE_PRODUCTS=BTC-USD,ETH-USD`
- `CBP_GATEIO_PAIRS=BTC_USDT,ETH_USDT`
- Coinbase optional: `CBP_COINBASE_JWT=...` (JWT expires ~2 minutes)

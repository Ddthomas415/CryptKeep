# Phase 28 — Multi-exchange ingestion + unified view

Adds:
- services/data/multi_exchange_collector.py
- scripts/collect_market_data_multi.py
- services/data/unified_view.py
- Dashboard: Multi-Exchange Monitor

Config:
- config/trading.yaml supports:
  multi_exchanges:
    db_path: data/market_raw.sqlite
    poll_sec: 5.0
    venues:
      - exchange_id: coinbase
        sandbox: true
        symbols: ["BTC/USDT"]
      - exchange_id: binance
        sandbox: true
        symbols: ["BTC/USDT"]
      - exchange_id: gateio
        sandbox: true
        symbols: ["BTC/USDT"]

Notes:
- Exchange ids are ccxt ids (strings). If an id differs on your ccxt version, the collector will report a fatal error for that venue.
- Data is stored with keys (exchange, symbol, timeframe) so venues remain isolated but comparable.

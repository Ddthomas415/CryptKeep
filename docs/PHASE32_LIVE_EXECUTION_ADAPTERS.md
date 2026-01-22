# Phase 32 — Live execution adapters + idempotent client IDs + reconciliation (HARD-OFF)

What this adds:
- services/execution/exchange_client.py (ccxt wrapper + client-id mapping)
- services/execution/live_executor.py
- scripts/live_submit_intent.py
- scripts/live_executor_tick.py
- scripts/live_reconcile.py
- Dashboard panel: Live Execution (HARD-OFF by default)

Hard safety gate:
Live orders will NOT be sent unless:
1) config/trading.yaml -> live.enabled: true
2) environment variable LIVE_TRADING=YES

Credentials:
Set per-exchange env vars:
- COINBASE_API_KEY / COINBASE_API_SECRET / COINBASE_API_PASSPHRASE (optional)
- BINANCE_API_KEY / BINANCE_API_SECRET
- GATEIO_API_KEY / GATEIO_API_SECRET

Run (if enabled):
- Submit an intent:
  python scripts/live_submit_intent.py --symbol BTC/USDT --side buy --qty 0.001
- Process + reconcile:
  LIVE_TRADING=YES python scripts/live_executor_tick.py

Notes:
- Reconciliation is intentionally conservative: we only write a synthetic fill when an order is CLOSED and FILLED>0.
- Next phase will add per-exchange trade-level reconciliation (fetch_my_trades) for partial fills + fee accuracy.

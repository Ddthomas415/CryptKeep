# Phase 321 — Unified Trading Runner (PAPER mode, safe)

What it does (PAPER only):
- Optionally starts CCXT price feeds (market data only)
- Reads latest prices from `data/market_data.sqlite`
- Aggregates prices (median/primary + staleness) => fail-closed if stale/missing
- Loads portfolio MTM from `data/paper_journal.sqlite`
- Applies strict risk gates before any order is allowed:
  - max trades/day
  - max position notional per symbol
  - max drawdown from peak equity
  - kill switch file (immediate stop)
- Places PAPER market orders and journals to SQLite.

Run:
- macOS/Linux: `./run_trader.sh`
- Windows: `.\run_trader.ps1`

Kill switch:
- Create file: `data/KILL_SWITCH.flag`
- Runner stops on next tick.

Config:
- `config/trading.yaml`

Notes:
- This runner is safe: paper only. Live execution is not enabled in Phase 321.

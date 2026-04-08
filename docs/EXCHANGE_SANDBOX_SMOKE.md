# Exchange Smoke Scripts

Quick scripts to validate basic exchange connectivity.

## Generic

Examples:

- Coinbase public smoke:
  - `python3 scripts/smoke_exchange.py --exchange coinbase --orderbook`
- Binance sandbox smoke:
  - `python3 scripts/smoke_exchange.py --exchange binance --sandbox --orderbook`
- Gate.io sandbox smoke:
  - `python3 scripts/smoke_exchange.py --exchange gateio --sandbox --orderbook`

Options:
- `--exchange`: `coinbase`, `binance`, or `gateio`
- `--symbol`: defaults to `BTC/USD`
- `--sandbox`: enable sandbox/testnet mode where supported
- `--orderbook`: include `fetch_order_book` check

Important note:
- Coinbase in the current repo/client combination does not expose a working CCXT sandbox URL.
- Use Coinbase with no `--sandbox` flag for public smoke and authenticated read-only connectivity proof.

The script prints JSON and exits:
- `0` when all checks pass
- `2` when any check fails

## Per-exchange wrappers

- `python3 scripts/smoke_coinbase.py` (public Coinbase smoke, no sandbox flag)
- `python3 scripts/smoke_binance.py`
- `python3 scripts/smoke_gateio.py`

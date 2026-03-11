# Exchange Sandbox Smoke Scripts

Quick scripts to validate basic exchange connectivity in sandbox mode.

## Generic

`python3 scripts/smoke_exchange.py --exchange coinbase --sandbox --orderbook`

Options:
- `--exchange`: `coinbase`, `binance`, or `gateio`
- `--symbol`: defaults to `BTC/USD`
- `--sandbox`: enable sandbox/testnet mode where supported
- `--orderbook`: include `fetch_order_book` check

The script prints JSON and exits:
- `0` when all checks pass
- `2` when any check fails

## Per-exchange wrappers

- `python3 scripts/smoke_coinbase.py`
- `python3 scripts/smoke_binance.py`
- `python3 scripts/smoke_gateio.py`


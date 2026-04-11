# Symbol Scanner

Read-only crypto scanner backed by `ccxt` and Coinbase spot market data.

## What it does

Ranks symbols by:
- 24h price change %
- volume surge
- intraday volatility
- RSI extremes

## CLI

```bash
python3 scripts/run_symbol_scanner.py
python3 scripts/run_symbol_scanner.py --json
```

## Dashboard

Open the **Symbol Scanner** page in Streamlit.

## Notes

- Scanner is read-only.
- It is not wired directly into execution.
- Errors per symbol are returned in the scanner result instead of failing the whole scan.

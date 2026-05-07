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
- Supervised paper mode can consume scanner-ranked symbols through `managed_symbols.source=scanner` with refresh-cached selection and active-symbol preservation.
- Live execution does not use scanner-driven symbol rotation.
- Errors per symbol are returned in the scanner result instead of failing the whole scan.

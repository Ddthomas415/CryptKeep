# ES Initial Entry Comparison

Research only. No campaign, promotion or execution-policy change.

## Reproduce

From the repository root, using the project venv:

```sh
./.venv/bin/python scripts/research/compare_es_initial_entry.py > /tmp/es_initial_entry.json
cmp docs/research/artifacts/es_initial_entry_2026_09_17/result.json /tmp/es_initial_entry.json
```

Requires the existing local `.cbp_state/data/market_raw.sqlite` archive.
The script opens it read-only and refuses a changed dataset, missing endpoints
or non-contiguous daily rows. It never fetches data. The dataset itself is not
bundled; without that archive this package cannot independently reproduce it.
Run normally, not with Python optimization that disables assertions.

Original computation code revision: 090e08d35's parent (5b78445d6), with the
temporary research adapter subsequently preserved as the script above. Current
package integrates master 066c24b56; rerun produced byte-identical JSON.

SHA256:

| Artifact | Hash |
| --- | --- |
| Input row encoding | c0d64661f4c09b4ca7be047694dceff46b22846ba576177f55e4464a623e28eb |
| Research script | 34517cc2f8aa2745f81f3246305d032815538bb53be5779174042cca83746fe4 |
| result.json | 58ea4a8c41181b641e9f007e52c462e50499abcb9d3b98a73152fab0395e3edb |
| services/backtest/parity_engine.py | d48d7566c398621ef53ea9633b8f2eeb1917bb3fb57e7e3c6653ff6d3d598f30 |

## Scope and Result

3077 Coinbase BTC/USD daily rows, 2018-01-01 through 2026-06-04 inclusive;
BTC/USDT strategy label is an explicit data proxy. SMA200/ATR20, warmup 210,
1000 initial quote units, 7.5 bps fee and 5 bps slippage per side.

The adapter suppresses buy unless the raw action changes from the preceding
observation; initial buy is suppressed. All other engine behavior is retained.
Sequence assertions cover initial sustained buy and hold-to-buy transitions.
Both runs begin with hold, produce identical trade lists and 31 closed trades.
This window does not exercise the initial-long launch difference.

This is NOT runner parity: all-cash sizing, bar-based sampling, exits and
duplicate-action handling remain the archive engine's. It is in-sample, assumes
costs and does not validate profitability, historical paper fills or launch policy.
No window search, parameter selection or campaign reset follows from the result.

Acceptance state: READY_FOR_INDEPENDENT_REVIEW for the packaged research adapter.

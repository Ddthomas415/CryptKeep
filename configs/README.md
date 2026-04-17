# configs/

Strategy-specific runtime configuration files.

## Why this exists alongside `config/`

`config/` is the canonical system configuration root (trading.yaml, services.yaml, etc).
`configs/` holds strategy-specific configs that are separate from system config by design:
  - strategy configs have a different lifecycle (promoted, versioned independently)
  - keeping them separate prevents accidentally modifying system config when tuning a strategy

## Contents

```
configs/strategies/
  es_daily_trend_v1.yaml   — ES Daily Trend v1 paper campaign config
```

## Adding a new strategy config

1. Create `configs/strategies/<strategy_id>.yaml`
2. Reference `docs/strategies/<strategy_id>.md` as the spec source of truth
3. Add the strategy_id to `configs/strategies/` in this README

## Not to be confused with

- `config/trading.yaml` — system-level trading parameters (live gate, risk limits)
- `config/services.yaml` — service topology
- `config/app.yaml` — application config

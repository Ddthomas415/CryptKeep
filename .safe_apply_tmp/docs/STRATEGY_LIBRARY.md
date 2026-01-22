# Strategy Library (Phase 227)

Interface:
- compute_signal(cfg, market, position) -> Signal(action: buy/sell/hold)
- suggest_orders(cfg, market, position, signal) -> list[OrderIntent] (directional intents)

Registry:
- services/strategies/registry.py
- choose by config: strategy.name

Built-ins:
- ema_cross (active by default)
- mean_reversion_rsi (safe hold unless strategy.mr_enabled = true)
- breakout_donchian (safe hold unless strategy.bo_enabled = true)

Risk separation:
- Exit controls (risk_exits) run BEFORE strategy
- Buy sizing (risk) runs outside strategy; strategy only proposes direction

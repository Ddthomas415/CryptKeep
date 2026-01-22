# Phase 277 — Multi-Strategy Library + Presets

Adds:
- Unified Signal schema: services/strategy/signals.py
- Indicators: services/strategy/indicators.py
- Strategies:
  - ema_crossover
  - mean_reversion (z-score)
  - breakout (donchian)
- Filters (gate-only):
  - volatility_filter (ATR% band)
  - regime_filter (trend slope check)
- Strategy registry: services/strategy/registry.py
- Presets: services/strategy/presets.py
- Streamlit panel: "Strategy Presets (No Config Editing)"

Config (optional):
strategy:
  type: ema_crossover | mean_reversion | breakout
  params: { ... }
  filters:
    volatility: { enabled, period, min_atr_pct, max_atr_pct }
    regime: { enabled, slow, slope_lookback }

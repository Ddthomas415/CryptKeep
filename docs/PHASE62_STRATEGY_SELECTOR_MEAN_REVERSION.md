# Phase 62 — Mean Reversion strategy + Strategy Selector (config switch)

Adds:
- services/pipeline/mean_reversion_strategy.py
  - Bollinger-band mean reversion:
    - BUY when close < lower band
    - SELL when close > upper band
  - uses StrategyStateStore to prevent duplicates
  - creates intents via IntentWriter (RiskGate enforced)

- services/pipeline/pipeline_router.py
  - build_pipeline() picks strategy based on config.pipeline.strategy

Updates:
- scripts/run_pipeline_once.py and scripts/run_pipeline_loop.py now use the router:
  - pipeline.strategy: "ema" | "mean_reversion"

Config:
Uses merged runtime trading config on the default path:
- `<your-repo-path>/.cbp_state/runtime/config/user.yaml` overlays `<your-repo-path>/config/trading.yaml`

pipeline:
  strategy: ema
  # mean reversion params
  bb_window: 20
  bb_k: 2.0

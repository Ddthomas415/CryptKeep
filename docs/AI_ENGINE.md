# AI Engine Scaffold

This repo now includes a lightweight AI engine scaffold under `services/ai_engine/`.

## Components

- `services/ai_engine/features.py`
  - Normalizes runtime context/telemetry into a stable numeric feature map.
- `services/ai_engine/model.py`
  - Linear signal model with logistic probability output.
- `services/ai_engine/trainer.py`
  - Simple trainer that derives linear weights from labeled examples.
- `services/ai_engine/signal_service.py`
  - Loads model JSON and evaluates BUY/SELL gating decisions.

## Integration Point

- `services/live_router/router.py`
  - Optional AI gate before order intent details are finalized.
  - Default behavior is pass-through unless explicitly enabled.

## Runtime Controls

- `CBP_AI_ENGINE_ENABLED=1` enable AI gate
- `CBP_AI_ENGINE_STRICT` retained for compatibility; exceptions reaching the enabled router AI hook block orders regardless of this flag
- `CBP_AI_MODEL_PATH=/path/to/ai_model.json` custom model path
- `CBP_AI_BUY_THRESHOLD=0.55` buy threshold
- `CBP_AI_SELL_THRESHOLD=0.45` sell threshold

Config-based equivalent (via user config) is under `ai_engine`:

```yaml
ai_engine:
  enabled: false
  strict: false
  model_path: ""
  buy_threshold: 0.55
  sell_threshold: 0.45
```

## Notes

- This is decision-support/risk-gating only.
- It does not bypass existing safety/risk controls.
- If no model exists, AI evaluation returns pass-through by design.
- Missing models and model read/parse errors return `model_missing_pass_through`
  inside `AISignalService`; the router exception handler does not see those
  errors. Exceptions that reach `services/live_router/router.py` block orders
  whenever AI is enabled. Do not interpret the router fix as complete model-error
  fail-closure.
  This scaffold description is not approval to activate the hook for live trading.

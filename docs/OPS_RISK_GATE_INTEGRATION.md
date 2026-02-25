# Ops + Risk Gate Integration

This project now supports a clean "ops brain + bot execution" split:

- Ops system: observe, explain, recommend, record
- Bot: decide, execute, reconcile

## Integration Modes

1) Decision-support mode (recommended)
- Bot publishes telemetry.
- Ops classifies regime/zone, detects hazards, emits recommendations.
- Bot still owns order decisions and execution.

2) Risk-gated execution mode (advanced)
- Ops publishes a gate state.
- Bot execution chokepoint enforces the gate before submit.
- Ops still does not place orders.

## Gate States

- `ALLOW_TRADING`
- `ALLOW_ONLY_REDUCTIONS`
- `HALT_NEW_POSITIONS`
- `FULL_STOP`

`ALLOW_ONLY_REDUCTIONS` and `HALT_NEW_POSITIONS` require `reduceOnly/reduce_only=true` on the order params.

## Implemented Interfaces

### Bot -> Ops telemetry

- Contract: `services/ops/risk_gate_contract.py` (`RawSignalSnapshot`)
- Adapter: `services/ops/live_signal_adapter.py`
- Store: `storage/ops_signal_store_sqlite.py` (`ops_raw_signal_snapshots`)

Expected fields include:
- exchange API health
- order reject rate
- websocket lag
- venue latency
- volatility
- drawdown / PnL
- exposure / leverage

### Ops -> Bot gate signal

- Contract: `services/ops/risk_gate_contract.py` (`RiskGateSignal`)
- Store: `storage/ops_signal_store_sqlite.py` (`ops_risk_gate_signals`)
- Enforced at: `services/execution/place_order.py` (global order chokepoint)

Expected fields include:
- system stress
- regime
- zone
- gate state
- hazards/reasons

## Enforcement Controls

Gate enforcement is intentionally optional by default.

- `CBP_OPS_RISK_GATE_ENFORCE=1`: enable enforcement in `place_order`
- `CBP_OPS_RISK_GATE_FAIL_CLOSED=1`: if enabled and no/invalid signal, block orders
- `CBP_OPS_DB_PATH=/path/to/ops_intel.sqlite`: override ops signal DB path

## Minimal Wiring Diagram

```
AI Crypto Bot
  - strategy/ML
  - execution
  - portfolio

      | telemetry (pnl, exposure, rejects, latency, feed lag)
      v

Trading Ops Intelligence
  - hazards / regime / alerts
  - narratives / runbooks
  - audit log
  - signal store

      | risk gates + recommendations
      v

AI Crypto Bot enforces gate at order chokepoint
  - allow / reductions-only / halt / full-stop
```


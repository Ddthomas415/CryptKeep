# Pass 3G — ops/, strategy_runner/, supervisor/

**Pass:** 3G | **Status:** COMPLETE

## Findings

### Finding 1 — ops risk gate 4-level state machine (Strength)

RiskGateState: ALLOW_TRADING, ALLOW_ONLY_REDUCTIONS, HALT_NEW_POSITIONS, FULL_STOP.
RawSignalSnapshot: exchange_api_ok, order_reject_rate, ws_lag_ms,
venue_latency_ms, realized_volatility, drawdown_pct, pnl_usd,
exposure_usd, leverage. Comprehensive ops signal input schema.

### Finding 2 — ops/risk_gate_engine seventh threshold set (Medium)

```python
reject_rate_warn=0.05, reject_rate_block=0.15
ws_lag_warn_ms=1200.0, ws_lag_block_ms=2500.0
venue_latency_warn_ms=800.0
```

Seventh separate risk threshold definition. Still not coordinated.

### Finding 3 — supervisor.MANAGED_SERVICES missing pipeline and executor (High = H9)

```python
MANAGED_SERVICES = ('dashboard', 'tick_publisher', 'market_ws',
    'evidence_webhook', 'ops_signal_adapter', 'ops_risk_gate',
    'intent_consumer', 'reconciler')
```

ES Daily Trend pipeline and intent executor are NOT in MANAGED_SERVICES.
If either crashes, supervisor does not detect or restart.

Combined with watchdog IDLE-on-crash false-positive (Pass 2N):
a dead pipeline may appear alive and fire no alerts.

Dead-process gap: pipeline can stop completely with no recovery triggered.

### Finding 4 — ema_crossover_runner full live strategy runner (Shown)

Imports 15+ modules including kill_conditions, performance_kill,
exposure_controls, position_scaling. Full execution loop for live_trader_loop.
Separate from supervised soak stack.

### Finding 5 — services/validation/ discovered (Noted)

Referenced from ema_crossover_runner. Zero-coverage, not in audit map.

## H9 confirmed

Supervisor gap: pipeline and executor not managed. Dead-process recovery
depends entirely on operator noticing via AI alert monitor (which only fires
on active run_once_failed, not on process death).

## Coverage

- services/ops/: 7 of 7 COMPLETE
- services/strategy_runner/: 2 of 2 COMPLETE
- services/supervisor/: 2 of 2 COMPLETE
- services/validation/: DISCOVERED (0 read)

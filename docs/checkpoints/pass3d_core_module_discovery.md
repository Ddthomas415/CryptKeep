# Pass 3D — Discovered core/ Module

**Pass:** 3D | **Status:** COMPLETE

## Discovery: core/ had 0 audit coverage

event_store_sqlite.py import led to core/. 12 files, none in audit map.

## Findings

**Strength:** core/interfaces.py — async Protocol contracts for MarketDataFeed
and ExecutionVenue. Pydantic models for all domain objects.

**Strength:** core/events.py — Venue enum, Channel enum, EventBase (Pydantic).
Canonical validated event types.

**Shown:** core/ipc.py — ServiceName (data_collector, strategy_runner,
execution_router) and CommandType enums. IPC layer.

**Medium:** core/risk_manager.py — SIXTH separate risk threshold definition.
max_trades_per_day=10, max_position_notional=2000, max_drawdown_frac=0.10.
Hardcoded. Differs from live_risk_gates.py. Not coordinated.

**Confirmed gap:** core/ entirely absent from audit map until this pass.

## core/ coverage: 12 files, 0 read in depth

Added to audit map as DISCOVERED.

## Fragmentation tally updated

| Pattern | Count |
|---|---|
| Risk/acceptance threshold sets | **6** |
| Strategy name normalizations | 4 |
| Intent tracking stores | 3 |
| Kill switch fail directions | 2 |

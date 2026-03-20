# Service Contracts

This document defines the Phase 1 interface contracts for `trade-ai-mvp` (research copilot mode only).

## Non-negotiable constraints
- `EXECUTION_ENABLED` must stay `false` in Phase 1.
- No service places orders or sends execution intents.
- All services expose `GET /health` returning:

```json
{ "status": "ok" }
```

## Gateway (`:8000`)
Gateway is the public API surface.

### `POST /query/explain`
Request:
```json
{
  "asset": "SOL",
  "question": "Why is SOL moving?"
}
```

Response:
```json
{
  "asset": "SOL",
  "question": "Why is SOL moving?",
  "current_cause": "Recent SOL price activity shows last price 145.20 with spread 0.2000, alongside fresh document hits.",
  "past_precedent": "Historical roadmap announcements showed similar follow-through.",
  "future_catalyst": "A scheduled governance event remains pending.",
  "confidence": 0.78,
  "evidence": [
    {
      "type": "market",
      "source": "coinbase",
      "timestamp": "2026-03-10T21:00:00Z"
    },
    {
      "type": "document",
      "source": "newsapi",
      "title": "SOL activity up",
      "timestamp": "2026-03-10T20:45:00Z"
    }
  ],
  "paper_positions": [
    {
      "symbol": "SOL-USD",
      "quantity": 1.25,
      "avg_entry_price": 145.2,
      "realized_pnl": 0.0
    }
  ],
  "recent_paper_fills": [
    {
      "id": "930f6d38-07ca-4ced-8447-d6b0293adb2f",
      "order_id": "d5955f0d-2455-404a-8cf5-e1468e407963",
      "symbol": "SOL-USD",
      "side": "buy",
      "price": 145.2,
      "quantity": 1.25,
      "fee": 0.12
    }
  ],
  "paper_risk_state": {
    "gate": "ALLOW",
    "paper_approved": true
  },
  "execution_disabled": true
}
```

Failure:
- `503` when orchestrator is unavailable.

### `POST /query/why-moving`
Request:
```json
{
  "asset": "SOL"
}
```

Behavior:
- Internally maps to `POST /query/explain` with question format `Why is <ASSET> moving?`.

### `POST /query/propose-trade`
Request:
```json
{
  "asset": "SOL",
  "question": "Should we open a SOL paper position now?",
  "max_notional_usd": 250
}
```

Response:
```json
{
  "asset": "SOL",
  "question": "Should we open a SOL paper position now?",
  "side": "buy",
  "order_type": "market",
  "suggested_quantity": 1.2,
  "estimated_price": 145.0,
  "estimated_notional_usd": 174.0,
  "rationale": "Momentum setup with supporting context.",
  "confidence": 0.8,
  "risk": {
    "gate": "ALLOW",
    "paper_approved": true
  },
  "execution_disabled": true,
  "requires_user_approval": true,
  "paper_submit_path": "/paper/orders"
}
```

Notes:
- This endpoint is proposal-only and never places orders.

### `GET /live/status`
Response:
```json
{
  "execution_enabled": false,
  "paper_trading_enabled": true,
  "custody_ready": false,
  "min_requirements_met": false,
  "blockers": [
    "execution_disabled_flag",
    "missing_exchange_credentials",
    "paper_window_not_ready",
    "risk_gate_full_stop"
  ],
  "paper_readiness": {
    "phase3_live_eligible": false
  },
  "risk_snapshot": {
    "gate": "FULL_STOP",
    "reason": "Phase 1 research mode only",
    "execution_disabled": true
  },
  "notes": [
    "Live order placement remains disabled in this phase scaffold."
  ]
}
```

### `GET /live/custody/status`
Response:
```json
{
  "provider": "coinbase",
  "ready": false,
  "key_present": false,
  "secret_present": false,
  "key_fingerprint": null,
  "secret_fingerprint": null,
  "blockers": [
    "missing_coinbase_api_key",
    "missing_coinbase_api_secret"
  ]
}
```

### `GET /live/custody/providers`
Response:
```json
{
  "as_of": "2026-03-11T08:10:00Z",
  "configured_provider": "vault_stub",
  "execution_disabled": true,
  "providers": [
    {
      "name": "env",
      "configured": false,
      "supported": true,
      "ready": true,
      "blockers": [],
      "metadata": {
        "source": "environment_variables",
        "key_present": true,
        "secret_present": true
      }
    },
    {
      "name": "vault_stub",
      "configured": true,
      "supported": true,
      "ready": false,
      "blockers": [
        "missing_custody_secret_ref"
      ],
      "metadata": {
        "source": "vault_stub",
        "key_ref_present": true,
        "secret_ref_present": false,
        "key_ref_hint": "vaul...main",
        "secret_ref_hint": null,
        "retrieval_mode": "metadata_only_no_secret_fetch"
      }
    }
  ]
}
```

### `GET /live/custody/policy`
Response:
```json
{
  "as_of": "2026-03-11T08:10:00Z",
  "configured_provider": "vault_stub",
  "rotation_max_age_days": 90,
  "last_rotated_at": "2026-03-04T08:10:00Z",
  "rotation_age_days": 7.0,
  "rotation_within_policy": true,
  "key_id": "vaul...main",
  "secret_id": "vaul...main",
  "blockers": [],
  "execution_disabled": true
}
```

### `GET /live/custody/keys`
Response:
```json
{
  "as_of": "2026-03-11T08:11:00Z",
  "configured_provider": "vault_stub",
  "provider": "coinbase:vault_stub",
  "key_present": true,
  "secret_present": true,
  "key_id": "vaul...main",
  "secret_id": "vaul...main",
  "key_fingerprint": "9b44a2aa31",
  "secret_fingerprint": "90d2f7bc2e",
  "rotation_max_age_days": 90,
  "last_rotated_at": "2026-03-04T08:10:00Z",
  "rotation_age_days": 7.0,
  "rotation_within_policy": true,
  "verify_ready": true,
  "blockers": [],
  "execution_disabled": true
}
```

### `POST /live/custody/keys/verify`
Request:
```json
{
  "operator": "ops-oncall",
  "ticket_id": "SEC-2042",
  "note": "verification before cutover",
  "strict": true
}
```

Response:
```json
{
  "as_of": "2026-03-11T08:11:30Z",
  "configured_provider": "env",
  "provider": "coinbase",
  "operator": "ops-oncall",
  "ticket_id": "SEC-2042",
  "strict": true,
  "verified": true,
  "reason": "custody_key_verification_passed",
  "checks": [
    {"id": "key_present", "ok": true},
    {"id": "secret_present", "ok": true},
    {"id": "rotation_within_policy", "ok": true, "required": true},
    {"id": "phase2_metadata_only", "ok": true}
  ],
  "blockers": [],
  "execution_disabled": true
}
```

Notes:
- Verification is metadata-only in Phase 2 and never fetches or rotates live secrets.
- In non-strict mode, stale rotation is reported in blockers but does not force `verified=false` when key/secret material is present.

### `GET /live/custody/rotation/plan`
Response:
```json
{
  "as_of": "2026-03-11T08:12:00Z",
  "configured_provider": "vault_stub",
  "rotation_max_age_days": 90,
  "last_rotated_at": "2026-03-04T08:10:00Z",
  "rotation_age_days": 7.0,
  "rotation_within_policy": true,
  "rotation_required": false,
  "due_at": "2026-06-02T08:10:00Z",
  "recommended_action": "no_action",
  "blockers": [],
  "execution_disabled": true
}
```

### `POST /live/custody/rotation/run`
Request:
```json
{
  "operator": "ops-oncall",
  "note": "quarterly rotation window",
  "ticket_id": "SEC-1234",
  "force": true
}
```

Response:
```json
{
  "as_of": "2026-03-11T08:13:00Z",
  "configured_provider": "vault_stub",
  "attempted": true,
  "accepted": false,
  "executed": false,
  "reason": "phase2_custody_key_management_disabled",
  "operator": "ops-oncall",
  "note": "quarterly rotation window",
  "ticket_id": "SEC-1234",
  "blockers": [
    "phase2_custody_key_management_disabled"
  ],
  "execution_disabled": true
}
```

Notes:
- Rotation run is intentionally blocked in Phase 2.
- Endpoint exists to provide auditable contract shape for future key-management integration.

### `GET /live/deployment/checklist`
Response:
```json
{
  "as_of": "2026-03-11T03:30:00Z",
  "ready_for_real_capital": false,
  "blockers": [
    "execution_flag",
    "paper_readiness_window",
    "risk_gate_allow",
    "custody_ready",
    "routing_candidate"
  ],
  "checks": [
    {
      "id": "execution_flag",
      "ok": false,
      "detail": "EXECUTION_ENABLED must be true for real-capital deployment."
    },
    {
      "id": "paper_readiness_window",
      "ok": false,
      "detail": "Paper readiness window must be met."
    }
  ]
}
```

### `GET /live/deployment/state`
Response:
```json
{
  "as_of": "2026-03-11T03:35:00Z",
  "armed": false,
  "armed_at": null,
  "armed_by": null,
  "note": null,
  "force": false,
  "blockers_at_arm": []
}
```

### `POST /live/deployment/arm`
Request:
```json
{
  "operator": "ops-oncall",
  "symbol": "SOL-USD",
  "note": "dry-run arm",
  "force": true
}
```

Behavior:
- Evaluates deployment checklist for the requested symbol.
- If checklist is not ready and `force=false`, returns `409` with blockers.
- If `force=true`, records dry-run armed state with blockers snapshot.
- Does not execute orders.

### `POST /live/deployment/disarm`
Request:
```json
{
  "operator": "ops-oncall",
  "symbol": "SOL-USD",
  "note": "dry-run disarm"
}
```

Behavior:
- Clears dry-run armed state.
- Does not execute orders.

### `POST /live/router/plan`
Request:
```json
{
  "symbol": "SOL-USD",
  "side": "buy",
  "quantity": 1.0,
  "order_type": "market"
}
```

Response:
```json
{
  "symbol": "SOL-USD",
  "side": "buy",
  "quantity": 1.0,
  "order_type": "market",
  "candidates": [
    {
      "venue": "coinbase",
      "score": 90,
      "reason": "primary integrated venue",
      "fee_bps": 8.0,
      "estimated_cost_bps": 14.8949,
      "route_eligible": true,
      "policy_blockers": [],
      "last_price": 145.0,
      "bid": 144.95,
      "ask": 145.05,
      "spread_bps": 6.8949
    },
    {
      "venue": "binance",
      "score": 5,
      "reason": "public book ticker; policy_blocked:spread_above_policy,estimated_cost_above_policy",
      "fee_bps": 10.0,
      "estimated_cost_bps": 210.0,
      "route_eligible": false,
      "policy_blockers": [
        "spread_above_policy",
        "estimated_cost_above_policy"
      ],
      "bid": 144.0,
      "ask": 146.0,
      "spread_bps": 137.931
    }
  ],
  "rejected_venues": [
    {
      "venue": "binance",
      "route_eligible": false
    }
  ],
  "selected_venue": "coinbase",
  "selected_reason": "primary integrated venue",
  "routing_policy": {
    "max_spread_bps": 120.0,
    "max_estimated_cost_bps": 180.0,
    "venue_fee_bps": {
      "coinbase": 8.0,
      "binance": 10.0,
      "kraken": 16.0
    }
  },
  "route_eligible": true,
  "execution_disabled": true
}
```

### `GET /live/router/policy`
Response:
```json
{
  "as_of": "2026-03-11T04:05:00Z",
  "max_spread_bps": 120.0,
  "max_estimated_cost_bps": 180.0,
  "venue_fee_bps": {
    "coinbase": 8.0,
    "binance": 10.0,
    "kraken": 16.0
  },
  "execution_disabled": true
}
```

### `POST /live/router/simulate`
Request:
```json
{
  "symbol": "SOL-USD",
  "side": "buy",
  "quantity": 1.0,
  "order_type": "market",
  "max_slippage_bps": 20.0
}
```

Response:
```json
{
  "symbol": "SOL-USD",
  "side": "buy",
  "quantity": 1.0,
  "order_type": "market",
  "feasible_route": true,
  "selected_venue": "coinbase",
  "selected_reason": "primary integrated venue",
  "candidates": [],
  "rejected_venues": [],
  "execution_disabled": true
}
```

Notes:
- Simulation reuses `/live/router/plan` and applies `max_slippage_bps` as an additional dry-run feasibility gate.
- No orders are placed.

### `POST /live/router/allocation`
Request:
```json
{
  "symbol": "SOL-USD",
  "side": "buy",
  "quantity": 3.0,
  "order_type": "market",
  "max_venues": 2,
  "min_venues": 1,
  "max_venue_ratio": 0.7,
  "min_slice_quantity": 0.25,
  "max_slippage_bps": 25.0
}
```

Response:
```json
{
  "symbol": "SOL-USD",
  "side": "buy",
  "quantity": 3.0,
  "order_type": "market",
  "feasible_route": true,
  "recommended_slices": [
    {
      "venue": "coinbase",
      "ratio": 0.63,
      "quantity": 1.89,
      "estimated_cost_bps": 12.0,
      "ratio_capped": false
    },
    {
      "venue": "binance",
      "ratio": 0.37,
      "quantity": 1.11,
      "estimated_cost_bps": 18.0,
      "ratio_capped": false
    }
  ],
  "rejected_venues": [],
  "routing_policy": {
    "max_spread_bps": 120.0,
    "max_estimated_cost_bps": 180.0,
    "allocation_max_venues": 2,
    "allocation_min_venues": 1,
    "allocation_max_venue_ratio": 0.7,
    "allocation_min_slice_quantity": 0.25
  },
  "total_estimated_cost_bps": 14.22,
  "execution_disabled": true
}
```

Notes:
- Allocation reuses `/live/router/plan`, filters high-cost candidates by `max_slippage_bps`, and returns dry-run split ratios.
- Optional diversification controls: `min_venues` enforces minimum venue breadth, and `max_venue_ratio` caps concentration per selected venue.
- `min_slice_quantity` enforces minimum per-slice quantity and drops/rejects dust slices when possible.
- Returns `ratio_capped=true` when a slice ratio was reduced by the concentration cap.
- This endpoint persists a dry-run routing decision with `source_endpoint=router_allocation`.
- No live execution path is enabled.

### `GET /live/router/decisions`
Query params:
- `symbol` (optional)
- `source_endpoint` (optional, e.g. `router_plan`, `router_simulate`, `router_allocation`)
- `limit` (optional, default `50`, max `500`)

Response:
```json
{
  "decisions": [
    {
      "id": "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d",
      "source_endpoint": "router_plan",
      "symbol": "SOL-USD",
      "side": "buy",
      "quantity": 1.0,
      "order_type": "market",
      "selected_venue": "coinbase",
      "selected_reason": "primary integrated venue",
      "route_eligible": true,
      "feasible_route": true,
      "execution_disabled": true
    }
  ]
}
```

Notes:
- Route decisions are persisted for dry-run replay and analytics only.
- This endpoint does not execute orders.

### `GET /live/router/analytics`
Query params:
- `symbol` (optional)
- `source_endpoint` (optional)
- `window_hours` (optional, default `24`)
- `limit` (optional, default `2000`, max `5000`)

Response:
```json
{
  "as_of": "2026-03-11T04:35:00Z",
  "symbol": "SOL-USD",
  "source_endpoint": "router_plan",
  "window_hours": 24,
  "total_decisions": 42,
  "route_eligible_count": 30,
  "feasible_route_count": 28,
  "selected_venue_count": 30,
  "route_eligible_rate": 0.7143,
  "feasible_route_rate": 0.6667,
  "selected_venue_rate": 0.7143,
  "selected_venue_counts": {
    "coinbase": 26,
    "binance": 4
  },
  "avg_estimated_cost_bps_by_venue": {
    "coinbase": 12.438,
    "binance": 19.125
  },
  "policy_blocker_counts": {
    "spread_above_policy": 8,
    "estimated_cost_above_policy": 5
  },
  "execution_disabled": true
}
```

Notes:
- Uses persisted dry-run route decisions (`live_route_decisions`) and computes aggregate telemetry only.
- Still no live execution path.

### `GET /live/router/alerts`
Query params:
- `symbol` (optional)
- `source_endpoint` (optional)
- `window_hours` (optional, default `24`)
- `limit` (optional, default `2000`, max `5000`)

Response:
```json
{
  "status": "alerting",
  "as_of": "2026-03-11T04:50:00Z",
  "symbol": "SOL-USD",
  "source_endpoint": "router_plan",
  "window_hours": 24,
  "total_decisions": 100,
  "thresholds": {
    "min_decisions": 20,
    "min_route_eligible_rate": 0.6,
    "min_feasible_route_rate": 0.55,
    "max_spread_blocker_ratio": 0.3,
    "max_cost_blocker_ratio": 0.3
  },
  "metrics": {
    "total_decisions": 100,
    "route_eligible_rate": 0.52,
    "feasible_route_rate": 0.49,
    "selected_venue_rate": 0.52,
    "spread_blocker_ratio": 0.45,
    "cost_blocker_ratio": 0.35
  },
  "triggered": [
    {
      "type": "route_eligibility_degraded",
      "metric": "route_eligible_rate",
      "value": 0.52,
      "threshold": 0.6,
      "severity": "medium"
    }
  ],
  "execution_disabled": true
}
```

Notes:
- Reuses router analytics and emits threshold-based degradation signals.
- Alerts are informational only in this phase and do not trigger execution paths.

### `POST /live/router/maintenance/retention`
Request:
```json
{
  "days": 30
}
```

Response:
```json
{
  "as_of": "2026-03-11T05:05:00Z",
  "retention_days": 30,
  "deleted_route_decisions": 11,
  "execution_disabled": true
}
```

Notes:
- Cleans persisted dry-run route decisions older than the retention window.
- This is maintenance-only and has no execution side effects.

### `GET /live/router/runbook`
Query params:
- `symbol` (optional)
- `source_endpoint` (optional)
- `window_hours` (optional, default `24`)
- `limit` (optional, default `2000`, max `5000`)

Response:
```json
{
  "status": "action_required",
  "as_of": "2026-03-11T05:15:00Z",
  "symbol": "SOL-USD",
  "source_endpoint": "router_plan",
  "window_hours": 24,
  "suggested_gate": "HALT_NEW_POSITIONS",
  "rationale": [
    "Route eligibility degraded below threshold."
  ],
  "actions": [
    {
      "id": "tighten_new_exposure",
      "priority": "high",
      "description": "Pause new exposure while venue availability recovers."
    }
  ],
  "alerts": [
    {
      "type": "route_eligibility_degraded"
    }
  ],
  "execution_disabled": true
}
```

Notes:
- Reuses `/live/router/alerts` and emits recommended dry-run operational actions.
- Suggested gate is advisory only in this phase and does not execute orders.

### `GET /live/router/gate`
Query params:
- `symbol` (optional)
- `source_endpoint` (optional)
- `window_hours` (optional, default `24`)
- `limit` (optional, default `2000`, max `5000`)
- `include_risk` (optional, default `false`; overlays `risk_stub` and takes stricter binding gate)

Response:
```json
{
  "as_of": "2026-03-11T06:10:00Z",
  "symbol": "SOL-USD",
  "source_endpoint": "router_plan",
  "window_hours": 24,
  "source": "incident",
  "recommended_gate": "HALT_NEW_POSITIONS",
  "router_gate": "HALT_NEW_POSITIONS",
  "risk_gate_raw": "FULL_STOP",
  "risk_gate_mapped": "FULL_STOP",
  "risk_gate_binding": false,
  "risk_gate_reason": "Phase 1 research mode only",
  "gate_sources": [
    "incident"
  ],
  "system_stress": "high",
  "regime": "degraded",
  "zone": "containment",
  "top_hazards": [
    {
      "type": "route_eligibility_degraded",
      "severity": "medium",
      "message": "Route eligibility rate is below configured threshold."
    }
  ],
  "rationale": [
    "Route eligibility degraded below threshold."
  ],
  "actions": [
    {
      "id": "tighten_new_exposure",
      "priority": "high"
    }
  ],
  "incident_id": "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d",
  "incident_status": "open",
  "execution_disabled": true
}
```

Notes:
- Emits a single dry-run gate payload for bot-side enforcement integration.
- Prefers latest open/acknowledged incident when available; falls back to computed runbook output.
- Optional risk overlay promotes to the stricter gate only when risk signal is binding.
- Output is advisory only in this phase and does not execute orders.

### `GET /live/router/gates`
Query params:
- `symbol` (optional)
- `source_endpoint` (optional)
- `source` (optional, e.g. `incident`, `runbook`)
- `recommended_gate` (optional)
- `limit` (optional, default `50`, max `500`)

Response:
```json
{
  "signals": [
    {
      "id": "70fa0898-b0a1-4e94-97cc-3c4ef49ca512",
      "created_at": "2026-03-11T06:12:00Z",
      "symbol": "SOL-USD",
      "source_endpoint": "router_plan",
      "source": "incident",
      "recommended_gate": "HALT_NEW_POSITIONS",
      "system_stress": "high",
      "regime": "degraded",
      "zone": "containment",
      "execution_disabled": true
    }
  ]
}
```

### `GET /live/router/gates/summary`
Query params:
- `symbol` (optional)
- `source_endpoint` (optional)
- `source` (optional)
- `window_hours` (optional, default `168`)
- `limit` (optional, default `5000`, max `5000`)

Response:
```json
{
  "as_of": "2026-03-11T06:20:00Z",
  "symbol": "SOL-USD",
  "source_endpoint": "router_plan",
  "window_hours": 168,
  "total_signals": 24,
  "by_source": {
    "incident": 10,
    "runbook": 14
  },
  "by_recommended_gate": {
    "HALT_NEW_POSITIONS": 8,
    "ALLOW_ONLY_REDUCTIONS": 9,
    "ALLOW_TRADING": 7
  },
  "by_system_stress": {
    "high": 8,
    "medium": 9,
    "low": 7
  },
  "by_regime": {
    "degraded": 8,
    "caution": 9,
    "stable": 7
  },
  "by_zone": {
    "containment": 8,
    "reduction_only": 9,
    "normal": 7
  },
  "latest_signal_at": "2026-03-11T06:12:00Z",
  "execution_disabled": true
}
```

### `POST /live/router/gates/maintenance/retention`
Request:
```json
{
  "days": 180
}
```

Response:
```json
{
  "as_of": "2026-03-11T06:30:00Z",
  "retention_days": 180,
  "deleted_gate_signals": 12,
  "execution_disabled": true
}
```

Notes:
- Cleans persisted dry-run gate signals older than retention window.
- Maintenance-only behavior; no execution side effects.

### `POST /live/router/incidents/open`
Request:
```json
{
  "operator": "ops-oncall",
  "symbol": "SOL-USD",
  "source_endpoint": "router_plan",
  "window_hours": 24,
  "limit": 2000,
  "note": "dry-run incident open",
  "force": false
}
```

Response:
```json
{
  "id": "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d",
  "status": "open",
  "severity": "high",
  "symbol": "SOL-USD",
  "source_endpoint": "router_plan",
  "window_hours": 24,
  "suggested_gate": "HALT_NEW_POSITIONS",
  "operator": "ops-oncall",
  "execution_disabled": true
}
```

Notes:
- Opens a dry-run routing incident from current runbook signals.
- Returns `409` when no action is required unless `force=true`.

### `GET /live/router/incidents`
Query params:
- `status` (optional)
- `symbol` (optional)
- `limit` (optional, default `50`, max `500`)

Response:
```json
{
  "incidents": [
    {
      "id": "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d",
      "status": "open",
      "severity": "high",
      "symbol": "SOL-USD",
      "suggested_gate": "HALT_NEW_POSITIONS",
      "execution_disabled": true
    }
  ]
}
```

### `GET /live/router/incidents/{incident_id}`
Response:
```json
{
  "id": "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d",
  "status": "acknowledged",
  "severity": "high",
  "symbol": "SOL-USD",
  "source_endpoint": "router_plan",
  "window_hours": 24,
  "suggested_gate": "HALT_NEW_POSITIONS",
  "operator": "ops-oncall",
  "execution_disabled": true
}
```

Notes:
- Returns one persisted dry-run router incident by id.
- Returns `404` when the incident id does not exist.

### `GET /live/router/incidents/summary`
Query params:
- `symbol` (optional)
- `source_endpoint` (optional)
- `window_hours` (optional, default `168`)
- `limit` (optional, default `2000`, max `5000`)

Response:
```json
{
  "as_of": "2026-03-11T05:30:00Z",
  "symbol": "SOL-USD",
  "source_endpoint": "router_plan",
  "window_hours": 168,
  "total_incidents": 12,
  "open_count": 4,
  "acknowledged_count": 3,
  "resolved_count": 5,
  "severity_counts": {
    "high": 4,
    "medium": 6,
    "low": 2
  },
  "suggested_gate_counts": {
    "HALT_NEW_POSITIONS": 4,
    "ALLOW_ONLY_REDUCTIONS": 6,
    "ALLOW_TRADING": 2
  },
  "avg_minutes_to_resolve": 42.5,
  "execution_disabled": true
}
```

### `POST /live/router/incidents/maintenance/retention`
Request:
```json
{
  "days": 180
}
```

Response:
```json
{
  "as_of": "2026-03-11T05:35:00Z",
  "retention_days": 180,
  "deleted_incidents": 7,
  "execution_disabled": true
}
```

Notes:
- Cleans persisted dry-run incidents older than retention window.
- Maintenance-only behavior; no execution side effects.

### `POST /live/router/incidents/{incident_id}/reopen`
Request:
```json
{
  "operator": "ops-oncall",
  "note": "reopened for verification"
}
```

Behavior:
- Transitions incident from `resolved` back to `open`.
- Clears `closed_at` and `resolution_note` for the reopened lifecycle.
- Rejects with `409` when incident is not currently `resolved`.

### `POST /live/router/incidents/{incident_id}/ack`
Request:
```json
{
  "operator": "ops-oncall",
  "note": "acknowledged"
}
```

Behavior:
- Transitions incident from `open` to `acknowledged`.
- Rejects with `409` if the incident is already `resolved`.

### `POST /live/router/incidents/{incident_id}/resolve`
Request:
```json
{
  "operator": "ops-oncall",
  "note": "resolved"
}
```

Behavior:
- Transitions incident to `resolved` and stamps `closed_at`.
- Dry-run governance only; no live execution side effects.

### `POST /live/order-intent`
Request:
```json
{
  "symbol": "SOL-USD",
  "side": "buy",
  "quantity": 1.0,
  "order_type": "market",
  "client_order_id": "live-dryrun-001"
}
```

Response:
```json
{
  "accepted": false,
  "execution_disabled": true,
  "reason": "execution_disabled_flag, missing_exchange_credentials, paper_window_not_ready, risk_gate_full_stop",
  "gate": "FULL_STOP",
  "routed_venue": null,
  "dry_run_order": {
    "symbol": "SOL-USD",
    "side": "buy",
    "quantity": 1.0,
    "order_type": "market",
    "client_order_id": "live-dryrun-001"
  }
}
```

Notes:
- `POST /live/order-intent` is a dry-run gate check only in this scaffold.
- No live exchange order is placed from these endpoints.

### `GET /live/order-intents`
Query params:
- `symbol` (optional)
- `status` (optional)
- `limit` (optional, default `50`, max `500`)

Response:
```json
{
  "intents": [
    {
      "id": "2d8f5913-4dc3-4924-af80-574147f38b56",
      "symbol": "SOL-USD",
      "side": "buy",
      "quantity": 1.0,
      "order_type": "market",
      "status": "blocked",
      "gate": "FULL_STOP",
      "reason": "execution_disabled_flag",
      "execution_disabled": true,
      "approved_for_live": false
    }
  ]
}
```

### `POST /live/order-intents/{intent_id}/approve`
Behavior:
- Marks a dry-run intent as approved for governance/audit purposes only.
- Keeps `execution_disabled=true` and does not place live orders.

Response:
```json
{
  "id": "2d8f5913-4dc3-4924-af80-574147f38b56",
  "symbol": "SOL-USD",
  "status": "approved_dry_run",
  "approved_for_live": true,
  "execution_disabled": true
}
```

### `GET /live/execution/providers`
Response:
```json
{
  "as_of": "2026-03-11T07:10:00Z",
  "sandbox_enabled": true,
  "configured_provider": "coinbase_sandbox",
  "execution_disabled": true,
  "providers": [
    {
      "name": "mock",
      "mode": "sandbox_submit",
      "configured": false,
      "enabled": false,
      "supported": true,
      "ready": true,
      "blockers": [],
      "metadata": {
        "simulated": true,
        "requires_credentials": false,
        "order_submit_contract": "mock_sandbox_envelope"
      }
    },
    {
      "name": "coinbase_sandbox",
      "mode": "sandbox_submit",
      "configured": true,
      "enabled": true,
      "supported": true,
      "ready": true,
      "blockers": [],
      "metadata": {
        "simulated": true,
        "requires_credentials": true,
        "key_present": true,
        "secret_present": true,
        "coinbase_use_sandbox": true,
        "order_submit_contract": "coinbase_sandbox_stub"
      }
    }
  ]
}
```

### `GET /live/execution/submissions`
Query params:
- `intent_id` (optional)
- `symbol` (optional)
- `provider` (optional)
- `mode` (optional)
- `status` (optional)
- `limit` (optional, default `50`, max `500`)

Response:
```json
{
  "submissions": [
    {
      "id": "8c2192ca-9bf3-4c27-a366-6f9ad30089dd",
      "created_at": "2026-03-11T07:15:01Z",
      "intent_id": "2d8f5913-4dc3-4924-af80-574147f38b56",
      "mode": "sandbox_submit",
      "provider": "mock",
      "symbol": "SOL-USD",
      "side": "buy",
      "quantity": 1.0,
      "order_type": "market",
      "status": "submitted_sandbox",
      "accepted": true,
      "execution_disabled": false,
      "reason": "submitted_to_exchange_sandbox",
      "venue": "coinbase",
      "venue_order_id": "sbox-coinbase-livedryrun001",
      "submitted_at": "2026-03-11T07:15:00Z",
      "sandbox": true,
      "blockers": []
    }
  ]
}
```

### `GET /live/execution/submissions/summary`
Query params:
- `symbol` (optional)
- `provider` (optional)
- `mode` (optional)
- `window_hours` (optional)
- `limit` (optional, default `5000`, max `5000`)

Response:
```json
{
  "as_of": "2026-03-11T08:40:00Z",
  "symbol": "SOL-USD",
  "provider": null,
  "mode": null,
  "window_hours": 24,
  "total_submissions": 12,
  "accepted_count": 4,
  "blocked_count": 8,
  "by_status": {
    "submitted_sandbox": 4,
    "submit_blocked_dry_run": 6,
    "submit_blocked_sandbox": 2
  },
  "by_provider": {
    "mock": 10,
    "coinbase_sandbox": 2
  },
  "by_mode": {
    "dry_run": 6,
    "sandbox_submit": 6
  },
  "latest_submission_at": "2026-03-11T08:35:00Z",
  "execution_disabled": true
}
```

### `GET /live/execution/place/analytics`
Query params:
- `symbol` (optional)
- `provider` (optional)
- `requested_strategy` (optional, e.g. `auto`, `intent`, `single_venue`, `multi_venue`)
- `resolved_strategy` (optional, e.g. `intent`, `single_venue`, `multi_venue`)
- `has_shortfall` (optional boolean filter over allocation shortfall attempts)
- `min_coverage_ratio` (optional float filter, `0.0` to `1.0`)
- `window_hours` (optional, default `168`)
- `limit` (optional, default `5000`, max `5000`)

Response:
```json
{
  "as_of": "2026-03-11T10:20:00Z",
  "symbol": "SOL-USD",
  "provider": null,
  "window_hours": 168,
  "total_attempts": 2,
  "accepted_count": 0,
  "blocked_count": 2,
  "by_status": {
    "submit_blocked_live": 2
  },
  "by_provider": {
    "coinbase_sandbox": 2
  },
  "blocker_counts": {
    "phase2_live_execution_path_disabled": 2,
    "deployment_not_armed": 1
  },
  "latest_attempt_at": "2026-03-11T10:18:00Z",
  "execution_disabled": true
}
```

Notes:
- Aggregates persisted `mode=live_place` submissions only.
- Intended for operator diagnostics and readiness tracking; does not execute orders.

### `GET /live/execution/place/strategy-analytics`
Query params:
- `symbol` (optional)
- `provider` (optional)
- `requested_strategy` (optional, e.g. `auto`, `intent`, `single_venue`, `multi_venue`)
- `resolved_strategy` (optional, e.g. `intent`, `single_venue`, `multi_venue`)
- `window_hours` (optional, default `168`)
- `limit` (optional, default `5000`, max `5000`)

Response:
```json
{
  "as_of": "2026-03-11T10:24:00Z",
  "symbol": "SOL-USD",
  "provider": "coinbase_sandbox",
  "window_hours": 168,
  "total_attempts": 2,
  "by_requested_strategy": {
    "auto": 1,
    "multi_venue": 1
  },
  "by_resolved_strategy": {
    "single_venue": 1,
    "multi_venue": 1
  },
  "requested_resolved_transitions": {
    "auto->single_venue": 1,
    "multi_venue->multi_venue": 1
  },
  "by_resolution_reason": {
    "feasible_route_with_lowest_blockers": 1
  },
  "by_resolution_tie_break_reason": {
    "lowest_estimated_cost_bps": 1
  },
  "auto_resolution_rate": 1.0,
  "auto_resolved_to_intent_count": 0,
  "auto_resolved_to_intent_rate": 0.0,
  "estimated_cost_samples": 2,
  "avg_estimated_cost_bps": 10.0,
  "min_estimated_cost_bps": 8.0,
  "max_estimated_cost_bps": 12.0,
  "avg_estimated_cost_bps_by_requested_strategy": {
    "auto": 8.0,
    "multi_venue": 12.0
  },
  "avg_estimated_cost_bps_by_resolved_strategy": {
    "single_venue": 8.0,
    "multi_venue": 12.0
  },
  "auto_avg_estimated_cost_bps": 8.0,
  "non_auto_avg_estimated_cost_bps": 12.0,
  "auto_vs_non_auto_cost_delta_bps": -4.0,
  "allocation_rejection_counts": {
    "min_venues_not_met": 1
  },
  "allocation_blocker_counts": {
    "allocation_min_venues_not_met": 1
  },
  "avg_allocation_coverage_ratio": 0.8,
  "avg_allocation_coverage_ratio_by_requested_strategy": {
    "auto": 1.0,
    "multi_venue": 0.6
  },
  "avg_allocation_coverage_ratio_by_resolved_strategy": {
    "single_venue": 1.0,
    "multi_venue": 0.6
  },
  "allocation_shortfall_attempt_count": 1,
  "allocation_shortfall_attempt_rate": 0.5,
  "constraint_failure_attempt_count": 1,
  "constraint_failure_attempt_rate": 0.5,
  "ratio_capped_attempt_count": 1,
  "ratio_capped_attempt_rate": 0.5,
  "provider_venue_compatible_count": 1,
  "provider_venue_mismatch_count": 1,
  "provider_venue_compatible_rate": 0.5,
  "route_feasible_count": 1,
  "route_not_feasible_count": 1,
  "route_feasible_rate": 0.5,
  "latest_attempt_at": "2026-03-11T10:22:00Z",
  "execution_disabled": true
}
```

Notes:
- Aggregates persisted `mode=live_place` submissions with strategy-resolution and provider-compatibility diagnostics.
- Includes estimated-cost distributions from placement attempts (`total_estimated_cost_bps`) with per-strategy cost averages and auto-vs-non-auto cost deltas.
- Includes diversification diagnostics from placement attempts (`rejected_venues` reasons and `ratio_capped` slice markers).
- Includes allocation coverage diagnostics (`avg_allocation_coverage_ratio`) plus per-strategy coverage averages and shortfall incidence metrics (`allocation_shortfall_attempt_count`, `allocation_shortfall_attempt_rate`).
- Includes allocation constraint blocker counts and failure-rate metrics derived from persisted route blockers (for example `allocation_min_venues_not_met`).
- Optional strategy filters (`requested_strategy`, `resolved_strategy`) scope the analytics window before metric aggregation.
- Optional allocation filters (`has_shortfall`, `min_coverage_ratio`) further scope the window before metric aggregation.
- Includes requested/resolved transition matrix metrics plus resolution reason/tie-break reason distributions for auto-resolution diagnostics.
- Helps operators validate whether auto-resolution and multi-venue strategies are producing provider-compatible feasible routes.
- This endpoint never executes orders.

### `POST /live/execution/submissions/maintenance/retention`
Request:
```json
{
  "days": 90
}
```

Response:
```json
{
  "as_of": "2026-03-11T09:10:00Z",
  "retention_days": 90,
  "deleted_submissions": 4,
  "execution_disabled": true
}
```

Notes:
- Cleans persisted live execution submission history older than the retention window.
- Defaults to `LIVE_EXECUTION_SUBMISSION_RETENTION_DAYS` when `days` is omitted.

### `GET /live/execution/submissions/{submission_id}`
Response:
```json
{
  "id": "8c2192ca-9bf3-4c27-a366-6f9ad30089dd",
  "intent_id": "2d8f5913-4dc3-4924-af80-574147f38b56",
  "mode": "sandbox_submit",
  "provider": "mock",
  "symbol": "SOL-USD",
  "status": "submitted_sandbox",
  "accepted": true,
  "execution_disabled": false
}
```

### `POST /live/execution/submissions/sync`
Query params:
- `symbol` (optional)
- `provider` (optional)
- `mode` (optional)
- `status` (optional)
- `limit` (optional, default `20`, max `200`)

Response:
```json
{
  "as_of": "2026-03-11T09:11:00Z",
  "total_candidates": 2,
  "synced_count": 1,
  "failed_count": 1,
  "items": [
    {
      "submission_id": "8c2192ca-9bf3-4c27-a366-6f9ad3008901",
      "synced": true,
      "submission_status": "submitted_sandbox",
      "order_status": "open",
      "transport": "stub",
      "error": null
    },
    {
      "submission_id": "8c2192ca-9bf3-4c27-a366-6f9ad3008902",
      "synced": false,
      "submission_status": "submitted_sandbox",
      "order_status": null,
      "transport": null,
      "error": "sync_failed"
    }
  ],
  "execution_disabled": true
}
```

Notes:
- Bulk-syncs persisted submission states via per-submission sync flow.
- Keeps partial success semantics: failed submissions are reported in `items` with `synced=false`.

### `POST /live/execution/submissions/{submission_id}/sync`
Response:
```json
{
  "as_of": "2026-03-11T09:12:00Z",
  "submission": {
    "id": "8c2192ca-9bf3-4c27-a366-6f9ad30089dd",
    "status": "submitted_sandbox",
    "provider": "mock",
    "accepted": true,
    "venue_order_id": "sbox-coinbase-livedryrun001"
  },
  "order_status": "open",
  "transport": "stub",
  "synced": true,
  "execution_disabled": true
}
```

Notes:
- Refreshes persisted submission state from sandbox provider status (stub/transport paths).
- Persists sync metadata under `response_payload.last_status_sync`.

### `GET /live/execution/orders/{venue_order_id}/status`
Query params:
- `submission_id` (optional)
- `provider` (optional)

Response:
```json
{
  "as_of": "2026-03-11T09:15:00Z",
  "submission_id": "8c2192ca-9bf3-4c27-a366-6f9ad30089dd",
  "provider": "mock",
  "venue": "coinbase",
  "venue_order_id": "sbox-coinbase-livedryrun001",
  "order_status": "open",
  "accepted": true,
  "canceled": false,
  "sandbox": true,
  "transport": "stub",
  "filled_size": null,
  "remaining_size": 1.0,
  "avg_fill_price": null,
  "execution_disabled": true
}
```

### `POST /live/execution/orders/{venue_order_id}/cancel`
Request:
```json
{
  "submission_id": "8c2192ca-9bf3-4c27-a366-6f9ad30089dd",
  "provider": "mock",
  "reason": "operator_cancel"
}
```

Response:
```json
{
  "as_of": "2026-03-11T09:16:00Z",
  "submission_id": "8c2192ca-9bf3-4c27-a366-6f9ad30089dd",
  "provider": "mock",
  "venue": "coinbase",
  "venue_order_id": "sbox-coinbase-livedryrun001",
  "cancel_requested": true,
  "canceled": true,
  "order_status": "canceled",
  "reason": "operator_cancel",
  "sandbox": true,
  "transport": "stub",
  "execution_disabled": true
}
```

### `POST /live/execution/place/preflight`
Request:
```json
{
  "intent_id": "2d8f5913-4dc3-4924-af80-574147f38b56",
  "provider": "coinbase_sandbox",
  "venue": "coinbase"
}
```

Response:
```json
{
  "as_of": "2026-03-11T10:05:00Z",
  "intent_id": "2d8f5913-4dc3-4924-af80-574147f38b56",
  "symbol": "SOL-USD",
  "provider": "coinbase_sandbox",
  "venue": "coinbase",
  "ready_for_live_placement": false,
  "blockers": [
    "phase2_safety_block"
  ],
  "checks": [
    {
      "id": "intent_approved",
      "ok": true
    },
    {
      "id": "phase2_safety_block",
      "ok": false
    }
  ],
  "execution_disabled": true
}
```

Notes:
- Performs per-intent readiness checks against deployment, approval, risk, custody, and routing.
- Keeps `ready_for_live_placement=false` in Phase 2 due explicit safety block.

### `POST /live/execution/place/preview`
Request:
```json
{
  "intent_id": "2d8f5913-4dc3-4924-af80-574147f38b56",
  "provider": "coinbase_sandbox",
  "venue": "coinbase",
  "mode": "sandbox_submit"
}
```

Response:
```json
{
  "as_of": "2026-03-11T10:07:00Z",
  "intent_id": "2d8f5913-4dc3-4924-af80-574147f38b56",
  "symbol": "SOL-USD",
  "provider": "coinbase_sandbox",
  "venue": "coinbase",
  "mode": "sandbox_submit",
  "payload": {
    "product_id": "SOL-USD",
    "side": "buy",
    "type": "market",
    "size": "1.00000000"
  },
  "transport": "stub",
  "can_submit": true,
  "blockers": [],
  "execution_disabled": true
}
```

Notes:
- Provides provider-specific order payload preview for operator verification.
- Computes blockers and `can_submit` without executing or mutating state.

### `POST /live/execution/place/route`
Request:
```json
{
  "intent_id": "2d8f5913-4dc3-4924-af80-574147f38b56",
  "provider": "coinbase_sandbox",
  "strategy": "intent",
  "max_venues": 2,
  "min_venues": 1,
  "max_venue_ratio": 0.7,
  "min_slice_quantity": 0.25,
  "max_slippage_bps": 25.0
}
```

Response:
```json
{
  "as_of": "2026-03-11T10:10:00Z",
  "intent_id": "2d8f5913-4dc3-4924-af80-574147f38b56",
  "symbol": "SOL-USD",
  "provider": "coinbase_sandbox",
  "strategy": "single_venue",
  "selected_venue": "coinbase",
  "selected_reason": "lowest_estimated_cost",
  "route_eligible": true,
  "feasible_route": true,
  "candidates": [
    {
      "venue": "coinbase",
      "estimated_cost_bps": 8.0,
      "route_eligible": true
    }
  ],
  "recommended_slices": [
    {
      "venue": "coinbase",
      "quantity": 1.0,
      "weight": 1.0
    }
  ],
  "requested_quantity": 1.0,
  "allocated_quantity": 1.0,
  "allocation_coverage_ratio": 1.0,
  "allocation_shortfall_quantity": 0.0,
  "total_estimated_cost_bps": 8.0,
  "rejected_venues": [],
  "provider_supported_venues": [
    "coinbase"
  ],
  "provider_venue_compatible": true,
  "deployment_armed": true,
  "custody_ready": true,
  "risk_gate": "ALLOW",
  "blockers": [
    "phase2_live_execution_path_disabled"
  ],
  "execution_disabled": true
}
```

Notes:
- Produces per-intent route recommendation from current router scoring (`single_venue`) or allocation logic (`multi_venue`).
- `strategy=intent` uses existing intent route metadata (`route_plan` / `venue_preference`) without recomputing venue scoring.
- Enforces provider/venue compatibility; incompatible route outcomes are marked with `provider_venue_mismatch` and `route_not_feasible`.
- Surfaces allocation coverage diagnostics (`requested_quantity`, `allocated_quantity`, `allocation_coverage_ratio`, `allocation_shortfall_quantity`); any positive shortfall marks the route not feasible with blocker `allocation_quantity_shortfall`.
- Maps allocation rejection reasons into explicit route blockers (for example `allocation_min_slice_quantity_not_met`, `allocation_min_slice_quantity_unachievable`, `allocation_max_venue_ratio_unachievable`) for clearer operator diagnostics.
- Includes deployment/risk/custody gating context and always keeps Phase 2 safety blocker active.
- This endpoint never submits orders.

### `POST /live/execution/place/route/compare`
Request:
```json
{
  "intent_id": "2d8f5913-4dc3-4924-af80-574147f38b56",
  "provider": "coinbase_sandbox",
  "strategies": [
    "intent",
    "single_venue",
    "multi_venue"
  ],
  "max_venues": 2,
  "min_venues": 1,
  "max_venue_ratio": 0.7,
  "min_slice_quantity": 0.25,
  "max_slippage_bps": 25.0
}
```

Response:
```json
{
  "as_of": "2026-03-11T10:12:00Z",
  "intent_id": "2d8f5913-4dc3-4924-af80-574147f38b56",
  "symbol": "SOL-USD",
  "provider": "coinbase_sandbox",
  "options": [
    {
      "strategy": "intent",
      "selected_venue": "coinbase",
      "route_eligible": true,
      "feasible_route": true,
      "provider_venue_compatible": true,
      "requested_quantity": 1.0,
      "allocated_quantity": 1.0,
      "allocation_coverage_ratio": 1.0,
      "allocation_shortfall_quantity": 0.0,
      "total_estimated_cost_bps": 9.6,
      "blocker_count": 1,
      "blockers": [
        "phase2_live_execution_path_disabled"
      ],
      "sort_rank": 2,
      "sort_key": {
        "blocker_count": 1,
        "estimated_cost_present": true,
        "estimated_cost_bps": 9.6,
        "allocation_coverage_ratio": 1.0,
        "strategy_priority": 2
      },
      "recommended": false
    },
    {
      "strategy": "multi_venue",
      "selected_venue": "coinbase",
      "route_eligible": true,
      "feasible_route": true,
      "provider_venue_compatible": true,
      "requested_quantity": 1.0,
      "allocated_quantity": 1.0,
      "allocation_coverage_ratio": 1.0,
      "allocation_shortfall_quantity": 0.0,
      "total_estimated_cost_bps": 7.4,
      "blocker_count": 1,
      "blockers": [
        "phase2_live_execution_path_disabled"
      ],
      "sort_rank": 1,
      "sort_key": {
        "blocker_count": 1,
        "estimated_cost_present": true,
        "estimated_cost_bps": 7.4,
        "allocation_coverage_ratio": 1.0,
        "strategy_priority": 0
      },
      "recommended": true
    }
  ],
  "recommended_strategy": "multi_venue",
  "recommended_reason": "feasible_route_with_lowest_blockers_lowest_estimated_cost",
  "recommended_estimated_cost_bps": 7.4,
  "recommended_allocation_coverage_ratio": 1.0,
  "recommended_allocation_shortfall_quantity": 0.0,
  "recommended_sort_rank": 1,
  "recommended_tie_break_reason": "lowest_estimated_cost_bps",
  "execution_disabled": true
}
```

Notes:
- Runs each requested strategy through the same non-executing route-evaluation path as `/live/execution/place/route`.
- Returns deterministic recommendation using lowest blocker count, then lowest estimated route cost, then strategy preference (`multi_venue` > `single_venue` > `intent`) on ties.
- Includes coverage/shortfall diagnostics per option and in the recommended summary for operator-side route-capacity validation.
- Includes explicit sort diagnostics (`sort_rank`, `sort_key`, `recommended`) and top-level tie-break attribution (`recommended_tie_break_reason`) for replay/debug.
- When no strategy is feasible and the selected winner contains allocation shortfall blockers, `recommended_reason` is tagged with `no_feasible_route_capacity_shortfall_*`; other allocation constraint blockers use `no_feasible_route_constraint_failure_*`.
- This endpoint never submits orders.

### `POST /live/execution/place`
Request:
```json
{
  "intent_id": "2d8f5913-4dc3-4924-af80-574147f38b56",
  "provider": "coinbase_sandbox",
  "strategy": "auto",
  "max_venues": 2,
  "min_venues": 1,
  "max_venue_ratio": 0.7,
  "min_slice_quantity": 0.25,
  "max_slippage_bps": 25.0
}
```

Response:
```json
{
  "accepted": false,
  "execution_disabled": true,
  "reason": "phase2_live_execution_path_disabled",
  "execution_mode": "live_place",
  "submission_id": "d2c7e7d0-3255-4b34-ae33-087fe4b58f03",
  "provider": "coinbase_sandbox",
  "venue": "coinbase",
  "strategy": "single_venue",
  "requested_strategy": "auto",
  "resolved_strategy": "single_venue",
  "strategy_resolution_reason": "feasible_route_with_lowest_blockers_lowest_estimated_cost",
  "strategy_resolution_tie_break_reason": "lowest_estimated_cost_bps",
  "selected_venue": "coinbase",
  "route_eligible": true,
  "feasible_route": true,
  "provider_supported_venues": [
    "coinbase"
  ],
  "provider_venue_compatible": true,
  "recommended_slices": [
    {
      "venue": "coinbase",
      "quantity": 1.0,
      "weight": 1.0
    }
  ],
  "requested_quantity": 1.0,
  "allocated_quantity": 1.0,
  "allocation_coverage_ratio": 1.0,
  "allocation_shortfall_quantity": 0.0,
  "rejected_venues": [
    {
      "venue": "binance",
      "reason": "provider_venue_not_supported"
    }
  ],
  "total_estimated_cost_bps": 8.0,
  "blockers": [
    "phase2_live_execution_path_disabled"
  ],
  "intent": {
    "id": "2d8f5913-4dc3-4924-af80-574147f38b56",
    "status": "submit_blocked_live",
    "approved_for_live": true,
    "execution_disabled": true
  }
}
```

Notes:
- This is a Phase 3 contract stub only; in Phase 2 it always blocks by design.
- Request supports venue-routing strategy controls: `strategy` (`intent`/`single_venue`/`multi_venue`/`auto`), `max_venues`, `min_venues`, `max_venue_ratio`, `min_slice_quantity`, and `max_slippage_bps`.
- `strategy=auto` resolves through `/live/execution/place/route/compare` and records `requested_strategy`, `resolved_strategy`, `strategy_resolution_reason`, and `strategy_resolution_tie_break_reason`.
- Includes route-level estimated cost output (`total_estimated_cost_bps`) for operator review and placement attempt audit payloads.
- Provider/venue compatibility is enforced in route evaluation and reflected in `provider_supported_venues`, `provider_venue_compatible`, and mismatch blockers.
- Persists blocked attempts into `live_execution_submissions` with `mode=live_place` for audit/replay.

### `POST /live/execution/submit`
Request:
```json
{
  "intent_id": "2d8f5913-4dc3-4924-af80-574147f38b56",
  "mode": "dry_run"
}
```

Supported `mode` values:
- `dry_run` (default)
- `sandbox_submit` (strict opt-in)
- `live_place` (delegates to `/live/execution/place`, blocked in Phase 2)

Optional `live_place` routing fields:
- `strategy` (`intent`/`single_venue`/`multi_venue`/`auto`)
- `max_venues`
- `min_venues`
- `max_venue_ratio`
- `min_slice_quantity`
- `max_slippage_bps`

Dry-run response:
```json
{
  "accepted": false,
  "execution_disabled": true,
  "reason": "execution_disabled_flag, deployment_not_armed",
  "execution_mode": "dry_run",
  "submission_id": "f4c2ea9a-c978-4e3a-b44a-ecf95240ee65",
  "provider": null,
  "sandbox": false,
  "intent": {
    "id": "2d8f5913-4dc3-4924-af80-574147f38b56",
    "status": "submit_blocked_dry_run",
    "approved_for_live": true,
    "execution_disabled": true
  }
}
```

Sandbox-submit response (when enabled and all gates pass):
```json
{
  "accepted": true,
  "execution_disabled": false,
  "reason": "submitted_to_exchange_sandbox",
  "execution_mode": "sandbox_submit",
  "submission_id": "8c2192ca-9bf3-4c27-a366-6f9ad30089dd",
  "provider": "mock",
  "venue": "coinbase",
  "venue_order_id": "sbox-coinbase-livedryrun001",
  "submitted_at": "2026-03-11T07:15:00Z",
  "sandbox": true,
  "intent": {
    "id": "2d8f5913-4dc3-4924-af80-574147f38b56",
    "status": "submitted_sandbox",
    "approved_for_live": true
  }
}
```

Live-place response (delegated contract, blocked in Phase 2):
```json
{
  "accepted": false,
  "execution_disabled": true,
  "reason": "phase2_live_execution_path_disabled",
  "execution_mode": "live_place",
  "submission_id": "d2c7e7d0-3255-4b34-ae33-087fe4b58f03",
  "provider": "coinbase_sandbox",
  "venue": "coinbase",
  "sandbox": false,
  "intent": {
    "id": "2d8f5913-4dc3-4924-af80-574147f38b56",
    "status": "submit_blocked_live",
    "approved_for_live": true
  }
}
```

Notes:
- Validates persisted dry-run intent + governance state.
- `mode=dry_run` remains blocked and never submits.
- `mode=sandbox_submit` is strict opt-in (`LIVE_EXECUTION_SANDBOX_ENABLED=true`) with provider dispatch via `LIVE_EXECUTION_PROVIDER`.
- Supported sandbox providers: `mock`, `coinbase_sandbox` (both stubbed contract paths; no real-capital execution).
- Optional Coinbase sandbox HTTP transport is gated by `LIVE_EXECUTION_SANDBOX_TRANSPORT_ENABLED=true`; when enabled it also requires `COINBASE_API_PASSPHRASE`.
- Each submit call persists a `live_execution_submissions` record (including blocked paths) and returns `submission_id` when persistence is available.

### `GET /alerts/paper/risk`
Response:
```json
{
  "status": "ok",
  "triggered": [
    {
      "type": "paper_drawdown_breach",
      "severity": "low",
      "message": "Paper max drawdown 12.50% breached threshold 10.00%",
      "metric": "max_drawdown_pct",
      "value": 12.5,
      "threshold": 10.0,
      "as_of": "2026-03-11T02:05:00Z"
    },
    {
      "type": "paper_concentration_breach",
      "severity": "low",
      "message": "Paper concentration 65.00% breached threshold 60.00%",
      "metric": "concentration_pct",
      "value": 65.0,
      "threshold": 60.0,
      "as_of": "2026-03-11T02:05:00Z"
    }
  ],
  "metrics": {
    "equity": 100120.55,
    "gross_exposure_usd": 1000.0,
    "max_drawdown_pct": 12.5,
    "concentration_pct": 65.0
  },
  "thresholds": {
    "drawdown_pct": 10.0,
    "concentration_pct": 60.0
  }
}
```

Notes:
- Evaluated against `execution_sim` `summary` + `performance`.
- Thresholds are configurable via `PAPER_ALERT_DRAWDOWN_PCT_THRESHOLD` and `PAPER_ALERT_CONCENTRATION_PCT_THRESHOLD`.

### `POST /documents/search`
Request:
```json
{
  "query": "SOL roadmap unlock validator growth",
  "asset": "SOL",
  "timeline": ["past", "present", "future"],
  "limit": 10
}
```

Response:
```json
{
  "results": [
    {
      "id": "b0d9f12a-703d-4b1a-9397-4f3f02f4e4f1",
      "source": "newsapi",
      "title": "SOL validator growth update",
      "url": "https://example.org/sol-update",
      "timeline": "present",
      "confidence": 0.84,
      "published_at": "2026-03-10T20:45:00Z",
      "snippet": "Validator count climbed while liquidity improved."
    }
  ]
}
```

Failure:
- `503` when memory service is unavailable.

### `GET /market/{symbol}/snapshot`
Example:
- `GET /market/BTC-USD/snapshot`

Response:
```json
{
  "symbol": "BTC-USD",
  "exchange": "coinbase",
  "last_price": "84250.12",
  "bid": "84249.90",
  "ask": "84250.20",
  "spread": "0.30",
  "timestamp": "2026-03-10T21:45:00Z"
}
```

Failure:
- `503` when market-data service is unavailable.

## Orchestrator (`:8001`)

### `POST /explain`
Request:
```json
{
  "asset": "SOL",
  "question": "Why is SOL moving?"
}
```

Behavior:
- Pulls market snapshot.
- Triggers news ingestion.
- Pulls recent news.
- Pulls historical archive context.
- Pulls future-timeline memory context.
- Calls risk stub and enforces `execution_disabled`.
- Optionally polishes phrasing with LLM if API key exists.
- Persists explanation record.
- Emits audit events for request, dependency calls, and completion/failure.

Degraded mode:
- Any dependency can fail independently.
- Orchestrator still returns valid response with fallbacks.

## Market Data (`:8002`)

### `GET /market/{symbol}/snapshot`
Behavior:
- Tries Coinbase public ticker endpoints.
- Falls back to seeded/default values if remote fetch fails.
- Persists snapshot in `market_snapshots`.

## News Ingestion (`:8003`)

### `POST /ingest/news`
Request:
```json
{ "asset": "SOL" }
```

Response:
```json
{
  "inserted": 2,
  "asset": "SOL"
}
```

### `GET /news/{asset}`
Response:
```json
{
  "asset": "SOL",
  "items": [
    {
      "id": "94ccf5ab-4be6-48ad-98aa-5d12dc0f6764",
      "title": "SOL rises as active addresses climb",
      "url": "https://example.org/sol-news",
      "timeline": "present",
      "published_at": "2026-03-10T20:45:00Z",
      "confidence": 0.7,
      "source": "newsapi"
    }
  ]
}
```

## Archive Lookup (`:8004`)

### `GET /archive/{asset}`
Response:
```json
{
  "asset": "SOL",
  "items": [
    {
      "title": "Historical Solana roadmap milestone precedent",
      "url": "https://web.archive.org/...",
      "timeline": "past",
      "timestamp": "2025-03-10T21:00:00Z",
      "source": "wayback"
    }
  ]
}
```

## Parser/Normalizer (`:8005`)

### `POST /normalize`
Request:
```json
{
  "title": "SOL roadmap update for next quarter",
  "url": "https://example.org/post",
  "html": "<h1>Roadmap</h1><p>Mainnet update planned next month.</p>"
}
```

Response:
```json
{
  "title": "SOL roadmap update for next quarter",
  "url": "https://example.org/post",
  "raw_text": null,
  "cleaned_text": "Roadmap Mainnet update planned next month.",
  "timeline": "future",
  "asset_tags": ["SOL"],
  "content_hash": "sha256-..."
}
```

## Memory (`:8006`)

### `POST /search`
Request:
```json
{
  "query": "SOL roadmap unlock validator growth",
  "asset": "SOL",
  "timeline": ["past", "present", "future"],
  "limit": 10
}
```

Response:
```json
{
  "results": []
}
```

Behavior:
- Primary retrieval from Postgres documents/events.
- Qdrant is optional and can be absent without failure.

## Risk Stub (`:8007`)

### `POST /risk/evaluate`
Request:
```json
{
  "asset": "SOL",
  "mode": "paper",
  "requested_action": "open_position",
  "proposed_notional_usd": 1200.0,
  "position_qty": 2.5,
  "daily_pnl": -45.0
}
```

Response:
```json
{
  "execution_disabled": true,
  "approved": false,
  "paper_approved": false,
  "gate": "FULL_STOP",
  "allowed_actions": ["OBSERVE_ONLY"],
  "reason": "Phase 1 research mode only",
  "requested_action": "open_position",
  "limits": {
    "paper_max_notional_usd": 25000.0,
    "paper_max_position_qty": 100.0,
    "paper_daily_loss_limit_usd": 2000.0
  }
}
```

Gate values:
- `ALLOW`
- `ALLOW_REDUCE_ONLY`
- `HALT_NEW_EXPOSURE`
- `FULL_STOP`

Notes:
- `approved` remains `false` because live execution is disabled in this phase.
- `paper_approved` may be `true` only when `mode=paper` and `PAPER_TRADING_ENABLED=true`.
- `paper_approved` is action-aware (`open_position` vs `reduce_position`).
- `HALT_NEW_EXPOSURE` and `ALLOW_REDUCE_ONLY` reject new exposure but allow risk reduction.

## Execution Sim (`:8009`)

Paper-only execution scaffold. No live trading.

### `GET /metrics`
Prometheus text exposition including:
- `paper_order_attempt_total`
- `paper_order_submit_total`
- `paper_order_reject_total{reason=...}`
- `paper_order_latency_seconds` histogram buckets/count/sum

### `POST /paper/orders`
Request:
```json
{
  "symbol": "SOL-USD",
  "side": "buy",
  "order_type": "market",
  "quantity": 1.25,
  "client_order_id": "paper-optional-id",
  "signal_source": "regime_model_v1",
  "rationale": "Momentum continuation with fresh news confirmation",
  "catalyst_tags": ["governance", "roadmap"],
  "metadata": {}
}
```

Approval gate:
- If `PAPER_ORDER_REQUIRE_APPROVAL=true`, gateway rejects order submissions unless request metadata contains `"user_approved": true`.

Response:
```json
{
  "id": "d5955f0d-2455-404a-8cf5-e1468e407963",
  "client_order_id": "paper-abc123",
  "symbol": "SOL-USD",
  "side": "buy",
  "order_type": "market",
  "status": "filled",
  "quantity": 1.25,
  "limit_price": null,
  "filled_quantity": 1.25,
  "average_fill_price": 145.2,
  "risk_gate": "ALLOW",
  "signal_source": "regime_model_v1",
  "rationale": "Momentum continuation with fresh news confirmation",
  "catalyst_tags": ["governance", "roadmap"],
  "execution_disabled": true,
  "paper_mode": true
}
```

### `GET /paper/orders`
Query params:
- `symbol` (optional)
- `status` (optional: `open`, `filled`, `canceled`)
- `since` (optional ISO timestamp)
- `cursor` (optional ISO timestamp cursor for pagination)
- `limit` (optional, default `50`, max `200`)
- `sort` (optional `asc|desc`, default `desc`)

Response:
```json
{
  "orders": [
    {
      "id": "d5955f0d-2455-404a-8cf5-e1468e407963",
      "client_order_id": "paper-abc123",
      "symbol": "SOL-USD",
      "side": "buy",
      "order_type": "market",
      "status": "filled",
      "quantity": 1.25,
      "filled_quantity": 1.25,
      "average_fill_price": 145.2,
      "execution_disabled": true,
      "paper_mode": true
    }
  ],
  "next_cursor": "2026-03-10T21:00:00Z",
  "has_more": false
}
```

### `GET /paper/orders/{order_id}`
Returns one paper order or `404` if absent.

### `POST /paper/orders/{order_id}/cancel`
Returns:
```json
{
  "canceled": true,
  "order": { "...paper order fields..." : "..." }
}
```

### `GET /paper/fills`
Query params:
- `symbol` (optional)
- `order_id` (optional UUID)
- `since` (optional ISO timestamp)
- `cursor` (optional ISO timestamp cursor for pagination)
- `limit` (optional, default `100`, max `500`)
- `sort` (optional `asc|desc`, default `desc`)

Response:
```json
{
  "fills": [
    {
      "id": "930f6d38-07ca-4ced-8447-d6b0293adb2f",
      "order_id": "d5955f0d-2455-404a-8cf5-e1468e407963",
      "symbol": "SOL-USD",
      "side": "buy",
      "price": 145.2,
      "quantity": 1.25,
      "fee": 0.12,
      "liquidity": "taker",
      "created_at": "2026-03-10T21:00:01Z"
    }
  ],
  "next_cursor": null,
  "has_more": false
}
```

### `GET /paper/positions`
Returns:
```json
{
  "positions": []
}
```

### `GET /paper/summary`
Response:
```json
{
  "as_of": "2026-03-10T21:10:00Z",
  "cash": 99800.25,
  "realized_pnl": 45.10,
  "unrealized_pnl": 320.30,
  "equity": 100120.55,
  "gross_exposure_usd": 181.50,
  "positions": [
    {
      "symbol": "SOL-USD",
      "quantity": 1.25,
      "avg_entry_price": 145.2,
      "mark_price": 145.2,
      "notional_usd": 181.5,
      "unrealized_pnl": 0.0
    }
  ]
}
```

### `GET /paper/performance`
Query params:
- `since` (optional ISO timestamp)
- `limit` (optional number of equity points considered, default `5000`)

Response:
```json
{
  "as_of": "2026-03-10T21:15:00Z",
  "points": 12,
  "period_start": "2026-03-10T00:00:00Z",
  "start_equity": 100000.0,
  "end_equity": 100120.55,
  "return_pct": 0.12055,
  "high_watermark": 100200.0,
  "low_equity": 99950.0,
  "max_drawdown_usd": 250.0,
  "max_drawdown_pct": 0.2495,
  "benchmark_name": "BTC_ETH_50_50",
  "benchmark_return_pct": 0.09,
  "excess_return_pct": 0.03,
  "sharpe_proxy": 0.55,
  "hit_rate": 58.33,
  "hit_rate_by_regime": {
    "unknown": 58.33
  }
}
```

### `POST /paper/performance/rollups/refresh`
Request:
```json
{
  "interval": "daily",
  "since": "2026-03-01T00:00:00Z"
}
```

Response:
```json
{
  "interval": "daily",
  "refreshed": 8
}
```

### `GET /paper/performance/rollups`
Query params:
- `interval` (`hourly|daily`, default `daily`)
- `since` (optional ISO timestamp)
- `limit` (optional, default `200`, max `1000`)
- `sort` (optional `asc|desc`, default `desc`)

Response:
```json
{
  "rollups": [
    {
      "interval": "hourly",
      "bucket_start": "2026-03-10T21:00:00Z",
      "bucket_end": "2026-03-10T21:44:00Z",
      "points": 5,
      "start_equity": 100000.0,
      "end_equity": 100120.0,
      "return_pct": 0.12,
      "high_watermark": 100130.0,
      "low_equity": 99995.0,
      "max_drawdown_usd": 35.0,
      "max_drawdown_pct": 0.0349,
      "benchmark_name": "BTC_ETH_50_50",
      "benchmark_return_pct": 0.08,
      "excess_return_pct": 0.04
    }
  ]
}
```

### `GET /paper/readiness`
Response:
```json
{
  "as_of": "2026-03-11T02:15:00Z",
  "phase3_live_eligible": false,
  "reason": "insufficient_paper_days",
  "min_days_required": 7,
  "min_points_required": 24,
  "observed_days": 2.1,
  "observed_points": 31,
  "return_pct": 1.2,
  "max_drawdown_pct": 3.1,
  "sharpe_proxy": 0.55
}
```

### `POST /paper/maintenance/retention`
Request:
```json
{
  "days": 30
}
```

### `POST /paper/replay/run`
Request:
```json
{
  "symbol": "SOL-USD",
  "start": "2026-03-01T00:00:00Z",
  "end": "2026-03-10T00:00:00Z",
  "entry_bps": 10.0,
  "hold_steps": 1
}
```

Response:
```json
{
  "symbol": "SOL-USD",
  "strategy": "momentum_v1",
  "start": "2026-03-01T00:00:00Z",
  "end": "2026-03-10T00:00:00Z",
  "points": 1200,
  "trades": 45,
  "gross_return_pct": 6.4,
  "max_drawdown_pct": 2.2,
  "status": "ok"
}
```

### `POST /paper/shadow/compare`
Request:
```json
{
  "symbol": "SOL-USD",
  "start": "2026-03-01T00:00:00Z",
  "end": "2026-03-10T00:00:00Z",
  "champion_entry_bps": 10.0,
  "challenger_entry_bps": 5.0,
  "hold_steps": 1
}
```

Response:
```json
{
  "symbol": "SOL-USD",
  "start": "2026-03-01T00:00:00Z",
  "end": "2026-03-10T00:00:00Z",
  "points": 1200,
  "champion_return_pct": 4.2,
  "challenger_return_pct": 5.1,
  "delta_return_pct": 0.9,
  "champion_trades": 41,
  "challenger_trades": 50,
  "winner": "challenger",
  "status": "ok"
}
```

Response:
```json
{
  "as_of": "2026-03-11T02:20:00Z",
  "retention_days": 30,
  "deleted_fills": 100,
  "deleted_orders": 100,
  "deleted_equity_points": 240,
  "deleted_rollups": 14
}
```

### `GET /paper/balances`
Returns:
```json
{
  "balances": [
    {
      "asset": "USD",
      "balance": 100000.0,
      "available": 100000.0
    }
  ]
}
```

### `POST /paper/equity/snapshot`
Request:
```json
{ "note": "manual" }
```

Response:
```json
{
  "ts": "2026-03-10T21:00:00Z",
  "equity": 100120.55,
  "cash": 99800.25,
  "unrealized_pnl": 320.30,
  "realized_pnl": 45.10,
  "note": "manual"
}
```

### `GET /paper/equity`
Query params:
- `since` (optional ISO timestamp)
- `limit` (optional, default `200`)
- `sort` (optional `asc|desc`, default `desc`)

Response:
```json
{
  "points": [
    {
      "ts": "2026-03-10T21:00:00Z",
      "equity": 100120.55,
      "cash": 99800.25,
      "unrealized_pnl": 320.30,
      "realized_pnl": 45.10,
      "note": "manual"
    }
  ]
}
```

Fill model notes:
- Market orders apply deterministic slippage via `PAPER_MARKET_SLIPPAGE_BPS`.
- Fills apply deterministic fees via `PAPER_FEE_BPS`.
- Limit orders can remain open if market price is unavailable.
- Current scaffold is long-only in paper mode (opening short exposure is rejected).

## Audit Log (`:8008`)

### `POST /audit/log`
Request:
```json
{
  "service_name": "orchestrator",
  "event_type": "response_returned",
  "request_id": "f65af8d2-4e2a-4e43-9396-fc8a4a1c9af2",
  "entity_type": "explanation",
  "entity_id": "SOL",
  "level": "INFO",
  "message": "Explain response generated",
  "payload": {
    "asset": "SOL",
    "confidence": 0.78
  }
}
```

Response:
```json
{ "status": "ok" }
```

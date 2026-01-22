# Live + WS Guardrails (Phase 238)

Enforces WS safety in LIVE mode. If marketdata.ws_use_for_trading == true:
- marketdata.ws_enabled must be true
- ws_health.enabled must be true
- Must have safe fallback (REST or auto-switch) or allow_ws_strict=true

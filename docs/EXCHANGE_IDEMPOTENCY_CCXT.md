# Phase 260 — Exchange-level Idempotency (CCXT params)

Goal:
- If the bot restarts, duplicate submits are rejected by the exchange using a deterministic client order id.

Mechanism:
- Runner (Phase 259) creates `client_oid` from `intent_id`.
- Phase 260 injects `client_oid` into CCXT `params` using config mapping:
  - binance: newClientOrderId
  - coinbase: clientOrderId
  - gateio: text

Config:
live_execution:
  idempotency_enabled: true
  idempotency_param_map:
    binance: newClientOrderId
    coinbase: clientOrderId
    gateio: text

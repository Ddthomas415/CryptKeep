# Remaining Tasks

Source: `CHECKPOINTS.md`

## Summary
- Total non-✅ items: 9
- 🔄 In progress: 0
- 🟡 Partial: 1
- ⏳ Not started: 8
- ⚠️ Constraint/note: 0

## 🔄 In Progress (0)


## 🟡 Partial (1)

- IG4: fill-based position accounting foundation added; cash/positions/realized/unrealized MTM snapshot covered; equity_by_quote + single-quote total_equity added; cross-quote aggregate equity supported with explicit FX marks
  Source: `CHECKPOINTS.md:596`

## ⏳ Not Started (8)

- LL6: Replace local role selector with real auth (OS keychain login / OAuth / SSO) (later)
  Source: `CHECKPOINTS.md:780`
- MB8: Multi-quote internal cash ledger (schema v2) if you need simultaneous USD+USDT accounting (future, optional)
  Source: `CHECKPOINTS.md:830`
- Next: “Ops intelligence” learning/adaptability module path (market data ingestion → feature store → model training → safe deployment gates)
  Source: `CHECKPOINTS.md:1001`
- Next: wire ML into decision flow (paper mode first), add monitoring + rollback triggers, integrate imported trader signals as features
  Source: `CHECKPOINTS.md:1089`
- Next: execution + reconciliation layer (idempotent orders, restart-safe state, latency-aware order placement) + add “best venue routing” in paper first
  Source: `CHECKPOINTS.md:1098`
- Next: trade-level reconciliation (fetch_my_trades) for partial fills, fee correctness, and robust restart recovery; then LIVE_SHADOW (observe-only) before any live ML gating
  Source: `CHECKPOINTS.md:1107`
- Next: true multi-role metadata (root/targets/timestamp/snapshot) + key rotation policy + threshold signatures; then WebSocket market data + event-driven execution for latency reduction
  Source: `CHECKPOINTS.md:1132`
- Next: packaging/installers (Mac + Windows) as a single installable app + one-command setup; then multi-exchange live safety UX (Coinbase/Binance/Gate.io) inside UI
  Source: `CHECKPOINTS.md:1151`

## ⚠️ Constraint / Note (0)

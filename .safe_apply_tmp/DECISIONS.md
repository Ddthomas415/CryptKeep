# Crypto Bot Pro — DECISIONS (Canonical)

Last updated: 2025-12-15 (America/New_York)

## Objective (Do not drift)
Build "Crypto Bot Pro" as an installable desktop app for macOS + Windows that runs a safe, reliable crypto trading system with:
- Bounded, auditable learning/adaptation
- Market-relevant monitoring
- Optional learning-from-traders via authorized APIs/webhooks (no scraping/ToS violations)
- First-class venues: Gate.io, Coinbase, Binance

## Standing Orders (Non-negotiable)
1) No fluff. Only actionable steps, minimal verbosity.
2) No misleading paths. If uncertain: label it and choose the safest path.
3) Safety-first engineering:
   - paper-first
   - hard risk limits
   - kill switch
   - idempotent orders
   - restart-safe reconciliation
4) Compliance: official APIs/webhooks only for signals/copy; no scraping private endpoints.
5) Backtest/live parity: same order rules, fees, slippage model, risk engine.
6) Secrets never in code: OS keychain/env; preflight validates presence.
7) Single gold repo only: no duplicates, no forked “versions” in parallel.
8) Each work session must update CHECKPOINTS.md statuses (✅ 🔄 🟡 ⏳).

## Locked Implementation Path (Unless explicitly changed)
- Desktop shell: Tauri
- UI v1: Streamlit runs locally; desktop app opens it
- Backend: Python services packaged per-OS (PyInstaller), bundled as a sidecar
- Core venues: native adapters for Gate.io + Coinbase + Binance
- CCXT: optional fallback only (not the primary execution path)

## Safety Defaults (Must exist before any Live Trading)
- Max daily loss (hard stop)
- Max position size / exposure cap
- Max trades/day
- Volatility halt (circuit breaker)
- “Live trading unlock” requires explicit operator confirmation and config flag
- Kill switch: local + UI + process termination behavior

## Out of Scope (Until core is stable)
- HFT/colocation claims or “zero latency” guarantees
- Unbounded RL controlling position sizing directly
- Any ToS-violating data collection from trader platforms

## Definition of Done (Core)
- Deterministic replay: same input data => same signals/trades in paper sim
- Reconciliation: restart mid-run does NOT create duplicate orders
- Backtest/live parity verified on a baseline strategy
- Desktop installers: macOS app + Windows MSI/EXE installer

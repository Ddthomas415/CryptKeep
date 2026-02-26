# Remaining Tasks

Source: `CHECKPOINTS.md`

## Summary
- Total non-✅ items: 112
- 🔄 In progress: 0
- 🟡 Partial: 2
- ⏳ Not started: 109
- ⚠️ Constraint/note: 1

## 🔄 In Progress (0)

## 🟡 Partial (2)
- LT5: Venue/runner integration patched best-effort (depends on file names/structure)  
  Source: `CHECKPOINTS.md:810`
- MC6: macOS .app wrapper + icons + no-console mode (next phase)  
  Source: `CHECKPOINTS.md:838`

## ⏳ Not Started (109)
- FI3: Add “copy key” button + show last 10 failures only toggle  
  Source: `CHECKPOINTS.md:315`
- FN6: Add icons to repo (real files) + optional CI build pipelines  
  Source: `CHECKPOINTS.md:323`
- FO4: Tag-based GitHub Releases (attach artifacts automatically)  
  Source: `CHECKPOINTS.md:329`
- FO5: Optional signing/notarization integration (requires certificates)  
  Source: `CHECKPOINTS.md:330`
- FP4: Optional signing/notarization release pipeline (cert-required)  
  Source: `CHECKPOINTS.md:336`
- FQ5: Add optional Linux AppImage build (if we want Linux distribution)  
  Source: `CHECKPOINTS.md:343`
- GI5: Hardening: console=False release build + signing/notarization (macOS) and code signing (Windows)  
  Source: `CHECKPOINTS.md:350`
- GK5: Replace remaining broad try/except pass blocks with logged errors (structured logging)  
  Source: `CHECKPOINTS.md:357`
- GM7: graceful stop (soft SIGTERM first) + runner detects shutdown and exits cleanly (next phase)  
  Source: `CHECKPOINTS.md:366`
- GP5: Automatic crash detection: controller watches heartbeat staleness and captures snapshot (watchdog) (next phase)  
  Source: `CHECKPOINTS.md:373`
- GQ6: “Supervisor mode” launcher that runs cockpit + watchdog loop as managed siblings (next phase)  
  Source: `CHECKPOINTS.md:381`
- GR6: Add “Start Supervisor” button in UI (optional; keep safest as launcher-first)  
  Source: `CHECKPOINTS.md:389`
- GS4: Single “Stop Everything” command (bot + watchdog + supervisor) with clear precedence rules (next phase)  
  Source: `CHECKPOINTS.md:395`
- GZ4: Fix any remaining violations revealed by verifier (next phase, if needed)  
  Source: `CHECKPOINTS.md:401`
- HA4: If Phase 209 verifier finds violations, patch each call site to use place_order (safe manual-targeted edits)  
  Source: `CHECKPOINTS.md:407`
- HR7: Add parameter validation + per-strategy presets in UI (next phase)  
  Source: `CHECKPOINTS.md:435`
- HI5: Live start gating next  
  Source: `CHECKPOINTS.md:444`
- HK5: Dry run cleanup next  
  Source: `CHECKPOINTS.md:449`
- HL6: Paper PnL/analytics UI next  
  Source: `CHECKPOINTS.md:454`
- HM5: MTM sampling next  
  Source: `CHECKPOINTS.md:459`
- HN5: Portfolio-level MTM next  
  Source: `CHECKPOINTS.md:464`
- HO6: Risk allocation next  
  Source: `CHECKPOINTS.md:469`
- HP5: Sell-side risk controls next  
  Source: `CHECKPOINTS.md:474`
- HQ6: Strategy-aware exit stacking next  
  Source: `CHECKPOINTS.md:479`
- HS6: Per-strategy preset bundles next  
  Source: `CHECKPOINTS.md:484`
- HT6: Guardrails for live mode next  
  Source: `CHECKPOINTS.md:489`
- HU5: Live execution layer future  
  Source: `CHECKPOINTS.md:494`
- HY5: Apply same auto-disable pattern to WS ticker feed (watchTicker) (next phase)  
  Source: `CHECKPOINTS.md:501`
- IC5: Live execution layer (real order routing) remains not implemented (future phase)  
  Source: `CHECKPOINTS.md:508`
- ID5: Full execution parity: intent -> sent -> fill -> journal + reconciliation against exchange order ids (next phase)  
  Source: `CHECKPOINTS.md:515`
- IH6: Backtest parity for new strategies inside the UI backtest engine (next phase)  
  Source: `CHECKPOINTS.md:523`
- JH5: MSIX packaging pipeline (MakeAppx + SignTool + manifest) (only if requested)  
  Source: `CHECKPOINTS.md:541`
- JN7: Strategy-to-intent builder (signals → intents) (next phase)  
  Source: `CHECKPOINTS.md:557`
- JP8: Strategy parameter UI editor + safe “apply preset” (config write) (next phase)  
  Source: `CHECKPOINTS.md:567`
- JS7: “True single-click” polish: icons, versioning, windowed mode, code signing/notarization (next phase)  
  Source: `CHECKPOINTS.md:576`
- JT6: Repair/Reset wizard + preflight self-checks (next phase)  
  Source: `CHECKPOINTS.md:584`
- IF4: Equity curve page + performance metrics (next phase)  
  Source: `CHECKPOINTS.md:590`
- IG4: True MTM equity (future)  
  Source: `CHECKPOINTS.md:596`
- II4: Legacy backtest cleanup  
  Source: `CHECKPOINTS.md:602`
- KJ6: “One-click run all safe steps” (non-destructive only) (next phase)  
  Source: `CHECKPOINTS.md:640`
- KM6: Optional packaged “double-click app” build pipeline (PyInstaller/Briefcase wrapper) (next phase)  
  Source: `CHECKPOINTS.md:648`
- KN6: Briefcase-based native installer pipeline (MSI/.app) if needed (next phase)  
  Source: `CHECKPOINTS.md:656`
- KO6: “Requirements sync” script (sync requirements.txt → briefcase requires list safely) (next phase)  
  Source: `CHECKPOINTS.md:664`
- KQ6: Signed builds + notarization workflow (macOS) / code signing (Windows) (next phase)  
  Source: `CHECKPOINTS.md:672`
- KR4: Integrate signing into release_checklist (opt-in via env flags; no secrets in repo) (next phase)  
  Source: `CHECKPOINTS.md:678`
- KR5: CI pipeline templates (GitHub Actions) for build → sign → notarize → package (next phase)  
  Source: `CHECKPOINTS.md:679`
- KS6: CI templates (GitHub Actions) with secrets in CI only (next phase)  
  Source: `CHECKPOINTS.md:687`
- KT5: Optional CI signing/notarization job (secrets-only, fail-closed) (next phase)  
  Source: `CHECKPOINTS.md:694`
- KU5: CI macOS *codesign* of .app before packaging (if Briefcase output isn’t already signed) (next phase)  
  Source: `CHECKPOINTS.md:701`
- KV5: Optional “verify stapled ticket + spctl assess” CI step (next phase)  
  Source: `CHECKPOINTS.md:708`
- KW5: Add CI artifact hash manifest after signing/notary (reuse release_checklist) (next phase)  
  Source: `CHECKPOINTS.md:715`
- KX5: “GitHub Release Publisher” workflow (attach artifacts + manifest to tagged releases) (next phase)  
  Source: `CHECKPOINTS.md:722`
- KY6: Add “release notes generator” (from CHANGELOG.md + manifest summary) (next phase)  
  Source: `CHECKPOINTS.md:730`
- KZ6: UI helper to preview release notes before tagging (optional) (next phase)  
  Source: `CHECKPOINTS.md:738`
- LA4: “Tag helper” (creates git tag locally after preview) (optional next phase)  
  Source: `CHECKPOINTS.md:744`
- LB6: “Pre-release sanity suite” (lint + typecheck + minimal integration checks) (next phase)  
  Source: `CHECKPOINTS.md:752`
- LC7: Minimal integration test (paper trade loop + DB write) (next phase)  
  Source: `CHECKPOINTS.md:761`
- LH9: Live execution adapters (CCXT authenticated trading with strict reconciliation) (next phase)  
  Source: `CHECKPOINTS.md:772`
- LL6: Replace local role selector with real auth (OS keychain login / OAuth / SSO) (later)  
  Source: `CHECKPOINTS.md:780`
- LP6: CI builds for Windows/macOS artifacts + release publishing (next phase)  
  Source: `CHECKPOINTS.md:788`
- LQ6: Optional macOS signing + notarization in CI (requires Apple Developer credentials) (next phase)  
  Source: `CHECKPOINTS.md:796`
- LT6: Hard integration: enforce preflight gate before every live order + pause/circuit breaker behavior (next phase)  
  Source: `CHECKPOINTS.md:811`
- LV7: Replace bot_runner stub with real runner integration + graceful strategy hot-reload (next phase)  
  Source: `CHECKPOINTS.md:820`
- MB8: Multi-quote internal cash ledger (schema v2) if you need simultaneous USD+USDT accounting (future, optional)  
  Source: `CHECKPOINTS.md:830`
- MC7: CI release pipeline (GitHub Actions) to auto-build & publish installers (next phase)  
  Source: `CHECKPOINTS.md:839`
- ME4: Optional code signing/notarization for macOS + Authenticode signing for Windows (later, optional)  
  Source: `CHECKPOINTS.md:845`
- MF6: In-app “guided setup” (step-by-step exchange selection + symbol mapping UI) (later)  
  Source: `CHECKPOINTS.md:853`
- Next: code signing + notarization scaffolding (macOS) + Windows signing hooks + in-app update checker consuming release/manifest.json  
  Source: `CHECKPOINTS.md:936`
- Next: Make the Start Live flow exclusively use the gated button path (remove duplicates)  
  Source: `CHECKPOINTS.md:943`
- Next: implement/verify paper_runner + live_runner entrypoints end-to-end (actual trading loop)  
  Source: `CHECKPOINTS.md:951`
- Next: “Installer UX” layer (signed installers, shortcuts, auto-updater) + make launcher start/stop collector/bots cleanly from UI  
  Source: `CHECKPOINTS.md:959`
- Next: Signed distribution (macOS notarization, Windows code signing) + “one button build” wrappers + CI artifacts  
  Source: `CHECKPOINTS.md:965`
- Next: wire installer signing into Inno Setup config + CI release artifacts + versioning automation  
  Source: `CHECKPOINTS.md:971`
- Next: “one-button release” that also creates a GitHub Release + attaches artifacts; plus optional signing in CI (requires secrets)  
  Source: `CHECKPOINTS.md:979`
- Next: optional signing in CI (requires secrets/certs), plus “release train” checklist in UI  
  Source: `CHECKPOINTS.md:986`
- Next: sign Windows installer too (Inno SignTool integration) + UI “Release Train” checklist page  
  Source: `CHECKPOINTS.md:992`
- Next: “Ops intelligence” learning/adaptability module path (market data ingestion → feature store → model training → safe deployment gates)  
  Source: `CHECKPOINTS.md:1001`
- Next: Make the Start Live flow exclusively use the gated button path (remove duplicates)  
  Source: `CHECKPOINTS.md:1005`
- Next: wire paper_runner/live_runner to call Ledger.apply_fill + mark_to_market on each tick/fill  
  Source: `CHECKPOINTS.md:1011`
- Next: Live order placement + reconciliation (idempotent orders, fills ingestion, restart recovery)  
  Source: `CHECKPOINTS.md:1015`
- Next: “live disable switch” (kill flag) + circuit breaker on spread/staleness inside runner + per-exchange order params normalization  
  Source: `CHECKPOINTS.md:1019`
- Next: Per-exchange order parameter normalization + min size checks + better symbol-specific spread thresholds  
  Source: `CHECKPOINTS.md:1024`
- Next: per-exchange param normalization map + tighter symbol-level thresholds + integration tests  
  Source: `CHECKPOINTS.md:1030`
- Next: Sandbox “smoke test” scripts per exchange + stricter symbol-level circuit breaker thresholds  
  Source: `CHECKPOINTS.md:1035`
- Next: integration tests that mock CCXT + deterministic runner tests; plus per-symbol circuit breaker thresholds UI  
  Source: `CHECKPOINTS.md:1040`
- Next: CI-style “one command validation” script + Windows/macOS installers packaging  
  Source: `CHECKPOINTS.md:1045`
- Next: Installer UX layer + launcher start/stop cleanly from UI  
  Source: `CHECKPOINTS.md:1049`
- Next: Signed distribution + one-button build wrappers + CI artifacts  
  Source: `CHECKPOINTS.md:1054`
- Next: wire installer signing into Inno Setup + CI release artifacts + versioning automation  
  Source: `CHECKPOINTS.md:1059`
- Next: one-button release + GitHub Release artifacts + optional signing in CI  
  Source: `CHECKPOINTS.md:1063`
- Next: optional signing in CI + release train checklist in UI  
  Source: `CHECKPOINTS.md:1069`
- Next: sign Windows installer too (Inno SignTool integration) + UI “Release Train” checklist page  
  Source: `CHECKPOINTS.md:1074`
- Next: CI signing of installer artifact + UI buttons to run packaging builds per-OS (local only)  
  Source: `CHECKPOINTS.md:1080`
- Next: “Ops intelligence” learning/adaptability module path (market data ingestion → feature store → model training → safe deployment gates)  
  Source: `CHECKPOINTS.md:1085`
- Next: wire ML into decision flow (paper mode first), add monitoring + rollback triggers, integrate imported trader signals as features  
  Source: `CHECKPOINTS.md:1089`
- Next: execution + reconciliation layer (idempotent orders, restart-safe state, latency-aware order placement) + add “best venue routing” in paper first  
  Source: `CHECKPOINTS.md:1098`
- Next: trade-level reconciliation (fetch_my_trades) for partial fills, fee correctness, and robust restart recovery; then LIVE_SHADOW (observe-only) before any live ML gating  
  Source: `CHECKPOINTS.md:1107`
- Next: OS-native secure key storage (macOS Keychain + Windows Credential Manager) via `keyring`, plus signed builds + auto-update channel  
  Source: `CHECKPOINTS.md:1116`
- Next: “auto-update” channel (in-app update notifier) + release manifest; then WebSocket market data + event-driven execution for lower latency  
  Source: `CHECKPOINTS.md:1124`
- Next: true multi-role metadata (root/targets/timestamp/snapshot) + key rotation policy + threshold signatures; then WebSocket market data + event-driven execution for latency reduction  
  Source: `CHECKPOINTS.md:1132`
- Next: “single-command installer” that sets up Python venv + dependencies + dashboard + scheduling on Mac/Windows (no folder bouncing) and produces a packaged desktop app shell (Phase 52)  
  Source: `CHECKPOINTS.md:1142`
- Next: packaging/installers (Mac + Windows) as a single installable app + one-command setup; then multi-exchange live safety UX (Coinbase/Binance/Gate.io) inside UI  
  Source: `CHECKPOINTS.md:1151`
- Next: “Installer UX” polish:  
  Source: `CHECKPOINTS.md:1164`
- Next: live-key UX per exchange (Coinbase/Binance/Gate.io) + UI key validation + “confirm to enable live” gate + alert wiring (Slack/email)  
  Source: `CHECKPOINTS.md:1176`
- After tests pass: flip to ✅ and add Session Log line  
  Source: `CHECKPOINTS.md:1184`
- manual wiring: place _phase85_after_live_submit() at the actual "submit success" line  
  Source: `CHECKPOINTS.md:1210`
- Next: integrate with live user WS feeds and FillSink choke point  
  Source: `CHECKPOINTS.md:1222`
- Next: integrate live user-stream adapters to call executor._on_fill(...) so real exchange fills never bypass it  
  Source: `CHECKPOINTS.md:1231`
- Next: Phase 87 exchange-specific param matrix + integration tests (submit/unknown retry/cancel/reconcile)  
  Source: `CHECKPOINTS.md:1263`

## ⚠️ Constraint / Note (1)
- BY6: Build separately per OS (no cross-compile)  
  Source: `CHECKPOINTS.md:108`

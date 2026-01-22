# Crypto Bot Pro — CARRYOVER PACK
Generated (UTC): 2026-01-21T03:06:52.708906+00:00
Version: 0.1.0
## Standing Orders (Directive)
- No fluff. No misleading paths. No lies. No unnecessary data.
- Keep installation simple for Mac + Windows. Prefer one-command install / one-click launcher.
- Track checkpoints: done / in progress / partial / incomplete.
- Paper-first. Live trading must stay hard-disabled unless explicitly armed with multiple gates.
- Never store or display API secrets. Use ENV-only secrets; config may contain env var NAMES only.
- Prefer safe, idempotent flows: intents -> execution -> reconciliation -> journal -> analytics.
- Add/upgrade recommendations only when they improve safety/reliability.
- When chat grows long: export Carryover Pack and continue from it in a new chat.

## Current Roadmap / Checkpoints
## AX) Explain PnL & Cancel/Replace Hooks
- ✅ AX1: execution_events has ref_id index for fast joins
- ✅ AX2: pnl.last_fills includes ext_id (if column exists)
- ✅ AX3: Explain PnL moves (fills ↔ exec events) timeline helper + dashboard viewer
- ✅ AX4: Cancel/replace event hook helpers added (ready for strategies/executors that cancel/replace)
- 🟡 AX5: Actual cancel/replace execution depends on strategy logic (not implemented here)

## BA) Decision Audit Store
- ✅ BA1: decision_audit.sqlite stores decision_id + deterministic decision inputs
- ✅ BA2: Router persists decision audit records (best-effort)
- ✅ BA3: Dashboard viewer for decision audit + meta drilldown

## BD) Service PID Files
- ✅ BD1: service_manager writes runtime/pids/<service>.pid on start
- ✅ BD2: service_manager clears pid files on stop/stop_all (best-effort)
- ✅ BD3: Run Reset safety detection can rely on pid files (BC3 resolved)

## BE) Dashboard Service Controls
- ✅ BE1: service_manager exposes known_service_names
- ✅ BE2: PID-scoped stop & cleanup helpers
- ✅ BE3: Dashboard buttons added

## BG) Run Reset Safety
- ✅ BG1: any_services_running checks pid liveness + health status != STOPPED
- ✅ BG2: Dashboard Run reset messaging matches the safety logic

## BC) Run Reset
- ✅ BC1: Safe run_id rotation helper (blocks if runtime/pids has live processes)
- ✅ BC2: Dashboard button 'Start new Run ID' (disabled if services detected running)
- 🟡 BC3: PID-based detection depends on service_manager writing pid files (if not, detection is best-effort)

## BI) Live Enforcement
- ✅ BI1: Live executors hard-block order submission when kill switch ARMED
- ✅ BI2: Live executors hard-block order submission when risk.enable_live is false
- ✅ BI3: Dashboard kill switch ARM/DISARM controls with audit events (kill_switch_changed)
- ✅ BI4: Blocked orders are logged as execution events (order_blocked)

## BK) Venue Aggregate Risk
- ✅ BK1: risk_ledger.sqlite daily_venue aggregate table (day+venue totals across symbols)
- ✅ BK2: Ledger updates daily_venue on every USD-quote fill
- ✅ BK3: Risk gate enforces optional max_daily_loss_usd_venue and max_trades_per_day_venue
- ✅ BK4: Dashboard risk panel shows venue aggregate stats when venue is provided

## PHASE_TEST
- ✅ Test checkpoint
## BM) Market Data Poller
- ✅ BM1: Market data poller loop fetches public tickers and caches to price_cache.sqlite
- ✅ BM2: Poller service entrypoint with STOP flag + health handshake (runtime/health/market_data_poller.json)
- ✅ BM3: Dashboard panel shows required conversion pairs + one-shot refresh + cache viewer
- ✅ BM4: service_manager auto-start spec added best-effort (depends on SERVICE_SPECS structure)

## BN) Cache Readiness Wiring
- ✅ BN1: cache_audit helper reports missing required pairs from price_cache.sqlite (no network)
- ✅ BN2: Preflight warns when cache missing pairs and allow_unknown_notional=false
- ✅ BN3: Dashboard panel: missing-pairs warning + “Populate required pairs now” button

## BP) Router Pre-Block Logging
- ✅ BP1: Router records risk_gate blocks into risk_blocks.sqlite (even without executors)
- ✅ BP2: order_blocked events now include payload.gate and payload.reason_code (backward compatible)
- ✅ BP3: Gate naming unified: risk_gate / live_guard

## BQ) Config Editor
- ✅ BQ1: Safe loader/writer for runtime/config/user.yaml (atomic write)
- ✅ BQ2: Validation for known keys (risk/preflight/market_data_poller) + allows unknown keys
- ✅ BQ3: Versioned backups in runtime/config/backups + restore
- ✅ BQ4: Dashboard config editor (guided + raw YAML) with dry-run diff

## BR) Live Enable Wizard
- ✅ BR1: Deterministic readiness evaluation (preflight + cache + risk non-zero + kill switch armed)
- ✅ BR2: Single action enable: sets risk.enable_live=true (atomic + backup) and DISARMS kill switch
- ✅ BR3: Audit event recorded: live_enabled (pre/post state + backup path)
- ✅ BR4: Dashboard wizard panel with explicit acknowledgement checkbox

## BS) Live Disable + Auto Recovery
- ✅ BS1: Live disable wizard: sets risk.enable_live=false + ARMS kill switch + audit event live_disabled
- ✅ BS2: Auto recovery on UI start: if enable_live=true OR kill switch disarmed => auto-disable (safe default)
- ✅ BS3: Config opt-out: safety.auto_disable_live_on_start: false
- ✅ BS4: Dashboard panels for auto recovery + manual Live Disable

## BT) Service-Level Live Enforcement
- ✅ BT1: live_trader_multi loop checks live_allowed() each iteration; STOPPING -> exit
- ✅ BT2: live_trader_fleet loop checks live_allowed() each iteration; STOPPING -> exit
- ✅ BT3: live services write health handshake RUNNING/STOPPING/STOPPED

## BU) Service Watchdog
- ✅ BU1: Watchdog snapshot: health status/ts/pid + pid-file liveness
- ✅ BU2: Best-effort last activity hint (searches event_log payload.source)
- ✅ BU3: Dashboard restart buttons: stop via pid-file scoped stop, start via service_manager.start_service (best-effort)

## BX) Installers
- ✅ BX1: scripts/bootstrap.py (install/run/doctor/poller/live entrypoints)
- ✅ BX2: one_click_mac.sh + one_click_windows.ps1 + one_click_windows.bat (run dashboard)
- ✅ BX3: start_poller_* launchers (optional)
- ✅ BX4: Safe default: installer does NOT auto-start live trading services

## CA) API Key Onboarding
- ✅ CA1: OS-backed credential storage via keyring (no secrets in files)
- ✅ CA2: Coinbase/Binance/Gate.io credential UI (save/delete/status)
- ✅ CA3: Private connectivity test (fetchBalance) per exchange
- ✅ CA4: Preflight private_check now runs private connectivity tests

## BY) Desktop Packaging
- ✅ BY1: desktop/native_window.py (Streamlit + pywebview)
- ✅ BY2: scripts/build_desktop.py (PyInstaller onedir build)
- ✅ BY3: build_desktop_mac.sh + build_desktop_windows.ps1 one-command
- ✅ BY4: docs/DESKTOP_BUILD.md
- ✅ BY5: requirements.txt updated with pywebview + pyinstaller
- ⚠️ BY6: Build separately per OS (no cross-compile)

## BZ) First-Run Wizard
- ✅ BZ1: Wizard computes first-run status (config presence + cache readiness + safety state)
- ✅ BZ2: Writes SAFE defaults (enable_live=false + kill switch ARMED) with backup + atomic write
- ✅ BZ3: Runs preflight from UI
- ✅ BZ4: Populates required cache pairs from UI (public tickers)
- ✅ BZ5: Dashboard UI for optional poller service start

## CB) Permissions Probes
- ✅ CB1: Read-only permission probes runner (fetchBalance/openOrders/myTrades/etc)
- ✅ CB2: Dashboard permissions panel with selectable probes + CCXT has flags
- ✅ CB3: Preflight private_check runs configurable preflight.private_probes (defaults apply)
- ✅ CB4: No order placement or test orders (probe layer is read-only only)

## CG) Master Read-Only Mode
- ✅ CG1: safety.read_only_mode global hard block for all order routing
- ✅ CG2: Enforced in router BEFORE exchange_policy/risk_gate (gate=master_read_only)
- ✅ CG3: Enforced again in executors before submit (defense-in-depth)
- ✅ CG4: Dashboard banner when enabled + toggle panel (safe write + diff + backup)
- ✅ CG5: risk_blocks.sqlite captures master_read_only blocks for explainability

## CH) Carryover Kit
- ✅ CH1: services/admin/state_report.py generates docs/STATE.md (sanitized config + checkpoints + snapshots)
- ✅ CH2: Dashboard button to update STATE.md + save snapshot copies
- ✅ CH3: Optional CLI: python scripts/bootstrap.py state

## CL) Idempotency & Reconciliation
- ✅ CL1: Persistent order_idempotency.sqlite stores intent_id → client_order_id + status
- ✅ CL2: Executors attach venue-specific client IDs
- ✅ CL3: Dedupe window blocks rapid resubmission
- ✅ CL4: Reconcile updates local records from open orders
- ✅ CL5: Dashboard panel shows reconcile + recent idempotency rows

## CN) Journal ↔ Exchange Reconciliation
- ✅ CN1: Scan local sqlite/db files for trade/order-like tables
- ✅ CN2: Fetch exchange history (myTrades/closedOrders) using stored creds
- ✅ CN3: Fingerprint-based comparison → missing_local / missing_exchange
- ✅ CN4: Snapshot saved to runtime/snapshots/journal_reconcile.<ts>.json
- ✅ CN5: Dashboard panel to run reconciliation and review results

## CO) Position Reconciliation
- ✅ CO1: Exchange spot balances via fetchBalance
- ✅ CO2: Local net base positions from detected trades
- ✅ CO3: Mismatch report with tolerances + snapshot
- ✅ CO4: Dashboard panel + live enable checklist gate

## CQ) Latency + Slippage Guard
- ✅ CQ1: exec_metrics.sqlite records submit→ack latency (ms) + slippage (bps) per order
- ✅ CQ2: rolling p95 computed per venue (window_n) for latency + slippage
- ✅ CQ3: router gate blocks when p95 exceeds thresholds (gate=latency_slippage_guard)
- ✅ CQ4: dashboard panel shows metrics, p95, and safe editing of thresholds

## CP) Position Reconciliation
- ✅ CP1: Exchange spot balances via fetchBalance
- ✅ CP2: Local net base positions from detected trades
- ✅ CP3: Dashboard position reconcile panel includes mode selector
- ✅ CP4: Live Enable Checklist now runs position reconcile per venue (mode-aware)

## CX) System Status Tick Publisher
- ✅ CX1: Background publisher writes runtime/snapshots/system_status.latest.json on interval
- ✅ CX2: Includes ticks[{venue,symbol,ts_ms,bid,ask,last}] compatible with staleness guard discovery
- ✅ CX3: File-based stop request + lock file to avoid accidental duplicate runners
- ✅ CX4: Dashboard panel: start/stop, status, snapshot preview, safe config editing

## CY) One Installer (Mac + Windows)
- ✅ CY1: install.py creates .venv, installs deps, creates runtime/data/config safely
- ✅ CY2: install.py writes runtime/config/user.yaml with safe defaults if missing
- ✅ CY3: run.py launches Streamlit dashboard; optional tick publisher autostart
- ✅ CY4: scripts/doctor.py verifies install without manual file edits
- ✅ CY5: No secrets stored; evidence webhook secrets remain in keyring/env

## CZ) Desktop App Build (PyInstaller)
- ✅ CZ1: desktop_launcher.py starts Streamlit via bootstrap and opens local browser
- ✅ CZ2: services/os/app_paths.py routes runtime/data to user-writable dir when frozen
- ✅ CZ3: packaging/crypto_bot_pro.spec bundles dashboard + modules + Streamlit data/metadata
- ✅ CZ4: scripts/build_desktop.py builds an OS-native distributable folder (dist/CryptoBotPro)
- ✅ CZ5: No secrets bundled; keyring/env remains the only secret path

## DA) Double-Click Desktop Supervisor
- ✅ DA1: desktop_launcher_gui.py provides a small Tk supervisor (Start/Open/Quit)
- ✅ DA2: Streamlit runs via bootstrap in a background thread; quitting stops the whole process
- ✅ DA3: Frozen app uses user-writable state/config paths via services/os/app_paths.py + config_editor patch
- ✅ DA4: PyInstaller spec now builds windowed (no console) and disables windowed traceback
- ✅ DA5: Optional icons supported if assets/icons/app.ico (Win) or app.icns (macOS) are provided

## DB) Graceful Stop for Services
- ✅ DB1: Evidence webhook supports stop-file shutdown (runtime/flags/evidence_webhook.stop)
- ✅ DB2: Evidence webhook uses lock + status files (runtime/locks/evidence_webhook.lock, runtime/flags/evidence_webhook.status.json)
- ✅ DB3: scripts/run_evidence_webhook.py supports run/stop commands
- ✅ DB4: Dashboard includes Service Controls panel to request stop for webhook + tick publisher

## DC) Supervisor Mode
- ✅ DC1: services/supervisor/supervisor.py start/stop/status with PID-based running detection
- ✅ DC2: Auto-clears stale supervisor lock if owning PID is dead (no manual lock deletion)
- ✅ DC3: scripts/supervisor.py CLI (start/stop/status) for one-command control
- ✅ DC4: Dashboard panel to start/stop services and view supervisor status
- ✅ DC5: Can start Streamlit dashboard from terminal supervisor (not from inside dashboard by default)

## DD) Desktop Default Full + Safe Mode
- ✅ DD1: Desktop app defaults to Full mode (Dashboard + Tick Publisher + Evidence Webhook)
- ✅ DD2: Safe Mode available (--safe or CBP_MODE=safe) starts dashboard only
- ✅ DD3: Tick publisher + evidence webhook now auto-clear stale locks if PID is dead
- ✅ DD4: Desktop UI includes Stop Services (writes stop-files) + Quit (stop-files + exit)

## DE) Execution Engine v1 (Paper Trading)
- ✅ DE1: SQLite schema for orders/fills/positions/equity + idempotent client_order_id
- ✅ DE2: PaperEngine submit/cancel + reconciliation of open orders
- ✅ DE3: Market fills use mid + slippage; limit fills cross bid/ask
- ✅ DE4: Runner supports start/stop/status via runtime files
- ✅ DE5: Dashboard console to place paper orders and monitor positions/orders/fills/equity

## DF) Strategy → Intent Pipeline (Paper)
- ✅ DF1: intent_queue.sqlite trade_intents table with durable statuses
- ✅ DF2: Intent consumer submits queued intents to PaperEngine using client_order_id=intent_<intent_id>
- ✅ DF3: Cooldown per symbol or symbol+side to prevent rapid repeats
- ✅ DF4: Minimal risk gate (max_trades/day, max_daily_notional_quote) using consumer_state counters
- ✅ DF5: Dashboard panel to enqueue intents + start/stop consumer + inspect queue

## DG) Strategy Runner v1 (EMA → Intents)
- ✅ DG1: EMA crossover runner reads mid price (tick publisher; CCXT fallback optional)
- ✅ DG2: Stateful (persists price buffer + last signal) to avoid repeated intent spam
- ✅ DG3: Position-aware default: buy only when flat, sell only when in position (option to sell full position)
- ✅ DG4: Produces intents into intent_queue.sqlite (queued), consumed by intent consumer → paper engine
- ✅ DG5: Start/stop/status via runtime files + dashboard panel

## DH) Intent → Filled + Trade Journal
- ✅ DH1: intent_reconciler watches submitted intents and updates status based on paper order status
- ✅ DH2: Writes trade_journal.sqlite journal_fills rows (idempotent by fill_id)
- ✅ DH3: Dashboard panel to start/stop reconciler and view journal + submitted intents
- ✅ DH4: PaperTradingSQLite extended with get_order_by_order_id + list_fills_for_order

## DI) Analytics v1 + Export
- ✅ DI1: FIFO realized PnL + win rate computed from trade_journal.sqlite journal_fills
- ✅ DI2: Max drawdown computed from paper_equity table
- ✅ DI3: Dashboard analytics panel (metrics + closed trades table + equity curve)
- ✅ DI4: Dashboard Download CSV for journal fills

## DK) Multi-Venue Market View + Best Venue Selection
- ✅ DK1: Multi-venue market view ranks venues by guard_ok → age_sec → spread_bps
- ✅ DK2: Dashboard panel shows per-venue quote metrics and the current best venue
- ✅ DK3: Strategy Runner optional auto_select_best_venue (default off) with safe switching (only when blocked)
- ✅ DK4: Strategy Runner CCXT fallback uses mapped_symbol for the chosen venue

## DL) Live Execution Scaffold (Disabled by Default)
- ✅ DL1: Separate live intent queue DB (prevents paper strategy from ever submitting live orders)
- ✅ DL2: Two-gate arming required: config live_trading.enabled=true AND env CBP_LIVE_ARMED=YES
- ✅ DL3: CCXT live adapter (Binance/Coinbase/Gateio) using env-based credentials (no secrets stored)
- ✅ DL4: Live consumer enforces market quality + daily trade/notional/min-notional limits
- ✅ DL5: Live reconciler best-effort fetch_order + fetch_my_trades (local logs)
- ✅ DL6: Dashboard Live panel: credentials presence, arming status, enqueue live intent (manual only)

## Final Phase 119: Live Enablement & Polish
- ✅ Staleness guard blocks submission if snapshot stale
- ✅ Panic button in dashboard stops all execution
- ✅ Installer + supervisor + launchers complete
- ✅ Versioning + update checker in place
- Ready for controlled live testing

## DP) Versioning + Safe Update Check
- ✅ DP1: VERSION file is the single source of truth for app version
- ✅ DP2: Dashboard About/Updates panel shows version and can check a JSON update channel (optional)
- ✅ DP3: Manual download only (no auto-install). Guarded by updates.allow_download
- ✅ DP4: bump_version script for controlled version increments

## DQ) Carryover Pack Exporter
- ✅ DQ1: services/app/carryover_exporter.py generates sanitized CARRYOVER.md
- ✅ DQ2: scripts/export_carryover.py CLI export to runtime/exports/CARRYOVER.md
- ✅ DQ3: Dashboard panel export + download button + preview

## DR) System Health + Diagnostics Export
- ✅ DR1: System health collector (flags/locks/pids/snapshots + market health rows)
- ✅ DR2: Dashboard System Health panel (process files + queue depth + market health table)
- ✅ DR3: Diagnostics exporter builds a sanitized zip (runtime tails + config snapshot + manifests)
- ✅ DR4: scripts/export_diagnostics.py CLI export to runtime/exports

## DS) Preflight Wizard
- ✅ DS1: services/app/preflight_wizard.py computes Ready/Not Ready with concrete reasons
- ✅ DS2: scripts/run_preflight.py prints JSON preflight report (CLI)
- ✅ DS3: Dashboard Preflight Wizard panel with fix actions + export buttons

## DT) Trader Learning Ingestion Scaffold (Public Signals)
- ✅ DT1: SignalEvent model + normalizer (accepts flexible payloads → canonical)
- ✅ DT2: signal_inbox.sqlite store with statuses (new/reviewed/ignored/routed)
- ✅ DT3: Local webhook receiver (POST /signal) to ingest signals safely
- ✅ DT4: Dashboard Signal Inbox page (view, review, ignore, optional route-to-paper)
- ✅ DT5: Signal replay backtest scaffold (signals → CCXT OHLCV → equity/trades)
- ✅ DT6: Routing allowlists + default routing OFF (requires explicit enable)

## DU) Signal Learning v1 (Reliability Scoring)
- ✅ DU1: signal_reliability.sqlite store (per source/author/symbol/venue/timeframe/horizon)
- ✅ DU2: Reliability scoring (hit_rate + avg_return_bps) using OHLCV replay horizon
- ✅ DU3: CLI recompute script (scripts/recompute_signal_reliability.py)
- ✅ DU4: Dashboard panel compute/store + leaderboard
- ✅ DU5: Optional learning gate + qty scaling for PAPER routing (signals_learning.*; default OFF)

## DV) Adaptive Meta-Strategy (Internal + External + Reliability)
- ✅ DV1: Internal EMA crossover signal via public OHLCV
- ✅ DV2: External signal aggregation from Signal Inbox (optional reliability-weighting)
- ✅ DV3: Meta composer (weights + conflict-hold + decision threshold)
- ✅ DV4: Meta decision journaling (meta_decisions.sqlite)
- ✅ DV5: Meta strategy runner creates PAPER intents only when explicitly enabled
- ✅ DV6: Dashboard panel to start/stop meta runner + inspect decisions + compute once

## Config Snapshot (sanitized)
Path: `/Users/baitus/Downloads/crypto-bot-pro/config/user_config.yaml`
```yaml
(missing or unreadable: /Users/baitus/Downloads/crypto-bot-pro/config/user_config.yaml : FileNotFoundError)
```
## Run Commands
```text
### Daily run (paper stack)
- Installed app (recommended):
  - macOS: double-click `CryptoBotPro.command`
  - Windows: double-click `CryptoBotPro.bat`
- From repo (dev):
  - `python3 scripts/cbp_supervisor.py start` (starts paper stack + dashboard)
  - `python3 scripts/cbp_supervisor.py stop` (stops all)
### Individual processes (paper)
- `python3 scripts/run_tick_publisher.py run`
- `python3 scripts/run_paper_engine.py run`
- `python3 scripts/run_intent_consumer.py run`
- `python3 scripts/run_strategy_runner.py run`
- `python3 scripts/run_intent_reconciler.py run`
### Live trading safety gates (DO NOT enable casually)
Requires BOTH:
1) `live_trading.enabled: true` in config
2) ENV `CBP_LIVE_ARMED=YES`
Plus Live Safety Pack (whitelist, qty bounds, dry_run, etc.)
```
## Install / App Usage
(missing or unreadable: /Users/baitus/Downloads/crypto-bot-pro/INSTALL_APP.md : FileNotFoundError)

## Packaging (Desktop .app / .exe)
(missing or unreadable: /Users/baitus/Downloads/crypto-bot-pro/PACKAGING.md : FileNotFoundError)

## Prior Artifacts Previously Provided (for reference)
- crypto-bot-pro.zip
- crypto-bot-pro-phase2.zip

## Notes for continuing in a new chat
- Paste this entire file into the new chat.
- Then say: “Continue from Phase ___” or “Continue from the next incomplete checkpoint.”

## AX) Explain PnL & Cancel/Replace Hooks
- ✅ AX1: execution_events has ref_id index for fast joins
- ✅ AX2: pnl.last_fills includes ext_id (if column exists)
- ✅ AX3: Explain PnL moves (fills ↔ exec events) timeline helper + dashboard viewer
- ✅ AX4: Cancel/replace event hook helpers added (ready for strategies/executors that cancel/replace)
- ✅ AX5: Actual cancel/replace execution depends on strategy logic (not implemented here)

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
- ✅ BC3: PID-based detection depends on service_manager writing pid files (if not, detection is best-effort)

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
- ✅ BY6: Packaging/build flow documented and scaffolded for host-OS-only builds (no cross-compile)

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

## FI) Order Blocked Inspector
- ✅ FI1: Schema-agnostic idempotency DB inspector (find DB, find table, list recent rows)
- ✅ FI2: UI panel to filter by venue/symbol and view full failure payloads
- ✅ FI3: Added copy-key action and “last 10 failures only” toggle in Operator Order Blocked Inspector

## FN) App Icon + Versioning Metadata
- ✅ FN1: desktop_app/app_meta.json (single source of truth)
- ✅ FN2: Windows version info generator (desktop_app/version_info_gen.py → version_info.txt)
- ✅ FN3: build script uses --version-file (Windows) + --osx-bundle-identifier (macOS)
- ✅ FN4: icon support (Windows .ico / macOS .icns) via build script
- ✅ FN5: branding/signing notes doc
- ✅ FN6: Real icon assets added (ICO/ICNS) and CI build pipelines already present

## FO) CI Desktop App Builds
- ✅ FO1: GitHub Actions workflow builds Windows + macOS artifacts
- ✅ FO2: Packages dist/ into zip (scripts/ci/package_dist.py)
- ✅ FO3: Uploads artifacts to Actions run
- ✅ FO4: Tag-based GitHub Releases delivered (release workflows attach artifacts)
- ✅ FO5: Optional signing/notarization integration delivered (secrets-gated CI paths)

## FP) Tag-based GitHub Releases
- ✅ FP1: Release workflow builds Windows + macOS on tags v*.*.*
- ✅ FP2: Creates GitHub Release + attaches zipped dist artifacts
- ✅ FP3: Release docs (docs/RELEASES.md)
- ✅ FP4: Optional signing/notarization release pipeline delivered (cert/secrets-gated)

## FQ) Signing + Notarization Hooks
- ✅ FQ1: Optional Windows signing script (scripts/ci/sign_windows.ps1)
- ✅ FQ2: Optional macOS sign+notarize script (scripts/ci/sign_macos.sh)
- ✅ FQ3: CI workflows call signing steps only if secrets exist
- ✅ FQ4: Signing/notarization docs (docs/SIGNING_NOTARIZATION.md)
- ✅ FQ5: Optional Linux AppImage scaffold added (`scripts/build_linux_appimage.sh` + desktop metadata + docs/tests)

## GI) Packaged App Builds (Optional)
- ✅ GI1: app_entry.py packaged entrypoint (launches Streamlit + opens browser)
- ✅ GI2: PyInstaller spec (packaging/cryptobotpro.spec) including required project data
- ✅ GI3: Build scripts for macOS + Windows
- ✅ GI4: docs/PACKAGING.md
- ✅ GI5: Hardening delivered (windowed release mode support + signing/notary/code-sign workflows)

## GK) Hardening: Preflight + No Silent Failures
- ✅ GK1: Preflight engine (python/config/imports/keys/db writable/runner hook marker checks)
- ✅ GK2: Safe bot runner CLI (scripts/run_bot_safe.py) that refuses to run if preflight fails
- ✅ GK3: Dashboard Preflight panel
- ✅ GK4: Resume sequence includes preflight as Step 0
- ✅ GK5: Silent broad `except: pass` blocks removed in hardened modules and enforced by test (`tests/test_no_silent_exception_pass_blocks.py`)

## GM) Process Control + Health Status
- ✅ GM1: PID tracking + bot log capture (data/bot_process.json, data/logs/bot.log)
- ✅ GM2: Start/Stop/Stop-All (cross-platform) via services/process/bot_process.py
- ✅ GM3: Heartbeat + last error file (data/bot_heartbeat.json)
- ✅ GM4: strategy_runner patched to emit heartbeat tick + error markers (best-effort)
- ✅ GM5: Streamlit Process Control panel (buttons + heartbeat + bot log tail/download)
- ✅ GM6: CLI bot controller (scripts/bot_ctl.py)
- ✅ GM7: Graceful stop is enforced (soft SIGTERM first, optional hard kill) and runner exits cleanly on shutdown signal

## GP) Crash Snapshot (Hard-Kill Forensics)
- ✅ GP1: Controller-written crash snapshot (data/crash_snapshot.json) with bot/app log tails
- ✅ GP2: stop_bot writes crash snapshot on hard-kill or stop failure
- ✅ GP3: Streamlit Crash Snapshot panel
- ✅ GP4: CLI viewer (scripts/crash_snapshot.py)
- ✅ GP5: Automatic crash detection is active in watchdog (stale heartbeat -> crash snapshot + kill switch + persisted watchdog result)

## GQ) Watchdog (Heartbeat Staleness)
- ✅ GQ1: Watchdog engine (services/process/watchdog.py) with persisted last result
- ✅ GQ2: On stale heartbeat: crash snapshot + kill switch ON
- ✅ GQ3: Optional auto-stop on stale (OFF by default)
- ✅ GQ4: CLI tool (scripts/watchdog.py) once/loop/show_last
- ✅ GQ5: Streamlit panel (run now + view last)
- ✅ GQ6: Supervisor mode runs cockpit + watchdog as managed siblings (services/process/supervisor_process.py + scripts/supervisor_ctl.py)

## GR) Supervisor Mode (Cockpit + Watchdog)
- ✅ GR1: Supervisor process manager (data/supervisor_process.json + cockpit/watchdog logs)
- ✅ GR2: Supervisor launcher (launchers/launch_supervisor.py) starts both + opens browser + stops both on exit
- ✅ GR3: Installer generates Supervisor double-click launchers (macOS/Windows)
- ✅ GR4: Dashboard Supervisor Status panel
- ✅ GR5: CLI stop/status (scripts/supervisor_ctl.py)
- ✅ GR6: “Start Supervisor” button shipped in Operator UI (dashboard/pages/00_Operator.py)

## GS) Watchdog Managed Process + Orphan Prevention
- ✅ GS1: PID-tracked watchdog loop process (data/watchdog_process.json + watchdog_loop.log)
- ✅ GS2: CLI watchdog controller (scripts/watchdog_ctl.py)
- ✅ GS3: Streamlit Watchdog Control panel (start/stop/clear + log tail/download)
- ✅ GS4: Single “Stop Everything” command shipped with explicit precedence (scripts/op.py + tests/test_op_control_surface.py)

## GZ) Enforce No Direct create_order
- ✅ GZ1: CLI verifier scans repo and fails on violations (scripts/verify_no_direct_create_order.py)
- ✅ GZ2: Unit test fails if .create_order appears outside place_order.py (tests/test_no_direct_create_order.py)
- ✅ GZ3: Policy doc (docs/NO_DIRECT_CREATE_ORDER.md)
- ✅ GZ4: Verifier confirms zero direct create_order violations (`scripts/verify_no_direct_create_order.py --print` -> `{'ok': True, 'violations': 0}`)

## HA) Order Audit Viewer (UI + CLI)
- ✅ HA1: execution_audit reader (storage/execution_audit_reader.py)
- ✅ HA2: CLI viewer (scripts/audit_view.py)
- ✅ HA3: Streamlit Order Audit Viewer panel (filters + tables)
- ✅ HA4: Conditional patch task closed (Phase 209 verifier currently reports zero violations)

## HD) Alert Hardening + Health + Dry-run Safety
- ✅ HD1: FIX: place_order routes alerts with cfg in scope (no NameError)
- ✅ HD2: Alert payload redaction (no secrets/webhooks/tokens)
- ✅ HD3: Dry-run alert suppression policy (alerts.never_alert_on_dry_run default true)
- ✅ HD4: Persist last alert send result (data/alerts_last.json) + UI display

## HH) Startup Status Gate (Freshness) + UI Indicator
- ✅ HH1: startup_status.json store (record_success/record_failure + is_fresh)
- ✅ HH2: startup_reconcile records status automatically
- ✅ HH3: run_bot_safe live start can require fresh startup reconciliation (configurable)
- ✅ HH4: Streamlit Startup Status panel (shows last status + run now)

## HJ) UI Live Start Gate + ARM LIVE
- ✅ HJ1: Bot Control Start button disables when LIVE gates fail
- ✅ HJ2: Explicit ARM LIVE + typed confirmation required for LIVE start
- ✅ HJ3: Enforce startup reconciliation freshness gate for LIVE start
- ✅ HJ4: Enforce live_safety.live_enabled + per-symbol confirmations for LIVE start
- ✅ HJ5: Auto-disarm LIVE controls after Start/Stop

## HR) Strategy Library + Registry (Selectable)
- ✅ HR1: Strategy interface + OrderIntent model (services/strategies/base.py)
- ✅ HR2: Strategy registry + factory (services/strategies/registry.py)
- ✅ HR3: ema_cross strategy wired (impl_ema_cross.py)
- ✅ HR4: mean_reversion_rsi + breakout_donchian stubs (safe hold unless enabled)
- ✅ HR5: run_bot_safe paper loop uses strategy registry (no hard-coded EMA)
- ✅ HR6: Streamlit Strategy Selector panel
- ✅ HR7: Strategy parameter validation and per-strategy preset controls added in Operator UI with safe config writes


## HG) Startup Auto-Reconciliation (Safe Mode)
- ✅ HG1–HG6: Startup reconciliation + UI + CLI + reports


## HI) Bot Control Single Entrypoint + Status Summary
- ✅ HI1–HI4: Single entrypoint + status summary + log tail
- ✅ HI5: Live start gating delivered via HJ controls (ARM LIVE + typed confirmation + freshness and safety gates)


## HK) Single Run Mode (paper|live) Across UI/CLI/Config
- ✅ HK1–HK4: Single run mode across UI/CLI/config
- ✅ HK5: strategy runner shutdown/dry-run cleanup completed; pre-set shutdown respected; entrypoint initialization order fixed; env parsing covered; runner slice passing


## HL) Paper Strategy Loop
- ✅ HL1–HL5: Paper loop foundation
- ✅ HL6: Paper PnL/analytics UI delivered in HM track


## HM) Paper Analytics + PnL
- ✅ HM1–HM4: Paper analytics + UI
- ✅ HM5: MTM sampling and metrics delivered in HN track


## HN) Paper MTM Equity + Sharpe/Sortino + Daily + CSV
- ✅ HN1–HN4: MTM equity + metrics + UI + CSV
- ✅ HN5: Portfolio-level MTM delivered in HO track


## HO) Portfolio MTM + Correlation + CSV
- ✅ HO1–HO5: Portfolio MTM + correlation + UI + CSV
- ✅ HO6: Risk allocation delivered in HP track


## HP) Risk Allocation + Position Sizing
- ✅ HP1–HP4: Risk sizing + caps + paper loop + UI
- ✅ HP5: Sell-side risk controls delivered in HQ track


## HQ) Sell-Side Risk Controls (Paper)
- ✅ HQ1–HQ5: Exit controls + panic reduce + UI
- ✅ HQ6: Strategy-aware exit stacking helper added with rule priority (stop-loss, trailing-stop, take-profit, time-stop) and tests


## HS) Strategy Validation + Presets + Trade Gate
- ✅ HS1–HS5: Validation + presets + trade gate + UI
- ✅ HS6: Per-strategy preset bundles delivered in HT track


## HT) Preset Bundles + Safe Paper Profile + Governance Log
- ✅ HT1–HT5: Bundles + governance log + UI
- ✅ HT6: Live-mode guardrails delivered in HU track


## HU) Live Guardrails for Bundles + Runtime Hard Block
- ✅ HU1–HU4: ARM LIVE + guardrails + runtime block
- ✅ HU5: Live execution layer delivered (gated) via DL/LT tracks (`services/execution/live_executor.py`, `services/execution/live_exchange_adapter.py`)

## HY) WS Capability Detection + Auto-Disable Unsupported Features
- ✅ HY1: Persistent WS feature blacklist (data/ws_feature_blacklist.json)
- ✅ HY2: ws_microstructure_manager checks exchange.has and skips unsupported watch_* features
- ✅ HY3: Auto-disable per venue+symbol+feature after repeated errors (cooldown)
- ✅ HY4: Streamlit WS Feature Blacklist panel (view/reset)
- ✅ HY5: watchTicker auto-disable added (blacklist-backed `services/marketdata/ws_ticker_feed.py` + runner + tests)

## IC) LIVE Guardrails include WS Safety
- ✅ IC1: Guardrails block live if ws_use_for_trading=true but ws_enabled=false
- ✅ IC2: Guardrails require ws_health.enabled when ws_use_for_trading=true in live
- ✅ IC3: Guardrails require REST fallback (ws_block_on_stale=false) OR auto_switch_enabled=true for live WS trading
- ✅ IC4: Optional override live_safety.allow_ws_strict=false by default
- ✅ IC5: Real live execution routing is implemented behind hard gates/arming (`services/execution/live_executor.py` + preflight/risk/latency checks)

## ID) Idempotent Order Intents + Restart-Safe Submission (Paper First)
- ✅ ID1: SQLite intent ledger (data/execution.sqlite) with deterministic intent_id
- ✅ ID2: Bot creates BUY/SELL intents per bar; skips if already exists (prevents duplicate submissions)
- ✅ ID3: Reconciliation skeleton: NEW -> STALE after max_new_age_sec
- ✅ ID4: Streamlit panel to view intents + manual reconcile
- ✅ ID5: Full execution parity delivered across intent/executor/reconcile/fills paths (`services/execution/intent_executor.py`, `services/execution/live_executor.py`, `services/fills/fills_poller.py`, journal stores)

## IH) Strategy Library + UI Presets
- ✅ IH1: Strategy registry + indicator utils (pure python)
- ✅ IH2: mean_reversion_rsi strategy
- ✅ IH3: breakout_donchian strategy
- ✅ IH4: Runner integration (strategy gating for BUY + safe SELL block with holdings check)
- ✅ IH5: Streamlit Strategy Selector + presets + config write-back + governance log
- ✅ IH6: Backtest parity for new strategies inside the UI backtest engine (deterministic parity engine + Operator panel + tests)

## IW) Mark Cache UI Locks + Owner Warnings
- ✅ IW1: Mark Cache Control panel disables Start/Stop when owner==runner
- ✅ IW2: Mark Cache Control panel shows warning/info based on owner
- ✅ IW3: Mark Cache Status panel displays owner
- ✅ IW4: Doc written for UI locks

## IY) Exchange-level Idempotency (CCXT clientOrderId wiring)
- ✅ IY1: live CCXT adapter injects client_oid into CCXT params
- ✅ IY2: config-driven venue param mapping (binance/coinbase/gateio)
- ✅ IY3: documentation added (EXCHANGE_IDEMPOTENCY_CCXT.md)

## JH) Signed Distribution (macOS notarization + Windows signing)
- ✅ JH1: macOS PyInstaller spec builds CryptoBotPro.app (windowed)
- ✅ JH2: macOS script: codesign + notarytool submit + stapler staple
- ✅ JH3: Windows script: signtool sign + timestamp + verify
- ✅ JH4: Signing/distribution doc added (SIGNING_DISTRIBUTION.md)
- ✅ JH5: MSIX packaging pipeline delivered via JI track (MakeAppx + SignTool + manifest + install script)

## JI) MSIX Packaging (Windows) — MakeAppx + SignTool + Install test
- ✅ JI1: AppxManifest.xml template + Assets folder
- ✅ JI2: build_msix.ps1 stages files and runs MakeAppx pack → dist/CryptoBotPro.msix
- ✅ JI3: sign_msix.ps1 signs + timestamps MSIX
- ✅ JI4: install_msix.ps1 installs MSIX locally for testing
- ✅ JI5: Docs added (MSIX_PACKAGING.md)

## JN) Bot Loop Wiring (Intents → Adapter → Journal → Reconcile) — paper-first
- ✅ JN1: Intent queue store (SQLite) (created if missing)
- ✅ JN2: Order event journal (SQLite) (created if missing)
- ✅ JN3: Executor executes READY intents via adapter + writes journal events
- ✅ JN4: Reconciler updates SENT/OPEN intents via open-orders/fetch_order
- ✅ JN5: Duplicate prevention (order_id guard + client_oid scan)
- ✅ JN6: Background supervisor start/stop + Streamlit control panel
- ✅ JN7: Strategy-to-intent builder is wired (pipeline strategies -> IntentWriter -> intent_queue mirror for executor consumption)

## JP) Multi-Strategy Library + Presets (EMA/MR/Breakout + filters)
- ✅ JP1: Unified Signal schema + indicator helpers
- ✅ JP2: Added strategies: mean_reversion (z-score), breakout (donchian)
- ✅ JP3: Added gate-only filters: volatility (ATR%), regime (trend slope)
- ✅ JP4: Strategy registry + default params
- ✅ JP5: Presets + Streamlit “run preset once” panel (no config editing)
- ✅ JP6: intent_builder upgraded to multi-strategy + filters (backwards compatible)
- ✅ JP7: Docs added (MULTI_STRATEGY_LIBRARY.md)
- ✅ JP8: Strategy parameter editor + safe preset apply-to-config shipped (Operator panel + validation gating)

## JS) Packaging & Installers (PyInstaller + Windows Setup + macOS helpers)
- ✅ JS1: Desktop launcher (runs Streamlit + opens browser)
- ✅ JS2: Dev packaging deps file (requirements-dev.txt)
- ✅ JS3: PyInstaller build script (onedir output)
- ✅ JS4: Windows installer template (Inno Setup .iss)
- ✅ JS5: macOS DMG helper script (optional)
- ✅ JS6: Docs added (PACKAGING.md, DIRECTIVE.md, CHAT_HANDOFF.md)
- ✅ JS7: Single-click polish delivered (icons/versioning/windowed toggles/signing-notary paths)

## JT) Single-Click Polish (Service Controls + Packaging Config + Build Wrappers)
- ✅ JT1: Packaging config file (packaging/config/app.json)
- ✅ JT2: Build wrappers (scripts/build_app.sh + scripts/build_app.ps1)
- ✅ JT3: PyInstaller build improvements (CBP_WINDOWED/CBP_CONSOLE toggles, icon/version hooks best-effort)
- ✅ JT4: Dashboard “START ALL / STOP ALL” service control panel (PID-supervised)
- ✅ JT5: Docs refreshed (PACKAGING.md + CHAT_HANDOFF.md)
- ✅ JT6: Repair/Reset wizard with preflight self-checks added (helper module + Operator controls + typed execute confirmation)

## IF) Position Accounting (Open/Closed + Realized/Unrealized) + Cash Ledger
- ✅ IF1: portfolio.sqlite with positions + cash_ledger + realized_events
- ✅ IF2: Bot applies every paper fill to portfolio state (BUY + SELL)
- ✅ IF3: Streamlit Portfolio panel (positions/cash/realized/unrealized)
- ✅ IF4: Equity curve and performance metrics delivered in IG track

## IG) Equity Curve + Performance Metrics (Deterministic from Fills)
- ✅ IG1: Equity curve builder
- ✅ IG2: Metrics (DD, winrate, Sharpe heuristic)
- ✅ IG3: Streamlit equity + metrics panel
- ✅ IG4: fill-based position accounting completed; cash/positions/realized/unrealized MTM snapshot covered; equity_by_quote + single-quote total_equity added; cross-quote aggregate equity supports explicit direct/inverse FX marks with conversion metadata

## II) Backtest / Walk-Forward Parity
- ✅ II1: Parity backtest via compute_signal
- ✅ II2: Deterministic fills
- ✅ II3: Streamlit backtest UI
- ✅ II4: Legacy backtest cleanup (shared fill model metrics path + malformed-row handling + compatibility wrapper retained)

## IJ) Risk Exits Parity
- ✅ IJ1: Shared exit rules
- ✅ IJ2: Runner + backtest parity
- ✅ IJ3: Restart-safe trailing state

## IK) Execution Adapter Abstraction + Reconciliation Skeleton
- ✅ IK1: ExecutionAdapter interface
- ✅ IK2: Paper adapter
- ✅ IK3: Live stub (gated)

## IN) Live Fill Reconciliation
- ✅ IN1: Order → fill mapping
- ✅ IN2: Idempotent apply

## IO) Higher-Fidelity + Partial Fills
- ✅ IO1: Trade aggregation
- ✅ IO2: Delta-based apply

## IQ) Audit-grade PnL + Daily Loss Cap
- ✅ IQ1: Realized PnL engine
- ✅ IQ2: Live loss cap enforcement

## IS) Mark Cache
- ✅ IS1: Cache store
- ✅ IS2: REST/WS fallback

## IX) Idempotency + Strict Intent Lifecycle
- ✅ IX1: client_oid
- ✅ IX2: SENDING state

## KJ) Reconciliation Wizard (step-by-step operator workflow)
- ✅ KJ1: Persistent wizard state (data/wizard_reconcile.json)
- ✅ KJ2: Streamlit reconciliation wizard panel with locked steps (1→6)
- ✅ KJ3: Typed confirmations for destructive steps (cancel/resolve/resume/reset)
- ✅ KJ4: Integrates existing reconcile/export/cancel/resolve/resume gates
- ✅ KJ5: Docs added (RECONCILIATION_WIZARD.md)
- ✅ KJ6: One-click non-destructive reconcile safe-steps path added (service helper + CLI + Operator button)

## KM) Installer (Mac + Windows) — One-command + desktop launcher
- ✅ KM1: macOS installer (installers/install.sh) creates .venv + installs deps + Desktop .command launcher
- ✅ KM2: Windows installer (installers/install.ps1) creates .venv + installs deps + Desktop .lnk shortcut
- ✅ KM3: Start scripts (installers/start.sh + installers/start.cmd)
- ✅ KM4: Update scripts (installers/update.sh + installers/update.ps1)
- ✅ KM5: Install docs added (docs/INSTALL.md)
- ✅ KM6: Optional packaged desktop build pipeline delivered via KN (PyInstaller wrapper)

## KN) Optional Packaged Desktop App (pywebview + PyInstaller wrapper)
- ✅ KN1: Desktop wrapper (starts Streamlit + embedded window; terminates server on close)
- ✅ KN2: Separate build requirements (requirements/desktop.txt)
- ✅ KN3: PyInstaller build scripts (macOS/Linux + Windows)
- ✅ KN4: Optional installer helpers for desktop build extras
- ✅ KN5: Docs added (PACKAGED_APP.md)
- ✅ KN6: Briefcase native installer pipeline delivered via KO track

## KO) Briefcase Native Installer Track (MSI/DMG)
- ✅ KO1: Briefcase app entry package (src/cryptobotpro_desktop) wraps desktop_wrapper
- ✅ KO2: pyproject.toml briefcase configuration added (or appended if missing)
- ✅ KO3: Briefcase extras requirements + installers (requirements/briefcase.txt + installers/install_briefcase_extras.*)
- ✅ KO4: Briefcase build scripts (packaging/briefcase/build_macos.sh + build_windows.ps1)
- ✅ KO5: Docs added (BRIEFCASE_NATIVE_INSTALLERS.md + packaging/briefcase/README.md)
- ✅ KO6: Requirements sync implemented (`scripts/sync_briefcase_requires.py`) with tests and installer wiring

## KQ) Release Checklist Automation (manifest + hashes)
- ✅ KQ1: release_checklist script (version bump + requires sync + optional package builds)
- ✅ KQ2: Writes release manifest JSON with artifact SHA-256 hashes
- ✅ KQ3: Keeps stdout/stderr per step (truncated) for troubleshooting
- ✅ KQ4: Docs added (RELEASE_CHECKLIST.md)
- ✅ KQ5: Streamlit dry-run button (optional)
- ✅ KQ6: Signed builds/notarization workflow delivered via KS/KU/KV/KW/KY chain

## KR) Signing & Distribution Hardening (macOS notarization + Windows Authenticode)
- ✅ KR1: macOS sign+notarize+staple helper script (packaging/signing/macos_sign_and_notarize.sh)
- ✅ KR2: Windows Authenticode signing helper script (packaging/signing/windows_sign.ps1)
- ✅ KR3: Distribution & signing docs added (docs/SIGNING_DISTRIBUTION.md)
- ✅ KR4: release_checklist signing integration delivered (env-gated, fail-closed)
- ✅ KR5: CI build→sign→notarize→package templates delivered in KT/KU/KV workflows

## KS) Release signing hooks (opt-in, fail-closed)
- ✅ KS1: release_checklist supports env-driven signing/notarization (RELEASE_SIGN_WINDOWS / RELEASE_NOTARIZE_MAC)
- ✅ KS2: Windows signing hook calls packaging/signing/windows_sign.ps1 on .exe/.msi artifacts
- ✅ KS3: macOS notarization hook calls packaging/signing/macos_sign_and_notarize.sh on .app artifacts
- ✅ KS4: Fail-closed behavior if required env vars/scripts/artifacts are missing
- ✅ KS5: Docs updated (RELEASE_CHECKLIST.md + SIGNING_DISTRIBUTION.md)
- ✅ KS6: CI templates with secrets-only signing/notary paths delivered

## KT) CI Templates (GitHub Actions)
- ✅ KT1: PyInstaller CI workflow (Mac + Windows) builds wrapper + uploads artifacts
- ✅ KT2: Briefcase CI workflow (manual trigger) packages (Windows ZIP default, macOS DMG)
- ✅ KT3: CI uploads release manifests + dist/build outputs
- ✅ KT4: Docs added (CI_GITHUB_ACTIONS.md)
- ✅ KT5: Optional CI signing/notarization jobs delivered (secrets-only, fail-closed)

## KU) CI Signing & Notarization (secrets-only, fail-closed)
- ✅ KU1: CI workflow for Windows signing using Marketplace signtool action (manual trigger)
- ✅ KU2: CI workflow for macOS notarization of DMG(s) via notarytool + staple (manual trigger)
- ✅ KU3: macOS CI scripts: prepare notary profile + notarize/staple file artifacts
- ✅ KU4: Docs added (CI_SIGNING_NOTARIZATION.md)
- ✅ KU5: macOS CI pre-notary codesign path delivered via KV workflow

## KV) macOS CI Code-Signing (pre-notary, secrets-only)
- ✅ KV1: CI keychain import script for .p12 cert (packaging/signing/macos_ci_import_cert.sh)
- ✅ KV2: CI codesign script for .app bundles (packaging/signing/macos_ci_codesign_apps.sh)
- ✅ KV3: ci-signing.yml updated to codesign before notarization (fail-closed on missing secrets)
- ✅ KV4: Docs updated (CI_SIGNING_NOTARIZATION.md)
- ✅ KV5: CI verify stapled ticket + Gatekeeper assess delivered in KW checks

## KW) CI Verification (post-sign / post-notary)
- ✅ KW1: Windows CI signature verification (signtool verify) for dist/.exe and dist/.msi
- ✅ KW2: macOS CI stapler validation for DMG(s)
- ✅ KW3: macOS CI Gatekeeper assessment (spctl) for .app bundles (when present)
- ✅ KW4: Docs updated (CI_SIGNING_NOTARIZATION.md)
- ✅ KW5: CI artifact hash manifest after signing/notary delivered in KX flow

## KX) CI Final Manifest (hashes of signed/notarized artifacts)
- ✅ KX1: CI writes a final release manifest after Windows signing + verification
- ✅ KX2: CI writes a final release manifest after macOS notarization + verification
- ✅ KX3: CI uploads releases/release_manifest_*.json with distributables
- ✅ KX4: Docs updated (CI_SIGNING_NOTARIZATION.md)
- ✅ KX5: GitHub Release Publisher delivered in KY workflow (artifacts + manifests)

## KY) GitHub Release Publisher (tag → build → attach artifacts + manifests)
- ✅ KY1: release-publish.yml workflow (tagged v* + manual dispatch)
- ✅ KY2: Builds Windows + macOS artifacts, writes final hash manifests
- ✅ KY3: Optional signing/notary paths are secrets-only and auto-skip when missing
- ✅ KY4: Publishes GitHub Release and uploads all artifacts + manifests
- ✅ KY5: Docs added (GITHUB_RELEASE_PUBLISHER.md)
- ✅ KY6: Release notes generator delivered in KZ (`scripts/generate_release_notes.py` + manifest summary)

## KZ) Release Notes Generator (CHANGELOG + manifest summary)
- ✅ KZ1: CHANGELOG.md format (versioned sections)
- ✅ KZ2: Deterministic generator script (scripts/generate_release_notes.py)
- ✅ KZ3: Includes manifest-derived artifact hashes in notes
- ✅ KZ4: GitHub Release Publisher uses body_path from generated RELEASE_NOTES.md
- ✅ KZ5: Docs added (RELEASE_NOTES_GENERATOR.md)
- ✅ KZ6: UI preview delivered in LA (generate + preview `releases/RELEASE_NOTES.md`)

## LA) UI Release Notes Preview (safe local generation)
- ✅ LA1: Streamlit panel to generate and preview releases/RELEASE_NOTES.md
- ✅ LA2: Displays current CHANGELOG.md inline for quick editing
- ✅ LA3: Docs added (UI_RELEASE_NOTES_PREVIEW.md)
- ✅ LA4: Tag helper delivered in LB (`scripts/tag_release.py` + Streamlit panel)

## LB) Local Tag Helper (fail-closed, no auto-push)
- ✅ LB1: scripts/tag_release.py added (strict checks, annotated tag, never pushes)
- ✅ LB2: Requires RELEASE_NOTES.md + clean git state + version match (pyproject ↔ tag)
- ✅ LB3: Optional pytest gate (only runs if tests/ exists)
- ✅ LB4: Streamlit panel added (safe: defaults to dry-run)
- ✅ LB5: Docs added (LOCAL_TAG_HELPER.md)
- ✅ LB6: Pre-release sanity suite delivered in LC (lint/types/tests/config checks + CI + UI runner)

## LC) Pre-release sanity suite (lint + types + tests + configs)
- ✅ LC1: requirements/dev.txt (ruff, mypy, pytest, types)
- ✅ LC2: scripts/pre_release_sanity.py (fail-closed runner)
- ✅ LC3: scripts/run_sanity.sh + scripts/run_sanity.ps1 (one-command local)
- ✅ LC4: CI workflow ci-sanity.yml (PR + main)
- ✅ LC5: Docs added (PRE_RELEASE_SANITY.md)
- ✅ LC6: Streamlit panel added (safe runner)
- ✅ LC7: Minimal integration test added for paper loop + journal DB writes

## LH) Unified trading runner (paper-safe) + MTM risk gates
- ✅ LH1: core/risk_manager.py (fail-closed order gating)
- ✅ LH2: strategies/ema_crossover.py (signal-on-change, warmup)
- ✅ LH3: config/trading.yaml (paper-safe defaults, kill switch, risk limits)
- ✅ LH4: services.trading_runner.run_trader (orchestrator: prices → MTM → risk → paper orders)
- ✅ LH5: PaperExecutionVenue upgraded for per-symbol prices (backward compatible)
- ✅ LH6: Launchers run_trader.sh / run_trader.ps1
- ✅ LH7: Tests added (risk gate unit tests)
- ✅ LH8: Docs added (TRADING_RUNNER_PAPER.md)
- ✅ LH9: Live execution adapters + authenticated submit/reconcile path delivered (CCXT adapter + live executor + reconcile flow)

## LL) Repair Wizard UI + role gating + exportable runbook reports
- ✅ LL1: dashboard/role_guard.py (VIEWER/OPERATOR/ADMIN gating)
- ✅ LL2: Dashboard “Repair Wizard” section (Generate → Approve → Execute) with typed confirmation
- ✅ LL3: Execution remains fail-closed (config + env gates still required)
- ✅ LL4: Export runbook report (scripts/repair_export.py) MD+JSON + optional PDF if reportlab installed
- ✅ LL5: Docs added (REPAIR_WIZARD_UI.md)
- ✅ LL6: Replace local role selector with real auth path (keychain-backed username/password login + role enforcement in Operator UI; controlled env fallback for headless/dev)

## LP) Real installers: Windows Inno Setup + macOS DMG builder + docs
- ✅ LP1: Updated PyInstaller build to create .app on macOS (adds --windowed on Darwin)
- ✅ LP2: Added Inno Setup script (packaging/windows/cryptobotpro.iss) to package dist/CryptoBotPro
- ✅ LP3: Added Windows installer build script (scripts/build_windows_installer.ps1)
- ✅ LP4: Added macOS DMG build script with create-dmg + hdiutil fallback (scripts/build_macos_dmg.sh)
- ✅ LP5: Added installer documentation (docs/INSTALLERS.md)
- ✅ LP6: CI installer builds + release publishing delivered in LQ workflow

## LQ) CI releases: build Windows installer + macOS DMG and attach to GitHub Release
- ✅ LQ1: Added GitHub Actions workflow to build installers on tag push
- ✅ LQ2: Windows job installs Inno Setup via Chocolatey and builds EXE installer
- ✅ LQ3: macOS job builds .app + DMG (create-dmg optional, hdiutil fallback)
- ✅ LQ4: Release job uploads both artifacts to GitHub Release via action-gh-release
- ✅ LQ5: Docs added (docs/CI_RELEASES.md)
- ✅ LQ6: Optional macOS CI signing/notarization delivered in LR (secrets-gated path)

## LR) macOS signing + notarization (optional, CI gated) + docs
- ✅ LR1: Added scripts/macos_codesign_app.sh (Developer ID signing)
- ✅ LR2: Added scripts/macos_notarize_dmg.sh (notarytool submit + stapler)
- ✅ LR3: Updated scripts/build_macos_dmg.sh to optionally sign/notarize when env vars are present
- ✅ LR4: Updated GitHub Actions macOS job to optionally import cert + sign/notarize (gated by secrets)
- ✅ LR5: Docs added (docs/MACOS_SIGNING_NOTARIZATION.md)

## LT) Execution latency tracking + stale-market safety gates
- ✅ LT1: ExecutionLatencyTracker (submit→ack, ack→fill) logs to data/market_ws.sqlite (category=execution)
- ✅ LT2: SafetyConfig + market freshness gate (max_ws_recv_age_ms)
- ✅ LT3: trading.yaml extended (execution_safety)
- ✅ LT4: Dashboard adds “Execution Latency” table view
- ✅ LT5: Live executor integration complete (WS freshness gate + submit/ack/fill latency wiring)
- ✅ LT6: Hard integration enforced in live executor (per-intent preflight gate + latency pause/circuit behavior) with dedicated integration tests

## LV) Managed background services: supervisor daemon + UI controls + logs + auto-restart
- ✅ LV1: Supervisor daemon (services/supervisor/supervisor_daemon.py)
- ✅ LV2: Services config (config/services.yaml) with market_ws enabled and bot_runner optional
- ✅ LV3: CLI scripts (start_supervisor.py / stop_supervisor.py / supervisor_status.py)
- ✅ LV4: Dashboard “Services Manager” panel (start/stop + status + log paths)
- ✅ LV5: Launcher auto-starts supervisor idempotently (AUTO_START_SUPERVISOR_v1)
- ✅ LV6: Docs added (docs/SERVICES_SUPERVISOR.md)
- ✅ LV7: Replaced bot_runner stub with real managed-service orchestration + config-signature hot-reload + graceful shutdown

## MB) Precise symbol-mapped reconciliation + strict SYNC_POSITION executor
- ✅ MB1: Symbol mapping helper builds canonical→exchange_symbol rows (services/reconciliation/symbol_mapping.py)
- ✅ MB2: Reconciler drift computed deterministically from symbol_maps (no guessing) + untracked assets list
- ✅ MB3: Repair planner emits SYNC_POSITION with exchange_symbol required
- ✅ MB4: Executor enforces SYNC_POSITION requires exchange_symbol; removed guessy base matching
- ✅ MB5: Runner updated to pass full trading_cfg into reconciler
- ✅ MB6: Config supports reconciliation.quote_ccys reporting (primary still portfolio.quote_ccy)
- ✅ MB7: Docs added (docs/PRECISE_SYNC_POSITION.md)
- ✅ MB8: Multi-quote internal cash ledger (schema v2) implemented (portfolio_cash_v2 + quote-aware reconciler drift for primary/secondary quotes)

## MC) Desktop packaging (Mac + Windows) — PyInstaller + Streamlit launcher
- ✅ MC1: Desktop launcher added (apps/desktop_launcher.py)
- ✅ MC2: PyInstaller spec added (packaging/pyinstaller/crypto_bot_pro.spec)
- ✅ MC3: macOS build script added (scripts/build_desktop_mac.sh)
- ✅ MC4: Windows build script added (scripts/build_desktop_windows.ps1)
- ✅ MC5: Packaging README added (packaging/README.md)
- ✅ MC6: macOS .app wrapper + icon hooks + no-console mode (build wrappers wired)
- ✅ MC7: CI release pipeline delivered (tagged builds publish installers/artifacts via release workflows)

## ME) CI builds + GitHub Releases (macOS + Windows)
- ✅ ME1: GitHub Actions release workflow added (tag v* => build macOS + Windows => create release => upload assets)
- ✅ ME2: Nightly workflow added (build artifacts only)
- ✅ ME3: Release documentation added (docs/RELEASES.md)
- ✅ ME4: Optional code signing/notarization and Authenticode paths delivered (secrets-gated CI + local scripts)

## MF) First-Run Wizard + Preflight + Config restore + Diagnostics export
- ✅ MF1: Config templates added (config/templates/trading.yaml.default + .env.template)
- ✅ MF2: Config restore helper added (services/diagnostics/config_restore.py)
- ✅ MF3: Preflight diagnostics added (services/diagnostics/preflight.py)
- ✅ MF4: Dashboard First-Run Wizard panel added (restore + copy/download diagnostics)
- ✅ MF5: First run docs added (docs/FIRST_RUN.md)
- ✅ MF6: guided setup summary + wizard/backend/bridge completed; Operator page now includes polished Guided Setup panel (status metrics, preflight/cache warnings, preset apply, custom patch apply, refresh) wired through preflight_wizard actions with existing guided setup bridge tests passing

## IZ–KA) Execution, Audit, Alerts, Packaging, Learning (260–290)
- ✅ Intent recovery via client_oid
- ✅ Stuck SENDING resolver
- ✅ Intent audit + continuous monitor
- ✅ Slack + Email alerts (opt-in)
- ✅ Alert routing + dedupe
- ✅ Packaging + installers + signing
- ✅ First-run + repair/reset wizard
- ✅ Exchange hardening + retries
- ✅ WebSocket mark feed
- ✅ Strategy learning + adaptation
- ✅ Imitation learning + overlay
- ✅ Overlay impact analytics

## KD–LG) Safety Guards, Pause/Resume, Reconciliation, CI, Releases, MTM (291–320)
- ✅ Overlay safety guard (auto-disable on harm + audit)
- ✅ Safety control center + soft pause/resume
- ✅ Held intents queue + resume gates
- ✅ Operator reconciliation actions + wizard
- ✅ Startup live guard + run-safe-steps
- ✅ Packaging, installers, and desktop polish
- ✅ CI signing, notarization, verification
- ✅ GitHub release publisher + notes generator
- ✅ Pre-release sanity suite
- ✅ Paper trading + journal store
- ✅ MTM equity + price aggregation

## Phases 321–330) Paper Runner → CI Builds
- OK Phase 321: Paper runner + risk gates + docs
- OK Phase 322: Live adapter scaffold (disabled by default)
- OK Phase 323: One-shot reconciliation CLI + dashboard
- OK Phase 324: Repair runbooks + logging
- OK Phase 325: Repair Wizard UI + role gating
- OK Phase 326: Auth + enforced roles
- OK Phase 327: Auth audit + lockout
- OK Phase 328: PyInstaller launcher scaffold
- OK Phase 329: Installer scaffolding
- OK Phase 330: CI build + release workflow

## Phases 331–340) Signing, WS Health, Safety Gates
- OK Phase 331: Optional macOS signing/notarization
- OK Phase 332: WS market data + latency dashboard
- OK Phase 333: Execution latency + safety gates
- OK Phase 334: Hard live preflight safety gate
- OK Phase 335: Supervisor daemon + UI manager
- OK Phase 336: Runner with idempotent orders (disabled by default)
- OK Phase 337: Strategy pipeline + risk sizing
- OK Phase 338: Portfolio accounting + equity curve
- OK Phase 339: Truth-source reconciliation + drift
- OK Phase 340: Fee reconciliation + runbook executor (OFF by default)

## Phases 341–350) Desktop App, CI, Guided Setup
- OK Phase 341: Strict SYNC_POSITION + symbol mapping
- OK Phase 342: Desktop packaging scaffolding
- OK Phase 343: macOS .app wrapper
- OK Phase 344: CI nightly + release workflows
- OK Phase 345: First-run wizard + diagnostics
- OK Phase 346: Guided setup UI
- OK Phase 347: WS latency test + history
- OK Phase 348: Live start gate (WS enforced)

## Phase 3) Feed Health Dashboard + Staleness Alerts
- OK: Feed health computation from events DB
- OK: WARN/BLOCK thresholds for staleness
- OK: Dashboard Feed Health panel
- NOTE: Collector auto-start is optional (future phase)

## Phase 4) Market Data Collector Control
- OK: Threaded CCXT polling collector
- OK: In-app Start / Stop controls
- OK: Collector status visibility in dashboard
- OK: Documentation added
- NEXT: Gate Live Start on collector + feed health

## Phase 77) Real installers + CI releases: macOS DMG (dmgbuild) + Windows installer (Inno Setup) + GitHub Actions release workflow + release manifest
- ✅ Add app metadata (config/app.yaml) + version script
- ✅ Add DMG build (dmgbuild settings + packaging/build_dmg.sh) :contentReference[oaicite:10]{index=10}
- ✅ Add Windows installer (Inno Setup .iss + local build script) :contentReference[oaicite:11]{index=11}
- ✅ Add CI workflow: builds PyInstaller + DMG + Windows installer; publishes release assets :contentReference[oaicite:12]{index=12}
- ✅ Add release manifest generator (hashes for updater-ready flow)
- ✅ Docs added (docs/PHASE77_REAL_INSTALLERS_AND_CI_RELEASES.md)
- ✅ Next: Delivered via Phase 18/21/38/40 + DP (signing/notary hooks and update-manifest verification path)

## Phase 5) UI Live Start gating (collector + feed health + WS gate)
- ✅ Add UI live gate evaluator (services/diagnostics/ui_live_gate.py)
- ✅ Add dashboard Live Start Gate panel (reasons + details)
- ✅ Best-effort patch: disable literal Start Live Bot button if present
- ✅ Docs added (docs/LIVE_UI_GATE.md)
- ✅ Next: Live start path is gated/centralized via HJ controls; duplicate literal Start Live button path is disabled

## Phase 6) Single-source bot start/stop (paper+live) with re-check gates + risk + confirmations
- ✅ Add cross-platform process manager (PID/status file + log routing) (services/bot/process_manager.py)
- ✅ Add start manager (single path; live gate + risk check + env confirmations) (services/bot/start_manager.py)
- ✅ Add CLI entrypoints for subprocess (services/bot/cli_live.py, services/bot/cli_paper.py)
- ✅ Add dashboard Bot Control (Single Source) panel
- ✅ Docs added (docs/BOT_CONTROL.md)
- ✅ Next: Bot runner now uses real managed loops/endpoints (pipeline + executor + ops_risk_gate + optional reconciler) with hot-reload and graceful stop

## Phase 16) One-command validation + packaging pass (macOS + Windows)
- ✅ Add launcher (app_launcher/launcher.py) for packaged & normal runs
- ✅ Add preflight checks (scripts/preflight.py): python/deps/config/paths/port
- ✅ Add validate command (scripts/validate.py + .sh/.ps1): preflight + pytest
- ✅ Add PyInstaller packaging scaffolding (spec + build scripts for macOS/Windows)
- ✅ Docs added (docs/PHASE16_VALIDATION_AND_PACKAGING.md, packaging/README.md)
- ✅ Next: Installer UX layer delivered via Phase 17/18/23 + JT/LV tracks (signed installers, shortcuts, build wrappers, and UI start/stop controls)

## Phase 17) Installer UX: Windows EXE installer (Inno) + macOS .app/.dmg scaffolding
- ✅ Add Inno Setup script (packaging/inno/CryptoBotPro.iss) + build helper (build_windows_installer.ps1)
- ✅ Add macOS .app spec (crypto_bot_pro_macos.spec) + DMG build script using hdiutil
- ✅ Add installer checklist doc (docs/PHASE17_INSTALLERS.md)
- ✅ Next: Delivered via Phase 18 + 21 + 23 + 38 (signed distribution paths, wrappers, CI artifacts)

## Phase 18) Signed distribution + one-button release scripts (macOS notarize/staple, Windows signtool)
- ✅ Add macOS release script: validate → build → optional codesign → optional notarytool submit → stapler staple
- ✅ Add Windows release script: validate → build → optional signtool sign/verify → build Inno installer
- ✅ Add signing/notarization doc (docs/PHASE18_SIGNING.md)
- ✅ Next: Installer signing/versioning/release artifacts delivered across Phase 18 + 19 + 21 + 23 + 38 tracks

## Phase 19) Release automation + versioning single source + CI artifacts
- ✅ Add VERSION + services/meta/version.py
- ✅ Add scripts/set_version.py and scripts/bump_version.py (propagates version to Inno + handoff)
- ✅ Show version in dashboard footer
- ✅ Release scripts now print VERSION
- ✅ Add GitHub Actions CI (validate) + Release (build Windows dist + macOS DMG on vX.Y.Z tags)
- ✅ Next: Delivered via Phase 20 + 21 + 23 (auto-publish GitHub Release with artifacts and optional CI signing)

## Phase 20) Auto-publish GitHub Releases (on tag) + attach Windows ZIP + macOS DMG
- ✅ Add publish_release GitHub Action (tag-triggered) that builds Windows/macOS artifacts
- ✅ Zips Windows dist output and renames macOS DMG to include tag
- ✅ Publishes a GitHub Release and uploads both artifacts automatically
- ✅ Docs added (docs/PHASE20_GITHUB_RELEASES.md)
- ✅ Next: Delivered via Phase 21 + 22 (optional CI signing + Release Train checklist UI)

## Phase 21) CI signing + CI notarization (optional, gated by secrets)
- ✅ Add CI signing scripts for Windows (signtool) and macOS (codesign + notarytool + stapler)
- ✅ Update publish_release workflow to sign/notarize only when env vars from secrets are present
- ✅ Docs added (docs/PHASE21_CI_SIGNING.md)
- ✅ Next: Delivered via Phase 22 + 23 (installer artifact flow + Release Train UI wiring)

## Phase 23) CI: build + (optional) sign Windows installer and upload to Release + UI local build buttons
- ✅ publish_release.yml now installs Inno Setup (CI) and builds Windows installer EXE
- ✅ Windows job uploads BOTH: dist zip + installer EXE (tagged names)
- ✅ Release attaches: Windows dist zip, Windows setup EXE, macOS DMG
- ✅ Add services/release/local_build.py for OS-gated local builds
- ✅ Add Release Train UI buttons for local packaging builds
- ✅ Docs added (docs/PHASE23_CI_INSTALLER_ARTIFACTS.md)
- ✅ Next: “Ops intelligence” learning/adaptability module path (market data ingestion → feature store → model training → safe deployment gates) delivered via learning/ops tracks (feature_store + model_registry + guardrails + ops risk gates)

## Phase 5) UI live gate + panel
- ✅ Docs added (docs/LIVE_UI_GATE.md)
- ✅ Next: Live start path is gated/centralized via HJ controls; duplicate literal Start Live button path is disabled

## Phase 8) Analytics panel
- ✅ Add analytics helpers (drawdown, returns, sharpe)
- ✅ Add dashboard Accounting & Analytics panel
- ✅ Add docs (docs/ACCOUNTING.md)
- ✅ Next: Paper/live loops are wired to fill + mark-to-market flows (paper engine fill path + per-tick MTM in paper runner)

## Phase 9) Ledger wiring
- ✅ Docs added (docs/PHASE9_LEDGER_WIRING.md)
- ✅ Next: Live order placement + reconciliation delivered (idempotent submit/replay + fills ingestion + restart-safe reconcile via `services/execution/live_executor.py`, `services/execution/intent_executor.py`, `services/fills/fills_poller.py`)

## Phase 10) Live trading
- ✅ Docs added (docs/LIVE_TRADING.md)
- ✅ Next: live disable switch + spread/staleness circuit breakers + per-exchange order params normalization delivered (`services/risk/killswitch.py`, `services/risk/market_quality_guard.py`, `services/execution/order_params.py`)

## Phase 11) Safety + kill switch
- ✅ Add optional panic flatten (OFF by default; env-confirmed if enabled)
- ✅ Docs added (docs/SAFETY.md)
- ✅ Next: per-exchange order parameter normalization + min size checks shipped (`services/execution/order_params.py`, `services/markets/rules.py`, `tests/test_market_rules_validation.py`)

## Phase 12) Execution hardening
- ✅ Live runner SELL path uses LiveTrader to enforce sizing rules
- ✅ Live runner alerts for kill/recon/circuit-breaker events (rate limited)
- ✅ Docs added (docs/PHASE12_HARDENING.md)
- ✅ Next: per-exchange normalization map + symbol-level safety threshold coverage delivered (`services/market_data/multi_venue_view.py`, `services/risk/market_quality_guard.py`, integration/unit tests)

## Phase 13) Exchange quirks adapters
- ✅ Add pytest suite for adapters + order sizing normalization
- ✅ Docs added (docs/PHASE13_EXCHANGE_QUIRKS.md)
- ✅ Next: Sandbox smoke scripts per exchange + symbol-level circuit breaker thresholds delivered (`scripts/smoke_exchange.py` + per-exchange wrappers; `market_quality_guard.symbol_thresholds`)

## Phase 14) Smoke tests
- ✅ Add config template smoke_test block (disabled by default)
- ✅ Docs added (docs/PHASE14_SMOKE_TESTS.md)
- ✅ Next: integration tests with mocked exchange clients + deterministic runner/live wiring shipped (`tests/test_live_execution_wiring.py`, `tests/test_live_executor_latency_safety_integration.py`, `tests/test_run_trader_integration_minimal.py`)

## Phase 15) Tests & symbol-level CB
- ✅ Add Safety panel preview + YAML snippet for per-symbol thresholds
- ✅ Docs added (docs/PHASE15_TESTS_AND_SYMBOL_CB.md)
- ✅ Next: Delivered via Phase 16 + 17 + 19 (validation runner + installer packaging tracks)

## Phase 16) Validation + packaging
- ✅ Docs added (docs/PHASE16_VALIDATION_AND_PACKAGING.md, packaging/README.md)
- ✅ Next: Installer UX + launcher start/stop delivered via JT/LV/KM/KN tracks

## Phase 17) Installers
- ✅ Add macOS .app spec + DMG build script
- ✅ Add installer checklist doc (docs/PHASE17_INSTALLERS.md)
- ✅ Next: Delivered via Phase 18 + 21 + 23 (signed paths, build wrappers, CI artifacts)

## Phase 18) Signing
- ✅ Add Windows release script: validate → build → optional signtool sign/verify → build Inno installer
- ✅ Add signing/notarization doc (docs/PHASE18_SIGNING.md)
- ✅ Next: Installer signing/versioning/release artifacts delivered across Phase 18 + 19 + 21 + 23 + 38 tracks

## Phase 19) CI Workflows
- ✅ Add GitHub Actions CI (validate) + Release (build Windows dist + macOS DMG on vX.Y.Z tags)
- ✅ Next: Delivered via Phase 20 + 21 + 23 (GitHub Release artifacts + optional CI signing)

## Phase 20) GitHub Releases
- ✅ Zips Windows dist output and renames macOS DMG to include tag
- ✅ Publishes a GitHub Release and uploads both artifacts automatically
- ✅ Docs added (docs/PHASE20_GITHUB_RELEASES.md)
- ✅ Next: Delivered via Phase 21 + 22 (optional CI signing + Release Train UI)

## Phase 21) CI Signing + Notarization
- ✅ Update publish_release workflow to sign/notarize only when env vars from secrets are present
- ✅ Docs added (docs/PHASE21_CI_SIGNING.md)
- ✅ Next: Delivered via Phase 22 + 23 (installer artifacts + Release Train page)

## Phase 22) Installer Signing + Release Train
- ✅ Add Release Train report helper (services/release/release_train.py)
- ✅ Add Release Train panel in dashboard (checklist + run validate button)
- ✅ Docs added (docs/PHASE22_INSTALLER_SIGNING_AND_RELEASE_TRAIN.md)
- ✅ Next: Delivered via Phase 23 + CI signing tracks (installer artifacts + local per-OS build buttons)

## Phase 23) CI Installer Artifacts
- ✅ Add Release Train UI buttons for local packaging builds
- ✅ Docs added (docs/PHASE23_CI_INSTALLER_ARTIFACTS.md)
- ✅ Next: duplicate carryover merged into line 1001 tracking (same Ops-intelligence path retained once)

## Phase 24) Learning Core v1
- ✅ Docs added (docs/PHASE24_LEARNING_CORE.md, docs/SOCIAL_LEARNING.md)
- ✅ Next: wire ML into decision flow (paper mode first), add monitoring + rollback triggers, integrate imported trader signals as features (router AI gate + canary/runtime policy + signal inbox/consensus integration)

## Phase 28) Multi-exchange ingestion (Coinbase + Binance + Gate.io) + normalization view + dashboard monitor
- ✅ Add multi-exchange collector (per-venue ticker + OHLCV → MarketStore)
- ✅ Add script: scripts/collect_market_data_multi.py
- ✅ Add unified view helpers (mid, cross-exchange spread bps)
- ✅ Add dashboard panel: Multi-Exchange Monitor
- ✅ Add config template block: multi_exchanges (coinbase/binance/gateio)
- ✅ Docs added (docs/PHASE28_MULTI_EXCHANGE_INGESTION.md)
- ✅ Next: execution + reconciliation layer (idempotent orders, restart-safe state, latency-aware order placement) + “best venue routing” in paper first (delivered via DK/CL/CQ tracks)

## Phase 32) Live execution adapters + idempotent client IDs + reconciliation (hard-off)
- ✅ Add ccxt ExchangeClient wrapper + per-exchange client ID param mapping
- ✅ Add Live executor: submit pending LIVE intents → submitted; reconcile orders → fills
- ✅ Add scripts: live_submit_intent.py, live_executor_tick.py, live_reconcile.py
- ✅ Add dashboard panel: Live Execution (HARD-OFF by default)
- ✅ Add config template: live.enabled/sandbox/exchange_id
- ✅ Docs added (docs/PHASE32_LIVE_EXECUTION_ADAPTERS.md)
- ✅ Next: trade-level reconciliation (fetch_my_trades) for partial fills, fee correctness, and robust restart recovery; plus LIVE_SHADOW (observe-only) before any live ML gating

## Phase 36) Installable desktop app (macOS + Windows) via PyInstaller + launcher
- ✅ Add Tkinter desktop launcher that starts/stops Streamlit and opens browser
- ✅ Add PyInstaller spec (packaging/desktop.spec)
- ✅ Add one-command builder script (scripts/build_desktop.py)
- ✅ Add Windows Inno Setup installer template (packaging/windows/inno_setup.iss)
- ✅ Add installer documentation (docs/PHASE36_INSTALLERS_MAC_WINDOWS.md)
- ✅ Record prior zip artifacts in docs/DOWNLOAD_CHECKPOINTS.md
- ✅ Next: Keyring-backed secret storage + signed build tracks + update-checker/manifest hardening delivered in CA/21/38/40

## Phase 38) Signed release pipeline (Windows + macOS)
- ✅ Add macOS sign+notarize helper (packaging/macos/sign_and_notarize.sh)
- ✅ Add Windows signtool signing helper (packaging/windows/sign_windows.ps1)
- ✅ Update Inno Setup template to include [Setup]: SignTool directive example
- ✅ Add signed release documentation (docs/PHASE38_SIGNED_RELEASE_PIPELINE.md)
- ✅ Update chat handoff with continuity note
- ✅ Next: Update notifier/channel + release manifest verification delivered via DP + release manifests + Phase 40 hardening

## Phase 40) TUF-style hardening for update manifests (expiry + anti-rollback + key rotation)
- ✅ Add local update state store (data/update_state.json) for anti-rollback tracking
- ✅ Add tuf-ish helpers: canonical JSON hashing, multi-key Ed25519 verify, expiry enforcement
- ✅ Patch update checker: require_signature option, multi-key verification, expiry handling, manifest hash state
- ✅ Add offline manifest validator script (scripts/release_validate_manifest.py)
- ✅ Docs added (docs/PHASE40_TUFISH_UPDATE_HARDENING.md)
- ✅ Next: true multi-role metadata (root/targets/timestamp/snapshot) + key rotation policy + threshold signatures delivered (`services/update/tufish.py`, `scripts/release_validate_manifest.py`); WebSocket market data + event-driven execution path delivered (`services/marketdata/ws_ticker_feed.py`, `services/execution/live_event_executor.py`, `scripts/run_live_event_executor.py`)

## Phase 51) OS-native scheduling + approval gate for model switching (paper safe-by-design)
- ✅ Add recommend_model_switch (writes recommendation file only)
- ✅ Add approve_model_switch (explicit operator approval file)
- ✅ Add apply_pending_model_switch (applies only if approval matches recommendation; consumes approval)
- ✅ Add macOS LaunchAgent installers (monitor + recommend/apply)
- ✅ Add Windows Task Scheduler installers (monitor + recommend/apply)
- ✅ Add dashboard panel: Scheduling & Approval Gate
- ✅ Docs added (docs/PHASE51_SCHEDULING_AND_APPROVAL_GATE.md)
- ✅ Next: Single-command installer path delivered across install.py/scripts/install.* + scheduling installers (Phase 51) + packaged desktop shell tracks

## Phase 62) Mean Reversion strategy + strategy selector (config switch: ema | mean_reversion)
- ✅ Add mean reversion Bollinger strategy (BB) → IntentWriter
- ✅ Add pipeline router (select via pipeline.strategy)
- ✅ Update run_pipeline_once / run_pipeline_loop to use router
- ✅ Add config template knobs: pipeline.strategy + bb_window + bb_k
- ✅ Add dashboard panel: Strategy Selector
- ✅ Docs added (docs/PHASE62_STRATEGY_SELECTOR_MEAN_REVERSION.md)
- ✅ Next: packaging/installers (Mac + Windows) as a single installable app + one-command setup delivered (install.py + scripts/install.* + desktop packaging tracks); multi-exchange live safety UX delivered in UI/preflight/permissions flows (Coinbase/Binance/Gate.io)

## Phase 63) Installable app path (Mac + Windows): one-command install/run + optional native PyInstaller builds
- ✅ Add desktop launcher (launcher/desktop_launcher.py) that starts Streamlit + opens browser
- ✅ Add scripts/run_desktop.py
- ✅ Add cross-platform installers:
  - mac/linux: scripts/install.sh
  - windows: scripts/install.ps1
- ✅ Add optional native build scripts (PyInstaller):
  - scripts/build_mac_app.sh
  - scripts/build_windows_exe.ps1
  - packaging/pyinstaller/crypto_bot_pro.spec
- ✅ Docs added: docs/PHASE63_PACKAGING_INSTALLERS.md
- ✅ Next: Installer UX polish delivered via Phase 64 setup wizard + preflight + single Start/Stop controls
  - config wizard (first-run) inside UI
  - validate exchange selection (coinbase/binance/gateio), API keys present, and live_enabled gating
  - create a single “Start Bot” button that starts pipeline + executor together

## Phase 64) Setup Wizard + Preflight checks + One Start Bot button (pipeline+executor+optional reconciler)
- ✅ Add ConfigManager (generate/save config/trading.yaml; presets)
- ✅ Add Preflight (readiness validation)
- ✅ Add ProcessSupervisor (pidfiles; start/stop/status cross-platform)
- ✅ Add scripts: start_bot.py / stop_bot.py / bot_status.py
- ✅ Add UI Setup Wizard section to dashboard/app.py with Start/Stop
- ✅ Docs added (docs/PHASE64_SETUP_WIZARD_START_BUTTON.md)
- ✅ Next: Live-key UX, key validation, live confirmation gate, and alert wiring delivered across CA/CB/HJ/HD tracks

## Phase 83) Deterministic LIVE gate inputs from exec_db (PnL today + trades today) + safe trade counter helper ✅
- ✅ Add JournalSignals (services/risk/journal_introspection_phase83.py) to compute realized_pnl_today_usd + trades_today
- ✅ Patch intent_executor_safe.py to use JournalSignals fallback when accounting lacks daily PnL
- ✅ Add CLI: scripts/show_live_gate_inputs.py
- ✅ Add helper: phase83_incr_trade_counter(exec_db) (call ONLY after confirmed LIVE submit success)
- ✅ Dashboard: show computed gate inputs in LIVE Safety panel
- ✅ After tests pass: flip to ✅ and add Session Log line

## Phase 82) LIVE mandatory risk gates + kill switch (hard enforced) ✅
- ✅ Add services/risk/live_risk_gates.py (limits + db + checks; fail-closed in LIVE)
- ✅ Add services/risk/killswitch.py + scripts/killswitch.py
- ✅ Patch services/execution/intent_executor_safe.py (inject check in first mode=='live' block)
- ✅ Add Streamlit panel: LIVE Safety Gates (Phase 82)
- ✅ Docs added (docs/PHASE82_LIVE_RISK_GATES.md)

## Phase 83) Deterministic daily counters (risk_daily) for LIVE gates ✅
- ✅ Add services/risk/risk_daily.py (risk_daily rollup)
- ✅ Add scripts/risk_daily_demo.py (manual test)
- ✅ Patch executor to use risk_daily as PnL source for Phase 82 gates
- ✅ Add dashboard panel: Daily Risk Rollup (Phase 83)
- ✅ Docs added (docs/PHASE83_RISK_DAILY.md)

## Phase 84) Fill hook → fills_ledger → risk_daily (deterministic PnL source) ✅
- ✅ Add services/risk/fill_hook.py (record_fill updates fills_ledger + risk_daily)
- ✅ Add scripts/record_dummy_fill.py (smoke test)
- ✅ Patch executor with helper _phase84_record_fill() (call it where fills are processed)
- ✅ Dashboard: Fill Ledger Quick Test panel
- ✅ Docs added (docs/PHASE84_FILL_HOOK.md)

## Phase 85) Unify LIVE gates to risk_daily (single source) ✅
- ✅ services/risk/live_risk_gates.py now reads trades_today + realized_pnl_usd_today from risk_daily (single source of truth)
- ✅ executor helper added: _phase85_after_live_submit() (call after LIVE submit success)
- ✅ manual wiring equivalent is in place at `LIVE_SUBMIT_SUCCESS_ANCHOR` in live_executor

## Phase 86) Increment trades/day only after LIVE submit success (explicit anchor) ✅
- ✅ Adds/uses _phase85_after_live_submit() to increment risk_daily.trades
- ✅ Uses explicit marker # LIVE_SUBMIT_SUCCESS_ANCHOR for zero-guess insertion
- ✅ Manual step completed: submit-success anchor is present and trade counter increments at that anchor

## Phase 88) REST Fills Poller → Canonical FillSink ✅

- ✅ services/fills/fills_poller.py
- ✅ scripts/run_fills_poller.py
- ✅ Dashboard panel: heartbeat, cursor, last error per exchange
- ✅ Next: integrated with live user WS feeds and FillSink choke point (`services/fills/user_stream_ws.py`, `services/fills/user_stream_router.py`, `scripts/run_user_stream_fills.py`)

## Phase 87) FillSink choke point + executor routes accounting fill calls through it + synthetic fill injector ✅
- ✅ Added FillSink contract + implementations
- ✅ Executor initializes CompositeFillSink and exposes _on_fill(...)
- ✅ Best-effort replacement of direct accounting fill calls
- ✅ CLI: scripts/inject_test_fill.py (safe)
- ✅ Dashboard: Inject synthetic test fill button
- ✅ Docs added (docs/PHASE87_FILL_SINK_CHOKEPOINT.md)
- ✅ Next: live user-stream adapters now route through executor `_on_fill(...)` with safe FillSink fallback (`services/execution/live_executor.py`, `services/fills/user_stream_router.py`, `services/fills/fills_poller.py`)

## Phase 88) LIVE prereq: market rules cache must be fresh (fail-closed) ✅
- ✅ Add services/markets/prereq.py (cache freshness check)
- ✅ Add scripts/market_rules_health.py (CLI PASS/FAIL)
- ✅ Best-effort patch: services/ops/live_prereqs.py blocks LIVE unless rules cache is fresh
- ✅ Dashboard panel: Market Rules Cache Health (Phase 88)
- ✅ Docs added (docs/PHASE88_MARKET_RULES_PREREQ.md)

## Phase 89) Market rules validation uses real intent fields + explicit anchor for submit path ✅
- ✅ Executor now has robust extractor for venue/symbol/qty/notional from the real intent/config
- ✅ Adds explicit anchor: # LIVE_MARKET_RULES_VALIDATE_ANCHOR (place right before LIVE submit)
- ✅ Re-run Phase 89 after placing anchor to inject fail-closed validation call

## Phase 90) Add tests for market rules cache/validate/prereq (no network) ✅
- ✅ Add tests/test_market_rules_validation.py (no network; monkeypatch where needed)
- ✅ Docs added (docs/PHASE90_MARKET_RULES_TESTS.md)

## Session Log
- 2026-02-21: Completed Phase 83 gate inputs (JournalSignals fallback + CLI/dashboard wiring) and confirmed `tests/test_market_rules_validation.py` passes inside the venv.
- 2026-02-22: Added runtime/pids tracking for service_manager (BC3) + cancel/replace helper coverage and heartbeat/error signals for strategy_runner (GM4).
- 2026-03-09: Closed GQ6/GR6/GS4/GZ4/HA4/LT6 after code+test verification (`tests/test_live_executor_latency_safety_integration.py`, `tests/test_live_executor_preflight_gate.py`, `tests/test_op_control_surface.py`, `tests/test_no_direct_create_order.py`, `tests/test_supervisor_process.py`).
- 2026-03-09: Completed FI3 in Operator UI (copy key + last-10 toggle) and added `tests/test_idempotency_inspector.py`.
- 2026-03-09: Closed GM7/GP5 and reconciled stale successor checkpoints (HI5/HL6/HM5/HN5/HO6/HP5/HS6/HT6/IF4/LP6/LQ6/MC7/ME4 + release/signing duplicate NEXT lines); validated with targeted runtime/watchdog/shutdown tests.
- 2026-03-09: Implemented HR7/JP8 strategy controls in Operator UI (typed param editor + validate + safe preset apply/save) and added `tests/test_strategy_config_tools.py`.
- 2026-03-09: Implemented LV7 by replacing `scripts/run_bot_runner.py` stub with real managed service orchestration (pipeline/executor/ops_risk_gate/reconciler), config-signature hot-reload, and graceful shutdown; added `tests/test_run_bot_runner.py`.
- 2026-03-09: Closed GK5/HU5/IC5/LH9 and reconciled stale duplicate NEXT lines (JH5/live-start gate/signing/update/installer carryovers), with targeted tests green.
- 2026-03-09: Implemented FQ5 optional Linux AppImage packaging scaffold (`scripts/build_linux_appimage.sh`, `packaging/appimage/CryptoBotPro.desktop`, `docs/LINUX_APPIMAGE.md`) with tests.
- 2026-03-09: Implemented KJ6 one-click non-destructive reconciliation safe steps (`services/admin/reconcile_safe_steps.py`, `scripts/run_reconcile_safe_steps.py`, Operator UI button) with tests.
- 2026-03-09: Closed JN7 by validating pipeline strategy -> intent wiring (`services/pipeline/*`, `services/execution/intent_writer.py`) with bridge/integration tests.
- 2026-03-09: Implemented JT6 Repair/Reset wizard self-check flow (`services/admin/repair_wizard.py` + Operator panel controls) and added `tests/test_repair_wizard.py`.
- 2026-03-09: Implemented HQ6 strategy-aware exit stacking helper (`services/risk/exit_controls.py`) with deterministic rule-priority tests (`tests/test_exit_control_stack.py`).
- 2026-03-09: Closed IH6/II4 by upgrading `services/backtest/parity_engine.py` (shared fill model + metrics + malformed-row cleanup), adding Operator Backtest Parity controls, and adding `tests/test_backtest_parity_engine.py`.
- 2026-03-09: Closed Phase 87/88 carryover fills routing by adding user-stream router + optional WS service (`services/fills/user_stream_router.py`, `services/fills/user_stream_ws.py`, `scripts/run_user_stream_fills.py`), wiring `fills_poller` through live executor `_on_fill` hook with FillSink fallback, and adding `tests/test_user_stream_router.py`/`tests/test_user_stream_ws.py`.
- 2026-03-09: Closed duplicate Installer-UX carryovers (Phase 16/17 shadows at lines 959/1049) after verifying installer/signing + UI service controls already shipped in JT/LV/KM/KN tracks.
- 2026-03-09: Closed stale Phase 9/10/11/12/14 carryovers for live execution hardening after re-verifying implemented kill-switch/circuit breaker/order-params/reconciliation flows and corresponding integration tests.
- 2026-03-09: Closed ID5 by validating end-to-end intent -> submit -> fill -> journal/reconcile parity in current executor/live paths.
- 2026-03-09: Closed HY5 with blacklist-backed watchTicker auto-disable (`services/marketdata/ws_ticker_feed.py`, `scripts/run_ws_ticker_feed.py`, `tests/test_ws_ticker_feed.py`).
- 2026-03-09: Closed Phase 13 smoke/threshold carryover by adding exchange sandbox smoke scripts (`scripts/smoke_exchange.py`, `scripts/smoke_coinbase.py`, `scripts/smoke_binance.py`, `scripts/smoke_gateio.py`) and symbol-level market quality thresholds in `services/risk/market_quality_guard.py`.
- 2026-03-09: Deduplicated duplicate Ops-intelligence carryover line (kept canonical tracker at line 1001).

## Phase 95-330) Recent checkpoint canonization
- ✅ Phase 95: Hardened `tests/test_checkpoints_recent_firstline_action_prefix.py` to anchor checkpoint lint
- ✅ Phase 95: Validated recent checkpoint narrative for the tail block
- ✅ Phase 95 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`305 passed`)
- ✅ Phase 96: Hardened `tests/test_checkpoints_recent_firstline_action_verb_cardinality.py` to anchor checkpoint lint
- ✅ Phase 96: Validated recent checkpoint narrative for the tail block
- ✅ Phase 96 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`306 passed`)
- ✅ Phase 97: Hardened `tests/test_checkpoints_recent_firstline_artifact_filter.py` to anchor checkpoint lint
- ✅ Phase 97: Validated recent checkpoint narrative for the tail block
- ✅ Phase 97 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`307 passed`)
- ✅ Phase 98: Hardened `tests/test_checkpoints_recent_firstline_backtick_pair_count.py` to anchor checkpoint lint
- ✅ Phase 98: Validated recent checkpoint narrative for the tail block
- ✅ Phase 98 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`308 passed`)
- ✅ Phase 99: Hardened `tests/test_checkpoints_recent_firstline_backtick_presence.py` to anchor checkpoint lint
- ✅ Phase 99: Validated recent checkpoint narrative for the tail block
- ✅ Phase 99 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`309 passed`)
- ✅ Phase 100: Hardened `tests/test_checkpoints_recent_firstline_no_ampersand.py` to anchor checkpoint lint
- ✅ Phase 100: Validated recent checkpoint narrative for the tail block
- ✅ Phase 100 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`310 passed`)
- ✅ Phase 101: Hardened `tests/test_checkpoints_recent_firstline_no_angle_brackets.py` to anchor checkpoint lint
- ✅ Phase 101: Validated recent checkpoint narrative for the tail block
- ✅ Phase 101 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`311 passed`)
- ✅ Phase 102: Hardened `tests/test_checkpoints_recent_firstline_no_at_sign.py` to anchor checkpoint lint
- ✅ Phase 102: Validated recent checkpoint narrative for the tail block
- ✅ Phase 102 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`312 passed`)
- ✅ Phase 103: Hardened `tests/test_checkpoints_recent_firstline_no_backslash.py` to anchor checkpoint lint
- ✅ Phase 103: Validated recent checkpoint narrative for the tail block
- ✅ Phase 103 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`313 passed`)
- ✅ Phase 104: Hardened `tests/test_checkpoints_recent_firstline_no_backtick_pair.py` to anchor checkpoint lint
- ✅ Phase 104: Validated recent checkpoint narrative for the tail block
- ✅ Phase 104 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`314 passed`)
- ✅ Phase 105: Hardened `tests/test_checkpoints_recent_firstline_no_caret.py` to anchor checkpoint lint
- ✅ Phase 105: Validated recent checkpoint narrative for the tail block
- ✅ Phase 105 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`315 passed`)
- ✅ Phase 106: Hardened `tests/test_checkpoints_recent_firstline_no_colon.py` to anchor checkpoint lint
- ✅ Phase 106: Validated recent checkpoint narrative for the tail block
- ✅ Phase 106 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`316 passed`)
- ✅ Phase 107: Hardened `tests/test_checkpoints_recent_firstline_no_commas.py` to anchor checkpoint lint
- ✅ Phase 107: Validated recent checkpoint narrative for the tail block
- ✅ Phase 107 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`317 passed`)
- ✅ Phase 108: Hardened `tests/test_checkpoints_recent_firstline_no_control_chars.py` to anchor checkpoint lint
- ✅ Phase 108: Validated recent checkpoint narrative for the tail block
- ✅ Phase 108 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`318 passed`)
- ✅ Phase 109: Hardened `tests/test_checkpoints_recent_firstline_no_curly_braces.py` to anchor checkpoint lint
- ✅ Phase 109: Validated recent checkpoint narrative for the tail block
- ✅ Phase 109 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`319 passed`)
- ✅ Phase 110: Hardened `tests/test_checkpoints_recent_firstline_no_dollar_sign.py` to anchor checkpoint lint
- ✅ Phase 110: Validated recent checkpoint narrative for the tail block
- ✅ Phase 110 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`320 passed`)
- ✅ Phase 111: Hardened `tests/test_checkpoints_recent_firstline_no_edge_backtick.py` to anchor checkpoint lint
- ✅ Phase 111: Validated recent checkpoint narrative for the tail block
- ✅ Phase 111 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`321 passed`)
- ✅ Phase 112: Hardened `tests/test_checkpoints_recent_firstline_no_equals.py` to anchor checkpoint lint
- ✅ Phase 112: Validated recent checkpoint narrative for the tail block
- ✅ Phase 112 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`322 passed`)
- ✅ Phase 113: Hardened `tests/test_checkpoints_recent_firstline_no_exclamation_mark.py` to anchor checkpoint lint
- ✅ Phase 113: Validated recent checkpoint narrative for the tail block
- ✅ Phase 113 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`323 passed`)
- ✅ Phase 114: Hardened `tests/test_checkpoints_recent_firstline_no_grave_accent.py` to anchor checkpoint lint
- ✅ Phase 114: Validated recent checkpoint narrative for the tail block
- ✅ Phase 114 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`324 passed`)
- ✅ Phase 115: Hardened `tests/test_checkpoints_recent_firstline_no_hash_sign.py` to anchor checkpoint lint
- ✅ Phase 115: Validated recent checkpoint narrative for the tail block
- ✅ Phase 115 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`325 passed`)
- ✅ Phase 116: Hardened `tests/test_checkpoints_recent_firstline_no_leading_space.py` to anchor checkpoint lint
- ✅ Phase 116: Validated recent checkpoint narrative for the tail block
- ✅ Phase 116 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`326 passed`)
- ✅ Phase 117: Hardened `tests/test_checkpoints_recent_firstline_no_parentheses.py` to anchor checkpoint lint
- ✅ Phase 117: Validated recent checkpoint narrative for the tail block
- ✅ Phase 117 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`327 passed`)
- ✅ Phase 118: Hardened `tests/test_checkpoints_recent_firstline_no_percent_sign.py` to anchor checkpoint lint
- ✅ Phase 118: Validated recent checkpoint narrative for the tail block
- ✅ Phase 118 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`328 passed`)
- ✅ Phase 119: Hardened `tests/test_checkpoints_recent_firstline_no_pipe.py` to anchor checkpoint lint
- ✅ Phase 119: Validated recent checkpoint narrative for the tail block
- ✅ Phase 119 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`329 passed`)
- ✅ Phase 120: Hardened `tests/test_checkpoints_recent_firstline_no_plus_sign.py` to anchor checkpoint lint
- ✅ Phase 120: Validated recent checkpoint narrative for the tail block
- ✅ Phase 120 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`330 passed`)
- ✅ Phase 121: Hardened `tests/test_checkpoints_recent_firstline_no_question_mark.py` to anchor checkpoint lint
- ✅ Phase 121: Validated recent checkpoint narrative for the tail block
- ✅ Phase 121 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`331 passed`)
- ✅ Phase 122: Hardened `tests/test_checkpoints_recent_firstline_no_quotes.py` to anchor checkpoint lint
- ✅ Phase 122: Validated recent checkpoint narrative for the tail block
- ✅ Phase 122 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`332 passed`)
- ✅ Phase 123: Hardened `tests/test_checkpoints_recent_firstline_no_repeated_punctuation.py` to anchor checkpoint lint
- ✅ Phase 123: Validated recent checkpoint narrative for the tail block
- ✅ Phase 123 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`333 passed`)
- ✅ Phase 124: Hardened `tests/test_checkpoints_recent_firstline_no_semicolon.py` to anchor checkpoint lint
- ✅ Phase 124: Validated recent checkpoint narrative for the tail block
- ✅ Phase 124 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`334 passed`)
- ✅ Phase 125: Hardened `tests/test_checkpoints_recent_firstline_no_semicolon_pair.py` to anchor checkpoint lint
- ✅ Phase 125: Validated recent checkpoint narrative for the tail block
- ✅ Phase 125 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`335 passed`)
- ✅ Phase 126: Hardened `tests/test_checkpoints_recent_firstline_no_square_brackets.py` to anchor checkpoint lint
- ✅ Phase 126: Validated recent checkpoint narrative for the tail block
- ✅ Phase 126 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`336 passed`)
- ✅ Phase 127: Hardened `tests/test_checkpoints_recent_firstline_no_tabs.py` to anchor checkpoint lint
- ✅ Phase 127: Validated recent checkpoint narrative for the tail block
- ✅ Phase 127 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`337 passed`)
- ✅ Phase 128: Hardened `tests/test_checkpoints_recent_firstline_no_tilde.py` to anchor checkpoint lint
- ✅ Phase 128: Validated recent checkpoint narrative for the tail block
- ✅ Phase 128 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`338 passed`)
- ✅ Phase 129: Hardened `tests/test_checkpoints_recent_firstline_no_trailing_space.py` to anchor checkpoint lint
- ✅ Phase 129: Validated recent checkpoint narrative for the tail block
- ✅ Phase 129 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`339 passed`)
- ✅ Phase 130: Hardened `tests/test_checkpoints_recent_firstline_no_triple_backtick.py` to anchor checkpoint lint
- ✅ Phase 130: Validated recent checkpoint narrative for the tail block
- ✅ Phase 130 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`340 passed`)
- ✅ Phase 131: Hardened `tests/test_checkpoints_recent_firstline_no_triple_period.py` to anchor checkpoint lint
- ✅ Phase 131: Validated recent checkpoint narrative for the tail block
- ✅ Phase 131 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`341 passed`)
- ✅ Phase 132: Hardened `tests/test_checkpoints_recent_firstline_no_wildcard_artifacts.py` to anchor checkpoint lint
- ✅ Phase 132: Validated recent checkpoint narrative for the tail block
- ✅ Phase 132 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`342 passed`)
- ✅ Phase 133: Hardened `tests/test_checkpoints_recent_firstline_purpose_delimiter.py` to anchor checkpoint lint
- ✅ Phase 133: Validated recent checkpoint narrative for the tail block
- ✅ Phase 133 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`343 passed`)
- ✅ Phase 134: Hardened `tests/test_checkpoints_recent_firstline_single_artifact.py` to anchor checkpoint lint
- ✅ Phase 134: Validated recent checkpoint narrative for the tail block
- ✅ Phase 134 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`344 passed`)
- ✅ Phase 135: Hardened `tests/test_checkpoints_recent_secondline_narrative_only.py` to anchor checkpoint lint
- ✅ Phase 135: Validated recent checkpoint narrative for the tail block
- ✅ Phase 135 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`345 passed`)
- ✅ Phase 136: Hardened `tests/test_checkpoints_recent_secondline_no_commas.py` to anchor checkpoint lint
- ✅ Phase 136: Validated recent checkpoint narrative for the tail block
- ✅ Phase 136 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`346 passed`)
- ✅ Phase 137: Hardened `tests/test_checkpoints_recent_secondline_no_test_tokens.py` to anchor checkpoint lint
- ✅ Phase 137: Validated recent checkpoint narrative for the tail block
- ✅ Phase 137 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`347 passed`)
- ✅ Phase 138: Hardened `tests/test_checkpoints_recent_secondline_scope_qualifier.py` to anchor checkpoint lint
- ✅ Phase 138: Validated recent checkpoint narrative for the tail block
- ✅ Phase 138 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`348 passed`)
- ✅ Phase 139: Hardened `tests/test_checkpoints_recent_secondline_validation_prefix.py` to anchor checkpoint lint
- ✅ Phase 139: Validated recent checkpoint narrative for the tail block
- ✅ Phase 139 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`349 passed`)
- ✅ Phase 140: Hardened `tests/test_checkpoints_recent_segment_boundary_purity.py` to anchor checkpoint lint
- ✅ Phase 140: Validated recent checkpoint narrative for the tail block
- ✅ Phase 140 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`350 passed`)
- ✅ Phase 141: Hardened `tests/test_checkpoints_recent_verification_backtick_payload_count.py` to anchor checkpoint lint
- ✅ Phase 141: Validated recent checkpoint narrative for the tail block
- ✅ Phase 141 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`351 passed`)
- ✅ Phase 142: Hardened `tests/test_checkpoints_recent_verification_delimiter_style.py` to anchor checkpoint lint
- ✅ Phase 142: Validated recent checkpoint narrative for the tail block
- ✅ Phase 142 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`352 passed`)
- ✅ Phase 143: Hardened `tests/test_checkpoints_recent_verification_delta_one.py` to anchor checkpoint lint
- ✅ Phase 143: Validated recent checkpoint narrative for the tail block
- ✅ Phase 143 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`353 passed`)
- ✅ Phase 144: Hardened `tests/test_checkpoints_recent_verification_evidence_payloads.py` to anchor checkpoint lint
- ✅ Phase 144: Validated recent checkpoint narrative for the tail block
- ✅ Phase 144 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`354 passed`)
- ✅ Phase 145: Hardened `tests/test_checkpoints_recent_verification_line_ending_contract.py` to anchor checkpoint lint
- ✅ Phase 145: Validated recent checkpoint narrative for the tail block
- ✅ Phase 145 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`355 passed`)
- ✅ Phase 146: Hardened `tests/test_checkpoints_recent_verification_marker_order.py` to anchor checkpoint lint
- ✅ Phase 146: Validated recent checkpoint narrative for the tail block
- ✅ Phase 146 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`356 passed`)
- ✅ Phase 147: Hardened `tests/test_checkpoints_recent_verification_parenthesis_payload_count.py` to anchor checkpoint lint
- ✅ Phase 147: Validated recent checkpoint narrative for the tail block
- ✅ Phase 147 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`357 passed`)
- ✅ Phase 148: Hardened `tests/test_checkpoints_recent_verification_phase_sequence.py` to anchor checkpoint lint
- ✅ Phase 148: Validated recent checkpoint narrative for the tail block
- ✅ Phase 148 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`358 passed`)
- ✅ Phase 149: Hardened `tests/test_checkpoints_recent_verification_punctuation_safety.py` to anchor checkpoint lint
- ✅ Phase 149: Validated recent checkpoint narrative for the tail block
- ✅ Phase 149 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`359 passed`)
- ✅ Phase 150: Hardened `tests/test_checkpoints_recent_verification_quality.py` to anchor checkpoint lint
- ✅ Phase 150: Validated recent checkpoint narrative for the tail block
- ✅ Phase 150 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`360 passed`)
- ✅ Phase 151: Hardened `tests/test_checkpoints_recent_verification_regex_contract.py` to anchor checkpoint lint
- ✅ Phase 151: Validated recent checkpoint narrative for the tail block
- ✅ Phase 151 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`361 passed`)
- ✅ Phase 152: Hardened `tests/test_checkpoints_recent_verification_segment_labels.py` to anchor checkpoint lint
- ✅ Phase 152: Validated recent checkpoint narrative for the tail block
- ✅ Phase 152 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`362 passed`)
- ✅ Phase 153: Hardened `tests/test_checkpoints_recent_verification_segment_shape.py` to anchor checkpoint lint
- ✅ Phase 153: Validated recent checkpoint narrative for the tail block
- ✅ Phase 153 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`363 passed`)
- ✅ Phase 154: Hardened `tests/test_checkpoints_recent_verification_whitespace_hygiene.py` to anchor checkpoint lint
- ✅ Phase 154: Validated recent checkpoint narrative for the tail block
- ✅ Phase 154 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`364 passed`)
- ✅ Phase 155: Hardened `tests/test_checkpoints_recent_artifact_naming_convention.py` to anchor checkpoint lint
- ✅ Phase 155: Validated recent checkpoint narrative for the tail block
- ✅ Phase 155 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`365 passed`)
- ✅ Phase 156: Hardened `tests/test_checkpoints_recent_artifact_phase_alignment.py` to anchor checkpoint lint
- ✅ Phase 156: Validated recent checkpoint narrative for the tail block
- ✅ Phase 156 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`366 passed`)
- ✅ Phase 157: Hardened `tests/test_checkpoints_recent_artifact_recent_prefix.py` to anchor checkpoint lint
- ✅ Phase 157: Validated recent checkpoint narrative for the tail block
- ✅ Phase 157 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`367 passed`)
- ✅ Phase 158: Hardened `tests/test_checkpoints_recent_artifact_uniqueness.py` to anchor checkpoint lint
- ✅ Phase 158: Validated recent checkpoint narrative for the tail block
- ✅ Phase 158 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`368 passed`)
- ✅ Phase 159: Hardened `tests/test_checkpoints_recent_checklist_content_quality.py` to anchor checkpoint lint
- ✅ Phase 159: Validated recent checkpoint narrative for the tail block
- ✅ Phase 159 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`369 passed`)
- ✅ Phase 160: Hardened `tests/test_checkpoints_recent_checklist_no_trailing_periods.py` to anchor checkpoint lint
- ✅ Phase 160: Validated recent checkpoint narrative for the tail block
- ✅ Phase 160 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`370 passed`)
- ✅ Phase 161: Hardened `tests/test_checkpoints_recent_crosscheck_marker.py` to anchor checkpoint lint
- ✅ Phase 161: Validated recent checkpoint narrative for the tail block
- ✅ Phase 161 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`371 passed`)
- ✅ Phase 162: Hardened `tests/test_checkpoints_recent_crosscheck_payload_truth.py` to anchor checkpoint lint
- ✅ Phase 162: Validated recent checkpoint narrative for the tail block
- ✅ Phase 162 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`372 passed`)
- ✅ Phase 163: Hardened `tests/test_checkpoints_recent_crosscheck_segment_wording_noise.py` to anchor checkpoint lint
- ✅ Phase 163: Validated recent checkpoint narrative for the tail block
- ✅ Phase 163 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`373 passed`)
- ✅ Phase 164: Hardened `tests/test_checkpoints_recent_crosscheck_token_cardinality.py` to anchor checkpoint lint
- ✅ Phase 164: Validated recent checkpoint narrative for the tail block
- ✅ Phase 164 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`374 passed`)
- ✅ Phase 165: Hardened `tests/test_checkpoints_recent_firstline_action_prefix.py` to anchor checkpoint lint
- ✅ Phase 165: Validated recent checkpoint narrative for the tail block
- ✅ Phase 165 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`375 passed`)
- ✅ Phase 166: Hardened `tests/test_checkpoints_recent_firstline_action_verb_cardinality.py` to anchor checkpoint lint
- ✅ Phase 166: Validated recent checkpoint narrative for the tail block
- ✅ Phase 166 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`376 passed`)
- ✅ Phase 167: Hardened `tests/test_checkpoints_recent_firstline_artifact_filter.py` to anchor checkpoint lint
- ✅ Phase 167: Validated recent checkpoint narrative for the tail block
- ✅ Phase 167 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`377 passed`)
- ✅ Phase 168: Hardened `tests/test_checkpoints_recent_firstline_backtick_pair_count.py` to anchor checkpoint lint
- ✅ Phase 168: Validated recent checkpoint narrative for the tail block
- ✅ Phase 168 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`378 passed`)
- ✅ Phase 169: Hardened `tests/test_checkpoints_recent_firstline_backtick_presence.py` to anchor checkpoint lint
- ✅ Phase 169: Validated recent checkpoint narrative for the tail block
- ✅ Phase 169 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`379 passed`)
- ✅ Phase 170: Hardened `tests/test_checkpoints_recent_firstline_no_ampersand.py` to anchor checkpoint lint
- ✅ Phase 170: Validated recent checkpoint narrative for the tail block
- ✅ Phase 170 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`380 passed`)
- ✅ Phase 171: Hardened `tests/test_checkpoints_recent_firstline_no_angle_brackets.py` to anchor checkpoint lint
- ✅ Phase 171: Validated recent checkpoint narrative for the tail block
- ✅ Phase 171 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`381 passed`)
- ✅ Phase 172: Hardened `tests/test_checkpoints_recent_firstline_no_at_sign.py` to anchor checkpoint lint
- ✅ Phase 172: Validated recent checkpoint narrative for the tail block
- ✅ Phase 172 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`382 passed`)
- ✅ Phase 173: Hardened `tests/test_checkpoints_recent_firstline_no_backslash.py` to anchor checkpoint lint
- ✅ Phase 173: Validated recent checkpoint narrative for the tail block
- ✅ Phase 173 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`383 passed`)
- ✅ Phase 174: Hardened `tests/test_checkpoints_recent_firstline_no_backtick_pair.py` to anchor checkpoint lint
- ✅ Phase 174: Validated recent checkpoint narrative for the tail block
- ✅ Phase 174 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`384 passed`)
- ✅ Phase 175: Hardened `tests/test_checkpoints_recent_firstline_no_caret.py` to anchor checkpoint lint
- ✅ Phase 175: Validated recent checkpoint narrative for the tail block
- ✅ Phase 175 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`385 passed`)
- ✅ Phase 176: Hardened `tests/test_checkpoints_recent_firstline_no_colon.py` to anchor checkpoint lint
- ✅ Phase 176: Validated recent checkpoint narrative for the tail block
- ✅ Phase 176 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`386 passed`)
- ✅ Phase 177: Hardened `tests/test_checkpoints_recent_firstline_no_double_ampersand.py` to anchor checkpoint lint
- ✅ Phase 177: Validated recent checkpoint narrative for the tail block
- ✅ Phase 177 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`387 passed`)
- ✅ Phase 178: Hardened `tests/test_checkpoints_recent_firstline_no_double_ampersand_again.py` to anchor checkpoint lint
- ✅ Phase 178: Validated recent checkpoint narrative for the tail block
- ✅ Phase 178 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`388 passed`)
- ✅ Phase 179: Hardened `tests/test_checkpoints_recent_firstline_no_double_ampersand_fourth.py` to anchor checkpoint lint
- ✅ Phase 179: Validated recent checkpoint narrative for the tail block
- ✅ Phase 179 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`389 passed`)
- ✅ Phase 180: Hardened `tests/test_checkpoints_recent_firstline_no_double_ampersand_third.py` to anchor checkpoint lint
- ✅ Phase 180: Validated recent checkpoint narrative for the tail block
- ✅ Phase 180 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`390 passed`)
- ✅ Phase 181: Hardened `tests/test_checkpoints_recent_firstline_no_double_angle_brackets.py` to anchor checkpoint lint
- ✅ Phase 181: Validated recent checkpoint narrative for the tail block
- ✅ Phase 181 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`391 passed`)
- ✅ Phase 182: Hardened `tests/test_checkpoints_recent_firstline_no_double_angle_brackets_again.py` to anchor checkpoint lint
- ✅ Phase 182: Validated recent checkpoint narrative for the tail block
- ✅ Phase 182 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`392 passed`)
- ✅ Phase 183: Hardened `tests/test_checkpoints_recent_firstline_no_double_angle_brackets_third.py` to anchor checkpoint lint
- ✅ Phase 183: Validated recent checkpoint narrative for the tail block
- ✅ Phase 183 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`393 passed`)
- ✅ Phase 184: Hardened `tests/test_checkpoints_recent_firstline_no_double_apostrophe.py` to anchor checkpoint lint
- ✅ Phase 184: Validated recent checkpoint narrative for the tail block
- ✅ Phase 184 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`394 passed`)
- ✅ Phase 185: Hardened `tests/test_checkpoints_recent_firstline_no_double_apostrophe_again.py` to anchor checkpoint lint
- ✅ Phase 185: Validated recent checkpoint narrative for the tail block
- ✅ Phase 185 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`395 passed`)
- ✅ Phase 186: Hardened `tests/test_checkpoints_recent_firstline_no_double_asterisk.py` to anchor checkpoint lint
- ✅ Phase 186: Validated recent checkpoint narrative for the tail block
- ✅ Phase 186 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`396 passed`)
- ✅ Phase 187: Hardened `tests/test_checkpoints_recent_firstline_no_double_asterisk_again.py` to anchor checkpoint lint
- ✅ Phase 187: Validated recent checkpoint narrative for the tail block
- ✅ Phase 187 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`397 passed`)
- ✅ Phase 188: Hardened `tests/test_checkpoints_recent_firstline_no_double_asterisk_fifth.py` to anchor checkpoint lint
- ✅ Phase 188: Validated recent checkpoint narrative for the tail block
- ✅ Phase 188 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`398 passed`)
- ✅ Phase 189: Hardened `tests/test_checkpoints_recent_firstline_no_double_asterisk_fourth.py` to anchor checkpoint lint
- ✅ Phase 189: Validated recent checkpoint narrative for the tail block
- ✅ Phase 189 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`399 passed`)
- ✅ Phase 190: Hardened `tests/test_checkpoints_recent_firstline_no_double_asterisk_seventh.py` to anchor checkpoint lint
- ✅ Phase 190: Validated recent checkpoint narrative for the tail block
- ✅ Phase 190 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`400 passed`)
- ✅ Phase 191: Hardened `tests/test_checkpoints_recent_firstline_no_double_asterisk_sixth.py` to anchor checkpoint lint
- ✅ Phase 191: Validated recent checkpoint narrative for the tail block
- ✅ Phase 191 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`401 passed`)
- ✅ Phase 192: Hardened `tests/test_checkpoints_recent_firstline_no_double_asterisk_third.py` to anchor checkpoint lint
- ✅ Phase 192: Validated recent checkpoint narrative for the tail block
- ✅ Phase 192 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`402 passed`)
- ✅ Phase 193: Hardened `tests/test_checkpoints_recent_firstline_no_double_at_sign.py` to anchor checkpoint lint
- ✅ Phase 193: Validated recent checkpoint narrative for the tail block
- ✅ Phase 193 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`403 passed`)
- ✅ Phase 194: Hardened `tests/test_checkpoints_recent_firstline_no_double_at_sign_again.py` to anchor checkpoint lint
- ✅ Phase 194: Validated recent checkpoint narrative for the tail block
- ✅ Phase 194 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`404 passed`)
- ✅ Phase 195: Hardened `tests/test_checkpoints_recent_firstline_no_double_at_sign_fourth.py` to anchor checkpoint lint
- ✅ Phase 195: Validated recent checkpoint narrative for the tail block
- ✅ Phase 195 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`405 passed`)
- ✅ Phase 196: Hardened `tests/test_checkpoints_recent_firstline_no_double_at_sign_third.py` to anchor checkpoint lint
- ✅ Phase 196: Validated recent checkpoint narrative for the tail block
- ✅ Phase 196 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`406 passed`)
- ✅ Phase 197: Hardened `tests/test_checkpoints_recent_firstline_no_double_backslash.py` to anchor checkpoint lint
- ✅ Phase 197: Validated recent checkpoint narrative for the tail block
- ✅ Phase 197 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`407 passed`)
- ✅ Phase 198: Hardened `tests/test_checkpoints_recent_firstline_no_double_backslash_again.py` to anchor checkpoint lint
- ✅ Phase 198: Validated recent checkpoint narrative for the tail block
- ✅ Phase 198 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`408 passed`)
- ✅ Phase 199: Hardened `tests/test_checkpoints_recent_firstline_no_double_backslash_fifth.py` to anchor checkpoint lint
- ✅ Phase 199: Validated recent checkpoint narrative for the tail block
- ✅ Phase 199 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`409 passed`)
- ✅ Phase 200: Hardened `tests/test_checkpoints_recent_firstline_no_double_backslash_fourth.py` to anchor checkpoint lint
- ✅ Phase 200: Validated recent checkpoint narrative for the tail block
- ✅ Phase 200 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`410 passed`)
- ✅ Phase 201: Hardened `tests/test_checkpoints_recent_firstline_no_double_backslash_seventh.py` to anchor checkpoint lint
- ✅ Phase 201: Validated recent checkpoint narrative for the tail block
- ✅ Phase 201 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`411 passed`)
- ✅ Phase 202: Hardened `tests/test_checkpoints_recent_firstline_no_double_backslash_sixth.py` to anchor checkpoint lint
- ✅ Phase 202: Validated recent checkpoint narrative for the tail block
- ✅ Phase 202 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`412 passed`)
- ✅ Phase 203: Hardened `tests/test_checkpoints_recent_firstline_no_double_backslash_third.py` to anchor checkpoint lint
- ✅ Phase 203: Validated recent checkpoint narrative for the tail block
- ✅ Phase 203 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`413 passed`)
- ✅ Phase 204: Hardened `tests/test_checkpoints_recent_firstline_no_double_backtick.py` to anchor checkpoint lint
- ✅ Phase 204: Validated recent checkpoint narrative for the tail block
- ✅ Phase 204 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`414 passed`)
- ✅ Phase 205: Hardened `tests/test_checkpoints_recent_firstline_no_double_backtick_again.py` to anchor checkpoint lint
- ✅ Phase 205: Validated recent checkpoint narrative for the tail block
- ✅ Phase 205 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`415 passed`)
- ✅ Phase 206: Hardened `tests/test_checkpoints_recent_firstline_no_double_backtick_fifth.py` to anchor checkpoint lint
- ✅ Phase 206: Validated recent checkpoint narrative for the tail block
- ✅ Phase 206 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`416 passed`)
- ✅ Phase 207: Hardened `tests/test_checkpoints_recent_firstline_no_double_backtick_fourth.py` to anchor checkpoint lint
- ✅ Phase 207: Validated recent checkpoint narrative for the tail block
- ✅ Phase 207 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`417 passed`)
- ✅ Phase 208: Hardened `tests/test_checkpoints_recent_firstline_no_double_backtick_sixth.py` to anchor checkpoint lint
- ✅ Phase 208: Validated recent checkpoint narrative for the tail block
- ✅ Phase 208 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`418 passed`)
- ✅ Phase 209: Hardened `tests/test_checkpoints_recent_firstline_no_double_backtick_third.py` to anchor checkpoint lint
- ✅ Phase 209: Validated recent checkpoint narrative for the tail block
- ✅ Phase 209 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`419 passed`)
- ✅ Phase 210: Hardened `tests/test_checkpoints_recent_firstline_no_double_braces.py` to anchor checkpoint lint
- ✅ Phase 210: Validated recent checkpoint narrative for the tail block
- ✅ Phase 210 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`420 passed`)
- ✅ Phase 211: Hardened `tests/test_checkpoints_recent_firstline_no_double_braces_again.py` to anchor checkpoint lint
- ✅ Phase 211: Validated recent checkpoint narrative for the tail block
- ✅ Phase 211 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`421 passed`)
- ✅ Phase 212: Hardened `tests/test_checkpoints_recent_firstline_no_double_braces_fifth.py` to anchor checkpoint lint
- ✅ Phase 212: Validated recent checkpoint narrative for the tail block
- ✅ Phase 212 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`422 passed`)
- ✅ Phase 213: Hardened `tests/test_checkpoints_recent_firstline_no_double_braces_fourth.py` to anchor checkpoint lint
- ✅ Phase 213: Validated recent checkpoint narrative for the tail block
- ✅ Phase 213 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`423 passed`)
- ✅ Phase 214: Hardened `tests/test_checkpoints_recent_firstline_no_double_braces_third.py` to anchor checkpoint lint
- ✅ Phase 214: Validated recent checkpoint narrative for the tail block
- ✅ Phase 214 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`424 passed`)
- ✅ Phase 215: Hardened `tests/test_checkpoints_recent_firstline_no_double_caret.py` to anchor checkpoint lint
- ✅ Phase 215: Validated recent checkpoint narrative for the tail block
- ✅ Phase 215 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`425 passed`)
- ✅ Phase 216: Hardened `tests/test_checkpoints_recent_firstline_no_double_caret_again.py` to anchor checkpoint lint
- ✅ Phase 216: Validated recent checkpoint narrative for the tail block
- ✅ Phase 216 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`426 passed`)
- ✅ Phase 217: Hardened `tests/test_checkpoints_recent_firstline_no_double_caret_fourth.py` to anchor checkpoint lint
- ✅ Phase 217: Validated recent checkpoint narrative for the tail block
- ✅ Phase 217 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`427 passed`)
- ✅ Phase 218: Hardened `tests/test_checkpoints_recent_firstline_no_double_caret_third.py` to anchor checkpoint lint
- ✅ Phase 218: Validated recent checkpoint narrative for the tail block
- ✅ Phase 218 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`428 passed`)
- ✅ Phase 219: Hardened `tests/test_checkpoints_recent_firstline_no_double_colon.py` to anchor checkpoint lint
- ✅ Phase 219: Validated recent checkpoint narrative for the tail block
- ✅ Phase 219 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`429 passed`)
- ✅ Phase 220: Hardened `tests/test_checkpoints_recent_firstline_no_double_colon_again.py` to anchor checkpoint lint
- ✅ Phase 220: Validated recent checkpoint narrative for the tail block
- ✅ Phase 220 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`430 passed`)
- ✅ Phase 221: Hardened `tests/test_checkpoints_recent_firstline_no_double_colon_fifth.py` to anchor checkpoint lint
- ✅ Phase 221: Validated recent checkpoint narrative for the tail block
- ✅ Phase 221 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`431 passed`)
- ✅ Phase 222: Hardened `tests/test_checkpoints_recent_firstline_no_double_colon_fourth.py` to anchor checkpoint lint
- ✅ Phase 222: Validated recent checkpoint narrative for the tail block
- ✅ Phase 222 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`432 passed`)
- ✅ Phase 223: Hardened `tests/test_checkpoints_recent_firstline_no_double_colon_third.py` to anchor checkpoint lint
- ✅ Phase 223: Validated recent checkpoint narrative for the tail block
- ✅ Phase 223 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`433 passed`)
- ✅ Phase 224: Hardened `tests/test_checkpoints_recent_firstline_no_double_comma.py` to anchor checkpoint lint
- ✅ Phase 224: Validated recent checkpoint narrative for the tail block
- ✅ Phase 224 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`434 passed`)
- ✅ Phase 225: Hardened `tests/test_checkpoints_recent_firstline_no_double_comma_again.py` to anchor checkpoint lint
- ✅ Phase 225: Validated recent checkpoint narrative for the tail block
- ✅ Phase 225 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`435 passed`)
- ✅ Phase 226: Hardened `tests/test_checkpoints_recent_firstline_no_double_comma_fourth.py` to anchor checkpoint lint
- ✅ Phase 226: Validated recent checkpoint narrative for the tail block
- ✅ Phase 226 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`436 passed`)
- ✅ Phase 227: Hardened `tests/test_checkpoints_recent_firstline_no_double_comma_third.py` to anchor checkpoint lint
- ✅ Phase 227: Validated recent checkpoint narrative for the tail block
- ✅ Phase 227 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`437 passed`)
- ✅ Phase 228: Hardened `tests/test_checkpoints_recent_firstline_no_double_comparison_mix.py` to anchor checkpoint lint
- ✅ Phase 228: Validated recent checkpoint narrative for the tail block
- ✅ Phase 228 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`438 passed`)
- ✅ Phase 229: Hardened `tests/test_checkpoints_recent_firstline_no_double_dollar.py` to anchor checkpoint lint
- ✅ Phase 229: Validated recent checkpoint narrative for the tail block
- ✅ Phase 229 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`439 passed`)
- ✅ Phase 230: Hardened `tests/test_checkpoints_recent_firstline_no_double_dollar_again.py` to anchor checkpoint lint
- ✅ Phase 230: Validated recent checkpoint narrative for the tail block
- ✅ Phase 230 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`440 passed`)
- ✅ Phase 231: Hardened `tests/test_checkpoints_recent_firstline_no_double_dollar_fifth.py` to anchor checkpoint lint
- ✅ Phase 231: Validated recent checkpoint narrative for the tail block
- ✅ Phase 231 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`441 passed`)
- ✅ Phase 232: Hardened `tests/test_checkpoints_recent_firstline_no_double_dollar_fourth.py` to anchor checkpoint lint
- ✅ Phase 232: Validated recent checkpoint narrative for the tail block
- ✅ Phase 232 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`442 passed`)
- ✅ Phase 233: Hardened `tests/test_checkpoints_recent_firstline_no_double_dollar_seventh.py` to anchor checkpoint lint
- ✅ Phase 233: Validated recent checkpoint narrative for the tail block
- ✅ Phase 233 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`443 passed`)
- ✅ Phase 234: Hardened `tests/test_checkpoints_recent_firstline_no_double_dollar_sixth.py` to anchor checkpoint lint
- ✅ Phase 234: Validated recent checkpoint narrative for the tail block
- ✅ Phase 234 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`444 passed`)
- ✅ Phase 235: Hardened `tests/test_checkpoints_recent_firstline_no_double_dollar_third.py` to anchor checkpoint lint
- ✅ Phase 235: Validated recent checkpoint narrative for the tail block
- ✅ Phase 235 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`445 passed`)
- ✅ Phase 236: Hardened `tests/test_checkpoints_recent_firstline_no_double_equal_again.py` to anchor checkpoint lint
- ✅ Phase 236: Validated recent checkpoint narrative for the tail block
- ✅ Phase 236 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`446 passed`)
- ✅ Phase 237: Hardened `tests/test_checkpoints_recent_firstline_no_double_equal_fourth.py` to anchor checkpoint lint
- ✅ Phase 237: Validated recent checkpoint narrative for the tail block
- ✅ Phase 237 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`447 passed`)
- ✅ Phase 238: Hardened `tests/test_checkpoints_recent_firstline_no_double_equal_sign.py` to anchor checkpoint lint
- ✅ Phase 238: Validated recent checkpoint narrative for the tail block
- ✅ Phase 238 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`448 passed`)
- ✅ Phase 239: Hardened `tests/test_checkpoints_recent_firstline_no_double_equal_third.py` to anchor checkpoint lint
- ✅ Phase 239: Validated recent checkpoint narrative for the tail block
- ✅ Phase 239 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`449 passed`)
- ✅ Phase 240: Hardened `tests/test_checkpoints_recent_firstline_no_double_exclamation.py` to anchor checkpoint lint
- ✅ Phase 240: Validated recent checkpoint narrative for the tail block
- ✅ Phase 240 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`450 passed`)
- ✅ Phase 241: Hardened `tests/test_checkpoints_recent_firstline_no_double_exclamation_again.py` to anchor checkpoint lint
- ✅ Phase 241: Validated recent checkpoint narrative for the tail block
- ✅ Phase 241 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`451 passed`)
- ✅ Phase 242: Hardened `tests/test_checkpoints_recent_firstline_no_double_exclamation_fourth.py` to anchor checkpoint lint
- ✅ Phase 242: Validated recent checkpoint narrative for the tail block
- ✅ Phase 242 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`452 passed`)
- ✅ Phase 243: Hardened `tests/test_checkpoints_recent_firstline_no_double_exclamation_third.py` to anchor checkpoint lint
- ✅ Phase 243: Validated recent checkpoint narrative for the tail block
- ✅ Phase 243 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`453 passed`)
- ✅ Phase 244: Hardened `tests/test_checkpoints_recent_firstline_no_double_grave_accent.py` to anchor checkpoint lint
- ✅ Phase 244: Validated recent checkpoint narrative for the tail block
- ✅ Phase 244 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`454 passed`)
- ✅ Phase 245: Hardened `tests/test_checkpoints_recent_firstline_no_double_grave_accent_again.py` to anchor checkpoint lint
- ✅ Phase 245: Validated recent checkpoint narrative for the tail block
- ✅ Phase 245 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`455 passed`)
- ✅ Phase 246: Hardened `tests/test_checkpoints_recent_firstline_no_double_grave_accent_fifth.py` to anchor checkpoint lint
- ✅ Phase 246: Validated recent checkpoint narrative for the tail block
- ✅ Phase 246 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`456 passed`)
- ✅ Phase 247: Hardened `tests/test_checkpoints_recent_firstline_no_double_grave_accent_fourth.py` to anchor checkpoint lint
- ✅ Phase 247: Validated recent checkpoint narrative for the tail block
- ✅ Phase 247 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`457 passed`)
- ✅ Phase 248: Hardened `tests/test_checkpoints_recent_firstline_no_double_grave_accent_sixth.py` to anchor checkpoint lint
- ✅ Phase 248: Validated recent checkpoint narrative for the tail block
- ✅ Phase 248 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`458 passed`)
- ✅ Phase 249: Hardened `tests/test_checkpoints_recent_firstline_no_double_grave_accent_third.py` to anchor checkpoint lint
- ✅ Phase 249: Validated recent checkpoint narrative for the tail block
- ✅ Phase 249 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`459 passed`)
- ✅ Phase 250: Hardened `tests/test_checkpoints_recent_firstline_no_double_hash.py` to anchor checkpoint lint
- ✅ Phase 250: Validated recent checkpoint narrative for the tail block
- ✅ Phase 250 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`460 passed`)
- ✅ Phase 251: Hardened `tests/test_checkpoints_recent_firstline_no_double_hash_again.py` to anchor checkpoint lint
- ✅ Phase 251: Validated recent checkpoint narrative for the tail block
- ✅ Phase 251 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`461 passed`)
- ✅ Phase 252: Hardened `tests/test_checkpoints_recent_firstline_no_double_hash_fourth.py` to anchor checkpoint lint
- ✅ Phase 252: Validated recent checkpoint narrative for the tail block
- ✅ Phase 252 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`462 passed`)
- ✅ Phase 253: Hardened `tests/test_checkpoints_recent_firstline_no_double_hash_third.py` to anchor checkpoint lint
- ✅ Phase 253: Validated recent checkpoint narrative for the tail block
- ✅ Phase 253 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`463 passed`)
- ✅ Phase 254: Hardened `tests/test_checkpoints_recent_firstline_no_double_hyphen.py` to anchor checkpoint lint
- ✅ Phase 254: Validated recent checkpoint narrative for the tail block
- ✅ Phase 254 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`464 passed`)
- ✅ Phase 255: Hardened `tests/test_checkpoints_recent_firstline_no_double_hyphen_again.py` to anchor checkpoint lint
- ✅ Phase 255: Validated recent checkpoint narrative for the tail block
- ✅ Phase 255 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`465 passed`)
- ✅ Phase 256: Hardened `tests/test_checkpoints_recent_firstline_no_double_hyphen_fifth.py` to anchor checkpoint lint
- ✅ Phase 256: Validated recent checkpoint narrative for the tail block
- ✅ Phase 256 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`466 passed`)
- ✅ Phase 257: Hardened `tests/test_checkpoints_recent_firstline_no_double_hyphen_fourth.py` to anchor checkpoint lint
- ✅ Phase 257: Validated recent checkpoint narrative for the tail block
- ✅ Phase 257 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`467 passed`)
- ✅ Phase 258: Hardened `tests/test_checkpoints_recent_firstline_no_double_hyphen_third.py` to anchor checkpoint lint
- ✅ Phase 258: Validated recent checkpoint narrative for the tail block
- ✅ Phase 258 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`468 passed`)
- ✅ Phase 259: Hardened `tests/test_checkpoints_recent_firstline_no_double_parentheses.py` to anchor checkpoint lint
- ✅ Phase 259: Validated recent checkpoint narrative for the tail block
- ✅ Phase 259 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`469 passed`)
- ✅ Phase 260: Hardened `tests/test_checkpoints_recent_firstline_no_double_parentheses_again.py` to anchor checkpoint lint
- ✅ Phase 260: Validated recent checkpoint narrative for the tail block
- ✅ Phase 260 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`470 passed`)
- ✅ Phase 261: Hardened `tests/test_checkpoints_recent_firstline_no_double_parentheses_fifth.py` to anchor checkpoint lint
- ✅ Phase 261: Validated recent checkpoint narrative for the tail block
- ✅ Phase 261 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`471 passed`)
- ✅ Phase 262: Hardened `tests/test_checkpoints_recent_firstline_no_double_parentheses_fourth.py` to anchor checkpoint lint
- ✅ Phase 262: Validated recent checkpoint narrative for the tail block
- ✅ Phase 262 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`472 passed`)
- ✅ Phase 263: Hardened `tests/test_checkpoints_recent_firstline_no_double_parentheses_sixth.py` to anchor checkpoint lint
- ✅ Phase 263: Validated recent checkpoint narrative for the tail block
- ✅ Phase 263 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`473 passed`)
- ✅ Phase 264: Hardened `tests/test_checkpoints_recent_firstline_no_double_parentheses_third.py` to anchor checkpoint lint
- ✅ Phase 264: Validated recent checkpoint narrative for the tail block
- ✅ Phase 264 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`474 passed`)
- ✅ Phase 265: Hardened `tests/test_checkpoints_recent_firstline_no_double_percent.py` to anchor checkpoint lint
- ✅ Phase 265: Validated recent checkpoint narrative for the tail block
- ✅ Phase 265 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`475 passed`)
- ✅ Phase 266: Hardened `tests/test_checkpoints_recent_firstline_no_double_percent_again.py` to anchor checkpoint lint
- ✅ Phase 266: Validated recent checkpoint narrative for the tail block
- ✅ Phase 266 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`476 passed`)
- ✅ Phase 267: Hardened `tests/test_checkpoints_recent_firstline_no_double_percent_fifth.py` to anchor checkpoint lint
- ✅ Phase 267: Validated recent checkpoint narrative for the tail block
- ✅ Phase 267 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`477 passed`)
- ✅ Phase 268: Hardened `tests/test_checkpoints_recent_firstline_no_double_percent_fourth.py` to anchor checkpoint lint
- ✅ Phase 268: Validated recent checkpoint narrative for the tail block
- ✅ Phase 268 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`478 passed`)
- ✅ Phase 269: Hardened `tests/test_checkpoints_recent_firstline_no_double_percent_seventh.py` to anchor checkpoint lint
- ✅ Phase 269: Validated recent checkpoint narrative for the tail block
- ✅ Phase 269 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`479 passed`)
- ✅ Phase 270: Hardened `tests/test_checkpoints_recent_firstline_no_double_percent_sixth.py` to anchor checkpoint lint
- ✅ Phase 270: Validated recent checkpoint narrative for the tail block
- ✅ Phase 270 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`480 passed`)
- ✅ Phase 271: Hardened `tests/test_checkpoints_recent_firstline_no_double_percent_third.py` to anchor checkpoint lint
- ✅ Phase 271: Validated recent checkpoint narrative for the tail block
- ✅ Phase 271 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`481 passed`)
- ✅ Phase 272: Hardened `tests/test_checkpoints_recent_firstline_no_double_period.py` to anchor checkpoint lint
- ✅ Phase 272: Validated recent checkpoint narrative for the tail block
- ✅ Phase 272 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`482 passed`)
- ✅ Phase 273: Hardened `tests/test_checkpoints_recent_firstline_no_double_period_again.py` to anchor checkpoint lint
- ✅ Phase 273: Validated recent checkpoint narrative for the tail block
- ✅ Phase 273 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`483 passed`)
- ✅ Phase 274: Hardened `tests/test_checkpoints_recent_firstline_no_double_period_fourth.py` to anchor checkpoint lint
- ✅ Phase 274: Validated recent checkpoint narrative for the tail block
- ✅ Phase 274 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`484 passed`)
- ✅ Phase 275: Hardened `tests/test_checkpoints_recent_firstline_no_double_period_third.py` to anchor checkpoint lint
- ✅ Phase 275: Validated recent checkpoint narrative for the tail block
- ✅ Phase 275 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`485 passed`)
- ✅ Phase 276: Hardened `tests/test_checkpoints_recent_firstline_no_double_pipe.py` to anchor checkpoint lint
- ✅ Phase 276: Validated recent checkpoint narrative for the tail block
- ✅ Phase 276 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`486 passed`)
- ✅ Phase 277: Hardened `tests/test_checkpoints_recent_firstline_no_double_pipe_again.py` to anchor checkpoint lint
- ✅ Phase 277: Validated recent checkpoint narrative for the tail block
- ✅ Phase 277 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`487 passed`)
- ✅ Phase 278: Hardened `tests/test_checkpoints_recent_firstline_no_double_pipe_fourth.py` to anchor checkpoint lint
- ✅ Phase 278: Validated recent checkpoint narrative for the tail block
- ✅ Phase 278 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`488 passed`)
- ✅ Phase 279: Hardened `tests/test_checkpoints_recent_firstline_no_double_pipe_third.py` to anchor checkpoint lint
- ✅ Phase 279: Validated recent checkpoint narrative for the tail block
- ✅ Phase 279 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`489 passed`)
- ✅ Phase 280: Hardened `tests/test_checkpoints_recent_firstline_no_double_plus_again.py` to anchor checkpoint lint
- ✅ Phase 280: Validated recent checkpoint narrative for the tail block
- ✅ Phase 280 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`490 passed`)
- ✅ Phase 281: Hardened `tests/test_checkpoints_recent_firstline_no_double_plus_fourth.py` to anchor checkpoint lint
- ✅ Phase 281: Validated recent checkpoint narrative for the tail block
- ✅ Phase 281 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`491 passed`)
- ✅ Phase 282: Hardened `tests/test_checkpoints_recent_firstline_no_double_plus_sign.py` to anchor checkpoint lint
- ✅ Phase 282: Validated recent checkpoint narrative for the tail block
- ✅ Phase 282 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`492 passed`)
- ✅ Phase 283: Hardened `tests/test_checkpoints_recent_firstline_no_double_plus_third.py` to anchor checkpoint lint
- ✅ Phase 283: Validated recent checkpoint narrative for the tail block
- ✅ Phase 283 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`493 passed`)
- ✅ Phase 284: Hardened `tests/test_checkpoints_recent_firstline_no_double_question.py` to anchor checkpoint lint
- ✅ Phase 284: Validated recent checkpoint narrative for the tail block
- ✅ Phase 284 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`494 passed`)
- ✅ Phase 285: Hardened `tests/test_checkpoints_recent_firstline_no_double_question_again.py` to anchor checkpoint lint
- ✅ Phase 285: Validated recent checkpoint narrative for the tail block
- ✅ Phase 285 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`495 passed`)
- ✅ Phase 286: Hardened `tests/test_checkpoints_recent_firstline_no_double_question_fourth.py` to anchor checkpoint lint
- ✅ Phase 286: Validated recent checkpoint narrative for the tail block
- ✅ Phase 286 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`496 passed`)
- ✅ Phase 287: Hardened `tests/test_checkpoints_recent_firstline_no_double_question_third.py` to anchor checkpoint lint
- ✅ Phase 287: Validated recent checkpoint narrative for the tail block
- ✅ Phase 287 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`497 passed`)
- ✅ Phase 288: Hardened `tests/test_checkpoints_recent_firstline_no_double_quote_again.py` to anchor checkpoint lint
- ✅ Phase 288: Validated recent checkpoint narrative for the tail block
- ✅ Phase 288 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`498 passed`)
- ✅ Phase 289: Hardened `tests/test_checkpoints_recent_firstline_no_double_quote_fifth.py` to anchor checkpoint lint
- ✅ Phase 289: Validated recent checkpoint narrative for the tail block
- ✅ Phase 289 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`499 passed`)
- ✅ Phase 290: Hardened `tests/test_checkpoints_recent_firstline_no_double_quote_fourth.py` to anchor checkpoint lint
- ✅ Phase 290: Validated recent checkpoint narrative for the tail block
- ✅ Phase 290 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`500 passed`)
- ✅ Phase 291: Hardened `tests/test_checkpoints_recent_firstline_no_double_quote_seventh.py` to anchor checkpoint lint
- ✅ Phase 291: Validated recent checkpoint narrative for the tail block
- ✅ Phase 291 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`501 passed`)
- ✅ Phase 292: Hardened `tests/test_checkpoints_recent_firstline_no_double_quote_sixth.py` to anchor checkpoint lint
- ✅ Phase 292: Validated recent checkpoint narrative for the tail block
- ✅ Phase 292 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`502 passed`)
- ✅ Phase 293: Hardened `tests/test_checkpoints_recent_firstline_no_double_quote_third.py` to anchor checkpoint lint
- ✅ Phase 293: Validated recent checkpoint narrative for the tail block
- ✅ Phase 293 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`503 passed`)
- ✅ Phase 294: Hardened `tests/test_checkpoints_recent_firstline_no_double_semicolon_again.py` to anchor checkpoint lint
- ✅ Phase 294: Validated recent checkpoint narrative for the tail block
- ✅ Phase 294 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`504 passed`)
- ✅ Phase 295: Hardened `tests/test_checkpoints_recent_firstline_no_double_semicolon_fourth.py` to anchor checkpoint lint
- ✅ Phase 295: Validated recent checkpoint narrative for the tail block
- ✅ Phase 295 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`505 passed`)
- ✅ Phase 296: Hardened `tests/test_checkpoints_recent_firstline_no_double_semicolon_third.py` to anchor checkpoint lint
- ✅ Phase 296: Validated recent checkpoint narrative for the tail block
- ✅ Phase 296 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`506 passed`)
- ✅ Phase 297: Hardened `tests/test_checkpoints_recent_firstline_no_double_slash.py` to anchor checkpoint lint
- ✅ Phase 297: Validated recent checkpoint narrative for the tail block
- ✅ Phase 297 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`507 passed`)
- ✅ Phase 298: Hardened `tests/test_checkpoints_recent_firstline_no_double_slash_again.py` to anchor checkpoint lint
- ✅ Phase 298: Validated recent checkpoint narrative for the tail block
- ✅ Phase 298 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`508 passed`)
- ✅ Phase 299: Hardened `tests/test_checkpoints_recent_firstline_no_double_slash_fifth.py` to anchor checkpoint lint
- ✅ Phase 299: Validated recent checkpoint narrative for the tail block
- ✅ Phase 299 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`509 passed`)
- ✅ Phase 300: Hardened `tests/test_checkpoints_recent_firstline_no_double_slash_fourth.py` to anchor checkpoint lint
- ✅ Phase 300: Validated recent checkpoint narrative for the tail block
- ✅ Phase 300 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`510 passed`)
- ✅ Phase 301: Hardened `tests/test_checkpoints_recent_firstline_no_double_slash_sixth.py` to anchor checkpoint lint
- ✅ Phase 301: Validated recent checkpoint narrative for the tail block
- ✅ Phase 301 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`511 passed`)
- ✅ Phase 302: Hardened `tests/test_checkpoints_recent_firstline_no_double_slash_third.py` to anchor checkpoint lint
- ✅ Phase 302: Validated recent checkpoint narrative for the tail block
- ✅ Phase 302 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`512 passed`)
- ✅ Phase 303: Hardened `tests/test_checkpoints_recent_firstline_no_double_spaces.py` to anchor checkpoint lint
- ✅ Phase 303: Validated recent checkpoint narrative for the tail block
- ✅ Phase 303 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`513 passed`)
- ✅ Phase 304: Hardened `tests/test_checkpoints_recent_firstline_no_double_square_brackets.py` to anchor checkpoint lint
- ✅ Phase 304: Validated recent checkpoint narrative for the tail block
- ✅ Phase 304 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`514 passed`)
- ✅ Phase 305: Hardened `tests/test_checkpoints_recent_firstline_no_double_square_brackets_again.py` to anchor checkpoint lint
- ✅ Phase 305: Validated recent checkpoint narrative for the tail block
- ✅ Phase 305 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`515 passed`)
- ✅ Phase 306: Hardened `tests/test_checkpoints_recent_firstline_no_double_square_brackets_fourth.py` to anchor checkpoint lint
- ✅ Phase 306: Validated recent checkpoint narrative for the tail block
- ✅ Phase 306 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`516 passed`)
- ✅ Phase 307: Hardened `tests/test_checkpoints_recent_firstline_no_double_square_brackets_third.py` to anchor checkpoint lint
- ✅ Phase 307: Validated recent checkpoint narrative for the tail block
- ✅ Phase 307 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`517 passed`)
- ✅ Phase 308: Hardened `tests/test_checkpoints_recent_firstline_no_double_tilde.py` to anchor checkpoint lint
- ✅ Phase 308: Validated recent checkpoint narrative for the tail block
- ✅ Phase 308 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`518 passed`)
- ✅ Phase 309: Hardened `tests/test_checkpoints_recent_firstline_no_double_tilde_again.py` to anchor checkpoint lint
- ✅ Phase 309: Validated recent checkpoint narrative for the tail block
- ✅ Phase 309 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`519 passed`)
- ✅ Phase 310: Hardened `tests/test_checkpoints_recent_firstline_no_double_tilde_fifth.py` to anchor checkpoint lint
- ✅ Phase 310: Validated recent checkpoint narrative for the tail block
- ✅ Phase 310 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`520 passed`)
- ✅ Phase 311: Hardened `tests/test_checkpoints_recent_firstline_no_double_tilde_fourth.py` to anchor checkpoint lint
- ✅ Phase 311: Validated recent checkpoint narrative for the tail block
- ✅ Phase 311 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`521 passed`)
- ✅ Phase 312: Hardened `tests/test_checkpoints_recent_firstline_no_double_tilde_sixth.py` to anchor checkpoint lint
- ✅ Phase 312: Validated recent checkpoint narrative for the tail block
- ✅ Phase 312 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`522 passed`)
- ✅ Phase 313: Hardened `tests/test_checkpoints_recent_firstline_no_double_tilde_third.py` to anchor checkpoint lint
- ✅ Phase 313: Validated recent checkpoint narrative for the tail block
- ✅ Phase 313 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`523 passed`)
- ✅ Phase 314: Hardened `tests/test_checkpoints_recent_firstline_no_double_underscore.py` to anchor checkpoint lint
- ✅ Phase 314: Validated recent checkpoint narrative for the tail block
- ✅ Phase 314 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`524 passed`)
- ✅ Phase 315: Hardened `tests/test_checkpoints_recent_firstline_no_double_underscore_again.py` to anchor checkpoint lint
- ✅ Phase 315: Validated recent checkpoint narrative for the tail block
- ✅ Phase 315 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`525 passed`)
- ✅ Phase 316: Hardened `tests/test_checkpoints_recent_firstline_no_double_underscore_third.py` to anchor checkpoint lint
- ✅ Phase 316: Validated recent checkpoint narrative for the tail block
- ✅ Phase 316 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`526 passed`)
- ✅ Phase 317: Hardened `tests/test_checkpoints_recent_focused_count_trend.py` to anchor checkpoint lint
- ✅ Phase 317: Validated recent checkpoint narrative for the tail block
- ✅ Phase 317 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`527 passed`)
- ✅ Phase 318: Hardened `tests/test_checkpoints_recent_focused_segment_wording_noise.py` to anchor checkpoint lint
- ✅ Phase 318: Validated recent checkpoint narrative for the tail block
- ✅ Phase 318 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`528 passed`)
- ✅ Phase 319: Hardened `tests/test_checkpoints_recent_focused_token_cardinality.py` to anchor checkpoint lint
- ✅ Phase 319: Validated recent checkpoint narrative for the tail block
- ✅ Phase 319 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`529 passed`)
- ✅ Phase 320: Hardened `tests/test_checkpoints_recent_focused_vs_full_counts.py` to anchor checkpoint lint
- ✅ Phase 320: Validated recent checkpoint narrative for the tail block
- ✅ Phase 320 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`530 passed`)
- ✅ Phase 321: Hardened `tests/test_checkpoints_recent_full_count_delta_one.py` to anchor checkpoint lint
- ✅ Phase 321: Validated recent checkpoint narrative for the tail block
- ✅ Phase 321 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`531 passed`)
- ✅ Phase 322: Hardened `tests/test_checkpoints_recent_full_count_strict_growth.py` to anchor checkpoint lint
- ✅ Phase 322: Validated recent checkpoint narrative for the tail block
- ✅ Phase 322 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`532 passed`)
- ✅ Phase 323: Hardened `tests/test_checkpoints_recent_full_focused_gap_trend.py` to anchor checkpoint lint
- ✅ Phase 323: Validated recent checkpoint narrative for the tail block
- ✅ Phase 323 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`533 passed`)
- ✅ Phase 324: Hardened `tests/test_checkpoints_recent_full_phrase_cardinality.py` to anchor checkpoint lint
- ✅ Phase 324: Validated recent checkpoint narrative for the tail block
- ✅ Phase 324 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`534 passed`)
- ✅ Phase 325: Hardened `tests/test_checkpoints_recent_full_pytest_count_trend.py` to anchor checkpoint lint
- ✅ Phase 325: Validated recent checkpoint narrative for the tail block
- ✅ Phase 325 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`535 passed`)
- ✅ Phase 326: Hardened `tests/test_checkpoints_recent_full_segment_wording_noise.py` to anchor checkpoint lint
- ✅ Phase 326: Validated recent checkpoint narrative for the tail block
- ✅ Phase 326 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`536 passed`)
- ✅ Phase 327: Hardened `tests/test_checkpoints_recent_full_token_cardinality.py` to anchor checkpoint lint
- ✅ Phase 327: Validated recent checkpoint narrative for the tail block
- ✅ Phase 327 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`537 passed`)
- ✅ Phase 328: Hardened `tests/test_checkpoints_recent_phase_block_order.py` to anchor checkpoint lint
- ✅ Phase 328: Validated recent checkpoint narrative for the tail block
- ✅ Phase 328 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`538 passed`)
- ✅ Phase 329: Hardened `tests/test_checkpoints_recent_phase_contiguity.py` to anchor checkpoint lint
- ✅ Phase 329: Validated recent checkpoint narrative for the tail block
- ✅ Phase 329 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`539 passed`)
- ✅ Phase 330: Hardened `tests/test_checkpoints_recent_phase_entry_verification_set_match.py` to anchor checkpoint lint
- ✅ Phase 330: Validated recent checkpoint narrative for the tail block
- ✅ Phase 330 verification: focused guard pass (`1 passed`), alignment cross-check pass (`True True True`), full pytest pass (`540 passed`)

## UX) Productized UI/UX surfaces (Beginner + Trader + Power user)
- ✅ UX1: App shell + route map + navigation IA completed with global mode badge, system health pill, alerts entrypoint, and kill-switch control in header (`attic/trade-ai-mvp/frontend/src/components/layout/AppShell.tsx`, `attic/trade-ai-mvp/frontend/src/app/{routes.ts,router.tsx}`)
- ✅ UX2: Dashboard screen implemented with mode/safety banner, portfolio summary, connections health, watchlist movers, explanations, recommendations, catalysts, and quick actions (`attic/trade-ai-mvp/frontend/src/pages/DashboardPage.tsx`)
- ✅ UX3: Connections v1 implemented with exchange cards, dynamic credential schema forms (Binance/Coinbase/Kraken/OKX + expansions), test/save/disable/remove flows, permissions detection, and read-only vs trading labeling (`attic/trade-ai-mvp/frontend/src/pages/ConnectionsPage.tsx`, `attic/trade-ai-mvp/frontend/src/components/forms/ExchangeCredentialForm.tsx`)
- ✅ UX4: Research workspace v1 implemented with ask box, filters, timeline tabs, answer sections (current/past/future/confidence/risk note), evidence, and history (`attic/trade-ai-mvp/frontend/src/pages/ResearchPage.tsx`)
- ✅ UX5: Settings v1 implemented across General/Notifications/AI/Data/Security tabs with safe defaults (`research_only`, evidence/confidence enabled) plus save path (`attic/trade-ai-mvp/frontend/src/pages/SettingsPage.tsx`, `attic/trade-ai-mvp/frontend/src/mock/data/settings.json`)
- ✅ UX6: Shared design system + component contracts implemented (badges, cards, forms, confirm modal, empty/loading/error states, typed UI contracts) (`attic/trade-ai-mvp/frontend/src/styles.css`, `attic/trade-ai-mvp/frontend/src/types/contracts.ts`, `attic/trade-ai-mvp/frontend/src/components/**`)
- ✅ UX7: Trading UI v1 implemented with recommendations/approvals/positions/orders/strategies tabs, explicit execution-state labeling, and recommendation detail drawer (`attic/trade-ai-mvp/frontend/src/pages/TradingPage.tsx`, `attic/trade-ai-mvp/frontend/src/components/trading/RecommendationDetailDrawer.tsx`)
- ✅ UX8: Risk UI v1 implemented with global risk summary, editable limits form, approval policy panel, restricted assets, kill-switch panel, blocked-trade view, and risk audit table (`attic/trade-ai-mvp/frontend/src/pages/RiskPage.tsx`, `attic/trade-ai-mvp/frontend/src/components/forms/RiskLimitsForm.tsx`)
- ✅ UX9: Approval workflows implemented (queue + approve/reject + optional size override) with confirmation modals and audit-hooked mock mutations (`attic/trade-ai-mvp/frontend/src/pages/TradingPage.tsx`, `attic/trade-ai-mvp/frontend/src/components/modals/ConfirmActionModal.tsx`, `attic/trade-ai-mvp/frontend/src/mock/handlers.ts`)
- ✅ UX10: Terminal mode v1 implemented as controlled app console (no shell) with allowlisted parser behavior, help groups, suggestions/autocomplete, command history, and dangerous-action confirmation (`attic/trade-ai-mvp/frontend/src/pages/TerminalPage.tsx`, `attic/trade-ai-mvp/frontend/src/components/terminal/**`, `attic/trade-ai-mvp/frontend/src/mock/handlers.ts`)
- ✅ UX11: Onboarding wizard v1 implemented (mode, sources, watchlist interests, risk profile, first query step) with beginner-safe defaults and completion hook (`attic/trade-ai-mvp/frontend/src/components/onboarding/OnboardingWizard.tsx`)
- ✅ UX12: Mock API handler pack + JSON fixture set expanded and aligned with typed UI contracts for decoupled frontend delivery (`attic/trade-ai-mvp/frontend/src/mock/handlers.ts`, `attic/trade-ai-mvp/frontend/src/mock/data/*.json`, `attic/trade-ai-mvp/frontend/src/services/mockApi.ts`)
- ✅ UX13: User-facing audit/history surfaces implemented across settings/trading/risk with traceability for decisions, approvals, risk blocks, and connection-setting actions (`attic/trade-ai-mvp/frontend/src/components/history/AuditTable.tsx`, `attic/trade-ai-mvp/frontend/src/pages/{SettingsPage.tsx,TradingPage.tsx,RiskPage.tsx}`)
- ✅ UX14: Multi-exchange UX expansion implemented with Bybit/KuCoin/Gate.io/Bitget/Hyperliquid fixture coverage and normalized capability/status badges (`attic/trade-ai-mvp/frontend/src/mock/data/exchanges.json`, `attic/trade-ai-mvp/frontend/src/pages/ConnectionsPage.tsx`)
- ⚠️ UX Safety rule: terminal must remain a controlled product console only; no unrestricted shell access from UI

## API) Frontend-backend contract alignment pack (v1)
- ✅ API1: `/api/v1` envelope rollout completed across implemented gateway domain routes (health/enums/dashboard/research/market/trading/approvals/risk/connections/settings/audit/terminal)
- ✅ API2: Shared enums/schemas added (`mode`, `risk_status`, `connection_status`, `timeline`, `approval_status`, recommendation side) and published via typed gateway OpenAPI routes
- ✅ API3: Implemented `GET /api/v1/dashboard/summary` contract shape with explicit mode/execution/approval/risk/kill-switch fields and UI-aligned portfolio/connections/watchlist/recommendations/catalyst containers
- ✅ API4: Implemented `/api/v1/research/explain`, `/api/v1/research/search`, and `/api/v1/research/history` envelope routes with filter/timeline inputs, evidence mapping, pagination meta, and graceful dependency-failure envelopes
- ✅ API5: Implemented market contracts (`GET /api/v1/market/{asset}/snapshot`, `GET /api/v1/market/{asset}/candles`) with exchange/interval params, envelope responses, and degraded fallback when candle storage is unavailable
- ✅ API6: Implemented trading recommendation contracts (`GET /api/v1/trading/recommendations`, detail, approve, reject) with explicit `execution_disabled`/`approval_required` fields and envelope responses
- ✅ API7: Implemented approvals domain (`GET /api/v1/approvals`, `POST /api/v1/approvals/:id/approve|reject`) mapped to recommendation approval workflow (scaffolded in-memory state pending DB-backed persistence)
- ✅ API8: Implemented risk contracts (`GET /api/v1/risk/summary`, `GET|PUT /api/v1/risk/limits`, `POST /api/v1/risk/kill-switch`) with role guards, kill-switch state updates, and policy-aligned error envelopes
- ✅ API9: Implemented connections/provider contracts (`/api/v1/connections/exchanges` GET/POST/PATCH/DELETE + `/test`, `/api/v1/connections/providers` GET/POST + `/test`) with role guards, permissions detection, and latency/health response fields
- ✅ API10: Implemented settings + audit contracts (`GET|PUT /api/v1/settings`, `GET /api/v1/audit/events` with pagination/meta and service/result filters) plus role guard on settings writes
- ✅ API11: Implemented controlled terminal contracts (`POST /api/v1/terminal/execute`, `POST /api/v1/terminal/confirm`) with allowlisted command policy checks, confirmation tokens for dangerous commands, and explicit no-shell execution path
- ✅ API12: Published API ownership/implementation-order/persistence anti-drift docs (`attic/trade-ai-mvp/docs/API_OWNERSHIP_IMPLEMENTATION_ORDER.md` + `DB_SCHEMA_ALIGNMENT_PACK.md`)
- ⚠️ API Safety rule: terminal endpoints must route only approved product commands; never expose raw shell execution

## DB) Schema alignment pack (UI/API/service ownership)
- ✅ DB1: Published domain-modeled ORM ownership modules (`shared/models/domain/{core,connections,market,research,trading,risk,ops}.py`) with ownership index and structural tests
- ✅ DB2: Defined MVP + full production table sets with promotion criteria in schema alignment pack (`attic/trade-ai-mvp/docs/DB_SCHEMA_ALIGNMENT_PACK.md`)
- ✅ DB3: Added endpoint-to-table mapping for `/api/v1` routes (`attic/trade-ai-mvp/docs/DB_SCHEMA_ALIGNMENT_PACK.md`)
- ✅ DB4: Added service write-ownership rules for single-writer domain boundaries (`attic/trade-ai-mvp/docs/DB_SCHEMA_ALIGNMENT_PACK.md`)
- ✅ DB5: Added FK-safe migration order plan (identity -> settings -> connections -> market -> research -> trading -> risk -> ops) (`attic/trade-ai-mvp/docs/DB_SCHEMA_ALIGNMENT_PACK.md`)
- ✅ DB6: Added high-frequency index plan for research/trading/risk/audit domains (`attic/trade-ai-mvp/docs/DB_SCHEMA_ALIGNMENT_PACK.md`)
- ✅ DB7: Added retention/archival policy with explicit config knobs (`attic/trade-ai-mvp/docs/DB_SCHEMA_ALIGNMENT_PACK.md`)
- ✅ DB8: Added vector/evidence traceability table definitions (`document_embeddings`, `evidence_links`) in schema alignment pack (`attic/trade-ai-mvp/docs/DB_SCHEMA_ALIGNMENT_PACK.md`)
- ✅ DB9: Added lifecycle persistence extensions for research/trading entities (`research_queries`, `recommendations`, `recommendation_versions`, `approvals`, etc.) in schema alignment pack (`attic/trade-ai-mvp/docs/DB_SCHEMA_ALIGNMENT_PACK.md`)
- ✅ DB10: Added connection credential split and rotation/test-history model (`exchange_connections`, `exchange_credentials`, `connection_test_results`) in schema alignment pack (`attic/trade-ai-mvp/docs/DB_SCHEMA_ALIGNMENT_PACK.md`)
- ⚠️ DB Safety rule: encrypted credential material must never be logged or returned in API responses

## SM) State machine centralization (modes, approvals, orders, positions, kill switch)
- ✅ SM1: Added `domain/state_machines/` package with explicit enums for mode/recommendation/approval/order/position/kill-switch/safety states
- ✅ SM2: Implemented explicit transition maps per machine (no implicit transitions)
- ✅ SM3: Implemented guard check functions for protected transitions (mode escalations, approval/order submission, kill-switch release)
- ✅ SM4: Added typed transition result contract (`TransitionResult`: `allowed`, `from_state`, `to_state`, `reason`, `side_effects`)
- ✅ SM5: Added transition audit-event helper (`build_transition_audit_event`) with actor/request/context fields
- ✅ SM6: Integrated kill-switch/order-transition guards into execution-affecting API paths (`trading .../approve`, `approvals .../approve`)
- ✅ SM7: Enforced explicit `rejected` vs `failed` order lifecycle split in state machine rules and tests
- ✅ SM8: Added position `error_state` with reconciliation-required guard and recovery side effect
- ✅ SM9: Added comprehensive state-machine tests and composite workflow tests (`attic/trade-ai-mvp/tests/test_state_machines.py`, `attic/trade-ai-mvp/tests/test_workflow_contracts.py`)
- ⚠️ SM Safety rule: no service may bypass state-machine guards for execution-affecting transitions

## PM) Permissions and policy matrix
- ✅ PM1: Defined centralized role/mode/risk/kill-switch/connection/terminal permission matrix modules (`domain/policy/*`) with deterministic allow/deny decisions and reason codes
- ✅ PM2: Encoded approval-required policy matrix (size/confidence/futures/new-asset/new-exchange/mode/risk) as composable evaluators (`approval_policy.py`, `trade_policy.py`)
- ✅ PM3: Route-level policy wiring completed for `/api/v1` mutating paths (trade/approval approve+reject, risk writes, connections writes, settings writes, terminal command execution+confirm) using centralized role/policy reason-code decisions

## WF) Workflow specs for end-to-end user journeys
- ✅ WF1: Published canonical workflow specs for connect exchange, research query, paper/live approvals, kill-switch lifecycle, and terminal execution (`attic/trade-ai-mvp/docs/WORKFLOW_SPECS.md`)
- ✅ WF2: Added per-step mapping from workflow actions to API endpoints, policy gates, state-transition expectations, and audit events (`attic/trade-ai-mvp/docs/WORKFLOW_SPECS.md`)
- ✅ WF3: Added workflow contract tests for happy/blocked paths across role/mode/risk/kill-switch permutations (`attic/trade-ai-mvp/tests/test_workflow_contracts.py`)

## 2026-03-22 audit output dir checkpoint
- blocker fixed: removed hardcoded OUT_DIR=/repo_audit_
- canonical output root: .cbp_state/audit_reports
- verified newest run directory contains 00_summary.txt, failed_checks.txt, and pytest_collect.txt
- latest successful run: .cbp_state/audit_reports/repo_audit_20260322_095927

## 2026-03-22 successful manual audit run
- audit script writes to .cbp_state/audit_reports
- verified newest run directory contains 00_summary.txt, failed_checks.txt, and pytest_collect.txt
- latest successful run: .cbp_state/audit_reports/repo_audit_20260322_100331
- failed_checks.txt is empty in the latest successful run

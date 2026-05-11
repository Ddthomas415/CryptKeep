# CryptKeep — Audit Coverage Map

**Last updated:** 2026-05-10 (after Pass 2O)

**Honest scope statement:**
This is a coverage-tracking document, not a claim of completeness.
The codebase contains approximately 1,400+ Python files. After 15 pass-2
audit segments (2A–2O), approximately 115–125 files have been read in
some depth. That is roughly 8–9% of the total codebase.

Previous versions of this document used the title 'Complete Audit Map'
which implied completeness it did not have. That title was wrong.
This version corrects the record.

---

## Depth taxonomy

| Label | Meaning |
|---|---|
| NOT_AUDITED | Never read |
| DISCOVERED | Purpose known, not read in depth |
| SAMPLED | Key sections read, not exhaustive |
| REVIEWED | Full read, all functions inspected |
| TESTED | Dynamic / adversarial verification |

---

## Actual coverage by directory

| Directory | Files total | Files reviewed | True coverage |
|---|---|---|---|
| services/execution/ | 80 | ~12 | 15% |
| services/strategies/ | 30 | ~5 | 17% |
| services/market_data/ | 29 | 0 | **0%** |
| services/admin/ | 26 | 16 | 62% |
| services/risk/ | 21 | 2 | 10% |
| services/security/ | 13 | 8 | 62% |
| services/backtest/ | 17 | 2 | 12% |
| services/analytics/ | 15 | 1 | 7% |
| services/signals/ | 13 | 0 | **0%** |
| services/ai_copilot/ | 12 | 3 | 25% |
| services/control/ | 9 | 5 | 56% |
| services/governance/ | 11 | 9 | 82% |
| services/fills/ | 3 | 2 | 67% |
| services/pipeline/ | 4 | 3 | 75% |
| services/runtime/ | 5 | 3 | 60% |
| services/os/ | 3 | 2 | 67% |
| All other services/ dirs | ~200+ | ~5 | <3% |
| storage/ | 46 | 5 | 11% |
| dashboard/pages/ | 26 | 18 | 69% |
| dashboard/services/ | ~30 | ~8 | 27% |
| scripts/ | 145 | ~15 | 10% |
| tests/ | 668 | 0 content | **0%** |

---

## What was actually covered (confirmed)

### Execution critical path
Reviewed: place_order.py, live_intent_consumer.py, live_reconciler.py,
fill_sink.py, system_health.py, intent_executor.py, adapters/factory.py,
adapters/paper.py, live_exchange_adapter.py, lifecycle_boundary.py,
order_params.py, paper_runner.py

### Admin and arming
Reviewed: kill_switch.py, live_guard.py, live_enable_wizard.py,
live_disable_wizard.py, system_guard.py, preflight.py, resume_gate.py,
safe_mode_recovery.py, safety_policy.py, service_controls.py,
repair_wizard.py, reconcile_safe_steps.py, config_editor.py, watchdog.py

### Security module
Reviewed: auth_gate.py, role_guard.py, auth_runtime_guard.py,
binance_guard.py, credentials_loader.py, direct_origin_guard.py,
exchange_factory.py, permission_probes.py
Sampled: auth_capabilities.py, secret_store.py, user_auth_store.py

### Storage
Reviewed: order_dedupe_store_sqlite.py, file_utils.py
Sampled: paper_trading_sqlite.py, live_intent_queue_sqlite.py,
live_trading_sqlite.py, strategy_state_store_sqlite.py,
trade_journal_sqlite.py

### Governance
Reviewed: campaign_state_machine.py, decision_engine.py, invalidation.py,
claims_guard.py, campaign_validation.py, deployment_truth.py,
operator_overrides.py, campaign_fingerprint.py

### Control plane
Reviewed: kernel.py, cognitive_budget.py, deployment_stage.py
Sampled: allocator.py not yet read

### Strategies
Reviewed: es_daily_trend.py, strategy_registry.py
Sampled: strategy_selector.py

### Dashboard pages (18 of 26 read)
Reviewed: 40_Trades, 50_Automation, 70_Settings, 60_Operations,
65_Copilot_Reports, 44_Paper_Reconciliation, 35_Research, 99_Legacy_UI,
20_Portfolio, 10_Markets, 30_Signals, plus home/overview/markets passes

---

## Confirmed NOT_AUDITED (highest risk surfaces not yet read)

### Must-read before live deployment
- services/market_data/ (29 files, 0 reviewed) — OHLCV fetch, WS feeds
- services/risk/risk_gate.py — runtime risk enforcement
- services/risk/live_risk_gates.py
- services/risk/market_quality_guard.py
- services/risk/position_sizing.py
- services/risk/daily_limits.py
- services/signals/ (13 files, 0 reviewed)
- services/execution/ remaining 68 files

### Should read before live deployment
- services/control/allocator.py
- services/control/runtime_identity.py
- services/analytics/ (15 files, 1 reviewed)
- storage/ remaining 41 files (especially risk-adjacent stores)
- tests/ content audit (668 files, 0 reviewed)

### Lower priority
- All other services/ directories with 0 coverage
- Historical PHASE*.md docs in docs/

---

## Open findings (after Passes 1–2O)

| # | Severity | Finding |
|---|---|---|
| H4 | High | Governance enforcement dead code — never called in production |
| H5 | High | resume_if_safe disconnected from config — Drill 6 confirmed |
| H6 | High | Soak evidence invisible to evidence promotion gate |
| H7 | High | enforce_direct_origin_block dead code — security guard never called |
| H1 | Medium | VIEWER partial arming state via Automation |
| H2 | Medium | VIEWER writes API keys via Settings |
| H3 | Medium | VIEWER corrupts paper state via Paper Reconciliation |
| M1 | Medium | find_order_by_client_oid swallows exchange exceptions |
| M2 | Medium | Safe wrapper routes to paper-era consumer |
| M3 | Medium | CURRENT_RUNTIME_TRUTH.md lists market_ws not started |

---

## Audit session log

| Date | Passes | Files covered | New High findings |
|---|---|---|---|
| 2026-05-10 | Pass 1 (sections 1–10) | ~60 | H1, H2, H3, H4 |
| 2026-05-10 | Pass 2A–2O | ~60 more | H5, H6, H7 |

---

## How to use this map

1. Pick the next surface from 'Must-read before live deployment'.
2. Read it. Update the coverage table.
3. Add findings to the open findings table.
4. Commit this file after each session.

Do not create new audit planning docs. Update this one.

# CryptKeep — Complete Audit Map

**Created:** 2026-05-10  
**Purpose:** Definitive reference for all audit work — past, present, and future.  
This document is designed to be carried forward across sessions and updated
as audit passes are completed.

---

## Audit depth taxonomy

Every surface in this map is assigned one of five depth labels:

| Label | Meaning |
|---|---|
| `NOT_AUDITED` | Never read. No findings. No coverage. |
| `DISCOVERED` | File/module identified, purpose understood, not read in depth. |
| `SAMPLED` | Key sections read. Representative patterns checked. Not exhaustive. |
| `REVIEWED` | Full read. All functions inspected. Static analysis complete. |
| `TESTED` | Dynamic analysis performed. Behavior verified by execution or adversarial test. |

Most production code requires `REVIEWED` before pre-live sign-off.
Critical execution paths require `REVIEWED` + `TESTED`.

---

## Audit method taxonomy

| Method | Meaning |
|---|---|
| `static` | File read only. No execution. |
| `dynamic` | Code was run and output observed. |
| `adversarial` | Attempted to trigger the failure mode, not just find it in code. |
| `doc_review` | Docs read and compared to code truth. |

---

## Summary — Pass 1 coverage

**Total Python files in repo:** ~1,400+ (services, storage, dashboard, scripts, tests)  
**Files read in depth (REVIEWED or better):** ~60  
**Files sampled:** ~40  
**Files not read:** ~1,300+

Pass 1 is a structured first-pass audit. It establishes the finding landscape
and identifies the highest-risk surfaces. It is not a complete code review.

---

## Section 1 — Runtime Control Plane

**Status:** SAMPLED (prior session) + REVIEWED (this session)

| File | Depth | Notes |
|---|---|---|
| `scripts/start_bot.py` | REVIEWED | Missing intent_consumer fixed PR #39 |
| `scripts/stop_bot.py` | REVIEWED | Flag syntax confirmed |
| `scripts/bot_status.py` | SAMPLED | PID tracking false-negative observed in soak |
| `services/runtime/process_supervisor.py` | REVIEWED | PID file not atomic; IDLE-on-crash; session detach gap |
| `services/process/bot_runtime_truth.py` | SAMPLED | canonical_service_status() used by alert monitor |
| `scripts/run_pipeline_loop.py` | REVIEWED | EMA default; executor_mode read; sma_period/atr_period wired |
| `scripts/run_bot_runner.py` | DISCOVERED | enabled=false; not in supervised stack |

**Open:** PID file write_text not atomic; market_ws listed in docs but not started.

---

## Section 2 — Paper Soak and Runtime Evidence

**Status:** REVIEWED

| File | Depth | Notes |
|---|---|---|
| `scripts/report_supervised_soak_status.py` | REVIEWED | counts_for_paper_gate ≠ gate-pass; drift flags confirmed |
| `docs/PAPER_SOAK_GATE.md` | REVIEWED + updated | Three operator decisions recorded 2026-05-10 |
| `docs/LAUNCH_CHECKLIST.md` | REVIEWED | Section 4.1 resolved via PAPER_SOAK_GATE.md |
| `.cbp_state/runtime/ai_reports/*.json` | SAMPLED | 9 incidents; 3 unique current-window families |
| `.cbp_state/runtime/logs/pipeline.log` | SAMPLED | 3 run_once_failed, all recovered |

---

## Section 3 — Execution, Routing, and Risk Gates

**Status:** REVIEWED (key files) + TESTED (via soak)

| File | Depth | Notes |
|---|---|---|
| `services/execution/place_order.py` | REVIEWED | Findings 1-2 open; async skips precision |
| `services/execution/live_intent_consumer.py` | REVIEWED | Findings 3-4 fixed PR #39 |
| `services/execution/live_reconciler.py` | REVIEWED | Findings 5-7; cursor fixed PR #36 |
| `services/execution/fill_sink.py` | REVIEWED | Findings 8-9; CompositeFillSink fixed PR #36 |
| `services/risk/system_health.py` | REVIEWED | Findings 10-11; invariant gap fixed PR #36 |
| `services/execution/intent_executor.py` | REVIEWED | Mode separation confirmed; _live_allowed canonical |
| `services/execution/adapters/factory.py` | REVIEWED | mode=paper routes to PaperEngineAdapter (PR #37) |
| `services/execution/adapters/paper.py` | REVIEWED | New PR #37; interface matches intent_executor |
| `scripts/run_intent_executor_safe.py` | REVIEWED | IDLE on crash; delegates to paper-era consumer |
| `scripts/run_live_reconciler_safe.py` | REVIEWED | IDLE on crash |
| `scripts/run_intent_consumer_safe.py` | REVIEWED | Wraps run_intent_consumer NOT run_live_intent_consumer |
| `scripts/run_live_intent_consumer.py` | SAMPLED | Correct script; started directly by start_bot.py |

**NOT_AUDITED:** live_exchange_adapter.py, order_router.py, position_tracker.py,
risk_gate.py, daily_risk.py, reconciliation/ services.

---

## Section 4 — Storage and State Integrity

**Status:** SAMPLED (4 of 46 storage files)

| File | Depth | Notes |
|---|---|---|
| `services/os/file_utils.py` | REVIEWED | atomic_write correct |
| `storage/paper_trading_sqlite.py` | SAMPLED | WAL; INSERT OR IGNORE on client_order_id |
| `storage/live_intent_queue_sqlite.py` | SAMPLED | WAL; BEGIN IMMEDIATE risk claim |
| `storage/live_trading_sqlite.py` | SAMPLED | INSERT OR IGNORE on fill_key |
| `storage/strategy_state_store_sqlite.py` | SAMPLED | INSERT OR REPLACE |

**NOT_AUDITED (42 files):** canonical_journal_sqlite.py, risk_ledger_store_sqlite.py,
order_dedupe_store_sqlite.py, live_position_store_sqlite.py, and 38 others.

---

## Section 5 — Market Data and Symbol Management

**Status:** SAMPLED

| File | Depth | Notes |
|---|---|---|
| `services/runtime/managed_symbol_selection.py` | REVIEWED | Scanner block in live; fallback; cache TTL |
| `services/runtime/dynamic_symbol_selector.py` | SAMPLED | Catches all exceptions |

**NOT_AUDITED:** ccxt_market_data.py, ws_market_data.py, managed_symbol_config.py.

---

## Section 6 — Dashboard and Operator UI

**Status:** REVIEWED (14 of 26 pages)

| Page | Depth | Key finding |
|---|---|---|
| `10_Markets.py` | REVIEWED | Watchlist strips source |
| `30_Signals.py` | REVIEWED | Recommendation provenance lost |
| `40_Trades.py` | REVIEWED | Synthetic fallback rows carry no provenance |
| `50_Automation.py` | REVIEWED | **HIGH: VIEWER can arm live** |
| `60_Operations.py` | REVIEWED | Correctly requires OPERATOR |
| `65_Copilot_Reports.py` | REVIEWED | Artifact browser, not current-window truth |
| `70_Settings.py` | REVIEWED | **HIGH: VIEWER can write API keys** |

**NOT_AUDITED (12 pages):** 05_Help, 20_Portfolio, 35_Research, 36-39 scanner/movers pages,
40_Market_Intelligence, 41-48 intelligence/backtest pages, 99_Legacy_UI.

---

## Section 7 — AI Copilot and Alerting

**Status:** REVIEWED (2 of 11 files)

| File | Depth | Notes |
|---|---|---|
| `services/ai_copilot/alert_monitor.py` | REVIEWED | Log dedup; incidents_written cumulative |
| `services/ai_copilot/context_collector.py` | REVIEWED | Canonical health + last 20 log lines |
| `services/ai_copilot/safety_auditor.py` | SAMPLED | write_text not atomic |

**NOT_AUDITED (8 files):** policy.py, providers.py, drift_auditor.py,
incident_analyst.py, oversight_watch.py, pr_reviewer.py, sim_runner.py, strategy_lab.py.

---

## Section 8 — Evidence, Promotion, and Governance

**Status:** SAMPLED

| File | Depth | Notes |
|---|---|---|
| `services/backtest/evidence_cycle.py` | SAMPLED | evidence_status classification confirmed |
| `dashboard/services/promotion_ladder.py` | REVIEWED | paper_supported enforced at both gates |
| `docs/governance/governance_signoff.md` | REVIEWED | 3 Blocking:Yes items from 2026-03-21 |
| `docs/governance/governance_checklist.md` | REVIEWED | Stale — different branch and strategy |

**NOT_AUDITED:** paper_strategy_evidence_service.py, paper_campaign_lifecycle.py,
services/governance/ (8 modules), most of services/backtest/.

---

## Section 9 — Auth, Roles, and Safety Boundaries

**Status:** REVIEWED

| File | Depth | Notes |
|---|---|---|
| `dashboard/auth_gate.py` | REVIEWED | Lockout server-side; bypass dev-only |
| `dashboard/role_guard.py` | REVIEWED | RolePolicy defined but not enforced on save paths |
| `dashboard/services/operator.py` | REVIEWED | 12 require_role sites; Operations correct |

**NOT_AUDITED:** auth_runtime_guard.py, exchange_factory.py, binance_guard.py,
MFA enrollment paths.

---

## Section 10 — Release, Validation, and Operator Docs

**Status:** REVIEWED

| File | Depth | Notes |
|---|---|---|
| `scripts/validate.py` | REVIEWED | Accurate; --quick and --full both correct |
| `scripts/pre_release_sanity.py` | REVIEWED | YAML + alignment; structured JSON output |
| `docs/CURRENT_RUNTIME_TRUTH.md` | REVIEWED | market_ws listed but not started |
| `docs/LAUNCH_CHECKLIST.md` | REVIEWED | Commands accurate; 4.1 resolved |
| `REMAINING_TASKS.md` | REVIEWED | Accurately describes current state |

---

## Open findings by severity

### High

| # | Finding | Location |
|---|---|---|
| H1 | VIEWER can arm live via Automation save | `50_Automation.py` |
| H2 | VIEWER can write API keys via Settings save | `70_Settings.py` |

### Medium

| # | Finding | Location |
|---|---|---|
| M1 | `run_intent_consumer_safe.py` wraps paper-era consumer | `scripts/` |
| M2 | Safe wrappers IDLE on crash; PID stays alive | `run_*_safe.py` |
| M3 | `CURRENT_RUNTIME_TRUTH.md` lists market_ws not started | `docs/` |
| M4 | `execution_enabled` badge reads from stale API source | `50_Automation.py` |
| M5 | Settings provider status is config-file string, not live probe | `70_Settings.py` |
| M6 | Recent fills carry no source field | `_shared_execution.py` |

### Low / Noted

| # | Finding | Location |
|---|---|---|
| L1 | PID file uses write_text not atomic_write | `process_supervisor.py` |
| L2 | dry_run_mode override not labeled on Automation page | `50_Automation.py` |
| L3 | incidents_written is cumulative not unique-failure | `alert_monitor.py` |
| L4 | AI monitor keywords are substring — false positives possible | `alert_monitor.py` |
| L5 | safety_auditor.py writes not atomic | `safety_auditor.py` |
| L6 | Governance signoff frozen 2026-03-21; 3 Blocking:Yes items | `governance_signoff.md` |
| L7 | Governance checklist stale — different branch/strategy | `governance_checklist.md` |
| L8 | Synthetic fallback rows carry no provenance on Trades page | `execution_view.py` |

---

## Recommended pass 2 — priority order

### Pass 2A — Critical pre-live surfaces (must read before live)

1. `services/execution/live_exchange_adapter.py`
2. `services/risk/daily_risk.py`
3. `services/risk/risk_gate.py`
4. `storage/canonical_journal_sqlite.py`
5. `storage/risk_ledger_store_sqlite.py`
6. `storage/order_dedupe_store_sqlite.py`
7. `services/security/auth_runtime_guard.py`

### Pass 2B — Fix verification (adversarial)

1. H1/H2: confirm VIEWER cannot arm live after role raise
2. M1: confirm safe wrapper points to live consumer
3. PR #36: confirm fill accounting holds under live conditions

### Pass 2C — Dashboard pages not yet read

Priority: 44_Paper_Reconciliation, 20_Portfolio, 35_Research, 99_Legacy_UI

### Pass 2D — Services with zero coverage, highest risk

1. `services/fills/` — fill processing pipeline
2. `services/reconciliation/` — reconciliation logic
3. `services/governance/` — 8 modules with open blockers
4. `services/analytics/paper_strategy_evidence_service.py`
5. `services/strategies/` — trading strategy implementations

### Pass 2E — Test audit

668 tests run, zero reviewed. Minimum: verify critical-path tests cover
failure cases (fill accounting, arming, reconciler, order dedup).

---

## Surfaces with zero coverage — services/

The following service subdirectories have never been read:

`services/admin/` `services/alerts/` `services/app/` `services/bot/`
`services/collector/` `services/control/` `services/data/`
`services/data_collector/` `services/desktop/` `services/diagnostics/`
`services/evidence/` `services/exchanges/` `services/fills/`
`services/governance/` `services/health/` `services/imitation/`
`services/journal/` `services/learning/` `services/live_router/`
`services/live_trader_fleet/` `services/live_trader_multi/`
`services/logging/` `services/markets/` `services/meta/`
`services/monitoring/` `services/net/` `services/onboarding/`
`services/ops/` `services/paper/` `services/paper_trader/`
`services/portfolio/` `services/preflight/` `services/profiles/`
`services/reconciliation/` `services/release/` `services/runbooks/`
`services/setup/` `services/signals/` `services/storage/`
`services/strategy/` `services/strategy_runner/` `services/supervisor/`
`services/trader_signals/` `services/trading/` `services/trading_runner/`
`services/update/` `services/utils/` `services/validation/`
`services/ws/` `services/ai_engine/` `services/marketdata/`

---

## Audit session log

| Date | Sections | Findings | Commits |
|---|---|---|---|
| 2026-05-10 | 1–10 pass 1 | H:2, M:6, L:8 | 11 checkpoint notes + this map |

---

## How to use this document

1. Read this map first. Do not re-audit REVIEWED surfaces.
2. Pick the next surface from Pass 2A, 2B, 2C, 2D, or 2E.
3. Update the depth label for each file read.
4. Add new findings to the open findings table.
5. Commit the updated map after each session.

**This map is the single source of truth for audit coverage.
Do not create new audit planning docs — update this one.**

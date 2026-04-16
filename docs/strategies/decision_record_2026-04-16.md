# Decision Record — 2026-04-16

## Context

Comprehensive repository audit completed (dual audit: internal + external review).

CryptKeep has completed its build phase for v1. The paper campaign path is runnable, the evidence
pipeline is wired, and promotion gates are machine-checkable. The audit surfaced structural issues
that were fixed before the first sustained paper run.

## Decisions Made

### 1. Removed crypto-trading-ai/ and phase1_research_copilot/ from git tracking

**Reason:** 847K of companion projects with no connection to the active trading system.
They caused false-positive searches, confused CI, and added maintenance surface.
Mock data was migrated to `sample_data/mock-data/`.

### 2. Eliminated services→scripts import layering violation

**Reason:** `services/control/kernel.py` imported from `scripts/check_promotion_gates.py`.
Services must not depend on scripts.
**Fix:** Created `services/control/retirement_checker.py` as the canonical service-layer module.
Both the kernel and the gate checker now import from it.

### 3. Established shared managed-component lifecycle utility

**Reason:** The lock/status/stop/stale-lock pattern was duplicated across tick_publisher,
paper_engine, and strategy_runner with subtle differences. Duplication was causing the same
bug class to appear in multiple services (stale locks on crash).
**Fix:** `services/control/managed_component.py` provides `ManagedComponent` with start, stop,
wait_stopped, is_alive, is_stale, clean_stale_lock, clear_stop_flag.
Adoption by existing services is an incremental path — the utility is available, not mandatory yet.

### 4. Session evidence guaranteed on every run, including zero-trade runs

**Reason:** A zero-trade run provides meaningful evidence: regime state, ops health, system
availability. Previously, a stop_requested campaign produced no evidence.
**Fix:** `run_es_daily_trend_paper.py` wraps `run_campaign()` in a try/finally block. Session
evidence is always written.

### 5. enable_live: false is now the committed default

**Reason:** `enable_live: true` was committed to `config/trading.yaml`. This is a safety risk
because it means anyone who accidentally changes `mode: live` is immediately live-armed.
**Fix:** Committed default is now `enable_live: false`. Live arming happens only at runtime
via the arming flow, never from the committed config.

### 6. CI uses pinned requirements and covers all test files

**Reason:** CI was using unpinned `requirements.txt` (non-reproducible) and a hardcoded
list of test files that missed `test_control_kernel.py`, `test_es_daily_trend.py`, and
`test_evidence_logger.py`.
**Fix:** CI now uses `requirements-pinned.txt` and runs `pytest tests/ -m 'not slow'`.

## Current strategy state

- Strategy: es_daily_trend_v1
- Instrument: BTC/USDT on Coinbase (crypto proxy; ES futures when connector available)
- Stage: paper
- Evidence: no fills yet — paper campaign has not run to completion
- Promotion gate status: 0 pass / 1 fail (no evidence) / 7 unknown

## What was explicitly NOT changed

- `ema_crossover_runner.py` split — reverted in a prior session due to test contract
  incompatibility. The file is 1,126 lines and misnamed. Tracked as debt, not blocking.
- `daily_loss_halt_pct` enforcement — remains declarative in v1. Tracked as a known
  limitation in spec doc and `CURRENT_RUNTIME_TRUTH.md`.
- Candidate pipeline to runner — the pipeline IS wired via `CBP_USE_CANDIDATE_ADVISOR=1`.
  The env var is now controlled by `use_candidate_advisor` in the strategy config.
  Default remains disabled until candidate scans have run.

## Next decision point

After 30 days of paper evidence with 50+ round trips: evaluate promotion to shadow stage
using `make check-gates`. The gate checker will produce a machine-readable verdict.

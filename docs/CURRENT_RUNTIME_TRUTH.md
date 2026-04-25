# Current Runtime Truth

**Last updated:** 2026-04-16  
**Commit:** ff55388 (pre this session) → updated after audit

This document states what is actually runnable right now, without ambiguity.
It is the single authoritative answer to "what is the system doing?"

---

## What is runnable

| Component | Status | Command |
|---|---|---|
| Paper campaign (es_daily_trend_v1) | ✅ Runnable | `make paper-run` |
| Promotion gate check | ✅ Runnable | `make check-gates` |
| Kernel status | ✅ Runnable | `make kernel-status` |
| Tick publisher | ✅ Starts automatically via paper campaign | — |
| Paper engine | ✅ Starts automatically via paper campaign | — |
| Dashboard | ✅ Runnable (separate process) | `make dashboard` |

## What is NOT runnable without additional setup

| Component | Blocker |
|---|---|
| Live trading | `enable_live` must be set at runtime via `live_arming.py`; never in committed config |
| ES futures (actual) | No ES futures connector; running BTC/USDT on Coinbase as crypto proxy |
| Candidate pipeline to runner | Wired into `strategy_selector` but runner reads from config directly |
| Multi-strategy campaigns | v1 is single-strategy only |

## Active strategy

| Field | Value |
|---|---|
| Strategy ID | `es_daily_trend_v1` |
| Instrument | **BTC/USDT on Coinbase** (crypto proxy; ES futures when connector available) |
| Signal | price > 200-day SMA → LONG; price ≤ SMA → FLAT |
| Stage | paper |
| Config | `configs/strategies/es_daily_trend_v1.yaml` |
| Spec | `docs/strategies/es_daily_trend_v1.md` |

The strategy spec is named "ES Daily Trend" because that is the intended instrument.
The actual running instrument in v1 is BTC/USDT. This is documented and intentional.

## Current promotion gate status

```
make check-gates
```

Gates will show UNKNOWN until 30 days of paper evidence accumulate.
The one FAIL gate (no evidence logs) becomes PASS after the first `make paper-run` completes.

## Operational workflow

```bash
# Daily
make paper-run           # runs one campaign (1 hour default)

# Check
make check-gates         # see gate status
make paper-status        # see stage, budget, thresholds
make paper-ps            # see running processes

# Clean up after SIGKILL or crash
make paper-clean-locks   # remove stale lock files

# Stop cleanly
make paper-stop          # send stop signals to all campaign processes

# Promote (when all gates pass)
make promote-strategy STRATEGY_ID=es_daily_trend_v1
```

## What requires manual action

- Kill switch test: after running, set `kill_switch_tested=True` in a session log
- Daily loss halt test: temporarily set `daily_loss_halt_pct: 0.001` in config, verify halt fires, restore
- `baseline_slippage_pct`: currently 0.10% (estimated); replace with measured p50 after 50 fills

## Known limitations (v1)

1. `daily_loss_halt_pct` in config is declarative, not the runtime enforcement source. Actual enforcement is in `services/risk/live_risk_gates_phase82.py`.
2. Candidate pipeline is built but not wired to the runner — runner still reads strategy from config.
3. `ema_crossover_runner.py` is the runtime for all strategies despite its name.
4. `crypto-trading-ai/` and `phase1_research_copilot/` are companion projects in the repo root — not part of the active trading system.

## Reading the repo layout

`build/`, `dist/`, `data/`, `logs/`, and `attic/` are gitignored and will not appear
when reading the tracked repo structure. To see only tracked content:

    tree -L 2 --gitignore

This hides build output, runtime state, logs, and companion project directories
that are present locally but not tracked by git.

## Out-of-scope stubs

`src-tauri/` is a scaffolding stub for a future Tauri desktop wrapper (3 files:
`Cargo.toml`, `tauri.conf.json`, `src/main.rs`). It has zero runtime role and is
not part of the active operator path. Removal is gated on updating the four doc
references that name it: docs/REPO_LAYOUT.md, docs/GOLDEN_PATH.md,
docs/HANDOFF.md, docs/INSTALL.md.

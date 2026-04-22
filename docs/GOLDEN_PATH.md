# Golden Path

One page. What runs, in what order, where evidence goes, what is optional.

## The product

CryptKeep is a safety-first paper and guarded-live trading runtime with evidence,
reconciliation, promotion gates, and operator controls.

## The canonical runtime

```
make paper-run-short          # dev/test — 60s, sample OHLCV, proves the path
make paper-run                # production — 3600s, live OHLCV from exchange
make check-gates              # promotion gate status (30-day evidence required)
make paper-status             # stage, budget, thresholds
make paper-stop-now           # emergency stop
```

## What runs inside make paper-run

1. `run_es_daily_trend_paper.py` — orchestrator (parent process)
2. `run_tick_publisher.py` — market data snapshot publisher
3. `run_paper_engine.py` — simulated order execution
4. `run_strategy_runner.py` → `ema_crossover_runner.py` — signal evaluation loop

Signal source: `public_ohlcv_1d` → fetches daily OHLCV → calls `es_daily_trend.signal_from_ohlcv()`

## Where evidence goes

All canonical evidence: `.cbp_state/data/evidence/es_daily_trend_v1/`

| File | Written when |
|---|---|
| `session_YYYY-MM-DD.jsonl` | Campaign start (phase=start) and end (phase=end) |
| `signal_YYYY-MM-DD.jsonl` | Each bar evaluated by the strategy |
| `fill_YYYY-MM-DD.jsonl` | Each confirmed fill (capped_live stage only) |
| `order_YYYY-MM-DD.jsonl` | Each order submitted (capped_live stage only) |

Legacy artifact (stale, ignore until fills exist): `.cbp_state/data/strategy_evidence/strategy_evidence.latest.json`

See `docs/EVIDENCE_MODEL.md` for full explanation.

## Promotion gates

Read by: `scripts/check_promotion_gates.py` from the canonical JSONL evidence directory.

Gates for paper → shadow promotion:
- 30 calendar days of operation
- 50+ completed round trips
- Expectancy within 30% of backtest
- No critical operational bugs
- Kill switch tested
- All evidence logs complete

## What is core vs optional

**Core** (required for the paper trading loop):
- `services/control/` — stage machine, kernel, allocator
- `services/strategies/` — signal logic, evidence logger, registry
- `services/execution/` — paper engine, order routing
- `services/analytics/` — campaign orchestration, evidence artifacts
- `services/risk/` — live risk gates, kill switch
- `services/security/` — auth, runtime guard
- `services/admin/` — kill switch, health
- `dashboard/` — operator visibility
- `config/` — system configuration
- `configs/strategies/` — strategy-specific runtime config

**Optional** (release/packaging surfaces — not needed to run the runtime):
- `packaging/` — Briefcase desktop build
- `desktop/` — desktop app shell
- `src-tauri/` — Tauri native wrapper
- `installers/` — OS-specific installers

**Archived** (not actively maintained):
- `crypto-trading-ai/` — earlier sidecar workspace
- `trade-ai-mvp/` — earlier prototype
- `phase1_research_copilot/` — research tooling

## The one regression test to run after any change to the signal path

```bash
python -m pytest tests/test_es_signal_regression.py -v
```

5 tests covering: OHLCV depth, signal_from_ohlcv evidence write, required fields,
campaign signal_source config, and _required_history bar count.

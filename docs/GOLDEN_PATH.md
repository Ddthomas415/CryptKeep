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

For the complete operator command map, use `scripts/SCRIPTS.md`. This Golden
Path intentionally stays narrow: it lists the current daily paper-campaign path,
while `scripts/SCRIPTS.md` classifies the full root script inventory as daily
operator commands, diagnostics, emergency controls, research tools, release
helpers, desktop surfaces, or specialized live-adjacent commands.

For dashboard/operator launches,
`scripts/run_paper_strategy_evidence_collector.py --daily-loop --detach` is the
managed persistent background path. The command returns after verifying the
detached collector PID, writes its process output under the selected
`CBP_STATE_DIR`, and records one new session day per new UTC day. Omit
`--detach` only when intentionally running the daily loop in the foreground.
For `sma_200_trend`, the managed collector uses `public_ohlcv_1d` so evidence is sourced
from daily public OHLCV instead of synthetic tick-derived bars.

After a host restart, check all accepted paper campaigns with:

```
make status-paper-campaigns
```

If one or more collectors are not alive, restore only the missing processes
with:

```
make restore-paper-campaigns
```

The command reads `configs/paper_evidence_campaigns.json`, preserves each
campaign's isolated `CBP_STATE_DIR`, and delegates startup to the authoritative
collector `--daily-loop --detach` path. It checks status before launch, so
repeated restore calls do not create duplicate collectors. Automatic OS-login
startup is intentionally not enabled; starting financial background jobs
requires this explicit operator action.

Public-OHLCV campaign health is fail-closed. A collector may remain alive while
reporting `ok=false`, `status=failed`, and `reason=no_public_ohlcv`. The
canonical manifest permits two attempts per UTC day; see
`docs/PAPER_CAMPAIGN_RECOVERY.md`.

## What runs inside make paper-run

1. `run_es_daily_trend_paper.py` — orchestrator (parent process)
2. `run_tick_publisher.py` — market data snapshot publisher
3. `run_paper_engine.py` — simulated order execution
4. `run_strategy_runner.py` → `ema_crossover_runner.py` — signal evaluation loop
5. `run_paper_sim_monitor.py` — auto-supervised read-only runtime monitor

Signal source: `public_ohlcv_1d` → fetches daily OHLCV → calls
`es_daily_trend.signal_from_ohlcv()` with explicit `public_ohlcv` provenance.
Unlabeled OHLCV calls may compute a signal, but they do not write promotion
JSONL evidence.

The paper sim monitor is operator-facing only. It does not submit orders or mutate runtime state.
It summarizes active strategy, fills, round trips, and recommendation state for the current managed campaign.
`current_window_realized_pnl` is reported only when the campaign service
provides an explicit window delta. When unavailable, it is `null` and the
summary says `unavailable`; lifetime position and equity realized PnL remain in
separate total fields.
It also surfaces paper-stage promotion threshold progress (30 days / 10 round trips) so a local
`recommendation=enough_evidence` event is not confused with full promotion readiness.
Managed paper campaigns also auto-seed default paper-sim watches:
- `next_fill`
- `position_closed`
- `campaign_completed`
- `investigate`

When one of those watches fires, the monitor writes JSON/Markdown reports under `.cbp_state/runtime/ai_reports/`
and attempts a local macOS desktop notification.
Operators can register or delete local watches from the Operations dashboard without using the CLI.

A daily paper campaign can complete without order/fill records when the strategy
does not trade. In that case the promotion gate treats signal plus session logs
as a complete no-trade evidence window; order/fill evidence is required once a
trade record appears.

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

Read by: `scripts/check_promotion_gates.py` from two canonical evidence surfaces:
JSONL for latest-window health and per-fill provenance qualification, then
`.cbp_state/data/trade_journal.sqlite` for prices, fees, completed round trips,
and realized expectancy restricted to those qualified order IDs. Raw journal
history remains diagnostic and does not count when either trade leg lacks the
configured provenance.

Gates for paper → shadow promotion:
- 30 calendar days of operation
- 10+ completed round trips
- Expectancy within 30% of backtest
- No critical operational bugs
- Kill switch tested within the configured cadence (`ops.kill_switch_test_frequency`, weekly by default)
- All evidence logs complete

The older 50+ round-trip target is retained as a stronger research-confidence floor before
larger live-capital decisions. It is not the paper → shadow/sandbox blocker for this
slow-turnover daily strategy.

Shadow readiness can be inspected before promotion:

```bash
./.venv/bin/python scripts/check_promotion_gates.py --stage shadow --json
```

The `--stage` option selects the gate report; it does not promote the strategy
or relabel existing evidence. The report exposes both `stage` and
`current_stage`. Until the persisted stage is `shadow`, all shadow gates remain
unknown with `evidence_scope.status=not_started`. After promotion, only records
explicitly stamped `_stage=shadow` and logged on or after that stage's
`since_ts` count toward shadow gates, schema checks, provenance, slippage, and
retirement checks. `provenance_all_time` remains diagnostic and does not make
the shadow gate pass or fail.

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

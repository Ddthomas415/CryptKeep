# Evidence Model

Three evidence surfaces exist in this repo. This document defines which one is
authoritative for each promotion question.

Executable guard: `tests/test_evidence_model_guard.py` pins the authority
boundaries in this document. If a future change moves promotion authority,
paper-history qualification, or leaderboard semantics, update that test and this
document together.

## Canonical: JSONL per-record evidence

**Location:** `.cbp_state/data/evidence/<strategy_id>/`

**Written by:** `services/strategies/evidence_logger.py` (EvidenceLogger)

**Read by:**
- `scripts/check_promotion_gates.py` — promotion schema, provenance, and log completeness checks
- `services/strategies/campaign_summary.py` — campaign summary reporting

**Record types per file:**
- `signal_YYYY-MM-DD.jsonl` — one record per bar evaluated (price, sma_200, regime_flag, ...)
- `session_YYYY-MM-DD.jsonl` — campaign start (phase=start) and end (phase=end)
- `fill_YYYY-MM-DD.jsonl` — one record per confirmed fill (fill_price, slippage_pct, pnl_usd)
- `order_YYYY-MM-DD.jsonl` — one record per order submitted
- `drawdown_YYYY-MM-DD.jsonl` — one record per drawdown event

**Schema:** defined in `configs/strategies/es_daily_trend_v1.yaml` under `evidence.required_*_fields`

**Promotion use:** JSONL is authoritative for proving that required evidence logs
exist, have valid schema, and carry market-data provenance. The promotion
provenance gate evaluates the latest dated evidence window for current collector
health. Separately, every fill used for round-trip or expectancy thresholds must
carry the configured source, timeframe, venue, symbol, and explicit non-sample
mode. Fresh latest-window provenance does not retroactively qualify older
unstamped fills.

The latest-window evidence-presence gate requires signal and session records on
every completed campaign window. Order and fill records are required when either
trade record type appears in that latest window. A no-trade window with signal
and session records is valid evidence collection, not a missing-log failure.

Signal calls with unlabeled OHLCV are not promotion evidence. The
`es_daily_trend` signal adapter returns the computed signal but does not write a
JSONL signal record unless the caller stamps a recognized source such as
`public_ohlcv` or `sample_ohlcv`. This prevents research/backtest calls with
unknown provenance from contaminating the promotion gate.

---

## Canonical: persisted paper fill history

**Location:** `.cbp_state/data/trade_journal.sqlite`

**Read by:**
- `services/analytics/strategy_feedback.py` — strategy-level paper-history summary
- `scripts/check_promotion_gates.py` — paper-stage round-trip count, realized expectancy, and retirement expectancy reporting

**Promotion use:** JSONL first identifies the order IDs whose entry and exit
fills both match the configured provenance contract. The journal then supplies
the immutable prices, quantities, and fees for only those qualified order IDs.
`check_promotion_gates.py --json` exposes qualified metrics under
`paper_history`; unqualified persisted history remains visible under
`paper_history.all_history` for diagnostics but cannot advance a promotion gate.
The shared `paper_promotion_progress` output also includes a structured
`qualification_explanation` and appends that explanation to its operator-facing
summary whenever all-history round trips are excluded, evidence fills fail the
provenance contract, or qualified fills do not form a complete round trip. This
is reporting only and does not retroactively qualify historical records.
The qualification payload also exposes first/latest provenance-qualified fill
timestamps, first/latest completed qualified round-trip close timestamps, and
date counts for unqualified fills so operators can see when clean gate-counting
began and which historical dates remain diagnostic-only.

---

## Legacy: Leaderboard artifact

**Location:** `.cbp_state/data/strategy_evidence/strategy_evidence.latest.json`

**Written by:** `services/backtest/evidence_cycle.py` via `run_campaign()` in
`paper_strategy_evidence_service.py` — only when fills or closed trades are present.

**Status:** This artifact is not the direct promotion gate source. It is a
historical leaderboard for comparing strategy performance across synthetic
windows and supplemental paper history.

`run_campaign()` and `load_runtime_status()` return this path in `result["evidence"]`
for backward compatibility. The canonical JSONL summary is in
`result["jsonl_evidence"]`.

---

## Operator rule

Use `scripts/check_promotion_gates.py --json` as the current promotion gate
summary. Interpret the sources this way:

1. `paper_history` answers how many provenance-qualified target-strategy paper
   fills and round trips exist, and what realized expectancy they produced.
   `paper_history.all_history` preserves the unfiltered descriptive ledger.
2. `schema` and `provenance` answer whether the JSONL evidence stream is complete
   and attributable to non-sample market data. `provenance`, session health, and
   evidence-log presence gates use the latest dated evidence window; kill-switch
   testing must be current within `ops.kill_switch_test_frequency`;
   `provenance_all_time` is diagnostic history.
3. `strategy_evidence.latest.json` is comparison context, not the final gate.

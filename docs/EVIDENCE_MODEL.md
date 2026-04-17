# Evidence Model

Two evidence systems exist in this repo. This document defines which is canonical.

## Canonical: JSONL per-record evidence

**Location:** `.cbp_state/data/evidence/<strategy_id>/`

**Written by:** `services/strategies/evidence_logger.py` (EvidenceLogger)

**Read by:**
- `scripts/check_promotion_gates.py` — promotion decision engine
- `services/strategies/campaign_summary.py` — campaign summary reporting

**Record types per file:**
- `signal_YYYY-MM-DD.jsonl` — one record per bar evaluated (price, sma_200, regime_flag, ...)
- `session_YYYY-MM-DD.jsonl` — campaign start (phase=start) and end (phase=end)
- `fill_YYYY-MM-DD.jsonl` — one record per confirmed fill (fill_price, slippage_pct, pnl_usd)
- `order_YYYY-MM-DD.jsonl` — one record per order submitted
- `drawdown_YYYY-MM-DD.jsonl` — one record per drawdown event

**Schema:** defined in `configs/strategies/es_daily_trend_v1.yaml` under `evidence.required_*_fields`

**This is the only evidence that gates promotion.** `check_promotion_gates.py` reads
exclusively from this directory.

---

## Legacy: Leaderboard artifact

**Location:** `.cbp_state/data/strategy_evidence/strategy_evidence.latest.json`

**Written by:** `services/backtest/evidence_cycle.py` via `run_campaign()` in
`paper_strategy_evidence_service.py` — only when fills or closed trades are present.

**Last updated:** 2026-03-19 (stale — no fills have occurred at paper stage)

**Status:** This artifact will remain stale until capped_live stage produces fills.
It is **not** used for promotion decisions. It is a historical leaderboard for
comparing strategy performance after fills exist.

`run_campaign()` returns this path in `result["evidence"]` for backward compatibility.
The JSONL path is in `result["jsonl_evidence"]`.

---

## Migration plan

Once the paper stage accumulates 50+ filled round trips, the leaderboard artifact
will become meaningful again. At that point:
1. Verify `evidence_cycle.py` reads from the JSONL fills (not the SQLite paper engine)
2. Update `_latest_strategy_evidence_artifacts()` to reference the JSONL directory
3. Retire the `strategy_evidence.latest.json` path as the primary artifact

Until then: **use the JSONL directory. Ignore the leaderboard artifact.**

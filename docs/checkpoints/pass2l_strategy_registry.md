# Pass 2L — Strategy Registry

**Date:** 2026-05-10
**Pass:** 2L
**Status:** COMPLETE — H6 confirmed; scope corrected after recheck

---

## Recheck performed

After initial commit, full evidence flow was traced:

1. `es_daily_trend_pipeline.py:18` — `STRATEGY_ID = "es_daily_trend_v1"`
2. Pipeline creates intents with `strategy_id="es_daily_trend_v1"` (line 122)
3. `paper_runner.py` records fills to `journal_fills` with `strategy_id=it.get("strategy_id")` → `"es_daily_trend_v1"`
4. `evidence_cycle._normalize_strategy_name("es_daily_trend_v1")` returns `None`
5. Fills go to `unmapped_strategy_ids` and are skipped in `grouped`
6. `report_supervised_soak_status.py` does NOT use `evidence_cycle` — confirmed by grep

---

## SHOWN findings

### Finding 1 — Unknown strategy falls back to `ema_cross` silently (Medium)

```python
if name not in SUPPORTED:
    name = "ema_cross"
```

A config typo silently runs EMA cross. No log. `"unknown_strategy"` return is dead code.

---

### Finding 2 — `sma_200_trend` vs `es_daily_trend_v1` strategy_id mismatch (High)

Two separate IDs used across the pipeline:

| Layer | ID used |
|---|---|
| Config strategy.name | `sma_200_trend` |
| Registry key | `sma_200_trend` |
| `es_daily_trend_pipeline.STRATEGY_ID` | `es_daily_trend_v1` |
| Intent `strategy_id` field | `es_daily_trend_v1` |
| `journal_fills.strategy_id` | `es_daily_trend_v1` |
| `_normalize_strategy_name()` result | `None` (unmapped) |
| EvidenceLogger JSONL files | `es_daily_trend_v1/` |

`_normalize_strategy_name` only recognizes:
`ema_cross`, `mean_reversion_rsi`, `breakout_donchian`, `momentum`.

**Scope (corrected after recheck):**

- **Soak gate (Section 4.1):** NOT affected. `report_supervised_soak_status.py`
  checks service uptime and incident counts only. Does not use `evidence_cycle`.
  The 168-hour soak will still pass Section 4.1.

- **Evidence promotion gate:** AFFECTED. When `evidence_cycle.load_paper_history_evidence()`
  is run after the soak to evaluate promotion readiness, fills under
  `strategy_id="es_daily_trend_v1"` will appear in `unmapped_strategy_ids` and
  be skipped. The promotion gate will show `insufficient` evidence even though
  168 hours of paper fills exist.

- **JSONL evidence files:** NOT affected. EvidenceLogger writes to
  `data/evidence/es_daily_trend_v1/` using the correct STRATEGY_ID. These are
  used by `stage_summary()` and `budget_summary()` for the `--check-promotion`
  command in `run_es_daily_trend_paper.py`.

**Fix:** Add to `_normalize_strategy_name` in `evidence_cycle.py`:
```python
if "sma_200" in text or "es_daily_trend" in text or "daily_trend" in text:
    return "sma_200_trend"
```

Must be done before any promotion gate evaluation using `load_paper_history_evidence`.

---

### Finding 3 — `trade_enabled` gate short-circuits correctly (Strength)

---

### Finding 4 — No catch around `fn()` calls (Noted)

Strategy exceptions propagate to pipeline `run_once()`. Visible as `run_once_failed`.

---

### Finding 5 — Registry params match strategy defaults (Strength)

`sma_200_trend` handler passes `sma_period=200`, `atr_period=20` matching strategy defaults.

---

## Summary

| Finding | Severity |
|---|---|
| Unknown strategy silent fallback | Medium |
| `es_daily_trend_v1` unmapped in evidence_cycle | **High** |
| `trade_enabled` gate | **Strength** |
| No catch around fn() | Noted |
| Registry params match defaults | **Strength** |

**H6 scope:** Soak gate (Section 4.1) is safe. Promotion gate evaluation is affected.

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2L
**H6 fix priority:** Before promotion gate evaluation, not before soak completion

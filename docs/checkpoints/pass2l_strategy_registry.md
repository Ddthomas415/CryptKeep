# Pass 2L — Strategy Registry

**Date:** 2026-05-10
**Pass:** 2L
**Status:** COMPLETE— H6 confirmed critical

---

## SHOWN findings

### Finding 1 — Unknown strategy name silently falls back to `ema_cross` (Medium)

```python
name = str(st.get('name', 'ema_cross')).strip()
if name not in SUPPORTED:
    name = 'ema_cross'
```

A config typo silently runs EMA cross with no error, warning, or log.
The `'unknown_strategy'` return at the bottom is dead code -- the fallback
prevents any unknown name from reaching it.

---

### Finding 2 — `sma_200_trend` registry key vs `es_daily_trend_v1` STRATEGY_ID (High)

Registry key: `'sma_200_trend'`
EvidenceLogger STRATEGY_ID: `'es_daily_trend_v1'`

Fills are filed under `'es_daily_trend_v1'`. `_normalize_strategy_name` in
`evidence_cycle.py:110` only recognizes:
`ema_cross`, `mean_reversion_rsi`, `breakout_donchian`, `momentum`.

`_normalize_strategy_name('es_daily_trend_v1')` returns `None`.

Fills go to `unmapped_strategy_ids`. The evidence cycle's leaderboard and
`_evidence_status_for_row` do NOT count unmapped fills toward any strategy's
promotion eligibility.

**THE ENTIRE 168-HOUR SOAK EVIDENCE IS IN `unmapped_strategy_ids` AND IS
INVISIBLE TO THE PROMOTION GATE.**

Fix: add to `_normalize_strategy_name`:
```python
if 'sma_200' in text or 'es_daily_trend' in text:
    return 'sma_200_trend'
```

Must be done before any promotion gate evaluation.

---

### Finding 3 — `trade_enabled` gate short-circuits correctly (Strength)

```python
if not bool(st.get('trade_enabled', True)):
    return {'ok': True, 'action': 'hold', 'reason': 'trade_disabled', ...}
```

---

### Finding 4 — No catch around `fn()` calls (Noted)

Strategy exceptions propagate to pipeline `run_once()`. Visible in soak
incident log as `run_once_failed` entries.

---

### Finding 5 — Registry params match strategy defaults (Strength)

`sma_200_trend` handler passes `sma_period=200`, `atr_period=20` matching
strategy defaults. Config overrides flow correctly.

---

## Summary

| Finding | Severity |
|---|---|
| Unknown strategy falls back to ema_cross silently | Medium |
| sma_200_trend key vs es_daily_trend_v1 ID mismatch | **High** |
| trade_enabled gate short-circuits | **Strength** |
| No catch around fn() calls | Noted |
| Registry params match strategy defaults | **Strength** |

---

## Updated High findings

| # | Finding |
|---|---|
| H4 | Governance enforcement dead code |
| H5 | resume_if_safe disconnected from config |
| H6 | **soak evidence invisible to promotion gate** |
| H1 | VIEWER partial arming state |
| H2 | VIEWER writes API keys |
| H3 | VIEWER corrupts paper state |

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2L
**URGENT:** H6 fix needed before promotion gate evaluation

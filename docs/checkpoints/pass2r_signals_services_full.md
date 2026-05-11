# Pass 2R — Signals Services Full Audit

**Date:** 2026-05-10
**Pass:** 2R — all 13 files in services/signals/
**Status:** COMPLETE

---

## SHOWN findings

### Finding 1 — webhook_server.py is an unaudited external signal ingestion surface (High)

HTTP server accepting POST /signal or /signals. HMAC-SHA256 validation.
If no secret: all requests rejected. If secret configured: HMAC required.
Writes to SignalInboxSQLite.

Not used in current soak. Represents external attack surface never examined
in Pass 1. Security of external signals entering the intent queue from an
unauthenticated source was not previously verified.

No enforcement that the shared secret is non-trivial.

---

### Finding 2 — auto_route_to_paper defaults False (Strength)

External signals NOT auto-routed by default. Operator must set explicitly.
Fail-safe.

---

### Finding 3 — Empty allowed lists permit all sources (Shown)

```python
if not allowed_list:
    return True   # empty = allow all
```

Operator who enables auto_route_to_paper without configuring allowed_sources,
allowed_authors, allowed_symbols would route all signals from any source.

---

### Finding 4 — ALLOWED_STRATEGIES does not include active soak strategy (Shown)

candidate_advisor ALLOWED_STRATEGIES frozenset:
pullback_recovery, mean_reversion_rsi, momentum, breakout_donchian, ema_cross.

Neither 'sma_200_trend' nor 'es_daily_trend_v1' present. Advisor can never
recommend the active soak strategy.

---

### Finding 5 — candidate_store uses atomic_write (Strength)

Consistent with established pattern.

---

### Finding 6 — signal_library pure computation with safe wrappers (Strength)

Standard indicators (SMA, RSI). _safe() and _clamp() on all inputs.
No network calls.

---

## What was missed in Pass 1

services/signals/ had zero coverage. webhook_server.py is an external attack
surface — external signals can route to paper intents — that was never examined.
This is an example of the gap your question identified.

---

## services/signals/ FULLY COVERED (13 of 13 files)

---

## Summary

| Finding | Severity |
|---|---|
| webhook_server external ingestion — previously unaudited | **High** |
| auto_route_to_paper defaults False | **Strength** |
| Empty allowed lists permit all sources | Shown |
| ALLOWED_STRATEGIES missing soak strategy | Shown |
| candidate_store atomic_write | **Strength** |
| signal_library pure computation | **Strength** |

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2R
**Next:** services/execution/ remaining 68 files

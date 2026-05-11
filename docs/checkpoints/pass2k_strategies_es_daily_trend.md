# Pass 2K — Active Soak Strategies

**Date:** 2026-05-10
**Pass:** 2K — full read of es_daily_trend.py
**Status:** COMPLETE

---

## SHOWN findings

### Finding 1 — Signal logic is simple, correct, and deterministic (Strength)

```python
def compute_signal(closes, *, period=200):
    if len(closes) < period: return 'flat'
    sma = sum(closes[-period:]) / period
    return 'long' if closes[-1] > sma else 'flat'
```

Two outcomes only: 'long' or 'flat'. `compute_stop` explicitly raises
`ValueError` for non-long sides. Long/flat constraint enforced at both
signal logic and stop calculation levels.

---

### Finding 2 — ATR regime filter has 4 explicit entry gates (Strength)

| Regime | ATR ratio | entry_allowed | size_factor |
|---|---|---|---|
| `high_vol` | > 2.50 | False | 0.5 |
| `trending` | >= 0.80 | True | 1.0 |
| `borderline` | 0.60-0.80 | True | 0.75 |
| `chop` | < 0.60 | False | 0.0 |
| `insufficient_data` | N/A | False | 0.0 |

`action = 'buy'` only when `signal == 'long'` AND `reg['entry_allowed']`.
High volatility and choppy markets both block entries.

---

### Finding 3 — Position sizing correctly caps on notional and stop distance (Strength)

Sizing derived from capital_at_risk (0.5% default), capped by max notional
(10% default). Zero stop distance returns `contracts: 0` with explanatory note.

---

### Finding 4 — `CAPPED_LIVE` stage enforces 1-contract maximum (Strength)

```python
if get_current_stage(STRATEGY_ID) == Stage.CAPPED_LIVE:
    size['contracts'] = min(size['contracts'], 1)
```

Correct deployment gate for initial live stage.

---

### Finding 5 — Evidence logging is non-blocking and comprehensive (Strength)

All evidence logging wrapped in try/except. Evidence logged even on
'insufficient_history' returns. A broken logger never affects signal output.

---

### Finding 6 — ATR zero-volatility defaults to 'trending' (Noted)

```python
atr_ratio = current_atr / rolling_avg if rolling_avg > 0 else 1.0
```

Flat price history -> rolling_avg=0 -> ratio=1.0 -> 'trending' -> entry_allowed.
Degenerate edge case; low probability in real markets.

---

### Finding 7 — OHLCV row length not validated (Noted)

```python
closes = [float(row[4]) for row in ohlcv]
```

No check that `len(row) >= 5`. Malformed row raises `IndexError`; caught
by caller's broad exception handler but would produce a failed signal.

---

## Summary

| Finding | Severity |
|---|---|
| Signal logic deterministic | **Strength** |
| ATR regime 4-gate filter | **Strength** |
| Sizing: capital at risk + notional cap | **Strength** |
| CAPPED_LIVE 1-contract max | **Strength** |
| Evidence logging non-blocking | **Strength** |
| ATR zero-vol defaults to trending | Noted |
| OHLCV row length not validated | Noted |

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2K
**Next:** `strategy_registry.py` (signal dispatch) or remediation for H4/H5

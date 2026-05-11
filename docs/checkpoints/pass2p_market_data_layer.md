# Pass 2P — Market Data Layer

**Date:** 2026-05-10
**Pass:** 2P — services/market_data/ critical path + signal_replay.py
**Status:** COMPLETE for critical path; 22 of 29 files NOT_AUDITED

---

## SHOWN findings

### Finding 1 — fetch_ohlcv creates new exchange connection on every call (Medium)

```python
ex = make_exchange(v, {'apiKey': None, 'secret': None}, enable_rate_limit=True)
try:
    return ex.fetch_ohlcv(sym, **kwargs)
finally:
    ex.close()
```

New CCXT object created and closed on every `fetch_ohlcv` call. No pooling,
no keep-alive. Low risk for daily OHLCV bars (not called on every tick in
practice) but pays full SSL handshake cost each call.

---

### Finding 2 — No explicit timeout; no retry in fetch_ohlcv (Medium)

`make_exchange` does not set `timeout` in CCXT config. CCXT default timeout
(commonly 10s) applies. A single timeout propagates immediately to
`run_once_failed`. No backoff, no retry at the fetch level.

**This is the confirmed root cause of all 3 soak incidents:**
1. fetch_ohlcv calls CCXT with no explicit timeout
2. Coinbase slow/unreachable
3. CCXT default timeout fires → NetworkError
4. Propagates to run_once_failed → pipeline.log → alert monitor
5. Next poll cycle: Coinbase back → recovery

All 3 recovered correctly. Recovery is at the pipeline level, not fetch level.

---

### Finding 3 — Null credentials correct for public endpoint (Strength)

`{'apiKey': None, 'secret': None}` is correct for `fetch_ohlcv` (public API).
`require_binance_allowed` still fires regardless of credentials.

---

### Finding 4 — Venue alias map has only 5 entries (Shown)

```python
VENUE_ALIASES = {'gate.io': 'gateio', 'gate': 'gateio', 'gateio': 'gateio',
                 'binance': 'binance', 'coinbase': 'coinbase', 'coinbasepro': 'coinbase'}
```

Unsupported venue strings pass through as-is to CCXT. Not pre-validated.
CCXT raises `ExchangeNotFound` for unknown IDs.

---

### Finding 5 — Local snapshot returns [] when absent — callers handle correctly (Strength)

Local cache miss returns []. `signal_from_ohlcv` handles: empty/short ohlcv
returns `action: 'hold'`. Safe degradation confirmed end-to-end.

---

### Finding 6 — regime_detector ATR formula correct (Strength)

```python
tr = max(h - l, abs(h - pc), abs(l - pc))
```

Standard True Range. `_safe()` wrapper on all float conversions.
Pure computation, no network calls.

---

## Not audited (22 of 29 files)

alternative_data.py, coinbase_movers.py, composite_ranker.py,
correlation_inputs.py, correlation_matrix.py, cross_exchange_discrepancy.py,
market_intelligence.py, multi_venue_view.py, order_book_intelligence.py,
poller_service.py, ranking_presets.py, rotation_engine.py,
run_price_feeds.py, symbol_normalize.py, volume_surge_detector.py and others.

These are intelligence/analytics sources — not on the critical signal path.

---

## Summary

| Finding | Severity |
|---|---|
| New exchange connection on every fetch | Medium |
| No explicit timeout; no retry | Medium |
| Null credentials correct for public endpoint | **Strength** |
| Venue alias map 5 entries | Shown |
| Local snapshot [] on miss — handled correctly | **Strength** |
| regime_detector ATR correct | **Strength** |

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for critical market data path
**Next:** services/risk/ remaining 19 files, services/signals/, or execution remaining

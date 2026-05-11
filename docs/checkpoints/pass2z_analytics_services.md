# Pass 2Z — Analytics Services Full Audit

**Date:** 2026-05-10
**Pass:** 2Z — all 15 files in services/analytics/
**Status:** COMPLETE

---

## SHOWN findings

### Finding 1 — Legacy vs canonical evidence paths documented (Strength)

latest_leaderboard_artifact() explicitly labeled 'LEGACY evidence system'.
Canonical path is jsonl_evidence_summary(). Consistent with Pass 2E finding:
EvidenceLogger writes to JSONL under data/evidence/{strategy_id}/.

---

### Finding 2 — Fourth strategy name normalization in strategy_feedback (Medium)

Four separate implementations of strategy name normalization:
1. evidence_cycle.py -- maps ema_cross, mean_reversion_rsi, breakout_donchian
2. paper_strategy_evidence_service.py -- its own mapping
3. strategy_feedback.py -- its own mapping
4. strategy_registry.py -- registry keys

H6 arose from inconsistency in evidence_cycle's normalizer. strategy_feedback
may have the same gap -- if it maps 'es_daily_trend_v1' differently, feedback
scores won't be attributed to the active soak strategy.

---

### Finding 3 — equity_curve no NaN protection on pnl values (Noted)

```python
balance += f.get('pnl', 0.0)   # handles None but not NaN/inf strings
```

Phase IG comment. If fill records contain 'nan' or 'inf' strings, equity
curve becomes corrupted. Not on live trading path.

---

### Finding 4 — component_is_alive IDLE-on-crash false-positive (Noted)

os.kill(pid, 0) confirms process exists, not that it's active.
Same pattern as watchdog.py (Pass 2N). Low impact for paper campaign.

---

### Finding 5 — paper_loss_replay uses no-timeout fetch_ohlcv (Noted)

Same fetch_ohlcv with no explicit timeout confirmed in Pass 2P.
Acceptable for replay analysis (not on live path).

---

### Finding 6 — paper_pnl injectable store for testing (Strength)

db = store or PaperTradingSQLite() -- correct testability pattern.

---

### Finding 7 — strategy_feedback thresholds separate from evidence gate (Noted)

STRATEGY_FEEDBACK_MIN_CLOSED_TRADES = 3 vs evidence gate minimum.
Separate thresholds could fire feedback before promotion eligibility.

---

## services/analytics/ FULLY COVERED (15 of 15)

---

## Summary

| Finding | Severity |
|---|---|
| Legacy vs canonical evidence documented | **Strength** |
| Fourth strategy name normalization | Medium |
| equity_curve no NaN on pnl | Noted |
| component_is_alive IDLE false-positive | Noted |
| paper_loss_replay no-timeout fetch | Noted |
| paper_pnl injectable store | **Strength** |
| strategy_feedback thresholds separate | Noted |

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2Z
**Next:** services/ai_copilot/ remaining 9 files, or storage/ critical stores

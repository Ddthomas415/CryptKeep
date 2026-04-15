# Strategy Spec: ES Daily Trend v1

**Parent framework:** `docs/DECISION_FRAMEWORK.md`  
**Control kernel:** `docs/CONTROL_KERNEL.md`  
**Stage:** Paper  
**Last reviewed:** 2026-04-14

This document fills in the blanks the framework intentionally leaves open.
It is the first concrete child of the decision framework.

---

## 1 — Strategy definition

| Field | Value |
|---|---|
| **Instrument** | ES (S&P 500 front-month futures) or SPY as proxy |
| **Timeframe** | Daily bars (close-to-close) |
| **Signal** | Price > 200-day SMA → LONG; price ≤ 200-day SMA → FLAT |
| **Direction** | Long/flat only. No short until this version is validated. |
| **Entry** | Next open after close crosses above 200-day SMA |
| **Exit** | Next open after close crosses below 200-day SMA |
| **Stop** | Hard stop: 2× ATR(20) below entry price |
| **Hold period** | Days to months — this is a slow-turnover system |
| **Universe** | One instrument. No expansion until paper/shadow gates pass. |

**Why this strategy:** It is simple enough to hold in one sentence, liquid enough that execution is not the edge, and has enough historical precedent to set realistic expectations. The goal is to validate the full framework pipeline — not to find a novel alpha source.

---

## Known limitations (v1)

- `daily_loss_halt_pct` in the config is a **declarative target**, not the runtime enforcement source in v1. Actual daily halt is enforced by `services/risk/live_risk_gates_phase82.py` using an absolute USD value. Keep these consistent manually until directly wired.
- `ops.baseline_slippage_pct: 0.10` is an estimate. Replace with measured median fill slippage after the first 50 fills.

## 2 — Regime filter

| Parameter | Value | Rationale |
|---|---|---|
| Regime indicator | 60-day ATR ratio (current ATR / 60-day avg ATR) | Simple, slow, explainable |
| Trending regime | ATR ratio ≥ 0.8 | Sufficient momentum to support trend signal |
| Range/chop override | ATR ratio < 0.6 for 5+ consecutive days | Likely whipsaw environment — no new entries |
| High vol override | ATR ratio > 2.5 | Disorderly market — reduce to half size or pause |
| Regime check frequency | Daily at bar close | Matches signal frequency |

**Rule:** No new entry if regime is flagged as chop or disorderly. Existing position may be held but not added to.

---

## 3 — Sizing and risk

| Parameter | Value |
|---|---|
| Capital at risk per trade | 0.5% of total capital at hard stop level |
| Position size formula | `(capital × 0.005) / (entry_price − stop_price)` |
| Max position notional | 10% of total capital (hard cap regardless of formula output) |
| Daily loss halt | 1.5% of total capital — **declarative target in v1**; not yet the runtime enforcement source. See Known Limitations. |
| Max drawdown before review | 12% |
| Drawdown at 50% of max | Halve position size |
| Drawdown at 75% of max | Paper only |
| Portfolio exposure cap | This is the only live strategy in v1; cap applies when second strategy is added |
| Correlation cap | N/A for single instrument; revisit if basket is added |

---

## 4 — Operational thresholds

These numbers must be confirmed before shadow and live promotion.

| Threshold | Value | Action if breached |
|---|---|---|
| Stale data timeout | 30 minutes past expected bar timestamp | No new entries; alert |
| Order reject limit | 3 consecutive rejects | Halt; investigate |
| Slippage warn threshold | 1.5× backtest median slippage | Log; review next session |
| Slippage halt threshold | 3× backtest median slippage | Halt; do not resume same session |
| Reconciliation tolerance | Zero unresolved mismatch | Flatten-only until resolved |
| Fill confirmation timeout | 5 minutes after order sent | Flag as unconfirmed; do not send duplicate |
| Kill switch test frequency | After every material system change; at minimum weekly |

---

## 5 — Evidence logging requirements

Every session must produce a log record for each of the following. No promotion without complete logs.

**Per signal:**
- Timestamp
- Price at signal
- 200-day SMA value at signal
- ATR ratio at signal (regime)
- Signal direction (long / flat)
- Regime flag (normal / chop / high-vol)

**Per order:**
- Timestamp sent
- Order type and size
- Intended entry/exit price
- Stop level
- Capital at risk (dollar amount)

**Per fill:**
- Timestamp confirmed
- Fill price
- Slippage vs. intended price (points and %)
- Fees paid

**Per session:**
- Regime state at open
- Any halts triggered (type, timestamp, reason)
- Any manual overrides (reason, operator, timestamp)
- Reconciliation check result (pass / mismatch + resolution)
- Running drawdown from peak

**Per drawdown event:**
- Peak equity
- Trough equity
- Duration in days
- Recovery date (when filled in)
- Action taken (held / halved / paused)

---

## 6 — Promotion checklist

Work through each gate in order. Do not advance until all items pass.

### Paper gate

- [ ] 30 calendar days of simulated operation
- [ ] 50+ completed round trips (entry + exit)
- [ ] Observed win rate and avg win/loss within 25% of backtest expectations
- [ ] No critical bugs in signal generation, order formatting, or state management
- [ ] Kill switch tested successfully
- [ ] All evidence logs complete and parseable
- [ ] Daily loss halt triggered and recovered correctly at least once in simulation
- [ ] Regime filter blocked at least one entry in the run

### Shadow gate

- [ ] 20+ trading days running against live market data
- [ ] Every signal logged with contemporaneous spread/depth data
- [ ] Estimated slippage for each would-be fill within 1.5× backtest estimate
- [ ] Regime filter correctly classifying conditions vs. manual review
- [ ] All operational integrity checks passing every session
- [ ] No unresolved reconciliation mismatches
- [ ] Recovery rule exercised at least once (simulated restart with state validation)

### Capped live gate

- [ ] 25% of intended position size only
- [ ] 20+ completed live round trips
- [ ] Minimum 8 weeks at capped size (this system is slow; trade count alone is insufficient)
- [ ] Realized slippage within 1.5× shadow estimates
- [ ] No halts from operational failures (data, rejects, reconciliation)
- [ ] Drawdown within expected range for this period
- [ ] All logs complete; nothing missing
- [ ] Expectancy positive over the capped-live period

### Full size gate

- [ ] All capped live items pass
- [ ] Explicit decision to scale — not automatic
- [ ] Scale in 25% increments over 4 weeks minimum
- [ ] Risk controls re-verified at full size (slippage, fills, daily halt behavior)

---

## 7 — Retirement thresholds

Defined now. Do not renegotiate under drawdown.

| Trigger | Threshold | Action |
|---|---|---|
| Rolling 60-day expectancy | Negative | Mandatory review; paper only pending outcome |
| Two consecutive review months negative | Both negative | Retire unless structural explanation found |
| Drawdown from peak | > 12% | Full stop; review before any resumption |
| Slippage trend | Rising for 3 consecutive months | Review execution; may indicate crowding or liquidity change |
| Regime accuracy | Filter flagging > 40% of bars as abnormal for 30+ days | Review regime parameters |
| Market structure change | Major index reconstitution, sustained vol regime shift, regulatory change | Mandatory review regardless of P&L |

**The rule:** If two or more triggers fire simultaneously, the strategy is retired until a formal review is complete. The review must happen before capital is re-deployed, not alongside it.

---

## 8 — What this strategy is not

Defined explicitly to prevent scope creep.

- It is not a short strategy. Short signals are ignored in v1.
- It is not a multi-instrument strategy. One instrument only in v1.
- It is not an intraday strategy. Bar frequency is daily. Intraday signals are ignored.
- It is not optimized. The 200-day SMA is not tuned. The stop is not tuned. Optimization comes after evidence, not before.
- It is not the final strategy. It is the first validated pipeline run.

---

## Change log

| Date | Change | Author |
|---|---|---|
| 2026-04-14 | v1 created | — |

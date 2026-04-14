# CryptKeep — Control Kernel Specification

**Version:** 1.0  
**Status:** Normative  
**Removal target for transitional families:** 2026-07-01

---

## Utility Function (Scalarized)

> Maximize: `long_term_return × (1 − ruin_risk)`  
> Subject to hard constraints:
> - Ruin probability < 1 %
> - Max drawdown < 25 %
> - Operator monitoring time < 30 min/day average

This is the declared objective. All threshold and allocation decisions are evaluated against it.

---

## 1 — Deployment Stages (exactly 5)

| Stage | New risk | Allowed actions | Notes |
|---|---|---|---|
| `paper` | none | simulate | Backtest / simulation only |
| `shadow` | none | simulate, monitor | Live data, no orders |
| `capped_live` | ≤ 5 % risk budget | submit_capped, monitor, reduce | Hard cap: 1 contract |
| `scaled_live` | allocator output | submit_full, monitor, reduce | Full allocation rules |
| `safe_degraded` | none | reduce, flatten, monitor | Zero new risk; reductions only |

### Promotion gates
Promotion from one stage to the next requires satisfying evidence gates defined in `docs/safety/strategy_promotion_ladder.md`. No automatic promotion — operator explicitly calls `promote()`.

### Demotion triggers
Any kernel breach automatically demotes to `safe_degraded`. Demotion is immediate and logged.

### Illegal transitions
- `safe_degraded → scaled_live` — illegal without passing through paper/shadow/capped
- `paper → scaled_live` — must pass through each intermediate stage

---

## 2 — Action Primitives (exactly 4)

| Action | Meaning |
|---|---|
| `allow` | Normal operation |
| `derisk` | Reduce position/size by 50 % |
| `restrict` | Reductions only, no new risk |
| `halt` | No orders of any kind |

Precedence (highest wins when multiple triggers fire):
1. `halt` (safety/data integrity)
2. `restrict` (execution integrity, reconciliation)
3. `derisk` (risk/signal quality)
4. `allow`

---

## 3 — Invariant Metrics (exactly 6)

| Metric | Warn threshold | Critical threshold | Action at critical |
|---|---|---|---|
| `slippage_p95` | > 0.5× expected edge | ≥ 1.0× | halt |
| `fill_rate` | < 92 % | < 80 % | halt |
| `recon_drift` | > 1 % | > 5 % | halt |
| `dd_duration_days` | > 30 days | > 60 days | safe_degraded |
| `regime_stability` | < 0.50 | < 0.25 | derisk |
| `alert_count` | ≥ 3 | ≥ 4 | safe_degraded (cognitive budget) |

---

## 4 — Cognitive Budget Rule

When `alert_count ≥ 4` OR any `active_symbols > 3`:
- System automatically calls `force_safe_degraded()`
- Entry is logged with reason `cognitive_budget_breach`
- Human override: 1 per 24 h, requires 48 h review

The budget exists because cognitive overload is a systematic risk. When the operator cannot hold the system state in their head, discretionary errors become the primary failure mode.

---

## 5 — Safe-Degraded Behaviour

Entry: automatic (via kernel evaluation) or manual.

While in `safe_degraded`:
- Allocation = 0.0 (no new risk)
- Only `reduce` and `flatten` actions allowed
- Human override: 1 per 24 h, logged
- Exit: explicit `promote()` to `paper` after incident review

---

## 6 — Allocator

```
allocation = base_weight × regime_stability × (1 − drift_penalty) × (1 − dd_frac)
clamped to [0, stage_max_alloc]
```

Where:
- `base_weight` = 0.10 (10 % of risk budget per strategy slot)
- `regime_stability` = 0.0–1.0 (fraction of recent days where trend is coherent)
- `drift_penalty` = 0.0–1.0 (proportional to slippage_p95)
- `dd_frac` = current_dd_days / max_dd_days

Returns 0.0 in `paper`, `shadow`, `safe_degraded` regardless of inputs.

---

## 7 — Termination Gate (the only one)

After any material change to the kernel or strategy:

> **"Can one operator, under stress, understand current state and decide the next action in ≤ 5 minutes?"**

If YES → 90-day lock. Only emergency patches allowed.

This gate is the stopping condition for spec refinement. It is deliberately non-representational: it cannot be automated. It requires a human decision.

---

## 8 — Canonical Reference Strategy

**200-day SMA trend following** (see `services/control/canonical_strategy.py`)

- Signal: `price > SMA_200 → LONG`, else `FLAT`
- All signals pass through `ControlKernel.evaluate()` before orders
- Allocation is kernel-controlled
- Regime stability estimated from SMA coherence over prior 60 days

This strategy is simple enough to hold in one sentence and rich enough to exercise all kernel branches.

---

## Implementation

| Component | File |
|---|---|
| Deployment stage machine | `services/control/deployment_stage.py` |
| Cognitive budget | `services/control/cognitive_budget.py` |
| State-aware allocator | `services/control/allocator.py` |
| Control kernel | `services/control/kernel.py` |
| Canonical strategy | `services/control/canonical_strategy.py` |
| Tests | `tests/test_control_kernel.py` |

---

## Complexity Budget (hard caps — do not exceed without mandatory refactor)

| Item | Cap |
|---|---|
| Stages | 5 |
| Action primitives | 4 |
| Core metrics | 6 |
| Rule categories | 5 |
| Alert count threshold | 4 |

These caps exist to keep the system understandable to one operator under stress.

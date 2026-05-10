# Evidence, Promotion, and Governance Audit — Pass 1

**Date:** 2026-05-10
**Section:** 8. Evidence, Promotion, and Governance
**Status:** COMPLETE

---

## Scope

- `services/backtest/evidence_cycle.py` — `_evidence_status_for_row()`, `_research_acceptance_for_row()`
- `dashboard/services/promotion_ladder.py` — `build_promotion_readiness()`
- `docs/governance/governance_checklist.md`
- `docs/governance/governance_signoff.md`

---

## Checklist status

- [x] Evidence status terminology matches actual data truth.
- [x] Promotion gate blockers enforceable and visible.
- [x] Synthetic/thin evidence cannot be presented as promotion-ready.
- [~] Governance docs match code and runtime — Finding 3 and 4 open.

---

## SHOWN findings

### Finding 1 — Evidence status classification is rigorous and numeric (Strength)

`_evidence_status_for_row()` produces one of four statuses based on hard thresholds:

```
"insufficient"     — 0 closed trades or 0 active windows
"synthetic_only"   — no paper history or no paper fills for this strategy
"paper_thin"       — paper fills < 6 OR paper closed trades < 3
"paper_supported"  — paper fills >= 6 AND paper closed trades >= 3
```

Thresholds are enforced in code, not config. Cannot be overridden via settings.

---

### Finding 2 — Synthetic and thin evidence are blocked from both promotion gates (Strength)

`_research_acceptance_for_row()` (`evidence_cycle.py:630`):
```python
if str(evidence_status ...) != "paper_supported":
    blockers.append("Evidence status is ...; require paper_supported.")
```

`build_promotion_readiness()` (`promotion_ladder.py:173, 241`):
```python
if top_evidence_status != "paper_supported":
    blockers.append("Top strategy evidence status is ...; require paper_supported.")
```

Both gates enforce `paper_supported` as a hard blocker. `synthetic_only` and
`paper_thin` produce named blockers that cannot be dismissed without
changing the numeric thresholds in code.

---

### Finding 3 — Governance signoff has three open Blocking:Yes items (Shown)

`docs/governance/governance_signoff.md` (frozen 2026-03-21) lists:

1. **Campaign validation** — "validation depth is still minimal and distributed"
2. **Invalidation** — "terminal invalidation enforcement outside status language is still not fully proven"
3. **CAUTION/invalidation** — "Need explicit end-to-end proof that invalid states cannot reach governed campaign continuation"

The signoff is frozen at 2026-03-21. The repo has evolved significantly
since then (PRs #36–#40 in the current session). The frozen signoff may
describe a state that no longer accurately reflects the current repo.

---

### Finding 4 — Governance checklist is for a different branch and strategy (Shown)

`docs/governance/governance_checklist.md` describes:
- Branch: `followup/compat-cleanup`
- Symbol: `APR/USD`, Strategies: `breakout_donchian`, `ema_cross`

Current active soak:
- Branch: `codex/runtime-hardening-ai-alert-monitor`
- Symbols: `B3/USD`, `B3/USDC`, Strategy: `ES Daily Trend v1`

The checklist has not been updated for the current evidence run. An operator
using it to verify lineage for the current soak would find it describes a
different strategy on a different branch.

---

### Finding 5 — Research acceptance enforces six independent numeric blockers (Strength)

All six must pass simultaneously:
- Paper closed trades ≥ threshold
- Represented windows ≥ threshold
- Post-cost return > 0
- Stressed post-cost return > 0 (after slippage sensitivity)
- Max drawdown ≤ threshold
- `evidence_status == "paper_supported"`
- `confidence_label in {"medium", "high"}`

Each is independent. Passing numeric filters with synthetic evidence is
still blocked.

---

## Summary

| Surface | Finding | Severity |
|---|---|---|
| Evidence status thresholds | Numeric, code-enforced, four clear states | **Strength** |
| Promotion gates block synthetic | Named blockers at both gates | **Strength** |
| Governance signoff open blockers | 3 Blocking:Yes items from 2026-03-21 | Shown |
| Governance checklist stale | Different branch and strategy | Shown |
| Six independent numeric blockers | All required simultaneously | **Strength** |

---

## UNVERIFIED points

- Whether the three governance signoff blocking items have been materially
  addressed by subsequent work and not updated.
- Whether checklist update is required before soak sign-off or whether
  `PAPER_SOAK_GATE.md` decisions are sufficient.

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Section 8
**Next target:** Section 10 — Release, Validation, and Operator Docs

# CryptKeep System Blueprint

**Method:** every statement below was treated as a hypothesis until traced. Nothing is
marked authoritative unless competing paths were checked. Claims are `SHOWN`,
`REFUTED`, `PARTIALLY SHOWN`, or `UNKNOWN`.

**Traced:** 2026-07-12 against `master` (`a84f82583`, after PR #261).
**Regression protection:** `tests/test_blueprint_invariants.py` (18 executable tests). Each
encoded fact fails a test if it changes. A failure there means *the blueprint is stale*,
not necessarily that a bug was introduced.

**Scope honesty:** this pass traced the concepts with money consequences —
fees, slippage, PnL, expectancy, promotion, retirement. Ranking/strategy-score
and risk-metric lineage are enumerated but **NOT fully traced** (marked UNKNOWN);
they are the next pass.

---

## 1. Claim Ledger (the findings that changed my picture)

### CLAIM-01 — REFUTED (material)

**Claim:** "The promotion gate measures expectancy per trade."

**Trace:**
```
paper_engine.py:332          pnl = None                       (BUY / opening leg)
                             pnl = realized  if side == "sell" (SELL / closing leg)
        ↓
evidence_logger.py:345       "pnl_usd": pnl   ← key written UNCONDITIONALLY,
                                                value None on entry fills
        ↓
check_promotion_gates.py:203 [float(f.get("pnl_usd") or 0)
                              for f in fills if "pnl_usd" in f]
                             ← key IS present → None coerced to 0.0
        ↓
                             entry fills ENTER THE MEAN AS ZERO
```

**Status: REFUTED.** The gate's expectancy is **mean-per-FILL**, not per closed trade.
For 1:1 round trips it is diluted ~50% toward zero. Proven executably: 5 round trips
with a +10 exit each yield a gate expectancy of **5.0**, not 10.0
(`test_gate_expectancy_is_per_fill_not_per_closed_trade`).

**Consequences:**
- The `len(pnls) < 10` guard counts **fills**, not trades — it can satisfy at 5 round trips.
- The gate's expectancy value is **not comparable to a per-trade backtest baseline**.
  Item #2 of the backlog (populate `backtest_expectations`) compares these directly.
- Direction is **conservative** (understates expectancy → harder to pass), so this is not
  a capital-loss bug. It is a *measurement-validity* bug.

**Competing path exists and is correct:**
`paper_evidence_qualification` computes `expectancy_per_closed_trade = net_realized /
closed_count` — a true per-trade figure. The gate's *history* path (line 1018) uses this
one. So **the same script contains both denominators**, applied to different evidence
sources.

**Regression protection:** 3 tests.

### CLAIM-02 — SHOWN

**Claim:** "`paper_engine` is authoritative for expectancy." → **PARTIALLY SHOWN, narrowed.**

Authoritative for: paper-fill execution costs, and the expectancy calculations *derived
from those fills* (`check_promotion_gates._check_expectancy`, `retirement_checker`,
`strategy_feedback`).
**NOT authoritative for:** backtest/walk-forward expectancy (separate cost model),
journal-derived `expectancy_return_pct` (`journal_analytics`).

### CLAIM-03 — SHOWN

**Claim:** "Backtest costs come from the same config as paper costs." → **REFUTED.**
The backtest family reads **no** user config (grep: zero `load_user_yaml` /
`paper_trading` in `services/backtest`). Costs arrive as parameters defaulting to
10.0/5.0. Setting `paper_trading.fee_bps` **does not change sweep/backtest costs.**

### CLAIM-04 — SHOWN

**Claim:** "There are three cost surfaces." → **REFUTED: there are five, plus a
seven-module backtest family.** My own earlier census was wrong; the census invariant
caught it.


### CLAIM-05 — REFUTED (capital-relevant)

**Claim:** "`realized_pnl_usd` means the same thing everywhere."

**Trace:**
```
storage/paper_trading_sqlite.py:354   proceeds(net of sell fee) - (avg incl. buy fee) * qty
                                      -> pnl_usd_semantics = "net_of_fees"      [NET]
storage/live_position_store_sqlite.py:220
                                      realized = (price - old_avg) * qty
                                      apply_fill() takes NO fee parameter       [GROSS]
        ↓
services/journal/fill_sink.py:140     pnl = pos_result["realized_pnl_usd"]      (gross)
        ↓                             fee passed SEPARATELY
services/risk/risk_daily.py           realized_pnl_usd column | fees_usd column
```

**Finding:** the same field name carries **two different mathematical meanings**.
Paper realized PnL is net of fees; live realized PnL is gross of fees, with the fee
carried in a separate column.

**Impact:** any comparison of paper expectancy (net) against live/journal realized PnL
(gross) is apples-to-oranges. The backlog's net-of-fees fix (#28) corrected the **paper**
path only.

### CLAIM-06 — REFUTED (capital-relevant, UNSAFE direction)

**Claim:** "The live daily-loss cap limits net loss."

**Trace:**
```
services/risk/risk_daily.py  snapshot() returns:
                               "realized_pnl": realized        <- GROSS
                               "fees":         fees
                               "pnl": (realized - fees)        <- NET, computed here
        ↓
services/risk/risk_daily.py  realized_today_usd() -> snap["realized_pnl"]   <- GROSS
        ↓
services/execution/_executor_submit.py:382
                             rpnl = RiskDailyDB(...).realized_today_usd()
                             -> PHASE82 live risk gates
```

**Finding:** the live daily-loss gate is evaluated against **gross** realized PnL —
even though `snapshot()` computes the net figure (`realized - fees`) on the adjacent
line and does not use it.

**Impact:** on a losing day the true **net** loss exceeds the configured cap by the
total fees paid. Unlike CLAIM-01 (which understates expectancy — conservative), this
direction is **unsafe**: it permits more loss than configured. This is a **deferred
capped-live** concern, not a paper-stage one, since the gate only runs on the live
submit path — but it must be resolved before capital is exposed.

**Not claimed:** whether the intended policy is a gross or net cap. That is an operator
decision. The blueprint records only what the code does.

**Regression protection:** `test_realized_today_usd_returns_gross_not_net`,
`test_risk_daily_snapshot_exposes_both_gross_and_net`.

---

## 2. Configuration Map — the cost surfaces

| Surface | Source | Fee | Slip | Role (traced) | Live? |
|---|---|---|---|---|---|
| `execution/paper_engine.py` | `user.yaml paper_trading.*` | **7.5** | **5.0** | canonical paper fills | **YES — authoritative** |
| `analytics/paper_strategy_evidence_service.py` | dataclass default | **10.0** | 5.0 | evidence/leaderboard scoring | YES (separate responsibility) |
| `backtest/*` (7 modules) | parameter default; **no config read** | **10.0** | 5.0 | backtest, walk-forward, sweep, leaderboard, parity, parameter sweep | YES |
| `paper_exec.py` | dataclass default | **10.0** | 5.0 | compat executor (`paper_trader/main.py`) | non-canonical |
| `paper_trader/paper_execution_venue.py` | dataclass default | **1.0** | **0.0** | legacy runner (`trading_runner/run_trader.py:125`) | non-canonical |
| `execution/paper_fees.py` | `user.yaml execution.paper_fee_bps` | **0.0** | — | **dormant — no production callers** | NO |

**Assumption fork (highest impact):** the legacy runner models **1.0 bps fee, 0.0
slippage** — near-free execution. Any evidence from that path is not comparable to
canonical paper evidence. *Action: leave separate, but pinned by test so it cannot
silently become an evidence source.*

**Assumption fork (Phase 1/Phase 2 boundary):** paper measurement (7.5) and archive-sweep
optimization (10.0) are governed by **independently sourced** cost models.
*Action: validate both surfaces separately. `scripts/check_cost_assumptions.py` validates
the paper surface and explicitly disclaims the backtest one.*

---

## 3. Authority Map (with exclusions — authority always has boundaries)

**`paper_engine`**
- Authoritative for: paper fill price, fill fee, realized PnL written to fill evidence.
- **Not** authoritative for: backtest expectancy, journal expectancy, evidence-scoring costs.
- Evidence: `_cfg()` → `apply_fill` → `pnl_usd` → gate/retirement/feedback.

**`paper_evidence_qualification`**
- Authoritative for: *which* fills count (provenance), and `expectancy_per_closed_trade`.
- **Not** authoritative for: the gate's JSONL expectancy path (which uses per-fill mean).

**`check_promotion_gates`**
- Authoritative for: promotion pass/fail.
- **Not** authoritative for: the *meaning* of its own expectancy number — it hosts two
  different denominators depending on evidence source (CLAIM-01).

**`walk_forward` / backtest family**
- Authoritative for: out-of-sample research expectancy under **its own** cost assumptions.
- **Not** authoritative for: anything the paper config governs.

---

## 4. Risk Map

| Risk | Why it exists | Detection | Mitigation |
|---|---|---|---|
| Gate expectancy compared to a per-trade baseline | CLAIM-01 fork | `test_gate_expectancy_is_per_fill…` | Decide the intended denominator **before** populating `backtest_expectations` (backlog #2) |
| Sweep optimizes against costs never validated | independent sourcing | `test_backtest_costs_not_sourced_from_user_yaml` | Validate the backtest surface separately |
| Legacy runner evidence enters analysis | 1.0/0.0 costs | `test_legacy_runner_models_near_free_execution` | Keep non-canonical; never treat as evidence |
| A sixth cost surface appears | census drift | `test_no_new_fee_surface_appeared` | Census invariant |
| **Live daily-loss cap permits more loss than configured** | CLAIM-06: gate reads gross PnL; fees excluded | `test_realized_today_usd_returns_gross_not_net` | **Decide gross-vs-net cap policy before capped-live**; the net figure already exists in `snapshot()["pnl"]` |
| Paper (net) vs live/journal (gross) PnL compared | CLAIM-05: same field name, different math | `test_live_position_store_realized_pnl_is_gross_of_fees` | Never compare across the boundary without normalizing |
| Backtest family diverges internally | 7 modules, 7 defaults | `test_backtest_fee_family_is_internally_consistent` | Family-consistency invariant |

---

## 5. Not Yet Traced (honest UNKNOWNs — next pass)

- **Strategy scores / ranking:** `composite_ranker`, `rotation_engine`, `signal_library`,
  `ranking_presets`, `coinbase_movers`, `multi_venue_view`. Producers enumerated;
  consumers and authority **not traced**.
- ~~**Risk metrics / PnL producers**~~ — **NOW TRACED**: see CLAIM-05 and CLAIM-06.
  `live_position_store` produces GROSS realized PnL; `paper_trading_sqlite` produces NET.
  `fill_sink` passes gross + fee separately to `risk_daily`. The live daily-loss gate
  consumes the gross figure.
- **`canonical_execdb`** realized-PnL semantics: still **UNKNOWN** (it receives
  `realized_pnl_usd` from `fill_sink`, so presumably gross, but its own transformations
  were not traced).
- **Retirement vs promotion thresholds:** both compute rolling expectancy but from
  different sources; equivalence **not verified**.
- **`journal_analytics.expectancy_return_pct`:** a fifth expectancy definition; inputs
  not traced.

These are named rather than glossed. Each is a hypothesis, not a fact, until traced.

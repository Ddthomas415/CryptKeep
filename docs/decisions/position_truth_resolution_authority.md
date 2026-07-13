# Decision Record — Position Truth Resolution Authority

**Status:** OPEN — deferred to a **capped-live stage gate**. No runtime change now.
**Traced:** 2026-07-11 against `a84f8258`; re-verified by tests on 2026-07-13 against `ada31670b`. SHOWN unless labelled.
**Risk class:** LOW today (the live lane is gated off; no drift can exist) · **HIGH when implemented** — it would arm a halt authority from an automated signal.
**Finding class:** **Resolution authority** — *two sources describe the same fact and nothing decides between them, or acts when they disagree.*

---

## 1. The question

Every other class in this audit set concerns authority over **internal** state: who may promote, who chooses the strategy, what a metric means, what a stop stops, which reader's answer counts, which writer wins.

This one asks a different question:

> **When the system's view of the world disagrees with the venue's view — how much of an asset we actually hold — what decides which is authoritative, and what action follows?**

## 2. Order truth ≠ position truth (the distinction that must not be conflated)

| | **Order truth** | **Position truth** |
|---|---|---|
| Question | *What happened to this order?* | *What do we actually hold?* |
| Mechanism | `_executor_reconcile` — `submit_unknown` → venue lookup by client-order-id → converge | — |
| Wired? | **Yes** | **No** |
| Scheduled? | **Yes** | **No** |
| Fault-tested? | **Yes** (deferred substrate #4, fault-injection suite) | **No** |

**Both are called "reconciliation."** They are different invariants. Deferred substrate #4 proved exactly-once submission and reconciler convergence **for orders** — it says nothing about position truth. Active #5's launch packet lists "reconciliation halt/resume" evidence without specifying *which*.

## 3. What was traced (SHOWN)

```
services/reconciliation/exchange_reconciler.py
    fetch_balance() / fetch_positions()          ← asks the venue what we hold
    ReconcileConfig(interval_sec=30, ...)        ← DESIGNED for a 30s loop
    severity_from(drift, cash_tol, qty_tol) -> "OK" | "WARN" | "CRITICAL"
        CRITICAL when |drift| > 3 x tolerance    (cash OR position qty)
    reconcile_once(...) -> writes recon/portfolio/runbook stores; builds a repair plan
        ↑
        └── IMPORTED BY: NOTHING.   ← zero production importers

services/admin/position_reconcile.py
    fetch_balance() / fetch_positions()
        └── admin/reconcile_safe_steps.py
              └── 2 scripts + dashboard/pages/60_Operations.py   ← OPERATOR-INVOKED ONLY
```

**Three findings:**
1. **The module that computes drift severity has zero importers.** It is dormant — *and it carries its own `interval_sec=30`*, so it is unwired despite being designed to be scheduled.
2. **No scheduled position reconciliation exists.** The only reachable path is an operator running a script or clicking a dashboard button.
3. **`CRITICAL` reaches no control.** `severity_from` returns a *string*. Nothing arms the kill switch, sets `master_read_only`, or blocks submission on it — because nothing consumes it.

**Bounds preserved:** no incorrect outcome was demonstrated, and none *can* be — the live lane is gated off and no live order has ever flowed, so venue drift cannot exist. Paper positions cannot drift either (`paper_trading_sqlite` *is* the world for paper; there is no external truth to disagree with). **This is the first finding in the set whose consequences are entirely prospective.**

## 4. "The venue wins" is not a policy — it is one clause of one

A resolution policy must define **when** the venue is authoritative, or a halt authority armed by drift will fire on ordinary operating conditions and call it safety.

**What `exchange_reconciler` models today (SHOWN):** magnitude tolerances only — `cash_tolerance: 5.0`, `asset_qty_tolerance: 0.0001`, `CRITICAL` at 3×.

**What it does not model — the entire time dimension:**

| Transient condition | Why a magnitude-only rule mishandles it |
|---|---|
| **Settlement / transfer lag** | funds legitimately in flight appear as drift |
| **Pending transfers** | balance is real but not yet reflected on one side |
| **Stale venue snapshot** | the venue's own view lags; drift is an artifact of *when* we asked |
| **Transient API inconsistency** | one bad `fetch_balance` response escalates to `CRITICAL` immediately |
| **A fill in flight** | local state has advanced past the venue's snapshot, or vice versa |

**A single 30-second snapshot exceeding 3× tolerance escalates to `CRITICAL` with no requirement that the drift persist.** That is a false-halt design.

### The repo has already solved this — in the order lane

The `submit_unknown` **not-found terminal policy** (deferred substrate #3) faced exactly this problem: *when is a venue observation trustworthy enough to act on irreversibly?* Its answer:

- **`CBP_SUBMIT_UNKNOWN_NOT_FOUND_MIN_OBS`** (default **3**) — the observation must repeat.
- **`CBP_SUBMIT_UNKNOWN_NOT_FOUND_TERMINAL_MS`** (default **900000** = 15 min) — and persist over time.
- **Lookup *exceptions* do not count** as observations.
- **Successful recovery clears the record.**

That is hysteresis plus a minimum age plus an error/observation distinction. **The position lane needs the same shape and does not have it.** The precedent is in-repo, accepted, and reviewed.

## 5. The decision required (deferred to a capped-live stage gate)

**A. Resolution authority — who wins?**
- *Venue wins* (local state is corrected to match), or
- *Halt and adjudicate* (no automatic correction; an operator decides), or
- *Bounded auto-repair* (correct within a policy envelope; halt outside it).

**B. Trust policy — when is the venue authoritative?** (the clause above, and the part most likely to be under-specified)
- persistence: drift must be observed across **N** consecutive reconciliations
- minimum age: and persist for **T** seconds
- exceptions ≠ observations: a failed `fetch_balance` is **not** evidence of drift
- snapshot staleness bound: a venue snapshot older than **S** is not evidence
- settlement/transfer allowance: known in-flight amounts are excluded from drift

**C. Halt binding — what does `CRITICAL` reach?**
Today: nothing. It must reach a **named halt authority** (see `docs/architecture/halt_scope_matrix.md`), and the choice of *which* determines the blast radius — `master_read_only` (paper engine + router) and the kill switch (live submission) have **different scopes**.

**No option is recommended here.** This is an operator decision, and it should be made *before* capped-live depends on it, not during an incident.

## 6. Stage gate (the operative requirement)

> **`capped_live` must not be entered until a scheduled position reconciliation exists, with a defined resolution authority and a trust policy, and `CRITICAL` drift bound to a named halt authority.**

This is a **capability requirement**, not a specific remediation. The audit demonstrates a missing operational capability; it does not dictate which policy is correct.

## 7. Facts pinned while this is OPEN

`tests/test_position_truth_authority.py`:

| Test | Asserts |
|---|---|
| `exchange_reconciler` has **zero** production importers | wiring it becomes a **deliberate, visible act** — it cannot be quietly enabled and mistaken for live protection |
| `severity_from` still reaches no halt authority | `CRITICAL` remains a report, not a control |
| the order reconciler does **not** reconcile positions | order truth and position truth stay distinct |
| the not-found precedent still carries hysteresis + min-age | the pattern the position lane should adopt is not lost |

**On resolution:** these become enforcement tests for the chosen policy — scheduled reconciliation exists, drift persistence is required before escalation, and `CRITICAL` is bound to the chosen halt authority.

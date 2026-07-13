"""Position truth authority — census invariants.

See docs/decisions/position_truth_resolution_authority.md (status: OPEN, deferred to
a capped-live stage gate).

AUDIT CLASS: **Resolution authority** — two sources describe the same fact and nothing
decides between them, or acts when they disagree.

THE GAP (SHOWN against a84f8258; re-verified against ada31670b):
  ORDER truth  ("what happened to this order?")  -> _executor_reconcile: WIRED,
                                                    scheduled, fault-injection tested.
  POSITION truth ("what do we actually hold?")   -> exchange_reconciler: computes venue
                                                    drift, escalates to CRITICAL at 3x
                                                    tolerance, carries interval_sec=30 —
                                                    AND HAS ZERO IMPORTERS.
                                                    CRITICAL reaches NO halt authority.

  Both are called "reconciliation". They are DIFFERENT INVARIANTS.

BOUNDS: no incorrect outcome was demonstrated and none can be — the live lane is gated
off, so venue drift cannot exist. Paper positions cannot drift (the paper store IS the
world for paper). This finding's consequences are entirely PROSPECTIVE, which is why it
is recorded now rather than after capped-live depends on it.

CATEGORY: [B] DECISION-WINDOW. On resolution these become ENFORCEMENT tests for the
chosen policy (scheduled reconciliation exists; drift must persist before escalation;
CRITICAL is bound to a named halt authority).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _py_sources(*roots: str):
    for root in roots:
        base = REPO / root
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if "__pycache__" in p.parts or p.name.startswith("test_"):
                continue
            yield p


def test_exchange_reconciler_has_no_production_importers():
    """The module that computes venue drift severity is DORMANT.

    Pinning this makes wiring it a DELIBERATE, VISIBLE act. Without the pin, it could be
    quietly enabled — or, worse, mistaken for live protection *because it exists and
    looks complete*. It fetches balances and positions, applies tolerances, escalates to
    CRITICAL, and builds a repair plan. Nothing imports it.

    A FAILURE HERE IS GOOD NEWS — it means position reconciliation is being wired. When
    that happens, this test must be replaced with enforcement tests for the chosen
    resolution policy (see the decision record).
    """
    importers = []
    for p in _py_sources("services", "scripts", "dashboard"):
        if p.name == "exchange_reconciler.py":
            continue
        src = p.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"(from\s+services\.reconciliation\.exchange_reconciler\s+import|import\s+exchange_reconciler)", src):
            importers.append(str(p.relative_to(REPO)))

    assert importers == [], (
        f"exchange_reconciler now has importers: {importers}. Position reconciliation is "
        "being wired — GOOD. Now confirm the decision record's requirements are met: a "
        "defined resolution authority, a trust policy (drift persistence, minimum age, "
        "exceptions-are-not-observations, snapshot-staleness bound), and CRITICAL bound "
        "to a NAMED halt authority. Replace this census test with those enforcement "
        "tests. See docs/decisions/position_truth_resolution_authority.md"
    )


def test_critical_drift_reaches_no_halt_authority():
    """`severity_from` returns a STRING. Nothing arms the kill switch, sets
    master_read_only, or blocks submission on it.

    Pinned so that binding CRITICAL to a control is a deliberate act — and so the choice
    of WHICH halt authority is made consciously, since they have different scopes
    (docs/architecture/halt_scope_matrix.md).
    """
    src = (REPO / "services/reconciliation/exchange_reconciler.py").read_text(encoding="utf-8")
    for halt_token in (
        "set_kill_switch", "is_kill_switch_on", "admin.kill_switch",
        "master_read_only", "system_guard",
    ):
        assert halt_token not in src, (
            f"exchange_reconciler now references '{halt_token}' — CRITICAL drift may now "
            "reach a halt authority. Confirm the trust policy exists FIRST: a magnitude-"
            "only rule with no drift-persistence requirement will fire on settlement lag, "
            "pending transfers, stale snapshots, and transient API errors, and call it "
            "safety. See docs/decisions/position_truth_resolution_authority.md §4."
        )


def test_order_reconciler_does_not_reconcile_positions():
    """ORDER truth and POSITION truth are different invariants and must not be conflated
    under the word 'reconciliation'.

    The order reconciler establishes what happened to an order (submit_unknown -> venue
    lookup by client-order-id -> converge). It does NOT ask what we hold.
    """
    src = (REPO / "services/execution/_executor_reconcile.py").read_text(encoding="utf-8")
    for pos_call in ("fetch_positions", "fetch_balance", "fetchPositions", "fetchBalance"):
        assert pos_call not in src, (
            f"_executor_reconcile now calls '{pos_call}' — the ORDER reconciler is now "
            "reconciling POSITION truth. These are different invariants with different "
            "failure modes; confirm this is intended and that the resolution policy exists."
        )


def test_the_hysteresis_precedent_still_exists_in_the_order_lane():
    """The pattern the position lane should adopt.

    The submit_unknown not-found terminal policy already answers 'when is a venue
    observation trustworthy enough to act on irreversibly?':
      - the observation must REPEAT (MIN_OBS)
      - and PERSIST over time (TERMINAL_MS)
      - lookup EXCEPTIONS do not count as observations
      - successful recovery CLEARS the record

    Pinned so the precedent is not lost. A position-drift policy built on magnitude
    tolerances alone — with no time dimension — would be a false-halt design.
    """
    found = False
    for p in _py_sources("services"):
        src = p.read_text(encoding="utf-8", errors="ignore")
        if "SUBMIT_UNKNOWN_NOT_FOUND_MIN_OBS" in src and "SUBMIT_UNKNOWN_NOT_FOUND_TERMINAL_MS" in src:
            found = True
            break
    assert found, (
        "the submit_unknown not-found hysteresis policy (MIN_OBS + TERMINAL_MS) is gone. "
        "That is the in-repo precedent for 'when is a venue observation trustworthy enough "
        "to act on' — the position-truth resolution policy is meant to adopt its shape. "
        "See docs/decisions/position_truth_resolution_authority.md §4."
    )


def test_reconcile_config_still_declares_an_interval_it_does_not_run():
    """The sharpest evidence that this is a MISSING WIRING, not a missing design:
    ReconcileConfig carries interval_sec=30 — the module was DESIGNED to be scheduled —
    and nothing schedules it.
    """
    src = (REPO / "services/reconciliation/exchange_reconciler.py").read_text(encoding="utf-8")
    assert "interval_sec" in src, (
        "ReconcileConfig no longer declares a reconciliation interval — the module's "
        "intended scheduling contract changed. Re-verify the decision record."
    )

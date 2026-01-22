# Phase 297 — Reconciliation Wizard (Operator)

Purpose:
- A guided, locked-step workflow to safely recover after restarts before resuming live execution.

Steps:
1) Run reconciliation (reconcile_once)
2) Export report (JSON)
3) Optional: cancel unknown exchange open orders (typed confirm)
4) Re-run reconciliation
5) Resolve local intents marked RECONCILE_NEEDED (typed confirm)
6) Resume (live-gated: preflight + private auth + reconciliation clean)

State:
- Persisted in: data/wizard_reconcile.json
- Reset requires typing RESET_WIZARD in the UI.

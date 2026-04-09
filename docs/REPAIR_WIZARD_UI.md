# Phase 325 — Repair Wizard UI (Role-Gated)

Where:
- Streamlit dashboard contains a "Repair Wizard (Role-Gated)" section.

Roles (authenticated):
- VIEWER: read-only
- OPERATOR: generate + approve
- ADMIN: execute

Authentication:
- Operator page now requires sign-in.
- Preferred provider: OS keychain-backed user store.
- Optional controlled fallback: `CBP_AUTH_USERNAME` + `CBP_AUTH_PASSWORD` (+ `CBP_AUTH_ROLE`).
- Optional bootstrap (first user creation): `CBP_AUTH_BOOTSTRAP_USER`, `CBP_AUTH_BOOTSTRAP_PASSWORD`, `CBP_AUTH_BOOTSTRAP_ROLE`.

Execution is fail-closed:
- Requires config mode=live AND execution.live_enabled=true
- Requires ENABLE_LIVE_TRADING=YES (existing live gate)
- Requires ENABLE_REPAIR_EXECUTION=YES
- If plan includes FLATTEN_POSITIONS, also requires ENABLE_FLATTEN=YES

Typed confirmation:
- Must type: `EXECUTE <PLAN_ID>`

Export:
- UI export writes:
  - data/runbook_exports/<plan_id>.md
  - data/runbook_exports/<plan_id>.json
  - Optional PDF if reportlab is installed
- CLI export:
  - `python scripts/repair_export.py --plan-id <PLAN_ID> --out-dir data/runbook_exports`

# Phase 325 — Repair Wizard UI (Role-Gated)

Where:
- Streamlit dashboard contains a "Repair Wizard (Role-Gated)" section.

Roles (local session placeholder):
- VIEWER: read-only
- OPERATOR: generate + approve
- ADMIN: execute

Execution is fail-closed:
- Requires config mode=live AND live.enabled=true
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

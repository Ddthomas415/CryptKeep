# Phase 51 — Scheduling (Mac + Windows) + approval gate for model switching (paper)

What runs automatically:
1) Monitor (safe):
   - scripts/monitor_and_maybe_rollback.py
   - Can disable model gate or roll back after sustained breaches (Phase 50)

2) Recommend+Apply (safe-by-design):
   - scripts/recommend_model_switch.py writes data/learning/recommended_model.json
   - scripts/apply_pending_model_switch.py applies ONLY if:
       - data/learning/model_switch_approval.json exists
       - approval model_id matches the recommended model_id
   - Approval is consumed after switching.

macOS:
- Install monitor:
  bash scripts/schedule/install_mac_monitor.sh 300
- Install recommend+apply:
  bash scripts/schedule/install_mac_recommend_apply.sh 1800

Windows:
- Install monitor:
  powershell -ExecutionPolicy Bypass -File scripts\\schedule\\install_windows_monitor.ps1 -IntervalMinutes 5
- Install recommend+apply:
  powershell -ExecutionPolicy Bypass -File scripts\\schedule\\install_windows_recommend_apply.ps1 -IntervalMinutes 30

Manual approval:
- python3 scripts/approve_model_switch.py --model_id m_xxx --approved_by operator

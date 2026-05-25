## Canonical Operator

| Script | Make target | Purpose |
|--------|-------------|---------|
| `bot_ctl.py` | `make start` / `make stop` | Start and stop the bot |
| `run_bot_safe.py` | — | Canonical launch entrypoint |
| `run_dashboard.py` | `make dashboard` | Dashboard entrypoint |
| `killswitch.py` | `make kill-switch-on` / `make kill-switch-off` | Arm/disarm kill switch |
| `paper_stop.py` | `make paper-stop-now` | Stop paper campaign |
| `preflight.py` | — | Pre-launch checks |
| `run_preflight.py` | — | Preflight entrypoint |
| `maintenance.py` | — | Maintenance tasks |
| `op.py` | — | Operator command surface |
| `doctor.py` | — | Diagnostic |
| `bot_status.py` | — | Process status query |
| `run_paper_strategy_evidence_collector.py` | — | Managed paper evidence collector; supports one-shot campaigns and a daily-supervised loop for the dashboard/operator path |
| `run_paper_sim_monitor.py` | — | Read-only paper simulation monitor, watch management, and local watch-trigger notifications |
| `run_signal_quality_report.py` | — | Read-only signal-quality report for scoring whether evidence signals were early enough to capture a target move |

## Canonical Operator

| Script | Make target | Purpose |
|--------|-------------|---------|
| `bot_ctl.py` | `make start` / `make stop` | Start and stop the bot |
| `run_bot_safe.py` | — | Canonical launch entrypoint |
| `run_dashboard.py` | `make dashboard` | Dashboard entrypoint |
| `run_daily_operator_flow.py` | `make daily-run` | Daily operator workflow |
| `killswitch.py` | `make kill-switch-on` / `make kill-switch-off` | Arm/disarm kill switch |
| `paper_stop.py` | `make paper-stop-now` | Stop paper campaign |
| `preflight.py` | — | Pre-launch checks |
| `run_preflight.py` | — | Preflight entrypoint |
| `maintenance.py` | — | Maintenance tasks |
| `op.py` | — | Operator command surface |
| `doctor.py` | — | Diagnostic |
| `bot_status.py` | — | Process status query |

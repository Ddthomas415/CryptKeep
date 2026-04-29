# Scripts Index

This directory contains 120+ scripts. They fall into these categories.
Use `make script-index` for a quick operational reference.

## Operational (run these day-to-day)

| Script | Make target | Purpose |
|---|---|---|
| `run_es_daily_trend_paper.py` | `make paper-run` | Run paper campaign |
| `check_promotion_gates.py` | `make check-gates` | Promotion gate status |
| `killswitch.py` | `make kill-switch-on/off` | Arm/disarm kill switch |
| `show_live_gate_inputs.py` | `make gate-inputs` | Live gate current values |
| `inject_test_fill.py` | `make inject-test-fill` | Inject test fill (paper only) |
| `run_candidate_scan.py` | `make candidate-scan` | Signal candidate scan |
| `live_reconcile.py` | `make live-reconcile` | Reconcile live positions |
| `show_control_kernel_status.py` | `make kernel-status` | Control kernel status |

## Evidence and Reporting

| Script | Purpose |
|---|---|
| `report_paper_run_diagnostics.py` | Paper run diagnostic report |
| `review_candidate_outcomes.py` | Candidate outcome review |
| `ingest_evidence.py` | Ingest external evidence |
| `export_diagnostics.py` | Export system diagnostics |
| `compare_candidate_vs_runner.py` | Compare candidate vs runner output |

## System Maintenance

| Script | Purpose |
|---|---|
| `rotate_logs.py` | Rotate log files |
| `doctor.py` | Repo health check |
| `validate.py` | Full validation suite |
| `pre_release_sanity.py` | Pre-release checks |
| `preflight.py` | System preflight |
| `repair_export.py` | Export repair artifacts |

## Market Data

| Script | Purpose |
|---|---|
| `run_tick_publisher.py` | Market data tick publisher |
| `run_ws_ticker_feed.py` | WebSocket ticker feed |
| `run_ws_ticker_feed_safe.py` | Managed-safe wrapper for WebSocket ticker feed |
| `collect_live_crypto_edge_snapshot.py` | Live edge snapshot |
| `run_crypto_edge_collector_loop.py` | Continuous edge collection |

## Live Trading (shadow/capped_live stages only)

| Script | Purpose |
|---|---|
| `live_submit_intent.py` | Submit a live order intent |
| `live_reconcile.py` | Reconcile live positions |
| `live_executor_tick.py` | Single live executor tick |
| `run_live_trader.py` | Live trader loop |
| `run_intent_consumer_safe.py` | Managed-safe wrapper for canonical live submit owner |
| `run_live_reconciler_safe.py` | Managed-safe wrapper for canonical live reconciler |

## Build and Release

| Script | Purpose |
|---|---|
| `build_desktop.py` | Build desktop app |
| `tag_release.py` | Tag a release |
| `bump_version.py` | Bump version number |
| `generate_release_notes.py` | Generate release notes |

## Archive / Experimental

The following scripts are not part of the current operational path.
They remain for reference but are not actively maintained:

`apply_pending_model_switch.py`, `approve_model_switch.py`,
`recommend_model_switch.py`, `replay_paper_losses.py`,
`find_strategy_signal_candidates.py`, `register_evidence_source.py`,
`set_evidence_webhook_secret.py`, `send_evidence_webhook.py`,
`phase82_apply.py`, `op.py`

---
*If a script you need is not here, check `ls scripts/*.py` or `make script-index`.*

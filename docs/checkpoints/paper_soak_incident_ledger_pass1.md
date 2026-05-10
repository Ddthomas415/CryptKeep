# Paper Soak Incident Ledger — Pass 1

**Date:** 2026-05-10  
**Scope:** classify persisted AI monitor incident reports into unique failure
families for the supervised paper-soak evidence window

This is an audit-only evidence ledger. It does not redefine gate policy or
recommend runtime changes.

## Evidence basis

- current paper-soak start from `scripts/report_supervised_soak_status.py --json`:
  - `started_ts_local = 2026-05-07T12:39:53`
  - equivalent UTC start for the current supervised soak window:
    `2026-05-07T16:39:53+00:00`
- current AI monitor status from `scripts/run_ai_alert_monitor.py --status`:
  - `incidents_written = 9`
  - `started_ts = 2026-05-07T16:39:53.284763+00:00`
- persisted incident reports under `.cbp_state/runtime/ai_reports/`
- `pipeline.log` `run_once_failed` lines and surrounding traceback context

## Summary

- persisted incident report count on disk: **9**
- reports inside the current supervised soak window: **6**
- reports before the current supervised soak window: **3**
- unique pipeline failure families inside the current supervised soak window:
  **3**
- all current-window pipeline failure families recovered without topology loss
  in the observed runtime evidence

## Current soak-window families

### Family A — Coinbase `RequestTimeout` on `v2/currencies/crypto`

- first report:
  - `ai_alert_monitor_20260507T175200Z.json`
  - `generated_at = 2026-05-07T17:52:00.583448+00:00`
- duplicate summary report:
  - `ai_alert_monitor_20260507T175500Z.json`
  - `generated_at = 2026-05-07T17:55:00.882940+00:00`
- underlying pipeline evidence:
  - `pipeline.log` line `4835`
  - `{'ok': False, 'note': 'run_once_failed', 'error_type': 'RequestTimeout', 'error': 'coinbase GET https://api.coinbase.com/v2/currencies/crypto'}`
- duplicate report count:
  - 2 persisted reports for 1 failure episode
- topology effect:
  - none shown
  - current and surrounding log lines show the pipeline resumed normal
    `multi_symbol_cycle` output immediately after the failure line
- evidence classification:
  - recovered warning-quality failure episode

### Family B — Coinbase `RequestTimeout` on `api/v3/brokerage/market/products`

- first report:
  - `ai_alert_monitor_20260508T015047Z.json`
  - `generated_at = 2026-05-08T01:50:47.633367+00:00`
- duplicate summary report:
  - `ai_alert_monitor_20260508T015247Z.json`
  - `generated_at = 2026-05-08T01:52:47.834726+00:00`
- underlying pipeline evidence:
  - `pipeline.log` line `7187`
  - `{'ok': False, 'note': 'run_once_failed', 'error_type': 'RequestTimeout', 'error': 'coinbase GET https://api.coinbase.com/api/v3/brokerage/market/products'}`
- duplicate report count:
  - 2 persisted reports for 1 failure episode
- topology effect:
  - none shown
  - surrounding log lines return to normal `multi_symbol_cycle` output
- evidence classification:
  - recovered warning-quality failure episode

### Family C — Coinbase `NetworkError` on `v2/currencies/crypto`

- first report:
  - `ai_alert_monitor_20260509T173720Z.json`
  - `generated_at = 2026-05-09T17:37:20.510363+00:00`
- duplicate summary report:
  - `ai_alert_monitor_20260509T174421Z.json`
  - `generated_at = 2026-05-09T17:44:21.187906+00:00`
- underlying pipeline evidence:
  - `pipeline.log` line `18443`
  - `{'ok': False, 'note': 'run_once_failed', 'error_type': 'NetworkError', 'error': 'coinbase GET https://api.coinbase.com/v2/currencies/crypto'}`
- duplicate report count:
  - 2 persisted reports for 1 failure episode
- topology effect:
  - none shown
  - surrounding log lines return to normal `multi_symbol_cycle` output
- evidence classification:
  - recovered warning-quality failure episode

## Pre-current-window persisted reports

These reports remain on disk and contribute to `incidents_written = 9`, but
they predate the current supervised soak window start.

### Pre-window Report 1 — service-down plus pipeline error burst

- report:
  - `ai_alert_monitor_20260507T062115Z.json`
- severity:
  - `critical`
- summary:
  - `service down: intent_consumer, market_ws, reconciler; 1 runtime log error burst(s)`
- evidence status:
  - historical only for the current soak
- notes:
  - `expected_services` is `None` in this report
  - this report is not attributable to the current paper-soak window

### Pre-window Report 2 — executor down

- report:
  - `ai_alert_monitor_20260507T140438Z.json`
- severity:
  - `critical`
- summary:
  - `service down: executor`
- evidence status:
  - historical only for the current soak
- notes:
  - this is the only persisted report in the set that directly indicates a
    managed-service topology failure
  - it predates the current supervised soak start

### Pre-window Report 3 — pipeline network burst

- report:
  - `ai_alert_monitor_20260507T163721Z.json`
- severity:
  - `warn`
- summary:
  - `1 runtime log error burst(s)`
- evidence status:
  - historical only for the current soak
- notes:
  - report timestamp is about 2 minutes before the current AI monitor
    `started_ts`
  - not attributable to the current supervised soak window

## SHOWN conclusions

- `incidents_written = 9` is a historical cumulative count, not a count of
  unique current-window failures.
- the current supervised soak window has **3** unique pipeline failure episodes
  in visible evidence, each represented by **2** persisted reports.
- all 3 current-window families are warning-quality external Coinbase
  connectivity failures and show immediate recovery in the pipeline log.
- the only persisted topology-failure report in the visible set is pre-window:
  `ai_alert_monitor_20260507T140438Z.json`.

## UNVERIFIED points

- whether any non-persisted or rotated incident artifacts existed before the
  current on-disk set
- whether the 3 current-window failure families should be treated as acceptable
  warnings or as Section 4.1 clock-reset events
- whether the pre-window `critical` reports have any residual operator meaning
  for final paper-gate sign-off

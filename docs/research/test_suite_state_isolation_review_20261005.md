# Test suite wrote into the real state directory - 2026-10-05

Reviewer: Claude. Result: patch 0066 (`07fd078e`, test infrastructure only) and patch 0067
(`7244a65d`, outcome log path), bundle rev78 folders 74 and 75. READY_FOR_INDEPENDENT_REVIEW.
Not pushed.

## How it was found

`.cbp_state/data/risk_sink_failed.flag` on this laptop, dated 2026-09-23 04:10, contains
`"error": "RuntimeError:record boom", "fill_id": "fill-2"`: the literal strings of
`tests/test_fill_sink_logging.py`.

## Finding (P1)

Tests that set no `CBP_STATE_DIR` of their own wrote into `<repo>/.cbp_state`. One full run in
the review clone changed the order-block flag, `kill_switch.json`, `live_arming.json`,
`system_guard.json`, `user.yaml`, the operator-event journal, both heartbeat files,
`critical_alerts.jsonl`, `execution.sqlite` and seven other stores.

## This laptop (read-only, checkout `620bc8dbe`)

| File | Last modified |
|---|---|
| `data/risk_sink_failed.flag` | 2026-09-23 04:10 |
| `data/live_arming.json` | 2026-09-23 04:09 |
| `runtime/kill_switch.json` | 2026-09-23 04:09 |
| `runtime/system_guard.json` | 2026-09-23 04:15 |
| `runtime/config/user.yaml` | 2026-09-23 04:09 |
| `data/operator_events/operator_events.jsonl` | 2026-09-23 04:15 |
| `runtime/outcomes/strategy_outcomes.jsonl` | 2026-09-23 04:15 |

All seven were last written inside one six-minute window, the length of a test run.
`strategy_outcomes.jsonl`: 450 rows, 284 carry `intent_id: "intent-1"`, a test fixture id.
None of the 12 `.cbp_state_challengers/*` directories has an outcome file of its own.

Consequence for earlier notes: anything I reported from this laptop's `user.yaml`,
kill-switch or arming state describes what the last test run left, not an operator setting.

## Patches

- 0066: the suite runs in a per-session temporary state directory; the run fails if one of
  six operator-only real files changes.
- 0067: the outcome log follows the state directory instead of the working directory.

With both, a full run (4844 passed, 33 skipped, 0 failed) changes no file in the real state
directory.

## Not fixed

- Existing test-written files and rows are untouched. Removing the flag, and deciding what
  to do with test rows in the operator-event journal and outcome file, are operator actions.
- The selector's outcome evidence cannot change which strategy is selected (clamped to +/-3
  against rank steps of 10). Recorded by test.
- Still relative to the working directory: `services/backtest/selector_run_store.py`,
  `services/backtest/backtest_run_store.py`, `services/market_data/market_intelligence.py`,
  `scripts/paper_stop.py`.

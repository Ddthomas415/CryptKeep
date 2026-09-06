# Bounded Extended Venue Observation Trial

Active role: ENGINEER. Risk: HIGH (background campaign launch configuration).
Status: READY_FOR_INDEPENDENT_REVIEW. No host deployment or launch performed.

## Objective and Design

Compare a full UTC-cycle observation window with the existing 15-minute daily
sampling on Binance and Gate.io. Use the existing managed paper collector and
EMA preset; preserve signal filters and canonical ES policy.

The new explicit manifest is
`configs/paper_evidence_campaigns.hetzner.extended_observation.json`.
It is not referenced by the default campaign manifests or Make targets.
Each trial uses its own state directory and session strategy ID:

- `ema_cross_gateio_btcusdt_24h_trial`.
- `ema_cross_binance_btcusdt_24h_trial`.

Each config sets `runtime_sec=86400`, `max_daily_attempts=1`, and
`max_loops=1`. The launcher now passes an optional positive integer
`max_loops` through to the existing collector CLI. Omitting this field leaves
existing daily-loop commands unchanged. Explicit zero, negative, boolean,
fractional, string, or null values are rejected rather than interpreted as
unbounded operation.

`max_loops` bounds collector iterations, not successful sessions: unreachable
preflight or an already-recorded day may end the trial without any strategy
window. A successful run ends after one strategy window even if it crosses UTC
midnight. The collector polls its stop flag and exits with `reason=max_loops`;
this is an expected end state, not a request for automatic recovery. Do not
register this manifest with persistent restore jobs.

## Runtime Boundaries to Review

- 24 hours is the strategy-window target. Startup, shutdown, evidence generation,
  blocking venue calls, and component cleanup can add time. This is not a hard
  wall-clock kill timer or a guarantee that every child exits at hour 24.
- `poll_interval_sec=300` controls the daily collector loop, not OHLCV request
  pacing. The strategy runner reads `strategy_runner.loop_interval_sec` from
  the isolated user configuration; the tick publisher has a separate interval.
  Existing request cadence is unchanged by this patch. A full-day run can
  perform roughly 96 times the requests of a 15-minute window at the same
  rate, before considering retries and actual venue latency.
- Before launch, inspect effective trial fee/slippage, preset filters, strategy
  polling, and tick intervals. Record their values and compare with the daily
  controls. Do not copy credentials into trial state or change shared config.
- New trial state starts independently; it does not inherit daily-campaign
  positions or evidence. Existing position rows are preserved by the managed
  collector when a state directory is reused. Stopping observation is not an
  instruction to liquidate positions; any unclosed paper position must be
  reported separately at the end.
- Source code preserves existing ownership checks and cleanup behavior. This
  change is CLI wiring, not new child-process supervision or an OHLCV reliability
  fix. Host lifecycle and request-rate proof remain part of launch verification.
- Independent review identified pre-existing exceptional-exit paths that can
  bypass tick-publisher/paper-engine cleanup, and normal cleanup does not check
  every stop-wait result. Collector termination is insufficient terminal proof.
  Before launch, define a host deadline and verify scoped child cleanup plus
  pending-intent and position reconciliation. Preserve unclosed positions;
  do not fabricate exits to finish the trial.

## Reviewed Launch Procedure

After independent review and deployment of the accepted change, use the host
app venv and explicitly select the trial manifest and campaign. Preflight must
run on Hetzner. Example command for each isolated campaign:

```bash
cd /srv/cryptkeep/app
./.venv/bin/python scripts/restore_paper_campaigns.py --config configs/paper_evidence_campaigns.hetzner.extended_observation.json --campaign ema_cross_gateio_btcusdt_24h_trial --restore --preflight-ohlcv
CBP_VENUE=binance CBP_ALLOW_BINANCE=1 ./.venv/bin/python scripts/restore_paper_campaigns.py --config configs/paper_evidence_campaigns.hetzner.extended_observation.json --campaign ema_cross_binance_btcusdt_24h_trial --restore --preflight-ohlcv
```

Launch close together, record actual start times, and compare only overlapping
observation intervals. Confirm each reaches collecting with valid public data;
record all existing collector PIDs first and confirm they are unchanged.
Do not claim success based solely on the detached-start response.

Status is read through the same explicit manifest:

```bash
./.venv/bin/python scripts/report_supervised_soak_status.py --config configs/paper_evidence_campaigns.hetzner.extended_observation.json --json
```

An early stop must target the specific trial state, for example:

```bash
CBP_STATE_DIR=/srv/cryptkeep/app/.cbp_state_challengers/ema_cross_gateio_btcusdt_24h_trial ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --stop
```

Use the corresponding Binance trial path to stop Binance. Inspect owned child
processes after termination; preserve state and evidence. Do not issue global
service restarts, delete state, or restart a finished trial automatically.

## Measurement and Acceptance

Record elapsed strategy runtime, venue errors/blocked intervals, final snapshot
timestamps and gaps, order/fill/closed-trade deltas, open positions, and evidence
writer health. Retain dataset hashes and actual effective config values.
Replay closed snapshot bars with the same preset to distinguish raw crossovers
and filter reasons, explicitly labeling replay as hypothetical and excluding
the last candle if its close cannot be established. A final runner status is
not a full per-bar diagnostic history.

Successful observation requires valid data over the claimed window, correct
identity/state isolation, and verified bounded completion. Zero trades is a
valid measurement. Missing coverage or a hung process is an incomplete trial,
not a strategy failure. One day is an operational cadence experiment, not
statistical validation of profitability or grounds to change promotion gates.

Implementation verification:

- `./.venv/bin/python -m pytest -q tests/test_bounded_venue_observation.py tests/test_paper_campaign_recovery.py tests/test_run_paper_strategy_evidence_collector.py`:
  46 passed, including existing collector cap/cleanup tests and new manifest
  isolation, unchanged legacy commands, and invalid-bound rejection checks.
- `git diff --check`: passed.
- Actual 24-hour execution, request volumes, and post-run host child cleanup:
  UNVERIFIED; no trial has been launched by this branch.

Independent AUDITOR verification: 46 tests above and 33 tests from
`tests/test_paper_strategy_evidence_service.py tests/test_paper_runner_lifecycle.py`
passed. The reviewer found no new merge-blocking implementation defect and
assessed the implementation as ACCEPTED_WITH_RISK, subject to the pre-existing
cleanup/continuity limitations above. That assessment did not cover the final
runbook additions. The complete packet remains READY_FOR_INDEPENDENT_REVIEW;
host launch is INCOMPLETE and has not been performed.

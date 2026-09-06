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

## Supervised Launch Procedure (Review Pending)

The opt-in user units are `packaging/systemd/trials/cbp-gateio-observation.service`
and `cbp-binance-observation.service`. They are not included in the default
installer and have no Install section: do not enable them for boot or recovery.
After independent review and accepted deployment, verify them with the host's
systemd verifier before linking them into the cryptkeep user manager. Preflight
must run on Hetzner before explicit start. Do not use the detached restore
command for this trial; the unit must own the foreground collector.

Units pin Type=exec, RuntimeMaxSec=25h, TimeoutStopSec=30s,
KillMode=control-group, Restart=no, restrictive file permissions, and separate
state/session identities. These are timeout escalation controls, not a graceful
drain guarantee. At expiry, termination can occur during SQLite/evidence work;
terminal reconciliation remains mandatory. Earlier cooperative stop instructions
remain appropriate before the deadline. No ExecStop command claims to await a
graceful drain. A manual second start is possible and must not be automated.

The unit command pins tick interval to 2s and uses the same manifest strategy,
symbol, source, runtime, drain, and loop caps. No shared environment file is
loaded. This does not establish every ambient/default configuration value;
effective configuration inspection remains a launch prerequisite.

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

## Terminal Verification Checklist

Before launch, record a UTC escalation deadline of launch time plus 25 hours
(24-hour strategy target plus one hour for startup/reporting). This is a trial
operations policy, not an enforced timer. Launch is not ready until a host-side
deadline mechanism or an available operator owns that check; a laptop reminder
alone is insufficient. If the deadline is exceeded, request the scoped stop
above and mark coverage INCOMPLETE rather than extending the window silently.

At normal completion or escalation:

1. Record collector status and its `started_components` and `reused_components`
   maps. In a fresh isolated trial, unexpected reused components require
   investigation, not blanket termination.
2. Check the collector and all four component identities: strategy runner,
   paper engine, tick publisher, and paper simulation monitor. Their state-local
   PID records are `runtime/locks/strategy_runner.lock`,
   `runtime/locks/paper_engine.lock`, `runtime/locks/tick_publisher.lock`, and
   `runtime/health/paper_sim_monitor.pid.json`. Confirm any live PID's command,
   start time, and state-directory association before acting; a lock file alone
   is not proof of ownership and a missing lock is not proof of process exit.
3. If owned children survive collector exit, use their existing state-scoped
   stop APIs. Capture timeout/failure explicitly. Do not signal by process name,
   delete locks, or reuse stale PIDs. Escalation to process termination needs
   verified identity and must exclude every pre-trial campaign PID.
4. Once all trial writers are confirmed stopped, inspect these databases using
   SQLite URI `mode=ro` (never construct a store that initializes missing files):
   `data/intent_queue.sqlite` (`trade_intents`), and
   `data/paper_trading.sqlite` (`paper_orders`, `paper_fills`, `paper_positions`).
   Record queue/order status counts, fill count, and every position's quantity,
   average price, and realized PnL. Preserve pending work and open positions as
   residual state; do not mark intents consumed, flatten positions, or restart
   the engine merely to improve the completion report. Missing/unreadable state
   is UNVERIFIED, never an empty/flat result.
5. Capture final artifact hashes after writers stop, alongside actual stop time
   and the pre/post PID comparison for existing campaigns. Operational completion
   requires stopped trial processes and accounted-for residual state, not zero
   positions. Unexplained residuals or surviving writers mean INCOMPLETE.

The host deadline mechanism and scoped shutdown rehearsal are still UNVERIFIED.
This checklist defines the required evidence; it does not claim it was executed.

### Host Rehearsal Plan and Result

Independent AUDITOR review accepted the terminal checklist at `b4641611b`
as documentation only; no actionable defects were found. Host launch remains
INCOMPLETE.

First inspect the host systemd version, user manager availability, and linger
state without changing them. If supported, rehearse a uniquely named transient
user service with dummy parent/child processes only, including a child started
in a separate POSIX session. Use a short runtime timeout, `Restart=no`, and
`KillMode=control-group`; verify the entire unit is empty after timeout and
unrelated campaign PIDs are unchanged. Preserve journal/result evidence before
removing the dummy unit. This is not a real collector shutdown proof.

The candidate trial supervisor would run the collector in foreground (omit
`--detach`), with `RuntimeMaxSec=25h` and a finite stop timeout. Do not wrap the
existing detached restore command as the service's main process. A timeout is
an INCOMPLETE trial with possible residual intents, not a successful finish.
Do not install or launch this candidate until host support and the rehearsal
are verified and the final supervision configuration is reviewed.

These candidate controls follow the upstream systemd
[service runtime documentation](https://raw.githubusercontent.com/systemd/systemd/main/man/systemd.service.xml)
and [control-group shutdown documentation](https://raw.githubusercontent.com/systemd/systemd/main/man/systemd.kill.xml).
Installed-host behavior must still be tested. No linger, credential, persistent
unit, or existing service changes are authorized by this preparation step.

SHOWN host rehearsal, 2026-09-06 06:58:33-06:58:41 UTC:

- systemd 255.4-1ubuntu8.17, user manager running, `Linger=no`.
- Transient unit `cryptkeep-dummy-deadline-1788677913738367016.service`
  used `Type=exec`, `RuntimeMaxSec=6s`, `TimeoutStopSec=2s`,
  `KillMode=control-group`, and `Restart=no`.
- Dummy parent PID 1514992 spawned child PID 1514994 with a separate POSIX
  session; the child deliberately ignored SIGTERM.
- Journal recorded runtime expiry at 06:58:39 and SIGKILL of the remaining
  child at 06:58:41. Terminal state was `Result=timeout`, `MainPID=0`,
  `ActiveState=failed`, empty `ControlGroup`. No matching dummy remained.
- Pre/post command and start-time inventory was identical for existing app
  Python processes: Coinbase collector 1287182, crypto-edge collector 1496067,
  Gate.io collector 1499165, Binance collector 1501788.
- Failed transient-unit state was reset only after journal capture (exit 0).
  No app state, credentials, persistent units, or existing services changed.

This proves dummy cgroup timeout cleanup on the installed host, not real
collector shutdown, graceful intent drain, or 25-hour persistence after logout.
Linger remains disabled. A durable supervisor choice and real trial effective
configuration/terminal reconciliation remain UNVERIFIED; no trial launched.

Follow-up host inspection on 2026-09-06: `user@UID.service` was active with
`StopWhenUnneeded=no`, four sessions were present, and `Linger=no` remained.
`sudo -n -l` required a password. Current sessions do not prove availability
after final logout. Enabling linger is a proposed persistent host change,
not performed here. Host checkout remained e38c342de9eb8209bdd7fdd44ca75cf757901fa2.
Both proposed trial state directories were absent. The manifest-defined daily
Gate.io/Binance state directories existed but had no `runtime/config/user.yaml`.
This establishes absence of state-local overrides, not a complete effective
configuration audit. No configuration or app state was created.

### Approved Linger Change, 2026-09-06

After the explicit question about enabling linger, the operator instructed
proceed. Executed `loginctl enable-linger cryptkeep` on Hetzner; it succeeded
without sudo authentication. A second SSH connection independently returned
`Linger=yes` and user manager `running`. Existing collector PIDs/start times
1287182, 1496067, 1499165, and 1501788 were unchanged. This supersedes the
earlier `Linger=no` snapshot, not the still-open real trial validation.

Rollback, if separately requested: `loginctl disable-linger cryptkeep`.
Assess active user units before rollback, because removing linger may affect
their availability after final logout. No service restart, app deployment,
trial launch, or credential change was performed. A final-logout experiment
was not attempted because existing sessions/campaigns must not be disrupted.

## Host Unit Parser Verification, 2026-09-06

Independent unit review found no blocking defect and accepted implementation
with risk. Added its requested test pins for WorkingDirectory, daily-loop,
and notification parity. The 26-test trial/collector slice passed afterward.

Copied only the two unit files to
`/tmp/cryptkeep-unit-verify.UkWgLA/packaging/systemd/trials/` on Hetzner.
`systemd-analyze --user verify` initially could not initialize its manager
because the SSH environment lacked a runtime directory. Retried with
`XDG_RUNTIME_DIR=/run/user/$(id -u)` after checking that directory exists:
exit 0, no parser diagnostics. This changed only the command environment.
No units installed, linked, enabled, or started.

Host/local SHA-256 values matched:

- Gate.io: `4115e9cc5aaef5da50ab0a65fa114996f6b39c7af769ad9e6b7286293069921c`.
- Binance: `a3d37939d3beffe1dbc5650a6044fd364b6b0ec1ce26f6e80f4126cabaae99db`.

Static parser success is not real collector shutdown proof. Also, a collector
failure can return exit zero: unit success alone is insufficient. Inspect
collector status, evidence, child membership and residual state before claiming
successful observation. Actual trial launch remains INCOMPLETE.

## Real Collector Rehearsal, 2026-09-06

Executed the deployed collector on host commit e38c342de in a unique transient
unit `cryptkeep-collector-rehearsal-1788702657525253826`, state
`/tmp/cryptkeep-collector-rehearsal-zr4qdhpa`. Gate.io, BTC/USDT,
public_ohlcv_5m, EMA, no first-signal override, 30-second strategy target,
one loop, runtime limit 120s and stop timeout 30s. This was a short lifecycle
rehearsal, not either production 24-hour trial or a Binance validation.

SHOWN: live cgroup contained collector 1515634, tick publisher 1515644,
paper engine 1515653, monitor 1515654, and strategy runner 1515663. No reused
components. Final unit inactive/dead, MainPID=0, empty ControlGroup,
Result=success; all recorded rehearsal PIDs absent. Existing collector
PID/start-time identities 1287182, 1496067, 1499165, 1501788 unchanged.

Strategy interval 13:51:08.210886-13:51:50.364774 UTC, reported duration
42.1548655s including overhead, stop_reason=runtime_elapsed. Collector stopped
with reason=max_loops, loops=1. A state-scoped stop request was issued, but
the recorded reason does not establish that it caused termination. Do not
claim cooperative-stop or forced-timeout coverage from this run.

Post-exit read-only SQLite checks: integrity_check=ok for intent_queue.sqlite
and paper_trading.sqlite; zero trade_intents, paper_orders, paper_fills,
paper_positions. Evidence generation was skipped because history was unchanged.
Health artifact SHA-256:
`67ec4781831eb21ddad2b08e4f3d37cb5e039ff69727bec34db8b9b8640f8c64`.
Temporary state is preserved. This establishes normal bounded lifecycle with
real collector children, not filled-position reconciliation, 24-hour data
coverage, or profitable behavior. Actual trial deployment remains unperformed.

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

- `./.venv/bin/python -m pytest -q tests/test_venue_trial_units.py tests/test_bounded_venue_observation.py tests/test_systemd_units.py`:
  21 passed. Tests pin unit limits, foreground execution, no automatic enable,
  explicit venue/state environment, and manifest command parity. Host unit
  parser validation and real collector shutdown are not covered by these tests.

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

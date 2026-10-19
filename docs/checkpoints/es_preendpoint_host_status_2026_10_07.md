# ES pre-endpoint host checkpoint

2026-10-07 23:36 UTC onward. AUDITOR. VERIFIED_ENV: actual Hetzner host,
cryptkeep user, existing isolated es_corrected_prospective_v1 state.

Read-only SSH inspection succeeded after user completed host authorization.
No service restart, file upload, environment/config change or database write.

## SHOWN

- Service active/running, PID 1553065, started September 21 01:27:11 UTC.
- Deadline timer next elapse October 13 00:00 UTC; points to trial stop service.
  Timer schedule is verified, future successful shutdown is not.
- September 13 through October 7 inclusive: 25 expected daily session files,
  none missing, each has an end record, 25 completed statuses.
- Latest session October 7 00:04:30-00:04:56 UTC; latest signal long,
  entry_allowed true, kernel_action null, capture marked captured.
- Read-only SQLite queries: zero intents, paper orders, paper fills and journal
  fills; no paper positions; paper cash_quote 10000.0.
- Signals from September 21 onward: 266 long, comprising 251 marked captured
  and 15 with no capture-status field. Missing-field timestamps were not yet
  compared with capture activation time. These counts do not verify input hashes.

## Proof boundaries and next action

Read-only inspection used systemctl show/list-timers, session/signal JSONL reads
and sqlite mode=ro SELECT queries. No repository runtime modules imported.
Zero trades is consistent with an unchanged long signal and crossover-only
entry. No reset, forced entry, extension or profitability conclusion follows.

Effective config/seed identity, captured-input replay and exact activation-boundary
coverage remain UNVERIFIED in this checkpoint. Next bounded check: compare the
15 missing capture records against activation, then verify input provenance and
resolved config against launch. Preserve the October 13 endpoint.

Acceptance: INCOMPLETE for full trial validity/economic evidence; bounded host
status inspection complete. No code tests run; no runtime change made.

## Subsequent capture and identity verification

SHOWN on actual host, same read-only scope:

- All 15 records without capture metadata are September 21 00:02:29-00:02:46
  UTC, before the authorized capture restart at 01:27:11 UTC. Zero missing
  capture-status records after that boundary in the inspected files.
- First captured record September 22 00:02:17 UTC. Each completed day through
  October 7 has 15 or 16 captured records, totaling 251.
- Deployed verifier SHA256 matches the inspected local verifier:
  76c74caf0698de3dfbd9f93a9221699d7755ea2972d3b61bb60703b617f81a49.
- Host verifier over [September 22 00:00, October 8 00:00) returned exit 0:
  selected 251, verified 251, problems empty. Verifies captured bytes, loaded
  signal-code identity, source provenance and replayed signal fields only.
- All 19 stored input artifacts identify SMA200/ATR20, Coinbase BTC/USDT,
  daily public OHLCV; captured strategy trade_enabled true.
- Running service allowlisted environment confirms the isolated state directory
  and CBP_CAPTURE_ES_SIGNAL_INPUTS=1. No credentials read or printed.
- Seed user.yaml SHA256 exactly matches launch:
  81accfe4d0acf86d7bcc11c771899c977c3c04893f9093500b073a535e92a1f8.
- Service command remains the isolated SMA trend collector, Coinbase BTC/USDT,
  public_ohlcv_1d, runtime 20 seconds and daily loop; capture drop-in present.

These checks clear the capture-boundary uncertainty from the initial checkpoint.
They do not verify every resolved exit/risk/execution setting, execution replay,
future deadline behavior or trading efficacy. Earlier pre-activation signals
remain non-replayable, not retrospectively repaired.

Next: preserve the fixed endpoint and prepare its report using the existing plan.
No trial restart, extension, forced entry or new strategy selection is authorized.

## Subsequent current configuration resolution

Actual host probe read seed YAML and deployed source, extracted only pure resolver
functions using Python AST, and evaluated them in memory. Runtime modules were
not imported: config_editor has import-time ensure_dirs and runner/paper modules
initialize logging. No remote files were written by the probe.

Managed child selection was reconstructed from the inspected service command
and component environment builder: sma_200_trend, Coinbase BTC/USDT,
public_ohlcv_1d. This is current-source resolution, NOT observation of historical
child memory. Non-material context defaults were supplied for resolver completion;
context policy is outside this proof.

SHOWN, contract assertions passed:

- SMA200, ATR20; preset es_daily_trend_v1; strategy trade_enabled true.
- Quantity 0.001 BTC; allow_first_signal_trade false.
- stop_loss_pct, take_profit_pct, trailing_stop_pct all 0.0; max_bars_hold 0.
- position_aware true; sell_full_position true.
- Paper initial cash 10000 USDT, fee 7.5 bps, slippage 5 bps.

Deployed source SHA256:

- runner: 3ef9a8f161a5f639d68e1eaad6fcfac2b6cf46ff7e5bd3da373be9057e776208
- paper: 245a41752c993213359447d071674bcdfd0a658134bac5da010dda97284a4c59
- presets: 002735111eb3eda44e940e98756a80fc5b7a571b08d05d9edf611e988386fd95
- config_tools: 50fcdb03ee344f2b480b9c112301f3554b26c4ecef601b0bb6da14e4eff7abcf

Seed identity and present resolver agree with the launch contract. This is not
proof that every past child used those settings, every risk field is enforced,
the fee is a live account rate, or execution behaves correctly. No trade exists
in this trial to verify costs against actual fills. Endpoint report must preserve
these distinctions and refresh status after October 13.

## October 8 read-only continuity check

Host observation October 8 15:04:07 UTC (11:04 AM America/New_York).
Service active/running. October 8 session end at 00:05:24 UTC reports completed,
reconciliation pass, no critical error or infrastructure halt, zero_trade_run true.
This is session-reported zero trading; accounting databases were not re-queried
in this check. October 7 database counts remain the last direct accounting proof.

Same deployed verifier over [September 21 01:27:11, October 9 00:00) returned
exit 0: 267 selected, 267 verified, no problems. The upper bound is a selection
boundary, not a claim that future observations were collected. Sixteen additional
records since the previous check pass signal replay. No remote mutations.

Next endpoint remains October 13 00:00 UTC (October 12 8:00 PM New York).
Actual monthly infrastructure cost requested from operator; not estimated silently.

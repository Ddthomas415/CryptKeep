# Inactive Group A paper profile candidates

Bot relation: BOT_RULES. Proposed configuration and synthetic integration only.
Runtime files were inspected in the prior local inventory; loaded processes,
effective server configuration and actual metadata were not checked here.
Checked against Git and latest work log 2026-11-14T11:58:40Z.

Submitted status: READY_FOR_INDEPENDENT_REVIEW. Dated closeout 2026-11-14T12:02:11Z:
separate Nash GATE ACCEPTED_WITH_RISK for inactive artifact only; independently
18passed/1xfail and raw fresh regression1failed. Receipt in INDEPENDENT_REVIEW.md.
Fresh-account readiness: INCOMPLETE. R10 remains STOPPED. Nothing is installed,
loaded or started. This closeout text was added after review; YAML/test hashes unchanged.

### Dated source-repair follow-up - 2026-11-14T12:20:15Z

Owner subsequently continued the explicitly recommended offline initializer repair.
The new source candidate writes authoritative currency only for a genuinely fresh
ledger; existing currency/equity history prevents fresh certification. All nine
profiles now pass unseeded initialization/sizing checks in temporary state.
Author consolidated result243passed5.24s, including this unchanged test file with
--runxfail. Separate source review pending; source READY_FOR_INDEPENDENT_REVIEW,
not deployment/commissioning. Evidence: `../paper_account_currency_20261114/`.
The earlier18pass/1xfail and rawfailure observations below remain historical.
Source review closeout2026-11-14T12:19:55Z: separate Nash ACCEPTED_WITH_RISK,
independently25focusedpasses including all9freshprofiles and the oldrawregression.
Source bootstrap gap closed for genuinely fresh accounts, not operating readiness.
Original YAML/test bytes and original manifest are preserved; its old store hash
does not describe the repaired source. No actual profile or ledger is changed.

## Practical result and discovered blocker

SHOWN: nine separate YAML files now specify the three frozen default presets
on BTC/USD, ETH/USD and SOL/USD. Real configuration loaders resolve their
canonical strategy names, unchanged strategy parameters, hourly public source,
15-second strategy loop, USD1,000 initial cash, 50bps per-side fees and zero
modeled slippage. Every file explicitly enables paper mode, disables live
execution/arming, requires fresh snapshot quotes and hourly candle quality,
disables exchange-price fallback, and selects available_cash_v1 sizing.

SHOWN: these profiles do **not yet bootstrap usable fresh cash-sized accounts**.
`PaperEngine._ensure_cash_initialized` calls `initialize_account`, which writes
cash, realized PnL and an origin receipt containing currency, but does not write
the standalone `paper_state.quote_currency` required by `entry_cash_snapshot`.
The sizing helper catches KeyError and refuses entry. Existing sizing fixtures
manually supply this key. The earlier accepted seeded-account tests therefore
did not prove fresh initialization; this narrows their conclusion, not their
recorded test results. Group B's fresh cash-sized accounts share this gap.
No actual financial loss, live order or deployed failure is established.

Cause: engineering interface defect and integration-verification omission.
Smallest proposed correction: write the authoritative currency atomically when
creating a genuinely fresh account, alongside its original cash/origin receipt;
do not reset cash/history, infer legacy currency or silently migrate old accounts.
This is a **proposal, not implemented or approved by these profile files**.

## Files and isolation

| Candidate filenames (under profiles/) | Preset / resolved strategy | Separate proposed state leaf |
|---|---|---|
| breakout-default-btc.yaml, breakout-default-eth.yaml, breakout-default-sol.yaml | breakout_default / breakout_donchian | Same basename without .yaml |
| ema-cross-default-btc.yaml, ema-cross-default-eth.yaml, ema-cross-default-sol.yaml | ema_cross_default / ema_cross | Same basename without .yaml |
| mean-reversion-default-btc.yaml, mean-reversion-default-eth.yaml, mean-reversion-default-sol.yaml | mean_reversion_default / mean_reversion_rsi | Same basename without .yaml |

Existing `services/control/group_a_account_units.py` defines the corresponding
proposed `/srv/cryptkeep/state/<release>/<account>/runtime/config/user.yaml`
paths and clean environment assignments. That renderer still emits non-startable
fragments, not an installer. No release, service user, actual target directory,
permission, capacity or deployment is selected here. No actual state directories
or nine ledgers are provisioned. Each eventual account must have its own queue,
ledger, strategy state and public cache; one global shared cache is not substituted.

Inactive means unapplied review files. `paper_trading.enabled: true` is necessary
for the intended guarded policy; it is not permission to launch them. No actual
user.yaml was copied, read, overwritten or used as a template in this task.
Only nonsecret settings derived from the frozen spec and accepted source appear.

## Frozen behavior preserved

- Strategy/preset parameters, risk policy and code are unchanged. No unrelated
  preset risk fields are copied. No qty, risk, exit-control or first-signal override
  is supplied. Runner fallback exits remain 3% stop / 6% take-profit / 2% trailing /
  60 bars (strategy_runner.py run_forever), not preset-defined values.
- Hourly source still admits forming candles under the frozen behavior. The
  freshness guard is not a completed-candle signal change. No one-hour execution
  delay from the separate 25-symbol ED-002 study is imported into Group A.
- USD1,000 initializes each independent hypothetical account, never resets it
  at restart or before an entry. Subsequent entries use remaining cash after
  costs and quantity rounding. No deposit or live allocation is modeled here.
- Market fills still use the engine's midpoint plus configured slippage (zero).
  Ask-based sizing reserves cash conservatively; it does not turn fills into
  observed ask/bid executions. Recorded bid/ask evaluation remains required.
- Group B selection keys are absent, not null. Group B remains staged after
  Group A capacity; the original 25-symbol mandate is unchanged.
- BA-24/exposure controls are neither fixed nor bypassed. R7 sample/drawdown
  adoption, commissioning, backup/monitoring and actual-start authority remain
  outstanding. No original acceptance criterion is weakened.

## Verification and exact limits

VERIFIED_ENV: existing local venv, temporary synthetic state only. Network and
subprocess attempts are test failures. The real configuration loader, resolver,
paper provisioning target validator, metadata cache reader, strict quote/candle
gates, sizing and PaperEngine/SQLite buy/sell accounting are exercised.
Operational read-only, market-quality, exposure-policy and evidence version
stamps are explicitly stubbed in the fixture; these checks do not certify them.
No actual strategy signal, runner loop, queue-consumer lifecycle, publisher
fanout, installed service, host permission or live market execution is tested.
Existing accepted runner/consumer regression evidence is reused, not rerun.

Command:

```sh
./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
  docs/review_artifacts/paper_profile_candidate_20261114/test_profiles.py --tb=short
```

Author result: **18 passed, 1 xfailed in 1.26s**. This is not a green readiness
result or a full suite. Nine seeded-state cases load all profiles, validate
identity and cash affordability, charge modeled fees, preserve cash on engine
reconstruction, sell with missing candles but fresh quotes, reuse sale proceeds,
and refuse missing-candle buys/stale quotes. Eight policy mutation cases refuse
provisioning, and one roster check binds the distinct existing unit state paths.
The separate strict expected-failure regression preserves the fresh bootstrap gap.
To expose it as an ordinary failure, use the same command with `--runxfail` and
select `::test_fresh_account_is_immediately_readable_by_cash_sizing`.

During fixture development, invalid release-label syntax, metadata timestamped
after its injected read clock, and blocked git provenance subprocess caused
failures. Only test setup was corrected; no production checks were relaxed.
The fresh-currency omission is distinct and intentionally remains unresolved.

## Requirement accounting and next boundary

DONE: nine explicit isolated candidate settings, canonical/default strategy
resolution, adopted paper sizing/cost/strict-input contract, synthetic seeded
account checks, preserved failing bootstrap evidence. PARTLY DONE: fresh-account
compatibility (blocked by missing authoritative currency). NOT DONE: actual
metadata refresh/cadence, real target provisioning/permissions, source deployment,
monitoring, R10, commissioning, experiment activation or forward performance.
Independent artifact review and final hashes are recorded alongside this file.

Before applying profiles, independently review and correct the fresh initializer
contract, then identify the exact approved target and obtain operational scope.
Do not seed a production currency key by hand to make the check pass. Legacy
accounts without independently known currency must remain unresolved.

What could overturn this finding: a verified production initializer/provisioning
path already writing the authoritative standalone currency before sizing. No such
writer was found in the searched services/storage/scripts sources; external
provisioning and actual server state remain UNVERIFIED.

What do I know that could change the owner's decision that I have not yet said?
Correct YAML does not resolve the fresh-account interface defect. The deliberately
seeded integration cases demonstrate accounting compatibility, not a working new
simulation. This pack must not be installed as evidence that commissioning passed.

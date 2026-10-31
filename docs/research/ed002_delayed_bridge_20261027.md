# ED-002 fixed one-hour delay: synthetic implementation

2026-10-27. Active role ENGINEER. Risk HIGH (financial/research timing).
State READY_FOR_INDEPENDENT_REVIEW. No experiment activation or operations.

## Delivered Scope

Operator chose "Use a fixed one-hour execution delay (Recommended)" under
ED002-TIMING-20261027, then instructed "carry out the next steps". This continues
the stated synthetic-only extension, not a market study or adoption of proposed
capital, fees, rounding, freshness, horizon or inference choices.

Added `services/backtest/delayed_signal_bridge.py` and its synthetic tests. The
existing `FrozenSignalBridge` remains the immediate-next-open interface. Its
only source change is an optional `HourlyPanel.window(..., available_by_ms=...)`:
default cutoff remains the window close, later cutoffs do not extend the signal
window, and a cutoff before the window close is rejected. Reversing just this
extension reproduces its independently accepted SHA256
`86825dfab40c82752d626b88586e1c66aa8832e8339b2c54a6452b9bc45c4acf`.
The accepted shared ledger and frozen strategy snapshot remain byte-identical.

## Clock Contract Implemented

- Signal bar closes at T. Frozen default signals see exactly the 300-hour window
  ending T, with original receipt timestamps no later than E=T+1 hour. The
  intervening bar never enters that signal. A later receipt is INCOMPLETE, not
  backdated or retried. Original receipt records are copied, never rewritten.
- Target formation at E uses the actual ledger's pre-fill wallet and T's close
  marks. It does not use the intervening close for features or target sizing.
  Units/cash are NOT rewound to an earlier wallet. This implements delayed
  signals with shared-capital allocation, not a frozen-quantity order submitted
  at T. Incidental resizing remains disclosed by the existing shared ledger.
- Signal eligibility is conservatively required to have been known/effective
  at T, as in the original signal path. This is distinct from the receipt
  allowance for candles. The unchanged ledger additionally checks the rule
  known by E and effective at execution E; an intervening disable can refuse
  the entry. Permission intervals are caller inputs, not created here.
- Modelled fills use the execution frame's open at E, not T's close/open. The
  intervening/current completed frame is checked against raw outcome rows for
  price consistency. Those prices can be observed later: this is ex-post
  valuation/fill-model data, NOT a claim they were available to the decision.
  No late outcome price is used in the signal or signal-close target marks.
- Incumbent Sunday-candle targets retain their original source formula and
  become eligible for the Monday 01:00 UTC modelled fill, rather than 00:00.
  Non-Sunday observations do not create extra incumbent rebalances.
- Traces retain signal-bar time, signal close, receipt cutoff and model execution
  time. The ledger's existing `signal_bar_ts_ms` remains its scheduling reference;
  delayed traces/trade annotations add `strategy_signal_bar_ts_ms` to distinguish
  the actual older strategy input. Financial fill records are not rewritten.

Controls use the same supplied frame sequence, first execution E and final
marked close as the candidate. A synthetic comparison test checks this. The
initial frame ends E and acts as the ledger decision frame, so candidate and
controls first fill at the following frame's open E. No pending order executes
beyond the supplied endpoint. This library does not invent activation dates,
add an unreported first hour to a prospective period, or claim a full 182-day
experiment exists. A future registration must explicitly align A, E, B and the
initial cash-only interval; horizon remains unadopted.

## Failure, Carry And Preservation

Missing required signal evidence, held marks or permission stays INCOMPLETE.
Known-ineligible flat assets do not require candles; unrelated assets do not
become incumbent signal requirements. Exhausted accounts remain terminal HOLD.
Missing execution opens expire the order as in the accepted ledger, without
latched retry. Known benchmark entry failure still needs comparison-level
INCOMPLETE handling before any market experiment; a mechanical cash-only control
is not a successful benchmark. No new benchmark acceptance gate was implemented.

Carry binds delay/policy identity, original receipt times, rules and outcome
rows already used in valuation, even when those outcome rows arrived later.
Changed historical inputs or switching to/from the immediate profile refuses
resume. Future rows after the closed prefix do not influence prior decisions.
Full versus split synthetic runs preserve units/cash/basis/pending state and
trade annotations exactly. Returned diagnostic equity on invalid paths is not
promoted into profit evidence.

Two existing model premises remain: one venue/common quote with no FX/yield,
and hypothetical full fills with explicitly supplied costs and precision.
One hour is a fixed modelling allowance, not measured latency, a guarantee of
data arrival or a live-fill promise. No status/minimum/rounding mapper was added.

## Verification

VERIFIED_ENV isolated synthetic command:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_delayed_signal_bridge.py tests/test_frozen_signal_bridge.py tests/test_shared_cash_research.py tests/test_next_open_research.py tests/test_harness_contracts_wp4.py
```

SHOWN: **157 passed in 5.13s**, comprising 28 new delayed cases and 129 prior
synthetic/compatibility cases. Earlier targeted development runs: 20 passed,
then 155 passed before the last two added cases. This is not a full-suite run.
Test-body socket/process guards prevent external work during tests; they do not
prove every imported module is permanently incapable of external behavior.

Cases include exact/+1ms/half-hour/full-hour receipt allowance, too-late receipt,
later opening prices, ignored intervening signals, signal-close sizing, separate
signal/execution permissions, gaps/conflicting outcomes, 25-wallet affordability
with fees, no latched retry, controls/endpoints, terminal pending intent, all
three real frozen families on synthetic data, weekly incumbent timing, full/split
carry, altered receipts and unreceived marking-price bindings.

No market data, strategy returns on historical prices, statistical calibration,
full pytest suite, service/account/credential/schedule, capital/risk, commit or
push operations. Proposed input contract and its review remain unchanged.

## Review Boundary

Separate review must assess causal clock separation, target-wallet/mark clocks,
eligibility checks, outcome-only inputs, carry identity and default compatibility.
Exact-source bindings accompany this checkpoint. This implementing thread does
not approve its own high-risk work. No market experiment can depend on this
extension until separate acceptance, complete protocol/data choices and explicit
run authorization.

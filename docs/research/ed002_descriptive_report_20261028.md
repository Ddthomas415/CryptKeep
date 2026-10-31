# ED-002 descriptive ledger reporting

Completed 2026-10-28. Role ENGINEER. Risk HIGH (financial reporting).
Implementation READY_FOR_INDEPENDENT_REVIEW; study readiness INCOMPLETE.

## Approval And Scope

Operator replied "approve. carry out the next steps" to the submitted mapper.
Record human ACCEPTED_WITH_RISK for that exact synthetic converter, not
independent review, real venue eligibility or statistical qualification.
Its source remains SHA256
`9c98bba24ed52bcb99e73ecc8bcd0bfa51ccd5e60447aa5f2017ef8cbb1e4099`.
Original contract, converter, engines, strategies and results are unchanged.

Added `services/backtest/descriptive_report.py` and synthetic tests for the
identified reporting gap. The reporter consumes ordered comparison chunk journals;
it does not execute strategies, acquire data, simulate orders or run inference.
It checks accounting on a private replay wallet using existing settlement logic.

## Interface And Definitions

`build_descriptive_report(cost_cases, symbols=..., monthly_overhead=20,
valuation_marks=...)` takes primary/stress journals and 25 explicit symbols.
Output Fractions remain exact. It chooses no dates and activates nothing.
Synthetic shorter periods must be an even number of UTC days for exact daily
and midpoint anchors; the adopted future 182-day horizon meets that constraint.

- Requires common clocks, the declared 25/25/50 fixed-unit mix, USD/coinbase
  profiles, 1000 model capital, 50/90 bps fees and 25 bps adverse adjustment.
  Profiles are model inputs, not actual balances or account fees.
- Requires complete seven-arm endpoints and actual initial benchmark buys.
  Reconciles chunk prefixes and every hourly cash/unit/NAV row. Cumulative
  trade journals are consumed once, not summed across resumed chunks.
- Rechecks reported costs, 0.01 USD settlement rounding and cost basis using
  the existing helper. This does not independently authenticate fills, original
  lot eligibility, source records or real liquidity.
- Marks come from historical frames or explicitly supplied original valuation
  sidecars. No stale substitution or future-known mark. Missing required
  evidence makes the case INCOMPLETE and withholds the combined headline.
- Reports net dollars/return, explicit costs, separate overhead, all-control
  gaps, hourly marked drawdown/duration, daily returns, exposure/time, turnover,
  exclusions, completed cycles, open inventory/basis and all symbol rows.
  Per-symbol realized plus unrealized contributions sum to account net PnL.
- Overhead is 20*12*elapsed_days/365, separate from the allocation wallet.
  Explicit-cost addback is labelled same-fill-path arithmetic, not a fee-free
  strategy rerun. Costs are not subtracted twice from net NAV.
- Halves retain boundary capital and cumulative cost/contribution anchors.
  Profits, costs and overhead add to the whole without resets or deposits.
  Half-period dollar gaps use each arm's carried capital, not independently
  funded equal-capital half-period accounts. Phase returns disclose their bases.
- Cycle counts assign exits to phases; their labelled lifetime PnL may include
  earlier entries/partial exits. Cycles are not independent samples. Hourly risk
  includes full recovery/unrecovered duration, but is not intrabar risk.
- Coverage includes terminal unexecuted decision traces, not submitted-order
  counts. Failed cases retain source status/reason, last recorded equity and
  costs as diagnostics, not completed economic results. No losing arm is removed.
- Keeps primary marked positions and dust. Terminal-liquidation sensitivity is
  None; no terminal sale is simulated. Marked profit is not realized user profit.

Different arm/case market histories or same-arm source bindings invalidate the
comparison. No confidence bounds, DSR, expected income, annualized earnings,
ranking selection or promotion gate: `experiment_pass` remains None.

## Verification

VERIFIED_ENV command, exit 0:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_descriptive_report.py tests/test_descriptive_metadata.py tests/test_delayed_research_comparison.py
```

SHOWN: **101 passed in 22.24s**: 25 report, 48 mapper, 28 existing comparison
cases. Initial report development: 21 passed in 17.71s. Added recovery-duration,
common-input/mix and historical-sidecar checks before final verification.

Fixtures use 25 invented labels/prices and scripted BUY/SELL/HOLD callbacks, not
actual strategy performance. They retain positive, negative and cash alternatives,
incidental resizes, a closed cycle and open risk. Full/split reports match across
all seven accounts and both costs; caller journals are unchanged. Corrupt money,
costs, hours, marks, trace, entry proof, profiles, recipes/mix or market inputs,
and partial/missing chunks cannot produce the combined profit headline.
Source hashes show all 13 submitted mapper/engine/contract inputs unchanged.

No full suite, old market backtest, random calibration or API request occurred.
External-work guards apply to test bodies/fixture execution, not system-wide
import/process certification. Actual 182-day scalability, source authenticity,
collection and current 25-asset identities remain UNVERIFIED.

## Remaining Boundary

Exact high-risk reporting code needs separate reviewer or human acceptance; this
implementing thread does not independently approve it. After reporting acceptance,
next is prospective input feasibility, warm-up/receipt coverage and source/data
bindings before future freeze/A/E/B. This is not acquisition or run permission.
No job/service/account/credential/capital/risk/trading, commit or push changes.
SB-1 and original confirmation requirements remain unchanged and unresolved.

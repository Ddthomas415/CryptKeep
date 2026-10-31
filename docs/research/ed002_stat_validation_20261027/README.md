# ED-002 adopted settings and synthetic statistical validation

2026-10-27 New York. Active role ENGINEER. Risk HIGH (financial inference).
Implementation READY_FOR_INDEPENDENT_REVIEW. Statistical validation INCOMPLETE.

## Result First

The proposed seven-day bootstrap is not ready to support confidence-based
promotion. In the fixed AR(1), rho=0.8, exchangeable null generator, it declared
at least one positive lower bound in **8/32 trials (25%)**, despite no expected
terminal-wealth advantage. The corresponding synthetic-trial Wilson 95% range
is approximately **13.25% to 42.11%**, above the nominal 5% familywise target.
The independent-noise generator yielded **1/32 (3.125%)**, range **0.55%-15.74%**;
that does not certify acceptable error control either. These are process-specific
pilot results, NOT estimated false-positive rates for crypto markets.

Code correctness and inferential validity are separate. All **213 focused tests
passed**, including 28 new statistical arithmetic/contract tests. This does not
erase the persistent-null warning or establish 95% coverage, power or profit.
No block length, generator, threshold or seed was changed to improve the result.

## Operator Settings Decision

`decision.json` preserves ED002-MODEL-SETTINGS-20261027 and the exact answer:
"Adopt draft settings; prepare synthetic statistical validation (Recommended)".
The adopted conventions are USD1,000 per hypothetical alternative, no deposits,
182 days, fees50bps per side/90bps stress, adverse price25bps per side,
USD0.01 per-order cash rounding and a separate USD20/month overhead scenario.
The existing 25-symbol scope, carry-forward and one-hour delay remain adopted.

These are model choices, not account/venue facts, live limits or an income
forecast. The overhead scenario for182days is20*12*182/365=USD119.6712328767;
it is separate from allocation cash and cancels in equal-period arm differences.
It must not be charged twice or multiplied by14 to imply actual spending.
Control mix, status/effective-interval policy, exact market-rule mapping,
inferential acceptance and actual activation dates are not adopted by this
bundle. No registration, collection, market run or trading is authorized.

## Implementation

Added `services/backtest/paired_wealth_screen.py`. Existing Sharpe bootstrap,
accounting, comparison wrapper, frozen signals and prior results remain intact.
The old `paired_block_sharpe` computes a different statistic/noncircular blocks;
it was not silently reused as the proposed net-dollar inference method.

The new function requires all seven named arms on the same182contiguous UTC
day ends and initial capital1000. It rejects missing/misaligned dates, invalid
returns and nonzero returns after an observed total account loss. Caller must
provide cost-inclusive daily simple returns anchored to pre-fill capital.
This implementation does not yet build/authenticate those daily rows from
hourly experiment artifacts or verify their fees/provenance.

Uniform circular calendar blocks are sampled jointly across every arm,
concatenated and truncated to182days. Exactly20,000replicates use PCG64 seed
20261027, in256-replicate batches to bound working arrays. Returns recompound
from1000; three family-minus-incumbent terminal-wealth differences use the
one-based334th sorted value, the proposed inverted-CDF1/60 lower quantile.
Seven days is primary;14/28 are labelled sensitivities, never selected as winners.

The output always retains `coverage_certified=false`,
`statistical_validation=INCOMPLETE`, and `experiment_pass=null`. A positive
numeric bound is not a promotion decision. Overflow/underflow or invalid wealth
makes computation INCOMPLETE without dropping bad resamples. Exact exhausted
wealth can be zero; this does not require a Sharpe standard deviation.

Official arithmetic references opened, not market endpoints:
[NumPy quantile](https://numpy.org/doc/stable/reference/generated/numpy.quantile.html)
and [PCG64](https://numpy.org/doc/stable/reference/random/bit_generators/pcg64.html).
The live stable docs identified2.5; the actual verified local runtime is
Python3.12.10/NumPy2.4.4, recorded in results. Runtime tests check the exact
quantile convention rather than assuming documentation versions are identical.

## Bounded Synthetic Pilot

`validate_pilot.py` and its exclusive-create `ATTEMPT.json` pin32trials each for
iid and AR(1)0.8 generators,1024burn-in observations, data seed20261128, and the
original bootstrap seed. Three families and incumbent have identical marginal
path laws, with shared common shocks plus identically distributed idiosyncratic
innovations. Thus there is no expected family-versus-incumbent wealth advantage.
Cash and two control columns are synthetic diagnostics, not traded portfolios.

Budget: at most67method calls (64null trials plus3fixed known-effect sensitivity
calls),20,000resamples each,120-second alarm during computation, no automatic
retry or overwrite. Imports/receipt writes are outside that compute timer.
Socket/process guards are installed before method imports; native BLAS/OMP
threads are constrained by the command. This is not a general system sandbox.

SHOWN: one attempt, exit0,67calls,5.894880seconds, peak process RSS61,472,768bytes.
Its `status=COMPLETE` means the pilot finished, while statistical validation
remains INCOMPLETE. Wilson ranges describe independent synthetic-trial rates
only;32trials cannot certify nominal coverage or power. No larger calibration
or post-result replacement method was run.

```sh
env -i PATH=/usr/bin:/bin PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ./.venv/bin/python -B docs/research/ed002_stat_validation_20261027/validate_pilot.py
```

The runner refuses another attempt in this folder. Preserve its outputs;
`result.json` SHA256 is
`18e7495fcf147bd82fb3f814d8ec483d6814a75e122cdc87af46dc9925351090`.
Pilot source/decision hashes were rechecked afterward and matched.

## Verification And Remaining Boundary

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_paired_wealth_screen.py tests/test_delayed_research_comparison.py tests/test_delayed_signal_bridge.py tests/test_frozen_signal_bridge.py tests/test_shared_cash_research.py tests/test_next_open_research.py tests/test_harness_contracts_wp4.py
```

VERIFIED_ENV:213passed8.20s,28new+185existing. Initial26new tests passed1.17s.
Fixtures cover paired/serial nulls, fixed effects, compounding and entry costs,
circular wrapping, empirical quantile rank, deterministic seeds, invalid input,
exhaustion and resample-only numerical overflow. No full suite or market inputs.

Separate review must distinguish formula implementation from the pilot's
negative inferential evidence. Before any market screen, require a prospectively
specified method/validation budget and independent evidence that the intended
inference is defensible. Do not silently switch to14/28-day blocks or retune
after market outcomes. No new strategy, old backtest, financial setting,
account/credential, service/schedule, trading, commit or push changed here.

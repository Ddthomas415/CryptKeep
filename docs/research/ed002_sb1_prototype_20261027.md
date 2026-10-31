# SB-1 NumPy-only prototype

2026-10-27 New York. Active role ENGINEER. Risk HIGH (financial inference).
READY_FOR_INDEPENDENT_REVIEW. Statistical validation remains INCOMPLETE.

## Delivered Scope

ED002-SB1-PROTOTYPE-20261027: operator explicitly selected "Adopt plan; build
NumPy-only prototype (Recommended)" after the question offering human adoption
of the exact SB-1 plan. This adopts the design for a prototype with deterministic
synthetic/reference tests only. No claim of independent method review or human
source inspection is inferred. No package installation, randomized development,
audit, market experiment, activation, account or trading action is authorized.

Added `services/backtest/sb1_prototype.py` and32tests. The module is independent
of the unreviewed original wealth calculator; it does not import that calculator,
the financial ledger, a strategy, a study, or the old pilot. Existing accepted
accounting/bridge/comparison code and all original statistical artifacts remain
unchanged. No compatibility API was replaced and the old213-test slice was not
rerun merely because this new, unconnected module was added.

## Implemented Behavior

The corrected stationary-length formula is applied to seven log-return columns,
three family-minus-incumbent log-return differences, and centered squares of
all ten. Exact constants are recorded and removed from selection only. One mean
block length is the ceiling of the maximum finite nonnegative estimate, at least1.
A zero finite estimate receives this explicit floor, not a seven-day fallback.
Undefined nonconstant estimates remain INCOMPLETE. If all20columns are constant,
length1is labelled degenerate, not a confidence certificate. Fewer than10effective
blocks abstains. These max/utility rules are the adopted candidate hypothesis,
not guarantees supplied by the reference package.

The sampler consumes caller-supplied index starts and uniforms. It restarts
when u<=1/mean_length, otherwise advances with circular wrap. All arms use the
same indices. Neither the sampler nor the full prototype constructs an RNG or
generates development/audit paths. Full evaluation requires exactly20000x182
supplied draws, processed in256-replicate batches, and fingerprints the draw
bytes. No saved file or scheduler provides draws automatically.

Daily inputs require seven aligned182-day UTC calendars and the adopted1000USD
model capital. Wealth is recompounded, with first-day costs retained, for three
family-minus-incumbent contrasts and the334th empirical lower order statistic.
Bankruptcy makes log-selector inference INCOMPLETE, not a removed accounting
loss. Invalid/numerically unrepresentable data cannot yield an accepted result
or discard bad draws. Draw inputs and daily records are not mutated.

Outputs always keep `prototype_only=true`, `statistical_validation=INCOMPLETE`,
`coverage_certified=false`, and `experiment_pass=null`. A positive computed bound
is not a trading decision, confidence certificate or demonstrated edge.

## Reference And License Evidence

Read the official tagged arch7.2.0selector/sampler and license. Captured exactly
three public source/license GET responses, with verified TLS, no auth/proxy,
redirect or retry,10seconds per request/35seconds overall. No market endpoint,
dependency install or remote-code execution. Append-only raw files/manifest:
`../review_artifacts/ed002_sb1_reference_20261027/`.

- `base.py.txt`:48eb6443a96877bbeac7051e83121cd6909240b62a5d5d1be1b4c5eb69aea2bc
- `samplers.py.txt`:dc353a7b84ce90ab9900d30277d35f0cd2e671cb66cae0b5a6072f0651d0a50b
- `LICENSE.md.txt`:c6e622bd89db4e13315f4e91605ff96fcbb9012d78ee74e429855870b203eed6

The fixture `tests/fixtures/sb1_arch720_reference.py` contains two verbatim
captured functions with local import/type scaffolding only. Tests first verify
the raw hashes and exact function-source equality, then compile only those two
function definitions via AST into a NumPy/type-alias namespace. They do not
import/execute the arch package or the captured module bodies. The complete
required notice/permission/disclaimer is retained in `docs/licenses/arch-7.2.0.txt`
and attribution accompanies the production prototype and fixture.

This pins the observed tag bytes and selected functions, not an independently
resolved upstream commit or the entire arch API. Parity is on stated fixtures,
not a proof of equivalence for every possible input or statistical coverage.
[Selector source](https://raw.githubusercontent.com/bashtage/arch/v7.2.0/arch/bootstrap/base.py),
[sampler source](https://raw.githubusercontent.com/bashtage/arch/v7.2.0/arch/bootstrap/_samplers_python.py),
[license](https://raw.githubusercontent.com/bashtage/arch/v7.2.0/LICENSE.md).

## Verification

VERIFIED_ENV Python3.12.10/NumPy2.4.4. arch/scipy remain absent.

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_sb1_prototype.py
```

SHOWN: **32passed1.23s**. Initial29cases passed1.05s before three additional
deterministic fixtures. No full suite or randomized development/audit run.

Cases cover five analytic selector series against the reference; four sampler
lengths, threshold equality, restart/wrap and unsigned indices; all20selector
features and max/ceiling; constants/undefined/too-few-block guards; full20000-draw
deterministic constant/null/effect fixtures; reference-index recomposition;
first-day fees, bankruptcy, numerical overflow and invalid data/draw refusal.
Test-body guards refuse NumPy RNG construction/draws and socket/process calls.
They are not an import-time or system-wide safety guarantee.

A deterministic persistent wave returned INCOMPLETE with41-day mean/fewer than
10effective blocks; it was preserved as a guard test, not changed to get a pass.
Some recomposition fixtures stub only selection to isolate arithmetic; those
are explicitly labelled and do not validate the real selector's statistical
properties. Constant supplied draw rows repeated20000times are unit fixtures,
not20000independent observations or a Monte Carlo calibration.

## Handoff Boundary

Exact sources/tests/reference/license and unchanged old pilot are bound in the
adjacent JSON. The existing reviewer's last observed state is usage-limit error;
no new retry or duplicate reviewer is initiated by this prototype. This thread
does not approve its own high-risk code. Separate independent/human code review
must assess reference parity, selector aggregation/abstention, shared indices,
recomposition, numerical behavior and authority before any later validation run.

No randomized development/audit runner was added. The proposed90/600-second
budgets and their execution remain separate authorization boundaries. This
prototype has NOT shown improvement over the original8/32persistent-null result.
Original evidence, registered studies, economic settings,25-symbol scope and
one-hour trading-model delay remain intact. No service, schedule, credential,
account, financial risk/capital, commit or push changed.

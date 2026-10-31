# ED-002 synthetic seven-arm comparison

2026-10-27. Active role ENGINEER. Risk HIGH (financial comparison logic).
State READY_FOR_INDEPENDENT_REVIEW. No market study or protocol activation.

## Purpose And Delivered Change

The separately reviewed delayed bridge is ACCEPTED_WITH_RISK, with 157 tests
independently passing in 4.58s. Its exact 14 reviewed bindings were verified
before reuse. Review SHA256:
`b8f684ef23e24713138f387900480fc3f6e48219d7d662817ce13e35ceade2ef`.
That acceptance explicitly left comparison-level benchmark-entry validation
unimplemented. Operator then approved continuation; this is the next bounded
synthetic-only implementation, not another strategy test or a new simulator.

Added `services/backtest/delayed_research_comparison.py` and its test file.
Reuses the accepted delayed bridge, frozen strategies and shared ledger unchanged.
Three frozen default families, the existing incumbent, cash, BTC hold and a
declared fixed-unit BTC/ETH/cash mix run as seven alternative shared-cash accounts.
The API chooses no capital, fee, adverse price, mix weights, precision or horizon:
these are explicit caller inputs, identical across arms. One call is one cost
case. Alternative capital/profits are never summed into one funded account.

This library supports explicit symbol sets for synthetic fixtures. The test
suite includes all 25 synthetic labels sharing each default-family wallet.
Actual research still requires the mandated 25 exact identities and dated input
contract; no asset coverage or trading status changed here.

## Clocks And Controls

Caller supplies aligned A (evaluation start) and B (end exclusive). First model
execution is E=A+1 hour. The first supplied frame starts A and ends E; it is the
ledger's initial decision frame, not an earlier trading opportunity. All arms
start flat and have an explicit cash-only equity row at E. Model trades at E
then affect the row at E+1 hour. Final marked close is B, with no execution of
pending orders at B. No dates or 182-day horizon are inferred or activated.

Cash and fixed-unit control callbacks use the same ledger, frames, costs and
outcome consistency checks. Controls issue their declared target only once;
there is no periodic rebalancing, retry or post-fill capital rebase. Normal lot
dust and residual cash are retained. A mixed control requires positive declared
weights for both named assets and records whether each actually entered.

## Benchmark Entry And Completeness

For each intended control component, require a positive nonterminal modelled buy
at the common first execution E. Known ineligibility, missing open, lot dust,
insufficient funds/minimum or another refusal cannot masquerade as successful
buy-and-hold. A partial entry in only one mixed-control asset is insufficient.

If this proof fails, preserve the diagnostic ledger but change the arm's
comparison status to INCOMPLETE and set marked NAV, net/phase profit and
unrealized PnL to unknown. `ledger_status` distinguishes a mechanically COMPLETE
cash-only ledger from a failed benchmark. Fees and diagnostic holdings remain
inspectable; there is no fabricated liquidation or negative economic verdict.

Top-level `economic_result_usable` requires every arm COMPLETE and every state
at B. Otherwise the top-level seven-arm net-profit summary is entirely unknown.
Arm results remain scoped diagnostics, not winner selection. A partial chunk
can retain valid ledger states for carry while its period-level status is
INCOMPLETE. No interim statistics, ranking or inference is produced.

## Carry And Input Preservation

Require all seven valid states, accepted entry proofs, matching comparison
recipe and one common resume clock. Keep cash, units, basis, pending targets and
the original entry proofs; never restart controls on a later chunk. Recipe binds
named control assets, mix, universe, A/E/B. Existing ledger/bridge bindings also
bind capital/cost/target identity, historical signals, receipts, rules and used
outcome prices. Changed fees/mix/endpoints, missing states and clock divergence
are refused. A failed initial benchmark cannot be resumed as if it entered.
Full versus split equity and all seven final states match in synthetic tests.

No dependency source, strategy config, original checkpoint/review, archive,
coverage registry, account, credential, service, schedule, risk or capital setting
was modified. Caller inputs are copied by the existing model; no persistence or
network code is introduced. No new metadata mapper or settlement assumption.

## Verification And Review

VERIFIED_ENV command:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_delayed_research_comparison.py tests/test_delayed_signal_bridge.py tests/test_frozen_signal_bridge.py tests/test_shared_cash_research.py tests/test_next_open_research.py tests/test_harness_contracts_wp4.py
```

SHOWN: **180 passed in 6.82s**: 23 new comparison cases plus 157 existing cases.
Initial comparison-only development run: 21 passed in 2.63s. No full suite,
historical strategy run, raw price analysis, statistical calibration or network.
Socket/process guards are test-body restrictions, not universal import proof.

Separate review must assess failed/partial benchmark entry, partial-period
reporting, common clocks/initial cash hour, carry identity and default compatibility.
Exact hashes accompany this checkpoint. This implementing thread does not accept
its own high-risk work. No experimental economic PASS follows from synthetic
plumbing. Cost/capital/rounding/status/horizon/inference choices and market-run
authorization remain separate; no collection, schedule or deployment is implied.

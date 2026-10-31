# ED-002 synthetic signal bridge

2026-10-27. Active role ENGINEER. Risk HIGH (financial logic).
Acceptance: ACCEPTED_WITH_RISK by separate GATE for the bounded synthetic
implementation/correction only; no market experiment or operational authority.

## Adopted Scope

ED002-ALLOCATION-20261027: two replies arrived for the same allocation question.
The earlier reply requested revision; the later reply explicitly selected
"Adopt rule; implement synthetic bridge (Recommended)". The later choice
supersedes the earlier one for this bounded stage. No adoption of the wider
experiment, cost scenarios, horizon, inference method or market-data run follows.

Added `services/backtest/frozen_signal_bridge.py` and synthetic contracts in
`tests/test_frozen_signal_bridge.py`. Existing ledger, strategies, snapshot,
old reports and raw archives are unchanged. No statistics implementation,
activation, collector, account or trading operation is included.

## Interface And Behavior

`FrozenSignalBridge` is a copied, in-memory callback. Caller supplies symbols,
venue/quote, dated `rules`, `observations`, and the exact frozen snapshot bytes
plus one of the three default family keys. Each observation is
`{row: [ts_ms, open, high, low, close, base_volume], known_at_ms: int}`.
Optional `recent_listings` records contain `first_bar_ms` and `known_at_ms`;
optional valuation marks use the accepted ledger schema. No files are loaded,
data fetched or external processes launched by the bridge.

The snapshot SHA256 is pinned to the existing file. Config is copied, evidence
emission disabled and later config mutation refused. The bridge calls the real
existing `compute_signal` with exactly300 contiguous completed/available rows.
Opening/closing prices of the current signal row must agree with the ledger
frame. Known ineligibility is reported separately from missing permission;
documented short recent-listing history stays signal-not-ready, while a hole
or late required observation is INCOMPLETE. No ticker/product identity is
inferred. Current source identity is a caller/review binding, not automatically
attested by the pinned configuration hash.

`event_targets(context, actions, marks)` implements the adopted rule using exact
fractions: held SELL targets0, flat BUY receives up to1/25 of portfolio NAV,
simultaneous entries share residual cash/selling weight, and retained holdings
use their prior-close weights. BUY while held and SELL while flat are ignored.
No actionable event, no affordable entry, or an exhausted cash/units account
produces no new decision. All-HOLD is not periodic rebalancing. Missed entries
and exits are not latched; every decision uses actual holdings and a fresh raw
signal. Required missing NAV or invalid/nonfinite signals are not converted to
HOLD. Arithmetic failures become explicit INCOMPLETE; assertion tripwires are
not swallowed.

For the incumbent, supply an explicit two-symbol `incumbent` pair instead of a
family. It uses61 complete UTC days, the frozen28-day/30-day population-volatility
formula, Sunday close only, and the same next-open ledger. Undefined required
volatility or missing hourly inputs is INCOMPLETE. A fixture compares the result
with only `target()` extracted from the frozen source AST on synthetic prices;
the executable historical study and its data-loading/grid body are never run.

`simulate_bridge(frames, bridge, target_contract_id=..., **ledger_profile)` calls
the unchanged shared-cash ledger. Hourly clock, universe, venue, rules and
valuation metadata must agree. Resume binds the bridge policy/family and all
previously available observations, listing evidence, rules and marks. Changed
past inputs or family refuse carry; newly available future rules do not rewrite
the past. Exact state types and existing ledger resume reconciliation remain.

If the initial decision cannot be established, return INCOMPLETE with stateNone,
not a fabricated initialized or traded account. Later failures retain the
ledger's incomplete wallet/state. Corrupt resumed-state errors are not hidden
as initial bootstrap failures. This adapter does not persist or serialize state.

The returned state retains per-close decisions/readiness/targets. `bridge_trades`
adds raw-action and incidental-rebalance labels without altering ledger fills;
`incidental_turnover_quote` reports their cumulative raw notional. Non-selling
held quantities can resize during another signal's batch because close weights
and joint costs are used at the next open; this is deliberately not exact old
trade-path parity. Incumbent scheduled rebalances and terminal liquidation are
not mislabeled as incidental default-strategy resizing.

## Verification

SHOWN, VERIFIED_ENV, isolated local Python, no repository conftest/plugins:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_frozen_signal_bridge.py tests/test_shared_cash_research.py tests/test_next_open_research.py tests/test_harness_contracts_wp4.py
```

Final result: **126 passed in3.50s** (33 new bridge cases plus93 existing
accounting/compatibility cases). Initial21bridge cases passed0.47s; an expanded
120-case slice passed3.53s before the final failure-path additions. No full-suite
or end-to-end runtime claim. New test-body socket/DNS/subprocess guards do not
cover module imports; a swallowed-assertion negative case proves signal-error
handling does not hide those assertion tripwires.

Fixtures cover simultaneous/zero-budget targets, ignored actions, exhaustion,
all-HOLD behavior, all three real frozen families, future-price/volume prefix
invariance, copied inputs/configuration, missing/late data and known listings,
ineligibility versus unknown metadata, open-price mismatch, minimum refusal with
no retry, incidental gap turnover,25synthetic instruments sharing one wallet,
full-versus-split state equality, historical/family drift rejection, future rule
addition, incumbent source parity/UTC timing and undefined volatility.

Accepted ledger SHA256 remains
`3625c91f7d9af17daa685f6c118d175387d5d132dc6209aafb2d50c5271333cc`;
snapshot remains
`709149a916da94c4edd99065f2f70b456ef7e8fc95b130e5420cc17aab998cfc`.
The proof manifest and isolated new-file diff are in
`../review_artifacts/ed002_signal_bridge_20261027/`.

## Evidence Limits And Next Gate

The October8 report `multisymbol_final_results_20261008.md` remains prior
counter-evidence: four of15 independently funded strategy arms had positive
Jan-September modelled results at25+5bps, one at60+5bps. Those were five assets,
OKX/USDT, fixed100-notional sizing and different costs; none establishes trading
income. This bridge is not a rerun, refutation or rescue of those outcomes.

Two modelling assumptions remain: one venue/common quote/no yield or FX; full
fills with declared costs and dated caller-supplied eligibility. All fixtures
are synthetic, including SYN-* labels, not proof that25 real assets are eligible.
No market dataset or API was used, no experiment/inference scored, no dependency,
service, schedule, account, credential, risk, capital, commit or push changed.

Next gate is independent review of these new source/tests and the unchanged
ledger interface. A reviewer acceptance would apply to synthetic implementation
only. Statistical validation, market-data feasibility, prospective protocol
adoption and activation remain separate unperformed boundaries.

### Independent Review Availability

Requested one bounded review from the existing separate GATE. Its status remained
errored with a usage-limit result; no new bridge review was returned. No duplicate
agent/job or quota workaround was created. This is not a new financial rejection,
nor does prior ledger/design acceptance cover this code. The bridge source/tests
remain frozen at implementation proof, READY_FOR_INDEPENDENT_REVIEW. Next action
is independent review of this exact handoff when a reviewer is available, not
another implementation or market-data run.

### Independent Rejection And Bounded Correction

The reviewer subsequently resumed and wrote
`ed002_signal_bridge_review_20261027.json`, REJECTED for ED002-BRIDGE-01. The
126-case slice passed independently, but a separate synthetic probe showed that
the incumbent skipped frame/panel validation outside Sunday rebalances. A
contradictory Monday execution open could therefore produce a COMPLETE path
with fictitious profit. The earlier availability note is historical, not the
current review disposition. Original code/tests/checkpoint/manifest/diff and
the rejection are preserved in
`../review_artifacts/ed002_signal_bridge_20261027/rejected_v1.tar`.

Added three cases for conflicting Monday open, conflicting close and missing
current-panel hour after a real synthetic Sunday target; all three failed on
the original bridge (33 deselected). The correction checks every present
incumbent frame open/close against its available current hourly observation
before the weekly trigger. Target cadence/formula and the accepted ledger
remain unchanged. Absent raw prices are not invented from the panel.

Validation occurs at each completed bar, not by reading its future close to
cancel an earlier opening fill. A failed bar can retain diagnostic modelled
entries, but the account is invalid, NAV/profit is unknown and it cannot be
carried as a valid path. These entries are not accepted executions or profit.

Corrected focused command (same four files above): **129 passed in3.66s**,
36bridge cases plus93 existing cases. Ledger SHA256 remains3625c91f...1333cc.
No full suite, market data, operations or frozen-strategy changes. Current
source/tests are frozen for independent correction review:
READY_FOR_INDEPENDENT_REVIEW, not accepted by the implementing thread.

### Independent Correction Acceptance

Separate GATE re-review ACCEPTED_WITH_RISK the exact correction and closed
ED002-BRIDGE-01 with no remaining blockers in its scope. It independently ran
the129-case slice once:129passed in3.57s. Record:
`ed002_signal_bridge_rereview_20261027.json`, SHA256
`9d7168f202877c15a2ab428ac23ac31df61cf9dd4fae4246f9c10ee4ce4cf9a4`.

All re-review input bindings matched before this documentation-only closeout;
reviewed code/tests, original rejection and archive remain unchanged. Checkpoint
and manifest digests in that review refer to their historical pre-closeout bytes.
Invalid-bar traces remain diagnostic only; consumers must honor INCOMPLETE,
unknown NAV/profit and invalid state rather than extract valid returns from them.

The adopted synthetic bridge objective is complete. Market-data feasibility,
inference validation, cost/horizon adoption and any future freeze/activation
remain unperformed and separately authorized. No observed profit follows.

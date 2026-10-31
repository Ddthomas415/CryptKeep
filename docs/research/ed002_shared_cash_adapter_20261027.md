# ED-002 synthetic shared-cash adapter

2026-10-27. Active role ENGINEER. Risk HIGH (financial logic).
Acceptance: ACCEPTED_WITH_RISK by separate GATE for the bounded synthetic
implementation and correction; no experiment or operational acceptance.

## Decision And Scope

Decision ED002-ADOPT-20261027: the operator selected "Adopt contract; implement
synthetic adapter" in this chat. This adopts the independently reviewed modelling
recommendations in `ed002_portfolio_contract_candidate_20261018.md`, not a new
strategy, capital allocation, market-data experiment or trading authorization.
The historical candidate document and its recommendation-only review are preserved.

Implemented `services/backtest/shared_cash_research.py`; synthetic contracts in
`tests/test_shared_cash_research.py`. Existing single-arm APIs, frozen studies,
research results and symbol coverage are unchanged. A 25-instrument synthetic
fixture is an accounting test, not historical coverage of the 25-symbol mandate.

## Interface

`simulate_shared_next_open(frames, target_fn, **profile)` requires explicit
`symbols`, `venue`, `quote`, `interval_ms`, `initial_cash`, `fee_bps`,
`slippage_bps`, `rules`, and `target_contract_id`. Optional `valuation_marks`,
`state` and `terminal_liquidation` are separate inputs. No data is fetched.

Each frame is `{ts_ms, open: {symbol: price}, close: {symbol: price}}` on an
explicit contiguous grid. Timestamp is bar open; close becomes available one
interval later. Missing prices are absent keys, not zero or carried prices.
The initial frame is warm-up; targets from it execute at the next frame's open.
There is no built-in indicator, strategy selection or position-sizing rule.

The callback receives copies of completed `history`, `decision_index`, `cash`,
`units`, `basis`, `marked_nav`, and `close_ms`. History is not silently truncated.
Return explicit nonnegative weights summing to at most one; omitted symbols
target zero. Return `None` for no new decision. A callback must itself remain
causal and side-effect-free: this is an in-process interface, not a sandbox.
`target_contract_id` is caller-declared identity, not an automatic source-hash
check or proof that a callable's external state is frozen.

Each symbol's dated rule list requires `known_at_ms`, `valid_from_ms`, exclusive
`valid_until_ms`, `venue`, `quote`, boolean `eligible`, positive `lot_step` and
`quote_step`, plus nonnegative `minimum_qty` and `minimum_notional_gross`.
Latest unambiguous rule must be known by decision close and valid at execution.
`minimum_notional_gross` explicitly refers to slipped execution gross before
fees. This is a model definition, not verified venue-minimum semantics.

Valuation-only records are `{ts_ms, known_at_ms, price}` keyed by symbol. Only a
unique contemporaneous observation known by that timestamp can fill a missing
mark. These records never supply executable prices. A missing execution open
excludes that symbol for that decision without redistributing its target; a
missing required held valuation or permission makes the case INCOMPLETE.

## Ledger And Continuity

The adapter reuses `corrected_research_math.rebalance` to seed its joint post-cost
solution, then refines the same piecewise equation with exact rational arithmetic
before lot flooring. Decimal input parsing and `Fraction` ledger values avoid
tolerance-funded orders. Only actual rounded debits and credits affect cash.
Sells settle before buys; sell fees are withheld before proceeds can fund buys.
All buy orders share proportional affordability resizing, not symbol priority.
Batch mutations are committed together only after the trade-cost NAV identity
reconciles. Retained dust keeps proportional basis. Realized, unrealized, fee,
slippage and quote-rounding attribution remain distinct and are not charged twice.

Return `state` unchanged to a contiguous next segment; cash, units, basis,
pending decisions, cost buckets and history carry forward. Resume reconciles
wallet totals with the fill ledger and validates the profile, NAV and pending
boundary clock. Phase start NAV is the preceding completed close; a boundary
opening gap belongs to the following segment. An INCOMPLETE account cannot be
resumed as a valid performance path; correction requires a separately labeled
replay. A legitimate open fill remains recorded if that later close is missing.

Numeric outputs and state use exact `Fraction` values. Callers must serialize
them losslessly (for example numerator/denominator pairs) and restore their
types; ordinary JSON encoding or rounded float conversion is not an exact
checkpoint format. No checkpoint persistence format is introduced here.

Primary endpoint is marked NAV, not realized cash. Optional terminal liquidation
is a separate cloned last-close simulation with sell costs, precision and dust;
it never changes the primary state or pending next-open decision. Residual
holdings remain explicitly marked rather than reported as liquidated cash.
Only the completed frame's actual close-price map may supply this synthetic
execution price; valuation-only marks remain marking inputs. Terminal exclusions
are reported separately, including missing executable closes.

`simulate_shared_comparison` runs cash, hold-BTC, caller-declared fixed-unit
BTC/ETH/cash mix and caller candidate through the same engine and costs. The two
benchmark symbol identities and mix weights must be supplied. The mix is bought
once, not periodically rebalanced. Exposure equivalence is not inferred or fitted.
All four states must be supplied together for a resumed comparison.
Each carries the normalized mix and both benchmark identities in
`comparison_contract`; a changed or missing declaration refuses the whole
resumed comparison before any arm is simulated.

## Verification And Limits

SHOWN, VERIFIED_ENV: the following focused command passed **93 tests in 2.99s**
on the corrected candidate (initial candidate: 90 passed in 3.06s):

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_shared_cash_research.py tests/test_next_open_research.py tests/test_harness_contracts_wp4.py
```

This intentionally bypasses repository conftest/plugins. It is targeted proof,
not the full repository suite or integration/runtime proof. New adapter tests
install socket/DNS/subprocess tripwires during test bodies, not during imports.
An earlier combined run had 88 passing and one failing error-message assertion;
the cash-tamper fixture now also changes its NAV anchor so it exercises ledger
reconciliation instead of being rejected earlier by the stricter NAV check.
The new 302-frame fixture prevents an arbitrary lookback truncation.

Preserved current source SHA256 values:

- next_open_research.py: `4f5bb1a98be726915bca155b8ea483d5036982ed786665e504c1e444ce2d1a7f`
- corrected_research_math.py: `d07ae7171e2293cbe60d15ae9bc0973d3ef8bd31b9c7b99105f928c029e29047`
- frozen ms_trend.py: `550dc2ea708c2a37a56f58f41b81b3a25d16f6077a8fa52b0a4bef2b287468cc`
- run_multisymbol_baseline.py: `d6ddce6d69a755db67c542e6e29f3e68f06612bd2fc95373490f671e3ead2e78`
- historical contract: `b16b1108d99a9fcd9a6b8d83650cb093fb026cd9fe40cfa7eaf4f7d9d9a16be8`

These match the inspected reuse boundaries; the frozen E10 script was not imported.
No market-data experiment, full suite, native service operation, scheduler,
account, credential, capital, risk change, commit or push was performed.

Assumptions (two): one venue/common quote with no cash yield/FX/financing; caller
supplies a causal unchanged target mapping and correctly interpreted dated data.
If false, the model is not suitable without a separately scoped extension.
UNVERIFIED: historical permissions/precision, actual fills, liquidity, partial
fills, queue/capacity/latency, strategy economics and production integration.
`COMPLETE` is an internal model-result label, not project acceptance. Every fill
is `MODELLED_FULL_FILL`; synthetic tests establish no profitability or readiness.

Next proof is a bounded independent financial-logic review of this adapter and
its synthetic tests. Existing market studies are not reopened or rerun.
This was the implementation handoff boundary; the completed review is below.

## First Independent Review And Bounded Correction

The first independent review was REJECTED despite its own 90 passing tests.
`ed002_shared_cash_adapter_review_20261027.json` preserves both reproduced
findings: terminal liquidation promoted valuation-only marks, and resumed
comparisons did not bind benchmark identities/mix. The reviewed source, tests,
checkpoint, first review and proof manifest are preserved unchanged in
`../review_artifacts/ed002_shared_cash_20261027/rejected_v1.tar`.

Three new regression cases failed against that source before correction. The
correction uses only the final frame's real close map for synthetic terminal
execution and binds normalized comparison declarations to every carried arm.
Primary valuation/carry state remains untouched; marked residual holdings and
terminal exclusion reasons remain visible. Re-review is required, not inferred.

Separately, the unchanged legacy archive/source-slice regression command passed
9 cases in 0.39s using temporary synthetic SQLite fixtures:
`tests/test_multisymbol_archive_runner.py tests/test_research_source_slice.py`
under the same isolated pytest flags. Total targeted cases across the two current
parent slices: 102. No full-suite or market-data claim follows.

## Independent Re-review Closeout

Separate GATE ACCEPTED_WITH_RISK the bounded correction, closing both findings
with no remaining blocker in its scope. It independently ran the same focused
slice once: 93 passed in 2.92s. Review:
`ed002_shared_cash_adapter_rereview_20261027.json`, SHA256
`e923a0d118f053cafdd7b31e38132822f6c041d4cd6953dbd7ce98028807fc81`.
The original REJECTED review remains unchanged. Before this documentation-only
closeout the parent verified all five re-review bindings and five preserved
source/contract bindings. The checkpoint hash in the review is historical
pre-closeout; reviewed source and tests remain byte-identical.

Implementation proof for the adopted synthetic scope is complete. Consumers
must preserve terminal residual-holding labels/exclusions, exact state types
and comparison recipe metadata; old comparison states without the declaration
fail closed. The next research boundary is a separately frozen and authorized
comparison contract/data/eligibility/cost package, not an automatic rerun.
No production integration, historical tradability or profit is established.

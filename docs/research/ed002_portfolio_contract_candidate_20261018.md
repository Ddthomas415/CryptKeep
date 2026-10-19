# ED-002 shared-cash contract candidate

2026-10-18 New York. Active role DIRECTOR. Risk HIGH (financial accounting).
Acceptance: READY_FOR_INDEPENDENT_REVIEW. All choices below are RECOMMENDED
proposals, not operator-approved decisions or a frozen experiment.
Scope: one bounded adapter reusing next_open timing and rebalance accounting;
no new framework, strategy, preregistration, scoring or financial-code change.
Material assumption (one): one venue and common quote currency, cash earning zero;
no FX, financing, transfers, staking or corporate-action conversion model.

## Evidence and reuse boundary

SHOWN by source inspection: next_open executes prior-bar actions at the next open;
rebalance solves joint post-cost long-only targets. E10 has shared holdings/cash
but stale marking and import-time experiments; inspect only, never import it.
The baseline replays prefixes independently per symbol/arm, not one shared pot.
Evidence: `services/backtest/next_open_research.py:45,86,134`,
`scripts/research/corrected_research_math.py:102`,
`docs/research/multisymbol_trend_20261015/ms_trend.py:32,48,87,109`,
`scripts/research/run_multisymbol_baseline.py:88,100,111`, and
`docs/research/portfolio_reuse_assessment_20261018.md`.
Preserve those APIs, frozen V3/E10 artifacts and verdicts; do not modify them.

## Recommended execution and accounting

1. **Inputs/capital:** require explicit positive caller-declared initial quote
   capital C, costs, dated precision/minima, evaluation grid and target mapping.
   C is a simulation parameter, never inferred user capital or risk permission;
   existing 1,000-unit fixtures are not approved funding. Caller supplies the
   unchanged signal-to-target rule; reject absent/ambiguous mappings, not invent one.
2. **Continuity:** one cash/quantity/basis/fee ledger per portfolio and cost case.
   Carry all state, dust and pending next-open decisions across split boundaries;
   no resets, deposits, duplicated fills or split liquidation. Exact prefix replay
   may reconstruct that same account. Phase profit = end NAV minus prior boundary
   NAV; unknown boundary NAV makes phase profit INCOMPLETE. Reused history is not
   a new holdout. No summing independent-arm returns as portfolio returns.
   At boundary B, anchor both phases to the completed preceding bar's close NAV,
   before any execution at B. Fills with execution timestamp <B belong left;
   fills at/after B and the opening-price change at B belong right. Preserve the
   identical pre-fill holdings/basis/cash; do not reset at the opening mark.
3. **Causality/allocation:** completed bar t determines all targets together;
   execute at t+1 open only, never using t+1 close. Require finite nonnegative
   portfolio weights summing <=1; omitted symbols target zero, not implicit hold.
   Freeze non-executable holdings, preserving quantities. Allocation NAV N is
   pre-trade NAV at the execution open, using marks available then for every
   holding including frozen ones, never that bar's later close. With known N,
   free subaccount E = cash + current-open value of executable holdings; desired
   executable notionals d_i = w_i*N. Scale all d_i by min(1,E/sum(d_i)) (1 if zero),
   then pass scaled d_i/E to rebalance jointly, including executable zero targets.
   If E=0, no purchases. No symbol-order priority or redistribution of exclusions.
   Each decision has one exact t+1-open execution timestamp. If that open or
   required NAV/eligibility is missing, expire it with a reason; never retry at
   a later price. Only not-yet-due decisions cross splits as pending. Missing
   held marks/required evidence makes the case INCOMPLETE, not a resumed valid
   return path; repaired-data replay requires a separately labeled correction.
4. **Settlement/costs:** derive signed deltas from the joint solution; ledger all
   sells before buys in that timestamp. Sell credit = q*open*(1-slip)*(1-fee);
   buy debit = q*open*(1+slip)*(1+fee). Net modelled sell proceeds are available
   within that batch only after the sell credit; never gross proceeds or future
   sales. This is a model convention, not evidence of venue settlement access.
5. **Precision/affordability:** floor absolute order quantities to declared lot
   steps, cap sells at holdings, skip below-minimum orders with reason and retain
   dust. Round quote credits down and debits up to declared quote precision.
   After rounded sells, if aggregate buy debits exceed cash, proportionally shrink
   all buys, floor again and recheck minima/debits; leave residual cash unallocated.
   Reconcile actual rounded deltas/fees, not helper cash, as authoritative ledger.
   No negative cash/holdings, borrowing, leverage or tolerance-funded purchases;
   failure to reconcile aborts batch atomically as INCOMPLETE. Missing precision
   inputs are INCOMPLETE, not silently continuous quantities or venue compliance.
   Record rounding loss separately: buy ceil(debit)-debit and sell
   credit-floor(credit), both nonnegative. Add actual rounded buy debit to
   weighted-average quote basis. On sale release basis in proportion to sold
   pre-sale quantity; realized PnL = rounded net credit minus released basis.
   Retain proportional basis for dust. Fees/slippage/rounding are attribution
   buckets already included in ledger cash/basis, not deductions applied twice.
   At identical raw marks the trade-only NAV change must equal minus the three
   cost buckets; even zero-fee trading can lose value through quote rounding.
6. **Fill scope:** label every accepted rounded order MODELLED_FULL_FILL; resizing
   is allocation, not an observed partial fill. No queue, capacity, latency,
   reservation, cancellation or partial-fill claim; no live-execution inference.
7. **Missingness/eligibility:** require dated venue/product/status permissions
   known by decision time and applicable at execution, plus valid current open.
   The 25-symbol mandate is scope, not 25 historically tradable assets; no automatic
   successor substitution. Known ineligibility excludes orders with reasons;
   missing eligibility evidence makes the affected portfolio case INCOMPLETE.
   Keep execution prices separate from timestamped valuation marks. Any held asset
   lacking a valid contemporaneous valuation makes NAV unknown and the interval
   INCOMPLETE; retain holdings/cash, suspend NAV-based rebalance and derived metrics.
   Last-known marks may be diagnostic only, never executable or reported valid NAV.
   Do not fabricate delisting proceeds, zero losses or interpolate missing returns.
8. **Terminal/controls:** primary endpoint is same-time close-marked NAV, cash,
   quantities and unrealized value, not realized cash. Separately report optional
   MODELLED terminal liquidation using last close with sell costs/rounding, explicitly
   synthetic rather than a next-open trade; retain unsellable dust and unknown NAV.
   Never mix marked and liquidated endpoints. Controls: hold BTC, a caller-declared
   initial BTC/ETH/cash buy-and-hold mix (fixed units after initial purchase, not
   periodic constant-weight rebalancing), cash, and the existing candidate.
   Require identical C, dates, available information, costs, eligibility, precision,
   carry and terminal basis. Charge costs for actual modeled control entries/exits;
   do not deduct hypothetical terminal exit costs from the primary marked path.
   Those costs belong only to the separate liquidation endpoint. Declare mix/exposure
   before outcomes, label any exposure mismatch, never fit it to realized returns.

## Existing tests to reuse; required adapter extensions (not new tests here)

| Existing file and test | Contract case / extension still required |
| --- | --- |
| `tests/test_next_open_research.py`: `test_next_open_and_two_leg_fees`, `test_no_future_signal_input_or_mutation`, `test_cash_and_fixed_size_refusal` | Timing, causality, fees; extend to simultaneous constrained buys, permutation invariance and rounding/minima. |
| `tests/test_harness_contracts_wp4.py`: `test_C_hand_calculated_full_allocation`, `test_C_hand_calculated_sell_then_buy_ledger`, `test_C_cash_never_negative_and_every_trade_affordable`, `test_B1_higher_fees_lower_nav_with_fills_fixed` | Joint sizing, net proceeds, affordability, fixed-fill fee effects; extend rounded reconciliation/dust and zero leverage. |
| `tests/test_multisymbol_archive_runner.py`: `test_continuous_cash_and_position_across_splits`, `test_incomplete_symbol_remains_reported`, `test_missing_or_changed_prefix_blocks_simulation` | Existing per-arm continuity/missingness; extend shared state, pending boundary fills, unknown held marks and dated eligibility. |
| `tests/test_research_source_slice.py`: `test_two_market_frozen_archive_and_carry_forward`; next_open `test_flat_round_trip_costs_and_terminal_exit` | Preserve independent-arm regression; add distinct shared-account fixture and marked/liquidated cost-comparable controls. |

SHOWN: named source/tests inspected; file diff/line count checked. Tests NOT RUN;
no E10/backtest execution or imports, network, dependencies or service operations.
UNVERIFIED: adapter behavior, historical eligibility/precision and venue execution.
Review correction: initial proposal omitted explicit valuation/boundary clock,
missed-decision expiry, control turnover/terminal costs and rounding/basis buckets.
Initial reviewed draft preserved in the installation-candidate artifact directory.
These recommendations close definitions, not prove an implemented ledger.
Next proof: independent contract review/operator choices before any implementation
or experiment freeze; then extend mapped fixtures. Parent owns work log, manifest
and collector; this sidecar changes only this document. READY_FOR_INDEPENDENT_REVIEW.

Independent AUDITOR re-review ACCEPTED the four revised definitions as
recommendations, no remaining blocker within that bounded review. No tests,
imports or execution by reviewer. This does not approve operator choices,
financial-code implementation, a frozen experiment or any financial result.

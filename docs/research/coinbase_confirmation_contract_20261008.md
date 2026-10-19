# Coinbase confirmation contract draft

DIRECTOR, HIGH financial research design. READY_FOR_INDEPENDENT_REVIEW.
Machine-readable draft: research/coinbase_confirmation_v1/plan.json.
No activation, data collection, scoring, collector, order or campaign change.

## Purpose and boundaries

Test all15 existing frozen strategy/coin arms on NEW Coinbase evidence without
selecting only prior winners. Same hourly USDT basket,1,000quote cash per
independent arm,100quote entries,completed-bar/next-open signal-only exits.
Prior OKX configurations are reused by preserved snapshot hash, not its data
or profits. No parameter search. These are newly started simulated accounts;
cash/positions carry within this study and are not imported from OKX or live
accounts. The prior carry-forward choice across phases remains unchanged.

Two bounded design assumptions: same-USDT basket preserves quote comparability;
180days is a practical observation window, not a power guarantee. Public catalog
coverage is shown; account tradability and complete hourly grids are unverified.

## Dates and stopping rule

Draft start October10,2026UTC,end April8,2027UTC exclusive:180days,4,320hours.
Warmup300hours from September27,2026 12:00UTC,4,620totalbars per market.
January8 is a90day descriptive checkpoint, not an early selection/stop/parameter
change. No checkpoint liquidation. Close remaining positions only at endpoint,
including final modeled fees/slippage. If preregistration is not complete before
start, do not backdate or inspect the nominal future window and then select new
dates; register a new future schedule first. No automatic scheduler is created.

Thirty naturally closed cycles must occur INSIDE confirmation. Prior trades
and forced terminal closures do not satisfy the floor. Too few cycles or
insufficient effective power means INCONCLUSIVE, not a relaxed threshold or
automatic extension. Other accepted research need not wait for this endpoint.

## Costs and uncertainty

Current account tier is observed:50bps taker,25bps maker per side. Primary
simulation uses taker50bps and modeled5bps slippage;10/20bps slippage stresses
must all be reported. Maker execution is not authorized by the lower fee.
The receipt hash is preserved. Historical/product-specific all-in costs remain
unverified. New fee observations are dated separately; no retrospective fee
rewrite. Executable-cost qualification needs exact product cost validation and
no omitted higher costs; current tier alone cannot prove that condition.

All15 primary arms must be reported. Predeclared paired circular additive-day
diagnostics use7/14/28day blocks,20,000replicates,seed20261010. Bonferroni tail
0.05/(2*45) covers15primaryarms times3blocklengths, not every possible research
claim. Secondary benchmark gaps/stress runs cannot authorize selection.
Stationarity remains unverified; this adjustment does not make resampled
increments a feasible reexecuted strategy or guarantee interval calibration.

Endpoint positive net profit,30natural cycles and positive lower bands at all
blocks are only a review screen. No automatic promotion, live capital allocation
or validated-edge conclusion. Infrastructure is approximatelyUSD20monthly
shared, not deducted repeatedly from independent arms. No portfolio aggregation.

## Required implementation and proof

Existing run_multisymbol_baseline.py is pinned to the old three-phase contract;
it must NOT be pointed at this draft as if compatible. Next engineering scope:
reviewed explicit contract support, read-only coverage checks, source/snapshot
hash verification, exact venue/product boundaries and frozen prefixes. Prove
new account start,continuous checkpoint account,terminal costs,no-lookahead,
natural-vs-terminal counts and no edits to old contracts. Public warmup coverage
preflight precedes activation; absence/gaps reported without substitution.

This draft is not yet a registered operating experiment. Independent review is
required; no operator approval for execution, new background jobs or campaign
mutation is inferred from the venue choice or research continuation.

## Warmup timing correction, pending implementation review

The final warmup candle closes at the study start; full warmup proof is not
available before that instant. Bind the preregistration before start, then
verify completed warmup before any evaluation scoring. No historical account
or evaluation outcome is imported. This does not activate a campaign or allow
scoring early. The draft plan now names registration_deadline and records
activation_timing separately; financial assumptions and dates are unchanged.

## Independent disposition

Separate GATE: ACCEPTED_WITH_RISK for design only. Independently verified
dates/bar counts, snapshot/receipt hashes and11selected-source hashes. No
activation, collection or scoring. Plan status remainsDRAFT_NOT_ACTIVATED.

Thirty cycles/180days are screening choices, not adequate-power assertions;
some arms may remain inconclusive. Bonferroni allocation is arithmetically
correct but depends on valid underlying intervals, which the adjustment does
not establish. With20,000replicates, each adjusted tail contains about11draws;
near-zero lower bounds are Monte-Carlo-sensitive and cannot be overstated.
Implementation must preserve these limits and all required output evidence.

Next scoped engineering step: explicit compatible contract/runner support,
independent verification before exact-product warmup preflight and activation.
If preregistration misses the future start, register new future dates before
any evaluation-window outcomes are accessed; never silently backdate.

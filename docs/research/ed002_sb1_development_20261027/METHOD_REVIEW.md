# SB-1 development: method disposition

2026-10-27. Active role AUDITOR. This is the implementing thread's saved-output
review, NOT an independent numerical/code review. Statistical readiness INCOMPLETE.

## Finding

SHOWN: all 96 saved selector/guard decisions match the frozen rule. Every one of
the 25 abstentions is the prescribed fewer-than-ten-effective-block decision.
There is no demonstrated defect in that boundary to repair. This is not proof
that the entire implementation is defect-free or statistically valid.

| Null case | Selected mean length: min / median / max | Computed / 16 |
| --- | --- | ---: |
| iid | 2 / 3 / 15 | 16 |
| AR0.5 | 6 / 8 / 13 | 16 |
| AR0.8 | 11 / 14.5 / 41 | 12 |
| AR0.95 | 19 / 20 / 21 | 0 |
| AR-0.5 | 7 / 12.5 / 41 | 13 |
| Volatility | 3 / 11 / 20 | 14 |

In the strongest-persistence case, 182/19 to 182/21 gives approximately 9.58 to 8.67
effective blocks. All 16 therefore correctly trigger the existing guard. Lowering
that threshold, dropping this case or increasing the adopted horizon now would
be a new model/protocol decision, not an implementation fix. This review changes
none of those choices.

Source inspection of the generator shows the four tested arms use the same
formula and identically distributed idiosyncratic factors under a common factor;
the constructed no-expected-advantage interpretation is consistent with that
design. This is not evidence that actual portfolio returns obey these laws.
Positive bounds on a few null paths do not alone prove excessive error in this
16-trial development sample. Their uncertainty and the abstentions prevent a
qualification claim. No power assessment or 512-path audit exists.

## Recommendation And Scope Choice

Do not spend the proposed larger audit budget automatically. Do not retune the
guard or parameters using these results. Preserve SB-1 as a documented,
unqualified candidate awaiting appropriate method review.

Recommended next direction: prepare the existing 25-symbol comparison's
descriptive-economic branch, while retaining statistical qualification as a
separate unresolved requirement for any promotion. That branch would report
modelled net dollars/costs/drawdown/coverage, not confidence, an edge certificate
or trading readiness. Use a separately specified future period, not another
rerun of the rejected strategies on reused history. This is a proposal only.

Impact: it would change the original design's ordering, which required inference
validation before a comparison freeze. It would NOT remove the inferential
workstream, change frozen strategies/old criteria, or grant trading permission.
Preserve the original confirmatory design and results; make any descriptive
branch a new explicitly labelled contract. Do not silently make that change.

Alternative: retain strict inference-first ordering and obtain a newly scoped
method/horizon review before any prospective comparison preparation. No method,
longer horizon, income outcome or review availability is promised by that route.
The operator must choose before the ordering changes. Neither choice authorizes
market-data collection/evaluation, schedules, accounts, services or trading.

## Verification

VERIFIED_ENV: parsed existing journal/source only, 96 unique decisions reconciled,
all 10 development evidence hashes matched. `method_review.json` records exact
counts/arithmetic and 6 input hashes. No estimator, simulator, RNG, test suite,
development run or market endpoint was invoked. No frozen artifacts changed.

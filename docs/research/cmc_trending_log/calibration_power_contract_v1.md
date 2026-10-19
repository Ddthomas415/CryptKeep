# Calibration and power contract: accepted design, not executed

Objective: decide whether a statistical method can support a directional net
excess-return claim under declared dependence and coverage assumptions. The
accepted pilot showed the current intervals are not certified for that purpose.
No change to frozen strategy, cohort, horizon, fee or market-outcome rules.

## Review before execution

Separate review must accept the simulation design and decision criteria before
the confirmation simulations run. This proposal is not a new production gate.
No observed CMC outcome may influence method or threshold selection.

Development simulations may compare at most three explicitly documented methods.
Choose exactly one method, with fixed parameters, before confirmation. Preserve
all rejected methods and count every development trial. If confirmation fails,
record failure; revised methods require a new contract and new seeds. Do not
choose the best confirmation result or repeatedly extend a failing sample.

## Proposed simulation grid

- Entry-day sample lengths:90,180,365. Calendar age is not sample sufficiency.
- Nulls: iid, literal overlapping7-day returns, stationary persistent returns,
  shared daily coin shocks, heavy tails, volatility shifts and sparse event days.
- Daily event counts: constant and unequal, including a single high-count day.
- Missingness: none, random20%, and loss-dependent missingness. A method may
  refuse inference; loss-dependent missingness must not silently pass on survivors.
- Alternatives: event-weighted net excess means of0.25%,0.5%,1% over7days.
  These are analysis targets, not asserted achievable trading returns.
- Development seeds:1000000–1999999. Confirmation seeds:3000000–3999999.
  The disjoint seeds prevent simulation reuse, not independence of real markets.
- Confirmation:1000 independently generated histories per declared cell;
  at least2000 resamples if the selected method uses a bootstrap.

## Proposed acceptance criteria

The selected method must report positive net excess only if its one-sided lower
confidence bound exceeds zero. Target false-positive rate:5% per null cell.
Report a95% Wilson Monte Carlo interval; its upper bound must be at most7.5% in
every supported null cell. This tolerance measures simulation uncertainty and
does not redefine the desired5% error rate. No averaging away failed cells.

Power must be at least80% at the proposed0.5% excess-return target, with its
95% Wilson lower bound at least75%, in every scenario claimed as supported.
Report all smaller/larger target outcomes. Refusal rates and reasons are mandatory;
abstentions do not count as successful power or erase failures.

Select the shortest tested length meeting both conditions; if none does, conclude
NO_CERTIFIED_SAMPLE. It is not a universal required market sample: effective
information, missingness and regime stability still need qualification. Dependence
outside the simulated support must remain INCOMPLETE rather than assumed safe.

## Bounded execution and evidence

First run a small runtime estimate, then publish an execution budget and checkpoint
before the full grid. Partition by cell with resumable immutable outputs; do not
launch an unbounded background job or repeat a broad matrix after every edit.
Each result records contract, implementation and configuration hashes, seeds,
trials, false-positive/power counts, unavailable results, runtimes and intervals.
Mixed-hash or duplicated cell outputs must not merge. No market-data reads.

After one frozen confirmation run, stop and obtain independent review. A passing
simulation does not qualify executable fills, selection bias, market stationarity,
multiple research hypotheses or profitability. Any change to the registered CMC
pass/fail policy requires explicit approval separately from this calibration.

User explicitly stated INDEPENDENTLY REVIEWED ACCEPTED after this design handoff.
Acceptance: ACCEPTED_WITH_RISK for the calibration design. The specified criteria
govern this synthetic study only, not the registered CMC scoring gate. No market
sample requirement or statistical method has yet been certified.

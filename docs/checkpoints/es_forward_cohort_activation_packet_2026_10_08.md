# Forward-only canonical ES cohort activation packet

Role: DIRECTOR. User selected the recommended forward-only preparation.
Risk: HIGH for gate/config activation. State: READY_FOR_INDEPENDENT_REVIEW
for this proposed contract only; activation remains INCOMPLETE.

## Chosen path

Prepare a new analytical cohort for the canonical laptop ES gate. Retain the same
raw state and records, entry latch, warmup and promotion thresholds. Do not combine
it with es_corrected_prospective_v1 on Hetzner. That trial ends October 13 as agreed.
An analytical cohort is not a forced entry, an account reset or an extra collector.

Exact proposed config surface: configs/strategies/es_daily_trend_v1.yaml,
promotion.paper.policy.cohort_start only, after identity/eligibility proof. Do not
copy a date from a commit or this document's preparation time. Archive the old
config and its hash before activation; prepare the candidate outside the active
config path and independently review its diff. No config candidate applied here.

## Preserve exactly

- slow_daily_single_symbol_v1 policy; 45 calendar days, 60 qualified bars,
  five qualified round trips; archive walk-forward and human review required.
- Source public_ohlcv, daily bars, Coinbase BTC/USDT.
- Accepted crossover-only rule, SMA200/ATR20 and declared disabled runner exits.
- Existing account history, positions, fills, fees, signal latch and raw evidence.
- Trial's registered paper cost basis; live fee adoption is a different decision.

## Verified preparation evidence

October 8 latest laptop session completed with no trade; latest signal long,
SMA 71841.3147, source Coinbase BTC/USDT daily. Recorded commit 620bc8dbe is not
proof of loaded dirty source. Latest signal has no input capture metadata.

Actual read-only canonical paper database contains these nonzero legacy positions:
SOL/USD 1.0 at 85.63, ORCA/USD .001 at 9.06803175, ADA/EUR .001 at 9.06803175,
BTC/USD 1.0 at 100.0. No position changed. These must not be reinterpreted as
corrected BTC/USDT entries or used to seed cost basis for a new analytical cohort.

Local runtime YAML contains SMA20 settings owned by another configured strategy;
managed name override can resolve a different preset. Do not infer ES period by
reading that number alone. The actual managed-child resolution must be verified.
Paper fee/slippage fields are 7.5/5 bps; separate unrelated paper_fee fields exist.
One active loaded configuration surface must be identified before acceptance.

## Activation blockers and proof required

1. Verify canonical managed child loaded strategy, source, sizing, exits and cost
   configuration at an observable boundary. Hash loaded/relevant source and seed;
   a checkout hash alone is insufficient. No historical identity guarantee inferred.
2. Verify whether a BTC/USDT position or unfinished cycle exists at activation.
   Preserve any such position; exclude any cycle whose entry predates the boundary.
   Other-symbol legacy positions remain history and cannot count as ES cycles.
3. Prove gate filtering with isolated tests: pre-boundary entries/closes cannot
   count; matching post-boundary cycles count; wrong policy/source/symbol rejected;
   threshold values unchanged. Date alone is not enough to enforce policy identity.
4. Establish explicit identity/cost-version evidence for future observations.
   This is not present in the latest laptop signal. If instrumentation is needed,
   scope/review it separately; do not pretend a cohort date creates evidence.
5. Separate review of exact candidate/config and targeted proof, then record
   actual activation time and effective hash. No retroactive guessed date.

## Recovery and report consequences

Keep old config bytes/hashes available. Reverting a config does not delete new
records or restore a prior evidence claim; report both effective policy periods.
No service restart is implied. If activation needs restart, authorize it separately
after current positions/ownership are established. Gate output is not profitability.

## Next bounded engineering task

Identity-bound eligibility proof on isolated fixtures, using current actual gate
code, before a canonical config change. An independent reviewer must evaluate
whether existing metadata supports this or an evidence-schema addition is needed.
Do not activate until that material fact is resolved. No collector or trial change.

# FC-01-r1 exploratory outcome run

Recorded before the first outcome run on 2026-10-04. One hypothesis: the
previously approved five-level imbalance >= 0.50, six-hour long/cash rule,
330-second availability. No threshold or horizon search in this run.

Input content hash: cd106bd53cf045d6ae10a76d439777d96e832dedceb62b2ca53ad9795f7a60f7.
Frozen input file: fc01_r1_pinned_inputs.json. Reporter: report_fc01_r1.py;
its source hash will accompany output. Design contract in
docs/research/faster_context_hypothesis_draft_20261004.md.

One $100 purchase notional per selected entry; fees additional to purchase.
Model: entry ask, exit bid, 50 bps fee on each leg's actual notional, zero
additional slippage. USD quote/reporting currency. No separate spread charge.
No maker fills, compounding, leverage or infrastructure deduction.

Prespecified descriptive intervals: 10,000 daily-block resamples, seed
20261004; three-day circular blocks as sensitivity, not result selection.
Unavailable windows remain unavailable, including cash decisions; zero-count
days remain in the bootstrap calendar. No intraholding drawdown claim.

This is an exploratory pilot, not confirmation. No power calculation or
confirmation N exists yet. capture_ts is storage time after fetch completion
(collector_service append calls, store _now_iso); upstream exchange freshness
and exact receive time remain unverified. No causal execution/actionability
claim. All costed results are CF-MODELLED, not actual profit.

Absolute negative net value cannot advance merely because the comparator
loses more. No same-data rescue or automatic promotion; independently review
the implementation before any economic decision or confirmation collection.
Historical related experiments are not audited here: this is not a claim that
the project's global multiple-testing trial count is one.

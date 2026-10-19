# FC-01: faster-cadence context feasibility proposal

2026-10-04. DIRECTOR. HIGH, trading-adjacent research only.
Design state: ACCEPTED by human approval. NOT a registered or run experiment.
Input-pinning implementation: ACCEPTED by human approval.
Exploratory outcome implementation: ACCEPTED_WITH_RISK by human approval; see
fc01_r1_exploratory_result_20261004.md. Disposition STOP under tested costs.
No confirmation registration or promotion; other campaigns remain unchanged.
Design revision FC-01-r1: user authorized 330-second freshness and explicit
entry pricing on 2026-10-04, after availability counts but before returns.
The previous 120-second specification is superseded, not retrospectively tested.
No capital, live orders, new collector, campaign change or strategy retirement.
SMA200 and all its history remain intact. This is not E02's unchanged-baseline
comparison and does not close E03's continue/revise/retire decision.

## Question and one fixed candidate

Does positive displayed book imbalance have enough six-hour directional
information to justify a separate costed entry-selection experiment?
Empirical hypothesis, not an established mechanism: persistent buy-side depth
may accompany later upward prices; cancelled depth and adverse selection can
invalidate that relationship. No spoofing or queue-position inference.

Proposed frozen rule: Coinbase BTC/USD, long-or-cash, evaluate at UTC
00:00, 06:00, 12:00, 18:00. Long only when five-level notional imbalance
(bid_notional - ask_notional)/(bid_notional + ask_notional) >= 0.50.
Exit at the next six-hour boundary. No shorting, maker fills, compounding,
threshold sweep, additional features or alternative horizon in this trial.
Threshold and horizon are design choices, not fitted or proven profitable.

Use the last valid snapshot captured at or before each boundary, at most
330 seconds old. Require positive finite bid/ask/depth, ask >= bid and a
positive depth denominator. Never fill missing features from later data.
Entry uses the first valid Coinbase BTC/USD quote captured at/after the
decision boundary within 330 seconds. Exit uses the first valid same-venue
quote captured at/after the next boundary within 330 seconds. Require finite
positive bid and ask, ask >= bid, and source=live_public. Resolve timestamp
ties by ascending row ID. The feature decision remains frozen at the boundary;
the later entry quote cannot change it. Quotes outside the limit are unavailable,
not carried forward or substituted from another venue, symbol or candles.
Gross midpoint drift uses these actual quote capture times, not invented
boundary prices. Modelled immediate taker entry uses entry ask and exit uses
exit bid, with separately declared fees/slippage. This is a delayed quote-based
scenario, not a claim of a fill at the boundary or a latency-validated replay.
Both gated and always-long comparisons use the identical entry/exit quotes.
For a missing entry or exit quote, the paired window is unavailable even if
the rule chose cash; do not turn unknown benchmark returns into zero.
Preserve counts and reasons
for all exclusions and non-entries. Do not drop losing windows selectively.

## Evidence available and limits

SHOWN via read-only SQL inventory on 2026-10-04:
.cbp_state/data/crypto_edge_research.sqlite, source=live_public,
capture_ts >= 2026-08-30: Coinbase BTC/USD has 7,790 book rows and 7,788
quote rows across 36 dates, from 2026-08-30T07:59:04+00:00 through
2026-10-04T00:06:13+00:00. No price outcomes were evaluated for this proposal.
The available interval contains at most 138 complete fixed six-hour windows
before freshness/exclusion checks, not 7,790 independent trades. Feature
eligibility further reduces entries; serial dependence further reduces power.
Days containing rows do not prove continuous coverage or one known regime.

SHOWN: rerunning docs/review_artifacts/20261004_fc01/fc01_gate2_count.py
against that fixed archive cut reproduces all availability counts and the
row-identity hashes in fc01_gate2_eligibility_count_20261004.md. At 120 seconds,
17 windows have a feature and outcome quote, three qualify, but zero qualifying
windows also have an entry quote. At 330 seconds, 106 windows have a feature
and outcome quote, 18 qualify, and 17 also have an entry quote. The complete
paired-window count (including rejected entries) must still be pinned before
analysis; 106 is not that count. No returns were computed. Row-identity hashes
cover IDs/timestamps only, not immutable price-content evidence.
The measured book cadence is median 311 seconds, p90 312 seconds; 330 seconds
is an availability-driven design choice, not a profit-selected threshold.
Seventeen complete qualifying windows are exploratory evidence, not a powered
confirmation sample. Collection gaps remain excluded and reported.

SHOWN after design approval: fc01_r1_pinned_inputs.json in
docs/review_artifacts/20261004_fc01/ contains the selected input fields (including
prices), all 138 window dispositions, exact selected row IDs and exclusion
reasons. There are 101 complete paired windows, of which 17 qualify and 84
choose cash. Input-content SHA256:
cd106bd53cf045d6ae10a76d439777d96e832dedceb62b2ca53ad9795f7a60f7.
This freezes the consumed fields, not the entire database or upstream feed.
Two read-only runs produce byte-identical artifacts. No returns computed.

Roadmap E02 explicitly compares the unchanged baseline. The separate E02
feasibility note uses a signal-only artifact, not a verified replay of all
current runner rules. Its zero-overlap conclusion must retain that scope;
it is not evidence that every actual campaign opportunity lacks context.

## Metrics and cost discipline

Primary proposed metric: paired incremental net return per eligible six-hour
window, gated long/cash minus always-long for that window. Cash windows are
zero strategy return, not discarded. Also require absolute net value versus
cash; an improvement on a losing baseline is not sufficient to advance.
Report rejected-opportunity returns, trade count, coverage, turnover, exposure,
drawdown, quote-currency results and reporting-currency conversions.

Show gross midpoint drift as OBSERVED, and cost-adjusted hypothetical returns
as CF-MODELLED, never actual fills. Use one $100 notional per entry for the
economic scenario, no overlapping positions. Spread/fees/slippage deducted
once only: do not subtract spread again from bid/ask-based executions.
The September 26 work-log entry records 50 bps taker PER SIDE from Coinbase's
authenticated SPOT endpoint (maker 25 bps). That dated observation is supported
by the project record; a fresh account check and historical applicability to
each observation remain UNVERIFIED here. It means a nominal 100 bps round-trip
fee hurdle before spread/slippage, with exact fees calculated on each leg's
notional. A 10-bps incremental improvement over always-long does not pay that
hurdle by itself: the separate absolute-net test is essential.
Verify account/venue/date/fee asset and quote timestamp semantics before
claiming realistic execution. No depth/capacity claim from aggregate snapshots.
Infrastructure cost is reported separately from per-trade trading costs.

## Gates before any outcome run

1. Pin an immutable archive copy/hash, exact eligible row IDs, code/config
   hashes, trial ledger entry, reporting currency and fee/slippage inputs.
   Determine whether capture_ts is usable as an availability timestamp and
   record exchange staleness limitations. No sub-second/actionability claims.
2. Availability count complete for the pinned cut, including the entry-quote
   correction above. Exact complete paired-window IDs, quote IDs and exclusion
   reasons are pinned under FC-01-r1 and human accepted. No collector needed.
3. Set minimum detectable incremental value to 10 bps per eligible window,
   one-sided alpha 0.05 and target power 0.80. Estimate required sample using
   a separate pilot and dependence-aware simulation, not raw row count.
   Do not assign an invented N or completion date without those inputs.
4. Treat the existing short archive as exploratory/pilot only. Freeze a later
   untouched confirmation interval, explicit N and a maximum 90-day deadline
   before looking at its outcomes. If N cannot be met within that cap, report
   INSUFFICIENT_POWER and stop; do not expand symbols or loosen the rule.
5. Prespecify daily-block bootstrap (all four windows remain together), 10,000
   resamples, seed 20261004. Report sensitivity to multi-day blocks as a
   diagnostic, not a selection device. Failure to support dependence assumptions
   means inconclusive evidence, not a positive result.

At the frozen end, advance only to further research if the primary 95% lower
bound exceeds zero and absolute net value is positive under declared costs.
Otherwise STOP/REVISE or INSUFFICIENT_POWER as appropriate. A revision gets a
new ID and new untouched data; it never rescues this trial retroactively.
No outcome here authorizes live capital.

ASSUMPTION 1: captured availability and symbol identity can be validated. If
false, no causal as-of backtest; timestamp/data repair precedes the experiment.
ASSUMPTION 2: costs can be supported or explicitly scenario-labelled. If false,
only gross descriptive analysis is possible; no economic advance decision.

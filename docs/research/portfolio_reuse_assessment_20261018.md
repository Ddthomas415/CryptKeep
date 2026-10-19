# Portfolio reuse assessment: ED-002

Date2026-10-18 New York. Active role AUDITOR; source inspection only.
Assessment complete for the named surfaces; ED-002 implementation INCOMPLETE.
No source import, new backtest, experiment, financial-code edit or test rerun.
25-symbol mandate, frozen V3 artifacts and E7-E10 verdicts unchanged.

## Findings and smallest reuse path

SHOWN: E10 already has a shared cash balance/holdings map and tradable/frozen
partition. `ms_trend.py:50` implements simulation; lines62-68 scale desired
notionals and call the existing joint post-cost `rebalance()` helper. Do not
describe the repo as lacking all portfolio accounting.

SHOWN: `run_multisymbol_baseline.py:88` independently initializes each
symbol/arm. Its replayed prefixes preserve per-arm phase continuity, not a
single shared account. Existing V3 package proof remains scoped accordingly.

| Contract | Existing capability | Gap requiring a frozen decision or targeted implementation |
| --- | --- | --- |
| Shared cash/allocation | E10 one cash/holdings map; math.rebalance jointly solves post-cost target weights | Integration with frozen per-symbol signals and constrained simultaneous entries |
| Sell proceeds | WP4 fixtures declare same-rebalance sells-first; joint helper returns aggregate state | Explicit event ledger and proceeds availability, not assumed venue settlement |
| Affordability | math.rebalance solves costs before quantities; next_open rejects fee-inclusive unaffordable buys | Shared-account adapter plus precision/minimum-order policy |
| Partial fills | Inspected models directly assign quantities | Explicit full-fill-only model scope or residual/reservation/partial-fill behavior; resizing is not a partial fill |
| Missing positions | E10 freezes unavailable holdings but marks last close without an age limit; baseline refuses incomplete grids | Separate executable prices from valuation marks, stale/unknown NAV and delisting policy |
| Carry-forward | Baseline prefix replay avoids intermediate liquidation and derives phase-start equity | Shared-account continuity; E10 independently starts D/H accounts |
| Costs/benchmark | E10 uses common modeled costs for invested comparators; terminal holdings marked | Exposure-matched BTC/ETH/cash control and explicit terminal treatment |
| Historical eligibility | Candle completeness and fixed research basket | Dated venue/asset/status permission input; scope membership is not tradability |

Evidence: `docs/research/multisymbol_trend_20261015/ms_trend.py:29,50,87,109`,
`scripts/research/corrected_research_math.py:102`,
`scripts/research/run_multisymbol_baseline.py:54,88,100`,
`services/backtest/next_open_research.py:45,86`, and
`docs/research/discovery_engine_proposal_review_20261016.md:130`.

Recommendation: extend the existing next-open research surface with one bounded
multi-symbol adapter, reusing rebalance and the tradable/frozen partition.
Preserve the existing single-arm API and frozen E10 script. Do not import E10
as a library: its module body runs experiments and writes results. This is a
reuse recommendation, not financial-logic implementation or approval to retest E10.

## Contracts to settle before implementation

1. Signal-to-target sizing, constrained simultaneous allocation, sells-first
   proceeds availability, and full-fill-only versus partial-fill model scope.
2. Executable versus valuation prices, stale/unknown NAV and historical
   eligibility failures. Never silently mark a stale price as executable.
3. Shared-prefix carry-forward, terminal accounting and matched benchmarks.
   Fixture amounts are not approved user capital. No genuine holdout may be
   created by relabeling already examined history.

Reuse existing tests, not a new platform: tests/test_harness_contracts_wp4.py
(sells-first/affordability/causality/fixed-ledger fees),
tests/test_next_open_research.py, tests/test_multisymbol_archive_runner.py,
tests/test_research_source_slice.py. Their presence is SHOWN; no fresh pass is
claimed in this assessment. Earlier accepted WP4 item1 is not reopened.

## Inspected source identities

```text
ms_trend.py 550dc2ea708c2a37a56f58f41b81b3a25d16f6077a8fa52b0a4bef2b287468cc
corrected_research_math.py d07ae7171e2293cbe60d15ae9bc0973d3ef8bd31b9c7b99105f928c029e29047
run_multisymbol_baseline.py d6ddce6d69a755db67c542e6e29f3e68f06612bd2fc95373490f671e3ead2e78
next_open_research.py 4f5bb1a98be726915bca155b8ea483d5036982ed786665e504c1e444ce2d1a7f
```

Separate specialist AUDITOR performed the bounded read-only assessment; parent
inspected the cited core functions and recorded hashes. Integration, venue
settlement/precision/liquidity and runtime behavior remain UNVERIFIED. No
profitability or portfolio-readiness conclusion follows.

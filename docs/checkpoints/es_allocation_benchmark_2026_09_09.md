# ES Allocation-Matched Benchmark Diagnostic

Active role: AUDITOR. Research only; no deployment decision.

Compared SMA20, SMA200 and buy-and-hold on the frozen 3077-row archive used in
prior diagnostics. Each starts with 100 active quote units and 900 idle cash,
zero cash interest, 7.5 bps fee/5 bps slippage per side. Benchmark entry is bar
209 (first strategy-eligible bar), with terminal sale costs. Both strategy
runs end flat, checked by assertion. Strategy profits stay in the active sleeve.

| Path | Portfolio return | Portfolio max drawdown |
| --- | ---: | ---: |
| SMA20 | 25.09% | 31.77% |
| SMA200 | 85.43% | 32.57% |
| Buy and hold | 67.46% | 36.58% |

SHOWN: initial 10% allocation does not imply a persistent 10% exposure cap:
the growing sleeve is not rebalanced. This is not volatility-matched risk,
not the campaign's actual sizing, and not a test of runner exit controls.
SMA200 beats this benchmark in total modeled return but still suffers a 32.57%
portfolio drawdown. Do not infer capital safety from the initial allocation.

Recommendation: keep exposure unchanged. The identity correction remains valid
independently of profitability; no promotion or sizing increase is supported.
Do not describe the previously inspected archive as a holdout. A genuine
holdout requires reserving a future or demonstrably unexamined period before
outcomes are inspected, with fixed sizing, benchmark and evaluation rules.
Equal-risk testing remains INCOMPLETE, not replaced by this allocation check.

Reproduction: .cbp_state/data/research/es_allocation_benchmark/20260909/ contains
es_allocation_benchmark_20260909.py and matching JSON. Script hash:
e996ccb3e5ee206caf2410e363b0d1b54a6c38601b624689664dd3118fd48371.
Input hash is verified against the prior frozen dataset. Read-only SQLite;
no archive/campaign changes. Existing engine used without modification.
Full suite not rerun for this research artifact.

PR #588: all seven CI checks successful at this inspection; not merged here.
Acceptance state: ACCEPTED for allocation diagnostic only.

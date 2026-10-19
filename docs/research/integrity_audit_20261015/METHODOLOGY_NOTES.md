# Methodology notes from the integrity audit (2026-10-15)

## Trade-sizing convention (explains the $37.83 candidate gap; not a bug)
- **Repo harness** (`scripts/research/corrected_research_math.py::rebalance`): solves by bisection for the post-cost equity E such that E + costs(E) = pre-trade NAV, then sets each position to weight × E. Costs therefore shrink every position proportionally.
- **Blind reimplementation (first version):** sets each position to weight × pre-cost NAV (valued at unslipped opens) and pays fees and slippage from cash. With weights below 100%, positions stay slightly larger, so results are a little higher in rising markets.
- **Evidence:** swapping the harness convention into the blind code (`blind/bgap_diag.py --postcost`) reproduces A $5,555.39, B $9,919.59, C $1,779.58 exactly. Under its own convention the blind code gives A +0.02%, B +0.38%, C −0.06%.
- **Implication:** both are valid modelling choices. Reported results should state which one is used. Differences of a few tenths of a percent between implementations are expected from this alone. Verdicts did not change under either.

## Initial NAV point (affects Sharpe and drawdown, not end value)
- The blind E6 code includes a $1,000 NAV point at the decision close, before the first trade; the repo E6 simulator starts its curve after the first execution. On hold-BTC in E6 period A this changes Sharpe (0.734 vs 0.761) and max drawdown (80.5% vs 78.8%) while end values match. This explanation is inferred, not separately tested.

## E6 product population (480 vs 467)
- 11 products (ALIGN, BASECAT, BLUECHIP, CP, CT, DATA, DRB, GRASS, GRVT, PONS, WHUF) have fewer than 90 valid daily rows. The repo script drops them up front; the blind code keeps them but they can never pass the 90-days-since-listing eligibility rule, so they never enter the universe.
- 2 products (UST, GYEN) are excluded by the repo script's longer stablecoin list but are NOT in the pre-registered exclusion list. This is a deviation of the registered script from the pre-registration text.
- Effect verified: rerunning the blind code with the repo script's longer list (`corrected_crosscheck/e6_blind_stablefix.py`) gives identical results in both modes, to every reported digit. The difference does not change the tested population's results.

## Open bias not addressed by any reproduction
- E10 uses today's surviving Coinbase symbols. Matching implementations do not remove that selection bias; it remains UNRESOLVED and unmeasured.

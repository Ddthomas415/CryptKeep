# Edge classification: BTC+ETH 28d trend, 2026-10-11 (existing results only)

Scope: no new backtests. Sources:
- `research/research_corrections_20261009/stress_corrected_v1.json` (sha256 18033c9b...)
- `dsr_btc_eth_trend_20261011/`

The fixed mix is 50/50 BTC/ETH at the rule's own average exposure in each period. That gives the benchmark hindsight, which makes the test harder for the rule. The mix has the same costs as the rule.

## Rule vs benchmarks (Sharpe / CAGR % / max drawdown %)

| Period | Fee/side | Rule | Fixed mix | Hold BTC |
|---|---|---|---|---|
| A 2016-19 | 0.5% | 1.49 / 65.2 / 51.9 | 1.43 / 50.2 / 49.5 | 1.30 / 105.8 / 83.8 |
| B 2020-23 | 0.5% | 1.70 / 77.5 / 32.8 | 1.17 / 39.9 / 45.3 | 1.00 / 55.6 / 76.7 |
| C 2024-26 | 0.5% | 0.82 / 23.1 / 32.0 | 0.50 / 10.2 / 34.4 | 0.70 / 24.6 / 53.1 |
| A 2016-19 | 1.2% (registered) | 1.33 / 55.5 / 55.7 | 1.39 / 48.6 / 50.0 | 1.30 / 105.4 / 83.8 |
| C 2024-26 | 1.2% (registered) | 0.53 / 12.4 / 35.3 | 0.48 / 9.4 / 34.6 | 0.69 / 24.2 / 53.1 |

**Robustness, from the registered stress test at 1.2%:**
- 5 of 13 one-at-a-time variants beat their own fixed mix on full-period Sharpe.
- 43.8% of the 105-setting grid beats its own fixed mix.
- The bootstrap 90% range of the Sharpe difference (rule minus mix) is −0.22 to +0.41.
- Registered verdict: REJECT (no robust timing edge beyond lower exposure).

**Versus BTC:** the active Sharpe is negative in every window (see the DSR report).

## Classification: Scenario 3, no demonstrated edge
- **Return vs BTC:** no edge.
- **Risk reduction vs BTC:** real, but a simple fixed BTC/ETH/cash mix also delivers most of it.
- **Rule vs the mix:**
  - At the real 0.5% fee tier, the exact baseline settings beat the mix on Sharpe in every period, and on drawdown in B and C.
  - But nearby settings mostly do not. So the timing advantage over the mix is not robust and may be specific to these settings.
- **Caveat:** the registered primary fee was 1.2%, then believed to be the Coinbase taker rate. The account tier observed since is 0.5%. Whether the robustness result changes at 0.5% is untested. Rerunning it now would be a post-hoc, exploratory analysis and needs operator approval.

## What the forward paper test can and cannot do
- **It cannot establish an edge in any practical time.** The standard error of a Sharpe difference between two strategies with return correlation ρ is roughly sqrt(2(1−ρ)/years).
  - At ρ = 0.8–0.9 (this is an assumption, not a measured value), 6 months gives a standard error of ~0.6–0.9.
  - Resolving a difference of 0.3 would take roughly 9–18 years.
- **What it can do:** confirm the pipeline works, and catch implementation breakage or a gross regime failure.

## Consequences
- **Maker-vs-taker:** park it. Under Scenario 3 its result changes no decision. The pre-registration stays as an unfrozen draft.
- **Next evidence that could move the classification:** a labelled-exploratory rerun of the registered robustness checks (13 variants, 105-setting grid, bootstrap) at the observed 0.5% tier. This needs operator approval because it is a new backtest. Even a pass would only move the rule to Scenario 2, small and credible, and would not justify capital.
- **Economic default, if nothing changes the classification:** a fixed BTC/ETH/cash allocation. It needs no bot and no server, which bears on the server decision.

## Addendum (same day): exploratory 0.5% robustness rerun
See `stress_fee050_exploratory_20261011/README.md`.

At 0.5%, the result moves:
- 13/13 variants and 94% of the grid beat the exposure-matched mix;
- 91.1% of bootstrap resamples above zero (not a probability of an edge; the 90% range of −0.05…+0.57 still crosses zero);
- the same rules give "keep_researching".

**Revised status:**
- **Timing edge over a fixed BTC/ETH/cash mix:** UNPROVEN but credible (Scenario 2 candidate). Post-hoc, the same data, weaker in 2024-26.
- **Return edge over BTC:** not shown.

Because the edge is cost-sensitive, the maker-vs-taker study is relevant again. The "park it" line above is superseded, pending the operator's decision.

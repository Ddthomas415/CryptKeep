# EXPLORATORY: stress robustness at the observed 0.50% fee, 2026-10-11

Operator-authorized, post-hoc analysis. It is **not confirmatory**, and the registered verdict (REJECT at 1.2%) is unchanged.

- **Script:** `stress_fee050_exploratory.py`, sha256 c56fdd4d..., written before the first run.
- **Result:** `stress_fee050_result.json`, sha256 4e9ab43f...
- **The only change** from the registered study is the fee: 1.2% → 0.5% per side. Data, execution, slippage, periods, variants, grid, benchmarks, pass rules and bootstrap are all the same. The frozen rerun module is imported unmodified, and its hash and the data hashes are checked.
- **Harness check passed:** the baseline at 0.5% reproduces the stored `stress_corrected_v1.json` result exactly.

## Results (fixed mix = 50/50 BTC/ETH at the rule's own average exposure, with hindsight)

| Check (same rules as registered) | at 1.2% (registered) | at 0.5% (exploratory) |
|---|---|---|
| Required 1: beats BTC and mix on Sharpe AND drawdown in ≥2 periods, incl. A | fail (B only) | **fail** (B, C pass; A fails on drawdown, 51.9% vs mix 49.5%) |
| Required 2: variants beating mix on full-period Sharpe (need ≥10/13) | 5/13, fail | **13/13, pass** |
| 105-setting grid beating mix on Sharpe | 43.8% | **94.3%** (6 losers, all near: L21/Tue and L42/Sat cells) |
| Grid beating mix on Sharpe AND drawdown | n/a | 62.9% |
| Grid beating mix on CAGR | n/a | 104/105 |
| Bootstrap Sharpe diff, 8-week blocks: observed, 90% range, share > 0 | 0.10, −0.22…+0.41, 68% | **0.26, −0.05…+0.57, 91.1% of resamples** |
| Verdict under the same rules | reject | **keep_researching** |

**Recent period (C, 2024-26):** only 8 of 13 variants beat the mix. The losers are:
- L14 (−0.25 vs 0.50);
- L21;
- Tuesday and Wednesday rebalances;
- BTC-only.

Period A: 12/13 beat the mix. Period B: 12/13.

## Reading (rule fixed before the run: a pass justifies more research only)
- **Not disproven.** At the realistic fee, the timing advantage over an exposure-matched mix is broad across nearby settings, not specific to one setting. It was the 1.2% fee that erased it.
- **The bootstrap figure** is the share of bootstrap resamples with a positive difference (91.1%). It is not a calibrated probability that an edge exists, and its 90% range still crosses zero.
- **Still unproven:**
  - the analysis is post-hoc;
  - it uses the same data the rule was selected on;
  - the variants are highly correlated, so 13/13 is not 13 independent confirmations;
  - the bootstrap 90% range still crosses zero;
  - it is weaker in 2024-26 (8/13).
- **Unchanged:** no return edge over holding BTC (see the DSR report).
- **New implication:** the edge over the mix is cost-sensitive. It is broad at 0.5% and mostly gone at 1.2%. That puts execution cost and turnover on the critical path, which is Scenario 2 territory.

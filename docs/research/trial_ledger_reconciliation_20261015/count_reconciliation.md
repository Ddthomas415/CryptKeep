# Trial-count reconciliation: historical vs revised (2026-10-15)

Counting configurations is an audit result. Estimating effective independent trials is a statistical modelling choice. They are reported separately below. Nothing here changes any registered verdict.

## 1. The October 11 figures (preserved as historical estimates)
Source: `../dsr_btc_eth_trend_20261011/README.md`. It stated "~576" raw configurations and a best-supported effective count of 10-15. It used V broad = 0.411/yr (SD of 11 Binance strategies' test Sharpes) and V narrow = 0.12/yr (105-setting neighbourhood).

## 2. Audit of the October 11 table (verified against the artifacts)
| Source | Oct 11 value | Recount from artifact | Status |
|---|---|---|---|
| Altcoin event search | 448 | 448 (`combinations_tested`) | match |
| Binance hybrid | 11 | 10 non-benchmark strategies (12 names incl. btc_hold, equal_weight_top20) | DISCREPANCY |
| Majors rules | 4 | 4 | match |
| Top-10 trend | 4 | 3 (`topn_trend` N = 5, 10, 20) | DISCREPANCY |
| Recovery / regime | 16 / 32 | 16 / 32 | match |
| CMC proxy | 20 | 20 | match |
| Dynamic Coinbase | 8 | 6 (8 includes hold_BTC, hold_ETH) | DISCREPANCY |
| Short holds | 14 | 14 | match |
| Three ideas | 9 | 24 (12 + 8 + 4 parameter combinations) | DISCREPANCY |
| **Sum** | **566 (stated as "~576")** | **577** | the stated total did not equal its own rows |

Configurations are distinct parameter sets; fee levels, periods and modes are evaluations of the same configuration and are not counted again.

## 3. Revised raw count of executed configurations
- Oct 11 sources, recounted: **577**.
- Executed but omitted from the Oct 11 count, or run since: **113** (strategy horizon scan 40; OKX multi-symbol 15; ES exit matrix 8; ES trial 1; ES v1 paper 1; FC-01 1; carry feasibility 1; leader daily 2; leader target 8; failed breakout 1; Monday diagnostic 1; E6 9; E7 5; E8 4; E9 3; E10 13).
- **Revised raw total: at least 690**, plus 9 families whose configuration counts are not yet established (EMA campaigns, breakout campaign, funding signals, hourly leader arms, reversal diagnostic, dip screen, colour-flip, BLAST/VARA, CMC trending log tests).
- Post-selection robustness (105 + 13 = 118) is reported separately, as in Oct 11.
- Duplicate implementations (the JUP/SUPER/SYRUP rerun, corrected reruns, blind reimplementations, re-evaluations at new fees) add no configurations.

## 4. Distinct economic hypotheses
Nine mechanism groups appear in the inventory (`mechanism_group` column):
H1 time-series trend; H2 cross-sectional momentum; H3 altcoin event / pump / dip / leader; H4 intraday technical rules; H5 carry and funding; H6 attention; H7 order-book imbalance; H8 calendar; H9 execution (not run).
About 35 separate research programs (each with its own data, rules and selection step) sit under them.

## 5. Effective independent trials: estimates, not a count
| Method | N | Assumption | Weakness |
|---|---|---|---|
| A. One per mechanism group | about 9 | variants inside a mechanism are near-duplicates | understates: programs within H3 used different data and selection |
| B. One per research program | about 35 | each program is an independent search | overstates where programs share data (e.g. H3 on the same hourly archive) |
| Historical (Oct 11) | 10-15 | selection chain that led to the candidate | predates about 113 further configurations |
| C. Raw configurations | at least 690 | every configuration independent | an upper bound, not realistic |

No method here has been independently checked. A return-correlation clustering of the trials could narrow the range, but many artifacts (e.g. the 448 event rules) store per-trade means rather than daily return series, so it cannot be run on all trials yet.

## 6. DSR inputs: sensitivity, not a verdict
The expected-maximum hurdle SR0 (annualized) for a Sharpe selected from N trials, using the Oct 11 V values:

| N | SR0, V broad (0.411/yr) | SR0, V narrow (0.12/yr) |
|---|---|---|
| 10 | 0.65 | 0.19 |
| 15 | 0.73 | 0.21 |
| 35 | 0.88 | 0.26 |
| 120 | 1.07 | 0.31 |
| 690 | 1.29 | 0.38 |

Formula: SR0 = sqrt(V) x ((1 - gamma) x Phi^-1(1 - 1/N) + gamma x Phi^-1(1 - 1/(N e))), gamma = Euler-Mascheroni. These are hurdle inputs only. **No DSR is recomputed here, and none should be treated as valid until N and V are independently checked.** V itself is unverified as a description of the full trial set: it was estimated from 11 strategies (broad) or one neighbourhood (narrow), not from the distribution of all Sharpes tried.

## 7. Unresolved
- Configuration counts for the 9 UNRESOLVED families.
- Whether the hybrid count of 11 and the top-10 count of 4 intentionally included a comparator.
- The exact datasets for ALT_EVENT_SEARCH and FAILED_BREAKOUT (marked "to be confirmed" in data_overlap.csv).
- A V estimated from the actual distribution of tried Sharpes, and an independent check of the effective-N method.

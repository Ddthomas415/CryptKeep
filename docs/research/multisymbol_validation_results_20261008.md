# Multi-symbol validation results

MODELLED exploratory results, not actual profit or validated edge. July 1 to
September 1, 2026 UTC, end-exclusive. Frozen settings and manifest unchanged;
cash and positions carry from January. No intermediate liquidation.

## Base-cost results

USDT quote equity change at 25 bps fee and 5 bps adverse slippage per side.
Independent arms start with 1,000 cash and use 100-notional entries.
Validation change is ending marked equity minus discovery ending marked equity.

| Coin | Breakout July-Aug | EMA July-Aug | Mean reversion July-Aug | Buy-hold July-Aug |
|---|---:|---:|---:|---:|
| BTC | 8.14 | 5.24 | 8.07 | 22.76 |
| ETH | 27.53 | 41.52 | 7.38 | 30.13 |
| SOL | 25.43 | 30.73 | -4.24 | 23.57 |
| ADA | 26.33 | 34.81 | 19.68 | 16.06 |
| XRP | 28.76 | -14.74 | -4.92 | 18.44 |

Cash is zero before infrastructure. Twelve of fifteen strategy arms gain in
this period at both 10 and 25 bps fees; eleven gain at 60 bps.

| Coin | Breakout Jan-Aug | EMA Jan-Aug | Mean reversion Jan-Aug |
|---|---:|---:|---:|
| BTC | -9.02 | -33.42 | -22.21 |
| ETH | 12.29 | 25.73 | -36.06 |
| SOL | 17.02 | -5.13 | -59.09 |
| ADA | -35.67 | 2.23 | -26.75 |
| XRP | -2.84 | -26.46 | -42.85 |

Only four arms are positive cumulatively at base costs. Period gains do not
erase discovery losses. Cycle counts are thin, especially mean reversion.
No confidence interval, significance, candidate selection or promotion claim.

## Attribution and limits

ETH/ADA mean-reversion and all five buy-hold controls inherit positions:
21 outcomes across three cost scenarios. Their validation change is not PnL
solely from validation-initiated trades. Full-cycle realized PnL of an inherited
trade includes earlier history; do not sum it as phase profit. Raw equity rows
preserve starting cash and position quantities.

ADA EMA and ADA mean-reversion remain open at endpoint, as do all buy-hold
controls. Marked equity includes unrealized PnL, with no invented exit fee.
Other strategy arms are flat. Raw drawdown, fees, cycles and time-in-market
are prefix metrics, not phase-local metrics. Calendar reporting and uncertainty
remain unfinished. Independent arms cannot be summed as a shared portfolio.

SHOWN: runner exit0, all5 MODELLED_RESULTS,75 outcomes. Manifest SHA256:
907768a3d839232e847dd1e9f62d5bd0c261572c062f7ae32790ced6172bac30.
Local base-cost checks verify exact discovery equity/trade prefixes and starting
equity across25 arms. Separate read-only AUDITOR found no discrepancies across
all75 outcomes: exact discovery prefixes, phase attribution, inherited positions,
manifest/plan/snapshot/config/archive hashes, fees, cash, quantities and execution
math. All437400 cumulative equity rows reconcile. This verifies descriptive
artifact consistency only, not economic edge or promotion eligibility.
Artifact: research/multisymbol_baseline_v1/validation_20261008.json.

Account fees remain UNVERIFIED. Deterministic hourly signal-only simulation is
not measured execution, L2 simulation, causal event analysis or live profit.
Infrastructure is the operator's approximately USD20/month shared estimate;
not deducted per arm, and USDT is not a verified USD conversion.
No source/config/campaign/account changes or new fetch. Final segment unscored.

Next after audit disposition: run the registered final segment unchanged,
including terminal liquidation, labeled exploratory rather than assured
untouched holdout. No settings will be changed to rescue losses.

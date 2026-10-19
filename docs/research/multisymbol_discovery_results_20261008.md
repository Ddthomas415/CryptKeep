# Multi-symbol discovery results

Status: MODELLED exploratory discovery, not actual trading profit or validated
edge. Period: 2026-01-01 to 2026-07-01, UTC end-exclusive. Validation and final
segment performance have not been evaluated. No thresholds/configs were tuned.

## Completed work

- Public OKX spot backfill: BTC, ETH, SOL, ADA and XRP against USDT; hourly;
  6,852 strict contiguous bars per market including 300 warmup bars.
- Frozen 15 phase prefixes. Preserved manifest SHA256:
  907768a3d839232e847dd1e9f62d5bd0c261572c062f7ae32790ced6172bac30.
- Discovery: all 15 registered strategy/coin arms, three fee scenarios each,
  plus cash and fixed-notional buy-and-hold controls. All markets completed.
- Each arm independently starts with 1,000 USDT-equivalent quote cash, takes
  100-quote-notional entries and executes prior completed-bar signals at next
  open. Cash/positions carry across later splits; no discovery-end liquidation.
- SHOWN ledger checks passed on 75 strategy/control outcomes: fixed entry
  notional, reconstructed cash, summed fees, completed cycle counts, preserved
  manifest and no intermediate liquidation. Core/prefix tests: 40 passed.

## Base cost scenario

Net quote change at **25 bps fee per side plus 5 bps adverse slippage per side**:

| Coin | Breakout | EMA cross | Mean reversion | Buy-and-hold control |
|---|---:|---:|---:|---:|
| BTC | -17.16 | -38.66 | -30.28 | -33.39 |
| ETH | -15.24 | -15.78 | -43.44 | -47.37 |
| SOL | -8.41 | -35.86 | -54.85 | -41.19 |
| ADA | -62.00 | -32.58 | -46.42 | -57.02 |
| XRP | -31.60 | -11.73 | -37.93 | -43.82 |

Cash control is zero before infrastructure. All 15 strategy arms lose under the
base scenario. At 10 bps fees, only SOL breakout is positive (+3.0049 USDT);
at 60 bps fees, all 15 are negative. The actual account fee tier remains
UNVERIFIED; these are sensitivities, not measured fees.

Breakout completed 37–45 cycles per coin; EMA 15–22; mean reversion 3–5.
Thin cycle counts do not justify a general no-edge conclusion. No confidence
interval or statistical-significance claim is made. Beating losing buy-and-hold
is not positive gain; no winner at the base fee scenario should be presented as
a profit candidate. No arm is promoted or adopted based on this period.

ETH/ADA mean-reversion and all buy-and-hold arms remain open. Their results
include marked unrealized PnL without a hypothetical discovery-end exit fee;
other strategy arms are flat. This follows the operator's carry-forward decision.
The final segment will include terminal liquidation if reached.

Infrastructure remains the operator's approximately USD20/month shared estimate,
not deducted in the table. Quote figures are USDT, not verified USD conversions.
Do not aggregate independent 1,000-quote accounts into a portfolio or deduct
the shared bill separately from every arm and sum it. No business/profitability
claim is supported by these discovery figures.

## Evidence and limits

Raw artifact: research/multisymbol_baseline_v1/discovery_20261008.json.
Archive, frozen strategy/source snapshot, manifest and per-symbol download
receipts reside in the same directory. Original campaigns/accounts were untouched.

This is signal-only simulation, not campaign stop/risk logic, an L2 execution
model, causal event analysis or live PnL. Costs are deterministic scenarios;
drawdown is bar-close sampled. Historical final quarantine is not assured
untouched data. Complete daily/week/month reporting and uncertainty analysis
remain unfinished; prefix totals are not disguised as phase-local statistics.

Recommended continuation: run the registered validation phase with exactly the
same configs and preserved manifest, without changing fees or thresholds to
rescue discovery losses. Keep the final segment unscored until the validation
report is recorded. Any new rule or tuning becomes a separately registered
hypothesis, not a rewrite of this experiment.

Separate read-only AUDITOR found no discrepancies: verified all15 frozen archive
prefix hashes, selected source/config fingerprints, 75 outcomes, next-open costs,
cash/quantity/cycle PnL and325800 equity rows. It independently confirmed all15
base-fee losses and SOLbreakout +3.004928USDT at10bps. No validation/final report
artifacts were found; their absence alone is not proof no computation occurred.
This audit validates descriptive artifact consistency, not economic edge.

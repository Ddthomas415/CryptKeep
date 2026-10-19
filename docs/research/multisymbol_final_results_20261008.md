# Multi-symbol final historical results

MODELLED exploratory research, not live profit, validated edge or assured
untouched holdout. September 2026 is the final phase; accounts carry from
January 1. Frozen strategy settings, fees, sizing and manifest are unchanged.
All remaining positions are liquidated at the final close with modeled exit
fee and adverse slippage. All five markets completed; all 75 outcomes end flat.

## Base costs

Quote profit in USDT, 25 bps fee plus 5 bps adverse slippage per side.
Each arm independently starts with 1,000 cash and takes 100-notional entries.
September profit is ending liquidated equity minus August ending marked equity.

| Coin | Breakout Sept | EMA Sept | Mean reversion Sept | Buy-hold Sept |
|---|---:|---:|---:|---:|
| BTC | -5.33 | 3.47 | -1.11 | 5.46 |
| ETH | -7.79 | 7.91 | 0.32 | 7.06 |
| SOL | 6.05 | 7.00 | 0.00 | 11.79 |
| ADA | 7.09 | -6.52 | 25.90 | 14.37 |
| XRP | 1.93 | 5.71 | 0.00 | 5.74 |

| Coin | Breakout Jan-Sept | EMA Jan-Sept | Mean reversion Jan-Sept | Buy-hold Jan-Sept |
|---|---:|---:|---:|---:|
| BTC | -14.35 | -29.95 | -23.32 | -5.17 |
| ETH | 4.50 | 33.64 | -35.74 | -10.19 |
| SOL | 23.06 | 1.87 | -59.09 | -5.83 |
| ADA | -28.58 | -4.29 | -0.85 | -26.59 |
| XRP | -0.90 | -20.75 | -42.85 | -19.65 |

Cash is zero before infrastructure. Positive strategy counts (September / full
period): 10 bps fee 9/8; 25 bps 9/4; 60 bps 7/1. Do not reinterpret a fee
scenario as the actual account tier, which remains UNVERIFIED.

## Screening and economics

Only four arms make positive cumulative modeled profit at base costs: ETH
breakout, ETH EMA, SOL breakout and SOL EMA. This does not establish edge.
ETH EMA has the highest cumulative result, 33.6381 USDT, but only 22 completed
cycles across the entire period. SOL breakout has 57 cycles; SOL EMA has 32.

September cycle counts are 0-9 per strategy arm. No arm reaches 30 cycles in
the final segment. The registered candidate rule does not explicitly define
whether its 30-cycle floor is phase-local or cumulative. On a cumulative
reading SOL breakout, SOL EMA, ADA breakout and XRP breakout pass the simple
positive-September/30-cycle screen; on a September-only reading none do.
This ambiguity is disclosed, not resolved in favor of attractive results.
No candidate selection or promotion is authorized by either reading. Calendar
reporting, uncertainty and prospective confirmation remain necessary.

The shared infrastructure estimate is approximately USD20/month, or USD180
over these nine months. Even the largest cumulative arm result is much smaller
numerically. This comparison assumes approximate USDT/USD equivalence only;
no conversion rate or invoice was verified. Costs are not deducted repeatedly
from separate arms and returns are not summed into a fictitious portfolio.
No larger-notional scaling or commercial profitability claim is supported.

## Carry-forward and liquidation attribution

September includes exposure inherited from August. Full-cycle realized sell
PnL is not the same as September equity change. Terminal_cycle_net_quote_pnl
contains an entire trade's PnL, not just the terminal exit's cost or September
contribution. Fees and adverse slippage on final exits are included; flat arms
do not incur a fabricated terminal trade. Raw equity rows are pre-liquidation
bar-close marks; terminal_equity_quote captures the final exit and its costs.

Raw drawdown, exposure, fees and closed-cycle totals are cumulative prefix
metrics, not September-only statistics. Drawdown is hourly-close sampled,
not intrabar maximum loss. Signal-only exits do not model the campaign risk/
stop stack. Missing uncertainty, measured fee tier and L2 execution evidence
remain limitations; price data do not explain governmental or other events.

## Evidence and next step

SHOWN: final runner exit0, all5 MODELLED_RESULTS, preserved manifest SHA256
907768a3d839232e847dd1e9f62d5bd0c261572c062f7ae32790ced6172bac30.
Local base-cost checks verify validation equity/trade prefixes, phase starting
equity and flat final positions across25 arms. Separate read-only AUDITOR found
no discrepancies across75 outcomes,491400 equity rows and39 terminal exits;
verified frozen hashes, exact validation prefixes, costs and phase attribution.
It confirmed the cycle-window ambiguity. Descriptive consistency only, not
economic acceptance. Raw artifact:
research/multisymbol_baseline_v1/final_20261008.json.

No source/config changes, fetching, campaign/account mutation or live trading.
This completes the three raw phase runs, not every required research report.
Next: derive reproducible calendar outcomes and uncertainty from these frozen
artifacts, preserving every arm and benchmark, before any prospective candidate
decision. Do not tune settings or change the registered rule retrospectively.

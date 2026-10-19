# Multi-symbol baseline v1

Role: DIRECTOR. Risk: HIGH for the subsequent financial simulation. This
registration changes research documentation only, not strategies or campaigns.

The plan is `research/multisymbol_baseline_v1/plan.json`. It bounds the first
experiment to five fixed spot markets, one-hour bars and three existing frozen
signal strategies. These are research choices, not claims about liquidity,
availability, suitability or profitability. Public-market availability must be
checked before collection. No asset substitution after looking at results.

## Scope and evidence

Objective: identify post-cost strategy/market candidates, not optimize win rate
or satisfy an invented daily return target. Five-minute and broader-universe
research remain in scope for later registered experiments, not this first run.
ES remains a separate daily strategy/trial; funding requires funding context,
so neither is silently evaluated as an hourly price-only arm.

Freeze resolved preset configurations and code hashes before fetching new data.
Record every one of the 15 strategy-symbol arms and 45 fee scenarios, including
failures. Use archive hashes, complete hourly grids and source instrument
metadata; never repair missing prices with another symbol or venue.

Dates and sizing are fixed in the plan. Historical final-period quarantine is
not proof of an untouched holdout: previous research may already have exposed
parts of these markets. Results remain exploratory. A selected candidate needs
separately registered prospective confirmation; no existing trial is extended.

Fee/slippage values are scenarios, not measured account costs. Quote profit is
USDT, not automatically USD. Report USD equivalence only with an explicit
conversion source. Infrastructure is the operator's approximate shared USD20
monthly estimate; show it separately, do not deduct it from every independent
arm and then sum those deductions or returns. Each arm models its own USD1000
equivalent account; adding independent returns does not produce a portfolio.

Report daily equity and observed weekly/monthly outcomes, drawdown, exposure,
closed cycles, terminal liquidation contribution, costs and cash/buy-hold
controls. Do not invent profit/hour by dividing total profit into a guarantee.
Minimum cycle count is a screening floor, not statistical power or evidence of
edge. Show uncertainty and search count before candidate selection.

## Proven tooling limitation and next treatment

Source inspection of `services/backtest/parity_engine.py` shows signal inputs
include the current completed candle and fills use its close, with full-cash
sizing. The plan requires next-bar-open execution and fixed USD100-equivalent
entries. Existing archive backfill/storage can be reused; the parity result
cannot be presented as satisfying this execution contract.

Next: implement a research-only adapter around the existing frozen next-open
comparison, supporting hashed archive inputs, explicit splits and these sizing
rules without changing canonical parity or runtime trading. Required proof:
synthetic next-open/no-lookahead test, fee/terminal liquidation arithmetic,
chronological boundaries, invalid/gapped data refusal, frozen config hashes,
and independent review before real-data economic conclusions.

No data was fetched and no experiment was run during registration. No new
collector, credential change, live order or campaign mutation is authorized by
this document. This is an explicit plan, not a completed profitability study.

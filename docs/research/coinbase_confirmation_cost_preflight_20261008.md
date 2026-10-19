# Coinbase confirmation cost preflight

Operator chose Coinbase. OKX baseline, frozen settings and results unchanged.
No trading/account migration or campaign activation follows from this choice.

SHOWN VERIFIED_ENV laptop,2026-10-08T23:40:20.616525UTC: one read-only
GET transaction_summary product_typeSPOT using existing Keychain credentials
returned maker25bps,taker50bps per side. Promo-fee and cost-plus flags false.
Receipt: research/coinbase_fee_observation_20261008.json. No credentials,
rawresponse, balances, volumes or accountIDs displayed/saved; no order or
credential write. Historical/product-specific all-in costs remain UNVERIFIED.

Official contract:
https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/fees/get-transaction-summary

InstalledCCXT4.5.48 fetch_trading_fees swaps maker/taker assignments, confirmed
by source and separate reviewer. Observer reads explicitly named raw fields,
with isolated disabled transport logger and exception-type-only reporting.
No dependency change.13targeted tests passed locally; separate GATE13passed,
ACCEPTED_WITH_RISK. A DEBUG logging blocker was fixed before the request.
The actual request was not independently repeated; redacted receipt is proof.

SHOWN: ten bounded public product metadata requests for BTC,ETH,SOL,ADA,XRP
againstUSD/USDT returned matching IDs,SPOT,online,trading_disabledFalse,
is_disabledFalse,view_onlyFalse. USD products haveUSDC aliases;USDT have none.
No credentials used. This is catalog coverage, not account tradability,
historical candle continuity, liquidity, capacity or execution evidence.

Next-open simulation is taker-like: current50bps per side is the applicable
account-tier research input, pending exact product verification. Maker25bps
cannot substitute to rescue results without separate maker-fill/adverse-selection
research. A100quote buy incurs0.50quote fee at50bps; sell fee follows its own
notional. Fivebps slippage remains a modeled assumption, not measured slippage.
Current Coinbase fees cannot be applied as actual historical OKX fees.

Recommendation: register a NEW Coinbase research contract, preserving all15
frozen strategy/coin arms and same-quoteUSDT products where coverage permits,
fixed100entries, next-open execution and carried-account logic. Define dates,
the30cycle window, sample/stopping rules and fee-refresh policy before new
results. No prospective confirmation, candidate selection, collector or
backfill started here. No fullsuite/CI or live proof is claimed.

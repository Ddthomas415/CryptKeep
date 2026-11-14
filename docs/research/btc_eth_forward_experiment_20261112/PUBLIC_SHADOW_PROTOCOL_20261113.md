# Bounded public execution diagnostic, not the E1 validation study

Bot relation: STANDALONE public research/shadow arithmetic. Runtime trading configuration not checked; no account data or actual order is used.

Owner approved the financial and public-data research packages in the current chat. This document bounds the **one-session preparation and at most one diagnostic**, not ongoing collection. The existing [E1 readiness reconciliation](../e1_readiness_reconciliation_20261028.md) and [E1 draft](../maker_taker_prereg_20261011/PREREGISTRATION_draft_v3.md) remain unchanged/unfrozen. Neither the tiny diagnostic nor public prints can establish actual account fill rates, strategy profit or a qualified E1 outcome.

## Fixed scope and end

- Completion/stop deadline: **2026-11-13T18:00:00Z**. Stop and report completed/partial items then; no open-ended sample, autonomous retry, new schedule or background process.
- Products BTC-USD and ETH-USD only, venue Coinbase Exchange public REST. At most10GETs in one foreground process: each product's public metadata, initial L2 book, arrival-proxy L2 book after2seconds, final L2 book afteranother2seconds, latest100 public trades. This is approximately a short four-second market path plus HTTP latency, **not** E1's60minute horizon or a Monday sample.
- Maximum5seconds/request,75second outer process bound,1MiB/body/10MiB total. TLS verification enabled, proxies/environment credentials disabled, no redirects/retries/auth/private endpoints. Failure preserves partial public receipts and stops without repairing, substituting sources or running another attempt. No dependency installation.
- Observe no later than the overall deadline after one independent source review and synthetic proof. No request before review. An unsuccessful prerequisite/capture is an honest incomplete result, not authority to repeat. Body/filesystem/outer-process uncertainty is reported rather than claiming a guaranteed cleanup or zero side effects.
- New append-only diagnostic namespace only; never write to tracker, CMC, primary Monday/eight-week observations, campaign or account state. This Friday snapshot cannot become a primary observation by renaming its timestamp.

## Source meaning and identity

Official sources opened2026-11-13: [Exchange product book](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-book), [Exchange product trades](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-trades), [single-product identity and status](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-single-product). L2 sizes are aggregated base units at each price; order count is not a multiplier. Trade `side` is **maker side**, not aggressor side. The trade endpoint is paginated; one page is not proof of full interval coverage. REST books also cannot show intervening cancellations/hidden liquidity or prove that an inserted order would leave the market path unchanged.

Retain product identity and status/disable/cancel/limit/post-only/auction evidence when supplied. Unknown flags, absent source timestamps or uncertain local/exchange alignment remain unknown. No inference that a received book is exactly the state at a hypothetical order arrival, and no assertion of uninterrupted tradability from isolated endpoint metadata.

Public receipts: original bytes, hashes, allowlisted public headers, product/endpoint identity, local UTC request/receipt, monotonic duration, source time/sequence when present, budget/failure records. Exclude raw credentials, environment dumps and private config. Invalid or incomplete inputs may be retained as evidence, never coerced into a valid quote/fill.

## Required diagnostic output

Report bid/ask and full spread in bps `10000*(ask-bid)/mid`, fractional half-spread `(ask-bid)/(2*mid)`, observed snapshot times and duration/arrival uncertainty. Report visible dollar depth within10bps where available without extrapolating beyond captured levels; distinguish base size, dollar notional and order counts. Report mid movement between snapshots and available public trade-price dispersion as **short-window descriptive context**, not an annualized volatility estimate or a high/low-volatility market classification. Missing prices/empty or malformed sides/auction/crossed/nonfinite books produce explicit incomplete diagnostics.

Retain available public trade prints and their timestamps/side semantics; deduplicate/conflicting records cannot silently supply a fill. Report incomplete pagination/interval coverage, absent prints and observation errors. No complete trade tape, no-trade interval or queue position is asserted from the single page. No fill rate/confidence interval is estimated from two assets in one short observation.

## Hypothetical maker/taker comparison

This is a **stress/sensitivity illustration**, not an E1 finding. Use the same base quantity for BUY/SELL methods, derived from a $500 reference notional at initial midpoint, with product precision/minimum constraints explicitly handled or marked unqualified. No account allocation or live order size changes.

T0-derived limit is the initial bid for BUY or initial ask for SELL; arrival book is the common execution reference for post-only eligibility and immediate-taker depth walk. If the limit would cross the arrival book, label it hypothetical post-only rejection, not an exchange acknowledgement. Unknown eligibility excludes cost comparison. Insufficient depth excludes both methods; do not extrapolate a last price to fill an unobserved residual.

For valid inputs compare clearly labeled alternatives: immediate arrival taker; an **assumed full maker fill** at the resting limit if eligible; and **no maker fill followed by full final-book taker fallback**. The favorable full-fill case assumes sufficient priority/eligible volume and ignores unobserved queue changes; it is not established by a small at/through print. Keep observed trade-through indicators separate from those assumptions. If partial filling is introduced, residual quantity must be crossed at final observed depth under an explicitly reviewed model; it is not silently free or fully filled.

Price implementation shortfall is signed consistently: BUY cost above initial midpoint, SELL cost below midpoint. Report fees separately with25bps maker/50bps taker as dated provisional fee **scenarios**, not current product/account confirmation. Charge maker fees only to assumed maker-filled quantity, taker fees to immediate/fallback quantity. A no-fill fallback may be better or worse due to price movement; do not declare the extremes proven bounds or a guaranteed saving. No simulated sell is a claim of shorting capability or assets held.

Evidence labels are mandatory and independent:
- **OBSERVED_PUBLIC_MARKET_DATA:** successfully captured public bytes with provenance and validation limits.
- **SIMULATED_EXECUTION_ESTIMATE / CF-MODELLED:** method scenarios under assumptions, conditional on available data.
- **ACTUAL_ACCOUNT_FILLS: UNVERIFIED:** no real order was placed, no queue acknowledgement, actual fee or account fill measured.

## Monday window and remaining boundary

The [prospective draft](CRITERIA_DRAFT_V3_3.md) separately describes weekly Monday00:00 UTC observation eligibility in its first60seconds. Today's diagnostic supplies **zero** such primary observations. No scheduled job, always-on collector, new dates or study activation is created. A future event-window invocation/monitoring arrangement must be specifically authorized and reviewed; a foreground process cannot promise attendance at future times after it ends.

After the one diagnostic, report what was observed, what the shadow assumptions did and which gaps remain. No new maker parameter search, strategy modification, backtest, account API, order/cancel/transfer, server/deployment or live trading follows. Finish the finite package and reassess whether further economic evidence merits work; do not keep collecting merely to avoid a negative or incomplete answer.

What do I know that could change the owner's decision that I have not yet said?

Even perfect receipts from this tiny sample cannot identify actual account maker fill probability or the strategy's durable edge. If public depth/prints/status or clocks are insufficient, the correct output is incomplete; the diagnostic's value is exposing that limit cheaply, not generating a favorable cost number.

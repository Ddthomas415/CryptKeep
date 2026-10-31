# ED-002 defaults-25: proposed input contract

2026-10-27. Active role DIRECTOR. Risk HIGH: proposed financial/research timing.
State READY_FOR_INDEPENDENT_REVIEW. Proposal only, not frozen or adopted.
No implementation, fetch, study, calibration, activation or trading permission.
This supplements rather than rewrites the independently reviewed original
`ed002_defaults25_comparison_design_20261027.md` and its historical bindings.

## Practical Decision

SHOWN: the accepted bridge can use 300 completed hourly bars only if their
`known_at_ms` values are no later than the decision close. The proposed design
fills at that close's next hourly open. A receipt after the boundary is too late.
Do not rewrite receipt times as candle-close times to make this pass.

One synthetic source-level probe on the unchanged `HourlyPanel.window` confirmed:
300 bars known at their closes pass; the identical final bar known 1 millisecond
after its close raises `missing_or_unavailable_ohlcv:TEST-USD`. This is the guard
working as designed, not a regression in accepted financial code. It shows a
timing compatibility constraint, not the actual latency of a live feed.

Recommendation: choose a fixed one-hour delay for the new prospective comparison
rather than imply that polled public candles support instantaneous execution.
That changes execution timing, not frozen signal parameters; it needs explicit
adoption and a separately reviewed synthetic-only extension before use. The
existing next-open model and all prior results remain intact.

Alternative: retain immediate next-open execution as an explicitly idealized
bar-model study. It can be useful exploratory research, but must not claim
receipt-time availability, measured latency or confirmation of executable edge.
It must not silently stand in for the original prospective causal design.

## Proposed Rules To Carry Into Registration

1. Universe: keep all 25 declared assets and all 75 family/asset consideration
   rows. Exact Coinbase product/base/quote identity and source hashes are required;
   matching tickers alone are candidates. Preserve MATIC's dated exclusion;
   no POL substitution, survivor removal or reduction to BTC/ETH. Known public
   exclusions leave allocation in cash; unresolved required facts remain unknown.
2. Availability: retain original bar-open time, first observed receipt time and
   payload hash separately. For an authorized historical diagnostic, an assumed
   publication time must be labelled modelled, never observed. Previously used
   archives ending October 9 are not fresh confirmation or current warm-up.
3. Delayed profile, IF adopted: signal bar ends at T; use exactly the frozen
   300-hour window ending T, received by cutoff T+1 hour; execute at the modelled
   open T+1 hour. Do not incorporate the later bar into that signal or use a
   delayed receipt arriving after cutoff. The incumbent's Sunday signal is also
   delayed by one hour; initial controls and evaluation boundaries must be aligned
   explicitly in a revised protocol before freeze. Fixed delay is a modelling
   allowance, not a measured/guaranteed execution latency. No implementation yet.
4. Missing data: no interpolation, last-price carry, invented zero recovery,
   retrospective availability or silent removal of a failed account. Unknown
   required held valuation/eligibility or unexplained required signal gaps make
   the affected comparison INCOMPLETE. Retain stopped state/last valid NAV and
   report the failure, not an economic FAIL. A documented recent listing with
   insufficient history remains signal-not-ready while flat. Known ineligibility
   and a known missing execution open keep the accepted engine's exclusion/expiry
   behavior; do not silently replace it with a retry. Benchmark entry failure
   invalidates that benchmark comparison, not a successful cash-only substitute.
5. Status: preserve product observations with received times, effective dates
   when actually provided, raw flags and evidence hash. An observed status is
   not an observed valid-through interval. Before registration, specify the
   status-sampling/freshness model and distinguish it from venue guarantees.
   Unknown required intervals are not manufactured by extending October 27
   metadata backwards or forever. Public eligibility is not account permission.
6. Order model: quantity-specified, modelled full fills, not funds-specified
   live orders or limit orders. Proposed `lot_step=base_increment` uses a dated
   valid positive decimal. The documented quantity-specified market semantics
   support proposed `minimum_qty=0`, `minimum_notional_gross=0`; this is not a
   waiver of lot precision, affordability or future venue changes. Do not map
   a limit-order minimum into this market model.
7. Cash rounding: propose `quote_step=0.01 USD` as an explicitly conservative
   model convention per order: round total buy debit upward and sell credit
   downward after fees, as the accepted engine does. It is NOT inferred from
   the product price tick or certified fee/fill settlement precision. This
   convention needs adoption; no new rounding mapper was implemented. Compare
   identical conventions across arms and retain rounding loss separately.
8. Costs/capital: retain the original proposed USD1,000 alternative accounts,
   50/90 bps fee and 25 bps adverse price per side, plus the separate USD20/month
   overhead scenario. These are NOT newly adopted account facts. Gross, fees,
   adverse price, rounding and overhead must reconcile. No extra spread charge,
   cost-free headline, cumulative capital across alternatives or income forecast.
   Fees apply to adjusted gross, not to unadjusted reference notional. Shared
   sizing, net-sell funding, incidental rebalancing and carry stay as adopted.

Only two model premises: (1) one Coinbase USD spot venue, no FX or cash yield;
(2) a hypothetical full-fill execution model with the explicitly adopted timing,
cost, quantity and rounding conventions. None supplies missing observed facts.

## Source Check And Limits

Opened official Coinbase documentation on October 27, without calling any market
API or order endpoint:

- [Order reference](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/orders/create-new-order):
  price ticks are distinct from amount precision. Its Size section also retains
  legacy min/max wording, so it is not used alone to invent a current minimum.
- [Exchange changelog, June 2 and June 30, 2022](https://docs.cdp.coinbase.com/exchange/changes/changelog):
  quantity-specified market orders no longer have min/max size checks unless
  funds are specified; the retained minimum is for limit orders. Future changes
  must still be checked at protocol freeze.
- [Products reference](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-all-known-trading-pairs):
  product identifiers/increments/status are inputs, not a historical permission
  or cash settlement certificate.

Local evidence: saved metadata capture/comparison and archive audit are linked
in the adjacent brief. Recent archive: 21/24 complete full windows, 24/24 final
300-hour windows; older: 0/24 complete full windows, 22/24 final 300-hour windows.
These counts do not settle future coverage, identity or availability.

No market strategy or financial simulation was executed. The source-level timing
probe was synthetic only; no full suite or already accepted 129-test slice was
repeated. Hash bindings are in the adjacent input-contract bindings JSON.
Independent review should assess coherence, not approve implementation or
pretend these inputs establish profit, power, capacity or data authenticity.

## Next Boundary

Obtain one operator choice: adopt a delayed-execution comparison or retain the
idealized immediate next-open model with narrower claims. Until then neither
timing, rounding/cost proposal nor protocol is adopted by this supplement.
Remaining sampling/freshness, capital/cost/horizon and inferential choices still
need a complete registration and authorization; this note does not create one.
Any delay implementation must preserve existing APIs/results, use synthetic
fixtures, and stop at READY_FOR_INDEPENDENT_REVIEW. No new collector, scheduled
task, API refresh, deployment, account access or trading operation is implied.

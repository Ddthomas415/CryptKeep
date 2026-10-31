# ED-002: frozen-default signals across the declared 25

2026-10-27. Active role DIRECTOR. Risk HIGH (proposed financial model).
Acceptance: READY_FOR_INDEPENDENT_REVIEW. Proposal only: NOT FROZEN, not an
experiment registration, implementation permission or market-data authorization.

## Decision And Question

ED002-SCOPE-20261027: operator chose "Existing frozen strategies, 25 symbols
(Recommended)" when asked which comparison to prepare. That choice covers
design only. CTREND's wider universe is not adopted; its original draft and
review remain intact. Existing research, lower-price/cap hypotheses and the
25-symbol mandate are not retired.

Question: do any of the three existing frozen default signal families produce
positive net modelled USD profit and incremental value over the existing trend
candidate when the declared25 share one account? Primary objective is return,
not prediction accuracy or whichever risk metric later looks best.

This is a prospective portfolio extension, not an exact replay of the earlier
fixed-100-notional independent accounts. Signal parameters stay frozen; the
allocation policy below is new, proposed and must be adopted before use. No
claim that an old rejected strategy is rescued or that history becomes unseen.

## Universe, Signals And Costs

- Include the25 unique asset identities from tier1/tier2/watchlist in
  `config/candidate_universe.yaml`. Coinbase USD spot is the proposed single
  venue/common quote, consistent with the user's Coinbase focus. The config's
  USDT labels are not proof of a corresponding USD product or identity.
- Keep all25 in the design/report denominator. Resolve exact asset/product IDs
  with dated evidence before eligibility; no ticker-only matches, successor
  substitution (including MATIC/POL), current-rank selection or survivor deletion.
  Known ineligible instruments receive explicit reasons and unused allocation
  remains cash. Unknown required identity/status/precision is INCOMPLETE, not
  "ineligible". This does not assert that all25 can trade on Coinbase.
- Three separate accounts: breakout_default, ema_cross_default and
  mean_reversion_default, using exactly the configs in
  `research/multisymbol_baseline_v1/strategies.snapshot.json`. Existing
  `compute_signal` gets copied completed OHLCV through the decision close,
  last300 contiguous hourly bars, with evidence emission disabled. No parameter
  search, new stop stack, shorts, family blending or outcome-based selection.
- Initial capital C=USD1,000 per hypothetical account/cost case, flat holdings;
  no deposits, interest, leverage, transfers or FX. C is a proposed simulation
  parameter, not the operator's balance, loss tolerance or live allocation.
- Two proposed cost scenarios on every actual modelled order of every arm:
  fee50bps + adverse price adjustment25bps per side; fee90bps + adjustment25bps
  per side. The50bps value has dated account-level precedent, not certified
  current/product-specific applicability; all are explicitly scenario inputs.
  The25bps adjustment is an assumption, not a measured spread, calibrated bound,
  maker fill or capacity proof. No separate spread is deducted on top of it.
- Report economics both before overhead and after a separate USD20/month
  scenario (operator estimate, not invoice), prorated as 20*12*days/365. Do not
  remove it from the allocation wallet or charge it14times to one real account.
  Each trajectory is an alternative, not cumulative invested capital or income.

## Proposed Event-Triggered Allocation

This is the exact additional signal-to-target policy proposed for adoption:

1. At each hourly close, let q_i be actual modelled units, p_i contemporaneous
   close marks and N=cash+sum(q_i*p_i). If required marks or signal inputs are
   unavailable, report INCOMPLETE. An invalid signal is not silently HOLD.
2. Define S as held symbols with SELL, B as flat symbols with BUY, and H as
   held symbols not in S. BUY while held and SELL while flat are ignored, as in
   the earlier long-only engine. HOLD preserves that classification; it is not
   a latent permission to enter. No warm-up trades or inherited positions.
3. If S and B are empty, return None: no batch and no periodic rebalancing.
   Otherwise set h_i=q_i*p_i/N for H, and R=1-sum(h_i). Assign each symbol in B
   target min(1/25,R/len(B)); if B is empty this term is unused. Targets for S
   and all other symbols are zero. If only zero-budget buys remain, return None.
   Otherwise emit the complete vector. Use exact arithmetic for this mapping.
4. The accepted adapter executes that vector at the one next open. Net sells
   fund buys; its joint post-cost solution, lot/minimum rules and proportional
   cash resizing govern actual fills. Known exclusions are not redistributed.
   Failed/expired entries are not latched: next turn uses actual holdings and a
   new raw signal. An unavailable SELL also expires; there is no hidden retry.
5. Existing holdings' weights are measured at the decision close, not future
   opening prices. Therefore an emitted batch can resize a non-selling holding
   after a price gap and for joint costs. This policy preserves close weights,
   NOT exact held quantities at the execution open. Record incidental rebalancing
   trades/turnover explicitly. Claiming exact original trade-path parity would
   be false. No alternate hold/sizing policy is selected after outcomes.

The1/25 limit is an entry target, not a hard mark-to-market position cap: existing
holdings may drift above it. Equity-dependent sizing means higher fee scenarios
can follow different fill paths; no invalid blanket NAV-monotonicity assertion.
N=0 with zero cash/units is a terminal exhausted account, not a leveraged target;
retain NAV0 and zero subsequent returns/targets. Negative or inconsistent ledgers
are errors. This exhaustion behavior needs an explicit synthetic bridge test.

## Timing, Data And Carry

Activation A is the first Monday00:00UTC at least7days after a signed future
freeze, and only if the preregistered preflight is complete before A. Write A
and all hashes into the activation record before observations; no backdating.
Endpoint B=A+182days, exclusive. If preflight misses A, do not silently shift
the registered dates: leave unactivated and obtain a new dated activation.

Default signals require300 valid preceding hourly candles. The incumbent also
needs61 complete preceding UTC days. Warm-up is information, not traded capital
or confirmation outcomes. The first decision uses the completed hour ending A;
first fills are at A. Evaluate exactly4368hours through the close ending B.
At B compute the last close NAV but do not execute the pending next-open signal.

Future frozen prefixes must contain OHLCV provenance/row hashes plus separate
dated identity/status/precision/minimum inputs and availability timestamps. A
candle alone is not trading permission. Current product flags cannot be applied
retroactively. Public venue status is not private/account/geographic entitlement.
No new collector, scheduler, paid source or API request is authorized by this
design; collection feasibility/coverage must be demonstrated separately.

Use contiguous hourly frames. Known insufficient history after a documented
recent listing is signal-not-ready and stays cash; unexplained archive gaps are
missing evidence, not proof of no trading. Missing held marks/required permissions
make the affected account INCOMPLETE; no imputation, stale prices, zero/50%
recovery payout or later-open retry. Preserve stopped state and last valid NAV;
do not count it as a profitable completed path. Report all25 consideration rows.

At A+91days retain the same cash/units/basis/pending state and preceding-close NAV
anchor; no split liquidation, reset, deposits or parameter changes. Midpoint
checks are collection/accounting health only, not interim return scoring or
selection. Report both halves only after B. No automatic extension or early win.

## Controls And Economic Screen

Every arm uses the accepted shared-account engine, same C, timestamps, modelled
costs, metadata and endpoint handling. Unique arms per scenario: three default
families, cash, BTC buy-and-hold, fixed-unit25/25/50 BTC/ETH/cash buy-and-hold,
and the incumbent28-day BTC/ETH volatility-scaled trend. Seven arms times two
cost scenarios =14alternative trajectories; not25independent wallets summed.

The incumbent retains the source target rule: SundayUTC close only, positive
28-day return, per-asset weight(1/2)*min(1,0.50/annualised30-day population
volatility), otherwise0, same first Sunday decision before A. Use complete UTC
daily closes/returns, sqrt365 annualisation. A zero required volatility is
undefined and INCOMPLETE; do not invent a weight. No band overlay or retuning.
Its source target semantics are in
`docs/research/btc_eth_stress_test_20261009/stress_btc_eth.py`, function `target`;
do not import
that executable study or run its historical grids. A pure future bridge needs
synthetic parity proof. This is not a new historical incumbent rerun.

Controls buy at A and pay their real modelled entry costs; no post-fill NAV
rebasing. The fixed-unit mix is not weekly rebalanced or fitted to realized
exposure. Differences in average exposure are reported, not hidden as matched
risk. Primary endpoint is same-time marked NAV; optional last-close liquidation
is a distinct modelled column retaining dust, unsellable units and labels. Never
deduct synthetic terminal costs from the primary marked path twice.
If an intended benchmark asset cannot be bought at A (permission/open/minimum
or precision failure), the relevant comparison is INCOMPLETE, even if an engine
cash-only fallback is mechanically COMPLETE. Do not relabel uninvested cash as
successful BTC hold or the declared mix. Normal lot dust is disclosed separately.

For each family, report net dollars, fees/price adjustment/rounding, realized
and unrealized PnL, overhead-adjusted dollars, drawdown, time/exposure, turnover,
worst day/trade, completed cycles, exclusions and coverage; compare all controls.
Do not annualise182days into an expected income projection.

A provisional return-screen candidate must have a COMPLETE182-day path, at
least30closed symbol-position cycles (not30independent statistical samples),
positive primary net profit after overhead, and primary marked NAV above both
BTC hold and the incumbent. It must also have a positive adjusted inference
bound below and positive overhead-adjusted profit/advantage over the incumbent
in the higher-fee scenario. Otherwise report failed specified screen or
INCONCLUSIVE for insufficient cycles/inference. INCOMPLETE data is never a
negative economic verdict. No gate grants paper/live eligibility or risk approval.
Maximum drawdown and risk tolerance require a later explicit operator decision;
this is return screening only, not a validated risk mandate.

## Proposed Statistical Method And Trial Accounting

Primary contrasts are the three default families minus the incumbent, at the
50bps scenario. For each, effect is final marked NAV difference in USD from equal
C. Calculate182paired UTC daily simple-return rows including entry costs in the
first day. Resample seven-day circular calendar blocks of the joint all-arm
daily return panel, uniformly by block start, concatenate and truncate to182days;
20,000replicates, seed20261027. Recompound each arm's resampled returns from C
and compare terminal wealth. This resamples observed modelled portfolio returns,
not market bars or a newly executable simulated trade path.

One-sided lower empirical quantile1/60 (Bonferroni0.05/3), inverted-CDF order
statistic ceil(20000/60), must exceed0. This is a proposed approximate bootstrap
screen, not a guaranteed95% interval or probability of profitability. Report
14/28-day block sensitivities without selecting a winner/method by their results.
Before freeze, require synthetic null/known-effect/serial-dependence fixtures,
cross-arm pairing and recomposition checks plus independent method review. If
that proof fails, do not manufacture an inferential PASS or quietly replace the
method after observing the market period. Statistical validation is not yet done.

Record three new portfolio policies, two cost cases,75considered symbol-family
exposures and150symbol-family-cost exposures, distinguishing considered from
actually evaluated. Record all14trajectories and all diagnostic methods; these
counts are not an effective independent N. No DSR value is asserted from the
incomplete historical selection ledger. No per-symbol winner selection or
post-outcome family blending. Update coverage only when authorized evidence
exists; design approval alone does not change research statuses.

## Required Next Proof And Boundaries

Proposed single next implementation: a pure OHLCV/signal-to-target bridge and
same-engine incumbent adapter, with synthetic fixtures only, reusing the reviewed
ledger. The shared adapter currently supplies only open/close history, so do not
pretend its callback already contains high/low/volume. The bridge must supply
timestamp-bounded copied OHLCV from frozen inputs, preserve300-bar semantics,
and never access future rows. Freeze bridge/source/environment/data identities
only after independent review and explicit adoption of this proposed policy.

Required fixtures: simultaneous entries and zero-budget refusals, ignored
BUY-while-held/SELL-while-flat, all-HOLD no rebalance, incidental opening-gap
rebalance disclosure, no latched failed intent, OHLCV-prefix/future perturbation,
known-new-listing versus unknown gap, incumbent weekly timing/volatility, full
versus split equality and the inference cases above. Existing102-case accounting
proof is preserved, not a substitute for these unsupported-interface tests.

Two explicit modelling assumptions: one Coinbase USD spot venue/no FX or cash
yield; full fills at the declared adverse price adjustment with caller-supplied
dated eligibility. Neither is venue execution evidence. Prospective182days is
a proposed horizon, not a demonstrated adequately powered sample. No income
target, account access, new job, infrastructure purchase or trading operation
is inferred. Raw data, previous verdicts and CTREND originals remain unchanged.

Source/strategy identity verification is in the adjacent
`ed002_defaults25_design_bindings_20261027.json`. This design has not opened
market datasets, evaluated signals, installed dependencies or rerun old studies.

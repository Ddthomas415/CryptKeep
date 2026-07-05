# Short-Market Strategy Research Spec - 2026-06-19

Status: ACCEPTED

Acceptance scope:
- This spec is accepted as the research and governance path for short-market
  strategy work.
- It does not authorize short orders, derivatives execution, margin, leverage,
  promotion-gate changes, or active campaign changes.
- The requested feasibility audit was completed in
  `docs/checkpoints/short_context_data_feasibility_audit_2026_06_19.md`.

## Purpose

Define a controlled research path for short-market strategies without changing
the current long/flat paper campaigns, promotion gates, execution code, or
operator workflow.

This spec exists because short exposure is not a parameter tweak to
`sma_200_trend`. It introduces separate instrument, margin, liquidation,
funding, borrow, venue, compliance, and fail-safe requirements.

## Evidence Basis

SHOWN:
- `docs/strategies/es_daily_trend_v1.md` defines the current target strategy as
  long/flat only and says short signals are ignored in v1.
- `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` already
  tracks short-market strategy research as Priority 12.
- `docs/checkpoints/infrastructure_activation_audit_2026_06_03.md` classifies
  `funding_extreme`, `open_interest_shift`, and `order_book_imbalance` as
  research-only or unsafe to enable without data-plumbing and risk proof.
- `services/strategies/funding_extreme.py`,
  `services/strategies/open_interest_shift.py`, and
  `services/strategies/order_book_imbalance.py` exist as strategy/context
  modules, but they are not the active paper campaign authority.
- `services/market_data/alternative_data.py` and
  `services/market_data/market_intelligence.py` contain funding, open-interest,
  and liquidation-context scaffolding.

UNVERIFIED:
- Whether the operator's current exchange accounts, jurisdiction, API
  permissions, and product access allow margin, shorting, or perpetual futures.
- Whether any derivatives venue is legally available to the operator.
- Whether funding, open-interest, liquidation, and order-book data are complete
  enough for production-grade decisions.
- Whether any short-side strategy is profitable after fees, funding, borrow
  costs, slippage, and liquidation constraints.

## Non-Goals

- Do not enable short orders.
- Do not enable margin, borrow, leverage, or derivatives execution.
- Do not modify the active `es_daily_trend_v1`, `ema_cross_default`,
  `breakout_default`, or `pullback_recovery_default` paper campaigns.
- Do not change promotion gates.
- Do not treat a `sell` signal as permission to open a short position.
- Do not add live credentials, public ports, remote deployment changes, or
  unattended background jobs.

## Instrument Tracks

### Track A - Spot Margin Short Research

Scope:
- Research-only until venue/account support and borrow mechanics are proven.
- Model borrow availability, borrow rate, locate failure, forced buy-in, and
  max borrow exposure before any paper simulation claims realism.

Required proof before paper simulation:
- Venue/account eligibility documented.
- Borrow cost model documented.
- Symbol-level shortability and borrow availability captured with provenance.
- Paper engine can distinguish "sell to exit long" from "sell to open short."

### Track B - Crypto Perpetual Futures Research

Scope:
- Research/testnet-only until separate compliance, account, margin, funding,
  and liquidation reviews are accepted.
- Initial leverage assumption is 1x unless a later high-risk review explicitly
  accepts a different limit.

Required proof before paper simulation:
- Venue eligibility and API permissions documented.
- Contract specs, funding schedule, tick size, lot size, maintenance margin,
  and liquidation behavior captured with provenance.
- Reduce-only exit behavior is supported and tested.
- Margin accounting and liquidation buffer are modeled in the paper engine.

### Track C - Traditional Futures

Scope:
- Later workstream only.
- Requires broker/FCM integration, contract lifecycle handling, expiry/roll
  logic, exchange calendars, margin rules, and a separate operational runbook.

Required proof before any implementation:
- Broker/FCM selection.
- Contract specs and expiry/roll requirements.
- Paper/replay data source.
- Separate risk and compliance review.

## Candidate Strategy Families

Research candidates:
- Trend breakdown short: enter only after a confirmed support break with trend
  and volatility filters.
- Failed breakout / bull trap: short after a breakout above resistance fails
  and price closes back inside the prior range.
- Funding extreme contrarian: short only when funding indicates crowded longs
  and price action confirms weakness.
- Open interest continuation: short when open interest rises while price falls,
  suggesting new short positioning or forced long exits.
- Order-book imbalance continuation: short only when persistent ask pressure
  aligns with downside price movement and spread/depth are acceptable.
- Intraday session breakdown: use 1m/5m/15m context, VWAP, prior day levels,
  and time-of-day labels as read-only features before any order path exists.

Candidate selection rule:
- Start with read-only signal logging and replay analysis. Do not route any
  candidate to the paper engine until its data inputs and failure modes are
  independently reviewed.

## Data Requirements

Minimum read-only context:
- OHLCV at 1m, 5m, 15m, 1h, and 1d where available.
- Bid/ask spread and depth snapshots.
- Funding rate history and next funding timestamp for perpetual candidates.
- Open interest snapshots and history.
- Liquidation-context estimates or explicitly documented absence of reliable
  liquidation data.
- Fee, funding, borrow, and slippage assumptions.
- Venue/product metadata: min size, tick size, lot size, margin mode, and
  reduce-only support where applicable.

Provenance requirements:
- Every row must include source, venue, symbol, timestamp, collection time, and
  whether the value came from live API, testnet, replay, or fixture data.
- Missing values must be explicit. Silent zero defaults are not acceptable for
  funding, open interest, margin, liquidation, or borrow costs.

## Risk Controls

Required before any paper short simulation:
- Strategy ID is separate from long/flat strategies.
- State directory is separate from canonical campaigns.
- Short intent is represented explicitly, not inferred from `sell`.
- Paper accounting tracks realized PnL, unrealized PnL, fees, funding, borrow
  costs, margin used, liquidation buffer, and max adverse excursion.
- Daily loss halt is defined for short exposure.
- Kill switch behavior is documented for open short positions.
- Position reconciliation distinguishes long, flat, and short.
- Exits are reduce-only where the venue/instrument supports it.
- Max notional and max position count are defined.
- No fail-open behavior when risk inputs are missing.

Initial defaults:
- Leverage: 1x for any derivatives paper simulation unless a separate review
  accepts otherwise.
- Missing funding/borrow/margin data: block strategy evaluation.
- Missing spread/depth: allow read-only logging, block simulated execution.
- Missing reduce-only proof: block paper execution for derivatives shorts.

## Stage Gates

### Stage 0 - Read-Only Data Quality

Objective:
- Prove data collection works without generating signals or orders.

Exit criteria:
- At least 5 trading days of read-only context for target symbols.
- Provenance fields are complete.
- Missing-data rates are reported.
- No credentials with trade permission are required.

### Stage 1 - Signal-Only Replay

Objective:
- Determine whether short-side signals identify downside moves early enough.

Exit criteria:
- Replay/backtest baseline with fees, funding/borrow assumptions, spread, and
  slippage.
- False-positive analysis across uptrend, downtrend, chop, and high-volatility
  regimes.
- Strategy-specific stop and invalidation rules documented.

### Stage 2 - Isolated Paper Simulation

Objective:
- Prove accounting and risk controls for short intent without touching active
  campaigns.

Exit criteria:
- Separate `CBP_STATE_DIR`.
- Separate strategy ID.
- No canonical gate contamination.
- Open short, reduce-only close, halt, and kill-switch cases covered by
  targeted tests or fixtures.
- Monitor summary distinguishes short exposure from long exits.

### Stage 3 - Shadow Candidate

Objective:
- Log short-side signals against live market data without orders.

Exit criteria:
- 20+ trading days of signal logs.
- Every signal can be replayed against contemporaneous market context.
- Operator-facing scorecard includes hit rate, adverse excursion, missed move,
  fees/funding/borrow estimate, and risk-control status.

### Stage 4 - Future Execution Review

Objective:
- Decide whether any short-side strategy is eligible for controlled execution.

Exit criteria:
- Separate high-risk review.
- Compliance note accepted.
- Venue/account permissions verified.
- Risk controls tested.
- Operator runbook accepted.

## Stop Conditions

Stop short-side work if any of these are true:
- Venue/account eligibility is unknown.
- Required data has silent defaults or unexplained gaps.
- Strategy cannot distinguish sell-to-exit from sell-to-open-short.
- Risk controls fail open when margin, funding, borrow, or liquidation data is
  missing.
- Paper simulation would write into canonical long/flat campaign state.
- The work requires live credentials or trade permissions before Stage 4.

## Completed Follow-Through

The read-only feasibility audit for existing short/context modules is complete:
- `funding_extreme`
- `open_interest_shift`
- `order_book_imbalance`
- market-data funding/open-interest/liquidation scaffolding

The audit selected the read-only crypto-edge collector as the safe base and
identified the missing collectors, provenance fields, storage rows, and replay
boundaries needed before short-side signal replay can be trusted.

## Current Next Action

Continue only from accepted read-only evidence:
- use deterministic sample data or accepted public row families for any replay
  prototype;
- use the OKX read-only derivatives source decision in
  `docs/research/crypto_edge_source_decision.md` as the default collection
  direction for funding, open-interest, and basis rows;
- keep replay fixture-only unless `make check-short-context-readiness` reports
  `live_public_replay_ready=true`;
- keep all sell-to-open-short intent explicit and separate from sell-to-exit;
- do not route any short/context signal to paper or execution without a
  separate high-risk review.

Acceptance state:
- ACCEPTED

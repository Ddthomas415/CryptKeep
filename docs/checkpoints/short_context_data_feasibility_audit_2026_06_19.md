# Short Context Data Feasibility Audit - 2026-06-19

Status: READY_FOR_INDEPENDENT_REVIEW

## Scope

Read-only audit of the repo surfaces needed before any short-side signal replay
can be trusted.

This audit does not enable shorting, derivatives execution, paper short
simulation, margin, leverage, new collectors, or promotion-gate behavior.

## Evidence Basis

SHOWN:
- `services/strategies/funding_extreme.py` emits `sell` when funding indicates
  crowded longs and `buy` when funding indicates crowded shorts.
- `services/strategies/open_interest_shift.py` emits `sell` when open interest
  rises while price falls.
- `services/strategies/order_book_imbalance.py` emits `sell` when order-book
  imbalance crosses the configured sell threshold.
- `services/strategies/presets.py` defines `funding_extreme_default` and
  `open_interest_shift_default`.
- `services/strategies/config_tools.py` accepts `funding_extreme` and
  `open_interest_shift`.
- `services/strategies/strategy_registry.py` does not route
  `funding_extreme`, `open_interest_shift`, or `order_book_imbalance`.
- `services/analytics/crypto_edge_collector.py` is explicitly read-only:
  collected payloads include `research_only=True` and
  `execution_enabled=False`.
- `scripts/collect_live_crypto_edge_snapshot.py` stores read-only funding,
  basis, and quote snapshots through `storage/crypto_edge_store_sqlite.py`.
- `sample_data/crypto_edges/live_collector_plan.json` includes one funding
  row, one basis row, and quote rows, but no open-interest, liquidation, or
  order-book-depth rows.
- `services/market_data/market_intelligence.py` has open-interest collection
  and liquidation scaffolding, but liquidation rows explicitly say
  `scaffold_only_no_live_liquidation_feed`.
- `services/market_data/order_book_intelligence.py` can fetch order-book
  snapshots and compute imbalance, spread, bid notional, and ask notional.

UNVERIFIED:
- Any venue/account eligibility for shorting, margin, or perpetual futures.
- Whether Binance/other derivatives data is available to the operator under
  current jurisdiction and account constraints.
- Whether collected funding, open-interest, liquidation, or order-book data is
  stable enough for strategy decisions.
- Whether any of the context signals improve strategy performance after fees,
  funding, borrow, slippage, and false positives.

## Findings

### F1 - Safe Read-Only Funding/Basis/Quote Path Exists

Severity: MEDIUM

SHOWN:
- `services/analytics/crypto_edge_collector.py` collects public funding, basis,
  and quote snapshots.
- Its returned object marks `research_only=True` and `execution_enabled=False`.
- `scripts/collect_live_crypto_edge_snapshot.py` persists only research rows.
- Tests cover successful collection and unsupported funding handling.

Impact:
- This is the safest existing foundation for Stage 0 short/context data
  collection.
- It should be treated as the canonical read-only collector path for funding,
  basis, and quotes until a better provenance model exists.

Constraint:
- It does not collect open interest, liquidation context, full depth snapshots,
  or order-book imbalance rows.

### F2 - Strategy Context Modules Are Not Runtime-Routable

Severity: HIGH

SHOWN:
- `strategy_registry.py` routes OHLCV strategies such as `ema_cross`,
  `breakout_donchian`, `pullback_recovery`, and `sma_200_trend`.
- It does not route `funding_extreme`, `open_interest_shift`, or
  `order_book_imbalance`.
- `config_tools.py` and `presets.py` know about `funding_extreme` and
  `open_interest_shift`, but that does not make them executable through the
  active strategy registry.

Impact:
- The repo has context-signal functions, not an accepted replay/runtime path
  for those strategies.
- A future replay implementation must add an explicit context-signal adapter
  instead of forcing these into the OHLCV registry.

Required next proof:
- A signal-only replay harness that accepts timestamped context rows and emits
  explicit `long_exit`, `short_entry`, `short_exit`, or `hold` intents.

### F3 - Market Intelligence Path Is Useful But Not Safe Enough

Severity: HIGH

SHOWN:
- `market_intelligence.py` can fetch open interest through ccxt and can build
  a combined funding/open-interest/liquidation/social snapshot.
- It silently skips per-symbol failures.
- It stores previous open-interest state under
  `.cbp_state/runtime/market_intelligence` instead of an explicit collector
  state passed by the caller.
- Liquidation output is scaffold-only with `None` cluster values while the
  wrapper still returns `ok=True`.

Impact:
- This path is useful for exploration but not sufficient as-is for trusted
  short-side replay.
- Silent skips and scaffold `ok=True` outputs could hide missing risk inputs.

Required next proof:
- Per-symbol `checks` rows.
- Explicit source/provenance fields.
- Caller-selected state directory.
- `ok=False` or `data_status=scaffold_only` for liquidation rows that do not
  represent live data.

### F4 - Order-Book Intelligence Needs Provenance And Failure Rows

Severity: MEDIUM

SHOWN:
- `order_book_intelligence.py` computes best bid, best ask, spread, bid
  notional, ask notional, imbalance, and pressure.
- It returns rows only when the fetch succeeds.
- `scan_order_book_pressure()` drops failed symbols instead of preserving a
  check row for each attempted symbol.

Impact:
- Good enough for exploratory dashboard/ranking use.
- Not good enough for replay evidence because missing symbols are invisible.

Required next proof:
- Per-symbol checks with `ok`, `reason`, venue, symbol, timestamp, depth, and
  source.
- Stored depth/notional/imbalance rows in the research store.

### F5 - Storage Covers Funding/Basis/Quotes Only

Severity: MEDIUM

SHOWN:
- `storage/crypto_edge_store_sqlite.py` defines tables for funding snapshots,
  basis snapshots, and quote snapshots.
- It does not define open-interest, liquidation, or order-book-depth tables.
- Its numeric conversion helper can default malformed numeric values to `0.0`.

Impact:
- Existing storage can support funding/basis/quote research.
- It cannot yet support complete short-context replay without additional
  storage tables or a generic context-event table.

Required next proof:
- Storage schema for open interest and order-book depth/imbalance.
- Explicit missing/invalid handling that rejects required numeric fields rather
  than silently storing zero.

## Recommended Canonical Path

Use `services/analytics/crypto_edge_collector.py` as the base for Stage 0
read-only context collection.

Do not use `services/market_data/market_intelligence.py` as the authority until
its silent skips, fixed state path, scaffold liquidation rows, and provenance
gaps are fixed or wrapped.

## Required Implementation Tasks Before Signal Replay

1. Extend the read-only collector plan to support open-interest and order-book
   depth/imbalance rows with per-symbol checks.
2. Add storage for open-interest and order-book rows, or add a versioned generic
   context-event table.
3. Add explicit data-status fields:
   `live_public`, `testnet_public`, `fixture`, `missing`, `unsupported`, and
   `scaffold_only`.
4. Reject missing required numeric fields for funding, open interest, spread,
   depth, and imbalance instead of silently converting them to zero.
5. Add a context-signal replay harness that does not touch the active OHLCV
   strategy registry or paper execution path.
6. Make short intent explicit. `sell` alone must not mean open-short.

## Stop Conditions

Stop any implementation if:
- A context signal would be routed directly to order execution.
- Missing funding, open-interest, liquidation, spread, or depth values are
  silently treated as neutral.
- Collector state writes into canonical long/flat campaign state without an
  explicit operator-selected state path.
- The implementation requires trade-enabled API credentials.
- The implementation requires a venue/jurisdiction assumption that has not been
  reviewed.

## Next Action

The smallest useful next implementation is still read-only:
- add open-interest and order-book rows to the existing crypto-edge collector
  and store, with per-symbol checks and explicit provenance.

That implementation would be high risk because it expands research data
collection for future financial strategy decisions. It must stop at
`READY_FOR_INDEPENDENT_REVIEW`.

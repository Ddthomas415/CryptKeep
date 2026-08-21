# Canonical ExecDB PnL Classification

Date: 2026-08-21

## Scope

This document classifies `services/journal/canonical_execdb.py` realized-PnL
semantics. It is a classification record only; it does not change fill
accounting, risk gates, promotion gates, live execution, or paper evidence.

## Finding

SHOWN from current source:

- `CanonicalJournal.record_fill()` stores `fee_usd` and `realized_pnl_usd` as
  separate columns in `canonical_fills`.
- `CanonicalJournal.record_fill()` does not subtract fees from
  `realized_pnl_usd`; it stores the value supplied by the caller.
- `CanonicalFillSink.on_fill()` passes any exchange-provided
  `realized_pnl_usd` through to the canonical journal unchanged, while storing
  `fee_usd` separately.
- If a fill has no exchange-provided `realized_pnl_usd`, `CanonicalFillSink`
  records `NULL` in `canonical_fills.realized_pnl_usd`; the later local PnL
  fallback is used for `risk_daily`, not backfilled into the canonical row.
- `LivePositionStore.apply_fill()` uses weighted-average spot cost basis and
  computes sell realized PnL as `(sell_price - avg_price) * sell_qty`, with no
  fee parameter.
- `RiskDailyDB.apply_fill_once()` receives that gross realized PnL and the fee
  separately; `risk_daily.snapshot()["pnl"]` derives net PnL by subtracting
  fees.

## Classification

| Surface | Classification | Semantics |
|---|---|---|
| `canonical_fills.realized_pnl_usd` | `source_supplied_realized_pnl_or_null` | Exchange-provided values are stored as supplied; fills without source-provided PnL store `NULL`. |
| `canonical_fills.fee_usd` | `separate_fee_column` | Fee is stored separately and must be subtracted by consumers that need net PnL. |
| `risk_daily.realized_pnl` | `gross_realized_pnl_when_locally_computed` | Gross realized PnL, excluding fees, when produced by `LivePositionStore`; source-provided values are passed through as supplied. |
| `risk_daily.snapshot()["pnl"]` | `net_realized_after_fees` | Derived net value: `realized_pnl_usd - fees_usd`. |

## Rules

- Do not treat `canonical_fills.realized_pnl_usd` as a complete PnL source:
  missing source PnL remains `NULL` in the canonical row even when `risk_daily`
  computes a local fallback.
- Do not treat source-provided `canonical_fills.realized_pnl_usd` as net-of-fees
  unless a source-specific fill contract explicitly proves the exchange-provided
  value is already net.
- Consumers that need net PnL must use an explicitly net field or subtract
  `fee_usd` from a proven gross field.
- Do not compare canonical ExecDB realized PnL directly with paper-fill
  `pnl_usd_semantics=net_of_fees` without normalizing.
- If canonical ExecDB begins storing a net realized field, update this
  classification and its executable guard in the same change.

## Executable Guard

`tests/test_canonical_execdb_pnl_classification.py` pins that:

- the classification document remains linked from architecture indexes;
- `CanonicalFillSink` stores `NULL` in `canonical_fills.realized_pnl_usd` when
  source PnL is missing;
- the canonical fee remains in `canonical_fills.fee_usd`;
- `risk_daily.realized_pnl` receives the locally computed gross fallback; and
- `risk_daily.snapshot()["pnl"]` remains the downstream net value.

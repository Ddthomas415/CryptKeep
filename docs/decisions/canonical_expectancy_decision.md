# Canonical Expectancy Decision

**Status:** RESOLVED - primary paper-history expectancy is authoritative for
paper promotion, 2026-07-12.

## Decision

Paper promotion expectancy must come from provenance-qualified paper-history
metrics, specifically the per-closed-trade net expectancy produced by the paper
evidence qualification path.

The JSONL `pnl_usd` fallback is not authoritative for paper promotion because it
uses fill-level records and can include opening legs with no realized PnL. When
paper-history qualification is unavailable, the gate reports expectancy as
unknown instead of computing a per-fill fallback average.

## Boundary

`scripts/check_promotion_gates.py::_paper_gate_trade_metrics()` returns
`expectancy_ok=None` and `expectancy_value=None` for the JSONL fallback path.

The lower-level `_check_expectancy()` helper remains available for legacy and
non-paper contexts that still explicitly use fill-level PnL. This decision only
changes paper-promotion authority.

## Rationale

A fallback is an authority transition. Switching from per-closed-trade
paper-history expectancy to JSONL per-fill expectancy changes denominator and
evidence source. The fail-closed behavior is to require qualified paper-history
metrics before using expectancy as a paper-promotion gate.

## Executable Guard

`tests/test_canonical_expectancy_decision_guard.py` pins the authoritative
paper-history source, JSONL fallback boundary, legacy helper boundary, authority
rationale, and backlog link so paper-promotion expectancy cannot silently drift
back to a per-fill fallback contract.

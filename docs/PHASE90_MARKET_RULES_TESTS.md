# Phase 90 — Market rules tests (no network)

Adds pytest coverage for:
- cache insert/get/freshness
- validation blocks: inactive, min_notional, min_qty, qty_step
- prereq fail-closed when cache empty
- prereq pass when cache fresh

Run:
  pytest -q

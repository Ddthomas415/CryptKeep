# Product Surface Triage

Date: 2026-07-03

## Current Decision

CryptKeep remains in lab-mode concentration until expectancy is proven.

## Retain Now

These directly support evidence, safety, recovery, or operator decisions:

- paper evidence collection
- promotion gates
- shadow would-be-fill evidence
- archive-first backtesting
- crypto-edge data collection
- operator status/alerting
- backup/restore and recovery proof

## Defer

These remain valid long-term ambitions but should not consume near-term
engineering unless they support the retained list above:

- cross-platform desktop packaging
- public onboarding/product polish
- non-operator-critical dashboard pages
- broad multi-exchange product claims
- automated strategy selection beyond read-only proposal/advisory mode

## Decision Rule

If a product-surface task does not improve evidence velocity, profitability
discovery, cost measurement, safety, recovery, or operator wake-up quality, it
should be deferred until a strategy has proven expectancy after costs.

Related scope policy: `docs/PROJECT_IDENTITY_AND_SCOPE.md`.

## Executable Guard

`tests/test_product_surface_triage.py` pins the current lab-mode decision, the
retain/defer lists, the decision-rule terms, and the README root-boundary
summary so product-surface drift is visible during CI.

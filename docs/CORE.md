# CryptKeep Operational Core

Date: 2026-07-03

## Purpose

Define the modules that belong to the current paper/research/shadow path and
the policy for everything outside that core.

## Current Core

These surfaces are part of the current supported operating path:

- `services/control/` - stage machine, gates, retirement/progress helpers.
- `services/strategies/` - strategy implementations and registry.
- `services/execution/` - paper engine, runner, execution adapters, and live
  execution boundaries.
- `services/analytics/` - paper evidence, reports, monitors, and advisory
  summaries.
- `services/risk/` - market quality, risk gates, kill conditions.
- `services/admin/` - operator stop/resume/status surfaces.
- `services/security/` - auth, runtime guard, exchange factory.
- `services/signals/` - candidate layer, currently read-only/advisory unless
  explicitly enabled.
- `services/market_data/` - supported market-data utilities and research
  rankers.
- `storage/` - canonical SQLite stores.
- `scripts/` - operator and research entrypoints.
- `dashboard/` - operator visibility and admin UI.
- `configs/` and `config/` - campaign, strategy, and runtime configuration.

## Quarantine Policy

Do not delete or move broad surfaces in one sweep. For each non-core or unclear
surface, choose one explicit state first:

- `core` - used by current paper/research/shadow path.
- `research_only` - allowed for read-only research, not stage promotion.
- `advisory_only` - may inform humans, cannot gate orders or promotion.
- `compatibility` - kept only for legacy import compatibility.
- `retired` - must not be reintroduced without an accepted architecture
  decision.
- `sidecar` - external or companion workspace, not part of root install/run/test
  baseline.

## Rule

New functionality should land in the core only when it directly improves one of:

- evidence velocity
- profitability discovery
- cost measurement
- safety
- recovery
- operator wake-up quality

Otherwise it belongs in research/advisory scope or should be deferred.

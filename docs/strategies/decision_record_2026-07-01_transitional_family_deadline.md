# Transitional Family Deadline Extension - 2026-07-01

## Decision

Extend the transitional service-family removal deadline from 2026-07-01 to
2026-08-01.

## Reason

SHOWN:
- CI failed on 2026-07-01 because `tests/test_deprecation_deadline.py` reached
  the removal deadline while `services/strategy` and `services/paper` still
  contained Python files.
- `docs/architecture/transitional_service_families.md` records
  `services/paper` as a frozen compatibility layer over canonical safety,
  storage, and paper-engine components.
- `docs/architecture/transitional_service_families.md` records
  `services/strategy` as a frozen internal compatibility island, not as an
  approved ownership target.
- `tests/test_startup_guard_regression.py` still verifies
  `services/strategy/startup_guard.py`.
- `tests/test_paper_main_mode_gate.py` and
  `tests/test_placeholder_recovery_phase3.py` still cover `services/paper`.

Deleting the directories in the Hetzner preflight PR would mix storage-host
readiness work with a broader compatibility migration and would risk removing
covered behavior without a focused migration proof.

## Consequence

The repo keeps the transitional families frozen. No new imports or feature work
should target them. The new 2026-08-01 deadline is a short extension for a
separate migration/removal PR, not an acceptance that the compatibility layer is
permanent.

## Status Update - 2026-07-01

The extended deadline was satisfied early. The tracked compatibility families
from this migration set were retired, and `tests/test_deprecation_deadline.py`
now guards against reintroduction through `RETIRED_FAMILIES`.

## Verification Required

Completed before 2026-08-01:
- migrated or retired remaining `services/paper` test callers
- migrated or retired `services/strategy/startup_guard.py`
- moved strategy runtime ownership to `services/execution/strategy_runner.py`
- retired `services/strategy_runner`
- marked `services/storage` retired after no tracked source remained
- updated architecture and retired-family guard docs

## Acceptance State

Acceptance state: ACCEPTED

Review reference:
- Independently reviewed and accepted by the human operator on 2026-07-01.

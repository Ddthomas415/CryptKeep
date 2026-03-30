# Remaining Tasks

This file is a lightweight index only.

## Current state
Production hardening is not complete.

## Canonical blocker list
See:

- docs/checkpoints/launch_blockers_root_runtime.md

## Interpretation
The critical path is:

1. freeze launch scope
2. configure one sandbox venue
3. prove private authenticated connectivity
4. prove private lifecycle runtime flow
5. resolve live lifecycle authority gap if required by the frozen launch path
6. collapse live-mode source of truth if required by the frozen launch path

## Notes
Do not mix:
- launch blockers
- conditional broader-scope controls
- non-blocking architectural debt

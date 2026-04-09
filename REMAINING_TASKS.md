# Remaining Tasks

This file is a lightweight index only.

## Current state
The frozen canonical root-runtime path is hardened enough on the repo side.
The remaining critical path is external environment proof or a human launch decision.

## Canonical blocker list
See:

- docs/checkpoints/launch_blockers_root_runtime.md

## Interpretation
The critical path is:

1. use the frozen canonical root-runtime path recorded in `docs/checkpoints/root_runtime_scope_record.md`
2. obtain one reachable supported sandbox/testnet venue from the operator environment
3. prove private lifecycle runtime flow on that reachable venue
4. or make an explicit human launch decision accepting the current environment-blocked exception

Already completed on the frozen canonical path:
- private authenticated connectivity for one supported venue
- singular live-mode source of truth
- boundary-governed live lifecycle authority
- hidden-default fencing for the chosen launch path

## Notes
Do not mix:
- launch blockers
- conditional broader-scope controls
- non-blocking architectural debt

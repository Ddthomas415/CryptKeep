# Runtime Stub Disposition

Date: 2026-07-04

## Scope

This records the disposition of two TODO-only runtime placeholder modules:

- `services/runtime/run_mode.py`
- `services/runtime/bot_process.py`

## Finding

SHOWN:

- Both files contained only a phase comment and `TODO: implement`.
- Repository import scan found no source importers for either module.

Command:

```bash
rg -n "runtime\.run_mode|runtime\.bot_process|services/runtime/run_mode|services/runtime/bot_process" \
  services scripts tests docs Makefile pyproject.toml -g '*.*'
```

Result:

- SHOWN: matches were documentation/audit references only.

## Decision

Delete the placeholder modules.

## Why

Keeping empty runtime modules makes the repo look like it has a unified run-mode
or bot-process authority when it does not. The current supported process
surfaces are documented elsewhere:

- `docs/PROCESS_CONTROL.md`
- `docs/SERVICES_SUPERVISOR.md`
- `docs/PAPER_CAMPAIGN_RECOVERY.md`
- `services/control/managed_component.py`

## Implementation Consequence

Future work that needs a unified run mode or process authority must start from
the documented managed-component/control surfaces and include a fresh
architecture decision. The deleted module names should not be reintroduced as
empty compatibility placeholders.

# Runtime Package

This package contains runtime helpers that still have supported callers.

- `process_supervisor.py` supports the compatibility bot-runner path through
  `scripts/compat/run_bot_runner.py`.
- `startup_hardening_audit.py` audits startup/runtime hardening state.
- `dynamic_symbol_selector.py` remains a runtime helper for managed symbol
  selection.

Deleted placeholder modules:

- `services/runtime/run_mode.py`
- `services/runtime/bot_process.py`

Those names were TODO-only stubs and must not be reintroduced as empty
compatibility placeholders. If future work needs unified run-mode or
bot-process authority, start from `docs/architecture/runtime_stub_disposition.md`
and the managed-component/process-control surfaces instead of recreating these
stubs.

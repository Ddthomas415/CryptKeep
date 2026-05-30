# Conformance Tests

Use targeted verification first. Expand only when the local risk justifies it.

## Root baseline slices
- Auth-facing regression slice:
  - `./.venv/bin/python -m pytest -q tests/test_auth_gate.py tests/test_auth_runtime_guard.py tests/test_auth_capabilities.py`
- Onboarding and root dependency contract:
  - `./.venv/bin/python -m pytest -q tests/test_onboarding_collector_docs.py tests/test_root_dependency_contract.py tests/test_repo_hook_source_of_truth.py`
- Validation lane wiring:
  - `./.venv/bin/python -m pytest -q tests/test_validation_lane_docs.py`
  - `./.venv/bin/python -m pytest -q -m runtime tests/test_auth_runtime_guard.py`
  - `./.venv/bin/python -m pytest -q -m checkpoint tests/test_checkpoints_latest_phase_consistency.py`

## Syntax / import checks
- Installer syntax:
  - `./.venv/bin/python -m py_compile install.py`
- Collector import path:
  - `./.venv/bin/python -c "import services.data_collector.main; print('ok')"`

## Full-suite note
- Full-suite validation is broader and slower. Use it when a change crosses multiple subsystems or when targeted slices are no longer sufficient.

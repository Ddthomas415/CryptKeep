# Managed Strategy Parameter Isolation

Active role: GATE. Risk: HIGH. ACCEPTED by human review of 1f064560e.

## Human Acceptance - 2026-09-08

The user explicitly accepted the corrected implementation at 1f064560e with
"INDEPENDENT REVIEW ACCEPTED". This records human acceptance, not a claim of
completed subagent re-review or GitHub CI. The earlier review history below is
preserved. Publication for CI is the next step; deployment and campaign restart
are not included. Running campaign configuration remains unverified by these
local tests.

## Defect and Scope

A managed CBP_STRATEGY_NAME override selected sma_200_trend but inherited
sma_period=20 from a differently named momentum block. Local nested parameters
were merged after the selected preset. The fix detects an explicit local
identity that differs canonically from the environment-selected identity and
does not inherit its local preset, nested parameters or legacy parameters.
The explicitly supplied environment preset retains its existing behavior.

Same-strategy overrides and no-override behavior remain unchanged. An explicit
nested trade_enabled=false still disables trading even across the switch;
parameter isolation must not silently remove a safety disable. Unnamed local
parameter blocks retain existing behavior: their intended ownership is not
redefined in this patch. Preset identity validation is not expanded here.

## Boundaries

No running campaign, state-local YAML, promotion gate, historical evidence,
cohort or deployment changed. This patch does not fix or alter runtime exit-risk
defaults. Before any ES restart/deployment, inspect the actual collector child
configuration, selected SMA period and risk exit settings. Historical recorded
SMA20-like evidence must not be relabeled as SMA200 by this code change.

## Verification

Final regression slice: 126 passed across test_managed_strategy_parameter_isolation.py,
test_strategy_runtime_runner.py, test_paper_strategy_evidence_service.py and
test_check_promotion_gates.py. git diff --check passed. Independent AUDITOR
review requested; result pending at this handoff.
Local tests are not proof of a running campaign's effective configuration.

## 2026-09-08 Runtime Review Correction

The user accepted commit 5c705d01d, but the independent AUDITOR subsequently
found a blocking bypass: the public-OHLCV loop reloaded raw nested parameters
and passed SMA20 despite startup resolving SMA200. The prior implementation
was incomplete; its 126 passing tests did not exercise this dispatch boundary.

The loop now applies _strategy_block_from_runner_cfg to the reloaded runner
configuration before binding the selected signal identity. Two bounded runtime
regressions capture the block passed to _registry_signal_with_context and assert
SMA200 plus preservation of explicit trade_enabled=true/false.

Verification: ./.venv/bin/python -m pytest -q
tests/test_strategy_runtime_runner.py
tests/test_managed_strategy_parameter_isolation.py
tests/test_paper_strategy_evidence_service.py tests/test_check_promotion_gates.py
returned 128 passed. git diff --check passed. Independent re-review requested.
No host, campaign or evidence mutation. Full-system integration remains
UNVERIFIED. Corrected implementation: READY_FOR_INDEPENDENT_REVIEW.

# Managed Strategy Parameter Isolation

Active role: ENGINEER. Risk: HIGH. READY_FOR_INDEPENDENT_REVIEW.

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

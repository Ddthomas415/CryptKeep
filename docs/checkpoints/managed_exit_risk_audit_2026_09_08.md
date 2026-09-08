# Managed Exit-Risk Configuration Audit

Active role: AUDITOR. Scope: read-only configuration-path assessment after
managed strategy parameter isolation. No runtime correction or deployment.

## SHOWN

- services/execution/strategy_runner.py::_cfg returns neither risk nor the
  four exit-control keys supplied under strategy_runner. A mocked config with
  explicit zero stop_loss_pct, take_profit_pct, trailing_stop_pct and
  max_bars_hold produced risk_present=False and exit_keys_present=[].
- run_forever reads cfg.risk and defaults absent trailing_stop_pct to 0.02.
  Thus the mocked configuration does not propagate its explicit zero.
- configs/strategies/es_daily_trend_v1.yaml declares all four controls zero,
  with a comment that exits are governed by close_below_sma.
- The collector's _component_env selects strategy identity but does not itself
  transport that strategy YAML's risk block to the runner.
- Commit 0926039e9 implemented risk-aware defaults previously. Those defaults
  are still present. tests/test_ema_runner_risk_defaults.py checks their source
  text, not whether _cfg supplies risk. This is a propagation gap, not absence
  of the earlier fix.

## Limits and Next Action

This mock proves current configuration loss, not the exact effective settings
of any historical or running process. It does not establish that copying all
local risk fields into a differently selected managed strategy is safe.

Recommended next correction: explicitly resolve ownership of managed exit
settings and propagate the selected controls through the collector/runner
boundary. Preserve explicit zeros, absent-value defaults and unrelated safety
limits; add behavioral tests at runtime dispatch, not source-string tests.
Do not blindly inherit another named strategy's risk block. Risk: HIGH;
independent review required for implementation. No campaign reset, historical
relabeling or deployment is authorized by this audit.

PR #587 remains separate: at this check five checks passed, two CI jobs were
running, and GitHub reported REVIEW_REQUIRED. No passive CI wait performed.

Acceptance state: INCOMPLETE (exit-risk treatment not implemented).

## Proposed Ownership Decision

Further trace: services/strategies/presets.py::PRESETS.es_daily_trend_v1
does not declare the four exit controls. The standalone YAML does. Selecting
the preset therefore does not currently select the YAML's exit policy.

Recommendation (requires operator decision before runtime implementation):
make the managed preset authoritative for these four exit controls. Add the
existing ES YAML's explicit zeros to the managed ES preset; carry only those
four controls to the runner, not the entire risk map. For other presets,
absence retains existing defaults. Same-identity local explicit overrides may
override the preset; differently named local overrides must not cross a managed
strategy switch. Reject malformed/nonfinite/negative supplied values rather
than silently falling back. No automatic loading of arbitrary strategy YAML.

This is a HIGH-risk change to exit policy, including disabling the currently
effective ES trailing stop. It is not merely a transport refactor. Acceptance
must explicitly cover that behavior. Implementation proof must include actual
run-loop exit-control arguments, zeros, absent defaults, same-identity overrides,
cross-identity rejection/isolation, malformed inputs, and unchanged unrelated
risk limits. Deployment remains separate and must assess open positions and
evidence segmentation; historical fills must not be reclassified.

Decision status: BLOCKED pending the explicit exit-policy choice. No runtime
implementation performed by this advisory stage.

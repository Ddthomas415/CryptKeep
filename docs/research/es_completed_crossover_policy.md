# ES completed daily crossover policy

Implementation candidate; HIGH risk; not deployed or enabled in any campaign.

The selected rule is `completed_daily_crossover_v1`. Previous completed close
must be at/below its own SMA and latest completed close strictly above its own
SMA. Regime permission must pass on that signal. Recovery of regime permission
while price remains above SMA is not a new crossing. Missing, stale, unordered
or gapped daily history blocks the policy. Forming bars do not determine it.

Explicit opt-in lives in `strategy_runner.strategy.entry_policy`; omission
preserves `legacy_signal_state` for historical trials. Runtime supplies the
conservative pre-fetch cutoff timestamp; offline research must supply its historical timestamp.
Each completed-bar entry remains subject to position, open-intent, emission
deduplication and existing risk controls. When first-signal trading is disabled,
the startup crossover is suppressed for that bar across retries and restarts.
Later crossover bars remain eligible. No latch reset. Capture verification
compares final action, crossover result, policy and completed-bar timestamp.

The shared registry implementation is exercised by the research-only
`scripts/research/es_crossover_schedule.py` next-open schedule. It does not
simulate fills, costs or profit. Legacy comparison results remain labeled
legacy: they must not be relabeled as crossover results. The existing generic
same-close parity engine is not next-open economic proof for this policy.

Operational runner execution occurs when a scheduled session processes the
completed bar, not necessarily at the exact historical opening price. No
next-open fill guarantee is made. Deploy/enable requires separate review and
an explicit transition record; preserve old evidence and original trial dates.
No default config, risk limit, exit rule, quantity or campaign is changed here.

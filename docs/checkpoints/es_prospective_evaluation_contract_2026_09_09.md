# Corrected ES Prospective Evaluation Contract

Active role: DIRECTOR. Research/operational evaluation only; no campaign launch.

## Isolated Runtime Proof

At research branch commit 55eb3279c, local venv executed six test files:
test_managed_exit_policy.py, test_strategy_runtime_runner.py,
test_managed_strategy_parameter_isolation.py, test_check_promotion_gates.py,
test_paper_strategy_evidence_service.py, test_ema_runner_risk_defaults.py.
SHOWN: 160 passed. Tests create temporary state and substitute market input.
Actual run-loop boundaries capture the signal block (SMA200, explicit trading
disable preserved) and exit-stack arguments (ES zero percentages/no time stop,
breakout defaults preserved). No real host child or venue session was launched.
This verifies isolated runtime behavior, not production deployment readiness.

## Frozen Evaluation Rules

Before launch, create a distinct research-only manifest/state directory and
record exact code, resolved config, dataset/source and cost hashes. Capture
resolved SMA200/ATR20 and four disabled runner controls from the actual child.
Use the explicitly approved launch manifest's quantity/capital; do not infer
portfolio sizing from the all-cash archive simulation or fitted sleeve weights.
Launch cannot proceed with missing or mismatched effective configuration.

Evaluation starts at the first completed UTC daily bar strictly after actual
launch. Fix the end at 30 calendar days after that start, with an operational
inspection after seven days. These are bounded inspection periods, not claims
of statistical sufficiency and not promotion thresholds. Missing bars remain
missing; do not slide the end date to get a favorable sample. No automatic
extension. A new period or parameter change requires a new labeled record.

Capture every expected daily observation, source availability, signal, intended
action, fill, exit reason, costs and effective config identity. Use only data
available at each decision timestamp; never substitute a later finalized daily
candle for the partial candle the runtime actually observed. Preserve raw input
snapshots so that this distinction can be checked later.

Operational success requires no configuration identity drift, no substituted
source/provenance, no duplicate execution accounting, and explicit reporting of
every missing scheduled observation. Any such failure marks the evaluation
invalid/incomplete; it cannot be repaired by counting older fills. This policy
does not install new automatic stop behavior into any existing campaign.

At the fixed endpoint, report completed trades, open position mark-to-market,
fees, drawdown, data gaps and strategy decisions including holds. Zero or few
trades is an inconclusive trading-efficacy result, not a failure to be hidden.
Compare cash and buy-and-hold with identical initial capital, source window and
explicit cost assumptions, separately labeled from actual paper fills. Do not
equate allocation matching with volatility/risk matching. No winner selection
or live promotion from this 30-day observation alone.

## Authorization Boundary

No trial has started and no future dataset is claimed reserved/observed yet.
The actual start/end and effective manifest must be recorded at launch. Existing
canonical campaign, cohort, positions, gate policy and historical evidence are
untouched. Before deploying accepted fixes to that campaign, inspect open
positions and separately authorize the transition and any restart.

Acceptance state: INCOMPLETE for prospective evidence (not yet collected).
Isolated implementation proof is SHOWN; production child proof is UNVERIFIED.

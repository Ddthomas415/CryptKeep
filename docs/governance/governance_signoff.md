# Governance Signoff

Version: 1.0
Status: Frozen
Owner: Governance
Effective Date: 2026-03-21

# Governance Sign-Off

| Control Area | Expected Canonical Module | Actual Repo File(s) | Present? | Gap? | Blocking? | Notes |
|---|---|---|---|---|---|---|
| Deployment truth | deployment_truth.py | `services/governance/deployment_truth.py` | yes | no | no | Canonical wrapper exists and reads deployment posture from settings + auth runtime guard |
| Campaign state | campaign_state.py | `services/governance/campaign_state.py` | yes | no | no | Canonical wrapper exposes the governed campaign state set |
| Campaign fingerprint | campaign_fingerprint.py | phase1_research_copilot/news_ingestion/main.py, services/admin/journal_exchange_reconcile.py | partial | yes | no | Fingerprint logic exists but may be fragmented |
| Campaign state machine | campaign_state_machine.py | `services/governance/campaign_state_machine.py` | yes | no | no | Canonical wrapper blocks invalid-to-running transitions |
| Campaign validation | campaign_validation.py | `services/governance/campaign_validation.py`, `scripts/run_paper_strategy_evidence_collector.py`, `services/analytics/paper_strategy_evidence_service.py` | yes | yes | yes | Wrapper exists, but validation depth is still minimal and distributed beyond the wrapper |
| Invalidation | invalidation.py | `services/governance/invalidation.py`, `services/backtest/evidence_cycle.py`, `dashboard/services/strategy_evaluation.py` | yes | yes | yes | Wrapper exists, but terminal invalidation enforcement outside status language is still not fully proven |
| Decision engine | decision_engine.py | `services/governance/decision_engine.py`, `services/backtest/evidence_cycle.py`, `dashboard/services/digest/builders.py` | yes | yes | yes | Canonical wrapper exists, but governed decision authority is still broader than this thin module |
| Claims guard | claims_guard.py | `services/governance/claims_guard.py`, `dashboard/services/digest/builders.py`, `services/security/auth_capabilities.py` | yes | yes | yes | Wrapper exists, but repo-wide product/deployment claim enforcement is still only partial |
| Operator overrides | operator_overrides.py | `services/governance/operator_overrides.py`, `services/profiles/bundles.py` | yes | yes | yes | Canonical wrapper exists, but full governed mutation authority still needs a single path |

## Auth / MFA Verified State

| Control Area | Actual Repo File | Assessment | Gap | Blocking |
|---|---|---|---|---|
| Built-in MFA / TOTP | `dashboard/auth_gate.py` | **Present** — MFA pending state, enrollment state, signed-in MFA controls, disable flow, session integration | Real operator validation still needed (enrollment, recovery, re-enable) | No |
| Session expiry | `dashboard/auth_gate.py` | **Present** — session timeout + last activity enforcement | Needs runtime/operator validation only | No |
| Dev-only bypass guard | `dashboard/auth_gate.py` | **Present** — bypass restricted outside dev | Needs deployment validation only | No |
| Failed-login lockout | `dashboard/auth_gate.py` | **Present** — failed count + lockout window | Needs runtime/operator validation only | No |
| Remote/public hardening | `dashboard/auth_gate.py` + deployment layer | **Partial** — app warns that stronger outer controls are required | Outer access control, direct-origin blocking, remote/public validation still open | **Yes** |

## Evidence / Decision Verified State

| Control Area | Actual Repo File | Assessment | Gap | Blocking |
|---|---|---|---|---|
| Evidence collection | `services/analytics/paper_strategy_evidence_service.py` | **Present** — bounded collection path owns campaign iteration, runtime status, evidence rerun trigger, and decision-record regeneration gates | Immutable campaign spec / deep spec freeze is still not fully proven in this layer | No |
| Evidence reclassification | `services/backtest/evidence_cycle.py` | **Present** — assigns evidence status, confidence, decision labels, comparison output, and `research_acceptance` per strategy row | Terminal invalidation and immutable lineage/fingerprint binding are still not fully proven here | **Yes** |
| Strategy decision surfacing | `dashboard/services/strategy_evaluation.py`, `dashboard/services/digest/builders.py`, `dashboard/services/copilot_reports.py` | **Present** — research-only workbench, Home digest, and Copilot Reports now surface thin or non-credible evidence explicitly | Surfacing is present, but it is not itself the authoritative promotion gate | No |
| CAUTION / invalidation enforcement | `services/backtest/evidence_cycle.py`, `dashboard/services/promotion_ladder.py` + related callers | **Partial** — thin/synthetic evidence is blocked from promotion-grade outcomes, but terminal invalidation remains not fully proven | Need explicit end-to-end proof that invalid states cannot reach governed campaign continuation | **Yes** |

### Working Notes — Evidence / Decision Audit

Use the code inspection above to replace placeholder values with:
- Present
- Partial
- Missing

Questions to answer:
1. Is evidence collection bounded and parameterized in one controlled path?
2. Does evidence reclassification explicitly constrain outcomes based on evidence status (e.g. `synthetic_only`, `paper_thin`)?
3. Is there any path where CAUTION/invalid evidence can still reach strong classifications?
4. Are invalidation conditions only displayed, or also enforced?
| Control Area | Actual Repo File | Assessment | Gap | Blocking |
|---|---|---|---|---|
| Single bounded campaign path | `services/analytics/paper_strategy_evidence_service.py` | **Present** — one top-level run loop owns strategy iteration, status writes, component startup/stop, and evidence rerun trigger | Need proof no alternate unmanaged campaign path exists elsewhere | No |
| Runtime ownership / exclusivity | `services/analytics/paper_strategy_evidence_service.py` | **Present** — blocks if another strategy runner PID is active | PID/lock ownership is operational, not full governance identity | No |
| Controlled component lifecycle | `services/analytics/paper_strategy_evidence_service.py` | **Present** — start/reuse/stop/wait logic for shared components is explicit | Not append-only or audit-grade | No |
| Stop handling | `services/analytics/paper_strategy_evidence_service.py` | **Present** — explicit stop-file causes terminal stop path | No visible auth/authorization boundary in this snippet | No |
| Evidence rerun gate | `services/analytics/paper_strategy_evidence_service.py` | **Present** — evidence cycle runs only when `_campaign_has_new_paper_history(results)` is true | Gate is based on result deltas, not full governed campaign invalidation | No |
| Decision-record regeneration gate | `services/analytics/paper_strategy_evidence_service.py` | **Present** — decision record only regenerates when paper history changed | No explicit campaign fingerprint/spec check visible here | No |
| Immutable campaign spec / deep spec freeze | `services/analytics/paper_strategy_evidence_service.py` | **Partial / not proven** | No persisted immutable campaign spec visible in this snippet | **Yes** |
| Terminal invalidation | `services/analytics/paper_strategy_evidence_service.py` | **Not proven** | No visible invalidation path from drift/contamination to terminal invalid state | **Yes** |
| Single governed mutation path | `services/analytics/paper_strategy_evidence_service.py` | **Partial** — this file owns runtime status mutation for campaigns | No proof all campaign truth mutations flow only through this path | **Yes** |

### Next Audit Targets

Need to verify from code:
1. Where `paper_thin` is assigned
2. Where invalidation conditions are enforced vs only displayed
3. Whether any path can still escalate thin/synthetic evidence into stronger outcomes
4. Whether campaign spec is persisted/frozen anywhere outside runtime status snapshots

## Evidence Artifact / Comparison State

| Control Area | Actual Repo File | Assessment | Gap | Blocking |
|---|---|---|---|---|
| Evidence comparison against prior artifact | `services/backtest/evidence_cycle.py` | **Present** — `build_evidence_comparison(...)` compares current vs prior persisted rows and summarizes improvement/degradation/top-strategy changes | Comparison is descriptive; not a hard governance gate by itself | No |
| Persisted evidence artifact writing | `services/backtest/evidence_cycle.py` | **Present** — `persist_strategy_evidence(...)` writes latest + historical JSON artifacts and injects comparison into payload | No append-only guarantee; artifacts are mutable files | No |
| Decision-record path generation | `services/backtest/evidence_cycle.py` | **Present** — dated markdown decision-record path is derived from `as_of` | Path generation alone does not prove decision governance | No |
| Comparison-driven invalidation enforcement | `services/backtest/evidence_cycle.py` | **Not proven** — comparison reports movement and evidence status deltas | No visible terminal invalidation or blocking on drift in this snippet | **Yes** |
| Immutable artifact lineage / fingerprint binding | `services/backtest/evidence_cycle.py` | **Partial / not proven** | Persisted history exists, but no visible cryptographic/spec fingerprint binding in this snippet | **Yes** |

## Evidence Status Enforcement — Verified Update

| Control Area | Actual Repo File | Assessment | Gap | Blocking |
|---|---|---|---|---|
| Base decision classification | `services/backtest/evidence_cycle.py` | **Present** — `_decision_for_row(...)` computes `keep / improve / freeze / retire` from explicit evidence inputs | Final governance mapping to `WATCH / ITERATE / PROMOTE / RETIRE` is not visible here | No |
| Negative paper-history downgrade | `services/backtest/evidence_cycle.py` | **Present** — `_apply_paper_history_adjustment(...)` downgrades `keep -> improve` and `improve -> freeze` on negative net realized PnL or weak win rate | No proof here that other code paths cannot bypass this | Yes |
| Promotion restraint | `services/backtest/evidence_cycle.py` | **Present** — positive supplemental paper history explicitly does **not** justify promotion by itself | Broader promotion guard outside this helper is not shown | Yes |
| Missing/synthetic evidence gating | `services/backtest/evidence_cycle.py` | **Present** — `_evidence_status_for_row(...)` returns `insufficient` or `synthetic_only` with `low` confidence when paper history is missing or strategy-attribution is absent | Full downstream enforcement against stronger governed outcomes is not shown | Yes |
| Paper-thin assignment | `services/backtest/evidence_cycle.py` | **Present** — `paper_fills < 6` or `paper_closed_trades < 3` yields `paper_thin` with `low` confidence | Need proof no downstream path can still escalate `paper_thin` into promotion-grade outcomes | Yes |
| Paper-supported ceiling | `services/backtest/evidence_cycle.py` | **Present** — adequate paper sample yields `paper_supported` with only `medium` confidence and explicitly “research-grade rather than promotion-grade” wording | Final governed promotion block still not shown in this snippet | Yes |

## Promotion Ladder — Verified Gate

| Control Area | Actual Repo File | Assessment | Gap | Blocking |
|---|---|---|---|---|
| Downstream promotion gate | `dashboard/services/promotion_ladder.py` | **Present** — tiny-live review is blocked unless the top strategy is `keep`, has at least 5 closed trades, has `paper_supported` evidence, has at least medium confidence, acceptable drawdown, and acceptable paper/live drift | Need proof no alternate promotion path bypasses this ladder | **Yes** |
| Thin/synthetic evidence block | `dashboard/services/promotion_ladder.py` | **Present** — if `top_evidence_status != "paper_supported"`, promotion is blocked with the evidence note or explicit blocker | Need full repo check for alternate bypass paths | **Yes** |
| Confidence gate | `dashboard/services/promotion_ladder.py` | **Present** — even `paper_supported` evidence is blocked if confidence is `unknown` or `low` | Need proof all promotion decisions use this path | **Yes** |
| Closed-trade minimum | `dashboard/services/promotion_ladder.py` | **Present** — promotion requires at least 5 closed trades | Threshold rationale may need policy sign-off | No |

## Promotion Gate — Human Approval

Human approvals recorded:
- `promotion_ladder.py` is accepted as the authoritative promotion gate.
- No alternate promotion path bypass is accepted at this stage.
- Current thresholds are approved:
  - recommendation must be `keep`
  - closed trades must be at least `5`
  - evidence status must be `paper_supported`
  - confidence must be at least `medium`
  - max drawdown must be `<= 8.0%`
  - paper/live drift must not be `unknown` or `high`

Governance status:
- Promotion gate authority: **Approved**
- Promotion bypass concern: **Accepted as cleared for current project state**
- Threshold policy: **Approved**

| Control Area | Actual Repo File | Assessment | Gap | Blocking |
|---|---|---|---|---|
| Promotion authority sign-off | `dashboard/services/promotion_ladder.py` | **Approved by human review** — authoritative promotion gate accepted, no alternate bypass accepted, thresholds approved | None for current governance baseline | No |

## Remaining Blocking Governance Gaps

| Control Area | Actual Repo File | Assessment | Gap | Blocking |
|---|---|---|---|---|
| Campaign / artifact fingerprinting | `services/admin/journal_exchange_reconcile.py`, `phase1_research_copilot/news_ingestion/main.py` | **Partial** — fingerprint logic exists | Not yet proven as canonical campaign/spec fingerprint binding | **Yes** |
| Terminal invalidation | visible repo grep only | **Not proven** | No explicit invalid terminal campaign state verified yet | **Yes** |
| Single governed mutation path | `services/profiles/bundles.py`, `services/live_router/router.py`, `services/analytics/paper_strategy_evidence_service.py` | **Partial** — multiple mutation/runtime paths exist | Need proof one governed state path is authoritative | **Yes** |
| Deployment drift handling | visible repo grep only | **Not proven** | No verified material deployment drift invalidation path yet | **Yes** |

## Governance Baseline — Human Decision

Human decisions recorded:
- Final governance baseline audit is accepted for the current project state.
- Remaining governance gaps are accepted as **blocking** before any new bounded campaign.

Blocking gaps before next campaign:
1. Terminal invalidation
2. Single governed mutation path
3. Immutable campaign spec / deep spec freeze
4. Canonical fingerprint binding / material deployment drift handling

Operational rule:
- No new bounded campaign may be approved until the four blocking gaps above are resolved or explicitly waived by human decision.

Governance status:
- Baseline audit: **Accepted**
- Campaign readiness: **Blocked pending gap closure**

## Blocking Governance Gaps — Human Approval

Human approvals recorded:
- Waiver authority over blocking gaps: **Approved**
- Final fixes approved for:
  - terminal invalidation
  - single governed mutation path
  - immutable campaign spec / deep spec freeze
  - canonical fingerprint binding / deployment-drift handling

Execution rule:
- The four blocking gaps are approved for implementation and closure in the current workstream.
- No new bounded campaign is approved until these four fixes are implemented and reviewed.


## Approved Implementation Worklist

1. Terminal invalidation
2. Single governed mutation path
3. Immutable campaign spec / deep spec freeze
4. Canonical fingerprint binding / deployment-drift handling

Next step:
- inspect the governing files above
- patch the minimal authoritative path
- add tests before approving any new bounded campaign


## Implementation Fixes — Human Approval

Human approvals recorded:
- Final acceptance of the implemented fixes: **Approved**
- Human authority to decide when campaign readiness changes from blocked to allowed: **Approved**

Readiness rule:
- Campaign readiness may change from **Blocked** to **Allowed** only after human review confirms the implemented fixes are present, tested, and accepted.

Required fix set:
1. Terminal invalidation
2. Single governed mutation path
3. Immutable campaign spec / deep spec freeze
4. Canonical fingerprint binding / deployment-drift handling

Governance state:
- Implementation approval: **Approved**
- Campaign readiness authority: **Approved**
- Campaign readiness status: **Blocked until human verification of implemented fixes**

## Blocking Governance Fixes — Human Verification and Readiness Decision

Human decisions recorded:
- Final verification that the four blocking fixes are actually implemented: **YES**
- Explicit decision changing campaign readiness from **Blocked** to **Allowed**: **YES**

Verified fix set:
1. Terminal invalidation
2. Single governed mutation path
3. Immutable campaign spec / deep spec freeze
4. Canonical fingerprint binding / deployment-drift handling

Governance state:
- Blocking fixes verified: **Approved**
- Campaign readiness: **Allowed**
- Bounded campaign authorization: **Enabled for the current governed path**


## Next Governed Bounded Evidence Campaign

Approved target strategies:
- breakout_donchian
- ema_cross

Frozen campaign spec:
- venue: coinbase
- symbol set: SUI/USD, APR/USD, 2Z/USD
- timeframe: live tick runner with current governed strategy settings
- runtime_sec: 300
- strategy_min_bars: 28
- tick_interval_sec: 1.0
- warmup_override: enabled only as already approved for managed evidence runs

Pass/fail gates:
- pass: new attributed paper fills are written to trade_journal.sqlite
- fail: no new attributed fills, or campaign exits outside governed path
- post-run action: rerun evidence only if paper history changed


## Human Oversight Confirmation — Campaign Phase

The following Human Oversight Required items were explicitly answered YES:

- prioritize next evidence campaign / deployment hardening / lifecycle safety review
- decide whether campaign readiness should be used now
- validate any production, public-exposure, or trading-performance claim
- approve the frozen campaign spec
- decide whether to run a second symbol after the first result
- accept the post-run reclassification outcome

Status:
- Human oversight confirmations for the current campaign phase: **Complete**

## Standing Human Oversight Rule

Human decision recorded:
- YES for any future newly introduced Human Oversight Required item.

Operational meaning:
- Any newly introduced oversight item in this governed campaign phase requires explicit human acknowledgment, and that acknowledgment is pre-authorized as YES unless later overridden by a new human decision.


## Campaign Execution Decisions — Human Approval

Human decisions recorded:
- Discard the interrupted SUI/USD run entirely for evidence purposes: **YES**
- If SUI/USD again produces no fills, running a second symbol is approved: **YES**
- Any post-run reclassification outcome from the governed path is approved for acceptance: **YES**

Operational rule:
- The interrupted SUI/USD run does not count as evidence.
- The current rerun on SUI/USD is the active governed attempt.
- If the rerun completes with no new attributed fills, one second-symbol governed run is allowed.
- Evidence is rerun only if paper history changes.


## Deployment Scope — Human Approval

Human decisions recorded:
- Keep `local_private_only` as the enforced default: **YES**
- Any future switch to `remote_allowed` requires explicit human approval: **YES**

Operational rule:
- Current enforced auth/deployment posture remains `local_private_only`.
- `remote_public_candidate` may exist as a settings/documentation state, but it is not treated as approved remote/public deployment.
- Any future switch to `remote_allowed` requires a new explicit human decision and verification of outer access control, MFA flow, and direct-origin blocking.


## Required Post-Run Diagnostics

After every governed paper campaign, generate and review:

python3 scripts/report_paper_run_diagnostics.py --limit 20

When strategy/symbol-specific tracing is needed, use:

python3 scripts/report_paper_run_diagnostics.py --strategy-id ema_cross --symbol 2Z/USD --limit 10

Purpose:
- confirm signal → intent → paper order → paper fill → journal fill path
- prevent stale or incorrect interpretation of campaign outcomes

## Required Post-Run Diagnostics

After every governed paper campaign, generate and review:

python3 scripts/report_paper_run_diagnostics.py --limit 20

When strategy/symbol-specific tracing is needed, use:

python3 scripts/report_paper_run_diagnostics.py --strategy-id ema_cross --symbol 2Z/USD --limit 10

Purpose:
- confirm signal → intent → paper order → paper fill → journal fill path
- prevent stale or incorrect interpretation of campaign outcomes

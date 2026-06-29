# Remaining Tasks

This file is a lightweight index only.

## Current state
The active operating state is paper-evidence collection, not live launch.

SHOWN:
- `master`, `origin/master`, and `review-stabilized` are kept aligned after
  accepted PR merges. Verify the exact current boundary with
  `git rev-parse HEAD origin/master origin/review-stabilized`.
- Laptop-owned paper campaigns are healthy:
  - `es_daily_trend_v1`: `fills=18`, `closed=9`, `pnl=32.1776`
  - `breakout_default`: `fills=11`, `closed=5`, `pnl=-4.1182`
- Hetzner-owned `ema_cross_default` must be checked with the Hetzner campaign
  manifest, not the laptop shortcut.
- Canonical `es_daily_trend_v1` paper promotion remains blocked at `2/10`
  provenance-qualified round trips, with `8` remaining.
- `make status-paper-gate-qualification` now explains which fills count,
  remain incomplete, or are rejected by provenance checks.
- `make status-paper-soak` and `make status-paper-all` now surface compact
  paper-history qualification details directly in the daily status output.
- Raw all-history currently reports `9` closed trades, but those remain
  diagnostic unless both entry and exit fills carry the required non-sample
  public-OHLCV provenance.

Current accepted checkpoint:

- docs/checkpoints/paper_gate_status_2026_06_24.md

## Canonical blocker list
Root-runtime launch blockers are tracked separately. They are not the same as
the current paper-evidence campaign blocker.

- docs/checkpoints/launch_blockers_root_runtime.md

Strategy-evaluation work is tracked separately:

- docs/checkpoints/strategy_signal_quality_plan_2026_05_22.md
- docs/checkpoints/pullback_recovery_campaign_plan_2026_06_19.md
- docs/checkpoints/composite_hybrid_strategy_wrapper_design_2026_06_24.md
- docs/checkpoints/composite_hybrid_leaderboard_comparison_2026_06_27.md
- docs/checkpoints/short_market_strategy_research_spec_2026_06_19.md
- docs/checkpoints/candidate_layer_read_only_activation_objective_2026_06_22.md
- docs/checkpoints/pr43_ai_operator_oversight_rebuild_objective_2026_06_28.md
- docs/checkpoints/pr43_managed_multi_symbol_runtime_objective_2026_06_28.md
- docs/checkpoints/pr43_safe_pipeline_startup_hardening_objective_2026_06_28.md

## Active Backlog
These are the remaining tasks visible from the accepted checkpoint and planning
documents. Keep implementation scoped; high-risk runtime, launch, strategy, or
deployment work still needs independent review.

1. Continue canonical paper evidence collection until `es_daily_trend_v1`
   reaches 10 provenance-qualified round trips.
2. After the paper gate reaches 10 qualified round trips, write the manual
   strategy performance decision against the accepted baseline.
3. Prove private lifecycle runtime flow in one reachable supported
   sandbox/testnet venue, or record an explicit human exception decision.
4. Produce the launch evidence packet: restart/recovery, kill-switch,
   reconciliation halt/resume, rollback, and lifecycle or exception evidence.
5. Continue only the still-open PR #43 rebuild candidates from clean `master`.
   AI operator oversight is independently accepted as a read-only one-shot
   synthesis report over existing monitor/watch/gate artifacts; do not rebuild
   a second background monitor. Managed multi-symbol paper runtime now has a
   read-only proposal planner implementation proof ready for independent
   review; do not implement autonomous campaign starts or mutate manifests.
   Safe pipeline wrapper/startup hardening is accepted as a read-only startup
   topology/gap audit; do not implement a new wrapper unless a current-master
   gap is reproduced and separately reviewed. Supervised-soak reporting and
   durable pipeline log evidence are already rebuilt/closed.
6. Run the full post-fix isolated Stage 0 proof for
   `pullback_recovery_default` before enabling any persistent campaign. The
   read-only readiness report is accepted and merged; run
   `make pullback-stage0-baseline` immediately before the long proof and
   `make pullback-stage0-verify` afterward.
7. Add additional composite/hybrid long-window research variants until the
   candidate has comparison evidence across at least three realized synthetic
   windows. Do not add a persistent paper campaign or production path until
   that comparison evidence is independently reviewed and accepted.
8. Continue accepted short/context follow-through: resolve the Binance
   derivatives public-data `NetworkError` or choose a compliant read-only
   derivatives venue, and keep replay limited to deterministic sample data or
   accepted public row families until that proof exists.
9. Continue the derivatives/intraday roadmap as read-only data collection and
   replay only until compliance, margin, liquidation, reduce-only, and risk
   controls are proven.
10. Complete Hetzner host follow-through before any canonical `.cbp_state`
    migration: backup restore rehearsal, disk/health alerting, single-owner
    proof, and reviewed stop-copy-verify-start procedure.
11. Keep `scripts/SCRIPTS.md`, `docs/GOLDEN_PATH.md`, and this file aligned
    whenever operator commands or workflow change.

## Recently completed
- Pullback Stage 0 readiness report is accepted:
  PR #139 merged as `f26dd965e`, adding
  `scripts/check_pullback_stage0_readiness.py` and
  `services/analytics/pullback_stage0_readiness.py`. The next pullback action
  is the operator-run 15-minute isolated Stage 0 proof, not another readiness
  review.
- Paper-soak status qualification visibility is complete:
  PR #127 merged after checks passed, and the daily soak output now shows
  qualified/all-history closed trades, latest all-history fill, counted,
  incomplete, and rejected evidence fills, and latest qualified close.
- PR #43 AI operator oversight report implementation proof is accepted:
  `docs/checkpoints/pr43_ai_operator_oversight_rebuild_objective_2026_06_28.md`
  records that the current paper-sim monitor is already the wake-up layer and
  that the accepted implementation is a read-only one-shot oversight synthesis
  report, not a second background monitor.
- PR #43 managed multi-symbol runtime is scoped:
  `docs/checkpoints/pr43_managed_multi_symbol_runtime_objective_2026_06_28.md`
  records that the current explicit manifest runtime remains the authority and
  any rebuild must start as a read-only campaign proposal planner, not an
  autonomous campaign starter.
- PR #43 managed multi-symbol runtime implementation proof is accepted:
  `scripts/plan_managed_paper_campaigns.py` and
  `services/analytics/managed_paper_campaign_planner.py` provide a read-only
  proposal planner that writes only proposal artifacts. Campaign manifests,
  state directories, and running collectors are unchanged.
- PR #43 safe-pipeline/startup hardening is scoped:
  `docs/checkpoints/pr43_safe_pipeline_startup_hardening_objective_2026_06_28.md`
  records that the current canonical startup path and existing safe wrappers
  must be audited first; do not add `run_pipeline_safe.py` or alter startup
  behavior unless a current-master gap is reproduced and separately reviewed.
- PR #43 safe-pipeline/startup hardening implementation proof is accepted:
  `scripts/audit_startup_hardening.py` and
  `services/runtime/startup_hardening_audit.py` provide a read-only topology
  audit that writes only startup-audit artifacts. Runtime startup behavior is
  unchanged and any wrapper/topology change remains a separate high-risk task.
- Composite/hybrid long-window research proof is accepted:
  `docs/checkpoints/composite_hybrid_long_window_research_proof_2026_06_27.md`
  records the accepted proof. It fixes the composite warmup/participation gap
  for one long synthetic window, but the candidate remains blocked from paper
  until comparison evidence exists across at least three realized synthetic
  windows.
- Shadow spread fresh-record proof is complete:
  `docs/checkpoints/shadow_spread_fresh_record_proof_2026_06_24.md` records
  `9/9` fresh `es_daily_trend_v1` signal records with `spread_bps` and
  `market_quality_reason=ok`.
- PR #43 rebuild follow-up is fully scoped:
  `docs/checkpoints/pr43_rebuild_followup_status_2026_06_24.md` records
  supervised-soak reporting, durable pipeline log evidence, and AI operator
  oversight as accepted. Managed multi-symbol runtime and safe-pipeline
  wrapper/startup hardening now have separate read-only objective checkpoints;
  implementation remains blocked until those scoped proofs are pursued.
- Paper gate snapshot refreshed:
  `docs/checkpoints/paper_gate_status_2026_06_24.md` records local laptop
  campaigns healthy, canonical `es_daily_trend_v1` at `2/10`
  provenance-qualified round trips, and manual review still required.
- Short-side feasibility audit is complete:
  `docs/checkpoints/short_context_data_feasibility_audit_2026_06_19.md`
  selected the read-only crypto-edge collector as the safe base; PR #72 then
  added accepted open-interest and order-book row support without enabling
  replay, paper short simulation, routing, or execution.
- Read-only candidate outcome report objective is accepted by PR #113:
  `614bae6e7` added the report builder, root CLI, Make target, tests, and
  artifact path; implementation remains read-only and does not enable
  candidate-advisor strategy selection.
- Pipeline exit evidence capture is closed by PR #109:
  `b4db2dba2` added durable supervised process log paths, the implementation
  was independently accepted, and PR #109 merged as `f4b8c296d`.

## Master integration TODO
Master integration completed through
[#49](https://github.com/Ddthomas415/CryptKeep/pull/49) on 2026-06-06.

SHOWN on 2026-06-06:
- PR #49 merged as `5ab9732a2`.
- All eight GitHub checks passed before merge.
- `origin/master...origin/review-stabilized = 0 / 0` after branch alignment.
- The prior 25-file conflict plan is obsolete and closed.

Next action:
- Keep new accepted work on focused branches or `review-stabilized`.
- Integrate future batches through reviewed pull requests without allowing
  `master` and the integration branch to accumulate avoidable divergence.

## Interpretation
Current paper-campaign path:

1. use `make status-paper-all` for the daily check-in: laptop campaign health,
   canonical paper-gate progress, and Hetzner-owned `ema_cross_default` status
2. use `make status-paper-soak` or `make status-paper-hetzner` only when you
   intentionally want one side of the split-host status
3. use `make status-paper-campaigns` only when you need raw laptop process
   restore/status detail
4. wait for `es_daily_trend_v1` to reach 10 provenance-qualified round trips,
   then perform the manual performance review

Root-runtime launch path:

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
- strategy signal-quality / paper-evaluation work
- conditional broader-scope controls
- non-blocking architectural debt

Do not treat raw all-history trade count as promotion progress. The actionable
paper gate is the provenance-qualified count reported by `make
status-paper-all`, `make status-paper-soak`, or
`scripts/check_promotion_gates.py --json`.

# PR #43 Managed Multi-Symbol Paper Runtime Objective - 2026-06-28

Status: ACCEPTED

Active role: DIRECTOR

## Purpose

Convert the remaining PR #43 managed multi-symbol paper-runtime rebuild group
into one current-master objective.

This checkpoint does not implement managed symbol selection, start campaigns,
change campaign manifests, or revive stale PR #43 source. It defines the
smallest defensible next implementation boundary after comparing the old
managed-symbol idea against the accepted current manifest-driven campaign
runtime.

## Evidence

SHOWN:
- `docs/checkpoints/pr43_operator_observability_disposition_2026_06_19.md`
  groups these old PR #43 commits under managed multi-symbol paper runtime:
  `25507b84`, `82f2ef20`, `953902cb`, `b67b99df`, `cde84dd0`,
  `a0b20c0c`, `c23d3823`, `c50a2af5`, and `f4f5605a`.
- `docs/checkpoints/pr43_rebuild_followup_status_2026_06_24.md` keeps managed
  multi-symbol paper runtime open only as a separate scoped rebuild candidate.
- Current source does not contain:
  - `services/runtime/managed_symbol_config.py`
  - `services/runtime/managed_symbol_selection.py`
- Current source already contains the accepted explicit campaign-manifest
  runtime:
  - `services/analytics/paper_campaign_recovery.py`
  - `scripts/restore_paper_campaigns.py`
  - `configs/paper_evidence_campaigns.json`
  - `configs/paper_evidence_campaigns.laptop.json`
  - `configs/paper_evidence_campaigns.hetzner.example.json`
  - `tests/test_paper_campaign_recovery.py`
- The current manifest model already supports multiple explicit campaigns,
  per-campaign `CBP_STATE_DIR` isolation, idempotent status/restore, selected
  campaign operations, and laptop/Hetzner ownership separation.
- The active laptop manifest owns `es_daily_trend_v1` and `breakout_default`.
- The Hetzner example manifest owns only `ema_cross_default` and disables
  desktop notifications.
- `configs/strategies/es_daily_trend_v1.yaml` keeps candidate-advisor strategy
  selection disabled.

UNVERIFIED:
- Whether dynamically selected symbols improve paper evidence quality.
- Whether scanner/candidate data is sufficiently fresh, liquid, and
  provenance-stamped to authorize managed campaign creation.
- Whether adding managed symbol selection would preserve single-owner campaign
  guarantees across laptop and Hetzner.
- Whether per-symbol state directories, gate attribution, and operator reports
  are sufficient for more than the currently accepted explicit campaigns.

## Decision

Do not rebuild the old PR #43 scanner-managed symbol runtime as an autonomous
campaign starter.

The accepted current model is explicit campaign ownership by manifest. Any
managed multi-symbol rebuild must be a read-only planner first. It may propose
campaign rows, but it must not start, stop, restore, or mutate campaign state.

The first implementation objective, if pursued, is:

- read current campaign manifests
- read accepted candidate/signal-quality artifacts where available
- propose candidate campaign rows for human review
- prove every proposed row has an isolated state directory, explicit strategy,
  explicit symbol, explicit venue, explicit signal source, and explicit host
  ownership
- write proposal artifacts only
- leave existing manifests and running campaigns unchanged

## Scoped Objective

Build a read-only managed paper-campaign planner that answers:

- Which candidate strategy/symbol pairs are eligible for a future explicit
  campaign manifest row?
- Which existing campaign, if any, already owns that strategy/symbol pair?
- Which host should own the proposed campaign: laptop, Hetzner, or neither?
- Which evidence/gate artifacts would be produced under the proposed isolated
  state directory?
- Which proposals are rejected, and why?

The planner must produce a proposal artifact only. A separate reviewed change
would be required before any generated proposal can be applied to
`configs/paper_evidence_campaigns*.json` or started by
`scripts/restore_paper_campaigns.py`.

## Required Boundaries

MUST NOT:
- start or stop paper campaigns
- call `restore_paper_campaigns.py --restore`
- mutate `configs/paper_evidence_campaigns*.json`
- create, move, or delete `.cbp_state*` directories
- enable candidate-advisor strategy selection
- change promotion gates or strategy decisions
- route orders, enqueue orders, or touch live execution
- merge laptop and Hetzner campaign ownership
- rely on stale PR #43 source files or compiled cache artifacts

MUST:
- be read-only by default
- consume current-master manifests and artifacts only
- keep generated proposals under a dedicated artifact path
- surface missing candidate data as `insufficient_candidate_evidence`
- reject proposals that reuse a state directory
- reject proposals that duplicate an existing `(strategy, session_strategy_id,
  symbol, venue)` owner
- require explicit host ownership for every proposal
- include tests proving no manifest mutation and no restore/start call

## Smallest Implementation Path

1. Add a service such as
   `services/analytics/managed_paper_campaign_planner.py`.
2. Add a root command such as `scripts/plan_managed_paper_campaigns.py`.
3. Load and normalize:
   - `configs/paper_evidence_campaigns.laptop.json`
   - `configs/paper_evidence_campaigns.hetzner.example.json`
   - optional candidate outcome and signal-quality artifacts
4. Produce:
   - latest JSON proposal artifact
   - dated JSON proposal artifact
   - optional Markdown summary
5. Add docs/tests proving the command is a planner, not a campaign controller.

## Proof Required

Before implementation can be accepted:

- A root CLI command runs without network access.
- Tests prove:
  - existing manifest rows are loaded and preserved unchanged
  - duplicate campaign names are rejected
  - duplicate state directories are rejected
  - duplicate strategy/session/symbol/venue owners are rejected
  - missing candidate artifacts produce `insufficient_candidate_evidence`
  - no campaign restore/start command is invoked
  - no manifest file is written
  - generated proposals include explicit host ownership
- `configs/strategies/es_daily_trend_v1.yaml` remains
  `use_candidate_advisor: false`.
- `scripts/SCRIPTS.md`, `docs/GOLDEN_PATH.md` if operator-facing, and
  `REMAINING_TASKS.md` describe the planner as read-only.

## Out Of Scope

- automatic scanner-managed campaign creation
- persistent multi-symbol daily loop
- manifest mutation
- active campaign migration between laptop and Hetzner
- candidate-advisor activation
- promotion-gate changes
- live trading, routing, or execution
- safe pipeline wrapper/startup hardening

## Risk

HIGH for later implementation:
- Managed multi-symbol runtime affects financial strategy experimentation,
  background job ownership, evidence attribution, and operator workflow.

LOW for this checkpoint:
- This is planning-only. It does not modify runtime behavior, background jobs,
  strategy logic, campaign manifests, gates, live execution, or order routing.

Acceptance state: ACCEPTED

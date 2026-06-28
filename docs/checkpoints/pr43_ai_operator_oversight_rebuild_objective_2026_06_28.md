# PR #43 AI Operator Oversight Rebuild Objective - 2026-06-28

Status: READY_FOR_IMPLEMENTATION

Active role: DIRECTOR

## Purpose

Convert the remaining PR #43 AI operator alerting/oversight rebuild candidate
into one current-master objective.

This checkpoint does not rebuild stale PR #43 code. It defines the only
defensible next implementation boundary after comparing the old rebuild idea
against the accepted current paper-simulation monitor, watches, dashboard
surfaces, and alert primitives.

## Evidence

SHOWN:
- `docs/checkpoints/pr43_operator_observability_disposition_2026_06_19.md`
  marks the old AI alert and oversight commits as `rebuild`, not `merge`.
- `docs/checkpoints/pr43_rebuild_followup_status_2026_06_24.md` requires a
  scoped objective before implementing any remaining PR #43 rebuild group.
- Current source still does not contain:
  - `scripts/run_ai_alert_monitor.py`
  - `scripts/run_ai_oversight_watch.py`
  - `services/ai_copilot/alert_monitor.py`
  - `services/ai_copilot/oversight_watch.py`
- Current source does contain the accepted paper monitor:
  - `scripts/run_paper_sim_monitor.py`
  - `services/analytics/paper_sim_monitor.py`
  - `tests/test_paper_sim_monitor.py`
  - `tests/test_run_paper_sim_monitor.py`
- `services/analytics/paper_sim_monitor.py` already provides:
  - named watches
  - durable JSON/Markdown watch reports
  - desktop notification attempts
  - recent watch report discovery
  - promotion-progress and provenance-qualification context
- `./.venv/bin/python scripts/run_paper_sim_monitor.py --status` shows four
  active watches: `next_fill`, `position_closed`, `campaign_completed`, and
  `investigate`.
- The same status output shows recent watch reports for `campaign_completed`
  and `investigate`, with desktop notifications marked `sent=true`.
- `services/alerts/alert_dispatcher.py` and `services/alerts/alert_router.py`
  provide lower-level alert primitives, but they are not a paper-campaign
  oversight product by themselves.
- Existing AI copilot modules are read-only analyst/reporting surfaces, not
  autonomous order-routing or promotion-gate authorities.

UNVERIFIED:
- Whether LLM-backed summaries are desirable for every watch event.
- Whether an external notification channel beyond local desktop notifications
  should be enabled for paper-campaign work.
- Whether the current monitor should dispatch through `services.alerts` or
  remain local-desktop/file-report only.

## Decision

Do not rebuild the old PR #43 AI alert monitor as a second background monitor.

The accepted current-master paper-simulation monitor is already the wake-up
layer. Adding a separate monitor would duplicate state ownership and increase
the chance of contradictory operator guidance.

The narrow rebuild candidate is an advisory synthesis layer:

- read existing paper-sim monitor status
- read recent paper-sim watch reports
- read canonical paper-gate progress
- read candidate/strategy evidence artifacts where available
- produce a read-only operator oversight report
- optionally summarize with an AI provider when configured
- never start, stop, route, promote, trade, or mutate gate state

## Scoped Objective

Build a read-only AI operator oversight report that answers:

- What changed since the latest watch report?
- Is the campaign healthy, idle, blocked, or requiring investigation?
- Which evidence/gate facts matter now?
- What should the human operator do next?
- What should remain untouched?

The report should be usable as a one-shot command first. No daemon, scheduler,
or automatic external alerting is in scope for the first implementation.

## Required Boundaries

MUST NOT:
- start another background monitor
- start or stop paper campaigns
- alter paper-sim watch configuration
- dispatch external notifications by default
- modify promotion gates or strategy decisions
- enable candidate-advisor strategy selection
- route orders, enqueue orders, or touch live execution
- rely on stale PR #43 source files or compiled cache artifacts

MUST:
- be read-only by default
- consume current-master artifacts and APIs only
- write any output under a dedicated report/artifact path
- make missing monitor status explicit
- make missing watch reports explicit
- separate AI-generated narrative from machine-observed facts
- degrade safely when no AI provider is configured
- include proof that strategy config remains non-authoritative for candidate
  advice and that live execution is untouched

## Smallest Implementation Path

1. Add a service such as `services/ai_copilot/operator_oversight.py`.
2. Add a root command such as `scripts/run_ai_operator_oversight.py`.
3. Load, normalize, and summarize:
   - `services.analytics.paper_sim_monitor.load_runtime_status()`
   - recent watch reports already exposed by the monitor status
   - `scripts.check_promotion_gates.run_check(stage_override="paper")`
   - optional candidate outcome and strategy evidence artifacts
4. Write:
   - latest JSON report
   - dated JSON report
   - optional Markdown summary
5. Add a Make target only if the CLI proof is stable, for example
   `make ai-operator-oversight`.

## Proof Required

Before implementation can be accepted:

- A root CLI command runs without network access when no AI provider is
  configured.
- The command produces a deterministic read-only report in a temp
  `CBP_STATE_DIR` during tests.
- Tests prove:
  - missing monitor status is reported as `insufficient_status`
  - missing watch reports are reported as `no_recent_watch_reports`
  - an `investigate` watch report produces an operator action item
  - paper-gate blockers are surfaced from machine facts
  - AI-provider absence degrades to machine-only summary
  - no paper campaign, promotion gate, candidate advisor, or order-routing
    state is mutated
- `configs/strategies/es_daily_trend_v1.yaml` remains
  `use_candidate_advisor: false`.
- `scripts/SCRIPTS.md`, `docs/ARCHITECTURE.md`, and `REMAINING_TASKS.md`
  describe the report as read-only advisory oversight.

## Out Of Scope

- external Slack/email/push notification enablement
- background scheduling
- autonomous restart or repair
- live trading oversight
- candidate advisor activation
- managed multi-symbol paper runtime
- safe pipeline wrapper/startup hardening

Those are separate high-risk objectives.

## Risk

HIGH for later implementation:
- This touches operator oversight around financial strategy experimentation and
  could influence human decisions.

LOW for this checkpoint:
- This document changes planning only. It does not modify runtime behavior,
  background jobs, strategy logic, order routing, or alert dispatch.

Acceptance state: ACCEPTED

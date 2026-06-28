# PR #43 AI Operator Oversight Rebuild Objective - 2026-06-28

Status: READY_FOR_INDEPENDENT_REVIEW

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

## Implementation Proof

Implemented in this proof pass:

- `services/ai_copilot/operator_oversight.py`
  - builds a read-only machine-fact report from the existing paper-sim monitor
    status, recent watch reports, and canonical paper-gate output
  - reports missing monitor status as `insufficient_status`
  - reports missing watch reports as `no_recent_watch_reports`
  - converts `recommendation_investigate` watch reports into operator action
    items
  - surfaces paper-gate blockers without mutating gate state
  - keeps machine facts separate from optional AI narrative
  - degrades to machine-only summary when AI is not requested or provider
    access is unavailable
  - writes latest and dated JSON/Markdown artifacts under
    `.cbp_state/runtime/ai_reports/`
- `scripts/run_ai_operator_oversight.py`
  - root one-shot operator CLI
  - writes artifacts by default
  - supports `--json`, `--no-write`, and explicit `--use-ai`
- `make ai-operator-oversight`
  - operator Make target for the report
- `tests/test_ai_copilot_operator_oversight.py`
  - missing monitor status proof
  - missing watch reports proof
  - investigate watch action proof
  - paper-gate blocker surfacing proof
  - AI-provider fallback proof
  - JSON/Markdown artifact write proof
  - candidate-advisor disabled proof
- `tests/test_run_ai_operator_oversight.py`
  - CLI JSON/no-write proof
  - CLI default artifact-write proof

The implementation remains read-only:

- no background monitor is started
- no paper campaign is started or stopped
- no watch configuration is mutated
- no external notification is dispatched
- no promotion gate is mutated
- no candidate-advisor strategy selection is enabled
- no order routing, submit, or cancellation path is touched
- `configs/strategies/es_daily_trend_v1.yaml` still has
  `use_candidate_advisor: false`

Verification in this environment:

- `./.venv/bin/python -m py_compile services/ai_copilot/operator_oversight.py scripts/run_ai_operator_oversight.py tests/test_ai_copilot_operator_oversight.py tests/test_run_ai_operator_oversight.py`
  - SHOWN: passed.
- `./.venv/bin/python scripts/run_ai_operator_oversight.py --no-write`
  - SHOWN: returned `status=investigate`, `watch_report_status=available`,
    `read_only=True`, and `ai_summary_status=machine_only` against the current
    local state.
- `CBP_STATE_DIR=/private/tmp/cbp-operator-oversight-proof ./.venv/bin/python scripts/run_ai_operator_oversight.py --json`
  - SHOWN: wrote latest and dated JSON/Markdown artifacts under
    `/private/tmp/cbp-operator-oversight-proof/runtime/ai_reports/`.
  - SHOWN: returned `status=insufficient_status`,
    `watch_report_status=no_recent_watch_reports`, and safety flags showing no
    background monitor start, no watch mutation, no external notification, no
    gate mutation, no order routing, and no live execution touch.
- `git diff --check`
  - SHOWN: passed.
- `rg -n "use_candidate_advisor:" configs/strategies/es_daily_trend_v1.yaml`
  - SHOWN: `use_candidate_advisor: false`.
- Targeted pytest was not run locally because this `.venv` currently reports
  `No module named pytest`.

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

HIGH for this implementation proof:
- This is read-only, but it produces operator guidance around financial
  strategy experimentation.

Acceptance state: READY_FOR_INDEPENDENT_REVIEW

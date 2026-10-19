# Signal-discovery modules and execution authority: independent review (structure item 9)

Date: 2026-10-05. Reviewer: Claude (AUDITOR). No patch: no defect found.
Reviewed at master `97c24c8e` plus the unpushed series through 0062; this
checkout is `620bc8dbe`.

## Result

The item's claim holds. The configured strategy is the only thing that
decides what is executed.

- SHOWN by reading `strategy_runner`: `select_strategy(...)` is called, but
  `selected_strategy` is then set to `cfg["strategy_id"]` again. The
  selector's output (regime, ranked candidates, scores, reason) goes only
  into status and intent metadata.
- The 15 guard tests for the classification and the authority decision pass.
- The dashboard's Execution Plan page cannot queue anything. SHOWN by probe
  in a scratch state directory: `queue_execution_intents` builds a row with
  no `intent_id`, the paper queue's `upsert_intent` requires one, and every
  row ends in `KeyError: 'intent_id'` (`queued: 0, errors: 1`). So the
  ranking and allocation pages have no route into the paper ledger.

## Facts worth knowing (not defects)

- The backlog says the candidate-advisor bridge is "explicitly env-gated".
  The canonical campaign script also turns that variable on from the
  strategy config (`use_candidate_advisor`); `es_daily_trend_v1.yaml` has it
  `false`. Either way the advisor only changes the advisory label.
- Selector metadata is what the canonical live consumer would pass to the
  optional AI gate as context (the gate is off; see patch 0056).
- This checkout's paper intent queue holds seven leftover smoke and test
  rows from March and April 2026 (`smoke-test-intent-*`, `meta-smoke-*`,
  `i-1`, `i1`), four of them marked `filled` with no linked order. None has
  a fill in the paper ledger, and all predate the gate cohort. They were
  written into the real state directory by smoke scripts or tests. Left
  untouched.

## Backlog coverage after this review

Every slice marked "ready for independent review" in the Active Backlog and
both deferred sections has now been reviewed in this series, except Active
item 16 (Hetzner host follow-through), which needs host access.

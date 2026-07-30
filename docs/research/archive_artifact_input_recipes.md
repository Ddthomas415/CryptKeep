# Archive Artifact Input Recipes

This note is an operator-facing contract for the accepted archive research
artifact producers. It is intentionally read-only: it documents the inputs that
must be selected before a producer is run, and it does not supply default
research choices.

## Scope Guard

This document does not run research jobs, fetch market data, generate research
artifacts, select strategy configs, select parameter grids, change strategy
configuration, start campaigns, change gates, change data ingestion, change
live routing, change execution, or create promotion evidence.

Archive research artifacts are research inputs to review. They are not campaign
evidence, not promotion evidence, not execution inputs, and not authority to
change strategy configuration.

## Accepted Producer Inputs

| Artifact | Make target | Args variable | Required accepted inputs | Default recipe |
| --- | --- | --- | --- | --- |
| `archive_walk_forward` | `archive-walk-forward` | `ARCHIVE_WALK_FORWARD_ARGS` | strategy config; venue/symbol/timeframe; archive row window; output path | no accepted default recipe |
| `archive_parameter_sweep` | `archive-parameter-sweep` | `ARCHIVE_PARAMETER_SWEEP_ARGS` | base strategy config; parameter grid; venue/symbol/timeframe; archive row window; output path | no accepted default recipe |
| `archive_parameter_sweep_triage` | `archive-parameter-sweep-triage` | `ARCHIVE_PARAMETER_SWEEP_TRIAGE_ARGS` | input archive_parameter_sweep artifact; output path | no accepted default recipe |

The current operator status reports expose these same requirements through
`research_artifact_inventory` and `operator_next_actions`. A bare Make target
is not an accepted archive recipe when the corresponding args variable is
required.

## Required Decisions Before Running

- Select the strategy config or source artifact path.
- Select the venue, symbol, timeframe, and archive row window when the producer
  reads archived market data.
- Select the parameter grid before running `archive_parameter_sweep`.
- Select explicit fee and slippage assumptions for any run whose output will be
  compared against paper-fill or walk-forward metrics.
- Select the output path or artifact directory.
- Record the command and resulting artifact hash before using the output in
  review.

## Non-Goals

- No checked-in default parameter grid is accepted by this note.
- No checked-in default archive row window is accepted by this note.
- No artifact produced by these commands becomes promotion evidence without a
  separate reviewed decision.
- No top-ranked sweep variant may change runtime strategy configuration without
  a separate reviewed config or campaign change.

## Guard

`tests/test_archive_artifact_input_recipes_doc.py` pins this contract against
the accepted archive artifact registry so the operator documentation cannot
silently drift from the Make targets, args variables, or required input labels
reported by `research_artifact_inventory`.

# Weekly Strategy Review Ritual

Date: 2026-07-03

## Purpose

Turn existing diagnostics and loss-replay tools into a repeatable weekly
operator artifact.

## Cadence

Run weekly while paper or shadow campaigns are active.

## Inputs

- current paper gate output
- `make status-paper-all`
- paper diagnostics report
- loss replay report when losses occurred
- strategy hypothesis docs
- latest work log/checkpoint changes

## Output

Write a dated checkpoint or strategy decision note that records:

- campaign health
- fills and qualified round trips
- wins/losses reviewed
- expectancy trend
- evidence/provenance failures
- strategy hypothesis updates or invalidation notes
- decision: continue, investigate, freeze, retire, or rewrite hypothesis

## Suggested Commands

Do not run these automatically if the operator has asked to avoid long commands:

```bash
make status-paper-all
./.venv/bin/python scripts/report_paper_run_diagnostics.py
./.venv/bin/python scripts/dev/replay_paper_losses.py
```

## Rule

The weekly review is advisory. Any config, strategy, gate, or promotion change
that follows must be a separate governed change.
